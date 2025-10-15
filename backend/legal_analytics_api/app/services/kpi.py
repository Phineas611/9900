from __future__ import annotations
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timedelta

from .jobs_store import parse_dt

def _in_range(ts: Optional[str], start: datetime, end: datetime) -> bool:
    if not ts:
        return False
    t = parse_dt(ts)
    if t is None:
        return False
    return (t >= start) and (t <= end)

def _avg(arr: list[float]) -> Optional[float]:
    arr = [x for x in arr if x is not None]
    return sum(arr)/len(arr) if arr else None

def _delta(curr: Optional[float], prev: Optional[float]) -> tuple[Optional[float], Optional[float]]:
    if curr is None or prev is None:
        return None, None
    if prev == 0:
        return None, curr  # pct undefined, diff only
    pct = (curr - prev) / prev * 100.0
    diff = curr - prev
    return pct, diff

def compute_kpis_period(uploads: List[Dict[str, Any]], start: datetime, end: datetime) -> Dict[str, Any]:
    # Current window
    win = [u for u in uploads if _in_range(u.get("finished_at") or u.get("uploaded_at"), start, end)]
    # Previous window
    span = end - start
    prev_start = start - span
    prev_end = start
    prev = [u for u in uploads if _in_range(u.get("finished_at") or u.get("uploaded_at"), prev_start, prev_end)]

    def total_contracts(arr):  # COMPLETED only
        return sum(1 for u in arr if (u.get("status") == "COMPLETED"))

    def sentences_classified(arr):
        vals = [u.get("total_sentences") for u in arr if u.get("status") == "COMPLETED"]
        return sum(v for v in vals if isinstance(v, (int, float)))

    def ambiguous_count(arr):
        vals = [u.get("ambiguous_count") for u in arr if u.get("status") == "COMPLETED"]
        return sum(v for v in vals if isinstance(v, (int, float)))

    def avg_clarity(arr):
        vals = [u.get("avg_explanation_clarity") for u in arr if u.get("status") == "COMPLETED"]
        vals = [float(v) for v in vals if v is not None]
        return _avg(vals)

    def avg_minutes(arr):
        samples: list[float] = []
        for u in arr:
            if u.get("status") != "COMPLETED":
                continue
            if u.get("duration_seconds") is not None:
                samples.append(float(u["duration_seconds"]) / 60.0)
            elif u.get("finished_at") and u.get("started_at"):
                tf = parse_dt(u["finished_at"]) 
                ts = parse_dt(u["started_at"]) 
                if tf is None or ts is None:
                    continue
                dt = tf - ts
                samples.append(max(0.0, dt.total_seconds()/60.0))
        return _avg(samples)

    curr_vals = {
        "total_contracts_processed": total_contracts(win),
        "sentences_classified": sentences_classified(win),
        "ambiguous_sentences_count": ambiguous_count(win),
        "avg_explanation_clarity": avg_clarity(win),
        "avg_analysis_time_minutes": avg_minutes(win),
    }

    prev_vals = {
        "total_contracts_processed": total_contracts(prev),
        "sentences_classified": sentences_classified(prev),
        "ambiguous_sentences_count": ambiguous_count(prev),
        "avg_explanation_clarity": avg_clarity(prev),
        "avg_analysis_time_minutes": avg_minutes(prev),
    }

    out: Dict[str, Any] = {}
    for k in curr_vals:
        curr = curr_vals[k]
        prevv = prev_vals[k]
        pct, diff = _delta(curr, prevv)
        out[k] = {
            "value": curr if curr is not None else None,
            "prev": prevv if prevv is not None else None,
            "delta_pct": pct,
            "delta_diff": diff,
        }
    return out
