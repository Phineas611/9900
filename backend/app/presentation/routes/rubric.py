import os, json, requests
from typing import Dict, Any, List

LT_PUBLIC_URL = os.getenv("LT_HOST", "https://api.languagetool.org/v2/check")

RUBRIC_DEF = {
    "grammar": "No grammatical/spelling errors that impede understanding. Minor typos permitted if do not affect meaning.",
    "word_choice": "Uses precise and appropriate legal terminology; avoids vague words.",
    "cohesion": "Logical flow; rationale links claim and evidence with proper connectives.",
    "conciseness": "No redundancy; delivers only necessary information while preserving meaning.",
    "completeness": "Covers all key aspects required to justify the predicted class.",
    "correctness": "Reasoning is factually consistent with the sentence and label; no hallucination.",
    "clarity": "Unambiguous, easy to understand by a practitioner.",
}

def language_tool_check(text: str, lang: str="en") -> Dict[str, Any]:
    """Return simple evidence for grammar quality using LanguageTool HTTP API."""
    try:
        r = requests.post(LT_PUBLIC_URL, data={"text": text, "language": lang}, timeout=15)
        j = r.json()
        matches = j.get("matches", [])
        return {
            "issues": len(matches),
            "issues_per_100_tok": round(100 * len(matches) / max(1, len(text.split())), 2),
            "provider": "LanguageTool"
        }
    except Exception as e:
        return {"issues": 0, "issues_per_100_tok": 0.0, "provider": "LanguageTool", "error": str(e)}

def build_prompt(item: Dict[str, Any], criteria: Dict[str, bool], manual_metrics: list,
                 lt_evidence: Dict[str, Any], require_json: bool=True) -> str:
    # 打乱 rubric 顺序以削弱位置偏差
    import random
    active_dims = [k for k, v in criteria.items() if v and k in RUBRIC_DEF]
    random.shuffle(active_dims)
    rubrics = "\n".join([f"- {k}: {RUBRIC_DEF[k]}" for k in active_dims])
    manual = "\n".join([f"- {m}: binary yes/no based on user-defined rule" for m in manual_metrics])
    json_hint = (
        "Do NOT include chain-of-thought; return ONLY this JSON object: "
        "{"
        " \"judge_label\": \"ambiguous|unambiguous\", "
        " \"rubric\": { \"<dim>\": { \"pass\": bool, \"confidence\": decimal in [0,1] (2 digits), \"notes\": string } }, "
        " \"manual\": { \"<metric>\": { \"pass\": bool, \"confidence\": decimal in [0,1] (2 digits), \"notes\": string } } "
        "}. Notes MUST be concise (<= 30 chars)."
        if require_json else "Return binary decisions."
    )
    return f"""
You are an impartial evaluation judge for contract-ambiguity analysis.

INPUT
- sentence: {item.get('sentence')}
- rationale_to_check: {item.get('rationale')}

TASKS
1) Independent Re-Judgment (classification without hints): decide judge_label ∈ {{ambiguous, unambiguous}} for the sentence itself.
2) Rubric-based Rationale Evaluation: evaluate each of the following criteria, output pass/confidence/notes.
{rubrics if rubrics else "(no rubric selected)"}
3) Manual Metrics: evaluate the following user-defined checks (binary yes/no), output pass/confidence/notes.
{manual if manual else "(none)"}

EVIDENCE (Grammar baseline):
- LanguageTool issues: {lt_evidence.get('issues')} (per 100 tokens: {lt_evidence.get('issues_per_100_tok')})

CONSTRAINTS
- Be strict but fair; avoid verbosity bias.
- {json_hint}
- IMPORTANT: Do NOT speculate about the original model's label; judge independently and evaluate the rationale text only against the rubric.
""".strip()

def build_batch_prompt(items: List[Dict[str, Any]], criteria: Dict[str, bool], manual_metrics: list,
                       require_json: bool=True) -> str:

    import random
    active_dims = [k for k, v in criteria.items() if v and k in RUBRIC_DEF]
    random.shuffle(active_dims)
    rubrics = "\n".join([f"- {k}: {RUBRIC_DEF[k]}" for k in active_dims])
    manual = "\n".join([f"- {m}: binary yes/no based on user-defined rule" for m in manual_metrics])
    json_hint = (
        "Return ONLY a JSON array, length == number of items, where each element is: "
        "{ \"judge_label\": \"ambiguous|unambiguous\", \"rubric\": {<dim>: {pass: bool, confidence: decimal in [0,1] (2 digits), notes: string}}, "
        "\"manual\": {<metric>: {pass: bool, confidence: decimal in [0,1] (2 digits), notes: string}} }. "
        "Notes MUST be concise (<= 30 chars)."
        if require_json else "Return binary decisions for each item"
    )
    lines = [
        "You are an impartial evaluation judge for contract-ambiguity analysis (BATCH MODE).",
        "TASKS",
        "1) For each item, decide judge_label ∈ {ambiguous, unambiguous}.",
        "2) Evaluate rubric criteria for that item's rationale.",
        rubrics if rubrics else "(no rubric selected)",
        "3) Evaluate manual metrics (binary yes/no).",
        manual if manual else "(none)",
        "CONSTRAINTS",
        "- Be strict but fair; avoid verbosity bias.",
        f"- {json_hint}",
        "- IMPORTANT: Preserve input order; output array index i corresponds to item i.",
        "",
        "INPUT ITEMS:",
    ]
    for idx, it in enumerate(items):
        lines.append(f"- [{idx}] sentence: {it.get('sentence')}")
        lines.append(f"  rationale_to_check: {it.get('rationale')}")
    return "\n".join(lines).strip()

def make_verdicts_schema(dim_keys: List[str], manual_metrics: List[str]) -> Dict[str, Any]:
    """为 Groq Llama-3.1-8B Structured Outputs 构造严格 JSON Schema（数组）。"""
    def leaf_schema():
        return {
            "type": "object",
            "properties": {
                "pass": {"type": "boolean"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                "notes": {"type": "string"},
            },
            "required": ["pass", "confidence", "notes"],
            "additionalProperties": False,
        }

    rubric_props = {k: leaf_schema() for k in dim_keys}
    manual_props = {m: leaf_schema() for m in manual_metrics}

    item_schema = {
        "type": "object",
        "properties": {
            "judge_label": {"type": "string", "enum": ["ambiguous", "unambiguous"]},
            "rubric": {
                "type": "object",
                "properties": rubric_props,
                "required": list(rubric_props.keys()),
                "additionalProperties": False,
            },
            "manual": {
                "type": "object",
                "properties": manual_props,
                "required": list(manual_props.keys()),
                "additionalProperties": False,
            },
        },
        "required": ["judge_label", "rubric", "manual"],
        "additionalProperties": False,
    }

    return {
        "name": "verdicts",
        "strict": True,
        "schema": {
            "type": "array",
            "items": item_schema,
        },
    }
