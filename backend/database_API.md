# Core API (Service at `backend/app/main.py`, Port 5000)

**Base URL:** `http://localhost:5000`
**Swagger UI:** `/docs`

---

## 1) Authentication

* **POST** `/api/auth/register`
  **Request**

  ```json
  { "username": "alice", "password": "123456" }
  ```

  **Response**

  ```json
  { "id": 1, "username": "alice" }
  ```

* **POST** `/api/auth/login`
  **Response (example)**

  ```json
  { "access_token": "xxxxx.yyyyy.zzzzz", "token_type": "bearer" }
  ```

> All protected endpoints require the header:

```
Authorization: Bearer <access_token>
```

---

## 2) File Upload & Background Processing

* **POST** `/api/uploads/`
  **Content-Type:** `multipart/form-data` (field: `file`)
  **Response (example)**

  ```json
  {
    "contract_id": 16,
    "job_id": "0c9f...",
    "message": "Upload successful, background processing started"
  }
  ```

---

## 3) Monitoring & Queries

* **Recent uploads:** **GET** `/api/uploads/recent?limit=20`

* **Activity feed:** **GET** `/api/activity/recent?limit=20`

* **KPI panel:** **GET** `/api/analytics/kpi`
  **Response (example)**

  ```json
  {
    "total_contracts": 9,
    "total_sentences": 2488,
    "ambiguous_sentences": 214,
    "avg_explanation_clarity": 8.1,
    "avg_analysis_time_sec": 132.5
  }
  ```

* **Sentence details:** **GET** `/api/contracts/{contract_id}/sentences?limit=100&offset=0`
  **Returns** an array; each item includes:
  `page`, `sentence_id`, `sentence`, `label`, `is_ambiguous`, `clarity_score`, `section`, `subsection`.

---

# Analytics Subservice (`legal_analytics_api`, optional standalone)

If integrated by the main service, keep using `http://localhost:5000/api`.
If started separately, you may choose a different port (see commands in the subservice README).

## 1) Register Output Directory

* **POST** `/api/jobs/{job_id}/register`
  **Body**

  ```json
  { "outputs_dir": "ABSOLUTE_PATH/outputs/1/16" }
  ```

  The directory **must** contain `sentences.csv`.

## 2) Summary Overview

* **GET** `/api/jobs/{job_id}/analytics/summary`
  **Returns** data structures ready for front-end plotting (histograms, scatter plots, section word frequencies, etc.).
  **Optional query params:** `bins_pages`, `bins_sentence`, `topk`.

## 3) Data Download

* **GET** `/api/jobs/{job_id}/analytics/download/{kind}`
  **`{kind}` values:**

  * `pages_vs_contracts`
  * `sentence_length_hist`
  * `avg_sentence_length_hist`
  * `section_counts`
  * `subsection_counts`
  * `contracts_scatter`

**Response type:** `text/csv` — can be fetched and downloaded directly by the browser or rendered as a table.

---

# Database Schema (SQLite at `backend/app/app.db`)

| Table                | Key Fields                                                                                                                | Description                   |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------- | ----------------------------- |
| `users`              | `id`, `username`, `password_hash`, `created_at`                                                                           | Accounts                      |
| `contracts`          | `id`, `user_id`, `file_name`, `processing_status`, `processed_at`                                                         | Upload records                |
| `analysis_jobs`      | `id`, `contract_id`, `status`, `total_sentences`, `started_at`, `finished_at`, `duration_seconds`                         | Each background analysis task |
| `contract_sentences` | `id`, `contract_id`, `page`, `sentence_id`, `sentence`, `label`, `is_ambiguous`, `clarity_score`, `section`, `subsection` | Sentence-level data           |
| `activity_logs`      | `id`, `user_id`, `event_type`, `title`, `message`, `created_at`                                                           | System event stream           |

**Relationships**

* `contracts` **1—N** `analysis_jobs`
* `analysis_jobs` **1—N** `contract_sentences`
* `contracts` **1—N** `contract_sentences`

---

# Front-End Integration Tips

1. After login, store the `access_token` globally (e.g., `localStorage`) and inject it into Axios/fetch **Authorization** headers.
2. After uploading, you can immediately poll `/uploads/recent` or `/contracts/{id}/sentences`. Refresh the page when `processing_status → completed` or when `total_sentences > 0`.
3. Map KPI/Dashboard cards directly from `/analytics/kpi` fields; charts can use data from the Analytics subservice `/summary`.
4. For CSV export, call `/analytics/download/{kind}` and trigger a browser download from the response **Blob**.
5. **Dev DB inspection:**
   Open `app.db` with *DB Browser for SQLite* (prefer read-only or work on a copy).

