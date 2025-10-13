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
    "Ch", "Fig", "Eq", "Ltd", "Inc", "Co", "Corp", "U.S", "e.g", "i.e", "vs",
    "Jan", "Feb", "Mar", "Apr", "Jun", "Jul", "Aug", "Sep", "Sept", "Oct", "Nov", "Dec",
    # Common company-style abbreviations
    "N.A", "S.A", "N.V", "B.V", "A.G", "L.P", "L.L.P", "LLP", "L.L.C", "LLC", "P.L.C", "PLC"
}

# Primary boundary: sentence-final punctuation + whitespace + likely new sentence start (optional bracket + capital/digit).
_SENT_BOUNDARY = re.compile(r'([.!?。；])\s+(?=[\(\[]?[A-Z0-9])')

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

# Bullet / enumerator detection
_BULLET_LINE = re.compile(
    r'^\s*(?:[\-\–\—•▪·]|\([a-zA-Z0-9]+\)|[a-zA-Z0-9]+\.)\s+'
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
    part of an abbreviation, URL/domain, or legal reference token.
    """
    # Abbreviation protection
    m = _PRE_TOKEN.search(prefix)
    if m and m.group(1) in _ABBR_TOKENS:
        return True

    # Domain/URL before the dot (e.g., example.com)
    if re.search(r'(?:https?://|www\.)', prefix, flags=re.IGNORECASE):
        return True
    if re.search(r'\b[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.(?:com|net|org|gov|edu|io|co|uk|au)\b$', prefix, flags=re.IGNORECASE):
        return True

    # Legal references like "Section 3.1" or "Sec. 2.4"
    if re.search(r'(?:Section|Sec|Art|Article|Exhibit|Schedule)\s+\d+(?:\.\d+)*$', prefix, flags=re.IGNORECASE):
        return True

    # Initials-like tokens "A." "B." "C." preceding a clause are common; avoid splitting right after them
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

# ====== Intra-block sentence splitting ======
def _split_sentences_in_block(block: str) -> List[str]:
    """
    Split a single block into sentences:
    - Keep headings/anchors as standalone sentences.
    - Split at sentence boundaries with abbreviation/URL/legal-reference protection.
    - Conservative: no secondary splitting on semicolons or mid-sentence bullets.
    """
    # Headings/anchors remain intact.
    if _is_all_caps_heading(block) or _HEAD_TOKENS.match(block) or block.startswith("ARTICLE "):
        return [block.strip()]

    parts: List[str] = []
    last_idx = 0
    for m in _SENT_BOUNDARY.finditer(block):
        punct_start = m.start(1)
        if _should_block_split(block[last_idx:punct_start]):
            continue
        cut = m.end(1)
        left = block[last_idx:cut].strip()
        if left:
            parts.append(left)
        last_idx = m.end()

    tail = block[last_idx:].strip()
    if tail:
        parts.append(tail)

    final: List[str] = [normalize_whitespace(x) for x in parts if normalize_whitespace(x)]
    return final

def split_into_sentences(text: str) -> List[str]:
    """Entry point: pre-segment into logical blocks, then split each block into sentences."""
    sentences: List[str] = []
    for blk in _pre_segment_blocks(text):
        sentences.extend(_split_sentences_in_block(blk))
    return sentences
