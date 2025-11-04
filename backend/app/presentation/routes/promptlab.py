from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Query,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import io
import csv
import pandas as pd
import logging

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
def list_models():
    """Return available models and the current selection."""
    return {
        "available": service.list_models(),
        "current": service.get_current_model(),
    }


@router.post("/models/switch")
def switch_model(body: ModelSwitchRequest):
    """Switch the current model by id."""
    ok = service.switch_model(body.model_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"ok": True, "current": service.get_current_model()}


@router.get("/prompts")
def list_prompts():
    """List preset prompt IDs (for frontend dropdown)."""
    return {"prompts": service.list_prompts()}


@router.post("/classify", response_model=List[ClassifyResult])
def classify(body: ClassifyRequest, db: Session = Depends(get_db)):
    """
    Classify one or multiple sentences.
    Body may provide 'sentence' and/or 'sentences'.
    """
    sentences: List[str] = []
    if body.sentence:
        sentences.append(body.sentence)
    if body.sentences:
        sentences.extend(body.sentences)
    if not sentences:
        raise HTTPException(status_code=400, detail="No sentence provided")

    try:
        return service.classify_sentences(
            sentences=sentences,
            prompt_id=body.prompt_id,
            custom_prompt=body.custom_prompt,
            db=db,
            user_id=0,
            contract_id=body.contract_id,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/explain/one", response_model=ExplainResult)
def explain_one(body: ExplainOneRequest, db: Session = Depends(get_db)):
    """Explain ambiguity for a single sentence."""
    try:
        return service.explain_one(
            sentence=body.sentence,
            prompt_id=body.prompt_id,
            custom_prompt=body.custom_prompt,
            db=db,
            user_id=0,
            contract_id=body.contract_id,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/explain/batch", response_model=List[ExplainResult])
def explain_batch(body: ExplainBatchRequest, db: Session = Depends(get_db)):
    """Explain ambiguity for multiple sentences (JSON array)."""
    if not body.sentences:
        raise HTTPException(status_code=400, detail="No sentences provided")
    try:
        return service.explain_batch(
            sentences=body.sentences,
            prompt_id=body.prompt_id,
            custom_prompt=body.custom_prompt,
            db=db,
            user_id=0,
            contract_id=body.contract_id,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


@router.post("/explain/file")
async def explain_file(
    file: UploadFile = File(...),
    prompt_id: str = Query(default="amb-basic"),
    custom_prompt: Optional[str] = Query(default=None),
    contract_id: Optional[int] = Query(default=None),
    out: str = Query(default="csv", regex="^(csv|xlsx)$"),
    db: Session = Depends(get_db),
):
    """
    Accept CSV/Excel of sentences and return CSV/XLSX with columns:
    id,sentence,label,rationale,model_id,contract_id,sentence_id

    Accepted input headers: sentence / text / clause (if none, use the first column).
    """
    logger = logging.getLogger(__name__)
    
    MAX_FILE_SIZE = 10 * 1024 * 1024
    MAX_SENTENCES = 500 
    
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"File too large (max {MAX_FILE_SIZE // 1024 // 1024}MB)"
        )
    
    logger.info(f"Processing file: {file.filename}, size: {file.size} bytes, contract_id: {contract_id}")
    
    raw = await file.read()
    filename = (file.filename or "").lower()

    # 1) Parse sentences from input file
    try:
        if filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(raw))
            use_col = None
            for c in ["sentence", "text", "clause", "sentences"]:
                if c in df.columns:
                    use_col = c
                    break
            if use_col is None:
                use_col = df.columns[0]
            sentences = df[use_col].fillna("").astype(str).tolist()
        else:
            decoded = raw.decode("utf-8", errors="ignore")
            reader = csv.DictReader(io.StringIO(decoded))
            sentences: List[str] = []
            for row in reader:
                sent = row.get("sentence") or row.get("text") or row.get("clause")
                if sent:
                    sentences.append(sent.strip())
    except Exception as e:
        logger.error(f"Error parsing file: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Error parsing file: {str(e)}")

    if not sentences:
        raise HTTPException(status_code=400, detail="No sentences found in file")
    
    if len(sentences) > MAX_SENTENCES:
        raise HTTPException(
            status_code=400, 
            detail=f"Too many sentences (max {MAX_SENTENCES}). Please split your file."
        )
    
    logger.info(f"Extracted {len(sentences)} sentences from file")

    # 2) Run inference via service
    try:
        results = service.explain_batch(
            sentences=sentences,
            prompt_id=prompt_id,
            custom_prompt=custom_prompt,
            db=db,
            user_id=0,
            contract_id=contract_id,
        )
    except RuntimeError as e:
        logger.error(f"RuntimeError in explain_batch: {e}", exc_info=True)
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in explain_batch: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

    # 3) Build output rows (id is 1-based; fill missing sentence_id with id)
    rows = []
    for idx, r in enumerate(results, start=1):
        rows.append({
            "id": idx,
            "sentence": r.sentence,
            "label": r.label,
            "rationale": r.rationale,
            "model_id": r.model_id,
            "contract_id": r.contract_id if r.contract_id is not None else (contract_id if contract_id is not None else ""),
            "sentence_id": r.sentence_id if r.sentence_id is not None else idx,
        })

    columns = ["id", "sentence", "label", "rationale", "model_id", "contract_id", "sentence_id"]

    # 4) Stream back CSV or XLSX
    try:
        if out == "xlsx":
            df_out = pd.DataFrame(rows, columns=columns)
            bio = io.BytesIO()
            with pd.ExcelWriter(bio, engine="openpyxl") as writer:
                df_out.to_excel(writer, index=False, sheet_name="promptlab")
            bio.seek(0)
            return StreamingResponse(
                bio,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": "attachment; filename=promptlab_results.xlsx"},
            )
        else:
            buff = io.StringIO()
            writer = csv.DictWriter(buff, fieldnames=columns)
            writer.writeheader()
            for row in rows:
                writer.writerow(row)
            buff.seek(0)
            return StreamingResponse(
                buff,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=promptlab_results.csv"},
            )
    except Exception as e:
        logger.error(f"Error generating output file: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating output: {str(e)}")
