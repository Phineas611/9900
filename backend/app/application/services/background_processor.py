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
        file_type: str
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
                # 获取数据库会话
                db = next(get_db())
                
                # 更新状态为处理中
                update_contract_processing_status(
                    db=db,
                    contract_id=contract_id,
                    user_id=user_id,
                    status="processing"
                )
                
                # 处理文件
                ContractProcessor.process_contract(
                    db=db,
                    contract_id=contract_id,
                    user_id=user_id,
                    file_path=file_path,
                    file_type=file_type
                )
                
                print(f"Background processing completed for contract {contract_id}")
                
            except Exception as e:
                # 处理失败，更新状态
                try:
                    db = next(get_db())
                    update_contract_processing_status(
                        db=db,
                        contract_id=contract_id,
                        user_id=user_id,
                        status="failed"
                    )
                except:
                    pass
                
                print(f"Background processing failed for contract {contract_id}: {e}")
        
        # 在后台线程中执行
        thread = threading.Thread(target=process_in_background)
        thread.daemon = True
        thread.start()