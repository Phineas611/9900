import os
import uuid
import io, json
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
from app.database.models.evaluation_run import EvaluationRun
from app.database.models.evaluation_item import EvaluationItem
from app.database.models.evaluation_aggregate import EvaluationAggregate
from app.database.models.evaluation_judgment import EvaluationJudgment


router = APIRouter(prefix="/eval-lab", tags=["Evaluation Lab"])

# Anchor under backend directory for consistency
BACKEND_DIR = Path(__file__).resolve().parents[3]
DATA_DIR = BACKEND_DIR / os.getenv("DATA_DIR", "data/eval_lab")
DATA_DIR.mkdir(parents=True, exist_ok=True)


RUN_TASKS: Dict[str, asyncio.Task] = {}
JOB_TO_RUN: Dict[str, str] = {}


def _build_assess_request(run_id: str, req: EvalRunRequest, rows_count: int) -> AssessRequest:

    if req.judges:
        jids: List[str] = []
        for j in req.judges:
            try:
                jid = (j or {}).get("id")
            except Exception:
                jid = None
            if isinstance(jid, str):
                jids.append(jid.strip())
        judge_models = jids if jids else DEFAULT_JUDGES[:]
    else:
        judge_models = DEFAULT_JUDGES[:]


    expand = False

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
        expand_judges=expand,
    )


def _norm_class_lower(val: Optional[str]) -> Optional[str]:
    """Normalize class label to 'ambiguous'/'unambiguous' or None."""
    if val is None:
        return None
    t = str(val).strip().lower()
    if t.startswith("amb"):
        return "ambiguous"
    if t.startswith("unamb"):
        return "unambiguous"
    return None


async def _run_in_background(job_id: str, run_id: str, assess_req: AssessRequest):
    """Execute assessment asynchronously, then materialize EvalLabRecord and update job status."""
    db = SessionLocal()
    repo = EvaluationRepository()
    svc = EvaluationService(repo)
    try:
        # Run assess and persist summary to evaluation_runs
        summary = await svc.assess_async(db, user_id=1, req=assess_req)
      
        try:
            repo.finish_run(db, run_id, summary)
        except Exception:
           
            pass

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

        # --- BEGIN OPTIMIZATION ---
        # Pre-fetch all judgments for the run to avoid N+1 queries
        from collections import defaultdict
        from app.database.models.evaluation_judgment import EvaluationJudgment
        all_judgments_query = select(EvaluationJudgment).where(EvaluationJudgment.run_id == run_id)
        all_judgments_results = db.execute(all_judgments_query).scalars().all()
        
        judgments_by_item_pk = defaultdict(list)
        for j in all_judgments_results:
            judgments_by_item_pk[j.item_pk].append(j)
        # --- END OPTIMIZATION ---

        total = 0
        finished = 0
        class_ok_total = 0
        rationale_pass_total = 0

        for item, agg in pairs:
            total += 1
            js = judgments_by_item_pk.get(item.id, [])
            judges_list = []
            class_votes = []
            rationale_votes = []
            for j in js:
                verdict = j.verdict or {}
                class_ok = verdict.get("predicted_class_correct")
                # Fallback: if class_ok missing, derive by gold vs pred; otherwise use judge label versus pred
                if not isinstance(class_ok, bool):
                    pred_norm = _norm_class_lower(getattr(item, "predicted_label", None))
                    gold_norm = _norm_class_lower(getattr(item, "gold_label", None))
                    judge_norm = _norm_class_lower(verdict.get("judge_label"))
                    if gold_norm is not None and pred_norm is not None:
                        class_ok = (pred_norm == gold_norm)
                    elif judge_norm is not None and pred_norm is not None:
                        class_ok = (judge_norm == pred_norm)
                    else:
                        class_ok = None
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


# Removed legacy Job Status endpoint in favor of /jobs/{job_id}/state


@router.get("/jobs/{job_id}/state")
def job_state(job_id: str, db: Session = Depends(get_db)):
    job = db.get(EvalLabJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="task/run not found")


    status: str
    if job.finished_at:
        status = "completed"
    elif job.started_at:
        status = "processing"
    else:
        status = "pending"


    run: Optional[EvaluationRun] = None
    try:
        run = db.execute(
            select(EvaluationRun)
            .where(EvaluationRun.config["job_id"].as_string() == job_id)
            .order_by(EvaluationRun.created_at.desc())
        ).scalars().first()
    except Exception:
        run = None
    if run is None:
        try:
            run = db.execute(
                select(EvaluationRun)
                .where(EvaluationRun.file_name == os.path.basename(job.file_path))
                .order_by(EvaluationRun.created_at.desc())
            ).scalars().first()
        except Exception:
            run = None


    message: Optional[str] = None
    if run:
        st = (run.status or "").upper()
        if st.startswith("FAILED"):
            status = "failed"
            message = run.summary or run.status or "Failed"
        elif st == "DONE":
            status = "completed"
            message = "Completed"
        elif st == "PROCESSING":
            status = "processing"
            message = "Processing"
        elif st == "QUEUED":
            status = "pending"
            message = "Queued"


    progress_obj: Optional[dict] = None
    if run:
        try:
            total_items = db.execute(
                select(func.count()).select_from(
                    select(EvaluationItem)
                    .where(EvaluationItem.run_id == run.id)
                    .subquery()
                )
            ).scalar_one()
            done_aggs = db.execute(
                select(func.count()).select_from(
                    select(EvaluationAggregate)
                    .where(EvaluationAggregate.run_id == run.id)
                    .subquery()
                )
            ).scalar_one()
            if total_items and total_items > 0:
                progress_obj = {"current": int(done_aggs or 0), "total": int(total_items)}
        except Exception:
            progress_obj = None

    if progress_obj is None and job.total and job.total > 0:
        progress_obj = {"current": int(job.finished or 0), "total": int(job.total)}


    started_at = job.started_at
    finished_at = job.finished_at
    if run:
        try:
            if run.created_at:
                started_at = run.created_at
            if run.finished_at:
                finished_at = run.finished_at
        except Exception:
            pass

 
    if message is None:
        if status == "pending":
            message = "Queued"
        elif status == "processing":
            message = "Processing"
        elif status == "completed":
            message = "Completed"
        elif status == "failed":
            message = "Failed"

    try:
        if progress_obj and int(progress_obj.get("total") or 0) > 0:
            cur = int(progress_obj.get("current") or 0)
            tot = int(progress_obj.get("total") or 0)
            if cur >= tot:
                status = "completed"
                if message is None or message.lower() != "completed":
                    message = "Completed"
    except Exception:
        pass

    return {
        "task_id": job_id,
        "status": status,
        "progress": progress_obj,
        "message": message,
        "started_at": started_at,
        "finished_at": finished_at,
        # Include metrics_summary so frontend no longer needs the removed /jobs/{job_id}
        "metrics_summary": job.metrics_summary or {},
        "judges": job.judges,
        "rubrics": job.rubrics,
        "custom_metrics": job.custom_metrics,
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


def hf_raw_stats(run_id: str, judge_id: str, sample_limit: int = Query(5, ge=1, le=50), db: Session = Depends(get_db)):
    rows = db.execute(
        select(EvaluationJudgment).where((EvaluationJudgment.run_id == run_id) & (EvaluationJudgment.judge_model == judge_id))
    ).scalars().all()
    required = ["grammar","word_choice","cohesion","conciseness","completeness","correctness","clarity"]
    total = len(rows)
    raw_total = 0
    missing = 0
    complete = 0
    neg = {k: 0 for k in required}
    denom = {k: 0 for k in required}
    samples = []
    for j in rows[:sample_limit]:
        raw = j.raw or {}
        txt = None
        if isinstance(raw, list) and raw:
            v0 = raw[0] or {}
            txt = v0.get("generated_text")
        elif isinstance(raw, dict):
            txt = raw.get("generated_text")
        parsed = None
        if isinstance(txt, str):
            raw_total += 1
            try:
                parsed = json.loads(txt)
            except Exception:
                parsed = None
        if parsed is None and not isinstance(txt, str):
            obj = j.verdict or {}
            rub = (obj.get("rubric") or {})
            missdims = []
        else:
            obj = parsed if parsed else {}
            rub = (obj.get("rubric") or {})
            missdims = [k for k in required if k not in rub]
        if missdims:
            missing += 1
        elif rub:
            complete += 1
            for k in required:
                leaf = (rub.get(k) or {})
                v = leaf.get("pass")
                if isinstance(v, bool):
                    denom[k] += 1
                    if not v:
                        neg[k] += 1
        samples.append({"item_pk": j.item_pk, "generated_text": (txt[:300] if isinstance(txt, str) else None), "missing_dims": missdims})
    rates = {k: (neg[k] / denom[k] if denom[k] else None) for k in required}
    return {
        "run_id": run_id,
        "judge_id": judge_id,
        "total": total,
        "raw_count": raw_total,
        "missing_key_count": missing,
        "missing_key_rate": (missing / raw_total if raw_total else None),
        "complete_count": complete,
        "true_negative_rate_by_dim": rates,
        "samples": samples,
    }