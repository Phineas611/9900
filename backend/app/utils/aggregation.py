# app/utils/aggregation.py
from collections import Counter
from typing import List, Dict, Tuple
import math

CATS = ["ambiguous", "unambiguous"]

def majority_label(votes: List[str]) -> Tuple[str, Dict[str, int], bool]:
    cnt = Counter([v for v in votes if v in CATS])
    if not cnt:
        return "ambiguous", {"ambiguous": 0, "unambiguous": 0}, True
    top = cnt.most_common()
    tie = len(top) > 1 and (top[0][1] == top[1][1])
    return top[0][0], {c: cnt.get(c, 0) for c in CATS}, tie

# --- Optional: Dawid–Skene (binary) ---
def dawid_skene_binary(votes_per_item: List[List[str]], max_iter: int = 50, eps: float = 1e-6, priors: List[str | None] | None = None) -> List[str]:
    """
    Minimal DS-EM for binary categories. Returns estimated true labels per item.
    Each item is a list[str] of labels in {'ambiguous','unambiguous'} from multiple judges.
    """
    n_items = len(votes_per_item)
    J = max(len(v) for v in votes_per_item) if votes_per_item else 0
    # Initialize priors: use provided priors when available, else majority
    z = []
    for idx, votes in enumerate(votes_per_item):
        if priors and idx < len(priors) and (priors[idx] in CATS):
            z.append(priors[idx])
        else:
            m, _, _ = majority_label(votes)
            z.append(m)
    # Worker accuracy (shared for simplicity)
    a = { "ambiguous": 0.7, "unambiguous": 0.7 }

    def e_step():
        # No soft posteriors here; keep hard labels for brevity
        return z

    def m_step():
        # Re-estimate a[c] as fraction of times vote==z over all workers
        num = {"ambiguous": 0, "unambiguous": 0}
        den = {"ambiguous": 0, "unambiguous": 0}
        for zi, votes in zip(z, votes_per_item):
            for v in votes:
                if v in CATS:
                    den[zi] += 1
                    if v == zi:
                        num[zi] += 1
        for c in CATS:
            if den[c] > 0:
                a[c] = max(0.51, min(0.99, num[c] / den[c]))

    for _ in range(max_iter):
        z_old = z[:]
        _ = e_step()
        m_step()
        # Hard update: reassign z by weighted majority (weights from a)
        for i, votes in enumerate(votes_per_item):
            score = {c: 1.0 for c in CATS}
            for v in votes:
                if v in CATS:
                    score[v] *= a[v]
                    score[[x for x in CATS if x != v][0]] *= (1.0 - a[[x for x in CATS if x != v][0]])
            z[i] = max(CATS, key=lambda c: score[c])
        if sum(zi != zj for zi, zj in zip(z, z_old)) == 0:
            break
    return z
