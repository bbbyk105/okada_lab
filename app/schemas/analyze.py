from typing import List, Optional, Literal
from pydantic import BaseModel, Field

Method = Literal["X-ray", "NMR", "EM"]

class AnalyzeRequest(BaseModel):
    uniprot_ids: List[str] = Field(..., min_length=1)
    methods: Optional[List[Method]] = None   # 未指定なら Config 側の選択に従う
    seq_ratio: Optional[int] = 80
    cis_threshold: Optional[float] = None
    export_artifacts: bool = True
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
    kpi: KPI = Field(default_factory=KPI)
    artifacts: Artifacts = Field(default_factory=Artifacts)
    note: Optional[str] = None

class AnalyzeResponse(BaseModel):
    results: List[AnalyzeItem]
