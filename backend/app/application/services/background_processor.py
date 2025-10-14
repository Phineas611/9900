# -*- coding: utf-8 -*-
import threading
from sqlalchemy.orm import Session

from app.database.setup import get_db
from app.persistence.contract_repository import update_contract_processing_status
from app.utils.text_extractor import ContractProcessor


class BackgroundProcessor:
    @staticmethod
    def process_contract_async(
        contract_id: int,
        user_id: int,
        file_path: str,
        file_type: str
    ):
        def process_in_background():
            try:
                db = next(get_db())
                
                update_contract_processing_status(
                    db=db,
                    contract_id=contract_id,
                    user_id=user_id,
                    status="processing"
                )
                
                ContractProcessor.process_contract(
                    db=db,
                    contract_id=contract_id,
                    user_id=user_id,
                    file_path=file_path,
                    file_type=file_type
                )
                
                print(f"Background processing completed for contract {contract_id}")
                
            except Exception as e:
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
        
        thread = threading.Thread(target=process_in_background)
        thread.daemon = True
        thread.start()