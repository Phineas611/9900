from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import io
import csv

from app.database.setup import get_db
from app.application.models.promptlab import (
    ModelSwitchRequest,
    ClassifyRequest,
    ExplainOneRequest,
    ExplainBatchRequest,
    ClassifyResult,
    ExplainResult,
)
from app.application.services.promptlab_service import PromptLabService

router = APIRouter(prefix="/promptlab", tags=["promptlab"])

service = PromptLabService()


@router.get("/models")
def get_models():
    return {
        "available": service.list_models(),
        "current": service.get_current_model(),
    }


@router.post("/models/switch")
def switch_model(body: ModelSwitchRequest):
    ok = service.switch_model(body.model_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"ok": True, "current": service.get_current_model()}


@router.post("/classify", response_model=List[ClassifyResult])
def classify(
    body: ClassifyRequest,
    db: Session = Depends(get_db),
):
    sentences: List[str] = []
    if body.sentence:
        sentences.append(body.sentence)
    if body.sentences:
        sentences.extend(body.sentences)
    if not sentences:
        raise HTTPException(status_code=400, detail="No sentence provided")

    return service.classify_sentences(
        sentences=sentences,
        prompt_id=body.prompt_id,
        custom_prompt=body.custom_prompt,
        db=db,
        user_id=0,
        contract_id=body.contract_id,
    )


@router.post("/explain/one", response_model=ExplainResult)
def explain_one(
    body: ExplainOneRequest,
    db: Session = Depends(get_db),
):
    return service.explain_one(
        sentence=body.sentence,
        prompt_id=body.prompt_id,
        custom_prompt=body.custom_prompt,
        db=db,
        user_id=0,
        contract_id=body.contract_id,
    )


@router.post("/explain/batch", response_model=List[ExplainResult])
def explain_batch(
    body: ExplainBatchRequest,
    db: Session = Depends(get_db),
):
    if not body.sentences:
        raise HTTPException(status_code=400, detail="No sentences provided")

    return service.explain_batch(
        sentences=body.sentences,
        prompt_id=body.prompt_id,
        custom_prompt=body.custom_prompt,
        db=db,
        user_id=0,
        contract_id=body.contract_id,
    )


@router.post("/explain/file")
async def explain_from_file(
    file: UploadFile = File(...),
    prompt_id: str = "amb-basic",
    custom_prompt: Optional[str] = None,
    contract_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Upload a CSV of sentences and get back a CSV with labels and rationales.
    CSV must have header: sentence (or text / clause).
    """
    if file.content_type not in ("text/csv", "application/vnd.ms-excel"):
        raise HTTPException(status_code=400, detail="Only CSV is supported right now.")

    raw = await file.read()
    decoded = raw.decode("utf-8", errors="ignore")

    reader = csv.DictReader(io.StringIO(decoded))
    sentences: List[str] = []
    for row in reader:
        sent = row.get("sentence") or row.get("text") or row.get("clause")
        if sent:
            sentences.append(sent.strip())

    if not sentences:
        raise HTTPException(status_code=400, detail="No sentences found in CSV file.")

    results = service.explain_batch(
        sentences=sentences,
        prompt_id=prompt_id,
        custom_prompt=custom_prompt,
        db=db,
        user_id=0,
        contract_id=contract_id,
    )

    # build output csv
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["sentence", "label", "rationale", "model_id", "contract_id", "sentence_id"])
    for r in results:
        writer.writerow([
            r.sentence,
            r.label,
            r.rationale,
            r.model_id,
            r.contract_id if r.contract_id else "",
            r.sentence_id if r.sentence_id else "",
        ])

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=promptlab_results.csv"},
    )
