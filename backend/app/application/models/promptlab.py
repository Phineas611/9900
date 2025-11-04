from pydantic import BaseModel
from typing import List, Optional


class ModelSwitchRequest(BaseModel):
    model_id: str


class ClassifyRequest(BaseModel):
    # either a single sentence...
    sentence: Optional[str] = None
    # ... or multiple
    sentences: Optional[List[str]] = None

    # prompt info
    prompt_id: Optional[str] = "amb-basic"
    custom_prompt: Optional[str] = None

    # optional: link to a contract
    contract_id: Optional[int] = None


class ClassifyResult(BaseModel):
    sentence: str
    label: str
    score: float
    model_id: str
    rationale: Optional[str] = None
    contract_id: Optional[int] = None
    sentence_id: Optional[int] = None


class ExplainOneRequest(BaseModel):
    sentence: str
    prompt_id: Optional[str] = "amb-basic"
    custom_prompt: Optional[str] = None
    contract_id: Optional[int] = None


class ExplainBatchRequest(BaseModel):
    sentences: List[str]
    prompt_id: Optional[str] = "amb-basic"
    custom_prompt: Optional[str] = None
    contract_id: Optional[int] = None


class ExplainResult(BaseModel):
    sentence: str
    label: str
    rationale: str
    model_id: str
    contract_id: Optional[int] = None
    sentence_id: Optional[int] = None


class TaskResponse(BaseModel):
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: Optional[dict] = None  # {"current": 10, "total": 100}
    message: Optional[str] = None