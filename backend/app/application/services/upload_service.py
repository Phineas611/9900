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

class UploadService:
    """
    文件上传服务类
    
    负责处理合同文件的上传、验证、保存和处理
    支持PDF和ZIP格式，自动提取句子并生成多种格式的导出文件
    """
    
    # 允许的文件类型
    ALLOWED_EXTENSIONS = {".pdf", ".zip"}
    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "application/zip"
    }
    
    # 最大文件大小 (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    @staticmethod
    def validate_file(file: UploadFile) -> bool:
        """
        验证上传的文件
        
        功能：
        - 检查文件扩展名是否为PDF或ZIP
        - 检查MIME类型是否匹配
        - 检查文件大小是否超过限制
        
        参数：
        - file: 上传的文件对象
        
        返回：
        - True: 文件有效
        - False: 文件无效
        """
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
        """
        保存上传的文件到服务器
        
        功能：
        - 生成唯一的文件名（避免重名冲突）
        - 创建用户专属的上传目录
        - 将文件内容写入磁盘
        
        参数：
        - file: 上传的文件对象
        - upload_dir: 上传目录路径
        
        返回：
        - 保存后的文件路径
        """
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
        """
        处理文件上传的完整流程
        
        功能：
        - 验证上传的文件
        - 创建合同数据库记录（使用文件名作为标题）
        - 保存文件到服务器
        - 自动处理文件（提取句子）
        - 生成多种格式的导出文件
        - 更新处理状态
        
        参数：
        - db: 数据库会话
        - file: 上传的文件
        - user_id: 用户ID
        
        返回：
        - 文件上传响应信息
        
        异常：
        - HTTPException: 文件验证失败或处理失败
        """
        if not UploadService.validate_file(file):
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only PDF and ZIP files are allowed (max 10MB)."
            )
        
        # 使用文件名作为标题
        file_name = Path(file.filename).stem
        title = file_name if file_name else "Untitled Contract"
        
        # 创建合同记录
        contract_data = ContractCreateRequest(
            title=title,
            description=f"Uploaded file: {file.filename}"
        )
        contract = create_contract(db, contract_data, user_id)
        
        # 设置上传目录
        upload_dir = Path("uploads") / str(user_id)
        
        try:
            # 保存文件
            file_path = UploadService.save_uploaded_file(file, upload_dir)
            
            # 更新合同文件信息
            update_contract_file_info(
                db=db,
                contract_id=contract.id,
                user_id=user_id,
                file_name=file.filename,
                file_type=Path(file.filename).suffix.lower(),
                file_size=file.size if hasattr(file, 'size') else 0,
                file_path=str(file_path)
            )
            
                        # 更新处理状态为待处理
            update_contract_processing_status(
                db=db,
                contract_id=contract.id,
                user_id=user_id,
                status=ProcessingStatus.PENDING
            )
            
            # 启动后台异步处理
            BackgroundProcessor.process_contract_async(
                contract_id=contract.id,
                user_id=user_id,
                file_path=str(file_path),
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
            # 如果上传失败，更新状态为失败
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