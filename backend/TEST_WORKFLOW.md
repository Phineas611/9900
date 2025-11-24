# Complete Testing Workflow

## Overview
<<<<<<< HEAD

This document describes how to use the `test_workflow.py` script to perform comprehensive end-to-end testing, covering all API endpoints, error handling, and boundary condition testing.

## Test Script Features

`test_workflow.py` is a comprehensive automated test script that includes three testing phases:

1. **🔴 Phase 1: Error Handling Tests** - Tests various error scenarios (404, 400, 401, 500)
2. **🟢 Phase 2: Normal Workflow Tests** - Tests complete business workflows
3. **🟡 Phase 3: Boundary Condition Tests** - Tests edge cases and abnormal inputs
=======
This document describes how to test the complete workflow:
1. Upload & Extract sentences
2. Classify with Prompt Lab
3. Evaluate with Evaluation Lab  
4. Test Analytics APIs
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98

---

## Prerequisites
<<<<<<< HEAD

- **Backend Server Running**: `http://localhost:5000`
- **Python Environment**: Python 3.7+, with `requests` library installed
- **Test User**: Default uses `user@example.com` / `string` (can be modified in the script)
- **Test Files**: Prepare a PDF file or directory containing PDF files

---

## Usage

### Method 1: Run Python Script Directly

```bash
# Using a single PDF file
python test_workflow.py path/to/contract.pdf

# Using a directory (automatically selects the first PDF file)
python test_workflow.py path/to/pdf/directory
```

### Method 2: Use Windows Batch Script

```bash
# Using default path
run_test.bat

# Specify file or directory
run_test.bat "C:\path\to\contract.pdf"
run_test.bat "C:\path\to\pdf\directory"
```

### Method 3: Use PowerShell Script

```powershell
# Using default path
.\run_test.ps1

# Specify file or directory
.\run_test.ps1 "C:\path\to\contract.pdf"
.\run_test.ps1 "C:\path\to\pdf\directory"
```

---

## Test Coverage

### Phase 1: Error Handling Tests

#### 1. Health Check (`test_healthcheck`)
- **Endpoint**: `GET /healthcheck`
- **Test**: Whether the server is running normally
- **Timeout**: 5 seconds
- **Error Handling**: Catches timeout and connection errors

#### 2. 404 Error Test (`test_error_404`)
- **Endpoints**: 
  - `GET /uploads/999999/status` (non-existent contract)
  - `GET /eval-lab/jobs/non-existent-job/state` (non-existent job)
  - `GET /extract/non-existent-job-id` (non-existent extraction job)
- **Expected**: All requests should return 404
- **Timeout**: 5 seconds

#### 3. 400 Error Test (`test_error_400`)
- **Endpoints**:
  - `POST /promptlab/explain/batch` (empty request body)
  - `POST /promptlab/explain/one` (missing required fields)
  - `POST /eval-lab/run` (empty job_id)
- **Expected**: Returns 400 or 422
- **Timeout**: 5 seconds

#### 4. 401 Error Test (`test_error_401`)
- **Endpoints**:
  - `GET /uploads/recent` (without authentication)
  - `GET /auth/me` (invalid session token)
- **Expected**: Returns 401
- **Timeout**: 5 seconds

#### 5. 500 Error Test (`test_error_500`)
- **Endpoint**: `POST /promptlab/models/switch` (invalid model_id)
- **Expected**: Returns 404 or 500
- **Timeout**: 5 seconds

#### 6. Invalid File Upload (`test_invalid_file_upload`)
- **Endpoint**: `POST /uploads/` (invalid file type or empty file)
- **Expected**: Returns 400 or 415
- **Requirement**: Requires authentication

---

### Phase 2: Normal Workflow Tests

#### 1. Authentication (`get_session_token`)
- **Endpoint**: `POST /auth/login`
- **Function**: Login and get session token
- **Timeout**: 10 seconds

#### 2. User Info (`test_auth_me`)
- **Endpoint**: `GET /auth/me`
- **Function**: Get current user information

#### 3. File Upload (`upload_file`)
- **Endpoint**: `POST /uploads/`
- **Function**: Upload contract file (PDF or ZIP)
- **Returns**: `contract_id`

#### 4. Processing Status Check (`check_processing_status`)
- **Endpoint**: `GET /uploads/{contract_id}/status`
- **Function**: Poll processing status and wait for completion
- **Timeout**: 60 seconds

#### 5. File Download (`test_download_file`)
- **Endpoint**: `GET /uploads/{contract_id}/download/{format}`
- **Formats**: CSV or XLSX
- **Function**: Download processed file

#### 6. Recent Uploads (`test_uploads_recent`)
- **Endpoint**: `GET /uploads/recent?limit=5`
- **Function**: Get list of recently uploaded files

#### 7. Import Sentences (`import_sentences`)
- **Endpoint**: `POST /contracts/{contract_id}/sentences/import`
- **Function**: Import extracted sentences into database
- **Returns**: `job_id`

#### 8. Get Extracted Sentences (`get_extracted_sentences`)
- **Endpoint**: `GET /extract/{job_id}`
- **Function**: Get list of extracted sentences
- **Requirement**: Requires authentication

#### 9. Contract Sentences (`test_contract_sentences`)
- **Endpoint**: `GET /contracts/{contract_id}/sentences`
- **Function**: Get list of contract sentences

#### 10. Prompt Lab - Model Management
- **Get Models** (`test_promptlab_models`): `GET /promptlab/models`
- **Switch Model** (`test_promptlab_switch_model`): `POST /promptlab/models/switch`
- **Get Prompts** (`test_promptlab_prompts`): `GET /promptlab/prompts`

#### 11. Prompt Lab - Sentence Classification
- **Batch Explain** (`classify_sentences`): `POST /promptlab/explain/batch`
- **Single Explain** (`test_promptlab_explain_one`): `POST /promptlab/explain/one`
- **Classify** (`test_promptlab_classify`): `POST /promptlab/classify`

#### 12. Prompt Lab - File Processing (Async)
- **Upload File** (`test_promptlab_explain_file`): `POST /promptlab/explain/file`
  - Creates test CSV file
  - Uploads and gets `task_id`
  - Polls status until completion
  - Downloads result file
- **Task Status** (`test_promptlab_file_status`): `GET /promptlab/explain/file/status/{task_id}`
- **Task Result** (`test_promptlab_file_result`): `GET /promptlab/explain/file/result/{task_id}`

#### 13. Analytics API (`check_analytics`)
- **Contract Statistics**: `GET /contracts/stats`
- **Trend Charts**: `GET /charts/trends?range=3months`
- **Recurring Phrases**: `GET /phrases/recurring?limit=5`
- **KPI Analytics**: `GET /analytics/kpi`

#### 14. Other Analytics Endpoints
- **Recent Activity** (`test_activity_recent`): `GET /activity/recent?limit=5`
- **Contracts List** (`test_contracts_list`): `GET /contracts?page=1&limit=10`
- **Reports Data** (`test_reports_data`): `GET /reports/data`
- **Reports Export** (`test_reports_export`): `POST /reports/export`

#### 15. Evaluation Lab - Config (`test_eval_config`)
- **Endpoint**: `GET /eval-lab/config`
- **Function**: Get available judges and rubrics

#### 16. Evaluation Lab - Upload (`upload_for_evaluation`)
- **Endpoint**: `POST /eval-lab/upload`
- **Function**: Upload CSV file containing classification results
- **Returns**: `job_id`

#### 17. Evaluation Lab - Run Evaluation (`run_evaluation`)
- **Endpoint**: `POST /eval-lab/run`
- **Function**: Start evaluation task (async)
- **Accepts Status Codes**: 200 or 202

#### 18. Evaluation Lab - Job State (`test_eval_job_state`)
- **Endpoint**: `GET /eval-lab/jobs/{job_id}/state`
- **Function**: Poll job status
- **Max Polls**: 5 times

#### 19. Evaluation Lab - Export Results
- **CSV Export** (`test_eval_export_csv`): `GET /eval-lab/jobs/{job_id}/export.csv`
- **XLSX Export** (`test_eval_export_xlsx`): `GET /eval-lab/jobs/{job_id}/export.xlsx`
- **Note**: 409 status code indicates file is being generated (expected behavior)

---

### Phase 3: Boundary Condition Tests

#### 1. Empty Data Handling (`test_empty_data`)
- **Test**: Empty sentence list, very long sentences
- **Endpoint**: `POST /promptlab/explain/batch`

#### 2. Special Characters (`test_special_characters`)
- **Test**: Sentences containing special characters
- **Endpoint**: `POST /promptlab/explain/batch`

#### 3. Large Batch Processing (`test_large_batch`)
- **Test**: Process 50 sentences
- **Endpoint**: `POST /promptlab/explain/batch`

#### 4. Pagination Boundaries (`test_pagination_boundaries`)
- **Test**: 
  - `page=0` or negative numbers
  - Very large page number (`page=999999`)
  - `limit=0` or very large values
- **Endpoint**: `GET /contracts?page={page}&limit={limit}`

---

## Detailed Test Workflow

### Complete Workflow

```
1. Health Check
   ↓
2. Error Handling Tests (404, 400, 401, 500)
   ↓
3. Login to get session token
   ↓
4. Upload contract file
   ↓
5. Wait for processing to complete
   ↓
6. Download processed file
   ↓
7. Import sentences into database
   ↓
8. Get extracted sentences
   ↓
9. Prompt Lab classification (batch, single, file)
   ↓
10. Test Analytics APIs
   ↓
11. Create evaluation CSV
   ↓
12. Upload to Evaluation Lab
   ↓
13. Run evaluation
   ↓
14. Poll evaluation status
   ↓
15. Export evaluation results
   ↓
16. Boundary condition tests
```

---

## Test Output Explanation

### Success Markers
- ✅ Indicates test passed
- ⚠️ Indicates warning (possible issue, but doesn't stop testing)
- ❌ Indicates test failed

### Status Code Explanation
- **200**: Success
- **202**: Accepted (async task started)
- **400**: Bad Request
- **401**: Unauthorized
- **404**: Not Found
- **409**: Conflict (file is being generated, expected behavior)
- **422**: Validation Error
- **500**: Server Error

---

## Error Handling and Timeout Mechanisms

### Timeout Settings
- **Health Check**: 5 seconds
- **Login**: 10 seconds
- **File Processing Wait**: 60 seconds
- **Async Task Polling**: 60 seconds
- **Error Tests**: 5 seconds

### Error Handling
All network requests include:
- `timeout` parameter
- `try-except` blocks to catch `Timeout` and `ConnectionError`
- Skip tests and show prompt when server is unavailable

### Retry Mechanism
- **Evaluation Results Fetch**: Retry up to 3 times with 2-second intervals
- **Async Task Status**: Poll until completion or timeout

---

## Configuration Options

### Modify Test User

Edit in `test_workflow.py`:

```python
TEST_EMAIL = "user@example.com"
TEST_PASSWORD = "string"
```

### Modify Default Path

Edit in `run_test.bat` or `run_test.ps1`:

```batch
set TEST_PATH="C:\your\default\path"
```
=======
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
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98

---

## Troubleshooting

<<<<<<< HEAD
### 1. Health Check Timeout

**Issue**: `❌ Health check timeout: Server not responding`

**Solution**:
```bash
# Make sure backend server is running
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 5000
```

### 2. Authentication Failed

**Issue**: `❌ Login failed: 401`

**Solution**:
- Check if test user exists
- Verify password is correct
- Check backend authentication configuration

### 3. File Upload Failed

**Issue**: `❌ Upload failed: 400`

**Solution**:
- Confirm file format is PDF or ZIP
- Check file size limits
- Verify file path is correct

### 4. Processing Timeout

**Issue**: `⏰ Timeout waiting for processing`

**Solution**:
- Check backend logs
- Verify file processing service is running normally
- Try using a smaller file

### 5. Evaluation Results 500 Error

**Issue**: `⚠️ Server error (500), retrying...`

**Solution**:
- This is a backend issue, the test script will automatically retry
- Check backend logs for specific errors
- Verify evaluation task completed correctly

### 6. Export File 409 Error

**Issue**: `⚠️ Export CSV: 409 Conflict`

**Solution**:
- This is expected behavior, indicating file is being generated
- Wait a few seconds and retry
- Or wait for evaluation task to fully complete before exporting

---

## Test Coverage Statistics

### Tested Endpoints (31 test functions)

#### Authentication (2)
- ✅ `POST /auth/login`
- ✅ `GET /auth/me`
- ⚠️ `POST /auth/logout` (implemented but not called in main)

#### File Upload (4)
- ✅ `POST /uploads/`
- ✅ `GET /uploads/{id}/status`
- ✅ `GET /uploads/{id}/download/{format}`
- ✅ `GET /uploads/recent`

#### Sentence Extraction (2)
- ✅ `POST /contracts/{id}/sentences/import`
- ✅ `GET /extract/{job_id}`

#### Prompt Lab (9)
- ✅ `GET /promptlab/models`
- ✅ `POST /promptlab/models/switch`
- ✅ `GET /promptlab/prompts`
- ✅ `POST /promptlab/explain/batch`
- ✅ `POST /promptlab/explain/one`
- ✅ `POST /promptlab/classify`
- ✅ `POST /promptlab/explain/file`
- ✅ `GET /promptlab/explain/file/status/{task_id}`
- ✅ `GET /promptlab/explain/file/result/{task_id}`

#### Evaluation Lab (5)
- ✅ `GET /eval-lab/config`
- ✅ `POST /eval-lab/upload`
- ✅ `POST /eval-lab/run`
- ✅ `GET /eval-lab/jobs/{id}/state`
- ✅ `GET /eval-lab/jobs/{id}/export.{format}`

#### Analytics API (8)
- ✅ `GET /contracts/stats`
- ✅ `GET /charts/trends`
- ✅ `GET /phrases/recurring`
- ✅ `GET /analytics/kpi`
- ✅ `GET /activity/recent`
- ✅ `GET /contracts`
- ✅ `GET /reports/data`
- ✅ `POST /reports/export`

#### Error Handling (5)
- ✅ `GET /healthcheck`
- ✅ 404 error tests
- ✅ 400 error tests
- ✅ 401 error tests
- ✅ 500 error tests

#### Boundary Conditions (4)
- ✅ Empty data handling
- ✅ Special character handling
- ✅ Large batch processing
- ✅ Pagination boundaries
=======
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
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98

---

## Expected Results

<<<<<<< HEAD
After completing the tests, you should see:

```
✅ Complete Workflow Test Finished!

📊 Test Summary:
   ✅ All API endpoints tested
   ✅ Error handling tested (404, 400, 401, 500)
   ✅ Boundary conditions tested (empty data, special chars, large batch, pagination)
   ✅ Normal workflow completed
```
=======
After completing all steps:
- ✅ Contract uploaded and processed
- ✅ Sentences extracted and stored
- ✅ Sentences classified (AMBIGUOUS/UNAMBIGUOUS)
- ✅ Evaluation results generated
- ✅ Analytics APIs showing non-zero ambiguity rates
>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98

---

## Notes

<<<<<<< HEAD
1. **Test Order**: Tests execute in a specific order, some tests depend on previous steps
2. **Async Tasks**: Prompt Lab file processing and Evaluation Lab evaluation are async, the script will automatically wait for completion
3. **Cleanup**: Test script automatically cleans up temporary files (e.g., `eval_input.csv`)
4. **Session Token**: All authenticated requests automatically use the session token obtained from login
5. **Timeout Handling**: All network requests have timeout settings to avoid infinite waiting
6. **Error Recovery**: Some errors won't cause the entire test to fail, the script will continue executing other tests

---

## Extending Tests

### Adding New Test Functions

1. Create a new function in `test_workflow.py`:

```python
def test_new_endpoint(session_token):
    """Test new endpoint"""
    print("\n🧪 Testing new endpoint...")
    cookies = {'session': session_token}
    response = requests.get(f"{BASE_URL}/new/endpoint", cookies=cookies, timeout=5)
    if response.status_code == 200:
        print("✅ New endpoint OK")
        return response.json()
    else:
        print(f"❌ New endpoint failed: {response.status_code}")
        return None
```

2. Call it in the `main()` function:

```python
test_new_endpoint(session_token)
```

---

## Related Files

- `test_workflow.py` - Main test script
- `run_test.bat` - Windows batch script
- `run_test.ps1` - PowerShell script
- `requirements.txt` - Python dependencies (requires `requests`)

---

## Changelog

- **2025-01-XX**: Added comprehensive error handling and timeout mechanisms
- **2025-01-XX**: Added Prompt Lab file processing tests
- **2025-01-XX**: Added boundary condition tests
- **2025-01-XX**: Added retry mechanisms and better error handling
=======
- Replace `YOUR_SESSION_TOKEN` with actual session cookie value
- Replace `YOUR_JOB_ID` with actual job ID from responses
- Contract IDs, Job IDs are examples - use actual values from responses
- Processing may take time depending on file size and model API latency

>>>>>>> ed771aba7f531cf9b42b6983f14a64843e17ac98
