from typing import List

# votes_per_item: List[List[str]]  # e.g. [['ambiguous','ambiguous','unambiguous'], ...]
CATS = ["ambiguous", "unambiguous"]

def fleiss_kappa(votes_per_item: List[List[str]]) -> float:

    if not votes_per_item:
        return 0.0
    N = len(votes_per_item)
    n = max(len(v) for v in votes_per_item) if votes_per_item else 0
    p = {c: 0 for c in CATS}
    P = []
    for votes in votes_per_item:
        cnt1 = sum(1 for v in votes if v == CATS[0])
        cnt2 = sum(1 for v in votes if v == CATS[1])
        P_i = (cnt1*(cnt1-1) + cnt2*(cnt2-1)) / (n*(n-1)) if n > 1 else 0.0
        P.append(P_i)
        p[CATS[0]] += cnt1
        p[CATS[1]] += cnt2
    p = {c: p[c] / (N*n) if N and n else 0.0 for c in CATS}
    P_bar = sum(P)/N if N else 0.0
    P_e = sum(p[c]**2 for c in CATS)
    return 0.0 if P_e == 1.0 else (P_bar - P_e) / (1 - P_e)

def cohens_kappa(v1: List[str], v2: List[str]) -> float:
    assert len(v1) == len(v2)
    N = len(v1)
    agree = sum(1 for a,b in zip(v1,v2) if a==b)
    p_o = agree / N if N else 0.0
    p1 = {c: (sum(1 for x in v1 if x==c)/N) if N else 0.0 for c in CATS}
    p2 = {c: (sum(1 for x in v2 if x==c)/N) if N else 0.0 for c in CATS}
    p_e = sum(p1[c]*p2[c] for c in CATS)
    return 0.0 if p_e == 1.0 else (p_o - p_e) / (1 - p_e)
