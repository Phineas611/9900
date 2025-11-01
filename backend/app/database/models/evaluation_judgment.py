from sqlalchemy import Integer, String, Float, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database.setup import Base

class EvaluationJudgment(Base):
    __tablename__ = "evaluation_judgments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("evaluation_runs.id"), index=True)
    item_pk: Mapped[int] = mapped_column(ForeignKey("evaluation_items.id"), index=True)
    judge_model: Mapped[str] = mapped_column(String(64))
    verdict: Mapped[dict] = mapped_column(JSON)                      # strict Verdict JSON
    latency_ms: Mapped[float] = mapped_column(Float)
    raw: Mapped[dict] = mapped_column(JSON)                          # original provider json
