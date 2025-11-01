from __future__ import annotations
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import String, Text, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database.setup import Base


class EvalLabJob(Base):
    __tablename__ = "eval_lab_jobs"


    job_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)

    columns_map: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    judges: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    rubrics: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    custom_metrics: Mapped[list[str]] = mapped_column(JSON, nullable=False)

    total: Mapped[int] = mapped_column(Integer, default=0)
    finished: Mapped[int] = mapped_column(Integer, default=0)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    metrics_summary: Mapped[dict[str, float]] = mapped_column(JSON, default=dict, nullable=False)


class EvalLabRecord(Base):
    __tablename__ = "eval_lab_records"

    pk: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(ForeignKey("eval_lab_jobs.job_id"), index=True)
    sid: Mapped[str] = mapped_column(String(128), nullable=False)  
    sentence: Mapped[str] = mapped_column(Text, nullable=False)
    gold_class: Mapped[str | None] = mapped_column(String(32), nullable=True)
    pred_class: Mapped[str] = mapped_column(String(32), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)


    judges_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    consensus_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)