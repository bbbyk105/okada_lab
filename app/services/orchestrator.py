from __future__ import annotations
from typing import List, Dict, Any, Optional
import os
import pandas as pd

# 既存モジュールをそのまま import（パスは実際の配置に合わせて調整）
from app.domain.config import Config
from app.domain.uniprot_handler import UniprotData
from app.domain.main import (
count_pdb, prep, run_DSA, save_score_details, save_summary_statistics
)
from app.domain.visualization import generate_heatmap

def _ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)

def run_analysis(
    uniprot_ids: List[str],
    methods: Optional[List[str]] = None,
    seq_ratio: Optional[int] = 80,
    cis_threshold: Optional[float] = None,
    export_artifacts: bool = True,
    verbose: bool = False,
) -> List[Dict[str, Any]]:
    """
    既存コード(main.py / example.py のフロー)をそのまま呼び出し、
    各IDのKPIと生成物パスを返す薄いラッパー
    """
    # Config をリクエストで上書き（未指定は既存デフォルトを利用）
    cfg_kwargs: Dict[str, Any] = {}
    if seq_ratio is not None:       cfg_kwargs["SEQ_RATIO"] = seq_ratio
    if cis_threshold is not None:   cfg_kwargs["CIS_THRESHOLD"] = cis_threshold
    # methods 未指定なら Config 側の USE_XRAY/USE_NMR/USE_EM に従う
    config = Config(**cfg_kwargs)

    dirpath = config.OUTPUT_DIR
    _ensure_dir(dirpath)

    results: List[Dict[str, Any]] = []
    for uid in uniprot_ids:
        try:
            unidata = UniprotData(uid)
            full_name = getattr(unidata, "get_fullname", lambda: None)()
            organism = getattr(unidata, "get_organism", lambda: None)()

            # Methods は Config に任せる（未指定時）
            sel_methods = methods if methods else config.METHODS_SELECTED

            # PDB 数チェック
            if not count_pdb(uid, methods=sel_methods):
                results.append({
                    "uniprot_id": uid,
                    "full_name": full_name,
                    "organism": organism,
                    "seq_ratio": config.SEQ_RATIO,
                    "kpi": {},
                    "artifacts": {},
                    "note": "Not enough PDB entries"
                })
                continue

            # データ準備
            seqdata, all_pdblist = prep(uid, methods=sel_methods, verbose=verbose)
            # 既存 example と同じ「nor+sub」構成
            seqdata1 = seqdata.filter(like=uid)
            pdbtuple = tuple(all_pdblist[0] + all_pdblist[1])
            seqdata2 = seqdata.loc[:, seqdata.columns.str.startswith(pdbtuple)]
            norsub_seqdata = pd.concat([seqdata1, seqdata2], axis=1)

            # 解析本体（既存の run_DSA をそのまま）
            score, log_text, summary_df = run_DSA(
                uid,
                norsub_seqdata,
                export=True,
                seqtype="nor+sub",
                methods=sel_methods,
                seq_ratio=config.SEQ_RATIO,
                cis_threshold=config.CIS_THRESHOLD,
                dirpath=dirpath,
                verbose=verbose
            )

            # KPI 抽出（既存 main/example の出力列に準拠）
            kpi = {}
            if summary_df is not None and len(summary_df) > 0:
                row0 = summary_df.iloc[0]
                def _get(col): 
                    return float(row0[col]) if col in row0 and pd.notna(row0[col]) else None
                kpi = {
                    "umf": _get("UMF"),
                    "cis": int(row0["cis"]) if "cis" in row0 and pd.notna(row0["cis"]) else None,
                    "mean_cisDist": _get("mean_cisDist"),
                    "std_cisDist": _get("std_cisDist"),
                    "mean_cisScore": _get("mean_cisScore"),
                    "cis_per_len_percent": _get("cis/Length(%)"),
                }

            # 既存のCSV統合（summary_details / summary_statistics）
            details_csv = stats_csv = None
            try:
                existing_details = None
                existing_stats = None
                # 詳細CSVを追記統合
                if score is not None and len(score) > 0:
                    existing_details = None
                    _ = save_score_details(uid, score, float(config.SEQ_RATIO), dirpath, existing_details)
                    details_csv = os.path.join(dirpath, "score_details.csv")
                # 統計CSVを追記統合
                if summary_df is not None and len(summary_df) > 0:
                    _ = save_summary_statistics(uid, full_name or "", organism or "",
                                                score, summary_df, float(config.SEQ_RATIO),
                                                dirpath, existing_stats)
                    stats_csv = os.path.join(dirpath, "summary_statistics.csv")
            except Exception:
                # CSV 統合は任意。失敗しても解析自体は成功扱いにする
                pass

            # 画像（任意）
            heatmap_png = None
            if export_artifacts and score is not None and len(score) > 0:
                heatmap_png = os.path.join(dirpath, f"{uid}_{config.SEQ_RATIO}_heatmap.png")
                try:
                    generate_heatmap(score, heatmap_png)
                except Exception:
                    heatmap_png = None

            # テキストサマリ（既存 main と同等のパス命名）
            summary_txt = os.path.join(dirpath, f"{uid}_{config.SEQ_RATIO}_summary.txt")
            # run_DSA 側/既存 main 側で出力していない場合は、必要に応じ作成してもOK

            results.append({
                "uniprot_id": uid,
                "full_name": full_name,
                "organism": organism,
                "seq_ratio": int(config.SEQ_RATIO),
                "kpi": kpi,
                "artifacts": {
                    "summary_csv": os.path.join(dirpath, "summary.csv"),
                    "details_csv": details_csv,
                    "stats_csv": stats_csv,
                    "heatmap_png": heatmap_png,
                    "summary_txt": summary_txt,
                },
                "note": "ok"
            })

        except Exception as e:
            results.append({
                "uniprot_id": uid,
                "full_name": None,
                "organism": None,
                "seq_ratio": int(config.SEQ_RATIO),
                "kpi": {},
                "artifacts": {},
                "note": f"error: {e}"
            })
            continue

    return results
