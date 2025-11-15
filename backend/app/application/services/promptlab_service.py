import os
import re
import json
import time
from typing import List, Optional, Dict, Any, Callable
from sqlalchemy.orm import Session
from datetime import datetime, timezone

import requests
from urllib.parse import quote

try:
    from huggingface_hub import get_token  # optional
except Exception:
    def get_token() -> Optional[str]:
        return None

from app.database.models.contract_sentence import ContractSentence
from app.application.models.promptlab import (
    ClassifyResult,
    ExplainResult,
)


class PromptLabService:
    """
    Call HF router with task-correct endpoints:
      - seq2seq (FLAN-T5):   /hf-inference/text2text-generation?model=<enc_repo>
      - causal (Qwen/GPT2):  /hf-inference/text-generation?model=<enc_repo>
    URL-encode repo id (google%2Fflan-t5-large). Keep API/DB/batch unchanged.
    """

    def __init__(self):
        self._models: Dict[str, Dict[str, Any]] = {
            "flan-t5-large": {
                "id": "flan-t5-large",
                "name": "FLAN-T5 Large (seq2seq, instruction following)",
                "hf_name": "google/flan-t5-large",
                "mode": "seq2seq",
            },
            "qwen2.5-0.5b-instruct": {
                "id": "qwen2.5-0.5b-instruct",
                "name": "Qwen2.5 0.5B Instruct (causal decoder)",
                "hf_name": "Qwen/Qwen2.5-0.5B-Instruct",
                "mode": "causal",
            },
            "gpt2-small": {
                "id": "gpt2-small",
                "name": "GPT-2 Small (generation)",
                "hf_name": "openai-community/gpt2",
                "mode": "causal",
            },
        }
        self._current_model_id: str = "flan-t5-large"

        self._prompts: Dict[str, str] = {
            "amb-basic": (
                "You are a contract ambiguity checker.\n"
                "Task: Decide if the clause is AMBIGUOUS or UNAMBIGUOUS, then give a short rationale.\n"
                "Return format:\n"
                "Label: <AMBIGUOUS|UNAMBIGUOUS>\n"
                "Reason: <one sentence>\n"
                "Clause: {clause}\n"
            ),
            "amb-strict": (
                "If multiple reasonable interpretations exist, return AMBIGUOUS; otherwise UNAMBIGUOUS. "
                "Explain briefly in one sentence.\nClause: {clause}\n"
            ),
            "amb-layman": (
                "Explain for a non-lawyer whether this clause is ambiguous. "
                "First output 'Label: Ambiguous' or 'Label: Unambiguous', then a one-sentence reason.\n"
                "Clause: {clause}\n"
            ),
            "amb-risky": (
                "If the clause leaves room for interpretation in actors, time, amounts, or conditions, "
                "mark AMBIGUOUS and justify briefly.\nClause: {clause}\n"
            ),
            "amb-short": (
                "Is this clause ambiguous? Output 'Label: AMBIGUOUS' or 'Label: UNAMBIGUOUS', then one-sentence reason.\n"
                "Clause: {clause}\n"
            ),
        }

        self._cache: Dict[str, Dict[str, Any]] = {}
        self._last_hf_error: Optional[str] = None

    # ---------- model mgmt ----------
    def list_models(self) -> List[Dict[str, Any]]:
        return list(self._models.values())

    def get_current_model(self) -> Dict[str, Any]:
        return self._models[self._current_model_id]

    def switch_model(self, model_id: str) -> bool:
        if model_id not in self._models:
            return False
        self._current_model_id = model_id
        return True

    # ---------- prompts ----------
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

    # ---------- HF token ----------
    def _resolve_hf_token(self) -> str:
        token = (
            os.environ.get("HF_API_TOKEN")
            or os.environ.get("HF_TOKEN")
            or os.environ.get("HUGGINGFACEHUB_API_TOKEN")
            or (get_token() if callable(get_token) else None)
        )
        if not token:
            raise RuntimeError(
                "Hugging Face token not set. Please export HF_API_TOKEN (or HF_TOKEN / HUGGINGFACEHUB_API_TOKEN)."
            )
        return token.strip()

    # ---------- HTTP to router ----------
    def _hf_http_infer(self, repo: str, inputs: str, mode: str) -> List[Dict[str, Any]]:
        """
        Use ONLY task-correct endpoints:
          - seq2seq:  /text2text-generation?model=<enc_repo>
          - causal:   /text-generation?model=<enc_repo>
        """
        token = self._resolve_hf_token()
        enc_repo = quote(repo, safe="")  # encode slash
        base_router = "https://router.huggingface.co/hf-inference"
        legacy_base = "https://api-inference.huggingface.co/models"

        if mode == "seq2seq":
            route = "text2text-generation"
        else:
            route = "text-generation"

        candidates = [
            f"{base_router}/{route}?model={enc_repo}",
            f"{base_router}/{route}/{enc_repo}",
            f"{base_router}/models/{enc_repo}",
            f"{legacy_base}/{enc_repo}",
        ]

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "x-wait-for-model": "true",
            "Accept": "application/json",
        }
        payload = {
            "inputs": inputs,
            "parameters": {
                "max_new_tokens": 160,
                "temperature": 0.2,
                "do_sample": False,
                "return_full_text": False,
            }
        }
        payload_with_model = dict(payload)
        payload_with_model["model"] = repo

        def _post(url: str) -> requests.Response:
            body = payload_with_model if "api-inference" in url or url.endswith(enc_repo) else payload
            return requests.post(url, headers=headers, json=body, timeout=90)

        delays = [0, 2, 4, 8, 16, 32]
        last_err = None

        for url in candidates:
            for attempt, delay in enumerate(delays, start=1):
                if delay:
                    time.sleep(delay)
                try:
                    resp = _post(url)
                    status = resp.status_code
                    if status == 200:
                        return self._normalize_http_json(resp)

                    if status in (429, 500, 502, 503, 504):
                        last_err = f"http_router status={status} url={url} body={resp.text[:300].replace(chr(10),' ')}"
                        print(f"[HF/router][attempt {attempt}] {last_err}")
                        continue  # retry same URL

                    # 404/405/415: wrong route or not provisioned -> no more alternatives for this mode
                    last_err = f"http_router status={status} url={url} body={resp.text[:300].replace(chr(10),' ')}"
                    print(f"[HF/router][attempt {attempt}] {last_err}")
                    break

                except requests.exceptions.RequestException as e:
                    last_err = f"network_error url={url}: {repr(e)[:300]}"
                    print(f"[HF/router][attempt {attempt}] {last_err}")
                    continue
                except Exception as e:
                    last_err = f"other_error url={url}: {repr(e)[:300]}"
                    print(f"[HF/router][attempt {attempt}] {last_err}")
                    break

        raise RuntimeError(last_err or "unknown error")

    def _normalize_http_json(self, resp: requests.Response) -> List[Dict[str, Any]]:
        """
        Normalize HF HTTP response into: list[{'generated_text': '...'}]
        """
        try:
            data = resp.json()
        except Exception:
            return [{"generated_text": resp.text}]

        if isinstance(data, list) and data:
            if isinstance(data[0], dict) and "generated_text" in data[0]:
                return data
            if isinstance(data[0], str):
                return [{"generated_text": " ".join(data)}]
            return [{"generated_text": json.dumps(data)[:5000]}]

        if isinstance(data, dict):
            if "generated_text" in data:
                return [data]
            if "outputs" in data and isinstance(data["outputs"], str):
                return [{"generated_text": data["outputs"]}]
            return [{"generated_text": json.dumps(data)[:5000]}]

        if isinstance(data, str):
            return [{"generated_text": data}]

        return [{"generated_text": resp.text}]

    # ---------- single-call inference ----------
    def _run_remote_model(self, model_id: str, text: str) -> Optional[Dict[str, Any]]:
        self._last_hf_error = None
        if model_id not in self._models:
            self._last_hf_error = f"Unknown model_id: {model_id}"
            return None
        cfg = self._models[model_id]
        repo = cfg["hf_name"]
        mode = cfg.get("mode", "causal")

        try:
            data = self._hf_http_infer(repo, text, mode)
            return self._normalize_hf_output(cfg, data)
        except Exception as e:
            self._last_hf_error = str(e)
            return None

    def _normalize_hf_output(self, cfg: Dict[str, Any], data: Any) -> Dict[str, Any]:
        try:
            if isinstance(data, list) and data and isinstance(data[0], dict) and "generated_text" in data[0]:
                text = str(data[0]["generated_text"]).strip()
            else:
                text = str(data)
        except Exception:
            text = str(data)

        up = text.upper()
        m = re.search(r"LABEL\s*:\s*(AMBIGUOUS|UNAMBIGUOUS|NOT\s+AMBIGUOUS)", up)
        if m:
            raw = m.group(1)
            label = "UNAMBIGUOUS" if "NOT" in raw else raw
        else:
            if "UNAMBIGUOUS" in up or "NOT AMBIGUOUS" in up:
                label = "UNAMBIGUOUS"
            elif "AMBIGUOUS" in up:
                label = "AMBIGUOUS"
            else:
                label = "AMBIGUOUS"

        return {"label": label, "rationale": text, "score": 0.9}

    def _run_inference(self, sentence: str, prompt: str) -> Dict[str, Any]:
        model = self.get_current_model()
        text = prompt  # send rendered prompt to HF

        out = self._run_remote_model(model["id"], text)
        if not out:
            hint = f" Last HF error: {self._last_hf_error}" if self._last_hf_error else ""
            raise RuntimeError(
                f"Hugging Face model unavailable. Check HF_TOKEN, network, and model id '{model['hf_name']}'.{hint}"
            )
        out["rationale"] = "[HF] " + str(out.get("rationale", "")).lstrip()
        return out

    # ---------- persistence (unchanged) ----------
    def _extract_score_from_rationale(self, rationale: str) -> Optional[float]:
        if not rationale:
            return None
        for pattern in (r'score\s*:?\s*(\d+\.?\d*)', r'with\s+score\s+(\d+\.?\d*)'):
            m = re.search(pattern, rationale, re.IGNORECASE)
            if m:
                try:
                    return float(m.group(1))
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
        auto_commit: bool = True,
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
        if auto_commit:
            db.commit()
            db.refresh(row)
        return row.id

    # ---------- public (unchanged) ----------
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
            rendered = prompt.format(clause=s) if "{clause}" in prompt else f"{prompt}\nClause: {s}\n"
            inf = self._run_inference(s, rendered)
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
        rendered = prompt.format(clause=sentence) if "{clause}" in prompt else f"{prompt}\nClause: {sentence}\n"
        inf = self._run_inference(sentence, rendered)
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
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> List[ExplainResult]:
        import logging
        logger = logging.getLogger(__name__)

        prompt = self._get_prompt(prompt_id, custom_prompt)
        model = self.get_current_model()
        out: List[ExplainResult] = []
        total = len(sentences)

        logger.info(f"[PromptLab] Starting batch processing: {total} sentences, contract_id={contract_id}")

        BATCH_SIZE = 10
        for i in range(0, len(sentences), BATCH_SIZE):
            batch = sentences[i:i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
            logger.info(f"[PromptLab] Processing batch {batch_num}/{total_batches} ({i+1}-{min(i+BATCH_SIZE, total)}/{total})")

            for idx_in_batch, s in enumerate(batch):
                try:
                    rendered = prompt.format(clause=s) if "{clause}" in prompt else f"{prompt}\nClause: {s}\n"
                    inf = self._run_inference(s, rendered)
                    sid = self._persist_result(db, user_id, contract_id, s, inf["label"], inf["rationale"], auto_commit=False)
                    out.append(
                        ExplainResult(
                            sentence=s,
                            label=inf["label"],
                            rationale=inf["rationale"],
                            model_id=model["id"],
                            contract_id=contract_id,
                            sentence_id=sid,
                        )
                    )
                except Exception as e:
                    logger.error(f"[PromptLab] Failed to process sentence {i+idx_in_batch+1}/{total}: {str(e)[:200]}")
                    out.append(
                        ExplainResult(
                            sentence=s,
                            label="ERROR",
                            rationale=f"Processing error: {str(e)[:200]}",
                            model_id=model["id"],
                            contract_id=contract_id,
                            sentence_id=None,
                        )
                    )

            try:
                db.commit()
                logger.info(f"[PromptLab] Batch {batch_num}/{total_batches} committed successfully")
                if progress_callback:
                    progress_callback(i + len(batch), total)
            except Exception as e:
                db.rollback()
                logger.error(f"[PromptLab] Database commit failed for batch {batch_num}: {str(e)[:200]}")

        logger.info(f"[PromptLab] Batch processing completed: {len(out)} results")
        return out
