from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.database.models.contract import Contract
from app.application.models.contract import ContractCreateRequest
from typing import Optional
from datetime import datetime, timezone

def create_contract(db: Session, contract_data: ContractCreateRequest, user_id: int) -> Contract:
    contract = Contract(
        title=contract_data.title,
        description=contract_data.description,
        user_id=user_id,
        processing_status="pending"
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract

def get_contract_by_id(db: Session, contract_id: int, user_id: int) -> Optional[Contract]:
    stmt = select(Contract).where(
        Contract.id == contract_id,
        Contract.user_id == user_id,
        Contract.is_active == True
    )
    return db.scalar(stmt)

def update_contract_file_info(
    db: Session,
    contract_id: int,
    user_id: int,
    file_name: str,
    file_type: str,
    file_size: int,
    file_path: str
) -> Optional[Contract]:
    contract = get_contract_by_id(db, contract_id, user_id)
    if not contract:
        return None
    
    contract.file_name = file_name
    contract.file_type = file_type
    contract.file_size = file_size
    contract.file_path = file_path
    contract.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(contract)
    return contract

def update_contract_processing_status(
    db: Session,
    contract_id: int,
    user_id: int,
    status: str
) -> Optional[Contract]:
    contract = get_contract_by_id(db, contract_id, user_id)
    if not contract:
        return None
    
    contract.processing_status = status
    if status == "completed":
        contract.processed_at = datetime.now(timezone.utc)
    
    contract.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(contract)
    return contract