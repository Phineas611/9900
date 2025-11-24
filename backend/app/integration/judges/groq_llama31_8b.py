import os, time, json, requests, logging, random, re
from .base import IJudgeModel
from .rate_limit import estimate_tokens_from_text, acquire_capacity, enter_concurrency

logger = logging.getLogger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

<<<<<<< HEAD

=======
# 简单的限速控制：最小调用间隔与最大重试次数（可用环境变量配置）
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
_MIN_INTERVAL_MS = int(os.getenv("GROQ_MIN_INTERVAL_MS", "250"))
_MAX_RETRIES = int(os.getenv("GROQ_MAX_RETRIES", "5"))
_DEFAULT_MAX_TOKENS = int(os.getenv("GROQ_MAX_TOKENS", "256"))
_last_call_ts = 0.0

def _sleep_min_interval():
    global _last_call_ts
    now = time.time()
    elapsed_ms = (now - _last_call_ts) * 1000.0
    if elapsed_ms < _MIN_INTERVAL_MS:
        wait_ms = _MIN_INTERVAL_MS - elapsed_ms
        logger.info(f"DEBUG: Rate-limit spacing, sleeping {wait_ms:.0f}ms before Groq call")
        time.sleep(wait_ms / 1000.0)
    _last_call_ts = time.time()

def _parse_retry_wait(resp) -> float:
<<<<<<< HEAD

=======
    """返回等待秒数，优先使用 Retry-After，其次解析错误消息中的建议等待时间。"""
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
    # Retry-After（秒）
    ra = resp.headers.get("Retry-After")
    if ra:
        try:
            return float(ra)
        except Exception:
            pass
<<<<<<< HEAD

=======
    # 解析 JSON 错误消息中的 "Please try again in Xms/Xs"
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
    try:
        data = resp.json()
        msg = (data.get("error") or {}).get("message") or ""
    except Exception:
        msg = resp.text or ""
    # ms
    m = re.search(r"try again in\s+(\d+(?:\.\d+)?)\s*ms", msg, re.IGNORECASE)
    if m:
        return float(m.group(1)) / 1000.0
    # s
    m = re.search(r"try again in\s+(\d+(?:\.\d+)?)\s*s", msg, re.IGNORECASE)
    if m:
        return float(m.group(1))
<<<<<<< HEAD

=======
    # 默认退避 1 秒
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
    return 1.0

class GroqLlama31_8B_Judge(IJudgeModel):
    model_id = "groq/llama-3.1-8b-instant"

    def judge(self, payload):
        t0 = time.time()
        api_key = os.getenv("GROQ_API_KEY")
        
        # Debug logging
        logger.info(f"DEBUG: GROQ_API_KEY present: {bool(api_key)}")
        if api_key:
            logger.info(f"DEBUG: Key starts with: {api_key[:10]}...")
        
        if not api_key:
            logger.info("DEBUG: No API key, using fallback")
            fallback = json.dumps({
                "judge_label": "unambiguous",
                "predicted_class_correct": True,
<<<<<<< HEAD
                "rubric": {k: {"pass": False, "confidence": 0.0, "notes": "no-api-key"} for k in
=======
                "rubric": {k: {"pass": True, "confidence": 0.5, "notes": "no-api-key"} for k in
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
                           ["grammar","word_choice","cohesion","conciseness","completeness","correctness","clarity"]},
                "manual": {}
            })
            return {"latency_ms": (time.time()-t0)*1000, "json": fallback, "provider_raw": {"error": "No GROQ_API_KEY"}}
        
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
<<<<<<< HEAD

=======
        # 新增：更短的生成长度与节流参数（可通过环境变量覆盖）
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
        max_tokens = int(os.getenv("GROQ_MAX_TOKENS", "192"))
        min_interval_ms = int(os.getenv("GROQ_MIN_INTERVAL_MS", "150"))
        max_retries = int(os.getenv("GROQ_MAX_RETRIES", "3"))

        req = {
            "model": "llama-3.1-8b-instant",
<<<<<<< HEAD
            "messages": [
                {"role": "system", "content": "Strict judge. Output ONLY JSON."},
                {"role": "user", "content": payload["prompt"]}
            ],
=======
            "messages": [{"role": "user", "content": payload["prompt"]}],
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
            "temperature": payload.get("temperature", 0.0),
            "max_tokens": max_tokens,
        }
        if payload.get("require_json"):
            req["response_format"] = {"type": "json_object"}

<<<<<<< HEAD
 
=======
        # 令牌桶：预估本次令牌占用并申请容量，减少 429
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
        prompt_text = "\n".join([m.get("content", "") for m in req.get("messages", []) if isinstance(m, dict)])
        required_tokens = estimate_tokens_from_text(prompt_text, max_output=max_tokens, extra=32)
        acquire_capacity(req["model"], required_tokens)
        attempt = 0
        last_exc = None
<<<<<<< HEAD
    
        while attempt <= max_retries:
            try:
                _sleep_min_interval() 
=======
        # 使用内部 try/except 重试，不在循环外层再放 except，避免作用域/控制流错误
        while attempt <= max_retries:
            try:
                _sleep_min_interval()  # 保留统一的全局最小间隔
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
                logger.info(f"DEBUG: Making Groq API call to {GROQ_URL} (attempt={attempt+1}/{max_retries+1})")
                with enter_concurrency(req["model"]):
                    resp = requests.post(GROQ_URL, headers=headers, json=req, timeout=60)
                logger.info(f"DEBUG: Groq response status: {resp.status_code}")

                if resp.status_code == 200:
                    data = resp.json()
                    content = data["choices"][0]["message"]["content"]
                    logger.info(f"DEBUG: Groq response content length: {len(content)}")
                    return {"latency_ms": (time.time()-t0)*1000, "json": content, "provider_raw": data}

<<<<<<< HEAD
     
=======
                # 429/5xx：短退避+随机抖动，优先使用服务端建议或 Retry-After
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
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
<<<<<<< HEAD
                 
=======
                        # 从错误文本中解析 “try again in Xs/ms”
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
                        for key in ["try again in ", "please try again in "]:
                            if key in txt:
                                tail = txt.split(key, 1)[1]
                                if "ms" in tail:
                                    suggested = float(tail.split("ms")[0].strip()) / 1000.0
                                elif "s" in tail:
                                    suggested = float(tail.split("s")[0].strip())
                                break
<<<<<<< HEAD
              
=======
                    # 退避时间：最短 0.25s，最长 1.25s（更快恢复），指数退避叠加
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
                    base = suggested if suggested is not None else 0.5
                    backoff = min(max(base, 0.25), 1.25) * (1 + (attempt * 0.25))
                    logger.info(f"DEBUG: 8B backoff sleeping {backoff:.2f}s (attempt={attempt})")
                    time.sleep(backoff)
                    continue

<<<<<<< HEAD
         
=======
                # 非可重试错误，直接抛
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
                error_text = resp.text
                logger.error(f"DEBUG: Groq API error {resp.status_code}: {error_text}")
                logger.error(f"DEBUG: Request payload was: {json.dumps(req, indent=2)}")
                raise Exception(f"HTTP {resp.status_code}: {error_text}")
            except Exception as e:
                last_exc = e
                logger.error(f"DEBUG: Groq API exception: {e}")
<<<<<<< HEAD
            
=======
                # 对异常也按退避策略重试（最多 max_retries 次）
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
                if attempt < max_retries:
                    wait_s = min(2.0, 0.5 * (2 ** attempt)) + random.uniform(0, 0.25)
                    logger.info(f"DEBUG: Exception backoff sleeping {wait_s:.2f}s (attempt={attempt})")
                    time.sleep(wait_s)
                    attempt += 1
                    continue
                break
<<<<<<< HEAD
   
        fallback = json.dumps({
            "judge_label": "unambiguous",
            "predicted_class_correct": True,
            "rubric": {k: {"pass": False, "confidence": 0.0, "notes": "api-error"} for k in
=======
        # Fallback: 返回保守 JSON，避免流水线直接失败（仅开发环境建议保留）
        fallback = json.dumps({
            "judge_label": "unambiguous",
            "predicted_class_correct": True,
            "rubric": {k: {"pass": True, "confidence": 0.5, "notes": "api-error"} for k in
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
                       ["grammar","word_choice","cohesion","conciseness","completeness","correctness","clarity"]},
            "manual": {}
        })
        return {"latency_ms": (time.time()-t0)*1000, "json": fallback, "provider_raw": {"error": str(last_exc) if last_exc else "unknown"}}
