from __future__ import annotations
from typing import List, Optional, Literal, Dict, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, timezone
import math

from ..services.jobs_store import load_uploads_for_job, upsert_uploads_for_job, UploadRecord, parse_dt, DEFAULT_TZ
from ..services.kpi import compute_kpis_period
from ..services.datasets import load_sentences_df, infer_sections
from pathlib import Path

router = APIRouter(tags=["dashboard"])

class BulkUpsertBody(BaseModel):
    uploads: List[UploadRecord] = Field(..., description="Array of upload/job execution records")

@router.post("/jobs/{job_id}/uploads/bulk_upsert")
def bulk_upsert_uploads(job_id: str, body: BulkUpsertBody):
    n = upsert_uploads_for_job(job_id, [u.model_dump() for u in body.uploads])
    return {"job_id": job_id, "upserted": n}

class KPIItem(BaseModel):
    value: Optional[float]
    prev: Optional[float]
    delta_pct: Optional[float] = None
    delta_diff: Optional[float] = None

class KPIsResponse(BaseModel):
    total_contracts_processed: KPIItem
    sentences_classified: KPIItem
    ambiguous_sentences_count: KPIItem
    avg_explanation_clarity: KPIItem
    avg_analysis_time_minutes: KPIItem

def _date_range(mode: Literal["last30","this_month","custom"], since: Optional[str], until: Optional[str]):
    now = datetime.now(DEFAULT_TZ)
    if mode == "last30":
        end = now
        start = end - timedelta(days=30)
    elif mode == "this_month":
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end = now
    else:
        if not since or not until:
            raise HTTPException(400, "custom mode requires since & until (ISO)")
        start = parse_dt(since)
        end = parse_dt(until)
        if start is None or end is None:
            raise HTTPException(400, "Invalid since/until; expected ISO-8601 datetime")
    return start, end

@router.get("/jobs/{job_id}/kpis", response_model=KPIsResponse)
def get_kpis(job_id: str,
             mode: Literal["last30","this_month","custom"] = "last30",
             since: Optional[str] = None,
             until: Optional[str] = None):
    start, end = _date_range(mode, since, until)
    uploads = load_uploads_for_job(job_id)
    return compute_kpis_period(uploads, start, end)

class RecentUploadRow(BaseModel):
    filename: str
    type: str
    uploaded_at: str
    status: Literal["QUEUED","PROCESSING","COMPLETED","FAILED"]
    analysis_summary: Optional[str] = None
    progress_pct: Optional[float] = None
    ambiguous_count: Optional[int] = None
    total_sentences: Optional[int] = None
    avg_explanation_clarity: Optional[float] = None
    duration_seconds: Optional[float] = None
    actions: Dict[str, Any] = {}

class RecentUploadsResponse(BaseModel):
    rows: List[RecentUploadRow]

@router.get("/jobs/{job_id}/uploads/recent", response_model=RecentUploadsResponse)
def recent_uploads(job_id: str, limit: int = Query(20, ge=1, le=200)):
    uploads = load_uploads_for_job(job_id)
    # Sort by uploaded_at desc
    def _sort_key(u: Dict[str, Any]):
        dt = parse_dt(u.get("uploaded_at") or u.get("started_at"))
        return dt or datetime(1970, 1, 1, tzinfo=DEFAULT_TZ)
    uploads = sorted(uploads, key=_sort_key, reverse=True)[:limit]
    rows: List[Dict[str, Any]] = []
    for u in uploads:
        row = {
            "filename": u.get("filename",""),
            "type": u.get("type",""),
            "uploaded_at": u.get("uploaded_at") or u.get("started_at") or "",
            "status": u.get("status","QUEUED"),
            "analysis_summary": u.get("analysis_summary"),
            "progress_pct": u.get("progress_pct"),
            "ambiguous_count": u.get("ambiguous_count"),
            "total_sentences": u.get("total_sentences"),
            "avg_explanation_clarity": u.get("avg_explanation_clarity"),
            "duration_seconds": u.get("duration_seconds") if u.get("duration_seconds") is not None else _calc_duration(u),
            "actions": u.get("actions") or {},
        }
        rows.append(row)
    return {"rows": rows}

def _calc_duration(u: Dict[str, Any]) -> Optional[float]:
    try:
        if u.get("finished_at") and u.get("started_at"):
            tf = parse_dt(u["finished_at"])
            ts = parse_dt(u["started_at"])
            if tf is None or ts is None:
                return None
            dt = tf - ts
            return max(0.0, dt.total_seconds())
    except Exception:
        return None
    return None
