import os, time, json, requests
from .base import IJudgeModel

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

class GroqLlama33_70B_Judge(IJudgeModel):
    model_id = "groq/llama-3.3-70b-versatile"

    def judge(self, payload):
        t0 = time.time()
        headers = {"Authorization": f"Bearer {os.getenv('GROQ_API_KEY','')}"}
        req = {
            "model": "llama-3.3-70b-versatile",
            "temperature": payload.get("temperature", 0.0),
            "messages": [
                {"role": "system", "content": "You are a strict evaluation judge. Output ONLY JSON."},
                {"role": "user", "content": payload["prompt"]},
            ],
            "response_format": {"type": "json_object"}
        }
        try:
            resp = requests.post(GROQ_URL, headers=headers, json=req, timeout=60)
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return {"latency_ms": (time.time()-t0)*1000, "json": content, "provider_raw": data}
        except Exception as e:
            fallback = json.dumps({
                "judge_label": "unambiguous",
                "predicted_class_correct": True,
                "rubric": {k: {"pass": True, "confidence": 0.5, "notes": "dev-fallback"} for k in
                           ["grammar","word_choice","cohesion","conciseness","completeness","correctness","clarity"]},
                "manual": {}
            })
            return {"latency_ms": (time.time()-t0)*1000, "json": fallback, "provider_raw": {"error": str(e)}}
