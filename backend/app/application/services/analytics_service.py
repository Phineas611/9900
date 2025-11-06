# backend/app/application/services/analytics_service.py
from sqlalchemy.orm import Session
from typing import List
import io
import pandas as pd
from datetime import datetime, timedelta, timezone
from app.application.models.analytics import (
    TrendChartData, TrendMonthlyData, TrendQualityScore,
    TrendContractType, TrendAmbiguityByType,
    RecurringPhrasesData, AmbiguousPhrase,
    ContractsListResponse, ContractListItem,
    ContractStatsResponse,
    ExtractedSentencesResponse, SentenceItem
)
from app.persistence.analytics_repository import AnalyticsRepository
from app.application.models.analytics import QualityData, AmbiguityTrend, ContractAnalysis, ReportsData

class AnalyticsService:
    
    @staticmethod
    def get_trends_chart_data(db: Session, range_days: int, user_id: int) -> TrendChartData:
        """Get trend chart data"""
        start_date = datetime.now(timezone.utc) - timedelta(days=range_days)
        
        # Get data from repository
        monthly_rows = AnalyticsRepository.get_monthly_data(db, start_date, user_id)
        quality_rows = AnalyticsRepository.get_quality_scores(db, start_date, user_id)
        types_rows = AnalyticsRepository.get_contract_types(db, start_date, user_id)
        
        # Transform to models
        monthly_data = [
            TrendMonthlyData(month=row[0], contracts=row[1], ambiguityRate=row[2])
            for row in monthly_rows
        ]
        
        quality_scores = [
            TrendQualityScore(month=row[0], score=row[1])
            for row in quality_rows
        ]
        
        contract_types = [
            TrendContractType(type=row[0] or "Unknown", value=row[1], ambiguity=row[2])
            for row in types_rows
        ]
        
        ambiguity_by_type = [
            TrendAmbiguityByType(type=t.type, ambiguity=t.ambiguity)
            for t in contract_types
        ]
        
        return TrendChartData(
            monthlyData=monthly_data,
            qualityScores=quality_scores,
            contractTypes=contract_types,
            ambiguityByType=ambiguity_by_type
        )
    
    @staticmethod
    def get_recurring_phrases_data(db: Session, limit: int, user_id: int) -> RecurringPhrasesData:
        """Get recurring ambiguous phrases"""
        phrases_rows = AnalyticsRepository.get_recurring_sentences(db, limit, user_id)
        
        # Calculate max frequency for normalization
        max_freq = max([row[1] for row in phrases_rows], default=0) if phrases_rows else 0
        if max_freq == 0:
            max_freq = 200  # Default for empty result
        
        ambiguous_phrases = []
        rank = 1
        
        # Add database results only
        for row in phrases_rows:
            if rank > limit:
                break
            ambiguous_phrases.append(AmbiguousPhrase(
                id=str(rank),
                rank=rank,
                phrase=row[0][:100],
                description=f"Found in {row[1]} sentences",
                frequency=row[1],
                maxFrequency=max_freq,
                status="High Risk" if row[1] > 50 else "Medium Risk",
                time=f"{row[1]} times"
            ))
            rank += 1
        
        return RecurringPhrasesData(ambiguousPhrases=ambiguous_phrases)
    
    @staticmethod
    def get_contracts_list(
        db: Session,
        page: int,
        limit: int,
        search: str,
        file_type: str,
        status: str,
        user_id: int  # 添加这行
    ) -> ContractsListResponse:
        """Get contracts list with filters and pagination"""
        # Build WHERE clause
        where_conditions = [
            "c.processing_status = 'completed'",
            "c.user_id = :user_id",        # 添加这行
            "c.is_active = True"           # 添加这行
        ]
        params = {"user_id": user_id}      # 添加这行
        
        if search:
            where_conditions.append("(c.title LIKE :search OR c.file_name LIKE :search)")
            params["search"] = f"%{search}%"
        
        if file_type:
            where_conditions.append("c.file_type = :type")
            params["type"] = file_type
        
        if status == "processed":
            where_conditions.append("c.processed_at IS NOT NULL")
        elif status == "pending":
            where_conditions.append("c.processing_status = 'pending'")
        
        where_clause = " AND ".join(where_conditions)
        
        # Get data from repository
        total = AnalyticsRepository.get_contracts_count(db, where_clause, params)
        
        offset = (page - 1) * limit
        rows = AnalyticsRepository.get_contracts_list(db, where_clause, params, limit, offset)
        
        # Transform to models
        items = []
        for row in rows:
            tags = []
            if row[3]:  # type
                tags.append(row[3])
            if row[5] > 10:  # ambiguity_rate > 10%
                tags.append("High Ambiguity")
            if row[6] > 7.0:  # quality_score > 7
                tags.append("High Quality")
            
            # Handle date - it might be datetime object or string
            date_str = ""
            if row[2]:
                if hasattr(row[2], 'isoformat'):
                    date_str = row[2].isoformat()
                else:
                    date_str = str(row[2])
            
            items.append(ContractListItem(
                id=str(row[0]),
                name=row[1] or "Untitled",
                date=date_str,
                type=row[3] or "Unknown",
                sentences=row[4],
                ambiguityRate=row[5],
                qualityScore=row[6],
                tags=tags
            ))
        
        return ContractsListResponse(items=items, total=total)
    
    @staticmethod
    def get_contract_stats(db: Session, user_id: int) -> ContractStatsResponse:
        """Get contract statistics"""
        now = datetime.now(timezone.utc)
        cur_start = now - timedelta(days=30)
        prev_start = now - timedelta(days=60)
        prev_end = cur_start
        
        # Get current window stats
        cur_contracts, cur_sentences, cur_amb_rate, cur_quality = \
            AnalyticsRepository.get_stats_current_window(db, cur_start, now, user_id)
        
        # Get previous window stats
        prev_contracts, prev_sentences, prev_amb_rate, prev_quality = \
            AnalyticsRepository.get_stats_current_window(db, prev_start, prev_end, user_id)
        
        # Calculate percentage change
        def pct_change(current, previous):
            if previous == 0:
                return 0
            return round(((current - previous) / previous) * 100, 1)
        
        return ContractStatsResponse(
            totalContracts=cur_contracts,
            totalContractsChange=pct_change(cur_contracts, prev_contracts),
            analyzedSentences=cur_sentences,
            analyzedSentencesChange=pct_change(cur_sentences, prev_sentences),
            averageAmbiguityRate=cur_amb_rate,
            averageAmbiguityRateChange=pct_change(cur_amb_rate, prev_amb_rate),
            averageQualityScore=cur_quality,
            averageQualityScoreChange=round(cur_quality - prev_quality, 1)
        )
    
    @staticmethod
    def get_extracted_sentences(db: Session, job_id: str, user_id: int) -> ExtractedSentencesResponse:
        """Get extracted sentences for a job"""
        job_info = AnalyticsRepository.get_job_info(db, job_id, user_id)
        if not job_info:
            raise ValueError("Job not found")
        
        file_name = job_info[0] or "Unknown"
        contract_id = job_info[1]
        
        sentences_rows = AnalyticsRepository.get_sentences_by_job(db, job_id)
        
        sentences = []
        for row in sentences_rows:
            # Determine label
            label = None
            if row[3]:  # label field
                label = "ambiguous" if row[3].upper().startswith("AMB") else "clear"
            elif row[4] is not None:  # is_ambiguous field
                label = "ambiguous" if row[4] else "clear"
            
            sentences.append(SentenceItem(
                docId=str(contract_id),
                docName=file_name,
                page=row[0],
                sentenceId=str(row[1]) if row[1] else "",
                text=row[2] or "",
                label=label,
                score=float(row[5]) if row[5] is not None else None,
                rationale=row[6] or ""
            ))
        
        return ExtractedSentencesResponse(sentences=sentences)
    
    @staticmethod
    def get_reports_data(db: Session, range_days: int, user_id: int) -> ReportsData:
        """Get complete reports data including all quality metrics"""
        start_date = datetime.now(timezone.utc) - timedelta(days=range_days)
        
        # Get all data from repository
        monthly_rows = AnalyticsRepository.get_monthly_data(db, start_date, user_id)
        quality_rows = AnalyticsRepository.get_quality_scores(db, start_date, user_id)
        completeness_rows = AnalyticsRepository.get_completeness_scores(db, start_date, user_id)
        accuracy_rows = AnalyticsRepository.get_accuracy_scores(db, start_date, user_id)
        consistency_rows = AnalyticsRepository.get_consistency_scores(db, start_date, user_id)
        contracts_rows = AnalyticsRepository.get_contracts_for_reports(db, start_date, user_id)
        
        # Combine quality scores by month
        quality_dict = {}
        
        # Add clarity scores
        for row in quality_rows:
            quality_dict[row[0]] = {'clarity': row[1]}
        
        # Add completeness scores
        for row in completeness_rows:
            if row[0] not in quality_dict:
                quality_dict[row[0]] = {'clarity': 0}
            quality_dict[row[0]]['completeness'] = row[1]
        
        # Add accuracy scores
        for row in accuracy_rows:
            if row[0] not in quality_dict:
                quality_dict[row[0]] = {'clarity': 0}
            quality_dict[row[0]]['accuracy'] = row[1]
        
        # Add consistency scores
        for row in consistency_rows:
            if row[0] not in quality_dict:
                quality_dict[row[0]] = {'clarity': 0}
            quality_dict[row[0]]['consistency'] = row[1]
        
        # Convert to list of QualityData
        quality_metrics = []
        for month in sorted(quality_dict.keys()):
            q = quality_dict[month]
            quality_metrics.append(QualityData(
                month=month,
                clarity=q.get('clarity', 0),
                completeness=q.get('completeness', 0),
                accuracy=q.get('accuracy', 0),
                consistency=q.get('consistency', 0)
            ))
        
        # Build ambiguity trends
        ambiguity_trends = []
        for row in monthly_rows:
            ambiguity_trends.append(AmbiguityTrend(
                month=row[0],
                ambiguityRate=row[2],
                targetRate=10.0
            ))
        
        # Build contract analysis
        contract_analysis = []
        for row in contracts_rows:
            contract_analysis.append(ContractAnalysis(
                name=row[0] or "Unknown",
                totalSentences=row[1],
                ambiguousSentences=row[2],
                percentage=row[3]
            ))
        
        # Calculate stats
        stats = {
            'totalContracts': len(contracts_rows),
            'ambiguousSentences': sum(r[2] for r in contracts_rows),
            'avgQualityScore': sum(q.get('clarity', 0) for q in quality_dict.values()) / len(quality_dict) if quality_dict else 0
        }
        if stats['totalContracts'] > 0:
            stats['ambiguityRate'] = round(sum(r[3] for r in contracts_rows) / len(contracts_rows), 2)
        else:
            stats['ambiguityRate'] = 0
        
        return ReportsData(
            stats=stats,
            qualityMetrics=quality_metrics,
            ambiguityTrends=ambiguity_trends,
            contractAnalysis=contract_analysis
        )
    
    @staticmethod
    def export_report(db: Session, format: str, user_id: int) -> io.BytesIO:
        """Generate report export (CSV or Excel)"""
        reports_data = AnalyticsService.get_reports_data(db, 180, user_id)  # 6 months
        
        if format == 'csv':
            return AnalyticsService._generate_csv_report(reports_data)
        elif format == 'excel':
            return AnalyticsService._generate_excel_report(reports_data)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    @staticmethod
    def _generate_csv_report(reports_data: ReportsData) -> io.BytesIO:
        """Generate CSV report"""
        buffer = io.StringIO()
        
        # Header
        buffer.write("Contract Analysis Report\n")
        buffer.write(f"Generated: {datetime.now(timezone.utc).isoformat()}\n\n")
        
        # Summary Statistics
        buffer.write("SUMMARY STATISTICS\n")
        buffer.write("Metric,Value\n")
        buffer.write(f"Total Contracts,{reports_data.stats['totalContracts']}\n")
        buffer.write(f"Ambiguous Sentences,{reports_data.stats['ambiguousSentences']}\n")
        buffer.write(f"Ambiguity Rate,{reports_data.stats['ambiguityRate']}%\n")
        buffer.write(f"Average Quality Score,{reports_data.stats['avgQualityScore']:.2f}/10\n")
        buffer.write("\n\n")
        
        # Quality Metrics
        buffer.write("QUALITY METRICS OVER TIME\n")
        buffer.write("Month,Clarity,Completeness,Accuracy,Consistency\n")
        for item in reports_data.qualityMetrics:
            buffer.write(f"{item.month},{item.clarity:.2f},{item.completeness:.2f},{item.accuracy:.2f},{item.consistency:.2f}\n")
        buffer.write("\n\n")
        
        # Ambiguity Trends
        buffer.write("AMBIGUITY RATE TRENDS\n")
        buffer.write("Month,Ambiguity Rate,Target Rate\n")
        for item in reports_data.ambiguityTrends:
            buffer.write(f"{item.month},{item.ambiguityRate:.2f}%,{item.targetRate}%\n")
        buffer.write("\n\n")
        
        # Contract Analysis
        buffer.write("PER-CONTRACT ANALYSIS\n")
        buffer.write("Contract Name,Total Sentences,Ambiguous Sentences,Ambiguity Rate\n")
        for item in reports_data.contractAnalysis:
            buffer.write(f"{item.name},{item.totalSentences},{item.ambiguousSentences},{item.percentage}%\n")
        
        # Export to BytesIO
        result = io.BytesIO()
        result.write(buffer.getvalue().encode('utf-8'))
        result.seek(0)
        return result
    
    @staticmethod
    def _generate_excel_report(reports_data: ReportsData) -> io.BytesIO:
        """Generate Excel report with multiple sheets"""
        buffer = io.BytesIO()
        
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            # Summary sheet
            summary_data = [
                ['Metric', 'Value'],
                ['Total Contracts', reports_data.stats['totalContracts']],
                ['Ambiguous Sentences', reports_data.stats['ambiguousSentences']],
                ['Ambiguity Rate', f"{reports_data.stats['ambiguityRate']}%"],
                ['Average Quality Score', f"{reports_data.stats['avgQualityScore']:.2f}/10"],
                ['Generated', datetime.now(timezone.utc).isoformat()]
            ]
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False, header=False)
            
            # Quality Metrics sheet
            quality_df = pd.DataFrame([
                {
                    'Month': item.month,
                    'Clarity': item.clarity,
                    'Completeness': item.completeness,
                    'Accuracy': item.accuracy,
                    'Consistency': item.consistency
                }
                for item in reports_data.qualityMetrics
            ])
            quality_df.to_excel(writer, sheet_name='Quality Metrics', index=False)
            
            # Ambiguity Trends sheet
            trends_df = pd.DataFrame([
                {
                    'Month': item.month,
                    'Ambiguity Rate': f"{item.ambiguityRate}%",
                    'Target Rate': f"{item.targetRate}%"
                }
                for item in reports_data.ambiguityTrends
            ])
            trends_df.to_excel(writer, sheet_name='Ambiguity Trends', index=False)
            
            # Contract Analysis sheet
            contracts_df = pd.DataFrame([
                {
                    'Contract Name': item.name,
                    'Total Sentences': item.totalSentences,
                    'Ambiguous Sentences': item.ambiguousSentences,
                    'Ambiguity Rate': f"{item.percentage}%"
                }
                for item in reports_data.contractAnalysis
            ])
            contracts_df.to_excel(writer, sheet_name='Contract Analysis', index=False)
        
        buffer.seek(0)
        return buffer