from __future__ import annotations
from typing import Dict, Any, List, Optional, Literal
from pathlib import Path
import json
from datetime import datetime, timezone

DATA_ROOT = Path(__file__).resolve().parents[2] / "storage" / "jobs"

DEFAULT_TZ = timezone.utc  # 生产可换成本地时区

def _job_dir(job_id: str) -> Path:
    d = DATA_ROOT / job_id
    d.mkdir(parents=True, exist_ok=True)
    return d

def parse_dt(s: str) -> datetime:
    # Accept 'Z' suffix or offset-aware; fallback
    if s.endswith("Z"):
        return datetime.fromisoformat(s.replace("Z","+00:00"))
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%S")

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
