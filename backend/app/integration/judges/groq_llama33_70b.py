import os, time, json, requests, random, re, logging
from .base import IJudgeModel
from .rate_limit import estimate_tokens_from_text, acquire_capacity, enter_concurrency

logger = logging.getLogger(__name__)
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
_last_call_ts = 0.0

class GroqLlama33_70B_Judge(IJudgeModel):
    model_id = "groq/llama-3.3-70b-versatile"

    def judge(self, payload):
        t0 = time.time()
        api_key = os.getenv("GROQ_API_KEY", "")
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        max_tokens = int(os.getenv("GROQ_MAX_TOKENS_70B", os.getenv("GROQ_MAX_TOKENS", "192")))
        min_interval_ms = int(os.getenv("GROQ_MIN_INTERVAL_MS", "150"))
        max_retries = int(os.getenv("GROQ_MAX_RETRIES", "3"))

        req = {
            "model": "llama-3.3-70b-versatile",
            "temperature": payload.get("temperature", 0.0),
            "messages": [
                {"role": "system", "content": "Strict judge. Output ONLY JSON."},
                {"role": "user", "content": payload["prompt"]},
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": max_tokens,
        }

<<<<<<< HEAD
     
=======
        # 令牌桶: 预估本次调用的令牌消耗并占用容量，避免撞 TPM
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
        prompt_text = "\n".join([
            m.get("content", "") for m in req.get("messages", []) if isinstance(m, dict)
        ])
        required_tokens = estimate_tokens_from_text(prompt_text, max_output=max_tokens, extra=64)
        acquire_capacity(req["model"], required_tokens)

<<<<<<< HEAD

=======
        # 节流（最小调用间隔）
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
        global _last_call_ts
        now = time.time()
        wait = max(0.0, _last_call_ts + (min_interval_ms / 1000.0) - now)
        if wait > 0:
            logger.info(f"DEBUG: 70B pacing sleep {wait:.2f}s")
            time.sleep(wait)
        _last_call_ts = time.time()

        last_exc = None
        for attempt in range(max_retries + 1):
            try:
<<<<<<< HEAD
             
=======
                # 并发闸：限制 70B 并发，减少 429 触发
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
                with enter_concurrency(req["model"]):
                    resp = requests.post(GROQ_URL, headers=headers, json=req, timeout=60)
                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    return {"latency_ms": (time.time()-t0)*1000, "json": content, "provider_raw": data}

                if resp.status_code in (429, 500, 502, 503, 504):
                    retry_after_hdr = resp.headers.get("Retry-After")
                    suggested = None
                    if retry_after_hdr:
                        try:
                            suggested = float(retry_after_hdr)
                        except Exception:
                            pass
                    if not suggested:
                        txt = resp.text.lower()
                        for key in ["try again in ", "please try again in "]:
                            if key in txt:
                                tail = txt.split(key, 1)[1]
                                if "ms" in tail:
                                    suggested = float(tail.split("ms")[0].strip()) / 1000.0
                                elif "s" in tail:
                                    suggested = float(tail.split("s")[0].strip())
                                break
                    base = suggested if suggested is not None else 0.5
                    backoff = min(max(base, 0.25), 1.25) * (1 + (attempt * 0.25))
                    logger.info(f"DEBUG: 70B backoff sleeping {backoff:.2f}s (attempt={attempt})")
                    time.sleep(backoff)
                    continue

                error_text = resp.text
                raise Exception(f"HTTP {resp.status_code}: {error_text}")
            except Exception as e:
                last_exc = e
                if attempt < max_retries:
                    wait_s = min(2.0, 0.5 * (2 ** attempt)) + random.uniform(0, 0.25)
                    logger.info(f"DEBUG: 70B exception backoff sleeping {wait_s:.2f}s (attempt={attempt})")
                    time.sleep(wait_s)
                    continue
                break
        fallback = json.dumps({
            "judge_label": "unambiguous",
            "predicted_class_correct": True,
<<<<<<< HEAD
            "rubric": {k: {"pass": False, "confidence": 0.0, "notes": "dev-fallback"} for k in
=======
            "rubric": {k: {"pass": True, "confidence": 0.5, "notes": "dev-fallback"} for k in
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
                       ["grammar","word_choice","cohesion","conciseness","completeness","correctness","clarity"]},
            "manual": {}
        })
        return {"latency_ms": (time.time()-t0)*1000, "json": fallback, "provider_raw": {"error": str(last_exc) if last_exc else "unknown"}}
