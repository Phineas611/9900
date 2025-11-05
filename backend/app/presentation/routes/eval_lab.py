import os
import uuid
import io
import asyncio
from pathlib import Path
from typing import List, Optional, Dict

import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException, Query, Depends, Response
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from app.database.setup import get_db, SessionLocal
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
from app.application.services.judges import get_available_judges
from app.application.models.evaluation import AssessRequest, DEFAULT_JUDGES
from app.persistence.evaluation_repository import EvaluationRepository
from app.application.services.evaluation_service import EvaluationService


router = APIRouter(prefix="/eval-lab", tags=["Evaluation Lab"])

# Anchor under backend directory for consistency
BACKEND_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BACKEND_DIR / os.getenv("DATA_DIR", "data/eval_lab")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------
# Async task registry (in-memory)
# ---------------------------
RUN_TASKS: Dict[str, asyncio.Task] = {}
JOB_TO_RUN: Dict[str, str] = {}


def _build_assess_request(run_id: str, req: EvalRunRequest, rows_count: int) -> AssessRequest:
    judge_models = req.judges or DEFAULT_JUDGES[:]
    crit = req.rubrics or {k: True for k in DEFAULT_RUBRICS}
    manual_metrics = req.custom_metrics or []
    return AssessRequest(
        run_id=run_id,
        judge_models=judge_models,
        criteria=crit,  # type: ignore
        manual_metrics=manual_metrics,
        page_limit=rows_count,
        temperature=0.0,
        require_json=True,
    )


async def _run_in_background(job_id: str, run_id: str, assess_req: AssessRequest):
    """Execute assessment asynchronously, then materialize EvalLabRecord and update job status."""
    db = SessionLocal()
    repo = EvaluationRepository()
    svc = EvaluationService(repo)
    try:
        # Run assess and persist summary to evaluation_runs
        await svc.assess_async(db, user_id=1, req=assess_req)

        # Materialize results into EvalLabRecord for frontend compatibility
        from datetime import datetime, timezone
        job = db.get(EvalLabJob, job_id)
        if not job:
            # job might have been deleted; mark run failed
            repo.update_run_status(db, run_id, "FAILED: job missing")
            return

        # Judges/rubrics/custom already set on job at submission time
        # Compute totals and fill records
        pairs, _ = repo.list_results(db, run_id, page=1, page_size=10**9)
        total = 0
        finished = 0
        class_ok_total = 0
        rationale_pass_total = 0

        for item, agg in pairs:
            total += 1
            js = repo.list_judgments_for_item(db, run_id, item.id)
            judges_list = []
            class_votes = []
            rationale_votes = []
            for j in js:
                verdict = j.verdict or {}
                class_ok = verdict.get("predicted_class_correct")
                rubric = verdict.get("rubric", {})
                manual = verdict.get("manual", {})
                jud = {
                    "judge_id": j.judge_model,
                    "class_ok": class_ok,
                    "rationale_ok_by_rubric": {k: (leaf or {}).get("pass") for k, leaf in rubric.items()},
                    "custom_ok": {k: (leaf or {}).get("pass") for k, leaf in manual.items()},
                }
                judges_list.append(jud)
                if isinstance(class_ok, bool):
                    class_votes.append(class_ok)
                rv = list(jud["rationale_ok_by_rubric"].values())
                if rv:
                    rationale_votes.append(sum(1 for v in rv if v) / len(rv))

            consensus = {
                "class_ok_ratio": (sum(class_votes) / len(class_votes)) if class_votes else None,
                "rationale_pass_ratio": (sum(rationale_votes) / len(rationale_votes)) if rationale_votes else None,
            }

            if consensus["class_ok_ratio"] is not None:
                class_ok_total += 1 if consensus["class_ok_ratio"] >= 0.5 else 0
            if consensus["rationale_pass_ratio"] is not None:
                rationale_pass_total += 1 if consensus["rationale_pass_ratio"] >= 0.5 else 0

            rec = EvalLabRecord(
                job_id=job_id,
                sid=item.item_id,
                sentence=item.sentence,
                gold_class=item.gold_label,
                pred_class=item.predicted_label,
                rationale=item.rationale,
                judges_json={"judges": judges_list},
                consensus_json=consensus,
            )
            db.add(rec)
            finished += 1

        job.total = total
        job.finished = finished
        job.finished_at = datetime.now(timezone.utc)
        job.metrics_summary = {
            "class_accuracy": (class_ok_total / total) if total else 0.0,
            "rationale_pass_rate": (rationale_pass_total / total) if total else 0.0,
        }
        db.add(job)
        db.commit()
    except Exception as e:
        # Mark run failed and keep job state without finishing
        try:
            repo.update_run_status(db, run_id, f"FAILED: {e}")
        except Exception:
            pass
    finally:
        try:
            db.close()
        finally:
            RUN_TASKS.pop(run_id, None)
            JOB_TO_RUN.pop(job_id, None)


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


@router.post("/run", status_code=202)
async def run_evaluation(req: EvalRunRequest, db: Session = Depends(get_db), response: Response = None):
    job = db.get(EvalLabJob, req.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")

    try:
        df, cols = load_table(job.file_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {e}")

    repo = EvaluationRepository()
    svc = EvaluationService(repo)
    run_id = uuid.uuid4().hex
    repo.create_run(db, run_id=run_id, user_id=1, file_name=os.path.basename(job.file_path), config={
        "job_id": job.job_id,
        "columns_map": cols,
    })

    rows = []
    id_col = cols.get("id")
    sent_col = cols.get("sentence")
    label_col = cols.get("label")
    rat_col = cols.get("rationale")
    gold_col = cols.get("gold_class")
    if not (id_col and sent_col and label_col and rat_col):
        raise HTTPException(status_code=400, detail=f"Missing required columns after detection: {cols}")

    for _, r in df.iterrows():
        row = {
            "item_id": str(r[id_col]),
            "sentence": str(r[sent_col]),
            "predicted_label": str(r[label_col]),
            "rationale": str(r[rat_col]),
        }
        if gold_col and gold_col in r and pd.notna(r[gold_col]):
            row["gold_label"] = str(r[gold_col])
        rows.append(row)
    repo.bulk_insert_items(db, run_id, rows)

    assess_req = _build_assess_request(run_id, req, len(rows))
    from datetime import datetime, timezone
    job.started_at = datetime.now(timezone.utc)
    job.judges = list(assess_req.judge_models)
    job.rubrics = [k for k, on in assess_req.criteria.items() if on]
    job.custom_metrics = list(assess_req.manual_metrics)
    job.total = len(rows)
    job.finished = 0
    job.finished_at = None
    db.add(job)
    db.commit()

    # Schedule background task if not already running
    JOB_TO_RUN[req.job_id] = run_id
    if run_id not in RUN_TASKS or RUN_TASKS[run_id].done():
        RUN_TASKS[run_id] = asyncio.create_task(_run_in_background(req.job_id, run_id, assess_req))

    # Immediate 202 Accepted with state links
    if response is not None:
        response.headers["Location"] = f"/api/eval-lab/jobs/{req.job_id}/state"
    return {
        "task_id": req.job_id,
        "run_id": run_id,
        "state": "PROCESSING",
        "status_url": f"/api/eval-lab/jobs/{req.job_id}/state",
        "result_csv": f"/api/eval-lab/jobs/{req.job_id}/export.csv",
        "result_xlsx": f"/api/eval-lab/jobs/{req.job_id}/export.xlsx",
    }


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


@router.get("/jobs/{job_id}/state")
def job_state(job_id: str, db: Session = Depends(get_db)):
    job = db.get(EvalLabJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="task/run not found")
    status = "QUEUED"
    if job.started_at and not job.finished_at:
        status = "PROCESSING"
    elif job.finished_at:
        status = "DONE"
    progress = None
    try:
        progress = (job.finished / max(1, job.total)) if job.total else 0.0
    except Exception:
        progress = None
    return {
        "task_id": job_id,
        "status": status,
        "started_at": job.started_at,
        "finished_at": job.finished_at,
        "progress": progress,
    }


def _normalize_label(val: Optional[str]) -> Optional[str]:
    if val is None:
        return None
    t = str(val).strip().lower()
    if t in {"ambiguous", "amb", "a"}:
        return "Ambiguous"
    if t in {"unambiguous", "unamb", "u"}:
        return "Unambiguous"
    return None


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
        pred_norm = _normalize_label(r.pred_class) or "Ambiguous"
        gold_norm = _normalize_label(r.gold_class)
        items.append({
            "id": r.sid,
            "sentence": r.sentence,
            "gold_class": gold_norm,
            "pred_class": pred_norm,
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
    job = db.get(EvalLabJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="task/run not found")
    # Guard: not ready -> 409
    if not job.finished_at or job.finished < job.total:
        raise HTTPException(status_code=409, detail="Not ready. Poll Request /api/eval-lab/jobs/{job_id}/state")
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
    job = db.get(EvalLabJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="task/run not found")
    # Guard: not ready -> 409
    if not job.finished_at or job.finished < job.total:
        raise HTTPException(status_code=409, detail="Not ready. Poll request /api/eval-lab/jobs/{job_id}/state")
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