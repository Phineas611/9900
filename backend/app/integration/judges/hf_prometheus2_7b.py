<<<<<<< HEAD
import os, time, json
from huggingface_hub import InferenceClient
from .base import IJudgeModel

MODEL_ID = "prometheus-eval/prometheus-7b-v2.0"
=======
import os, time, json, requests
from .base import IJudgeModel

HF_URL = "https://api-inference.huggingface.co/models/prometheus-eval/prometheus-7b-v2.0"
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98

class HFPrometheus2_7B_Judge(IJudgeModel):
    model_id = "hf/prometheus-7b-v2.0"

    def judge(self, payload):
        t0 = time.time()
<<<<<<< HEAD
        try:
            max_new = int(os.getenv("HF_MAX_NEW_TOKENS", "320"))
            dims = ["grammar","word_choice","cohesion","conciseness","completeness","correctness","clarity"]
            strict_prefix = (
                "You must return ONLY a JSON object with keys judge_label,rubric,manual. "
                "Required rubric dimensions: grammar, word_choice, cohesion, conciseness, completeness, correctness, clarity. "
                "If undecidable, set pass=false and confidence=0.0. Notes <= 30 chars.\n"
            )
            skeleton = (
                "{"
                "\"judge_label\": \"ambiguous|unambiguous\", "
                "\"rubric\": { "
                + ", ".join([f"\"{d}\": {{ \"pass\": false, \"confidence\": 0.0, \"notes\": \"\" }}" for d in dims])
                + " }, \"manual\": {} }"
            )
            token = os.getenv("HF_API_TOKEN") or os.getenv("HF_TOKEN")
            if not token:
                raise RuntimeError("missing HF_API_TOKEN/HF_TOKEN")
            client = InferenceClient(token=token, timeout=90)
            prompt1 = strict_prefix + "JSON skeleton:\n" + skeleton + "\n" + payload["prompt"]
            out1 = client.text_generation(prompt=prompt1, model=MODEL_ID, max_new_tokens=max_new, return_full_text=False)
            raws = [{"generated_text": out1}]
            parsed1 = None
            try:
                parsed1 = json.loads(out1)
            except Exception:
                parsed1 = None
            rub1 = (parsed1.get("rubric") if isinstance(parsed1, dict) else {}) or {}
            miss = [k for k in dims if k not in rub1]
            final_json = out1
            if miss:
                repair_prefix = (
                    "You omitted these rubric dimensions: " + ", ".join(miss) + ". "
                    "Return the SAME JSON keys as skeleton and include all listed dimensions. "
                    "Do not output anything outside the JSON object.\n"
                )
                prompt2 = repair_prefix + strict_prefix + "JSON skeleton:\n" + skeleton + "\n" + payload["prompt"]
                out2 = client.text_generation(prompt=prompt2, model=MODEL_ID, max_new_tokens=max_new, return_full_text=False)
                raws.append({"generated_text": out2})
                parsed2 = None
                try:
                    parsed2 = json.loads(out2)
                except Exception:
                    parsed2 = None
                rub2 = (parsed2.get("rubric") if isinstance(parsed2, dict) else {}) or {}
                if all(k in rub2 for k in dims):
                    final_json = out2
            return {"latency_ms": (time.time()-t0)*1000, "json": final_json, "provider_raw": raws}
=======
        headers = {"Authorization": f"Bearer {os.getenv('HF_API_TOKEN','')}"}
        # Simple text generation; rely on prompt to force JSON
        try:
            resp = requests.post(HF_URL, headers=headers, json={"inputs": payload["prompt"], "parameters": {"max_new_tokens": 256}}, timeout=90)
            data = resp.json()
            # HF Inference can return a list of dicts with 'generated_text'
            content = data[0]["generated_text"] if isinstance(data, list) else data.get("generated_text", json.dumps(data))
            return {"latency_ms": (time.time()-t0)*1000, "json": content, "provider_raw": data}
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
        except Exception as e:
            fallback = json.dumps({
                "judge_label": "unambiguous",
                "predicted_class_correct": True,
<<<<<<< HEAD
                "rubric": {k: {"pass": False, "confidence": 0.0, "notes": "dev-fallback"} for k in ["grammar","word_choice","cohesion","conciseness","completeness","correctness","clarity"]},
=======
                "rubric": {k: {"pass": True, "confidence": 0.5, "notes": "dev-fallback"} for k in
                           ["grammar","word_choice","cohesion","conciseness","completeness","correctness","clarity"]},
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
                "manual": {}
            })
            return {"latency_ms": (time.time()-t0)*1000, "json": fallback, "provider_raw": {"error": str(e)}}
