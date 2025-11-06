import os
import uuid
from pathlib import Path
from typing import Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.application.services.background_processor import BackgroundProcessor
from app.persistence.contract_repository import (
    create_contract, 
    update_contract_file_info,
    update_contract_processing_status
)
from app.application.models.contract import (
    ContractCreateRequest, 
    FileUploadResponse,
    ProcessingStatus
)
from app.utils.text_extractor import ContractProcessor
from app.database.models.activity_log import ActivityLog

class UploadService:

    ALLOWED_EXTENSIONS = {".pdf", ".zip"}
    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "application/zip"
    }
    

    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    @staticmethod
    def validate_file(file: UploadFile) -> bool:
        """Validate uploaded file type and size"""
        # Check file size if available
        if hasattr(file, 'size') and file.size and file.size > UploadService.MAX_FILE_SIZE:
            return False
        
        # Check file extension
        file_path = Path(file.filename or "")
        if file_path.suffix.lower() not in UploadService.ALLOWED_EXTENSIONS:
            return False
        
        # Check MIME type (allow None for some clients that don't send it)
        if file.content_type and file.content_type not in UploadService.ALLOWED_MIME_TYPES:
            return False
        
        return True
    
    @staticmethod
    def save_uploaded_file(file: UploadFile, upload_dir: Path) -> Path:

        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = upload_dir / unique_filename
        upload_dir.mkdir(parents=True, exist_ok=True) 
        with open(file_path, "wb") as buffer:
            content = file.file.read()
            buffer.write(content)
        
        return file_path
    
    @staticmethod
    def process_upload(
        db: Session,
        file: UploadFile,
        user_id: int
    ) -> FileUploadResponse:
      

        if not UploadService.validate_file(file):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only PDF and ZIP files are allowed (max 10MB)."
            )
        

        file_name = Path(file.filename).stem
        title = file_name if file_name else "Untitled Contract"
        

        contract_data = ContractCreateRequest(
            title=title,
            description=f"Uploaded file: {file.filename}"
        )
        contract = create_contract(db, contract_data, user_id)
        

        # Use persistent disk if UPLOAD_DIR is set (for Render), otherwise use uploads/
        if os.getenv("UPLOAD_DIR"):
            upload_base = Path(os.getenv("UPLOAD_DIR"))
        else:
            upload_base = Path("uploads")
        upload_dir = upload_base / str(user_id)
        
        try:

            file_path = UploadService.save_uploaded_file(file, upload_dir)
            # Convert to absolute path to ensure persistence across restarts
            file_path_absolute = file_path.resolve()

            update_contract_file_info(
                db=db,
                contract_id=contract.id,
                user_id=user_id,
                file_name=file.filename,
                file_type=Path(file.filename).suffix.lower(),
                file_size=file.size if hasattr(file, 'size') else 0,
                file_path=str(file_path_absolute)
            )
            

            activity_log = ActivityLog(
                user_id=user_id,
                event_type="UPLOAD",
                title="Contract Uploaded",
                message=f"Contract '{title}' was uploaded successfully."
            )
            db.add(activity_log)
            db.commit()

            update_contract_processing_status(
                db=db,
                contract_id=contract.id,
                user_id=user_id,
                status=ProcessingStatus.PENDING
            )
            

            BackgroundProcessor.process_contract_async(
                contract_id=contract.id,
                user_id=user_id,
                file_path=str(file_path_absolute),
                file_type=Path(file.filename).suffix.lower()
            )
            
            return FileUploadResponse(
                contract_id=contract.id,
                file_name=file.filename,
                file_type=Path(file.filename).suffix.lower(),
                file_size=file.size if hasattr(file, 'size') else 0,
                message="File uploaded successfully, processing in background"
            )
        except Exception as e:

            update_contract_processing_status(
                db=db,
                contract_id=contract.id,
                user_id=user_id,
                status=ProcessingStatus.FAILED
            )
            raise HTTPException(
                status_code=500,
                detail=f"Failed to process upload: {str(e)}"
            )