# -*- coding: utf-8 -*-
from __future__ import annotations
import re
from typing import List

# ====== Feature toggles ======
# Prefer continuity: stitch adjacent blocks when the first does NOT end with terminal punctuation,
# unless the next block is clearly a heading / bullet / list anchor.
PREFER_CONTINUITY = True

# ====== Base rules ======
# Abbreviations after which a trailing period should NOT be treated as a sentence boundary.
_ABBR_TOKENS = {
    "Mr", "Mrs", "Ms", "Dr", "Prof", "Sr", "Jr", "St", "No", "Art", "Sec", "Secs",
    "Ch", "Fig", "Eq", "Ltd", "Inc", "Co", "Corp", "U.S", "U.S.C", "C.F.R", "e.g", "i.e", "vs",
    "Jan", "Feb", "Mar", "Apr", "Jun", "Jul", "Aug", "Sep", "Sept", "Oct", "Nov", "Dec",
    # Common company-style abbreviations
    "N.A", "S.A", "N.V", "B.V", "A.G", "L.P", "L.L.P", "LLP", "L.L.C", "LLC", "P.L.C", "PLC"
}

# Primary boundary: sentence-final punctuation (+ optional closing quote/bracket) + whitespace
# + likely new sentence start (optional opening bracket + capital/digit).
_SENT_BOUNDARY = re.compile(
    r'([.!?。；]["”’\'\)\]]?)\s+(?=[\(\[]?[A-Z0-9])'
)

# Helper to capture the token immediately before punctuation (used for abbreviation protection).
_PRE_TOKEN = re.compile(r'([A-Za-z\.]+)$')

# Headings / anchors typically found in contracts.
_HEAD_TOKENS  = re.compile(r'(?im)^(BACKGROUND|RECITALS|DEFINITIONS|NOW,\s*THEREFORE,|WHEREAS,)\b')
_ARTICLE_LINE = re.compile(r'(?im)^(ARTICLE\s+[IVXLCDM]+\b.*)$')
_ALL_CAPS_LINE = re.compile(r'^(?=.{6,}$)([A-Z0-9\s\-\’\'/&,\.]+)$')
_PAGE_NUM_LINE = re.compile(r'^\s*\d+\s*$')

# Keyword-list detection (explicit label only).
_RE_RKW       = re.compile(r'(?i)\brestricted\s+key\s*word[s]?\b')
_RE_RKW_BRAND = re.compile(r'(?i)\b([A-Z][A-Za-z]+)\s+Restricted\s+Key\s*Words\b')

# Line-start bullet / enumerator detection (for paragraph-level items).
_BULLET_LINE = re.compile(
    r'^\s*(?:[\-\–\—•▪·]|\([a-zA-Z0-9ivxIVX]+\)|[a-zA-Z0-9ivxIVX]+[.)])\s+'
)

# NEW: inline enumeration anchors (for a., b., c., 1., (i), (a), iii., etc.) anywhere in a block
# but only when they appear after whitespace or at the start (to avoid "U.S." false hits).
_INLINE_ENUM_ANCHOR = re.compile(
    r'(?:(?<=^)|(?<=\s))'                              # start of block OR preceded by whitespace
    r'(?:\(\s*([A-Za-z0-9ivxlcdmIVXLCDM]+)\s*\)'       # (a) / (i) / (1)
    r'|([A-Za-z0-9ivxlcdmIVXLCDM]+)[\.\)])'            # a. / a) / 1. / iii. / III)
    r'\s+(?=\S)',                                      # followed by some content
)

# ====== Utilities ======
def normalize_whitespace(text: str) -> str:
    """Collapse all whitespace to single spaces and trim."""
    return re.sub(r"\s+", " ", text).strip()

def _is_all_caps_heading(line: str) -> bool:
    """Heuristic: treat brief ALL-CAPS lines (or ARTICLE ...) as headings."""
    line = line.strip()
    if not line or len(line) < 6:
        return False
    if not _ALL_CAPS_LINE.match(line):
        return False
    # Avoid classifying long body paragraphs as headings
    return len(line) <= 120 or line.startswith("ARTICLE ")

def _is_bulletish(line: str) -> bool:
    """Return True if the line looks like a bullet/numbered item."""
    return bool(_BULLET_LINE.match(line or ""))

def _should_block_split(prefix: str) -> bool:
    """
    Return True if we should NOT split at the found punctuation because it is
    part of an abbreviation, numeric chain, URL/email/domain, or legal reference token.
    """
    # Abbreviation protection (e.g., "U.S.", "Inc.", "e.g.")
    m = _PRE_TOKEN.search(prefix)
    if m and m.group(1) in _ABBR_TOKENS:
        return True

    # Email addresses (name@example.com).
    if re.search(r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b$', prefix):
        return True

    # Domain/URL before the dot (e.g., example.com, https://...).
    if re.search(r'(?:https?://|www\.)', prefix, flags=re.IGNORECASE):
        return True
    if re.search(r'\b[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.(?:com|net|org|gov|edu|io|co|uk|au)\b$', prefix, flags=re.IGNORECASE):
        return True

    # Numeric chains: decimals, versioning, dates like 10.12.2020 or 3.14, 1.2.3
    if re.search(r'(?:\b\d+(?:\.\d+){1,3}\b|\b\d+\.\d+\b)$', prefix):
        return True

    # Legal references like "Section 3.1" or "Sec. 2.4"
    if re.search(r'(?:Section|Sec|Art|Article|Exhibit|Schedule)\s+\d+(?:\.\d+)*$', prefix, flags=re.IGNORECASE):
        return True

    # Initial-like tokens "A." "B." "C." that are NOT list anchors (handled elsewhere)
    # Keep this conservative; inline list splitting comes first and removes true list anchors.
    if re.search(r'\b[A-Za-z]\.$', prefix):
        return True

    return False

def _soft_fix_raw_text(raw: str) -> str:
    """
    Perform non-destructive text fixes:
    - Normalize newlines
    - De-hyphenate wrapped words: "non-\ntechnical" -> "non-technical"
    Do NOT stitch blocks here; defer to the block-level stitcher.
    """
    s = raw.replace("\r\n", "\n").replace("\r", "\n")
    s = re.sub(r'(\w)-\n(\w)', r'\1-\2', s)
    return s

def _split_rkw_block(text: str) -> List[str]:
    """
    Smart decomposition for explicit "* Restricted Key Words" pages:
    - If the label includes a brand (e.g., "United Restricted Key Words"),
      split by that brand as an anchor so each keyword phrase becomes a separate item.
    - Otherwise, fall back to per-line items.
    """
    m = _RE_RKW_BRAND.search(text)
    if m:
        anchor = m.group(1)  # e.g., "United", "Continental"
        core = _RE_RKW.sub("", text, count=1)  # strip the label once
        # Split at positions where a new item likely starts with the anchor (keep the anchor).
        pat = re.compile(r'(?i)(?=\b' + re.escape(anchor) + r'\b)')
        parts = [normalize_whitespace(p) for p in pat.split(core) if normalize_whitespace(p)]
        return parts

    # No brand detected: split line-wise (each non-empty line is an item).
    lines = [ln.strip() for ln in text.split("\n")]
    return [ln for ln in lines if ln]

# ====== Pre-segmentation: keep paragraphs, detect headings, drop page numbers ======
def _pre_segment_blocks(raw: str) -> List[str]:
    """
    Convert the raw page text into higher-level blocks:
    - Remove standalone page number lines.
    - Insert breaks before key anchors and ARTICLE lines.
    - Split on double newlines.
    - If a block contains headings plus body, split so headings stand alone.
    - If a block matches "* Restricted Key Words", split using brand anchor or per-line.
    - Prefer continuity: if a block does NOT end with terminal punctuation and the next
      block is NOT a heading/bullet/RKW, stitch them together.
    """
    s = _soft_fix_raw_text(raw)

    # Remove standalone page numbers
    lines = [ln for ln in s.split("\n") if not _PAGE_NUM_LINE.match(ln)]
    s = "\n".join(lines)

    # Collapse excessive blank lines
    s = re.sub(r"\n{3,}", "\n\n", s)

    # Force a block break before common anchors and ARTICLE headings.
    s = re.sub(r"(?m)^(\s*)(BACKGROUND|RECITALS|DEFINITIONS|WHEREAS,|NOW,\s*THEREFORE,)", r"\n\1\2", s)
    s = re.sub(r"(?m)^(\s*)(ARTICLE\s+[IVXLCDM]+\b.*)$", r"\n\1\2", s)

    # Split into blocks on double newlines.
    blocks = [blk.strip() for blk in re.split(r"\n\s*\n", s) if blk.strip()]

    refined: List[str] = []
    for blk in blocks:
        # If the whole block explicitly contains a "* Restricted Key Words" marker, split smartly.
        if _RE_RKW.search(blk):
            refined.extend([x for x in _split_rkw_block(blk) if x])
            continue

        # Otherwise, split out headings from body; join non-heading lines into one block.
        sublines = blk.split("\n")
        cur: List[str] = []
        for ln in sublines:
            if _is_all_caps_heading(ln) or _HEAD_TOKENS.match(ln) or _ARTICLE_LINE.match(ln):
                if cur:
                    refined.append(" ".join(x.strip() for x in cur if x.strip()))
                    cur = []
                if ln.strip():
                    refined.append(ln.strip())
            else:
                cur.append(ln)
        if cur:
            refined.append(" ".join(x.strip() for x in cur if x.strip()))

    # Final stitching to prefer continuity
    stitched: List[str] = []
    i = 0
    while i < len(refined):
        cur_blk = refined[i]
        if PREFER_CONTINUITY and i + 1 < len(refined):
            next_blk = refined[i + 1]

            # Do not stitch into obvious structural starts (heading, bullet, RKW marker).
            if (_is_all_caps_heading(next_blk)
                or _HEAD_TOKENS.match(next_blk)
                or _ARTICLE_LINE.match(next_blk)
                or _RE_RKW.search(next_blk)
                or _is_bulletish(next_blk)):
                stitched.append(normalize_whitespace(cur_blk))
                i += 1
                continue

            # If the current block ends with a strong terminal punctuation (or colon), do not stitch.
            if re.search(r'[.!?。；:]["”\']?$', cur_blk.strip()):
                stitched.append(normalize_whitespace(cur_blk))
                i += 1
                continue

            # Otherwise, prefer to stitch (maximize sentence continuity).
            merged = normalize_whitespace(cur_blk.rstrip()) + " " + normalize_whitespace(next_blk.lstrip())
            stitched.append(merged)
            i += 2
            continue

        stitched.append(normalize_whitespace(cur_blk))
        i += 1

    return [x for x in stitched if x]

# ====== Inline enumeration splitter (NEW) ======
def _split_by_inline_enumerations(block: str) -> List[str]:
    """
    Split a block at inline enumeration anchors like: a.  b.  c.   or   (i) (ii) (iii)  or  1) 2) 3)
    The anchor must be at start-of-block OR preceded by whitespace to avoid matching 'U.S.' or 'A.G.'.
    We also skip anchors that are actually known abbreviations (e.g., 'No.').
    Heuristic: trigger if there are >=2 anchors, OR a single anchor at the very beginning.
    """
    matches = list(_INLINE_ENUM_ANCHOR.finditer(block))
    if not matches:
        return [block]

    # Filter out anchors that are actually abbreviations ('No.', 'Art.', etc.)
    filtered = []
    for m in matches:
        token = m.group(1) or m.group(2) or ""
        token_clean = re.sub(r'[^A-Za-z0-9]+', '', token)
        if token_clean and token_clean in _ABBR_TOKENS:
            continue
        filtered.append(m)

    if not filtered:
        return [block]

    if len(filtered) < 2 and filtered[0].start() != 0:
        # Only one candidate and not at the start: don't split to avoid false positives.
        return [block]

    # Perform the split: keep the anchor with its segment.
    parts: List[str] = []
    starts = [m.start() for m in filtered] + [len(block)]
    for i in range(len(filtered)):
        seg = block[starts[i]:starts[i+1]].strip()
        if seg:
            parts.append(seg)
    # Also include any leading text before the first anchor as its own segment (rare).
    lead = block[:filtered[0].start()].strip()
    if lead:
        parts.insert(0, lead)
    return parts

# ====== Intra-block sentence splitting ======
def _split_sentences_in_block(block: str) -> List[str]:
    """
    Split a single block into sentences:
    - Keep headings/anchors as standalone sentences.
    - Split at sentence boundaries with abbreviation/URL/email/legal-reference/numeric protection.
    - NEW: First split by inline enumerations (a., b., c., (i), 1., etc.) so list items on the same line are separated.
    """
    # Headings/anchors remain intact.
    if _is_all_caps_heading(block) or _HEAD_TOKENS.match(block) or block.startswith("ARTICLE "):
        return [block.strip()]

    # First, separate inline enumeration items (if any).
    subblocks = _split_by_inline_enumerations(block)

    sentences: List[str] = []
    for sub in subblocks:
        last_idx = 0
        for m in _SENT_BOUNDARY.finditer(sub):
            punct_start = m.start(1)
            if _should_block_split(sub[last_idx:punct_start]):
                continue
            cut = m.end(1)  # include the ender (and possible closing quote/bracket)
            left = sub[last_idx:cut].strip()
            if left:
                sentences.append(left)
            last_idx = m.end()

        tail = sub[last_idx:].strip()
        if tail:
            sentences.append(tail)

    final: List[str] = [normalize_whitespace(x) for x in sentences if normalize_whitespace(x)]
    return final

def split_into_sentences(text: str) -> List[str]:
    """Entry point: pre-segment into logical blocks, then split each block into sentences."""
    sentences: List[str] = []
    for blk in _pre_segment_blocks(text):
        sentences.extend(_split_sentences_in_block(blk))
    return sentences
