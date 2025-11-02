import pandas as pd
from typing import Dict, Tuple, List

CANON: Dict[str, List[str]] = {
    "id": ["id", "sid", "sample_id", "item_id", "row_id"],
    "sentence": ["sentence", "text", "clause", "contract_sentence"],
    "label": ["label", "pred_class", "prediction", "label_pred", "predicted_label", "pred"],
    "rationale": ["rationale", "reason", "explanation", "justification"],
    "gold_class": ["gold_class", "gold", "ground_truth", "true_label", "gold_label"],
    "contract_id": ["contract_id", "doc_id", "document_id", "contract"],
    "sentence_id": ["sentence_id", "sent_id", "text_id"],
    "model_id": ["model_id", "model", "model_name", "llm_id", "llm"],
}


def _guess_column(df: pd.DataFrame, keys: List[str]) -> str:
    cols = {c.lower(): c for c in df.columns}
    for k in keys:
        if k in cols:
            return cols[k]

    for c in df.columns:
        norm = str(c).lower().replace(" ", "").replace("_", "")
        for k in keys:
            if k.replace("_", "") == norm:
                return c
    raise KeyError(f"missing column for keys={keys}")


def detect_columns(df: pd.DataFrame) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for canon, alts in CANON.items():
        try:
            out[canon] = _guess_column(df, [a.lower() for a in alts])
        except KeyError:
            # 可选字段列表
            if canon in ("gold_class", "model_id", "contract_id", "sentence_id"):
                continue  
            raise
    return out


def load_table(file_path: str) -> Tuple[pd.DataFrame, Dict[str, str]]:
    if file_path.endswith(".xlsx"):
        df = pd.read_excel(file_path)
    else:
        df = pd.read_csv(file_path)
    cols = detect_columns(df)
    return df, cols