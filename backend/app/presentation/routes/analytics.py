from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.setup import get_db
from sqlalchemy import text
from typing import List, Optional

router = APIRouter()

@router.get("/analytics/kpi")
def get_kpi_analytics(db: Session = Depends(get_db)):
    try:
        total_contracts_query = text("SELECT COUNT(*) FROM contracts WHERE processing_status = 'completed'")
        total_contracts = db.execute(total_contracts_query).scalar_one_or_none() or 0

        sentences_query = text("SELECT COUNT(*), SUM(CASE WHEN is_ambiguous = 1 THEN 1 ELSE 0 END) FROM contract_sentences")
        total_sentences, ambiguous_sentences = db.execute(sentences_query).first() or (0, 0)

        avg_clarity_query = text("SELECT ROUND(AVG(clarity_score), 2) FROM contract_sentences WHERE clarity_score IS NOT NULL")
        avg_explanation_clarity = db.execute(avg_clarity_query).scalar_one_or_none() or 0.0

        avg_time_query = text("SELECT ROUND(AVG(duration_seconds), 1) FROM analysis_jobs WHERE duration_seconds IS NOT NULL AND status='COMPLETED'")
        avg_analysis_time_sec = db.execute(avg_time_query).scalar_one_or_none() or 0.0

        return {
            "total_contracts": total_contracts,
            "total_sentences": total_sentences or 0,
            "ambiguous_sentences": ambiguous_sentences or 0,
            "avg_explanation_clarity": avg_explanation_clarity,
            "avg_analysis_time_sec": avg_analysis_time_sec,
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