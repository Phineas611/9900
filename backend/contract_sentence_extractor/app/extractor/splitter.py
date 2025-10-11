# -*- coding: utf-8 -*-
from __future__ import annotations
import re
from typing import List

_ABBR_TOKENS = {
    "Mr","Mrs","Ms","Dr","Prof","Sr","Jr","St","No","Art","Sec","Secs",
    "Ch","Fig","Eq","Ltd","Inc","Co","Corp","U.S","e.g","i.e","vs",
    "Jan","Feb","Mar","Apr","Jun","Jul","Aug","Sep","Sept","Oct","Nov","Dec"
}

_SENT_BOUNDARY = re.compile(r'([.!?。；])\s+(?=[\(\[]?[A-Z0-9])')
_PRE_TOKEN = re.compile(r'([A-Za-z\.]+)$')

_HEAD_TOKENS = re.compile(r'(?im)^(BACKGROUND|RECITALS|DEFINITIONS|NOW,\s*THEREFORE,|WHEREAS,)\b')
_ARTICLE_LINE = re.compile(r'(?im)^(ARTICLE\s+[IVXLCDM]+\b.*)$')
_ALL_CAPS_LINE = re.compile(r'^(?=.{6,}$)([A-Z0-9\s\-\’\'/&,\.]+)$')
_PAGE_NUM_LINE = re.compile(r'^\s*\d+\s*$')

_CONNECTOR_START = re.compile(r'^(and|or|of|to|with|for|in|on|at|by|from|as|that|which|who|whose|where|when|whether|outside|inside|into|onto|over|under|between|among|including|without|limitation)\b')

def normalize_whitespace(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()

def _is_all_caps_heading(line: str) -> bool:
    line = line.strip()
    if not line or len(line) < 6:
        return False
    if not _ALL_CAPS_LINE.match(line):
        return False
    return len(line) <= 120 or line.startswith("ARTICLE ")

def _should_block_split(prefix: str) -> bool:
    m = _PRE_TOKEN.search(prefix)
    return bool(m and m.group(1) in _ABBR_TOKENS)

def _soft_fix_raw_text(raw: str) -> str:
    s = raw.replace("\r\n", "\n").replace("\r", "\n")

    # 1) Dehyphenate wrapped words: "non-\ntechnical" -> "non-technical"
    s = re.sub(r'(\w)-\n(\w)', r'\1-\2', s)

    # 2) Stitch across double newlines when previous line is not a true sentence end
    #    and the next line starts with lowercase or a connector word.
    def _stitch(match):
        left = match.group(1)
        right = match.group(2)
        if _CONNECTOR_START.match(right) or (right and right[0].islower()):
            return left + " " + right
        return left + "\n\n" + right

    s = re.sub(r'([^\n])\n\n([^\n].*)', _stitch, s)

    return s

def _pre_segment_blocks(raw: str) -> List[str]:
    s = _soft_fix_raw_text(raw)

    # Remove standalone page numbers
    lines = [ln for ln in s.split("\n") if not _PAGE_NUM_LINE.match(ln)]
    s = "\n".join(lines)

    # Normalize excessive blank lines
    s = re.sub(r"\n{3,}", "\n\n", s)

    # Insert blank line BEFORE anchors (force block break)
    s = re.sub(r"(?m)^(\s*)(BACKGROUND|RECITALS|DEFINITIONS|WHEREAS,|NOW,\s*THEREFORE,)", r"\n\1\2", s)
    s = re.sub(r"(?m)^(\s*)(ARTICLE\s+[IVXLCDM]+\b.*)$", r"\n\1\2", s)

    # Split into blocks on double newlines
    blocks = [blk.strip() for blk in re.split(r"\n\s*\n", s) if blk.strip()]

    # If a block contains mixed headings + body, split on heading lines inside
    refined: List[str] = []
    for blk in blocks:
        sublines = blk.split("\n")
        cur: List[str] = []
        for ln in sublines:
            if _is_all_caps_heading(ln) or _HEAD_TOKENS.match(ln) or _ARTICLE_LINE.match(ln):
                if cur:
                    refined.append(" ".join(x.strip() for x in cur if x.strip()))
                    cur = []
                refined.append(ln.strip())
            else:
                cur.append(ln)
        if cur:
            refined.append(" ".join(x.strip() for x in cur if x.strip()))

    # Final stitching pass: if a block doesn't end with terminal punctuation and the next block starts lowercase/connector, merge.
    stitched: List[str] = []
    i = 0
    while i < len(refined):
        cur_blk = refined[i]
        if i + 1 < len(refined):
            next_blk = refined[i + 1]
            if (not re.search(r'[.!?。；:]["”\']?$', cur_blk)
                and not (_is_all_caps_heading(next_blk) or _HEAD_TOKENS.match(next_blk) or _ARTICLE_LINE.match(next_blk))
                and (_CONNECTOR_START.match(next_blk) or (next_blk and next_blk[0].islower()))
            ):
                cur_blk = cur_blk.rstrip() + " " + next_blk.lstrip()
                i += 2
                stitched.append(cur_blk)
                continue
        stitched.append(cur_blk)
        i += 1

    return [normalize_whitespace(x) for x in stitched if normalize_whitespace(x)]

def _split_sentences_in_block(block: str) -> List[str]:
    # Keep headings as single sentence
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

    # Conservative: no semicolon-based split, no mid-sentence bullet split
    final: List[str] = [normalize_whitespace(x) for x in parts if normalize_whitespace(x)]
    return final

def split_into_sentences(text: str) -> List[str]:
    sentences: List[str] = []
    for blk in _pre_segment_blocks(text):
        sentences.extend(_split_sentences_in_block(blk))
    return sentences
