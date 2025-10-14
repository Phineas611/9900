from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Boolean, Text, Integer, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.setup import Base

class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    file_path: Mapped[str] = mapped_column(String(500), nullable=True) 
    file_name: Mapped[str] = mapped_column(String(255), nullable=True) 
    file_type: Mapped[str] = mapped_column(String(50), nullable=True)  
    file_size: Mapped[int] = mapped_column(Integer, nullable=True)     
    
    processing_status: Mapped[str] = mapped_column(String(50), default="pending") 
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="contracts")
    
    analysis_jobs: Mapped[list["AnalysisJob"]] = relationship("AnalysisJob", back_populates="contract", cascade="all, delete-orphan")
    sentences: Mapped[list["ContractSentence"]] = relationship("ContractSentence", back_populates="contract", cascade="all, delete-orphan")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)