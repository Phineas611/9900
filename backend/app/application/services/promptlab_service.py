import os
import re
import json
import time  # NEW: used to throttle HF request rate
from typing import List, Optional, Dict, Any, Callable
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
        """
        Service responsible for running ambiguity checks on contract clauses
        using Hugging Face text-classification models.
        All configured models are generic NLI-type classifiers (not sentiment-specific).
        """
        self._models: Dict[str, Dict[str, Any]] = {
            "llama3-8ba_instruct-hf": {
                "id": "llama3-8ba_instruct-hf",
                "name": "Llama3 8B Instruct (HF)",
                "hf_name": "meta-llama/Meta-Llama-3-8B-Instruct",
                "task": "chat-completion",
            },
            "llama3-70ba_instruct-hf": {
                "id": "llama3-70ba_instruct-hf",
                "name": "Llama3 70B Instruct (HF)",
                "hf_name": "meta-llama/Meta-Llama-3-70B-Instruct",
                "task": "chat-completion",
            },
            "qwen3-8b": {
                "id": "qwen3-8b",
                "name": "Qwen3 8B (HF)",
                "hf_name": "Qwen/Qwen3-8B",
                "task": "chat-completion",
            },
        }

        # Default model: light-weight Groq 8B chat
        self._current_model_id: str = "llama3-8ba_instruct-hf"

        # ----------------- prompt templates (unified format) -----------------
        # All prompts now explicitly ask for:
        # - a classification: Ambiguous / Unambiguous
        # - a concrete rationale explaining why
        self._prompts: Dict[str, str] = {
            "amb-basic": (
                "You are a legal AI assistant for contract review.\n"
                "Task: Decide whether the following contract clause is Ambiguous or Unambiguous and briefly explain why.\n\n"
                "Definitions:\n"
                "- Ambiguous: Uses subjective or vague terms (e.g., 'reasonable', 'promptly', 'satisfactory', 'materially') "
                "or lacks concrete metrics, dates, amounts, or conditions.\n"
                "- Unambiguous: Uses specific numbers, dates, percentages, or objective standards (e.g., '14 days', '$5,000').\n\n"
                "Clause:\n\"{clause}\"\n\n"
                "Output Format (English only):\n"
                "Classification: Ambiguous or Unambiguous\n"
                "Rationale: One sentence explaining why the clause is Ambiguous or Unambiguous, "
                "referring to specific words or structure in the clause."
            ),
            "amb-strict": (
                "You are acting as a strict contract ambiguity auditor.\n"
                "If a clause leaves ANY room for interpretation, treat it as Ambiguous. "
                "Highlight vague or subjective expressions.\n\n"
                "Common vague expressions include: reasonable, best efforts, appropriate, substantial, undue, "
                "as soon as practicable, without undue delay.\n\n"
                "Clause:\n\"{clause}\"\n\n"
                "Output Format (English only):\n"
                "Classification: Ambiguous or Unambiguous\n"
                "Rationale: One sentence explaining why, explicitly mentioning the vague or clear terms in the clause."
            ),
            "amb-risky": (
                "You are a legal risk analyst.\n"
                "Analyze whether the following clause is Ambiguous or Unambiguous and explain the legal risk.\n\n"
                "Guidance:\n"
                "- If the clause is vague or open to multiple interpretations, it is Ambiguous and therefore higher legal risk.\n"
                "- If the clause is precise and leaves little room for interpretation, it is Unambiguous and lower legal risk.\n\n"
                "Clause:\n\"{clause}\"\n\n"
                "Output Format (English only):\n"
                "Classification: Ambiguous or Unambiguous\n"
                "Rationale: One sentence explaining the key source of risk or clarity, based on the wording of the clause."
            ),
            "amb-layman": (
                "You are explaining contract language to a non-lawyer.\n"
                "Decide whether the sentence is Ambiguous or Unambiguous, and explain it in simple language.\n\n"
                "Clause:\n\"{clause}\"\n\n"
                "Output Format (English only):\n"
                "Classification: Ambiguous or Unambiguous\n"
                "Rationale: One or two simple sentences that a non-lawyer can understand, "
                "stating whether the clause is clear or confusing and why."
            ),
            "amb-short": (
                "Binary classification task for contract ambiguity.\n"
                "Input clause:\n\"{clause}\"\n\n"
                "Rules of thumb:\n"
                "- If the clause mainly uses subjective or vague words, classify as Ambiguous.\n"
                "- If the clause mainly uses objective numbers, dates, or precise conditions, classify as Unambiguous.\n\n"
                "Output Format (English only):\n"
                "Classification: Ambiguous or Unambiguous\n"
                "Rationale: A very short explanation (one sentence) referring to the main vague or precise elements."
            )
        }

        # Optional: simple in-memory cache (currently unused).
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._last_hf_error: Optional[str] = None

    # ---------- model management ----------
    def list_models(self) -> List[Dict[str, Any]]:
        """Return all available model metadata."""
        return list(self._models.values())

    def get_current_model(self) -> Dict[str, Any]:
        """Return the currently selected model config."""
        return self._models[self._current_model_id]

    def switch_model(self, model_id: str) -> bool:
        """Switch the active model by id. Returns False if the id is unknown."""
        if model_id not in self._models:
            return False
        self._current_model_id = model_id
        return True

    # ---------- prompt management ----------
    def list_prompts(self) -> List[str]:
        """Return the list of available prompt ids."""
        return list(self._prompts.keys())

    def _get_prompt(self, prompt_id: Optional[str], custom_prompt: Optional[str]) -> str:
        """
        Resolve and validate the prompt text to use.

        - If custom_prompt is provided, we use that (after basic validation).
        - Otherwise, we look up the prompt by prompt_id (default = 'amb-basic').
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

    # ---------- inference on HF ----------
    def _get_hf_client(self) -> InferenceClient:
        """
        Create an InferenceClient.

        We support both HF_API_TOKEN and HF_TOKEN so that different
        deployment setups can reuse the same code.
        HF_API_TOKEN takes precedence if both are set.
        """
        hf_token = os.environ.get("HF_API_TOKEN") or os.environ.get("HF_TOKEN")
        if not hf_token:
            raise RuntimeError(
                "HF_API_TOKEN / HF_TOKEN is not set in environment. "
                "Please set it in your environment variables or in the Render Dashboard."
            )
        return InferenceClient(token=hf_token, timeout=90)

    def _run_remote_model(self, model_id: str, text: str) -> Optional[Dict[str, Any]]:
        """
        Call the remote Hugging Face model via InferenceClient, with retry.

        All configured models here are text-classification models. We keep a
        fallback 'text-generation' branch for future extension, but it is not
        used by the current configuration.
        """
        self._last_hf_error = None

        if model_id not in self._models:
            self._last_hf_error = f"Unknown model_id: {model_id}"
            return None

        cfg = self._models[model_id]
        task = cfg.get("task", "text-classification")
        repo = cfg["hf_name"]

        if task == "groq-chat":
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                self._last_hf_error = "missing GROQ_API_KEY"
                return None
            import requests, time as _time
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            req = {
                "model": repo,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a legal AI assistant for contract ambiguity analysis.\n"
                            "You MUST do three things:\n"
                            "1) Decide whether the clause is AMBIGUOUS or UNAMBIGUOUS.\n"
                            "2) Provide a confidence score between 0 and 1 (as a decimal number).\n"
                            "3) Provide a brief rationale explaining why, referencing the wording of the clause.\n\n"
                            "Respond in exactly this format (English only):\n"
                            "Label: AMBIGUOUS or UNAMBIGUOUS\n"
                            "Confidence: <number between 0 and 1>\n"
                            "Rationale: <one-sentence explanation>"
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                "temperature": 0.0,
                "max_tokens": 256,
            }
            delays = [0, 2, 5, 10]
            last_err = None
            for attempt, d in enumerate(delays, start=1):
                if d:
                    _time.sleep(d)
                try:
                    resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=req, timeout=60)
                    if resp.status_code == 200:
                        j = resp.json()
                        choices = j.get("choices") or []
                        msg = (choices[0] or {}).get("message", {}) if choices else {}
                        content = msg.get("content") or ""
                        return self._normalize_hf_output(cfg, [{"generated_text": content}])
                    last_err = f"groq_http_{resp.status_code}: {resp.text[:200]}"
                    if resp.status_code in (429, 500, 502, 503):
                        continue
                    break
                except Exception as e:
                    last_err = f"groq_error: {str(e)[:200]}"
                    break
            self._last_hf_error = last_err or "unknown_groq_error"
            return None

        try:
            client = self._get_hf_client()
        except Exception as e:
            self._last_hf_error = f"client_init: {e}"
            return None

        import time as _time
        # Exponential backoff, up to ~1 minute total.
        delays = [0, 2, 4, 8, 16, 32]
        last_err = None

        for attempt, delay in enumerate(delays, start=1):
            if delay:
                _time.sleep(delay)

            try:
                if task == "text-generation":
                    # Not used by the current configuration, but kept for completeness.
                    out = client.text_generation(
                        prompt=text,
                        model=repo,
                        max_new_tokens=96,
                        temperature=0.2,
                        do_sample=False,
                        return_full_text=False,
                    )
                    data = [{"generated_text": out}]
                elif task == "chat-completion":
                    # Require label + confidence + rationale
                    out = client.chat_completion(
                        model=repo,
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are a legal AI assistant for contract ambiguity analysis.\n"
                                    "You MUST do three things:\n"
                                    "1) Decide whether the clause is AMBIGUOUS or UNAMBIGUOUS.\n"
                                    "2) Provide a confidence score between 0 and 1 (as a decimal number).\n"
                                    "3) Provide a brief rationale explaining why, referencing the wording of the clause.\n\n"
                                    "Respond in exactly this format (English only):\n"
                                    "Label: AMBIGUOUS or UNAMBIGUOUS\n"
                                    "Confidence: <number between 0 and 1>\n"
                                    "Rationale: <one-sentence explanation>"
                                ),
                            },
                            {"role": "user", "content": text},
                        ],
                    )
                    try:
                        content = out["choices"][0]["message"]["content"]
                    except Exception:
                        content = str(out)
                    data = [{"generated_text": content}]
                else:
                    # Main path: generic text-classification call.
                    data = client.text_classification(
                        text=text,
                        model=repo,
                    )

                return self._normalize_hf_output(cfg, data)

            except (HfHubHTTPError, InferenceTimeoutError) as e:
                status = getattr(getattr(e, "response", None), "status_code", None)
                body = getattr(getattr(e, "response", None), "text", "") or str(e)
                last_err = f"status={status} body={(body[:300]).replace(chr(10), ' ')}"
                print(f"[HF][attempt {attempt}] {last_err}")
                # Retry on rate limit (429), service unavailable (503), and bad gateway (502/500).
                if status in (429, 502, 503, 500):
                    continue
                break
            except Exception as e:
                last_err = f"other_error: {str(e)[:200]}"
                print(f"[HF][attempt {attempt}] {last_err}")
                break

        self._last_hf_error = last_err or "unknown error"
        return None

    def _normalize_hf_output(self, cfg: Dict[str, Any], data: Any) -> Dict[str, Any]:
        """
        Normalize HF output into a unified format:
        {
            "label": "AMBIGUOUS" or "UNAMBIGUOUS",
            "rationale": "...",
            "score": float  # probability in [0, 1]
        }

        For classification models, we interpret NLI-style labels (e.g., NEUTRAL,
        CONTRADICTION) as indicators of potential ambiguity, and "positive"
        labels (e.g., ENTAILMENT) as relatively clear semantics.
        """
        task = cfg.get("task", "text-classification")

        # ----- Generation-style output -----
        if task in ("text-generation", "chat-completion", "groq-chat"):
            if isinstance(data, list) and data and "generated_text" in data[0]:
                text = str(data[0]["generated_text"])
                up = text.upper()

                # Extract confidence score from model output and normalize to [0, 1]
                score = self._extract_score_from_rationale(text)
                if score is None:
                    score = 0.7
                score = max(0.0, min(1.0, score))

                if "AMBIGUOUS" in up and "UNAMBIGUOUS" not in up:
                    label = "AMBIGUOUS"
                elif "UNAMBIGUOUS" in up or "NOT AMBIGUOUS" in up:
                    label = "UNAMBIGUOUS"
                else:
                    label = "AMBIGUOUS"

                return {
                    "label": label,
                    "rationale": text.strip(),
                    "score": float(score),
                }

            return {
                "label": "AMBIGUOUS",
                "rationale": "Unsupported generation output.",
                "score": 0.5,
            }

        # ----- Classification-style output (main path) -----
        if isinstance(data, list) and data and isinstance(data[0], dict) and "label" in data[0]:
            first = data[0]
            raw = str(first.get("label", "")).upper()
            score = float(first.get("score", 0.9))
            # Force score to be a probability in [0, 1]
            score = max(0.0, min(1.0, score))

            ambiguous_markers = (
                "CONTRADICT",
                "NEUTRAL",
                "UNSURE",
                "UNCERTAIN",
                "UNKNOWN",
                "MIXED",
                "OTHER",
                "NEG",
                "RISK",
                "0",
            )

            if any(k in raw for k in ambiguous_markers):
                label = "AMBIGUOUS"
                rationale = (
                    f"HF ({cfg['hf_name']}) predicted label '{raw}' with confidence {score:.3f}. "
                    "We interpret this as indicating that the clause may admit multiple or "
                    "unstable interpretations (i.e., potential ambiguity in meaning)."
                )
            else:
                label = "UNAMBIGUOUS"
                rationale = (
                    f"HF ({cfg['hf_name']}) predicted label '{raw}' with confidence {score:.3f}. "
                    "We interpret this as suggesting a relatively clear, dominant reading of "
                    "the clause (i.e., lower ambiguity)."
                )

            return {
                "label": label,
                "rationale": rationale,
                "score": score,
            }

        # Fallback if the output format is unknown.
        return {
            "label": "AMBIGUOUS",
            "rationale": "Unknown HF output format.",
            "score": 0.5,
        }

    def _run_batch_chat(self, model_id: str, sentences: List[str], prompt: str) -> Optional[List[Dict[str, Any]]]:
        self._last_hf_error = None
        if model_id not in self._models:
            self._last_hf_error = f"Unknown model_id: {model_id}"
            return None
        cfg = self._models[model_id]
        task = cfg.get("task", "text-classification")
        if task not in ("chat-completion", "groq-chat", "text-generation"):
            return None
        repo = cfg["hf_name"]

        items = [{"id": i + 1, "sentence": s} for i, s in enumerate(sentences)]
        sys_msg = (
            "Return only strict JSON array. Each element must have keys: sentence, label, rationale, score. "
            "label must be AMBIGUOUS or UNAMBIGUOUS. "
            "score must be a probability number between 0 and 1. "
            "rationale must be a brief English explanation of why the clause is classified that way. "
            "No extra text."
        )
        user_msg = json.dumps({
            "instruction": prompt,
            "items": items,
        }, ensure_ascii=False)

        try:
            if task == "groq-chat":
                api_key = os.getenv("GROQ_API_KEY")
                if not api_key:
                    self._last_hf_error = "missing GROQ_API_KEY"
                    return None
                import requests
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                req = {
                    "model": repo,
                    "messages": [
                        {"role": "system", "content": sys_msg},
                        {"role": "user", "content": user_msg},
                    ],
                    "temperature": 0.0,
                    "max_tokens": 2048,
                }
                resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=req, timeout=90)
                if resp.status_code != 200:
                    self._last_hf_error = f"groq_http_{resp.status_code}: {resp.text[:200]}"
                    return None
                j = resp.json()
                choices = j.get("choices") or []
                msg = (choices[0] or {}).get("message", {}) if choices else {}
                content = msg.get("content") or ""
            else:
                client = self._get_hf_client()
                out = client.chat_completion(
                    model=repo,
                    messages=[
                        {"role": "system", "content": sys_msg},
                        {"role": "user", "content": user_msg},
                    ],
                )
                try:
                    content = out["choices"][0]["message"]["content"]
                except Exception:
                    content = str(out)

            try:
                parsed = json.loads(content)
            except Exception:
                try:
                    import re as _re
                    m = _re.search(r"\[\s*\{[\s\S]*\}\s*\]", content)
                    if m:
                        parsed = json.loads(m.group(0))
                    else:
                        return None
                except Exception:
                    return None

            if not isinstance(parsed, list) or len(parsed) != len(sentences):
                return None

            out_list: List[Dict[str, Any]] = []
            for i, it in enumerate(parsed):
                sent = sentences[i]
                lbl = str(it.get("label", "AMBIGUOUS")).upper()
                if "UNAMBIGUOUS" in lbl or "NOT AMBIGUOUS" in lbl:
                    lbl = "UNAMBIGUOUS"
                elif "AMBIGUOUS" in lbl:
                    lbl = "AMBIGUOUS"
                else:
                    lbl = "AMBIGUOUS"
                rat = str(it.get("rationale", "")).strip()

                raw_score = it.get("score", None)
                if isinstance(raw_score, (int, float)):
                    val = float(raw_score)
                    if 0.0 <= val <= 1.0:
                        score = val
                    elif 1.0 < val <= 100.0:
                        score = val / 100.0
                    else:
                        score = 0.7
                else:
                    score = self._extract_score_from_rationale(rat) or 0.7
                score = max(0.0, min(1.0, score))

                out_list.append({
                    "sentence": sent,
                    "label": lbl,
                    "rationale": rat,
                    "score": float(score),
                })
            return out_list
        except Exception as e:
            self._last_hf_error = str(e)[:200]
            return None

    def _run_inference(self, sentence: str, prompt: str) -> Dict[str, Any]:
        """
        High-level inference wrapper.

        For classification models we simply send the raw sentence to the model.
        The configured prompt is not used by HF directly, but is still part of
        the public API for future extension or local models.
        """
        model = self.get_current_model()
        task = model.get("task")

        if task == "text-classification":
            text = sentence
        else:
            # Currently not used by our configuration, kept for completeness.
            try:
                text = prompt.format(clause=sentence)
            except Exception:
                text = f"{prompt}\nClause: {sentence}\n"

        out = self._run_remote_model(model["id"], text)
        # Do not fall back to other models; if the primary model fails, raise an error
        # so that the caller can mark this sentence as ERROR.
        if not out:
            hint = f" Last HF error: {self._last_hf_error}" if self._last_hf_error else ""
            raise RuntimeError(
                f"Hugging Face model unavailable. "
                f"Check HF_API_TOKEN / HF_TOKEN, network, and model id '{model['hf_name']}'.{hint}"
            )

        out["rationale"] = "[HF] " + str(out.get("rationale", "")).lstrip()
        return out

    # ---------- persistence helpers ----------
    def _extract_score_from_rationale(self, rationale: str) -> Optional[float]:
        """
        Try to extract a numeric confidence score from the model output or rationale text.
        This returns a float in [0, 1] if possible:
        - If the extracted value is already between 0 and 1, use it directly.
        - If the extracted value is between 1 and 100, treat it as a percentage and divide by 100.
        """
        if not rationale:
            return None

        patterns = [
            r"confidence\s*:?\s*([0-9]+\.?[0-9]*)",
            r"score\s*:?\s*([0-9]+\.?[0-9]*)",
            r"probability\s*:?\s*([0-9]+\.?[0-9]*)",
        ]

        for pattern in patterns:
            match = re.search(pattern, rationale, re.IGNORECASE)
            if match:
                try:
                    val = float(match.group(1))
                    if 0.0 <= val <= 1.0:
                        return val
                    if 1.0 < val <= 100.0:
                        return val / 100.0
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
        score: float,
        auto_commit: bool = True,
    ) -> Optional[int]:
        """
        Persist a single result into the ContractSentence table, if possible.
        """
        if not contract_id:
            return None

        try:
            # First try to match the sentence text exactly.
            row = (
                db.query(ContractSentence)
                .filter(
                    ContractSentence.contract_id == contract_id,
                    ContractSentence.sentence == sentence,
                )
                .first()
            )

            # Fallback: pick the earliest sentence without explanation.
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
        row.clarity_score = score
        row.updated_at = datetime.now(timezone.utc)

        db.add(row)
        if auto_commit:
            db.commit()
            db.refresh(row)
        return row.id

    # ---------- public APIs ----------
    def classify_sentences(
        self,
        sentences: List[str],
        prompt_id: Optional[str],
        custom_prompt: Optional[str],
        db: Session,
        user_id: int,
        contract_id: Optional[int],
    ) -> List[ClassifyResult]:
        """
        Classify a list of sentences as AMBIGUOUS / UNAMBIGUOUS and optionally
        persist the results to the database.
        """
        prompt = self._get_prompt(prompt_id, custom_prompt)
        model = self.get_current_model()
        res: List[ClassifyResult] = []

        for idx, s in enumerate(sentences):
            inf = self._run_inference(s, prompt)
            sid = self._persist_result(db, user_id, contract_id, s, inf["label"], inf["rationale"], inf["score"])
            res.append(
                ClassifyResult(
                    sentence=s,
                    label=inf["label"],
                    score=inf["score"],  # probability in [0, 1]
                    model_id=model["id"],
                    rationale=inf["rationale"],
                    contract_id=contract_id,
                    sentence_id=sid,
                )
            )
            # Small delay between single-sentence classifications to reduce request rate.
            time.sleep(0.5)

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
        """
        Explain ambiguity for a single sentence.
        """
        prompt = self._get_prompt(prompt_id, custom_prompt)
        model = self.get_current_model()
        inf = self._run_inference(sentence, prompt)
        sid = self._persist_result(db, user_id, contract_id, sentence, inf["label"], inf["rationale"], inf["score"])
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
        """
            Explain ambiguity for a batch of sentences, committing in batches
            for robustness and logging progress as we go.
            """
        import logging

        logger = logging.getLogger(__name__)

        prompt = self._get_prompt(prompt_id, custom_prompt)
        model = self.get_current_model()
        out: List[ExplainResult] = []
        total = len(sentences)

        logger.info(f"[PromptLab] Starting batch processing: {total} sentences, contract_id={contract_id}")

        BATCH_SIZE = 50
        for i in range(0, len(sentences), BATCH_SIZE):
            batch = sentences[i : i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
            logger.info(
                f"[PromptLab] Processing batch {batch_num}/{total_batches} "
                f"({i+1}-{min(i+BATCH_SIZE, total)}/{total})"
            )

            used_batch_chat = False
            try:
                if model.get("task") == "chat-completion":
                    batch_inf = self._run_batch_chat(model["id"], batch, prompt)
                    if batch_inf:
                        used_batch_chat = True
                        for idx_in_batch, inf in enumerate(batch_inf):
                            s = batch[idx_in_batch]
                            sid = self._persist_result(
                                db,
                                user_id,
                                contract_id,
                                s,
                                inf["label"],
                                inf["rationale"],
                                inf.get("score", 0.7),
                                auto_commit=False,
                            )
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
                logger.error(f"[PromptLab] Batch chat failed: {str(e)[:200]}")

            if not used_batch_chat:
                for idx_in_batch, s in enumerate(batch):
                    try:
                        inf = self._run_inference(s, prompt)
                        sid = self._persist_result(
                            db,
                            user_id,
                            contract_id,
                            s,
                            inf["label"],
                            inf["rationale"],
                            inf["score"],
                            auto_commit=False,
                        )
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
                        logger.error(
                            f"[PromptLab] Failed to process sentence {i+idx_in_batch+1}/{total}: {str(e)[:200]}"
                        )
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

                    time.sleep(0.5)

            try:
                db.commit()
                logger.info(f"[PromptLab] Batch {batch_num}/{total_batches} committed successfully")

                if progress_callback:
                    progress_callback(i + len(batch), total)

            except Exception as e:
                db.rollback()
                logger.error(
                    f"[PromptLab] Database commit failed for batch {batch_num}: {str(e)[:200]}"
                )

        logger.info(f"[PromptLab] Batch processing completed: {len(out)} results")
        return out
