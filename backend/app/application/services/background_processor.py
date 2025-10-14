# -*- coding: utf-8 -*-
"""
后台文件处理服务

负责异步处理上传的合同文件，包括句子提取和文件生成
"""
import threading
from sqlalchemy.orm import Session

from app.database.setup import get_db
from app.persistence.contract_repository import update_contract_processing_status
from app.utils.text_extractor import ContractProcessor
from app.database.models.analysis_job import AnalysisJob
from datetime import datetime, timezone


class BackgroundProcessor:
    """
    后台文件处理器
    
    负责异步处理合同文件，避免阻塞上传接口
    """
    
    @staticmethod
    def process_contract_async(
        contract_id: int,
        user_id: int,
        file_path: str,
        file_type: str,
        job_id: str,  # 新增参数
    ):
        """
        异步处理合同文件
        
        功能：
        - 在后台线程中处理文件
        - 更新处理状态
        - 生成句子文件
        
        参数：
        - contract_id: 合同ID
        - user_id: 用户ID
        - file_path: 文件路径
        - file_type: 文件类型
        """
        def process_in_background():
            try:
                db = next(get_db())

                # 合同状态：processing
                update_contract_processing_status(
                    db=db,
                    contract_id=contract_id,
                    user_id=user_id,
                    status="processing"
                )

                # 作业状态：PROCESSING + started_at
                job = db.get(AnalysisJob, job_id)
                if job:
                    job.status = "PROCESSING"
                    job.started_at = datetime.now(timezone.utc)
                    db.commit()

                # 实际处理
                result = ContractProcessor.process_contract(
                    db=db,
                    contract_id=contract_id,
                    user_id=user_id,
                    file_path=file_path,
                    file_type=file_type
                )

                # 作业状态：COMPLETED + finished_at + 汇总字段
                if job:
                    job.status = "COMPLETED"
                    job.finished_at = datetime.now(timezone.utc)
                    job.progress_pct = 100.0
                    job.total_sentences = int(result.get("sentences_extracted", 0))
                    if job.started_at and job.finished_at:
                        job.duration_seconds = (job.finished_at - job.started_at).total_seconds()
                    db.commit()

                print(f"Background processing completed for contract {contract_id}")
            except Exception as e:
                try:
                    db = next(get_db())
                    # 合同状态：failed
                    update_contract_processing_status(
                        db=db,
                        contract_id=contract_id,
                        user_id=user_id,
                        status="failed"
                    )
                    # 作业状态：FAILED + finished_at
                    job = db.get(AnalysisJob, job_id)
                    if job:
                        job.status = "FAILED"
                        job.finished_at = datetime.now(timezone.utc)
                        job.progress_pct = 0.0
                        db.commit()
                except:
                    pass
                print(f"Background processing failed for contract {contract_id}: {e}")
        
        # 在后台线程中执行
        thread = threading.Thread(target=process_in_background)
        thread.daemon = True
        thread.start()