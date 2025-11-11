from typing import Iterable, List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from app.database.models.evaluation_run import EvaluationRun
from app.database.models.evaluation_item import EvaluationItem
from app.database.models.evaluation_judgment import EvaluationJudgment
from app.database.models.evaluation_aggregate import EvaluationAggregate

class EvaluationRepository:
    # RUN
    def create_run(self, db: Session, run_id: str, user_id: int, file_name: str, config: dict) -> EvaluationRun:
        run = EvaluationRun(id=run_id, user_id=user_id, file_name=file_name, config=config, status="QUEUED")
        db.add(run)
        db.commit()
        db.refresh(run)
        return run

    def update_run_status(self, db: Session, run_id: str, status: str):
        db.query(EvaluationRun).filter(EvaluationRun.id == run_id).update({"status": status})
        db.commit()

    def finish_run(self, db: Session, run_id: str, summary: dict):
        db.query(EvaluationRun).filter(EvaluationRun.id == run_id).update({
            "status": "DONE",
            "summary": summary,
            "finished_at": datetime.now(timezone.utc)
        })
        db.commit()

    def get_run(self, db: Session, run_id: str) -> Optional[EvaluationRun]:
        return db.get(EvaluationRun, run_id)

    # ITEMS
    def bulk_insert_items(self, db: Session, run_id: str, rows: Iterable[dict]):
        objects = [EvaluationItem(run_id=run_id, **row) for row in rows]
        db.bulk_save_objects(objects)
        db.commit()

    def list_items(self, db: Session, run_id: str, offset: int=0, limit: int=500) -> List[EvaluationItem]:
        return db.execute(
            select(EvaluationItem).where(EvaluationItem.run_id == run_id).offset(offset).limit(limit)
        ).scalars().all()

    def count_items(self, db: Session, run_id: str) -> int:
        return db.execute(select(func.count()).select_from(
            select(EvaluationItem.id).where(EvaluationItem.run_id == run_id).subquery()
        )).scalar_one()

    # JUDGMENTS
    def add_judgment(self, db: Session, run_id: str, item_pk: int, judge_model: str, verdict: dict, latency_ms: float, raw: dict):
        db.add(EvaluationJudgment(
            run_id=run_id, item_pk=item_pk, judge_model=judge_model, verdict=verdict, latency_ms=latency_ms, raw=raw
        ))
        db.commit()

    def list_judgments_for_item(self, db: Session, run_id: str, item_pk: int) -> List[EvaluationJudgment]:
        return db.execute(
            select(EvaluationJudgment).where((EvaluationJudgment.run_id == run_id) & (EvaluationJudgment.item_pk == item_pk))
        ).scalars().all()

    # AGGREGATES
    def upsert_aggregate(self, db: Session, run_id: str, item_pk: int, yesno: dict, confidence: dict, notes: dict, judge_votes: dict, time_ms: float, agg_label: str | None = None, class_agreement: bool | None = None, needs_review: bool | None = None):
        existing = db.execute(
            select(EvaluationAggregate).where((EvaluationAggregate.run_id == run_id) & (EvaluationAggregate.item_pk == item_pk))
        ).scalar_one_or_none()
        if existing:
            existing.yesno = yesno
            existing.confidence = confidence
            existing.notes = notes
            existing.judge_votes = judge_votes
            existing.time_ms = time_ms
            if agg_label is not None:
                existing.agg_label = agg_label
            if class_agreement is not None:
                existing.class_agreement = class_agreement
            if needs_review is not None:
                existing.needs_review = needs_review
            db.commit()
            return existing
        obj = EvaluationAggregate(run_id=run_id, item_pk=item_pk, yesno=yesno, confidence=confidence, notes=notes, judge_votes=judge_votes, time_ms=time_ms, agg_label=agg_label, class_agreement=class_agreement, needs_review=(needs_review or False))
        db.add(obj)
        db.commit()
        return obj

    def list_results(self, db: Session, run_id: str, page: int, page_size: int) -> Tuple[List[Tuple[EvaluationItem, EvaluationAggregate]], int]:
        total = self.count_items(db, run_id)
        offset = (page-1)*page_size
        items = db.execute(
            select(EvaluationItem, EvaluationAggregate).where(
                (EvaluationItem.run_id == run_id) & (EvaluationAggregate.item_pk == EvaluationItem.id)
            ).offset(offset).limit(page_size)
        ).all()
        return items, total
