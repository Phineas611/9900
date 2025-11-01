from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import pandas as pd

from app.application.services.eval_io import load_table
from app.application.services.judges import get_available_judges
from app.application.models.eval_lab import Label, DEFAULT_RUBRICS
from app.database.models.eval_lab import EvalLabJob, EvalLabRecord


def norm_label(x: str) -> Label:
    x = str(x).strip().lower()
    return "Ambiguous" if x in ("ambiguous", "a", "1", "true") else "Unambiguous"


def run_job(
    session: Session,
    job_id: str,
    judges: Optional[List[str]],
    rubrics_on: Optional[Dict[str, bool]],
    custom_metrics: Optional[List[str]],
):
    job = session.get(EvalLabJob, job_id)
    assert job, f"job not found: {job_id}"

    df, cols = load_table(job.file_path)
    job.columns_map = cols  
    rubrics = [r for r, on in (rubrics_on or {r: True for r in DEFAULT_RUBRICS}).items() if on]
    customs = custom_metrics or []


    all_judges = get_available_judges()
    chosen_ids = judges or list(all_judges.keys())
    clients = [all_judges[j] for j in chosen_ids if j in all_judges]
    job.judges = [c.judge_id for c in clients]
    job.rubrics = rubrics
    job.custom_metrics = customs
    job.started_at = datetime.now(timezone.utc)

    session.add(job)
    session.commit()

    total = 0
    finished = 0
    class_ok_total = 0
    rationale_pass_total = 0

    for _, row in df.iterrows():
        total += 1
        sid = str(row[cols["id"]])
        sentence = str(row[cols["sentence"]])
        pred_class = norm_label(row[cols["pred_class"]])
        rationale = str(row[cols["rationale"]])
        gold_class: Optional[Label] = None
        if "gold_class" in cols and cols["gold_class"] in row and not pd.isna(row[cols["gold_class"]]):
            gold_class = norm_label(row[cols["gold_class"]])

        judges_list: List[Dict] = []
        class_votes: List[bool] = []
        rationale_votes: List[float] = []

        for client in clients:
            
            if gold_class is not None:
                class_ok = pred_class == gold_class
            else:
                class_ok = client.judge_class_correct_if_no_gold(sentence, pred_class)

            
            rat = client.judge_rationale_by_rubrics(sentence, pred_class, rationale, rubrics, customs)
            j_rec = {
                "judge_id": client.judge_id,
                "class_ok": class_ok,
                "rationale_ok_by_rubric": rat.get("rubrics", {}),
                "custom_ok": rat.get("custom", {}),
            }
            judges_list.append(j_rec)

            if class_ok is not None:
                class_votes.append(bool(class_ok))

 
            rubric_vals = list(j_rec["rationale_ok_by_rubric"].values())
            if rubric_vals:
                rationale_votes.append(sum(1 for v in rubric_vals if v) / len(rubric_vals))


        consensus = {
            "class_ok_ratio": (sum(class_votes) / len(class_votes)) if class_votes else None,
            "rationale_pass_ratio": (sum(rationale_votes) / len(rationale_votes)) if rationale_votes else None,
        }

  
        if consensus["class_ok_ratio"] is not None:
            class_ok_total += 1 if consensus["class_ok_ratio"] >= 0.5 else 0
        if consensus["rationale_pass_ratio"] is not None:
            rationale_pass_total += 1 if consensus["rationale_pass_ratio"] >= 0.5 else 0

        rec = EvalLabRecord(
            job_id=job_id,
            sid=sid,
            sentence=sentence,
            gold_class=gold_class,
            pred_class=pred_class,
            rationale=rationale,
            judges_json={"judges": judges_list},
            consensus_json=consensus,
        )
        session.add(rec)
        finished += 1

    job.total = total
    job.finished = finished
    job.finished_at = datetime.now(timezone.utc)
    job.metrics_summary = {
        "class_accuracy": (class_ok_total / total) if total else 0.0,
        "rationale_pass_rate": (rationale_pass_total / total) if total else 0.0,
    }
    session.add(job)
    session.commit()
    return df, cols