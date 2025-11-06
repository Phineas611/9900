from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from pathlib import Path

from app.database.setup import get_db
from app.application.auth import get_current_user
from app.application.services.upload_service import UploadService
from app.application.models.contract import FileUploadResponse
from app.persistence.contract_repository import get_contract_by_id

router = APIRouter(prefix="/uploads", tags=["uploads"])

# Anchor outputs under backend directory to align with processing pipeline
import os
BACKEND_DIR = Path(__file__).resolve().parents[3]
# Use persistent disk if OUTPUT_DIR is set (for Render), otherwise use backend/outputs
if os.getenv("OUTPUT_DIR"):
    OUTPUT_ROOT = Path(os.getenv("OUTPUT_DIR"))
else:
    OUTPUT_ROOT = BACKEND_DIR / "outputs"

@router.post("/", response_model=FileUploadResponse)
def upload_contract(    
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    
    return UploadService.process_upload(
        db=db,
        file=file,
        user_id=current_user.id
    )

@router.get("/{contract_id}/status")
def get_upload_status(    
    contract_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):

    contract = get_contract_by_id(db, contract_id, current_user.id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    return {
        "contract_id": contract.id,
        "title": contract.title,
        "processing_status": contract.processing_status,
        "file_name": contract.file_name,
        "created_at": contract.created_at,
        "processed_at": contract.processed_at
    }

@router.get("/{contract_id}/download/{format}")
def download_processed_file(
    contract_id: int,
    format: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
  
    contract = get_contract_by_id(db, contract_id, current_user.id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    if contract.processing_status != "completed":
        raise HTTPException(status_code=400, detail="Contract processing not completed")
    
    # 构建文件路径（统一为backend/outputs）
    output_dir = OUTPUT_ROOT / str(current_user.id) / str(contract_id)
    file_path = output_dir / f"sentences.{format}"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        filename=f"contract_{contract_id}_sentences.{format}",
        media_type="application/octet-stream"
    )