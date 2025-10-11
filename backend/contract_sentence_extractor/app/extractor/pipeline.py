# -*- coding: utf-8 -*-
from __future__ import annotations
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List, Dict, Any, Optional
import pandas as pd

from .utils import detect_type, ensure_dir
from .parsers import iter_pdf_chunks, iter_docx_chunks
from .splitter import split_into_sentences

@dataclass
class SentenceRow:
    contract_id: str
    file_name: str
    file_type: str
    page: int
    sentence_id: int
    sentence: str

def process_files(
    file_paths: Iterable[Path],
    output_dir: Path,
    export_formats: Optional[List[str]] = None,
) -> Dict[str, Any]:
    if export_formats is None:
        export_formats = ["csv", "xlsx", "txt"]

    ensure_dir(output_dir)

    rows: List[SentenceRow] = []
    file_count = 0

    for path in file_paths:
        p = Path(path)
        ftype = detect_type(p)
        if ftype is None:
            continue
        file_count += 1
        contract_id = str(uuid.uuid4())
        sentence_counter = 0

        chunks = iter_pdf_chunks(p) if ftype == "pdf" else iter_docx_chunks(p)

        for ch in chunks:
            sentences = split_into_sentences(ch.text)
            for s in sentences:
                sentence_counter += 1
                rows.append(SentenceRow(
                    contract_id=contract_id,
                    file_name=p.name,
                    file_type=ftype,
                    page=ch.page,
                    sentence_id=sentence_counter,
                    sentence=s
                ))

    df = pd.DataFrame([asdict(r) for r in rows])

    outputs = {}
    if "csv" in export_formats:
        csv_path = output_dir / "sentences.csv"
        df.to_csv(csv_path, index=False, encoding="utf-8")
        outputs["csv"] = str(csv_path)
    if "xlsx" in export_formats:
        xlsx_path = output_dir / "sentences.xlsx"
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="sentences")
        outputs["xlsx"] = str(xlsx_path)
    if "txt" in export_formats:
        txt_path = output_dir / "sentences.txt"
        with open(txt_path, "w", encoding="utf-8") as f:
            for s in df["sentence"].tolist():
                f.write(s.strip() + "\n")
        outputs["txt"] = str(txt_path)

    return {
        "files_processed": file_count,
        "sentences_extracted": int(len(df)),
        "output_dir": str(output_dir),
        "outputs": outputs,
    }
