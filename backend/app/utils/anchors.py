import json
import os
import re
from typing import Dict, List, Tuple, Optional

Lexicon = Dict[str, Dict[str, List[str]]]
CompiledPatterns = Tuple[List[re.Pattern], List[re.Pattern]]

def _default_lexicon() -> Lexicon:
    return {
        "ambiguous": {
            "regex": [
                r"\b(reasonable endeavours?|best endeavours?|commercially reasonable|promptly|as soon as practicable|material|within a reasonable time)\b"
            ],
            "phrases": [
                "reasonable endeavours",
                "best endeavours",
                "commercially reasonable",
                "promptly",
                "as soon as practicable",
                "material",
                "within a reasonable time",
            ],
        },
        "unambiguous": {
            "regex": [
                r"\b(within \d+ (business )?days?|AUD ?\d{1,3}(,\d{3})*|Clause \d+(\.\d+)?)\b"
            ],
            "phrases": [
                "within 3 business days",
                "within 5 business days",
                "Clause 3.2",
                "AUD 10,000",
            ],
        },
    }

def load_anchor_lexicon(path: Optional[str]) -> Lexicon:
    if path:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # basic shape validation
            if not isinstance(data, dict):
                return _default_lexicon()
            return data
        except Exception:
            return _default_lexicon()
    return _default_lexicon()

def compile_anchor_patterns(lexicon: Lexicon) -> CompiledPatterns:
    amb_patterns: List[re.Pattern] = []
    clear_patterns: List[re.Pattern] = []
    # compile regex lists
    for pat in lexicon.get("ambiguous", {}).get("regex", []):
        try:
            amb_patterns.append(re.compile(pat, re.I))
        except Exception:
            pass
    for pat in lexicon.get("unambiguous", {}).get("regex", []):
        try:
            clear_patterns.append(re.compile(pat, re.I))
        except Exception:
            pass
    # compile phrases into word-boundary regex
    for phrase in lexicon.get("ambiguous", {}).get("phrases", []):
        s = re.escape(phrase.strip())
        if s:
            amb_patterns.append(re.compile(fr"\b{s}\b", re.I))
    for phrase in lexicon.get("unambiguous", {}).get("phrases", []):
        s = re.escape(phrase.strip())
        if s:
            clear_patterns.append(re.compile(fr"\b{s}\b", re.I))
    return amb_patterns, clear_patterns

def match_anchor(text: str, compiled: CompiledPatterns) -> Optional[str]:
    amb_patterns, clear_patterns = compiled
    # ambiguous wins if both match; conservative default
    for p in amb_patterns:
        if p.search(text):
            return "ambiguous"
    for p in clear_patterns:
        if p.search(text):
            return "unambiguous"
    return None