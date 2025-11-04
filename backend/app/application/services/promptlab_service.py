import os
import re
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from huggingface_hub import InferenceClient
try:
    from huggingface_hub.errors import HfHubHTTPError, InferenceTimeoutError
except Exception:
    try:
        from huggingface_hub.utils import HfHubHTTPError, InferenceTimeoutError  # type: ignore
    except Exception:
        class HfHubHTTPError(Exception):
            pass
        class InferenceTimeoutError(Exception):
            pass

from app.database.models.contract_sentence import ContractSentence
from app.application.models.promptlab import (
    ClassifyResult,
    ExplainResult,
)


class PromptLabService:

    def __init__(self):
        self._models: Dict[str, Dict[str, Any]] = {
            "distilbert-base": {
                "id": "distilbert-base",
                "name": "DistilBERT SST-2 (classification)",
                "hf_name": "distilbert/distilbert-base-uncased-finetuned-sst-2-english",
                "task": "text-classification",
            },
            "legal-bert": {
                "id": "legal-bert",
                "name": "FinBERT (classification)",
                "hf_name": "ProsusAI/finbert",
                "task": "text-classification",
            },
            "gpt2-small": {
                "id": "gpt2-small",
                "name": "GPT-2 Small (generation)",
                "hf_name": "openai-community/gpt2",
                "task": "text-generation",
            },
        }
        self._current_model_id: str = "distilbert-base"

        self._prompts: Dict[str, str] = {
            "amb-basic": (
                "Classify the following contract clause as AMBIGUOUS or UNAMBIGUOUS, "
                "then briefly explain why.\nClause: {clause}\nOutput:"
            ),
            "amb-strict": (
                "You are a contract ambiguity checker. If multiple reasonable meanings exist, "
                "return AMBIGUOUS, else UNAMBIGUOUS. Provide a short reason.\nClause: {clause}\n"
            ),
            "amb-layman": (
                "Explain for a non-lawyer whether this clause is ambiguous. "
                "First say 'Ambiguous' or 'Not Ambiguous', then give a short explanation.\n"
                "Clause: {clause}\n"
            ),
            "amb-risky": (
                "If the clause leaves room for interpretation (actors/times/amounts/conditions), "
                "mark AMBIGUOUS and justify briefly.\nClause: {clause}\n"
            ),
            "amb-short": (
                "Is this clause ambiguous? Answer AMBIGUOUS or UNAMBIGUOUS, then one-sentence reason.\n"
                "Clause: {clause}\n"
            ),
        }

        self._cache: Dict[str, Dict[str, Any]] = {}
        self._last_hf_error: Optional[str] = None

    # ---------- model management ----------
    def list_models(self) -> List[Dict[str, Any]]:
        return list(self._models.values())

    def get_current_model(self) -> Dict[str, Any]:
        return self._models[self._current_model_id]

    def switch_model(self, model_id: str) -> bool:
        if model_id not in self._models:
            return False
        self._current_model_id = model_id
        return True

    # ---------- prompt management ----------
    def list_prompts(self) -> List[str]:
        return list(self._prompts.keys())

    def _get_prompt(self, prompt_id: Optional[str], custom_prompt: Optional[str]) -> str:
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

    # ---------- inference on HF ----------
    def _get_hf_client(self) -> InferenceClient:
        hf_token = os.environ.get("HF_API_TOKEN")
        if not hf_token:
            raise RuntimeError(
                "HF_API_TOKEN is not set in environment. "
                "Please set it in Render Dashboard > Environment Variables."
            )
        # 有的版本叫 token，有的文档叫 api_key；token 在各版本都可用
        return InferenceClient(token=hf_token, timeout=90)

    def _run_remote_model(self, model_id: str, text: str) -> Optional[Dict[str, Any]]:
        self._last_hf_error = None

        if model_id not in self._models:
            self._last_hf_error = f"Unknown model_id: {model_id}"
            return None
        cfg = self._models[model_id]

        try:
            client = self._get_hf_client()
        except Exception as e:
            self._last_hf_error = f"client_init: {e}"
            return None

        task = cfg.get("task", "text-classification")
        repo = cfg["hf_name"]

        import time
        delays = [0, 2, 4, 8, 16, 32]  # ~1 min
        last_err = None

        for attempt, delay in enumerate(delays, start=1):
            if delay:
                time.sleep(delay)
            try:
                if task == "text-generation":
                    out = client.text_generation(
                        prompt=text,
                        model=repo,
                        max_new_tokens=96,
                        temperature=0.2,
                        do_sample=False,
                        return_full_text=False,
                    )
                    data = [{"generated_text": out}]
                else:
                    data = client.text_classification(
                        text=text,
                        model=repo,
                    )
                return self._normalize_hf_output(cfg, data)

            except (HfHubHTTPError, InferenceTimeoutError) as e:
                status = getattr(getattr(e, "response", None), "status_code", None)
                body = getattr(getattr(e, "response", None), "text", "") or str(e)
                last_err = f"status={status} body={(body[:300]).replace(chr(10),' ')}"
                print(f"[HF][attempt {attempt}] {last_err}")
                # Retry on rate limit (429), service unavailable (503), and bad gateway (502)
                if status in (429, 502, 503,500):
                    continue
                break  
            except Exception as e:
                last_err = f"other_error: {str(e)[:200]}"
                print(f"[HF][attempt {attempt}] {last_err}")
                break

        self._last_hf_error = last_err or "unknown error"
        return None

    def _normalize_hf_output(self, cfg: Dict[str, Any], data: Any) -> Dict[str, Any]:
        task = cfg.get("task", "text-classification")
        if task == "text-generation":
            if isinstance(data, list) and data and "generated_text" in data[0]:
                text = str(data[0]["generated_text"])
                up = text.upper()
                if "AMBIGUOUS" in up:
                    label = "AMBIGUOUS"
                elif "UNAMBIGUOUS" in up or "NOT AMBIGUOUS" in up:
                    label = "UNAMBIGUOUS"
                else:
                    label = "AMBIGUOUS"
                return {"label": label, "rationale": text.strip(), "score": 0.9}
            return {"label": "AMBIGUOUS", "rationale": "Unsupported generation output.", "score": 0.5}

        if isinstance(data, list) and data and isinstance(data[0], dict) and "label" in data[0]:
            first = data[0]
            raw = str(first.get("label", "")).upper()
            if any(k in raw for k in ("NEG", "CON", "0")):
                label = "AMBIGUOUS"
            else:
                label = "UNAMBIGUOUS"
            return {
                "label": label,
                "rationale": f"HF ({cfg['hf_name']}) predicted {raw} with score {first.get('score', 0):.3f}",
                "score": float(first.get("score", 0.9)),
            }

        return {"label": "AMBIGUOUS", "rationale": "Unknown HF output format.", "score": 0.5}

    def _run_inference(self, sentence: str, prompt: str) -> Dict[str, Any]:
        model = self.get_current_model()
        text = sentence if model.get("task") == "text-classification" else prompt

        out = self._run_remote_model(model["id"], text)
        if not out:
            hint = f" Last HF error: {self._last_hf_error}" if self._last_hf_error else ""
            raise RuntimeError(
                f"Hugging Face model unavailable. Check HF_TOKEN, network, and model id '{model['hf_name']}'.{hint}"
            )
        out["rationale"] = "[HF] " + str(out.get("rationale", "")).lstrip()
        return out

    # ---------- persistence ----------
    def _extract_score_from_rationale(self, rationale: str) -> Optional[float]:
        if not rationale:
            return None 
        patterns = [
            r'score\s*:?\s*(\d+\.?\d*)', 
            r'with\s+score\s+(\d+\.?\d*)',  
        ]
        
        for pattern in patterns:
            match = re.search(pattern, rationale, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except (ValueError, IndexError):
                    continue
        
        return None

    def _persist_result(
        self,
        db: Session,
        user_id: int,
        contract_id: Optional[int],
        sentence: str,
        label: str,
        rationale: str,
    ) -> Optional[int]:
        if not contract_id:
            return None

        try:

            row = (
                db.query(ContractSentence)
                .filter(
                    ContractSentence.contract_id == contract_id,
                    ContractSentence.sentence == sentence
                )
                .first()
            )
            
            if not row:
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
            return None

        if not row:
            return None

        row.label = label
        row.is_ambiguous = (label == "AMBIGUOUS")
        row.explanation = rationale
        
        extracted_score = self._extract_score_from_rationale(rationale)
        row.clarity_score = extracted_score if extracted_score is not None else 0.9
        
        row.updated_at = datetime.now(timezone.utc)

        db.add(row)
        db.commit()
        db.refresh(row)
        return row.id

    # ---------- public ----------
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
        res: List[ClassifyResult] = []
        for s in sentences:
            inf = self._run_inference(s, prompt)
            sid = self._persist_result(db, user_id, contract_id, s, inf["label"], inf["rationale"])
            res.append(
                ClassifyResult(
                    sentence=s,
                    label=inf["label"],
                    score=inf["score"],
                    model_id=model["id"],
                    rationale=inf["rationale"],
                    contract_id=contract_id,
                    sentence_id=sid,
                )
            )
        return res

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
        sid = self._persist_result(db, user_id, contract_id, sentence, inf["label"], inf["rationale"])
        return ExplainResult(
            sentence=sentence,
            label=inf["label"],
            rationale=inf["rationale"],
            model_id=model["id"],
            contract_id=contract_id,
            sentence_id=sid,
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
        out: List[ExplainResult] = []
        for s in sentences:
            out.append(
                self.explain_one(
                    sentence=s,
                    prompt_id=prompt_id,
                    custom_prompt=custom_prompt,
                    db=db,
                    user_id=user_id,
                    contract_id=contract_id,
                )
            )
        return out
