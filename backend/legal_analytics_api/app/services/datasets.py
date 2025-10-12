from __future__ import annotations
from pathlib import Path
from typing import Dict, Any, List
import re
import numpy as np
import pandas as pd

SECTION_RE = re.compile(r'(?i)\b(section|sec\.|article|art\.|clause)\s+([A-Z\d][\w.\-]*)')
SUBSEC_RE = re.compile(r'(?i)\b(\d+(?:\.\d+)+)\b')

# ---------- Loaders & enrichment ----------

def load_sentences_df(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    # Normalize expected columns
    required = ["contract_id", "file_name", "sentence"]
    for c in required:
        if c not in df.columns:
            raise ValueError(f"sentences.csv missing required column: {c}")
    if "page" not in df.columns:
        df["page"] = 1
    df["sentence"] = df["sentence"].astype(str).fillna("")
    df["sentence_len"] = df["sentence"].str.len()
    # Keep a safe copy of contract_id
    df["contract_id"] = df["contract_id"].astype(str)
    return df

def infer_sections(df: pd.DataFrame) -> pd.DataFrame:
    if "section" not in df.columns:
        df["section"] = df["sentence"].str.extract(SECTION_RE, expand=True)[1]
    if "subsection" not in df.columns:
        df["subsection"] = df["sentence"].str.extract(SUBSEC_RE, expand=False)
    df["section"] = df["section"].fillna("")
    df["subsection"] = df["subsection"].fillna("")
    return df

# ---------- Core aggregates ----------

def pages_per_contract(df: pd.DataFrame) -> pd.DataFrame:
    # pages = max(page) per contract
    g = df.groupby("contract_id")["page"].max().reset_index(name="pages")
    # attach file_name (first)
    names = df.groupby("contract_id")["file_name"].first().reset_index(name="file_name")
    return g.merge(names, on="contract_id", how="left")

def sentences_per_contract(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("contract_id").size().reset_index(name="sentences")
    names = df.groupby("contract_id")["file_name"].first().reset_index(name="file_name")
    return g.merge(names, on="contract_id", how="left")

def avg_sentence_len_per_contract(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby("contract_id")["sentence_len"].mean().reset_index(name="avg_sentence_len")
    names = df.groupby("contract_id")["file_name"].first().reset_index(name="file_name")
    return g.merge(names, on="contract_id", how="left")

def hist(series: pd.Series, bins: int) -> Dict[str, Any]:
    counts, edges = np.histogram(series.to_numpy(), bins=bins)
    return {"bins": edges.tolist(), "counts": counts.astype(int).tolist()}

def to_pages_vs_contracts_df(df: pd.DataFrame) -> pd.DataFrame:
    pc = pages_per_contract(df)
    return pc.sort_values("pages")

def to_sentence_length_hist_df(df: pd.DataFrame, bins: int = 20) -> pd.DataFrame:
    h = hist(df["sentence_len"], bins=bins)
    return pd.DataFrame({"bin_left": h["bins"][:-1], "bin_right": h["bins"][1:], "count": h["counts"]})

def to_avg_sentence_length_hist_df(df: pd.DataFrame, bins: int = 20) -> pd.DataFrame:
    ac = avg_sentence_len_per_contract(df)
    h = hist(ac["avg_sentence_len"], bins=bins)
    return pd.DataFrame({"bin_left": h["bins"][:-1], "bin_right": h["bins"][1:], "count": h["counts"]})

def to_section_counts_df(df: pd.DataFrame, topk: int = 20) -> pd.DataFrame:
    counts = (df.loc[df["section"].ne("")]
                .groupby("section").size()
                .reset_index(name="count")
                .sort_values("count", ascending=False)
                .head(topk))
    return counts

def to_subsection_counts_df(df: pd.DataFrame, topk: int = 20) -> pd.DataFrame:
    counts = (df.loc[df["subsection"].ne("")]
                .groupby("subsection").size()
                .reset_index(name="count")
                .sort_values("count", ascending=False)
                .head(topk))
    return counts

def to_contracts_scatter_df(df: pd.DataFrame) -> pd.DataFrame:
    pc = pages_per_contract(df)
    sc = sentences_per_contract(df)
    ac = avg_sentence_len_per_contract(df)
    merged = pc.merge(sc[["contract_id","sentences"]], on="contract_id")                .merge(ac[["contract_id","avg_sentence_len"]], on="contract_id")
    return merged

def box_stats(series: pd.Series) -> Dict[str, Any]:
    q1 = float(series.quantile(0.25))
    med = float(series.quantile(0.5))
    q3 = float(series.quantile(0.75))
    return {"min": int(series.min()), "q1": q1, "median": med, "q3": q3, "max": int(series.max())}

def compute_summary(df: pd.DataFrame, bins_pages: int = 10, bins_sentence: int = 20, topk: int = 20) -> Dict[str, Any]:
    pc = pages_per_contract(df)
    sc = sentences_per_contract(df)
    ac = avg_sentence_len_per_contract(df)

    meta = {
        "contracts": int(pc.shape[0]),
        "sentences": int(df.shape[0]),
        "files": df["file_name"].nunique(),
    }

    page_hist = hist(pc["pages"], bins=bins_pages)
    sent_hist = hist(df["sentence_len"], bins=bins_sentence)
    avg_sent_hist = hist(ac["avg_sentence_len"], bins=bins_sentence)

    section_counts = to_section_counts_df(df, topk=topk).to_dict(orient="records")
    subsection_counts = to_subsection_counts_df(df, topk=topk).to_dict(orient="records")

    scatter = to_contracts_scatter_df(df).to_dict(orient="records")

    box = box_stats(df["sentence_len"])

    return {
        "metadata": meta,
        "page_length_hist": page_hist,
        "sentence_length_hist": sent_hist,
        "avg_sentence_length_hist": avg_sent_hist,
        "contracts_scatter": scatter,
        "section_frequency": section_counts,
        "subsection_frequency": subsection_counts,
        "sentence_length_box": box,
    }
