# backend/app/persistence/analytics_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Tuple, Optional
from datetime import datetime


class AnalyticsRepository:
    
    @staticmethod
    def get_monthly_data(db: Session, start_date: datetime) -> List[Tuple[str, int, float]]:
        """Get monthly contract count and ambiguity rate - only count analyzed sentences"""
        query = text("""
            SELECT 
                strftime('%Y-%m', cs.created_at) AS month,
                COUNT(DISTINCT cs.contract_id) AS contracts,
                COALESCE(
                    ROUND(100.0 * SUM(CASE WHEN cs.is_ambiguous = 1 OR cs.is_ambiguous IS TRUE THEN 1 ELSE 0 END) / NULLIF(COUNT(cs.id), 0), 2),
                    0
                ) AS ambiguity_rate
            FROM contract_sentences cs
            JOIN contracts c ON c.id = cs.contract_id
            WHERE cs.created_at >= :start_date
              AND c.processing_status = 'completed'
              AND cs.is_ambiguous IS NOT NULL
            GROUP BY strftime('%Y-%m', cs.created_at)
            ORDER BY month ASC
        """)
        return db.execute(query, {"start_date": start_date}).fetchall()
    
    @staticmethod
    def get_quality_scores(db: Session, start_date: datetime) -> List[Tuple[str, float]]:
        """Get quality scores (clarity) by month - use sentence creation date for grouping"""
        query = text("""
            SELECT 
                strftime('%Y-%m', cs.created_at) AS month,
                ROUND(AVG(cs.clarity_score), 2) AS score
            FROM contract_sentences cs
            JOIN contracts c ON c.id = cs.contract_id
            WHERE (c.created_at >= :start_date OR cs.created_at >= :start_date)
              AND c.processing_status = 'completed'
              AND cs.clarity_score IS NOT NULL
            GROUP BY strftime('%Y-%m', cs.created_at)
            ORDER BY month ASC
        """)
        return db.execute(query, {"start_date": start_date}).fetchall()
    
    @staticmethod
    def get_contract_types(db: Session, start_date: datetime) -> List[Tuple[str, int, float]]:
        """Get contract statistics grouped by file type"""
        query = text("""
            SELECT 
                c.file_type AS type,
                COUNT(DISTINCT c.id) AS value,
                COALESCE(
                    ROUND(100.0 * SUM(CASE WHEN cs.is_ambiguous = 1 OR cs.is_ambiguous IS TRUE THEN 1 ELSE 0 END) / NULLIF(COUNT(cs.id), 0), 2),
                    0
                ) AS ambiguity
            FROM contracts c
            LEFT JOIN contract_sentences cs ON cs.contract_id = c.id
            WHERE c.created_at >= :start_date
              AND c.processing_status = 'completed'
            GROUP BY c.file_type
            ORDER BY value DESC
        """)
        return db.execute(query, {"start_date": start_date}).fetchall()
    
    @staticmethod
    def get_recurring_sentences(db: Session, limit: int) -> List[Tuple[str, int]]:
        """Get recurring ambiguous sentences"""
        query = text("""
            SELECT 
                sentence,
                COUNT(*) AS frequency
            FROM contract_sentences
            WHERE is_ambiguous = 1 OR is_ambiguous IS TRUE
              AND sentence IS NOT NULL
            GROUP BY sentence
            HAVING COUNT(*) > 1
            ORDER BY frequency DESC
            LIMIT :limit
        """)
        return db.execute(query, {"limit": limit}).fetchall()
    
    @staticmethod
    def get_contracts_count(db: Session, where_clause: str, params: dict) -> int:
        """Get total count of contracts matching filters"""
        query = text(f"""
            SELECT COUNT(DISTINCT c.id)
            FROM contracts c
            WHERE {where_clause}
        """)
        return db.execute(query, params).scalar_one() or 0
    
    @staticmethod
    def get_contracts_list(
        db: Session, where_clause: str, params: dict, limit: int, offset: int
    ) -> List[Tuple]:
        """Get paginated contracts list with statistics"""
        query = text(f"""
        SELECT 
            c.id,
            c.file_name AS name,
            c.created_at AS date,
            c.file_type AS type,
            COALESCE(
                (SELECT aj.total_sentences 
                 FROM analysis_jobs aj 
                 WHERE aj.contract_id = c.id 
                   AND aj.status = 'COMPLETED'
                 ORDER BY aj.finished_at DESC 
                 LIMIT 1), 
                0
            ) AS sentences,
            COALESCE(
                (SELECT ROUND(100.0 * SUM(CASE WHEN cs2.is_ambiguous = 1 OR cs2.is_ambiguous IS TRUE THEN 1 ELSE 0 END) / NULLIF(COUNT(cs2.id), 0), 2)
                 FROM contract_sentences cs2
                 WHERE cs2.contract_id = c.id),
                0
            ) AS ambiguity_rate,
            COALESCE(
                (SELECT ROUND(AVG(cs3.clarity_score), 2)
                 FROM contract_sentences cs3
                 WHERE cs3.contract_id = c.id AND cs3.clarity_score IS NOT NULL),
                (SELECT aj.avg_explanation_clarity
                 FROM analysis_jobs aj 
                 WHERE aj.contract_id = c.id 
                   AND aj.status = 'COMPLETED'
                 ORDER BY aj.finished_at DESC 
                 LIMIT 1),
                0.0
            ) AS quality_score
        FROM contracts c
        WHERE {where_clause}
        ORDER BY c.created_at DESC
        LIMIT :limit OFFSET :offset
    """)
        return db.execute(query, {**params, "limit": limit, "offset": offset}).fetchall()
    
    @staticmethod
    def get_stats_current_window(db: Session, start: datetime, end: datetime) -> Tuple[int, int, float, float]:
        """Get statistics for current time window - only count analyzed sentences"""
        query = text("""
            SELECT 
                COUNT(DISTINCT c.id) AS total_contracts,
                COUNT(DISTINCT cs.id) AS analyzed_sentences,
                COALESCE(
                    ROUND(100.0 * SUM(CASE WHEN cs.is_ambiguous = 1 OR cs.is_ambiguous IS TRUE THEN 1 ELSE 0 END) / NULLIF(SUM(CASE WHEN cs.is_ambiguous IS NOT NULL THEN 1 ELSE 0 END), 0), 2),
                    0
                ) AS average_ambiguity_rate,
                COALESCE(AVG(cs.clarity_score), 0.0) AS average_quality_score
            FROM contracts c
            LEFT JOIN contract_sentences cs ON cs.contract_id = c.id AND cs.is_ambiguous IS NOT NULL
            WHERE c.processing_status = 'completed'
              AND ((c.created_at >= :start AND c.created_at <= :end) OR (cs.created_at >= :start AND cs.created_at <= :end))
        """)
        row = db.execute(query, {"start": start, "end": end}).first()
        return (
            row[0] if row and row[0] else 0,
            row[1] if row and row[1] else 0,
            row[2] if row and row[2] else 0,
            row[3] if row and row[3] else 0
        )
    
    @staticmethod
    def get_job_info(db: Session, job_id: str) -> Optional[Tuple[str, int]]:
        """Get job file name and contract id"""
        query = text("""
            SELECT aj.file_name, aj.contract_id
            FROM analysis_jobs aj
            WHERE aj.id = :job_id
        """)
        row = db.execute(query, {"job_id": job_id}).first()
        return row if row else None
    
    @staticmethod
    def get_sentences_by_job(db: Session, job_id: str) -> List[Tuple]:
        """Get all sentences for a job"""
        query = text("""
            SELECT 
                page,
                sentence_id,
                sentence,
                label,
                is_ambiguous,
                clarity_score,
                explanation
            FROM contract_sentences
            WHERE job_id = :job_id
            ORDER BY page ASC, sentence_id ASC
        """)
        return db.execute(query, {"job_id": job_id}).fetchall()
    
    @staticmethod
    def get_completeness_scores(db: Session, start_date: datetime) -> List[Tuple[str, float]]:
        """Calculate completeness scores by month"""
        query = text("""
            SELECT 
                strftime('%Y-%m', cs.created_at) AS month,
                ROUND(
                    (
                        (SUM(CASE WHEN cs.explanation IS NOT NULL THEN 1 ELSE 0 END) * 4.0 +
                         SUM(CASE WHEN cs.label IS NOT NULL THEN 1 ELSE 0 END) * 3.0 +
                         SUM(CASE WHEN cs.clarity_score IS NOT NULL THEN 1 ELSE 0 END) * 3.0)
                        / NULLIF(COUNT(cs.id) * 10.0, 0)
                    ) * 10, 2
                ) AS completeness_score
            FROM contract_sentences cs
            JOIN contracts c ON c.id = cs.contract_id
            WHERE c.processing_status = 'completed'
              AND cs.created_at >= :start_date
            GROUP BY strftime('%Y-%m', cs.created_at)
            ORDER BY month ASC
        """)
        return db.execute(query, {"start_date": start_date}).fetchall()
    
    @staticmethod
    def get_accuracy_scores(db: Session, start_date: datetime) -> List[Tuple[str, float]]:
        """Calculate accuracy scores by month based on label coverage"""
        query = text("""
            SELECT 
                strftime('%Y-%m', cs.created_at) AS month,
                ROUND(
                    (1.0 - (COUNT(CASE WHEN cs.label IS NULL THEN 1 END) / NULLIF(COUNT(cs.id), 0))) * 10, 2
                ) AS accuracy_score
            FROM contract_sentences cs
            JOIN contracts c ON c.id = cs.contract_id
            WHERE c.processing_status = 'completed'
              AND cs.created_at >= :start_date
            GROUP BY strftime('%Y-%m', cs.created_at)
            ORDER BY month ASC
        """)
        return db.execute(query, {"start_date": start_date}).fetchall()
    
    @staticmethod
    def get_consistency_scores(db: Session, start_date: datetime) -> List[Tuple[str, float]]:
        """Calculate consistency scores by month based on ambiguity rate stability"""
        query = text("""
            WITH monthly_rates AS (
                SELECT 
                    strftime('%Y-%m', cs.created_at) AS month,
                    ROUND(100.0 * SUM(CASE WHEN cs.is_ambiguous = 1 OR cs.is_ambiguous IS TRUE THEN 1 ELSE 0 END) / NULLIF(COUNT(cs.id), 0), 2) AS ambiguity_rate
                FROM contract_sentences cs
                JOIN contracts c ON c.id = cs.contract_id
                WHERE c.processing_status = 'completed'
                  AND cs.created_at >= :start_date
                GROUP BY strftime('%Y-%m', cs.created_at)
            ),
            ranked_rates AS (
                SELECT 
                    month,
                    ambiguity_rate,
                    LAG(ambiguity_rate) OVER (ORDER BY month) AS prev_ambiguity_rate
                FROM monthly_rates
            )
            SELECT 
                month,
                CASE 
                    WHEN prev_ambiguity_rate IS NULL THEN 10.0
                    WHEN (10 - ABS(ambiguity_rate - prev_ambiguity_rate) * 2) < 0 THEN 0.0
                    ELSE ROUND(10 - ABS(ambiguity_rate - prev_ambiguity_rate) * 2, 2)
                END AS consistency_score
            FROM ranked_rates
            ORDER BY month ASC
        """)
        return db.execute(query, {"start_date": start_date}).fetchall()
    
    @staticmethod
    def get_contracts_for_reports(db: Session, start_date: datetime) -> List[Tuple]:
        """Get contract analysis data for reports"""
        query = text("""
            SELECT 
                c.file_name AS name,
                COUNT(DISTINCT cs.id) AS total_sentences,
                SUM(CASE WHEN cs.is_ambiguous = 1 OR cs.is_ambiguous IS TRUE THEN 1 ELSE 0 END) AS ambiguous_sentences,
                COALESCE(
                    ROUND(100.0 * SUM(CASE WHEN cs.is_ambiguous = 1 OR cs.is_ambiguous IS TRUE THEN 1 ELSE 0 END) / NULLIF(COUNT(DISTINCT cs.id), 0), 2), 0
                ) AS percentage
            FROM contracts c
            LEFT JOIN contract_sentences cs ON cs.contract_id = c.id
            WHERE c.processing_status = 'completed'
              AND c.created_at >= :start_date
            GROUP BY c.file_name, c.created_at
            ORDER BY c.created_at DESC
            LIMIT 10
        """)
        return db.execute(query, {"start_date": start_date}).fetchall()