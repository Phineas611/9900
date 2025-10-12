from __future__ import annotations
from pathlib import Path
from typing import Optional, Literal, List, Dict, Any
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field
import io
import pandas as pd

from ..services.datasets import load_sentences_df, infer_sections, compute_summary,     to_pages_vs_contracts_df, to_sentence_length_hist_df, to_avg_sentence_length_hist_df,     to_section_counts_df, to_subsection_counts_df, to_contracts_scatter_df

router = APIRouter(tags=["analytics"])

DATA_ROOT = Path(__file__).resolve().parents[2] / "storage" / "jobs"

class RegisterBody(BaseModel):
    outputs_dir: str = Field(..., description="Filesystem path to a directory that contains sentences.csv")

@router.post("/jobs/{job_id}/register")
def register_outputs(job_id: str, body: RegisterBody):
    out_dir = Path(body.outputs_dir).resolve()
    if not out_dir.exists():
        raise HTTPException(400, f"outputs_dir not found: {out_dir}")
    csv = out_dir / "sentences.csv"
    if not csv.exists():
        raise HTTPException(400, f"sentences.csv not found under: {out_dir}")
    job_dir = DATA_ROOT / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    # Link or copy: we use a small 'pointer' file that stores the path.
    (job_dir / "pointer.txt").write_text(str(out_dir), encoding="utf-8")
    return {"job_id": job_id, "registered_outputs": str(out_dir)}

def _resolve_csv(job_id: str) -> Path:
    job_dir = DATA_ROOT / job_id
    pointer = job_dir / "pointer.txt"
    if not pointer.exists():
        raise HTTPException(404, f"job not registered: {job_dir}")
    out_dir = Path(pointer.read_text(encoding='utf-8').strip())
    csv = out_dir / "sentences.csv"
    if not csv.exists():
        raise HTTPException(404, f"sentences.csv missing for job {job_id}: {csv}")
    return csv

class SummaryResponse(BaseModel):
    metadata: Dict[str, Any]
    page_length_hist: Dict[str, Any]
    sentence_length_hist: Dict[str, Any]
    avg_sentence_length_hist: Dict[str, Any]
    contracts_scatter: List[Dict[str, Any]]
    section_frequency: List[Dict[str, Any]]
    subsection_frequency: List[Dict[str, Any]]
    sentence_length_box: Dict[str, Any]

@router.get("/jobs/{job_id}/analytics/summary", response_model=SummaryResponse)
def analytics_summary(job_id: str, bins_pages: int = 10, bins_sentence: int = 20, topk: int = 20):
    csv = _resolve_csv(job_id)
    df = load_sentences_df(csv)
    df = infer_sections(df)  # fill section/subsection if missing

    summary = compute_summary(df, bins_pages=bins_pages, bins_sentence=bins_sentence, topk=topk)
    return summary

DownloadKind = Literal[
    "pages_vs_contracts", "sentence_length_hist", "avg_sentence_length_hist",
    "section_counts", "subsection_counts", "contracts_scatter"
]

@router.get("/jobs/{job_id}/analytics/download/{kind}")
def analytics_download(job_id: str, kind: DownloadKind):
    csv = _resolve_csv(job_id)
    df = load_sentences_df(csv)
    df = infer_sections(df)

    if kind == "pages_vs_contracts":
        out = to_pages_vs_contracts_df(df)
    elif kind == "sentence_length_hist":
        out = to_sentence_length_hist_df(df)
    elif kind == "avg_sentence_length_hist":
        out = to_avg_sentence_length_hist_df(df)
    elif kind == "section_counts":
        out = to_section_counts_df(df)
    elif kind == "subsection_counts":
        out = to_subsection_counts_df(df)
    elif kind == "contracts_scatter":
        out = to_contracts_scatter_df(df)
    else:
        raise HTTPException(400, f"Unknown kind: {kind}")

    buf = io.StringIO()
    out.to_csv(buf, index=False)
    buf.seek(0)
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv",
                             headers={"Content-Disposition": f'attachment; filename="{kind}.csv"'})
