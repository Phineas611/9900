from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, DateTime, Integer, Text, ForeignKey, UniqueConstraint, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.setup import Base


class ContractSentence(Base):
    __tablename__ = "contract_sentences"
    __table_args__ = (UniqueConstraint('contract_id', 'page', 'sentence_id', name='_contract_page_sentence_uc'),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("analysis_jobs.id"), nullable=False)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id"), index=True, nullable=False)


    file_name: Mapped[str] = mapped_column(String(255))
    file_type: Mapped[str] = mapped_column(String(50))
    page: Mapped[Optional[int]] = mapped_column(Integer)
    sentence_id: Mapped[Optional[int]] = mapped_column(Integer) 
    section: Mapped[Optional[str]] = mapped_column(String(255))
    subsection: Mapped[Optional[str]] = mapped_column(String(255))


    sentence: Mapped[str] = mapped_column(Text, nullable=False)
    sentence_vec: Mapped[Optional[bytes]] = mapped_column() 


    label: Mapped[Optional[str]] = mapped_column(String(50))
    is_ambiguous: Mapped[Optional[bool]] = mapped_column()
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    suggested_revision: Mapped[Optional[str]] = mapped_column(Text)
    clarity_score: Mapped[Optional[float]] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    job = relationship("AnalysisJob", back_populates="sentences")
    contract = relationship("Contract", back_populates="sentences")