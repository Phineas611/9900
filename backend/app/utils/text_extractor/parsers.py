from __future__ import annotations
from pathlib import Path
from typing import Iterator
from dataclasses import dataclass

import fitz  # PyMuPDF
from docx import Document


@dataclass
class PageChunk:
    page: int
    text: str


def iter_pdf_chunks(path: Path) -> Iterator[PageChunk]:

    doc = fitz.open(str(path))
    try:
        for i, page in enumerate(doc, start=1):
            text = page.get_text("text")
            if text and text.strip():
                yield PageChunk(page=i, text=text)
    finally:
        doc.close()


def iter_docx_chunks(path: Path) -> Iterator[PageChunk]:

    document = Document(str(path))
    buf: list[str] = []
    current_len = 0
    chunk_page = 1
    for para in document.paragraphs:
        t = para.text.strip()
        if not t:
            continue
        buf.append(t)
        current_len += len(t) + 1
        if current_len >= 4000:
            yield PageChunk(page=chunk_page, text=" ".join(buf))
            buf = []
            current_len = 0
            chunk_page += 1
    if buf:
        yield PageChunk(page=chunk_page, text=" ".join(buf))