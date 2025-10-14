# -*- coding: utf-8 -*-
from __future__ import annotations
import uuid
import zipfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List, Dict, Any, Optional
import pandas as pd
from sqlalchemy.orm import Session

from .utils import detect_type, ensure_dir
from .parsers import iter_pdf_chunks, iter_docx_chunks
from .splitter import split_into_sentences
from app.persistence.contract_repository import update_contract_processing_status

# Anchor output root under the backend directory (not repository root).
# pipeline.py is at: backend/app/utils/text_extractor/pipeline.py
# parents[3] => backend/
BACKEND_DIR = Path(__file__).resolve().parents[3]
DEFAULT_OUTPUT_ROOT = BACKEND_DIR / "outputs"


@dataclass
class SentenceRow:
    """
    A single sentence extracted from a contract file.
    Note: contract_id maps to your DB entity id (int), not a UUID per file.
    """
    contract_id: int
    file_name: str
    file_type: str
    page: int
    sentence_id: int
    sentence: str


class ContractProcessor:
    """Processor for contract files (PDF/DOCX) and ZIP archives."""

    # ----------------------------
    # ZIP extraction helper
    # ----------------------------
    @staticmethod
    def extract_zip_files(zip_path: Path, extract_dir: Path) -> List[Path]:
        """
        Extract supported files (.pdf, .docx) from a ZIP into extract_dir.
        Keep nested folders inside zip (if any).
        """
        extracted_files: List[Path] = []

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                if file_info.is_dir():
                    continue
                file_path = Path(file_info.filename)
                if file_path.suffix.lower() in ['.pdf', '.docx']:
                    zip_ref.extract(file_info, extract_dir)
                    extracted_files.append(extract_dir / file_info.filename)

        return extracted_files

    # ----------------------------
    # Internal helpers for export
    # ----------------------------
    @staticmethod
    def _safe_folder_name(p: Path, used: set[str]) -> str:
        """
        Make a safe, de-duplicated folder name for a file under the output root.

        Default to <stem> (spaces -> underscores). If duplicated, fallback to
        <stem>_<ext> (without dot), and if still duplicated, append a numeric suffix.
        """
        base = p.stem.replace(" ", "_")
        candidate = base
        ext_tag = p.suffix.lower().lstrip(".") if p.suffix else "file"
        counter = 1

        while candidate in used:
            new_candidate = f"{base}_{ext_tag}" if counter == 1 else f"{base}_{ext_tag}-{counter}"
            candidate = new_candidate
            counter += 1

        used.add(candidate)
        return candidate

    @staticmethod
    def _export_df(df: pd.DataFrame, out_dir: Path, export_formats: List[str]) -> Dict[str, str]:
        """
        Write CSV/XLSX/TXT into out_dir. Return a dict of output file paths.
        If the DataFrame is empty, skip writing files to avoid empty artifacts.
        """
        if df.empty:
            return {}

        ensure_dir(out_dir)
        outputs: Dict[str, str] = {}

        # CSV
        if "csv" in export_formats:
            csv_path = out_dir / "sentences.csv"
            df.to_csv(csv_path, index=False, encoding="utf-8")
            outputs["csv"] = str(csv_path)

        # Excel
        if "xlsx" in export_formats:
            xlsx_path = out_dir / "sentences.xlsx"
            with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="sentences")
            outputs["xlsx"] = str(xlsx_path)

        # TXT (one sentence per line)
        if "txt" in export_formats:
            txt_path = out_dir / "sentences.txt"
            with open(txt_path, "w", encoding="utf-8") as f:
                for s in df["sentence"].tolist():
                    f.write((s or "").strip() + "\n")
            outputs["txt"] = str(txt_path)

        return outputs

    # ----------------------------
    # Core: process list of files (PER-FILE EXPORTS)
    # ----------------------------
    @staticmethod
    def process_files(
        file_paths: Iterable[Path],
        contract_id: int,
        output_dir: Path,
        export_formats: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Process PDF/DOCX files and export ONE SET PER INPUT FILE under:
            <output_dir>/<file_folder>/sentences.csv|xlsx|txt

        Return structure (JSON-friendly):
        {
          "files_processed": <int>,
          "sentences_extracted": <int>,        # total across all files
          "root_output_dir": "<output_dir>",
          "per_file": [
            {
              "file_name": "1.pdf",
              "file_type": "pdf",
              "folder_name": "1",              # actual folder created
              "output_dir": "<output_dir>/1",
              "sentences_extracted": 123,
              "outputs": {
                "csv": ".../sentences.csv",
                "xlsx": ".../sentences.xlsx",
                "txt": ".../sentences.txt"
              }
            },
            ...
          ],
          # Back-compat aggregate (folder_name -> outputs dict)
          "outputs": {
            "1": { "csv": "...", "xlsx": "...", "txt": "..." },
            "2": { ... }
          }
        }
        """
        if export_formats is None:
            export_formats = ["csv", "xlsx", "txt"]

        ensure_dir(output_dir)

        per_file: List[Dict[str, Any]] = []
        outputs_aggregate: Dict[str, Dict[str, str]] = {}
        total_sentences = 0
        files_processed = 0
        used_names: set[str] = set()  # to avoid folder name collisions
        # Collect rows across all files for a root-level aggregate export
        all_rows: List[SentenceRow] = []

        for path in file_paths:
            p = Path(path)
            ftype = detect_type(p)
            if ftype is None:
                # skip unsupported files quietly
                continue

            files_processed += 1
            sentence_counter = 0
            rows: List[SentenceRow] = []

            # Choose iterator based on file type
            chunks = iter_pdf_chunks(p) if ftype == "pdf" else iter_docx_chunks(p)

            for ch in chunks:
                # Debug logs helpful while stabilizing extraction across PDFs
                print(f"[extract] file={p.name}, page={ch.page}, text_length={len(ch.text)}")
                preview = (ch.text or "")[:120].replace("\n", " ")
                print(f"[extract] preview: {preview}...")

                sentences = split_into_sentences(ch.text)
                print(f"[extract] page {ch.page}: {len(sentences)} sentences")
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
            # Accumulate for aggregate root-level export
            all_rows.extend(rows)

            # Per-file output folder name (dedup if needed)
            folder_name = ContractProcessor._safe_folder_name(p, used_names)
            file_out_dir = output_dir / folder_name
            file_outputs = ContractProcessor._export_df(df, file_out_dir, export_formats)

            total_sentences += int(len(df))
            per_file.append({
                "file_name": p.name,
                "file_type": ftype,
                "folder_name": folder_name,
                "output_dir": str(file_out_dir),
                "sentences_extracted": int(len(df)),
                "outputs": file_outputs
            })
            outputs_aggregate[folder_name] = file_outputs

        return {
            "files_processed": files_processed,
            "sentences_extracted": total_sentences,
            "root_output_dir": str(output_dir),
            "per_file": per_file,
            "outputs": outputs_aggregate,  # back-compat convenience map
            # Root-level aggregate outputs (CSV/XLSX/TXT) for download endpoint compatibility
            # Note: written only if there are sentences
            **(lambda agg: {"root_outputs": agg} if agg else {})(
                ContractProcessor._export_df(
                    pd.DataFrame([asdict(r) for r in all_rows]),
                    output_dir,
                    export_formats
                )
            )
        }

    # ----------------------------
    # High-level: one contract job
    # ----------------------------
    @staticmethod
    def process_contract(
        db: Session,
        contract_id: int,
        user_id: int,
        file_path: str,
        file_type: str
    ) -> Dict[str, Any]:
        """
        Orchestrates a contract processing job:
        - Update status (processing -> completed/failed)
        - If .zip: extract supported files, then process all extracted
        - Else: process the single file
        - Export one set per file into: backend/outputs/<user_id>/<contract_id>/<file_stem>/
        - Return a summary dict
        """
        try:
            # 1) mark processing
            update_contract_processing_status(
                db=db,
                contract_id=contract_id,
                user_id=user_id,
                status="processing"
            )

            file_path_obj = Path(file_path)

            # Root output dir for this user+contract anchored under backend/
            output_dir = DEFAULT_OUTPUT_ROOT / str(user_id) / str(contract_id)
            ensure_dir(output_dir)

            if file_type.lower() == ".zip":
                # Extract and process extracted files
                extract_dir = output_dir / "extracted"
                ensure_dir(extract_dir)
                extracted_files = ContractProcessor.extract_zip_files(file_path_obj, extract_dir)
                result = ContractProcessor.process_files(
                    extracted_files, contract_id, output_dir
                )
            else:
                # Single file
                result = ContractProcessor.process_files(
                    [file_path_obj], contract_id, output_dir
                )

            # 2) mark completed
            update_contract_processing_status(
                db=db,
                contract_id=contract_id,
                user_id=user_id,
                status="completed"
            )

            # 3) return detailed summary
            return {
                "contract_id": contract_id,
                "total_sentences": result["sentences_extracted"],
                "root_output_dir": result["root_output_dir"],
                "outputs": result["outputs"],     # folder_name -> file paths
                "per_file": result["per_file"],   # detailed per-file entries
                "status": "completed"
            }

        except Exception as e:
            update_contract_processing_status(
                db=db,
                contract_id=contract_id,
                user_id=user_id,
                status="failed"
            )
            # Bubble up for API error handling layer to catch
            raise e
