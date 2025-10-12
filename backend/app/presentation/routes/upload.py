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

@router.post("/", response_model=FileUploadResponse)
def upload_contract(    
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    上传合同文件并自动处理
    
    功能：
    - 接收PDF或ZIP格式的合同文件
    - 验证文件类型和大小（最大10MB）
    - 保存文件到服务器
    - 自动提取合同中的句子
    - 生成CSV、XLSX、TXT格式的句子文件
    - 更新合同处理状态
    - 自动使用文件名作为合同标题
    
    参数：
    - file: 上传的文件（PDF或ZIP）
    
    返回：
    - 合同ID、文件名、文件类型、文件大小等信息
    - 处理状态消息
    """
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
    """
    获取合同处理状态
    
    功能：
    - 查询指定合同的处理状态
    - 检查用户是否有权限访问该合同
    - 返回处理进度和文件信息
    
    参数：
    - contract_id: 合同ID
    
    返回：
    - 合同基本信息
    - 处理状态（pending/processing/completed/failed）
    - 文件信息
    - 时间戳
    """
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
    """
    下载处理好的句子文件
    
    功能：
    - 下载指定合同的处理结果
    - 支持CSV、XLSX、TXT三种格式
    - 验证合同处理状态和用户权限
    - 返回文件流供下载
    
    参数：
    - contract_id: 合同ID
    - format: 文件格式（csv/xlsx/txt）
    
    返回：
    - 文件流（可直接下载）
    - 文件名：contract_{contract_id}_sentences.{format}
    
    错误：
    - 404: 合同不存在或文件未找到
    - 400: 合同处理未完成
    """
    contract = get_contract_by_id(db, contract_id, current_user.id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    if contract.processing_status != "completed":
        raise HTTPException(status_code=400, detail="Contract processing not completed")
    
    # 构建文件路径
    output_dir = Path("outputs") / str(current_user.id) / str(contract_id)
    file_path = output_dir / f"sentences.{format}"
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        filename=f"contract_{contract_id}_sentences.{format}",
        media_type="application/octet-stream"
    )