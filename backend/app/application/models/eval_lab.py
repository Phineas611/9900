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
    judges: Optional[List[str]] = None  #If it is empty, the system defaults to three judges
    rubrics: Optional[Dict[str, bool]] = None  # If it is empty, the system defaults to three judges
    custom_metrics: Optional[List[str]] = None  # User-defined metrics, such as [" Executability ", "legal basis Citation "]

    # 明确 API 示例，避免 additionalProp1/2/3
    model_config = ConfigDict(json_schema_extra={
        "examples": [{
            "job_id": "example-job-id",
            "judges": ["judge-mini-a", "judge-mini-b", "judge-mini-c"],
            "rubrics": {
                "grammar": True,
                "word_choice": True,
                "cohesion": True,
                "conciseness": True,
                "completeness": True,
                "correctness": True,
                "clarity": True
            },
            "custom_metrics": []
        }]
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