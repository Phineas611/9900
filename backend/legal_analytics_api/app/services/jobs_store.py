from __future__ import annotations
from typing import Dict, Any, List, Optional, Literal
from pathlib import Path
import json
from datetime import datetime, timezone

DATA_ROOT = Path(__file__).resolve().parents[2] / "storage" / "jobs"

DEFAULT_TZ = timezone.utc  

def _job_dir(job_id: str) -> Path:
    d = DATA_ROOT / job_id
    d.mkdir(parents=True, exist_ok=True)
    return d

def parse_dt(s: Optional[str]) -> Optional[datetime]:
    """Parse a datetime string robustly and return a tz-aware datetime.

    - Returns None for empty/None/obviously invalid inputs.
    - Accepts ISO-8601 with 'Z' or offsets, with/without fractional seconds.
    - For naive results, attaches DEFAULT_TZ.
    """
    if s is None:
        return None
    if not isinstance(s, str):
        return None
    s = s.strip()
    if not s:
        return None
    # Common placeholder/invalid tokens seen in bad data
    if s.lower() in {"string", "null", "none", "na", "n/a", "nan"}:
        return None

    # ISO-8601 with 'Z' suffix
    if s.endswith("Z"):
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=DEFAULT_TZ)
            return dt
        except Exception:
            pass

    # Generic ISO-8601 parse
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=DEFAULT_TZ)
        return dt
    except Exception:
        pass

    # Fallback formats
    fmts = [
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ]
    for fmt in fmts:
        try:
            dt = datetime.strptime(s, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=DEFAULT_TZ)
            return dt
        except Exception:
            continue

    # Unable to parse
    return None

def _uploads_path(job_id: str) -> Path:
    return _job_dir(job_id) / "uploads.jsonl"

def load_uploads_for_job(job_id: str) -> List[Dict[str, Any]]:
    p = _uploads_path(job_id)
    if not p.exists():
        return []
    out: List[Dict[str, Any]] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: 
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out

def upsert_uploads_for_job(job_id: str, uploads: List[Dict[str, Any]]) -> int:
    # upsert by filename + uploaded_at
    existing_list = load_uploads_for_job(job_id)
    existing = {(u.get("filename",""), u.get("uploaded_at","")): i for i, u in enumerate(existing_list)}
    arr: List[Dict[str, Any]] = existing_list[:]
    for u in uploads:
        key = (u.get("filename",""), u.get("uploaded_at",""))
        if key in existing:
            idx = existing[key]
            arr[idx] = {**arr[idx], **u}
        else:
            arr.append(u)
    # write back
    p = _uploads_path(job_id)
    with p.open("w", encoding="utf-8") as f:
        for u in arr:
            f.write(json.dumps(u, ensure_ascii=False) + "\n")
    return len(uploads)

from pydantic import BaseModel, Field

class UploadRecord(BaseModel):
    filename: str
    type: str = Field(description="PDF/DOCX/TXT...")
    uploaded_at: str = Field(description="ISO-8601 string, e.g., 2025-10-12T09:15:00Z")
    status: Literal["QUEUED","PROCESSING","COMPLETED","FAILED"]
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    progress_pct: Optional[float] = None
    ambiguous_count: Optional[int] = None
    total_sentences: Optional[int] = None
    avg_explanation_clarity: Optional[float] = None
    duration_seconds: Optional[float] = None
    analysis_summary: Optional[str] = None
    actions: Optional[Dict[str, Any]] = None
