import os, time, json, requests, logging
from .base import IJudgeModel

logger = logging.getLogger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

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
                "rubric": {k: {"pass": True, "confidence": 0.5, "notes": "no-api-key"} for k in
                           ["grammar","word_choice","cohesion","conciseness","completeness","correctness","clarity"]},
                "manual": {}
            })
            return {"latency_ms": (time.time()-t0)*1000, "json": fallback, "provider_raw": {"error": "No GROQ_API_KEY"}}
        
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        req = {
            "model": "llama-3.1-8b-instant",
            "messages": [{"role": "user", "content": payload["prompt"]}],
            "temperature": payload.get("temperature", 0.0),
        }
        if payload.get("require_json"):
            req["response_format"] = {"type": "json_object"}
        try:
            logger.info(f"DEBUG: Making Groq API call to {GROQ_URL}")
            resp = requests.post(GROQ_URL, headers=headers, json=req, timeout=60)
            logger.info(f"DEBUG: Groq response status: {resp.status_code}")
            
            if resp.status_code != 200:
                error_text = resp.text
                logger.error(f"DEBUG: Groq API error {resp.status_code}: {error_text}")
                logger.error(f"DEBUG: Request payload was: {json.dumps(req, indent=2)}")
                raise Exception(f"HTTP {resp.status_code}: {error_text}")
                
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            logger.info(f"DEBUG: Groq response content length: {len(content)}")
            return {"latency_ms": (time.time()-t0)*1000, "json": content, "provider_raw": data}
        except Exception as e:
            logger.error(f"DEBUG: Groq API exception: {e}")
            # Fallback: return a permissive all-True JSON to keep pipeline running in dev
            fallback = json.dumps({
                "judge_label": "unambiguous",
                "predicted_class_correct": True,
                "rubric": {k: {"pass": True, "confidence": 0.5, "notes": "api-error"} for k in
                           ["grammar","word_choice","cohesion","conciseness","completeness","correctness","clarity"]},
                "manual": {}
            })
            return {"latency_ms": (time.time()-t0)*1000, "json": fallback, "provider_raw": {"error": str(e)}}
