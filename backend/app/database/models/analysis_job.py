from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Integer, Float, ForeignKey, Text
from sqlalchemy import JSON

from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.setup import Base


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # uuid
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id"), index=True, nullable=False)


    file_name: Mapped[Optional[str]] = mapped_column(String(255))
    file_type: Mapped[Optional[str]] = mapped_column(String(50))
    file_size: Mapped[Optional[int]] = mapped_column(Integer)


    status: Mapped[str] = mapped_column(String(20), default="QUEUED")  # QUEUED/PROCESSING/COMPLETED/FAILED
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    progress_pct: Mapped[Optional[float]] = mapped_column(Float)


    total_sentences: Mapped[Optional[int]] = mapped_column(Integer)
    ambiguous_count: Mapped[Optional[int]] = mapped_column(Integer)
    avg_explanation_clarity: Mapped[Optional[float]] = mapped_column(Float)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float)
    analysis_summary: Mapped[Optional[str]] = mapped_column(Text)
    actions: Mapped[Optional[dict]] = mapped_column(JSON)

    user = relationship("User", back_populates="analysis_jobs")
    contract = relationship("Contract", back_populates="analysis_jobs")
    sentences: Mapped[list["ContractSentence"]] = relationship("ContractSentence", back_populates="job")