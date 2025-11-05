from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database.setup import get_db
from sqlalchemy import text, delete
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from app.application.auth import get_current_user  
from pathlib import Path
import pandas as pd
from uuid import uuid4
from app.database.models.analysis_job import AnalysisJob
from app.database.models.contract_sentence import ContractSentence
from app.persistence.contract_repository import get_contract_by_id
from app.application.services.analytics_service import AnalyticsService
from fastapi.responses import StreamingResponse
from app.application.models.analytics import (
    TrendChartResponse, RecurringPhrasesResponse,
    ContractsListResponse, ContractStatsResponse,
    ExtractedSentencesResponse, ReportsData, ExportReportRequest
)
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

        # Sentences and ambiguous counts — aggregate from contract_sentences per contracts
        sentences_query_cur = text(
            """
            SELECT COUNT(*) AS total_sentences,
                   SUM(CASE WHEN is_ambiguous = 1 OR is_ambiguous IS TRUE THEN 1 ELSE 0 END) AS ambiguous_sentences
            FROM contract_sentences cs
            JOIN contracts c ON c.id = cs.contract_id
            WHERE c.processing_status = 'completed'
              AND cs.created_at BETWEEN :start AND :end
            """
        )
        s_cur_row = db.execute(sentences_query_cur, {"start": cur_start, "end": now}).first()
        total_sentences_cur = (s_cur_row[0] if s_cur_row and s_cur_row[0] is not None else 0)
        ambiguous_sentences_cur = (s_cur_row[1] if s_cur_row and s_cur_row[1] is not None else 0)

        sentences_query_prev = text(
            """
            SELECT COUNT(*) AS total_sentences,
                   SUM(CASE WHEN is_ambiguous = 1 OR is_ambiguous IS TRUE THEN 1 ELSE 0 END) AS ambiguous_sentences
            FROM contract_sentences cs
            JOIN contracts c ON c.id = cs.contract_id
            WHERE c.processing_status = 'completed'
              AND cs.created_at BETWEEN :start AND :end
            """
        )
        s_prev_row = db.execute(sentences_query_prev, {"start": prev_start, "end": prev_end}).first()
        total_sentences_prev = (s_prev_row[0] if s_prev_row and s_prev_row[0] is not None else 0)
        ambiguous_sentences_prev = (s_prev_row[1] if s_prev_row and s_prev_row[1] is not None else 0)

        # Average explanation clarity — aggregate from contract_sentences
        avg_clarity_query_cur = text(
            """
            SELECT ROUND(AVG(cs.clarity_score), 2)
            FROM contract_sentences cs
            JOIN contracts c ON c.id = cs.contract_id
            WHERE c.processing_status = 'completed'
              AND cs.clarity_score IS NOT NULL
              AND cs.created_at BETWEEN :start AND :end
            """
        )
        avg_explanation_clarity_cur = db.execute(avg_clarity_query_cur, {"start": cur_start, "end": now}).scalar_one_or_none() or 0.0

        avg_clarity_query_prev = text(
            """
            SELECT ROUND(AVG(cs.clarity_score), 2)
            FROM contract_sentences cs
            JOIN contracts c ON c.id = cs.contract_id
            WHERE c.processing_status = 'completed'
              AND cs.clarity_score IS NOT NULL
              AND cs.created_at BETWEEN :start AND :end
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
              (SELECT aj.id 
               FROM analysis_jobs aj 
               WHERE aj.contract_id = c.id 
                 AND aj.status = 'COMPLETED'
               ORDER BY aj.finished_at DESC 
               LIMIT 1) AS job_id,
              c.id AS contract_id,
              c.file_name,
              c.file_type,
              c.created_at AS uploaded_at,
              c.processing_status AS status,
              COALESCE(
                  (SELECT aj.total_sentences 
                   FROM analysis_jobs aj 
                   WHERE aj.contract_id = c.id 
                     AND aj.status = 'COMPLETED'
                   ORDER BY aj.finished_at DESC 
                   LIMIT 1),
                  0
              ) AS total_sentences
            FROM contracts c
            WHERE c.processing_status IN ('completed', 'processing', 'pending')
            ORDER BY c.created_at DESC
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


@router.post("/contracts/{contract_id}/sentences/import")
def import_contract_sentences(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:

        contract = get_contract_by_id(db, contract_id, current_user.id)
        if not contract:
            raise HTTPException(status_code=404, detail="Contract not found")


        backend_dir = Path(__file__).resolve().parents[3]
        output_root = backend_dir / "outputs" / str(current_user.id) / str(contract_id)

        if not output_root.exists():
            raise HTTPException(status_code=404, detail="Output directory not found")


        csv_path = None
        root_outputs_dir = output_root
        root_csv = root_outputs_dir / "sentences.csv"  
        if root_csv.exists():
            csv_path = root_csv
        else:

            for p in output_root.iterdir():
                if p.is_dir():
                    candidate = p / "sentences.csv"
                    if candidate.exists():
                        csv_path = candidate
                        break

        if not csv_path:
            raise HTTPException(status_code=404, detail="Sentences CSV not found in outputs")

    
        df = pd.read_csv(csv_path, encoding="utf-8")
        if df.empty:
            raise HTTPException(status_code=400, detail="CSV is empty")


        job_id = str(uuid4())
        job = AnalysisJob(
            id=job_id,
            user_id=current_user.id,
            contract_id=contract_id,
            file_name=contract.file_name,
            file_type=contract.file_type,
            file_size=contract.file_size,
            status="COMPLETED",
            uploaded_at=datetime.now(timezone.utc),
            started_at=datetime.now(timezone.utc),
            finished_at=datetime.now(timezone.utc),
            progress_pct=100.0,
            total_sentences=int(len(df)),
            ambiguous_count=0,
            avg_explanation_clarity=None,
            duration_seconds=0.0,
            analysis_summary=None,
            actions=None
        )
        db.add(job)
        db.commit()


        # Update or insert sentences - preserve existing analysis data
        # Use (page, sentence_id) as key to match unique constraint (contract_id, page, sentence_id)
        existing_sentences = {
            (cs.page, cs.sentence_id): cs
            for cs in db.query(ContractSentence).filter(
                ContractSentence.contract_id == contract_id
            ).all()
        }
        
        objs = []
        for _, row in df.iterrows():
            page = int(row.get("page")) if not pd.isna(row.get("page")) else None
            sentence_id = int(row.get("sentence_id")) if not pd.isna(row.get("sentence_id")) else None
            sentence = str(row.get("sentence") or "")
            
            # Check if sentence already exists by (page, sentence_id) to match unique constraint
            key = (page, sentence_id)
            if key in existing_sentences:
                # Update existing record - only update basic fields, preserve analysis data
                existing = existing_sentences[key]
                existing.job_id = job_id  # Update job_id
                existing.file_name = str(row.get("file_name") or contract.file_name or existing.file_name)
                existing.file_type = str(row.get("file_type") or contract.file_type or existing.file_type)
                # Update sentence text if provided
                if sentence:
                    existing.sentence = sentence
                # Keep existing label, is_ambiguous, explanation, clarity_score, etc.
            else:
                # Create new record
                objs.append(ContractSentence(
                    job_id=job_id,
                    contract_id=contract_id,
                    file_name=str(row.get("file_name") or contract.file_name or ""),
                    file_type=str(row.get("file_type") or contract.file_type or ""),
                    page=page,
                    sentence_id=sentence_id,
                    section=None,
                    subsection=None,
                    sentence=sentence,
                    sentence_vec=None,
                    label=None,
                    is_ambiguous=None,
                    explanation=None,
                    suggested_revision=None,
                    clarity_score=None
                ))
        
        if objs:
            db.bulk_save_objects(objs)
        db.commit()

        return {
            "contract_id": contract_id,
            "job_id": job_id,
            "imported_count": len(objs),
            "csv_path": str(csv_path)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/charts/trends", response_model=TrendChartResponse)
def get_trends_chart(
    range: str = Query("3months", description="Time range: 1month, 3months, 6months, 1year"),
    db: Session = Depends(get_db)
):
    """Get trend chart data"""
    try:
        days_map = {
            "1month": 30,
            "3months": 90,
            "6months": 180,
            "1year": 365
        }
        days = days_map.get(range, 90)
        
        data = AnalyticsService.get_trends_chart_data(db, days)
        return TrendChartResponse(data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/phrases/recurring", response_model=RecurringPhrasesResponse)
def get_recurring_phrases(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get recurring ambiguous phrases"""
    try:
        data = AnalyticsService.get_recurring_phrases_data(db, limit)
        return RecurringPhrasesResponse(data=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contracts", response_model=ContractsListResponse)
def get_contracts(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str = Query(""),
    type: str = Query(""),
    status: str = Query(""),
    db: Session = Depends(get_db)
):
    """Get contracts list with filters and pagination"""
    try:
        return AnalyticsService.get_contracts_list(db, page, limit, search, type, status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contracts/stats", response_model=ContractStatsResponse)
def get_contract_stats(db: Session = Depends(get_db)):
    """Get contract statistics"""
    try:
        return AnalyticsService.get_contract_stats(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/extract/{job_id}", response_model=ExtractedSentencesResponse)
def get_extracted_sentences(job_id: str, db: Session = Depends(get_db)):
    """Get extracted sentences for a job"""
    try:
        return AnalyticsService.get_extracted_sentences(db, job_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/reports/data", response_model=ReportsData)
def get_reports_data(
    range: str = Query("6months", description="Time range: 1month, 3months, 6months"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get complete reports data"""
    try:
        days_map = {
            "1month": 30,
            "3months": 90,
            "6months": 180,
            "1year": 365
        }
        days = days_map.get(range, 180)
        
        data = AnalyticsService.get_reports_data(db, days)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reports/export")
def export_report(
    request: ExportReportRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Export comprehensive analysis report"""
    try:
        buffer = AnalyticsService.export_report(db, request.format)
        
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        
        if request.format == 'csv':
            filename = f"contract_report_{timestamp}.csv"
            media_type = "text/csv"
        elif request.format == 'excel':
            filename = f"contract_report_{timestamp}.xlsx"
            media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        else:
            raise HTTPException(400, f"Unsupported format: {request.format}")
        
        return StreamingResponse(
            buffer,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))