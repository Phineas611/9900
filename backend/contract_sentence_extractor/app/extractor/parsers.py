# -*- coding: utf-8 -*-
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Union

from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer
from docx import Document

@dataclass
class Chunk:
    page: int
    text: str

def iter_pdf_chunks(path: Union[str, Path]):
    p = Path(path)
    page_num = 0
    for page_layout in extract_pages(str(p)):
        page_num += 1
        texts = []
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                texts.append(element.get_text())
        yield Chunk(page=page_num, text="\n".join(texts))

def iter_docx_chunks(path: Union[str, Path]):
    doc = Document(str(path))
    buf = []
    for para in doc.paragraphs:
        t = para.text.strip()
        if t:
            buf.append(t)
    if buf:
        yield Chunk(page=0, text="\n".join(buf))
