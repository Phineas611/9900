# Legal Analytics API (backend-only)

This FastAPI service exposes analytics endpoints for your contract sentences dataset
(exported by your existing **contract_sentence_extractor** tool as `sentences.csv`).

It provides:
- POST `/api/jobs/{job_id}/register` – Register an **outputs** directory containing `sentences.csv`.
- GET  `/api/jobs/{job_id}/analytics/summary` – JSON for charts (hist, scatter, box).
- GET  `/api/jobs/{job_id}/analytics/download/{kind}` – CSV downloads for the frontend.
  - `kind` ∈ {`pages_vs_contracts`, `sentence_length_hist`, `avg_sentence_length_hist`, `section_counts`, `subsection_counts`, `contracts_scatter`}.

> You can later add a `/process` endpoint that **calls your extractor** to produce `sentences.csv`,
> but this skeleton keeps responsibilities separate and simple.

## Run (dev)
```bash
python -m venv .venv
# Windows PowerShell:
#   & .\.venv\Scripts\Activate.ps1
# Linux/Mac:
#   source .venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload --port 5055
```

## Expected `sentences.csv` schema
Minimal columns used by the analytics:
- `contract_id` (str)
- `file_name` (str)
- `page` (int) – page number (1-based). If missing, will be imputed as 1.
- `sentence` (str)

Optional (if available, improves quality):
- `section` (str), `subsection` (str), `sentence_idx` (int).

If `section`/`subsection` are not present, the API applies a conservative regex over `sentence`
to infer common *Section / Article / Clause* headers like `Article II` or `Section 3.1`.

## Wire protocol design
- JSON responses are modelled to be front-end friendly (bins + counts for hist; scatter arrays; box stats).
- CSV downloads are normalized flat tables that the UI can fetch and hand to the user.


## New Dashboard Endpoints

- `POST /api/jobs/{job_id}/uploads/bulk_upsert` — Batch write/update "Recently Uploaded" records for KPIs & tables.
- `GET  /api/jobs/{job_id}/kpis?mode=last30` — Return 5 key performance indicators (current value + comparison with the previous period).
- `GET  /api/jobs/{job_id}/uploads/recent?limit=20` — Recently, the table data was uploaded.

### UploadRecord 字段
```json
{
  "filename": "NDA-123.pdf",
  "type": "PDF",
  "uploaded_at": "2025-10-12T09:15:00Z",
  "status": "COMPLETED",
  "started_at": "2025-10-12T09:16:00Z",
  "finished_at": "2025-10-12T09:18:36Z",
  "progress_pct": 100,
  "ambiguous_count": 14,
  "total_sentences": 238,
  "avg_explanation_clarity": 8.7,
  "duration_seconds": 156,
  "analysis_summary": "Ambiguous clauses in Sections 2, 3.1, 7.4",
  "actions": {"view": "/contracts/NDA-123", "download_report": "/api/reports/NDA-123.csv"}
}
```
# Legal Analytics API — Dashboard & Analytics Guide

This document describes the backend endpoints and data flow for your **Dashboard** page and **Analytics** (charts & downloads).
It is designed to work with the extractor that exports `outputs/sentences.csv` and with a lightweight event log `uploads.jsonl`.

---

## Quick Start

```powershell
# From the project root (this folder)
py -3 -m venv .venv
& .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

uvicorn app.main:app --reload --port 5055
```

Register your extractor outputs directory (contains `sentences.csv`):
```powershell
$body = @{ outputs_dir = "D:\...\contract_sentence_extractor\outputs" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:5055/api/jobs/demo/register" -ContentType "application/json" -Body $body
```

---

## Data Stores

- **`sentences.csv`** (from your extractor): one row per sentence; used for distributions/trends.
- **`storage/jobs/{job_id}/pointer.txt`**: stores the absolute path to the `outputs/` directory that contains `sentences.csv`.
- **`storage/jobs/{job_id}/uploads.jsonl`**: event log of recent uploads/runs; used for KPIs and the “Recent Uploads” table.
  - Upsert key = `filename + uploaded_at`.

> A **job** is a logical dataset registered via `/api/jobs/{job_id}/register`. All endpoints operate within a job’s data.

---

## 1) Bulk Upsert “Recent Uploads” (drives KPIs & table)

**POST** `/api/jobs/{job_id}/uploads/bulk_upsert`

Request body:
```json
{
  "uploads": [
    {
      "filename": "NDA-123.pdf",
      "type": "PDF",
      "uploaded_at": "2025-10-12T09:15:00Z",
      "status": "COMPLETED",
      "started_at": "2025-10-12T09:16:00Z",
      "finished_at": "2025-10-12T09:18:36Z",
      "progress_pct": 100,
      "ambiguous_count": 14,
      "total_sentences": 238,
      "avg_explanation_clarity": 8.7,
      "duration_seconds": 156,
      "analysis_summary": "Ambiguous clauses in Sections 2, 3.1, 7.4",
      "actions": {"view": "/contracts/NDA-123", "download_report": "/api/reports/NDA-123.csv"}
    }
  ]
}
```

Server persists records to `storage/jobs/{job_id}/uploads.jsonl` (JSON Lines). Upsert key is `filename + uploaded_at`.

**Field usage:**  
- `status` → contributes to **`total_contracts_processed`** (only `COMPLETED` counted).  
- `total_sentences` / `ambiguous_count` → **`sentences_classified` / `ambiguous_sentences_count`**.  
- `avg_explanation_clarity`, `started_at`, `finished_at`, `duration_seconds` → used by the rest of the KPIs.  

---

## 2) KPI Cards (top 4 + optional “ambiguous” card)

**GET** `/api/jobs/{job_id}/kpis?mode=last30`

Query params:
- `mode = last30 | this_month | custom`
- when `custom`, also pass `since=ISO&until=ISO`

Sample response:
```json
{
  "total_contracts_processed": { "value": 18, "prev": 12, "delta_pct": 50.0, "delta_diff": 6.0 },
  "sentences_classified":      { "value": 4217, "prev": 3765, "delta_pct": 12.0, "delta_diff": 452.0 },
  "ambiguous_sentences_count": { "value": 338,  "prev": 290,  "delta_pct": 16.6, "delta_diff": 48.0 },
  "avg_explanation_clarity":   { "value": 8.7,  "prev": 8.2,  "delta_pct": 6.1,  "delta_diff": 0.5 },
  "avg_analysis_time_minutes": { "value": 4.5,  "prev": 4.65, "delta_pct": -3.2, "delta_diff": -0.15 }
}
```

**Definitions:**
- `total_contracts_processed.value` = count of records with `status=COMPLETED` in the period.  
- `sentences_classified.value` = sum of `total_sentences` in the period.  
- `ambiguous_sentences_count.value` = sum of `ambiguous_count` in the period (use this for the ⚠️ card if desired).  
- `avg_explanation_clarity.value` = mean of `avg_explanation_clarity` for completed records.  
- `avg_analysis_time_minutes.value` = mean of durations for completed records (prefer `duration_seconds`; otherwise `finished_at - started_at`).  
- `prev` metrics are computed over the **previous window of equal length**.  
- `delta_pct = ((value - prev)/prev)*100` (if `prev=0`, only `delta_diff` is provided).

---

## 3) Recent Uploads Table

**GET** `/api/jobs/{job_id}/uploads/recent?limit=20`

Response:
```json
{
  "rows": [
    {
      "filename": "NDA-123.pdf",
      "type": "PDF",
      "uploaded_at": "2025-10-12T09:15:00Z",
      "status": "COMPLETED",
      "analysis_summary": "Ambiguous clauses in Sections 2, 3.1, 7.4",
      "progress_pct": 100,
      "ambiguous_count": 14,
      "total_sentences": 238,
      "avg_explanation_clarity": 8.7,
      "duration_seconds": 156,
      "actions": {"view": "/contracts/NDA-123", "download_report": "/api/reports/NDA-123.csv"}
    }
  ]
}
```
If `duration_seconds` is missing, the server computes it from `finished_at - started_at`.  
Rows are ordered by `uploaded_at` (fallback to `started_at`) descending.

---

## 4) Analytics (distributions & downloads)

### Summary for charts
**GET** `/api/jobs/{job_id}/analytics/summary`

Returns:
- `metadata` — counts: contracts, sentences, files  
- `page_length_hist` — histogram `{ bins, counts }` of pages-per-contract → “页面长度与合同数量”.  
- `sentence_length_hist` — histogram of per-sentence character lengths.  
- `avg_sentence_length_hist` — histogram of per-contract average sentence length.  
- `contracts_scatter` — list of points `{ pages, sentences, avg_sentence_len, file_name, contract_id }`.  
- `section_frequency` — top-K sections (e.g., *Section 1*, *Article II*).  
- `subsection_frequency` — top-K subsections (e.g., *3.1*, *4.2.1*).  
- `sentence_length_box` — boxplot stats `{ min, q1, median, q3, max }`.

> If `sentences.csv` lacks `section`/`subsection`, the service **conservatively infers** them from sentence text (regexes such as `Article II`, `Section 3.1`).

### CSV downloads
**GET** `/api/jobs/{job_id}/analytics/download/{kind}`

`{kind}` options:
- `pages_vs_contracts` — one row per contract with page counts  
- `sentence_length_hist` — histogram bins for sentence lengths  
- `avg_sentence_length_hist` — histogram bins for avg sentence length per contract  
- `section_counts` — frequency of sections  
- `subsection_counts` — frequency of subsections  
- `contracts_scatter` — raw scatter points (`pages`, `sentences`, `avg_sentence_len`)

---

## 5) Schemas

### `sentences.csv` (minimum)
- **Required**: `contract_id` (str), `file_name` (str), `sentence` (str)  
- **Recommended**: `page` (int) — used for page counts (defaults to 1 if missing)  
- **Optional**: `section` (str), `subsection` (str), `sentence_idx` (int)

### Upload record (one line in `uploads.jsonl`)
```json
{
  "filename": "NDA-123.pdf",
  "type": "PDF",
  "uploaded_at": "2025-10-12T09:15:00Z",
  "status": "COMPLETED",
  "started_at": "2025-10-12T09:16:00Z",
  "finished_at": "2025-10-12T09:18:36Z",
  "progress_pct": 100,
  "ambiguous_count": 14,
  "total_sentences": 238,
  "avg_explanation_clarity": 8.7,
  "duration_seconds": 156,
  "analysis_summary": "Ambiguous clauses in Sections 2, 3.1, 7.4",
  "actions": {"view": "/contracts/NDA-123", "download_report": "/api/reports/NDA-123.csv"}
}
```

---

## 6) Integration Steps

1. Unzip `legal_analytics_api_with_kpi.zip` into your repo, e.g.:
   ```text
   D:\LegalContractAnalyzer_h18c_bread-login-register\services\legal_analytics_api\
   ```
2. Start the API (see **Quick Start**).
3. Register your extractor outputs: `POST /api/jobs/{job}/register`.
4. Feed upload/run events via `POST /api/jobs/{job}/uploads/bulk_upsert`.
5. Frontend calls:
   - KPIs: `GET /api/jobs/{job}/kpis?mode=last30`
   - Recent uploads: `GET /api/jobs/{job}/uploads/recent?limit=20`
   - Analytics summary: `GET /api/jobs/{job}/analytics/summary`
   - CSV downloads: `GET /api/jobs/{job}/analytics/download/{kind}`

---

## 7) Sample Shapes (for frontend)

Histogram:
```json
"page_length_hist": { "bins": [1,4,7,...], "counts": [3,5,2,...] }
```

Scatter:
```json
"contracts_scatter": [
  {"contract_id":"abc","file_name":"A.pdf","pages":12,"sentences":540,"avg_sentence_len":148.7}
]
```

Top-K frequencies:
```json
"section_frequency": [
  {"section":"Section 1","count":84}, {"section":"Article II","count":71}
]
```

---

## Notes
- All endpoints are **job-scoped**. Use different `job_id`s to separate datasets/users/batches.
- If `prev` window in KPIs has `0`, `delta_pct` is omitted and only `delta_diff` is returned.
- You can replace file storage (`uploads.jsonl` & `pointer.txt`) with a database without changing the API.
