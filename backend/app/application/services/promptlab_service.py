import os
import requests
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database.models.contract_sentence import ContractSentence
from app.application.models.promptlab import (
    ClassifyResult,
    ExplainResult,
)


class PromptLabService:
    """
    Service layer for Prompt Lab.
    - manages 3 HF models
    - manages prompt templates
    - runs inference: remote HF first, then local fallback
    - can persist result back to contract_sentence table
    """

    def __init__(self):
        # 3 HF models required by the project
        self._models: Dict[str, Dict[str, Any]] = {
            "distilbert-base": {
                "id": "distilbert-base",
                "name": "DistilBERT Base (contracts)",
                "hf_name": "distilbert-base-uncased",
                "task": "text-classification",
            },
            "legal-bert": {
                "id": "legal-bert",
                "name": "Legal BERT base",
                "hf_name": "nlpaueb/legal-bert-base-uncased",
                "task": "text-classification",
            },
            "gpt2-small": {
                "id": "gpt2-small",
                "name": "GPT-2 Small (rationale)",
                "hf_name": "gpt2",
                "task": "text-generation",
            },
        }
        self._current_model_id: str = "distilbert-base"

        # 5 preconfigured prompt templates
        self._prompts: Dict[str, str] = {
            "amb-basic": (
                "Classify the following contract clause as AMBIGUOUS or UNAMBIGUOUS. "
                "Then explain briefly.\nClause: {clause}\nOutput:"
            ),
            "amb-strict": (
                "You are a contract ambiguity checker. Say AMBIGUOUS if multiple meanings are possible, "
                "else UNAMBIGUOUS. Then explain.\nClause: {clause}\n"
            ),
            "amb-layman": (
                "Explain to a non-lawyer if this clause is ambiguous. First say 'Ambiguous' or "
                "'Not Ambiguous', then explain.\nClause: {clause}\n"
            ),
            "amb-risky": (
                "If the clause leaves room for interpretation or missing actors/times/amounts, "
                "mark AMBIGUOUS. Then justify.\nClause: {clause}\n"
            ),
            "amb-short": (
                "Is this clause ambiguous? Answer AMBIGUOUS or UNAMBIGUOUS, then one sentence why.\n"
                "Clause: {clause}\n"
            ),
        }

        # placeholder for future cache (e.g. Redis)
        self._cache: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------
    # model management
    # ------------------------------------------------------------
    def list_models(self) -> List[Dict[str, Any]]:
        return list(self._models.values())

    def get_current_model(self) -> Dict[str, Any]:
        return self._models[self._current_model_id]

    def switch_model(self, model_id: str) -> bool:
        if model_id not in self._models:
            return False
        self._current_model_id = model_id
        return True

    # ------------------------------------------------------------
    # prompt management
    # ------------------------------------------------------------
    def _get_prompt(self, prompt_id: Optional[str], custom_prompt: Optional[str]) -> str:
        """
        Return the prompt text to use.
        If a custom prompt is provided, use it.
        Otherwise, look up by prompt_id.
        """
        if custom_prompt:
            cp = custom_prompt.strip()
            if not cp:
                raise ValueError("Custom prompt is empty")
            if len(cp) > 2000:
                raise ValueError("Custom prompt too long")
            return cp

        if not prompt_id:
            prompt_id = "amb-basic"

        if prompt_id not in self._prompts:
            raise ValueError(f"Unknown prompt_id: {prompt_id}")

        return self._prompts[prompt_id]

    # ------------------------------------------------------------
    # inference: HF first, then fallback
    # ------------------------------------------------------------
    def _run_remote_model(self, model_id: str, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Call Hugging Face Inference API.
        If token is missing or HF is loading / failed, return None so caller can fallback.
        """
        hf_token = os.environ.get("HF_TOKEN")
        if not hf_token:
            return None

        cfg = self._models.get(model_id)
        if not cfg:
            return None

        url = f"https://api-inference.huggingface.co/models/{cfg['hf_name']}"
        headers = {"Authorization": f"Bearer {hf_token}"}
        payload = {"inputs": prompt}

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=30)
        except Exception:
            return None

        if resp.status_code == 503:
            # model is still loading on HF
            return None
        if resp.status_code != 200:
            return None

        data = resp.json()
        return self._normalize_hf_output(cfg, data)

    def _normalize_hf_output(self, cfg: Dict[str, Any], data: Any) -> Dict[str, Any]:
        """
        Normalize different HF outputs into our internal schema.
        """
        task = cfg.get("task", "text-classification")

        # text generation (gpt2-small)
        if task == "text-generation":
            if isinstance(data, list) and data and "generated_text" in data[0]:
                text = data[0]["generated_text"]
                up = text.upper()
                if "AMBIGUOUS" in up:
                    label = "AMBIGUOUS"
                elif "UNAMBIGUOUS" in up or "NOT AMBIGUOUS" in up:
                    label = "UNAMBIGUOUS"
                else:
                    label = "AMBIGUOUS"
                return {
                    "label": label,
                    "rationale": text.strip(),
                    "score": 0.9,
                }
            # unknown format
            return {
                "label": "AMBIGUOUS",
                "rationale": f"HF ({cfg['hf_name']}) returned unsupported generation format.",
                "score": 0.5,
            }

        # text classification (list of {label, score})
        if isinstance(data, list) and len(data) > 0 and "label" in data[0]:
            first = data[0]
            raw_label = first["label"].upper()
            if (
                "1" in raw_label
                or "AMBIGUOUS" in raw_label
                or "POSITIVE" in raw_label
            ):
                label = "AMBIGUOUS"
            else:
                label = "UNAMBIGUOUS"
            return {
                "label": label,
                "rationale": f"HF ({cfg['hf_name']}) predicted {raw_label} with score {first.get('score', 0):.3f}",
                "score": float(first.get("score", 0.9)),
            }

        # final fallback
        return {
            "label": "AMBIGUOUS",
            "rationale": f"HF ({cfg['hf_name']}) returned an unknown format.",
            "score": 0.5,
        }

    def _run_local_rule(self, sentence: str, prompt: str) -> Dict[str, Any]:
        """
        Very simple rule-based ambiguity detector used as a fallback.
        """
        text = f"{prompt} {sentence}".lower()
        triggers = [
            "may",
            "at its discretion",
            "from time to time",
            "reasonable",
            "material",
            "or",
        ]
        ambiguous = False

        if "shall" in text and "may" in text:
            ambiguous = True
        elif any(t in text for t in triggers):
            ambiguous = True

        if ambiguous:
            return {
                "label": "AMBIGUOUS",
                "rationale": "AMBIGUOUS: wording allows more than one reasonable interpretation.",
                "score": 0.93,
            }
        return {
            "label": "UNAMBIGUOUS",
            "rationale": "UNAMBIGUOUS: wording is specific and single-meaning.",
            "score": 0.9,
        }

    def _run_inference(self, sentence: str, prompt: str) -> Dict[str, Any]:
        """
        Try HF first; if not available, use local rule.
        """
        model = self.get_current_model()
        remote = self._run_remote_model(model["id"], prompt)
        if remote:
            return remote
        return self._run_local_rule(sentence, prompt)

    # ------------------------------------------------------------
    # persistence
    # ------------------------------------------------------------
    def _persist_result(
        self,
        db: Session,
        user_id: int,
        contract_id: Optional[int],
        sentence: str,
        label: str,
        rationale: str,
    ) -> Optional[int]:
        """
        If contract_id is provided and the table exists, update one row
        in contract_sentence. This is just to integrate with your uploader.
        """
        if not contract_id:
            return None

        try:
            row = (
                db.query(ContractSentence)
                .filter(
                    ContractSentence.contract_id == contract_id,
                    ContractSentence.explanation.is_(None),
                )
                .order_by(ContractSentence.id.asc())
                .first()
            )
        except Exception:
            # table may not exist in early sprint
            return None

        if not row:
            return None

        row.label = label
        row.is_ambiguous = True if label == "AMBIGUOUS" else False
        row.explanation = rationale
        row.clarity_score = 0.9
        row.updated_at = datetime.now(timezone.utc)

        db.add(row)
        db.commit()
        db.refresh(row)

        return row.id

    # ------------------------------------------------------------
    # public methods called by routers
    # ------------------------------------------------------------
    def classify_sentences(
        self,
        sentences: List[str],
        prompt_id: Optional[str],
        custom_prompt: Optional[str],
        db: Session,
        user_id: int,
        contract_id: Optional[int],
    ) -> List[ClassifyResult]:
        prompt = self._get_prompt(prompt_id, custom_prompt)
        model = self.get_current_model()

        results: List[ClassifyResult] = []

        for s in sentences:
            inf = self._run_inference(s, prompt)
            sentence_db_id = self._persist_result(
                db=db,
                user_id=user_id,
                contract_id=contract_id,
                sentence=s,
                label=inf["label"],
                rationale=inf["rationale"],
            )
            results.append(
                ClassifyResult(
                    sentence=s,
                    label=inf["label"],
                    score=inf["score"],
                    model_id=model["id"],
                    rationale=inf["rationale"],
                    contract_id=contract_id,
                    sentence_id=sentence_db_id,
                )
            )

        return results

    def explain_one(
        self,
        sentence: str,
        prompt_id: Optional[str],
        custom_prompt: Optional[str],
        db: Session,
        user_id: int,
        contract_id: Optional[int],
    ) -> ExplainResult:
        prompt = self._get_prompt(prompt_id, custom_prompt)
        model = self.get_current_model()
        inf = self._run_inference(sentence, prompt)
        sentence_db_id = self._persist_result(
            db=db,
            user_id=user_id,
            contract_id=contract_id,
            sentence=sentence,
            label=inf["label"],
            rationale=inf["rationale"],
        )
        return ExplainResult(
            sentence=sentence,
            label=inf["label"],
            rationale=inf["rationale"],
            model_id=model["id"],
            contract_id=contract_id,
            sentence_id=sentence_db_id,
        )

    def explain_batch(
        self,
        sentences: List[str],
        prompt_id: Optional[str],
        custom_prompt: Optional[str],
        db: Session,
        user_id: int,
        contract_id: Optional[int],
    ) -> List[ExplainResult]:
        results: List[ExplainResult] = []
        for s in sentences:
            results.append(
                self.explain_one(
                    sentence=s,
                    prompt_id=prompt_id,
                    custom_prompt=custom_prompt,
                    db=db,
                    user_id=user_id,
                    contract_id=contract_id,
                )
            )
        return results
