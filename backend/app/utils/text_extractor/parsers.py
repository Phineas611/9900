# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Union

# Primary extractor
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer

# DOCX
from docx import Document

@dataclass
class Chunk:
    page: int
    text: str

def iter_pdf_chunks(path: Union[str, Path]):
    """
    Extract text per page from a PDF.
    Strategy:
      1) Try pdfminer page-by-page.
      2) If total extracted text is empty (common for tricky/embedded fonts PDFs),
         fall back to PyMuPDF (fitz) page-by-page.
      3) If both fail, yield empty pages (keeps page indices consistent).
    """
    p = Path(path)

    # ---- Attempt 1: pdfminer ----
    texts = []
    page_num = 0
    try:
        for page_layout in extract_pages(str(p)):
            page_num += 1
            page_texts = []
            for element in page_layout:
                if isinstance(element, LTTextContainer):
                    page_texts.append(element.get_text())
            texts.append((page_num, "\n".join(page_texts)))
    except Exception:
        texts = []

    total_len = sum(len((t or "").strip()) for _, t in texts)
    if total_len > 0:
        for pg, t in texts:
            yield Chunk(page=pg, text=t or "")
        return

    # ---- Attempt 2: PyMuPDF (fitz) fallback ----
    try:
        import fitz  # PyMuPDF
        with fitz.open(str(p)) as doc:
            for idx, pg in enumerate(doc, start=1):
                # "text" mode is robust for most PDFs
                t = pg.get_text("text") or ""
                yield Chunk(page=idx, text=t)
        return
    except Exception:
        # Fall through to empty output
        pass

    # ---- Final: yield empty pages (best-effort to preserve page count) ----
    if page_num == 0:
        # pdfminer didn't even enumerate pages; assume single page
        yield Chunk(page=1, text="")
    else:
        for pg in range(1, page_num + 1):
            yield Chunk(page=pg, text="")

def iter_docx_chunks(path: Union[str, Path]):
    """Iterate paragraph text from a DOCX file. Page is unknown -> 0."""
    doc = Document(str(path))
    buf = []
    for para in doc.paragraphs:
        t = para.text.strip()
        if t:
            buf.append(t)
    if buf:
        yield Chunk(page=0, text="\n".join(buf))
