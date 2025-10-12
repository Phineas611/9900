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

@dataclass
class SentenceRow:
    contract_id: int
    file_name: str
    file_type: str
    page: int
    sentence_id: int
    sentence: str

class ContractProcessor:
    
    @staticmethod
    def extract_zip_files(zip_path: Path, extract_dir: Path) -> List[Path]:     
        extracted_files = []
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            for file_info in zip_ref.infolist():
                if file_info.is_dir():
                    continue
                
                file_path = Path(file_info.filename)
                if file_path.suffix.lower() in ['.pdf', '.docx']:
                    zip_ref.extract(file_info, extract_dir)
                    extracted_files.append(extract_dir / file_info.filename)
        
        return extracted_files
    
    @staticmethod
    def process_files(
        file_paths: Iterable[Path],
        contract_id: int,
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
            sentence_counter = 0
            
            chunks = iter_pdf_chunks(p) if ftype == "pdf" else iter_docx_chunks(p)
            
            for ch in chunks:
                print(f"Processing chunk: page={ch.page}, text_length={len(ch.text)}")
                print(f"Text preview: {ch.text[:100]}...")
                sentences = split_into_sentences(ch.text)
                print(f"Extracted {len(sentences)} sentences")
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
                for row in rows:
                    f.write(row.sentence.strip() + "\n")
            outputs["txt"] = str(txt_path)
        
        return {
            "files_processed": file_count,
            "sentences_extracted": int(len(df)),
            "output_dir": str(output_dir),
            "outputs": outputs,
        }
    
    @staticmethod
    def process_contract(
        db: Session,
        contract_id: int,
        user_id: int,
        file_path: str,
        file_type: str
    ) -> Dict[str, Any]:
        try:
           
            update_contract_processing_status(
                db=db,
                contract_id=contract_id,
                user_id=user_id,
                status="processing"
            )
            
            file_path_obj = Path(file_path)
            output_dir = Path("outputs") / str(user_id) / str(contract_id)
            ensure_dir(output_dir)
            all_sentences = []
            
            if file_type == ".zip":
               
                extract_dir = output_dir / "extracted"
                ensure_dir(extract_dir)
                
                extracted_files = ContractProcessor.extract_zip_files(file_path_obj, extract_dir)
                result = ContractProcessor.process_files(extracted_files, contract_id, output_dir)
            else:
               
                result = ContractProcessor.process_files([file_path_obj], contract_id, output_dir)
            
           
            update_contract_processing_status(
                db=db,
                contract_id=contract_id,
                user_id=user_id,
                status="completed"
            )
            
            return {
                "contract_id": contract_id,
                "total_sentences": result["sentences_extracted"],
                "outputs": result["outputs"],
                "status": "completed"
            }
            
        except Exception as e:
            update_contract_processing_status(
                db=db,
                contract_id=contract_id,
                user_id=user_id,
                status="failed"
            )
            raise e