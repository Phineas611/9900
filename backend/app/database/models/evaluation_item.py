from sqlalchemy import Integer, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database.setup import Base

class EvaluationItem(Base):
    __tablename__ = "evaluation_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("evaluation_runs.id"), index=True)
    item_id: Mapped[str] = mapped_column(String(128), index=True)     # id from file
    sentence: Mapped[str] = mapped_column(Text)
    gold_label: Mapped[str | None] = mapped_column(String(64), nullable=True)
    predicted_label: Mapped[str] = mapped_column(String(64))
    rationale: Mapped[str] = mapped_column(Text)
