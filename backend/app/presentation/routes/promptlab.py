from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Query,
    BackgroundTasks,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import io
import csv
import pandas as pd
import logging
import uuid
import threading
from datetime import datetime

from app.database.setup import get_db
from app.application.models.promptlab import (
    ModelSwitchRequest,
    ClassifyRequest,
    ExplainOneRequest,
    ExplainBatchRequest,
    ClassifyResult,
    ExplainResult,
    TaskResponse,
    TaskStatusResponse,
)
from app.application.services.promptlab_service import PromptLabService

router = APIRouter(prefix="/promptlab", tags=["promptlab"])
service = PromptLabService()
logger = logging.getLogger(__name__)

_tasks: Dict[str, Dict[str, Any]] = {}
_tasks_lock = threading.Lock()


@router.get("/models")
def list_models():
    """Return available models and the current selection."""
    try:
        return {
            "available": service.list_models(),
            "current": service.get_current_model(),
        }
    except Exception as e:
        logger.error(f"Error in list_models: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")


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


def _process_file_async(
    task_id: str,
    sentences: List[str],
    prompt_id: str,
    custom_prompt: Optional[str],
    contract_id: Optional[int],
    out: str,
):
    """Background task function for processing file"""
    logger = logging.getLogger(__name__)
    
    try:
        with _tasks_lock:
            _tasks[task_id]["status"] = "processing"
            _tasks[task_id]["progress"] = {"current": 0, "total": len(sentences)}
        
        from app.database.setup import SessionLocal
        db = SessionLocal()
        
        try:
            def update_progress(current: int, total: int):
                with _tasks_lock:
                    if task_id in _tasks:
                        _tasks[task_id]["progress"] = {"current": current, "total": total}
            
            results = service.explain_batch(
                sentences=sentences,
                prompt_id=prompt_id,
                custom_prompt=custom_prompt,
                db=db,
                user_id=0,
                contract_id=contract_id,
                progress_callback=update_progress,
            )
            
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
            
            if out == "xlsx":
                df_out = pd.DataFrame(rows, columns=columns)
                bio = io.BytesIO()
                with pd.ExcelWriter(bio, engine="openpyxl") as writer:
                    df_out.to_excel(writer, index=False, sheet_name="promptlab")
                bio.seek(0)
                result_data = bio.getvalue()
                result_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                result_filename = "promptlab_results.xlsx"
            else:
                buff = io.StringIO()
                writer = csv.DictWriter(buff, fieldnames=columns)
                writer.writeheader()
                for row in rows:
                    writer.writerow(row)
                buff.seek(0)
                result_data = buff.getvalue().encode("utf-8")
                result_type = "text/csv"
                result_filename = "promptlab_results.csv"
            
            with _tasks_lock:
                _tasks[task_id]["status"] = "completed"
                _tasks[task_id]["progress"] = {"current": len(sentences), "total": len(sentences)}
                _tasks[task_id]["result"] = {
                    "data": result_data,
                    "type": result_type,
                    "filename": result_filename,
                }
                _tasks[task_id]["message"] = f"Successfully processed {len(sentences)} sentences"
                _tasks[task_id]["completed_at"] = datetime.now().isoformat()
            
            logger.info(f"[Task {task_id}] Completed successfully")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"[Task {task_id}] Error: {e}", exc_info=True)
        with _tasks_lock:
            _tasks[task_id]["status"] = "failed"
            _tasks[task_id]["message"] = f"Processing failed: {str(e)}"
            _tasks[task_id]["error"] = str(e)
            _tasks[task_id]["failed_at"] = datetime.now().isoformat()


@router.post("/explain/file", response_model=TaskResponse)
async def explain_file(
    file: UploadFile = File(...),
    prompt_id: str = Query(default="amb-basic"),
    custom_prompt: Optional[str] = Query(default=None),
    contract_id: Optional[int] = Query(default=None),
    out: str = Query(default="csv", regex="^(csv|xlsx)$"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db),
):
    """
    Async file processing: accepts CSV/Excel file, returns task ID.
    Use /explain/file/status/{task_id} to check status, /explain/file/result/{task_id} to get results.
    """
    logger = logging.getLogger(__name__)
    
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"File too large (max {MAX_FILE_SIZE // 1024 // 1024}MB)"
        )
    
    logger.info(f"Received file: {file.filename}, size: {file.size} bytes, contract_id: {contract_id}")
    
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
    
    logger.info(f"Extracted {len(sentences)} sentences from file")

    # 2) Create task
    task_id = str(uuid.uuid4())
    with _tasks_lock:
        _tasks[task_id] = {
            "status": "pending",
            "progress": {"current": 0, "total": len(sentences)},
            "message": "Task created",
            "created_at": datetime.now().isoformat(),
            "sentences_count": len(sentences),
            "contract_id": contract_id,
        }
    
    # 3) Add background task
    background_tasks.add_task(
        _process_file_async,
        task_id=task_id,
        sentences=sentences,
        prompt_id=prompt_id,
        custom_prompt=custom_prompt,
        contract_id=contract_id,
        out=out,
    )
    
    logger.info(f"Created task {task_id} for {len(sentences)} sentences")
    
    return TaskResponse(
        task_id=task_id,
        status="pending",
        message=f"Task created. Processing {len(sentences)} sentences. Use /explain/file/status/{task_id} to check status."
    )


@router.get("/explain/file/status/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str):
    """Get task status"""
    with _tasks_lock:
        task = _tasks.get(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return TaskStatusResponse(
        task_id=task_id,
        status=task["status"],
        progress=task.get("progress"),
        message=task.get("message"),
    )


@router.get("/explain/file/result/{task_id}")
def get_task_result(task_id: str):
    """Get task result (CSV/XLSX file)"""
    with _tasks_lock:
        task = _tasks.get(task_id)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Task not completed yet. Current status: {task['status']}"
        )
    
    result = task.get("result")
    if not result:
        raise HTTPException(status_code=500, detail="Result data not found")
    
    return StreamingResponse(
        io.BytesIO(result["data"]),
        media_type=result["type"],
        headers={"Content-Disposition": f"attachment; filename={result['filename']}"},
    )
