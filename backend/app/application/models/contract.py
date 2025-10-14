from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# 合同创建请求
class ContractCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)

# 合同响应模型
class ContractResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    file_name: Optional[str]
    file_type: Optional[str]
    file_size: Optional[int]
    processing_status: str
    created_at: datetime
    updated_at: datetime
    processed_at: Optional[datetime]
    is_active: bool
    user_id: int

    class Config:
        from_attributes = True


# 文件上传响应
class FileUploadResponse(BaseModel):
    contract_id: int
    file_name: str
    file_type: str
    file_size: int
    message: str