from typing import List, Optional, Dict, Literal
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

# ==========================
# Eval Lab Schemas
# ==========================

Label = Literal["Ambiguous", "Unambiguous"]

DEFAULT_RUBRICS = [
    "grammar",
    "word_choice",
    "cohesion",
    "conciseness",
    "completeness",
    "correctness",
    "clarity",
]


class EvalUploadResponse(BaseModel):
    job_id: str
    columns_detected: Dict[str, str]  
    preview_rows: List[Dict]


class EvalRunRequest(BaseModel):
    job_id: str
    judges: Optional[List[Dict[str, str]]] = None  
    rubrics: Optional[Dict[str, bool]] = None      
    custom_metrics: Optional[List[str]] = None    

 
    model_config = ConfigDict(json_schema_extra={
        "example": {
            "job_id": "",
            "judges": [
                {"id": "groq/llama-3.1-8b-instant", "label": "judge-mini-a"},
                {"id": "groq/llama-3.3-70b-versatile", "label": "judge-mini-c"},
                {"id": "hf/prometheus-7b-v2.0", "label": "judge-mini-b"}
            ],
            "rubrics": {
                "clarity": True,
                "cohesion": True,
                "completeness": True,
                "conciseness": True,
                "correctness": True,
                "grammar": True,
                "word_choice": True
            }
        }
    })


class EvalJobStatus(BaseModel):
    job_id: str
    total: int
    finished: int
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    judges: List[str]
    rubrics: List[str]
    custom_metrics: List[str]
    metrics_summary: Dict[str, float]  # e.g. {"class_accuracy": 0.875, "rationale_pass_rate": 0.742}


class JudgeAssessment(BaseModel):
    judge_id: str
    class_ok: Optional[bool]  # If gold_class exists, class_ok is compared by the system and reused. Otherwise, it will be judged by the judges
    rationale_ok_by_rubric: Dict[str, bool]
    custom_ok: Dict[str, bool]


class EvalRecordOut(BaseModel):
    id: str
    sentence: str
    gold_class: Optional[Label]
    pred_class: Label
    rationale: str
    judges: List[JudgeAssessment]
    consensus: Dict[str, Optional[float]]  # e.g. {"class_ok_ratio": 0.67, "rationale_pass_ratio": 0.71}


class EvalRecordsPage(BaseModel):
    page: int
    page_size: int
    total: int
    items: List[EvalRecordOut]


class EvalConfig(BaseModel):
    judges: List[Dict[str, str]]  # [{"id": "...", "label": "..."}, ...]
    default_rubrics: List[str] = Field(default=DEFAULT_RUBRICS)