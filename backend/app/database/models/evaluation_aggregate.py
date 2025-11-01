from sqlalchemy import Integer, String, JSON, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column
from app.database.setup import Base

class EvaluationAggregate(Base):
    __tablename__ = "evaluation_aggregates"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("evaluation_runs.id"), index=True)
    item_pk: Mapped[int] = mapped_column(ForeignKey("evaluation_items.id"), index=True)
    yesno: Mapped[dict] = mapped_column(JSON)         # {"grammar": true/false/None, ...}
    confidence: Mapped[dict] = mapped_column(JSON)    # {"grammar": 0.0..1.0, ...}
    notes: Mapped[dict] = mapped_column(JSON)         # {"grammar": "...", ...}
    judge_votes: Mapped[dict] = mapped_column(JSON)   # {"grammar": {"model_id": bool, ...}, ...}
    time_ms: Mapped[float] = mapped_column(Float, default=0.0)
    agg_label: Mapped[str | None] = mapped_column(String(32), nullable=True)
    class_agreement: Mapped[bool | None] = mapped_column(nullable=True)
    needs_review: Mapped[bool] = mapped_column(nullable=False, default=False)
