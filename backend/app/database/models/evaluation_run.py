from datetime import datetime, timezone
from sqlalchemy import String, DateTime, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column
from app.database.setup import Base

class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)     # uuid str
    user_id: Mapped[int] = mapped_column(Integer, index=True, default=0)
    file_name: Mapped[str] = mapped_column(String(255))
    config: Mapped[dict] = mapped_column(JSON)                        # judge list, criteria, manual metrics
    status: Mapped[str] = mapped_column(String(20), default="QUEUED") # QUEUED/PROCESSING/DONE/FAILED
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
