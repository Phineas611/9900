# Contract Sentence Extractor (Sprint 1 – US2/US3 core)

This package provides a minimal, production-friendly pipeline and API to **extract sentences** from **PDF** and **DOCX** contracts and **export** them as **CSV/XLSX/TXT**.  
It is designed to plug in **after teammate B** has already handled file uploads and optional ZIP extraction (only PDF/DOCX are passed in).

> Scope alignment: Upload, extraction, downloads and basic data outputs are part of Sprint 1 (US1–US4). This module implements the **extraction and export** portion you own (US2 & US3) and can be called by B's upload/unzip step.


## Quick Start

### 1) Install
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r app/requirements.txt
```

### 2) Run the API (so B can call you)
```bash
python -m app.main --serve --host 0.0.0.0 --port 5001
# Health check:
#   GET http://localhost:5001/api/health  -> {"status":"ok"}
# Extraction (multipart form):
#   POST http://localhost:5001/api/extract
#   form-data field: files[] = <one or more PDF/DOCX>
#   optional: ?out=./outputs_custom
```

### 3) Or use CLI (local batch, no server)
```bash
python -m app.main --input "./contracts/*.pdf" "./contracts/*.docx" --out "./outputs" --formats csv xlsx txt
```

### 4) Outputs
Writes `outputs/sentences.csv`, `outputs/sentences.xlsx`, and `outputs/sentences.txt` by default.  
Schema (CSV/XLSX):  
- `contract_id` (uuid4 per file)  
- `file_name`  
- `file_type` (pdf|docx)  
- `page` (0 for DOCX when page is unknown; PDF pages start at 1)  
- `sentence_id` (1..N per file)  
- `sentence`  


## Implementation Notes

- **Parsing**
  - **PDF:** Uses `pdfminer.six` to collect visible text **per page** (preserves page numbers for downstream UI mapping).
  - **DOCX:** Uses `python-docx` to read paragraphs; DOCX has no stable page info, so `page=0`.
- **Splitting**
  - `app/extractor/splitter.py` is a **legal-aware regex splitter** with common abbreviation protections (`Sec.`, `No.`, `Ltd.`, `U.S.`, `e.g.`, etc.).
  - Very long sentences may additionally split on `; ` when followed by a capital letter (common in legal drafting).
- **Exports**
  - CSV via `pandas.to_csv`, Excel via `openpyxl`, TXT as one sentence per line.
- **Extensibility**
  - Optional OCR fallback can be added (commented deps in `requirements.txt`) for scanned PDFs when needed.
  - You can swap in spaCy or a custom ML splitter later without changing the API.

## API Contract (for teammate B)

**Endpoint:** `POST /api/extract`  
**Form field:** `files[]` (multiple) with `.pdf` or `.docx` only  
**Query param (optional):** `?out=/absolute/or/relative/folder`  
**Response (200):**
```json
{
  "files_processed": 3,
  "sentences_extracted": 1243,
  "output_dir": "./outputs",
  "outputs": {
    "csv": "./outputs/sentences.csv",
    "xlsx": "./outputs/sentences.xlsx",
    "txt": "./outputs/sentences.txt"
  }
}
```
**Errors (400):**
```json
{"error": "No 'files' field in form-data"}
{"error": "No valid PDF/DOCX files uploaded"}
```

## Project Layout

```
contract_sentence_extractor/
├─ app/
│  ├─ extractor/
│  │  ├─ utils.py
│  │  ├─ parsers.py
│  │  └─ splitter.py
│  ├─ main.py
│  └─ requirements.txt
├─ outputs/           # exported files written here by default
├─ tests/
│  └─ test_smoke.md   # quick smoke instructions
├─ scripts/
│  └─ run_dev.sh
└─ README.md
```

## Testing (Smoke)

1. Put a few sample contracts under `./contracts/` (PDF/DOCX).  
2. Run the CLI:
   ```bash
   python -m app.main --input "./contracts/*.pdf" "./contracts/*.docx" --out "./outputs"
   ```
3. Confirm `outputs/sentences.csv` exists and opens in Excel.

## Notes

- If a PDF is **image-only** (scanned), `pdfminer.six` will return empty text. To handle these, enable OCR:
  - Install system deps (`tesseract`, `poppler`) and uncomment `pytesseract`/`pdf2image` in `requirements.txt`.
  - Add an OCR fallback in `parsers.py` (kept minimal here for portability).
- This module focuses on **US2/US3**. The **dashboard (US4)** is owned by another teammate.  
- Keep raw files in object storage and use the `contract_id` + `file_name` to tie UI highlights and exports later.
