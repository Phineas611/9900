from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import csv
import io

import pandas as pd

from app.database.setup import get_db
from app.application.services.promptlab_service import PromptLabService

router = APIRouter(prefix="/promptlab", tags=["promptlab"])

service = PromptLabService()

print(">>> promptlab router loaded (fixed 4-column export)")


@router.get("/models")
def list_models():
    """
    Return all available models and the current one.
    """
    return {
        "available": service.list_models(),
        "current": service.get_current_model(),
    }


@router.post("/models/switch")
def switch_model(body: Dict[str, Any]):
    """
    Body: { "model_id": "..." }
    """
    model_id = body.get("model_id")
    if not model_id:
        raise HTTPException(status_code=400, detail="model_id is required")
    ok = service.switch_model(model_id)
    if not ok:
        raise HTTPException(status_code=404, detail="unknown model id")
    return {"ok": True, "current": service.get_current_model()}


@router.get("/prompts")
def list_prompts():
    """
    For frontend dropdown.
    """
    return {"prompts": service.list_prompts()}


@router.post("/classify")
def classify(
    body: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """
    Classify single / multiple sentences.
    """
    sentences: List[str] = []
    if body.get("sentence"):
        sentences.append(body["sentence"])
    if body.get("sentences"):
        sentences.extend(body["sentences"])

    if not sentences:
        raise HTTPException(status_code=400, detail="no sentence(s) provided")

    res = service.classify_sentences(
        sentences=sentences,
        prompt_id=body.get("prompt_id"),
        custom_prompt=body.get("custom_prompt"),
        db=db,
        user_id=0,
        contract_id=body.get("contract_id"),
    )
    return [r.dict() for r in res]


@router.post("/explain/one")
def explain_one(
    body: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """
    Chat-like single sentence explanation.
    """
    sentence = body.get("sentence")
    if not sentence:
        raise HTTPException(status_code=400, detail="sentence is required")

    res = service.explain_one(
        sentence=sentence,
        prompt_id=body.get("prompt_id"),
        custom_prompt=body.get("custom_prompt"),
        db=db,
        user_id=0,
        contract_id=body.get("contract_id"),
    )
    return res.dict()


@router.post("/explain/batch")
def explain_batch(
    body: Dict[str, Any],
    db: Session = Depends(get_db),
):
    """
    JSON batch.
    """
    sentences = body.get("sentences") or []
    if not sentences:
        raise HTTPException(status_code=400, detail="sentences is required")

    res = service.explain_batch(
        sentences=sentences,
        prompt_id=body.get("prompt_id"),
        custom_prompt=body.get("custom_prompt"),
        db=db,
        user_id=0,
        contract_id=body.get("contract_id"),
    )
    return [r.dict() for r in res]


@router.post("/explain/file")
async def explain_file(
    file: UploadFile = File(...),
    prompt_id: str = Query(default="amb-basic"),
    custom_prompt: Optional[str] = Query(default=None),
    out: str = Query(default="csv", regex="^(csv|xlsx)$"),
    db: Session = Depends(get_db),
):
    """
    Upload CSV/Excel of sentences and return a CSV/XLSX with exactly:
    item_id,sentence,predicted_label,rationale
    """
    raw = await file.read()
    filename = file.filename or ""

    # 1. read input sentences
    if filename.lower().endswith((".xlsx", ".xls")):
        df = pd.read_excel(io.BytesIO(raw))
        col = None
        for c in ["sentence", "text", "clause", "sentences"]:
            if c in df.columns:
                col = c
                break
        if col is None:
            col = df.columns[0]
        sentences = df[col].fillna("").astype(str).tolist()
    else:
        decoded = raw.decode("utf-8", errors="ignore")
        reader = csv.DictReader(io.StringIO(decoded))
        sentences: List[str] = []
        for row in reader:
            sent = row.get("sentence") or row.get("text") or row.get("clause")
            if sent:
                sentences.append(sent.strip())

    if not sentences:
        raise HTTPException(status_code=400, detail="No sentences found in file")

    # 2. run promptlab
    results = service.explain_batch(
        sentences=sentences,
        prompt_id=prompt_id,
        custom_prompt=custom_prompt,
        db=db,
        user_id=0,
        contract_id=None,
    )

    # 3. build output rows
    rows = []
    for idx, r in enumerate(results, start=1):
        rows.append(
            {
                "item_id": idx,
                "sentence": r.sentence,
                "predicted_label": r.label,
                "rationale": r.rationale,
            }
        )

    # 4. export
    if out == "csv":
        buff = io.StringIO()
        writer = csv.DictWriter(buff, fieldnames=["item_id", "sentence", "predicted_label", "rationale"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        buff.seek(0)
        return StreamingResponse(
            buff,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=promptlab_results.csv"},
        )
    else:
        # xlsx
        df_out = pd.DataFrame(rows, columns=["item_id", "sentence", "predicted_label", "rationale"])
        bio = io.BytesIO()
        with pd.ExcelWriter(bio, engine="openpyxl") as writer:
            df_out.to_excel(writer, index=False, sheet_name="promptlab")
        bio.seek(0)
        return StreamingResponse(
            bio,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=promptlab_results.xlsx"},
        )
