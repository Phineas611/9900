import os
import uuid
import io
from pathlib import Path
from typing import List, Optional

import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.database.setup import get_db
from app.database.models.eval_lab import EvalLabJob, EvalLabRecord
from app.application.models.eval_lab import (
    EvalUploadResponse,
    EvalRunRequest,
    EvalJobStatus,
    EvalRecordsPage,
    EvalConfig,
    DEFAULT_RUBRICS,
)
from app.application.services.eval_io import load_table, detect_columns
from app.application.services.eval_pipeline import run_job
from app.application.services.judges import get_available_judges


router = APIRouter(prefix="/eval-lab", tags=["Evaluation Lab"])

# Anchor under backend directory for consistency
BACKEND_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BACKEND_DIR / os.getenv("DATA_DIR", "data/eval_lab")
DATA_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/config", response_model=EvalConfig)
def get_config():
    judges = [{"id": jid, "label": jid} for jid in get_available_judges().keys()]
    return {"judges": judges, "default_rubrics": DEFAULT_RUBRICS}


@router.post("/upload", response_model=EvalUploadResponse)
async def upload_result_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    ext = os.path.splitext(file.filename or "")[-1].lower()
    if ext not in (".csv", ".xlsx"):
        raise HTTPException(status_code=400, detail="Only .csv or .xlsx are supported")

    job_id = uuid.uuid4().hex
    dst = DATA_DIR / f"{job_id}{ext}"
    with open(dst, "wb") as f:
        f.write(await file.read())


    try:
        df, cols = load_table(str(dst))
    except Exception as e:
  
        try:
            os.remove(dst)
        except Exception:
            pass
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")
    preview = df.head(5).to_dict(orient="records")

    job = EvalLabJob(
        job_id=job_id,
        file_path=str(dst),
        columns_map=cols,
        judges=[],
        rubrics=DEFAULT_RUBRICS,
        custom_metrics=[],
        total=0,
        finished=0,
        metrics_summary={},
    )
    db.add(job)
    db.commit()
    return {"job_id": job_id, "columns_detected": cols, "preview_rows": preview}


@router.post("/run")
def run_evaluation(req: EvalRunRequest, db: Session = Depends(get_db)):
    job = db.get(EvalLabJob, req.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")

    run_job(
        session=db,
        job_id=req.job_id,
        judges=req.judges,
        rubrics_on=req.rubrics,
        custom_metrics=req.custom_metrics,
    )
    db.refresh(job)
    return {"job_id": req.job_id, "total": job.total, "started_at": job.started_at}


@router.get("/jobs/{job_id}", response_model=EvalJobStatus)
def job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.get(EvalLabJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return {
        "job_id": job.job_id,
        "total": job.total,
        "finished": job.finished,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
        "judges": job.judges,
        "rubrics": job.rubrics,
        "custom_metrics": job.custom_metrics,
        "metrics_summary": job.metrics_summary or {},
    }


@router.get("/jobs/{job_id}/records", response_model=EvalRecordsPage)
def list_records(
    job_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    judges: str = Query("", description="Comma-separated IDs of the judges, only the results of these judges will be returned; if empty, all will be returned."),
    contract_id: Optional[str] = Query(None, description="Filter by contract ID."),
    sentence_id: Optional[str] = Query(None, description="Filter by sentence ID."),
    db: Session = Depends(get_db),
):
    ids: Optional[List[str]] = [x for x in judges.split(",") if x] if judges else None

    query = select(EvalLabRecord).where(EvalLabRecord.job_id == job_id)
    if contract_id:
        query = query.where(EvalLabRecord.contract_id == contract_id)
    if sentence_id:
        query = query.where(EvalLabRecord.sentence_id == sentence_id)

    total = db.execute(
        select(func.count()).select_from(query.subquery())
    ).scalar_one()

    rows = db.execute(
        query.order_by(EvalLabRecord.pk.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).scalars().all()

    items = []
    for r in rows:
        jlist = []
        judges_json = r.judges_json or {}
        for j in judges_json.get("judges", []):
            if ids and j.get("judge_id") not in ids:
                continue
            jlist.append(j)
        items.append({
            "id": r.sid,
            "sentence": r.sentence,
            "gold_class": r.gold_class,
            "pred_class": r.pred_class,
            "rationale": r.rationale,
            "judges": jlist,
            "consensus": r.consensus_json or {},
        })

    return {"page": page, "page_size": page_size, "total": total, "items": items}


def _fetch_df_for_export(db: Session, job_id: str) -> pd.DataFrame:
    job = db.get(EvalLabJob, job_id)
    rubric_keys = list(job.rubrics) if job and job.rubrics else []
    custom_keys = list(job.custom_metrics) if job and job.custom_metrics else []
    rows = db.execute(
        select(EvalLabRecord)
        .where(EvalLabRecord.job_id == job_id)
        .order_by(EvalLabRecord.pk.desc())
    ).scalars().all()
    if not rows:
        return pd.DataFrame()
    
    recs = []
    for r in rows:
    
        rationale_val = r.rationale if r.rationale is not None else ""
        if isinstance(rationale_val, str) and rationale_val.strip().lower() == "nan":
            rationale_val = ""
        base = {
            "id": r.sid,
            "sentence": r.sentence,
            "gold_class": r.gold_class,
            "pred_class": r.pred_class,
            "rationale": rationale_val,
            "consensus_class_ok_ratio": (r.consensus_json or {}).get("class_ok_ratio"),
            "consensus_rationale_pass_ratio": (r.consensus_json or {}).get("rationale_pass_ratio"),
        }
        
        judges_json = r.judges_json or {}
        for j in judges_json.get("judges", []):
            jid = j.get("judge_id", "unknown")
            base[f"{jid}__class_ok"] = j.get("class_ok")
            rb = (j.get("rationale_ok_by_rubric") or {})
            mn = (j.get("custom_ok") or {})
            
            for k in rubric_keys:
                base[f"{jid}__rubric__{k}"] = rb.get(k)
            for k in custom_keys:
                base[f"{jid}__custom__{k}"] = mn.get(k)
        recs.append(base)
    return pd.DataFrame(recs)


@router.get("/jobs/{job_id}/export.csv")
def export_csv(job_id: str, db: Session = Depends(get_db)):
    df = _fetch_df_for_export(db, job_id)
    if df.empty:
        raise HTTPException(status_code=404, detail="no data")
    stream = io.StringIO()
    df.to_csv(stream, index=False)
    stream.seek(0)
    return StreamingResponse(iter([stream.getvalue()]), media_type="text/csv", headers={
        "Content-Disposition": f"attachment; filename=eval_{job_id}.csv"
    })


@router.get("/jobs/{job_id}/export.xlsx")
def export_xlsx(job_id: str, db: Session = Depends(get_db)):
    df = _fetch_df_for_export(db, job_id)
    if df.empty:
        raise HTTPException(status_code=404, detail="no data")

    b = io.BytesIO()
    with pd.ExcelWriter(b, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="eval")
    b.seek(0)
    return StreamingResponse(b, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={
        "Content-Disposition": f"attachment; filename=eval_{job_id}.xlsx"
    })