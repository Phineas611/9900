# Complete Testing Workflow

## Overview
This document describes how to test the complete workflow:
1. Upload & Extract sentences
2. Classify with Prompt Lab
3. Evaluate with Evaluation Lab  
4. Test Analytics APIs

---

## Prerequisites
- Backend running on `http://localhost:5000`
- User account exists (User ID: 2, Email: newuser@example.com)
- Have a PDF file ready for testing

---

## Step 1: Upload & Extract

### 1.1 Upload a contract file
```bash
curl -X POST "http://localhost:5000/api/uploads/" \
  -H "Cookie: session=YOUR_SESSION_TOKEN" \
  -F "file=@/path/to/test.pdf"
```

**Response:**
```json
{
  "contract_id": 39,
  "file_name": "test.pdf",
  "file_type": ".pdf",
  "file_size": 12345,
  "message": "File uploaded successfully, processing in background"
}
```

**Save `contract_id` for next steps!**

### 1.2 Check processing status
```bash
curl "http://localhost:5000/api/uploads/39/status" \
  -H "Cookie: session=YOUR_SESSION_TOKEN"
```

Wait until `processing_status` is `completed`.

### 1.3 Import sentences into database
```bash
curl -X POST "http://localhost:5000/api/contracts/39/sentences/import" \
  -H "Cookie: session=YOUR_SESSION_TOKEN"
```

**Response:**
```json
{
  "contract_id": 39,
  "job_id": "abc-123-def",
  "imported_count": 150,
  "csv_path": "..."
}
```

---

## Step 2: Prompt Lab Classification

### 2.1 Get available models
```bash
curl "http://localhost:5000/api/promptlab/models"
```

**Response:**
```json
{
  "available": [...],
  "current": {"id": "distilbert-base", ...}
}
```

### 2.2 Get extracted sentences
```bash
# First, get the job_id from Step 1.3
curl "http://localhost:5000/api/extract/YOUR_JOB_ID"
```

### 2.3 Classify sentences
```bash
curl -X POST "http://localhost:5000/api/promptlab/classify" \
  -H "Content-Type: application/json" \
  -d '{
    "sentences": [
      "The parties agree to use reasonable efforts to complete the transaction.",
      "Payment shall be made within 30 days."
    ],
    "prompt_id": "amb-basic",
    "contract_id": 39
  }'
```

**Response:**
```json
[
  {
    "sentence": "The parties agree...",
    "label": "AMBIGUOUS",
    "score": 0.9,
    "model_id": "distilbert-base",
    "rationale": "...",
    "contract_id": 39,
    "sentence_id": 1
  },
  ...
]
```

### 2.4 Explain sentences (with rationale)
```bash
curl -X POST "http://localhost:5000/api/promptlab/explain/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "sentences": [
      "The parties agree to use reasonable efforts...",
      "Payment shall be made within 30 days."
    ],
    "prompt_id": "amb-basic",
    "contract_id": 39
  }'
```

---

## Step 3: Export for Evaluation Lab

### 3.1 Download classified sentences as CSV
You need to get sentences with labels and rationales from the database.

**Option A: Use existing CSV from outputs**
```bash
curl "http://localhost:5000/api/uploads/39/download/csv" \
  -H "Cookie: session=YOUR_SESSION_TOKEN" \
  -o sentences_with_labels.csv
```

**Option B: Query database and format as CSV manually**

Required columns:
- `item_id` (or `id`)
- `sentence` 
- `predicted_label` (from Prompt Lab: AMBIGUOUS/UNAMBIGUOUS)
- `rationale`
- `gold_label` (optional)

Example CSV:
```csv
item_id,sentence,predicted_label,rationale,gold_label
1,"The parties agree to use reasonable efforts to complete the transaction.","AMBIGUOUS","The phrase 'reasonable efforts' is subjective.",UNAMBIGUOUS
2,"Payment shall be made within 30 days.","UNAMBIGUOUS","Specific timeframe provided.",UNAMBIGUOUS
```

---

## Step 4: Evaluation Lab

### 4.1 Upload results file
```bash
curl -X POST "http://localhost:5000/api/eval-lab/upload" \
  -F "file=@sentences_with_labels.csv"
```

**Response:**
```json
{
  "job_id": "eval-job-123",
  "columns_detected": {...},
  "preview_rows": [...]
}
```

### 4.2 Run evaluation
```bash
curl -X POST "http://localhost:5000/api/eval-lab/run" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "eval-job-123",
    "judges": ["groq/llama-3.1-8b", "groq/llama-3.3-70b"],
    "rubrics": {
      "grammar": true,
      "word_choice": true,
      "cohesion": true
    },
    "custom_metrics": []
  }'
```

**Response:**
```json
{
  "job_id": "eval-job-123",
  "total": 2,
  "started_at": "2025-..."
}
```

### 4.3 Check evaluation status
```bash
curl "http://localhost:5000/api/eval-lab/jobs/eval-job-123"
```

### 4.4 Get evaluation results
```bash
curl "http://localhost:5000/api/eval-lab/jobs/eval-job-123/records?page=1&page_size=10"
```

### 4.5 Download results
```bash
curl "http://localhost:5000/api/eval-lab/jobs/eval-job-123/export.csv" -o eval_results.csv
```

---

## Step 5: Test Analytics APIs

### 5.1 Contract statistics
```bash
curl "http://localhost:5000/api/contracts/stats"
```

### 5.2 Trend charts
```bash
curl "http://localhost:5000/api/charts/trends?range=3months"
```

### 5.3 Recurring phrases
```bash
curl "http://localhost:5000/api/phrases/recurring?limit=20"
```

### 5.4 Contracts list
```bash
curl "http://localhost:5000/api/contracts?page=1&limit=10"
```

### 5.5 KPI analytics
```bash
curl "http://localhost:5000/api/analytics/kpi"
```

---

## Quick Test Script

Save this as `test_workflow.sh`:

```bash
#!/bin/bash
# Quick workflow test

BASE_URL="http://localhost:5000/api"
CONTRACT_ID=39

echo "=== Step 1: Upload ==="
echo "Upload a file via: POST $BASE_URL/uploads/"

echo "=== Step 2: Import ==="
curl -X POST "$BASE_URL/contracts/$CONTRACT_ID/sentences/import"

echo "=== Step 3: Prompt Lab ==="
curl -X POST "$BASE_URL/promptlab/explain/batch" \
  -H "Content-Type: application/json" \
  -d '{"sentences": ["Test sentence"], "contract_id": '$CONTRACT_ID'}'

echo "=== Step 4: Analytics ==="
curl "$BASE_URL/contracts/stats"
curl "$BASE_URL/charts/trends"
curl "$BASE_URL/phrases/recurring"
```

Run with: `bash test_workflow.sh`

---

## Troubleshooting

### Issue: Authentication required
**Solution:** Get session cookie first:
```bash
curl -X POST "http://localhost:5000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "newuser@example.com", "password": "your_password"}' \
  -c cookies.txt

# Then use: curl -b cookies.txt ...
```

### Issue: No ambiguity data
**Solution:** Make sure Step 3 (Prompt Lab) completed successfully and updated database records.

### Issue: Evaluation Lab judges fail
**Solution:** Check environment variables: `GROQ_API_KEY`, `HF_TOKEN`

---

## Expected Results

After completing all steps:
- ✅ Contract uploaded and processed
- ✅ Sentences extracted and stored
- ✅ Sentences classified (AMBIGUOUS/UNAMBIGUOUS)
- ✅ Evaluation results generated
- ✅ Analytics APIs showing non-zero ambiguity rates

---

## Notes

- Replace `YOUR_SESSION_TOKEN` with actual session cookie value
- Replace `YOUR_JOB_ID` with actual job ID from responses
- Contract IDs, Job IDs are examples - use actual values from responses
- Processing may take time depending on file size and model API latency

