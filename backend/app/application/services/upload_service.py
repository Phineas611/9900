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
from app.database.models.analysis_job import AnalysisJob

class UploadService:

    ALLOWED_EXTENSIONS = {".pdf", ".zip"}
    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "application/zip"
    }
    

    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    @staticmethod
    def validate_file(file: UploadFile) -> bool:
  
        if hasattr(file, 'size') and file.size > UploadService.MAX_FILE_SIZE:
            return False
        file_path = Path(file.filename or "")
        if file_path.suffix.lower() not in UploadService.ALLOWED_EXTENSIONS:
            return False
        if file.content_type not in UploadService.ALLOWED_MIME_TYPES:
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
        

        upload_dir = Path("uploads") / str(user_id)
        
        try:

            file_path = UploadService.save_uploaded_file(file, upload_dir)

            update_contract_file_info(
                db=db,
                contract_id=contract.id,
                user_id=user_id,
                file_name=file.filename,
                file_type=Path(file.filename).suffix.lower(),
                file_size=file.size if hasattr(file, 'size') else 0,
                file_path=str(file_path)
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
            

            # 新增：创建 AnalysisJob（QUEUED）
            job = AnalysisJob(
                id=str(uuid.uuid4()),
                user_id=user_id,
                contract_id=contract.id,
                file_name=file.filename,
                file_type=Path(file.filename).suffix.lower(),
                file_size=file.size if hasattr(file, 'size') else 0,
                status="QUEUED",
            )
            db.add(job)
            db.commit()

            BackgroundProcessor.process_contract_async(
                contract_id=contract.id,
                user_id=user_id,
                file_path=str(file_path),
                file_type=Path(file.filename).suffix.lower(),
                job_id=job.id,  # 传递 job_id 以便后台更新
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