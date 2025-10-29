from fastapi import APIRouter, HTTPException
from app.schemas.analyze import AnalyzeRequest, AnalyzeResponse, AnalyzeItem, KPI, Artifacts
from app.services.orchestrator import run_analysis

router = APIRouter(prefix="/analyze", tags=["analyze"])

@router.post("", response_model=AnalyzeResponse)
def analyze(req: AnalyzeRequest):
    try:
        results = run_analysis(
            uniprot_ids=req.uniprot_ids,
            methods=req.methods,
            seq_ratio=req.seq_ratio,
            cis_threshold=req.cis_threshold,
            export_artifacts=req.export_artifacts,
            verbose=req.verbose,
        )
        items = []
        for r in results:
            items.append(AnalyzeItem(
                uniprot_id=r.get("uniprot_id"),
                full_name=r.get("full_name"),
                organism=r.get("organism"),
                seq_ratio=r.get("seq_ratio"),
                kpi=KPI(**(r.get("kpi") or {})),
                artifacts=Artifacts(**(r.get("artifacts") or {})),
                note=r.get("note")
            ))
        return AnalyzeResponse(results=items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
