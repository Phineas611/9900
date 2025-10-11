# -*- coding: utf-8 -*-
from __future__ import annotations
from pathlib import Path
from typing import Optional

PDF_EXTS = {".pdf"}
DOCX_EXTS = {".docx"}

def detect_type(path: Path) -> Optional[str]:
    ext = path.suffix.lower()
    if ext in PDF_EXTS:
        return "pdf"
    if ext in DOCX_EXTS:
        return "docx"
    return None

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
