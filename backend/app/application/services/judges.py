from typing import Dict, List, Optional, Literal
from os import getenv
import json

from app.integration.judges.groq_llama31_8b import GroqLlama31_8B_Judge
from app.integration.judges.groq_llama33_70b import GroqLlama33_70B_Judge
from app.integration.judges.hf_prometheus2_7b import HFPrometheus2_7B_Judge
from app.presentation.routes.rubric import build_prompt

Label = Literal["Ambiguous", "Unambiguous"]


class JudgeClient:


    def __init__(self, judge_id: str, endpoint: str):
        self.judge_id = judge_id
        self.endpoint = endpoint  # 例如已有的推理网关/本地服务/云端API

    def _make_model(self):
 
        jid = (self.judge_id or "").strip().lower()
        if jid.startswith("groq/llama-3.1-8b") or jid == "judge-mini-a":
            return GroqLlama31_8B_Judge()
        if jid.startswith("groq/llama-3.3-70b") or jid == "judge-mini-b":
            return GroqLlama33_70B_Judge()
        if jid.startswith("hf/prometheus-7b-v2.0") or jid == "judge-mini-c":
            return HFPrometheus2_7B_Judge()
    
        return GroqLlama31_8B_Judge()

    def _parse_json(self, txt: str) -> dict:

        try:
            return json.loads(txt)
        except Exception:
            s = txt.find("{")
            e = txt.rfind("}")
            if s >= 0 and e > s:
                try:
                    return json.loads(txt[s:e+1])
                except Exception:
                    pass
        return {}

    def judge_class_correct_if_no_gold(self, sentence: str, pred_class: Label) -> Optional[bool]:

        try:
            model = self._make_model()

            criteria: Dict[str, bool] = {}
            manual_metrics: List[str] = []
            lt_stub = {"issues": [], "issues_per_100_tok": 0}
            prompt = build_prompt({"sentence": sentence, "rationale": ""}, criteria, manual_metrics, lt_stub, True)
            res = model.judge({"prompt": prompt, "temperature": 0.0, "require_json": True})
            data = self._parse_json(res.get("json", "{}"))
            jl = str(data.get("judge_label", "")).strip().lower()
            pred = "ambiguous" if str(pred_class).lower().startswith("a") else "unambiguous"
            if jl in ("ambiguous", "unambiguous"):
                return jl == pred
            return None
        except Exception:
            return None

    def judge_rationale_by_rubrics(
        self,
        sentence: str,
        pred_class: Label,
        rationale: str,
        rubrics: List[str],
        custom_metrics: List[str],
    ) -> Dict[str, Dict[str, bool]]:

    
        try:
            model = self._make_model()
  
            cn2en = {
                "grammar": "grammar",
                "word_choice": "word_choice",
                "cohesion": "cohesion",
                "conciseness": "conciseness",
                "completeness": "completeness",
                "correctness": "correctness",
                "clarity": "clarity",
            }
            en_selected = [cn2en[r] for r in rubrics if r in cn2en]

            criteria: Dict[str, bool] = {k: True for k in en_selected}
            lt_stub = {"issues": [], "issues_per_100_tok": 0}
            prompt = build_prompt({"sentence": sentence, "rationale": rationale or ""}, criteria, custom_metrics, lt_stub, True)
            res = model.judge({"prompt": prompt, "temperature": 0.0, "require_json": True})
            data = self._parse_json(res.get("json", "{}"))
            out_rubrics: Dict[str, bool] = {}
            out_custom: Dict[str, bool] = {}
            rb = data.get("rubric", {}) or {}
            mn = data.get("manual", {}) or {}

            for r in rubrics:
                en = cn2en.get(r)
                leaf = rb.get(en) or {}
                out_rubrics[r] = bool(leaf.get("pass", False))
            for c in custom_metrics:
                leaf = mn.get(c) or {}
                out_custom[c] = bool(leaf.get("pass", False))
            return {"rubrics": out_rubrics, "custom": out_custom}
        except Exception:

            return {"rubrics": {r: False for r in rubrics}, "custom": {c: False for c in custom_metrics}}


def get_available_judges() -> Dict[str, JudgeClient]:
    """
    用配置驱动。从环境/配置文件读取三位评委的 endpoint/model_id。
    示例：EVAL_JUDGES='judge-mini-a=http://...;judge-mini-b=http://...;judge-mini-c=http://...'
    """
    mapping: Dict[str, JudgeClient] = {}
    raw = getenv("EVAL_JUDGES", "").strip()
    if raw:
        for item in raw.split(";"):
            if not item.strip():
                continue
            parts = item.split("=", 1)
            if len(parts) != 2:
                continue
            jid, endpoint = parts
            mapping[jid.strip()] = JudgeClient(judge_id=jid.strip(), endpoint=endpoint.strip())

    if not mapping:
        # The bottom three positions (if it has been configured in the project, it won't reach here)
        mapping = {
            "judge-mini-a": JudgeClient("judge-mini-a", "http://localhost:9001"),
            "judge-mini-b": JudgeClient("judge-mini-b", "http://localhost:9002"),
            "judge-mini-c": JudgeClient("judge-mini-c", "http://localhost:9003"),
        }

    return mapping