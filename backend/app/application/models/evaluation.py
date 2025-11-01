from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal

# Default judge IDs (you can override in POST /evaluation/assess)
DEFAULT_JUDGES = [
    "groq/llama-3.1-8b-instant",
    "groq/llama-3.3-70b-versatile",
    "hf/prometheus-7b-v2.0",
]

EvalDimension = Literal["grammar","word_choice","cohesion","conciseness","completeness","correctness","clarity"]

class UploadResponse(BaseModel):
    run_id: str
    file_name: str
    total_items: int
    columns_mapped: Dict[str, str]

class AssessRequest(BaseModel):
    run_id: str
    judge_models: List[str] = Field(default_factory=lambda: DEFAULT_JUDGES[:])
    criteria: Dict[EvalDimension, bool] = Field(default_factory=lambda: {
        "grammar": True,
        "word_choice": True,
        "cohesion": True,
        "conciseness": True,
        "completeness": True,
        "correctness": True,
        "clarity": True
    })
    manual_metrics: List[str] = Field(default_factory=list)
    page_limit: int = 500
    temperature: float = 0.0
    require_json: bool = True

class VerdictLeaf(BaseModel):
    # "pass" is reserved keyword in Python; expose via alias
    pass_: Optional[bool] = Field(alias="pass", default=None)
    confidence: Optional[float] = None
    notes: str = ""

class Verdict(BaseModel):
    judge_label: Optional[Literal["ambiguous","unambiguous"]] = None
    predicted_class_correct: Optional[bool] = None
    rubric: Dict[EvalDimension, VerdictLeaf]
    manual: Dict[str, VerdictLeaf] = Field(default_factory=dict)

class ResultsQuery(BaseModel):
    run_id: str
    page: int = 1
    page_size: int = 12
