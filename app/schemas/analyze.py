from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field

Method = Literal["X-ray", "NMR", "EM"]

class AnalyzeRequest(BaseModel):
    uniprot_ids: List[str] = Field(..., min_length=1)
    methods: Optional[List[Method]] = None           # 未指定なら Config に従う
    seq_ratio: Optional[int] = 80
    cis_threshold: Optional[float] = None            # 未指定なら Config に従う
    max_pdbs: Optional[int] = None                   # 既存prepに影響しないなら無視可
    clean_old_pdbs: bool = False                     # 既存運用に合わせ任意
    export_artifacts: bool = True                    # heatmap等の画像出力を許可
    verbose: bool = False

class KPI(BaseModel):
    umf: Optional[float] = None
    cis: Optional[int] = None
    mean_cisDist: Optional[float] = None
    std_cisDist: Optional[float] = None
    mean_cisScore: Optional[float] = None
    cis_per_len_percent: Optional[float] = None

class Artifacts(BaseModel):
    summary_csv: Optional[str] = None
    details_csv: Optional[str] = None
    stats_csv: Optional[str] = None
    heatmap_png: Optional[str] = None
    summary_txt: Optional[str] = None

class AnalyzeItem(BaseModel):
    uniprot_id: str
    full_name: Optional[str] = None
    organism: Optional[str] = None
    seq_ratio: Optional[int] = None
    kpi: KPI
    artifacts: Artifacts = Artifacts()
    note: Optional[str] = None

class AnalyzeResponse(BaseModel):
    results: List[AnalyzeItem]
