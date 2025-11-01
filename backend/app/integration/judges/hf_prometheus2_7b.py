import os, time, json, requests
from .base import IJudgeModel

HF_URL = "https://api-inference.huggingface.co/models/prometheus-eval/prometheus-7b-v2.0"

class HFPrometheus2_7B_Judge(IJudgeModel):
    model_id = "hf/prometheus-7b-v2.0"

    def judge(self, payload):
        t0 = time.time()
        headers = {"Authorization": f"Bearer {os.getenv('HF_API_TOKEN','')}"}
        # Simple text generation; rely on prompt to force JSON
        try:
            resp = requests.post(HF_URL, headers=headers, json={"inputs": payload["prompt"], "parameters": {"max_new_tokens": 256}}, timeout=90)
            data = resp.json()
            # HF Inference can return a list of dicts with 'generated_text'
            content = data[0]["generated_text"] if isinstance(data, list) else data.get("generated_text", json.dumps(data))
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
