from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.setup import get_db
from sqlalchemy import text
from typing import List, Optional
from datetime import datetime, timedelta, timezone

router = APIRouter()

@router.get("/analytics/kpi")
def get_kpi_analytics(db: Session = Depends(get_db)):
    try:
        # Define windows for trend calculation: last 30 days vs previous 30 days
        now = datetime.now(timezone.utc)
        cur_start = now - timedelta(days=30)
        prev_start = now - timedelta(days=60)
        prev_end = cur_start

        # Helper: delta percentage and difference
        def pct(v: Optional[float], p: Optional[float]) -> Optional[float]:
            try:
                if p is None or p == 0 or v is None:
                    return None
                return round(((float(v) - float(p)) / float(p)) * 100, 1)
            except Exception:
                return None

        def diff(v: Optional[float], p: Optional[float]) -> Optional[float]:
            try:
                if v is None or p is None:
                    return None
                return round(float(v) - float(p), 2)
            except Exception:
                return None

        # Contracts processed (current window)
        total_contracts_query_cur = text(
            """
            SELECT COUNT(*) FROM contracts
            WHERE processing_status = 'completed'
              AND processed_at IS NOT NULL
              AND processed_at BETWEEN :start AND :end
            """
        )
        total_contracts_cur = db.execute(total_contracts_query_cur, {"start": cur_start, "end": now}).scalar_one_or_none() or 0

        # Contracts processed (previous window)
        total_contracts_query_prev = text(
            """
            SELECT COUNT(*) FROM contracts
            WHERE processing_status = 'completed'
              AND processed_at IS NOT NULL
              AND processed_at BETWEEN :start AND :end
            """
        )
        total_contracts_prev = db.execute(total_contracts_query_prev, {"start": prev_start, "end": prev_end}).scalar_one_or_none() or 0

        # Sentences and ambiguous counts — aggregate from analysis_jobs per completed jobs (trend windows)
        sentences_query_cur = text(
            """
            SELECT COALESCE(SUM(total_sentences),0) AS total_sentences,
                   COALESCE(SUM(ambiguous_count),0) AS ambiguous_sentences
            FROM analysis_jobs
            WHERE status = 'COMPLETED'
              AND finished_at IS NOT NULL
              AND finished_at BETWEEN :start AND :end
            """
        )
        s_cur_row = db.execute(sentences_query_cur, {"start": cur_start, "end": now}).first()
        total_sentences_cur = (s_cur_row[0] if s_cur_row and s_cur_row[0] is not None else 0)
        ambiguous_sentences_cur = (s_cur_row[1] if s_cur_row and s_cur_row[1] is not None else 0)

        sentences_query_prev = text(
            """
            SELECT COALESCE(SUM(total_sentences),0) AS total_sentences,
                   COALESCE(SUM(ambiguous_count),0) AS ambiguous_sentences
            FROM analysis_jobs
            WHERE status = 'COMPLETED'
              AND finished_at IS NOT NULL
              AND finished_at BETWEEN :start AND :end
            """
        )
        s_prev_row = db.execute(sentences_query_prev, {"start": prev_start, "end": prev_end}).first()
        total_sentences_prev = (s_prev_row[0] if s_prev_row and s_prev_row[0] is not None else 0)
        ambiguous_sentences_prev = (s_prev_row[1] if s_prev_row and s_prev_row[1] is not None else 0)

        # Average explanation clarity — prefer job-level aggregated clarity per completed jobs
        avg_clarity_query_cur = text(
            """
            SELECT ROUND(AVG(avg_explanation_clarity), 2)
            FROM analysis_jobs
            WHERE status = 'COMPLETED'
              AND avg_explanation_clarity IS NOT NULL
              AND finished_at IS NOT NULL
              AND finished_at BETWEEN :start AND :end
            """
        )
        avg_explanation_clarity_cur = db.execute(avg_clarity_query_cur, {"start": cur_start, "end": now}).scalar_one_or_none() or 0.0

        avg_clarity_query_prev = text(
            """
            SELECT ROUND(AVG(avg_explanation_clarity), 2)
            FROM analysis_jobs
            WHERE status = 'COMPLETED'
              AND avg_explanation_clarity IS NOT NULL
              AND finished_at IS NOT NULL
              AND finished_at BETWEEN :start AND :end
            """
        )
        avg_explanation_clarity_prev = db.execute(avg_clarity_query_prev, {"start": prev_start, "end": prev_end}).scalar_one_or_none() or 0.0

        # Average analysis time seconds — completed jobs in windows
        avg_time_query_cur = text(
            """
            SELECT ROUND(AVG(duration_seconds), 1)
            FROM analysis_jobs
            WHERE status='COMPLETED'
              AND duration_seconds IS NOT NULL
              AND finished_at IS NOT NULL
              AND finished_at BETWEEN :start AND :end
            """
        )
        avg_analysis_time_sec_cur = db.execute(avg_time_query_cur, {"start": cur_start, "end": now}).scalar_one_or_none() or 0.0

        avg_time_query_prev = text(
            """
            SELECT ROUND(AVG(duration_seconds), 1)
            FROM analysis_jobs
            WHERE status='COMPLETED'
              AND duration_seconds IS NOT NULL
              AND finished_at IS NOT NULL
              AND finished_at BETWEEN :start AND :end
            """
        )
        avg_analysis_time_sec_prev = db.execute(avg_time_query_prev, {"start": prev_start, "end": prev_end}).scalar_one_or_none() or 0.0

        return {
            # current window values (original keys kept for backward compatibility)
            "total_contracts": total_contracts_cur,
            "total_sentences": total_sentences_cur,
            "ambiguous_sentences": ambiguous_sentences_cur,
            "avg_explanation_clarity": avg_explanation_clarity_cur,
            "avg_analysis_time_sec": avg_analysis_time_sec_cur,

            # trend fields for frontend UI
            "growth_percentage": pct(total_contracts_cur, total_contracts_prev) or 0,
            "certificates_change_pct": pct(total_sentences_cur, total_sentences_prev) or 0,
            "score_change": diff(avg_explanation_clarity_cur, avg_explanation_clarity_prev) or 0,
            "time_change_pct": pct(avg_analysis_time_sec_cur, avg_analysis_time_sec_prev) or 0,

            # optional: previous window values (can be used later if needed)
            "_prev": {
                "total_contracts": total_contracts_prev,
                "total_sentences": total_sentences_prev,
                "ambiguous_sentences": ambiguous_sentences_prev,
                "avg_explanation_clarity": avg_explanation_clarity_prev,
                "avg_analysis_time_sec": avg_analysis_time_sec_prev,
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/uploads/recent")
def get_recent_uploads(limit: int = 20, db: Session = Depends(get_db)):
    try:
        query = text("""
            SELECT 
              aj.id       AS job_id, 
              c.id        AS contract_id, 
              aj.file_name, 
              aj.file_type, 
              aj.uploaded_at, 
              aj.status, 
              COALESCE(aj.total_sentences, 0) AS total_sentences 
            FROM analysis_jobs aj 
            JOIN contracts c ON c.id = aj.contract_id 
            ORDER BY aj.uploaded_at DESC 
            LIMIT :limit
        """)
        result = db.execute(query, {"limit": limit}).fetchall()

        uploads = [dict(row._mapping) for row in result]
        return uploads
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/contracts/{contract_id}/sentences")
def get_contract_sentences(
    contract_id: int, 
    limit: int = 100, 
    offset: int = 0, 
    db: Session = Depends(get_db)
):
    try:
        query = text("""
            SELECT page, sentence_id, sentence, label, is_ambiguous, clarity_score, section, subsection 
            FROM contract_sentences 
            WHERE contract_id = :cid
            ORDER BY page, sentence_id
            LIMIT :limit OFFSET :offset
        """)
        result = db.execute(query, {"cid": contract_id, "limit": limit, "offset": offset}).fetchall()

        sentences = [dict(row._mapping) for row in result]
        return sentences
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/activity/recent")
def get_recent_activity(limit: int = 20, db: Session = Depends(get_db)):
    try:
        query = text("""
            SELECT id, user_id, event_type, title, message, created_at
            FROM activity_logs
            ORDER BY created_at DESC
            LIMIT :limit
        """)
        result = db.execute(query, {"limit": limit}).fetchall()

        activities = [dict(row._mapping) for row in result]
        return activities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
