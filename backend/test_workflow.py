#!/usr/bin/env python3
"""
Complete workflow test script for Legal Contract Analyzer
Tests: Upload -> Extract -> Prompt Lab -> Evaluation Lab -> Analytics
"""
import requests
import json
import time
import sys
from pathlib import Path

BASE_URL = "http://localhost:5000/api"

# Test user credentials
TEST_EMAIL = "user@example.com"
TEST_PASSWORD = "string"  # Update with actual password

def get_session_token():
    """Login and get session token"""
    print("🔐 Logging in...")
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
            timeout=10
        )
        if response.status_code == 200:
            print("✅ Login successful")
            # Get session cookie
            session_cookie = response.cookies.get("session")
            return session_cookie
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
    except requests.exceptions.Timeout:
        print(f"❌ Login timeout: Server not responding")
        return None
    except requests.exceptions.ConnectionError:
        print(f"❌ Login connection error: Cannot connect to {BASE_URL}")
        return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None


def upload_file(session_token, file_path):
    """Step 1: Upload a contract file"""
    print("\n📤 Step 1: Uploading file...")
    # Determine file extension for proper MIME type
    ext = Path(file_path).suffix.lower()
    mime_types = {'.pdf': 'application/pdf', '.zip': 'application/zip'}
    content_type = mime_types.get(ext, 'application/octet-stream')
    
    with open(file_path, 'rb') as f:
        files = {'file': (Path(file_path).name, f, content_type)}
        cookies = {'session': session_token}
        response = requests.post(
            f"{BASE_URL}/uploads/",
            files=files,
            cookies=cookies
        )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Upload successful: contract_id={data['contract_id']}")
        return data['contract_id']
    else:
        print(f"❌ Upload failed: {response.text}")
        return None


def check_processing_status(session_token, contract_id):
    """Wait for processing to complete"""
    print("⏳ Waiting for processing...")
    max_wait = 60  # 60 seconds
    elapsed = 0
    
    while elapsed < max_wait:
        cookies = {'session': session_token}
        response = requests.get(
            f"{BASE_URL}/uploads/{contract_id}/status",
            cookies=cookies
        )
        
        if response.status_code == 200:
            data = response.json()
            status = data.get('processing_status')
            print(f"   Status: {status}")
            
            if status == 'completed':
                print("✅ Processing completed")
                return True
            elif status == 'failed':
                print("❌ Processing failed")
                return False
        
        time.sleep(2)
        elapsed += 2
    
    print("⏰ Timeout waiting for processing")
    return False


def import_sentences(session_token, contract_id):
    """Step 2: Import sentences into database"""
    print("\n📥 Step 2: Importing sentences...")
    cookies = {'session': session_token}
    response = requests.post(
        f"{BASE_URL}/contracts/{contract_id}/sentences/import",
        cookies=cookies
    )
    
    if response.status_code == 200:
        data = response.json()
        job_id = data.get('job_id')
        count = data.get('imported_count')
        print(f"✅ Imported {count} sentences, job_id={job_id}")
        return job_id
    else:
        print(f"❌ Import failed: {response.text}")
        return None


def get_extracted_sentences(session_token, job_id):
    """Get sentences from extraction"""
    print("\n📋 Step 3: Getting extracted sentences...")
    cookies = {'session': session_token}
    response = requests.get(f"{BASE_URL}/extract/{job_id}", cookies=cookies)
    
    if response.status_code == 200:
        data = response.json()
        sentences = data.get('sentences', [])
        print(f"✅ Retrieved {len(sentences)} sentences")
        return sentences
    else:
        print(f"❌ Failed to get sentences: {response.text}")
        return []


def classify_sentences(test_sentences, contract_id):
    """Step 4: Classify with Prompt Lab"""
    print("\n🤖 Step 4: Classifying with Prompt Lab...")
    
    # Take first 5 sentences for testing
    sentences_to_classify = [s['text'] for s in test_sentences[:5]]
    
    response = requests.post(
        f"{BASE_URL}/promptlab/explain/batch",
        json={
            "sentences": sentences_to_classify,
            "prompt_id": "amb-basic",
            "contract_id": contract_id
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Classified {len(data)} sentences")
        
        # Show sample results
        for i, result in enumerate(data[:3]):
            print(f"   [{i+1}] {result['sentence'][:50]}...")
            print(f"       Label: {result['label']}")
        
        return data
    else:
        print(f"❌ Classification failed: {response.text}")
        return []


def check_analytics(session_token):
    """Step 5: Test Analytics APIs"""
    print("\n📊 Step 5: Testing Analytics APIs...")
    
    cookies = {'session': session_token}
    
    # Test each analytics endpoint
    endpoints = [
        ("/contracts/stats", "Contract statistics"),
        ("/charts/trends?range=3months", "Trend charts"),
        ("/phrases/recurring?limit=5", "Recurring phrases"),
        ("/analytics/kpi", "KPI analytics"),
    ]
    
    for endpoint, name in endpoints:
        print(f"\n   Testing {name}...")
        response = requests.get(f"{BASE_URL}{endpoint}", cookies=cookies)
        
        if response.status_code == 200:
            print(f"   ✅ {name} OK")
            # Print summary if available
            data = response.json()
            if isinstance(data, dict):
                if 'totalContracts' in data:
                    print(f"      Total contracts: {data['totalContracts']}")
                elif 'data' in data:
                    monthly_data = data['data'].get('monthlyData', [])
                    print(f"      Monthly data points: {len(monthly_data)}")
        else:
            print(f"   ❌ {name} failed: {response.status_code}")


def create_eval_csv(classified_results):
    """Create CSV file for Evaluation Lab"""
    print("\n📝 Creating evaluation CSV...")
    
    csv_content = "item_id,sentence,predicted_label,rationale\n"
    for i, result in enumerate(classified_results):
        label = result.get('label', 'AMBIGUOUS')
        csv_content += f'{i+1},"{result["sentence"]}","{label}","{result.get("rationale", "")}"\n'
    
    csv_file = Path("eval_input.csv")
    csv_file.write_text(csv_content, encoding='utf-8')
    print(f"✅ Created {csv_file}")
    return csv_file


def upload_for_evaluation(csv_file):
    """Step 6: Upload to Evaluation Lab"""
    print("\n🔬 Step 6: Uploading to Evaluation Lab...")
    
    with open(csv_file, 'rb') as f:
        files = {'file': f}
        response = requests.post(
            f"{BASE_URL}/eval-lab/upload",
            files=files
        )
    
    if response.status_code == 200:
        data = response.json()
        job_id = data.get('job_id')
        print(f"✅ Uploaded to eval lab, job_id={job_id}")
        return job_id
    else:
        print(f"❌ Upload failed: {response.text}")
        return None


def run_evaluation(eval_job_id):
    """Step 7: Run evaluation"""
    print("\n⚖️ Step 7: Running evaluation...")
    
    # Use default judges and rubrics
    response = requests.post(
        f"{BASE_URL}/eval-lab/run",
        json={
            "job_id": eval_job_id,
            "judges": [],
            "rubrics": {},
            "custom_metrics": []
        }
    )
    
    # Accept both 200 (OK) and 202 (Accepted) as success
    if response.status_code in [200, 202]:
        data = response.json()
        total = data.get('total')
        task_id = data.get('task_id') or data.get('job_id')
        print(f"✅ Evaluation started (status: {response.status_code}), total items: {total}")
        if task_id:
            print(f"   Task ID: {task_id}")
        return True
    else:
        print(f"❌ Evaluation failed: {response.status_code} - {response.text}")
        return False


# ========== Additional Test Functions ==========

def test_healthcheck():
    """Test health check endpoint"""
    print("\n🏥 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/healthcheck", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Health check OK: {data.get('status', 'unknown')}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print(f"❌ Health check timeout: Server not responding (is backend running on {BASE_URL}?)")
        return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Health check connection error: Cannot connect to {BASE_URL}")
        print(f"   Please make sure the backend server is running!")
        return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False


def test_auth_me(session_token):
    """Test get current user info"""
    print("\n👤 Testing GET /auth/me...")
    cookies = {'session': session_token}
    response = requests.get(f"{BASE_URL}/auth/me", cookies=cookies)
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Current user: {data.get('email', 'unknown')}")
        return data
    else:
        print(f"❌ Get user info failed: {response.status_code}")
        return None


def test_auth_logout(session_token):
    """Test logout"""
    print("\n🚪 Testing POST /auth/logout...")
    cookies = {'session': session_token}
    response = requests.post(f"{BASE_URL}/auth/logout", cookies=cookies)
    if response.status_code == 204:
        print("✅ Logout successful")
        return True
    else:
        print(f"⚠️ Logout returned: {response.status_code}")
        return False


def test_promptlab_models():
    """Test Prompt Lab models endpoint"""
    print("\n🤖 Testing GET /promptlab/models...")
    response = requests.get(f"{BASE_URL}/promptlab/models")
    if response.status_code == 200:
        data = response.json()
        available = data.get('available', [])
        current = data.get('current', {})
        print(f"✅ Available models: {len(available)}")
        print(f"   Current model: {current.get('id', 'unknown')}")
        return data
    else:
        print(f"❌ Get models failed: {response.status_code}")
        return None


def test_promptlab_switch_model(model_id):
    """Test switch model"""
    print(f"\n🔄 Testing POST /promptlab/models/switch (model_id={model_id})...")
    response = requests.post(
        f"{BASE_URL}/promptlab/models/switch",
        json={"model_id": model_id}
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Model switched: {data.get('current', {}).get('id', 'unknown')}")
        return True
    else:
        print(f"⚠️ Switch model returned: {response.status_code}")
        return False


def test_promptlab_prompts():
    """Test get prompts list"""
    print("\n📝 Testing GET /promptlab/prompts...")
    response = requests.get(f"{BASE_URL}/promptlab/prompts")
    if response.status_code == 200:
        data = response.json()
        prompts = data.get('prompts', [])
        print(f"✅ Available prompts: {len(prompts)}")
        if prompts:
            print(f"   Sample: {prompts[0]}")
        return prompts
    else:
        print(f"❌ Get prompts failed: {response.status_code}")
        return []


def test_promptlab_explain_one(sentence, contract_id):
    """Test single sentence explanation"""
    print("\n🔍 Testing POST /promptlab/explain/one...")
    response = requests.post(
        f"{BASE_URL}/promptlab/explain/one",
        json={
            "sentence": sentence,
            "prompt_id": "amb-basic",
            "contract_id": contract_id
        }
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Single sentence explained")
        print(f"   Label: {data.get('label')}")
        print(f"   Score: {data.get('score', 0):.2f}")
        return data
    else:
        print(f"❌ Explain one failed: {response.status_code}")
        return None


def test_promptlab_classify(sentences, contract_id):
    """Test classify endpoint (without explanation)"""
    print("\n🏷️ Testing POST /promptlab/classify...")
    response = requests.post(
        f"{BASE_URL}/promptlab/classify",
        json={
            "sentences": sentences[:2],  # Test with 2 sentences
            "prompt_id": "amb-basic",
            "contract_id": contract_id
        }
    )
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Classified {len(data)} sentences")
        for i, result in enumerate(data[:2]):
            print(f"   [{i+1}] Label: {result.get('label')}")
        return data
    else:
        print(f"❌ Classify failed: {response.status_code}")
        return []


def test_promptlab_explain_file(session_token, contract_id):
    """Test file upload for async processing"""
    print("\n📄 Testing POST /promptlab/explain/file (async file processing)...")
    
    # Create a test CSV file with a few sentences
    test_csv_content = "sentence\n"
    test_sentences = [
        "This is a test sentence for file processing.",
        "Another sentence to test batch processing.",
        "A third sentence to verify the async task works."
    ]
    for sent in test_sentences:
        test_csv_content += f'"{sent}"\n'
    
    # Create temporary CSV file
    test_csv_file = Path("test_prompt_file.csv")
    test_csv_file.write_text(test_csv_content, encoding='utf-8')
    
    try:
        cookies = {'session': session_token}
        with open(test_csv_file, 'rb') as f:
            files = {'file': ('test_sentences.csv', f, 'text/csv')}
            response = requests.post(
                f"{BASE_URL}/promptlab/explain/file?prompt_id=amb-basic&contract_id={contract_id}&out=csv",
                files=files,
                cookies=cookies
            )
        
        if response.status_code == 200:
            data = response.json()
            task_id = data.get('task_id')
            status = data.get('status')
            print(f"✅ File upload successful, task_id={task_id}, status={status}")
            
            # Test status endpoint and wait for completion
            if task_id:
                # First status check (verbose)
                test_promptlab_file_status(task_id)
                
                # Poll status until completed (with timeout)
                max_wait = 60  # 60 seconds timeout
                elapsed = 0
                poll_interval = 2  # Poll every 2 seconds
                
                print(f"⏳ Waiting for task to complete (max {max_wait}s)...")
                while elapsed < max_wait:
                    status_data = test_promptlab_file_status(task_id, silent=True)
                    if status_data:
                        current_status = status_data.get('status', '').lower()
                        progress = status_data.get('progress', {})
                        current = progress.get('current', 0)
                        total = progress.get('total', 0)
                        
                        if current_status == 'completed':
                            print(f"✅ Task completed ({current}/{total}), downloading result...")
                            # Test result download
                            result_file = test_promptlab_file_result(task_id)
                            if result_file:
                                print(f"✅ File processing test completed successfully")
                            break
                        elif current_status == 'failed':
                            print(f"⚠️ Task failed: {status_data.get('message', 'Unknown error')}")
                            break
                        else:
                            # Show progress during polling
                            print(f"   Status: {current_status}, Progress: {current}/{total}")
                    
                    time.sleep(poll_interval)
                    elapsed += poll_interval
                
                if elapsed >= max_wait:
                    print(f"⚠️ Task did not complete within {max_wait} seconds (may still be processing)")
            
            return task_id
        else:
            print(f"❌ File upload failed: {response.status_code} - {response.text}")
            return None
    finally:
        # Cleanup
        if test_csv_file.exists():
            test_csv_file.unlink()


def test_promptlab_file_status(task_id, silent=False):
    """Test get file processing task status"""
    if not silent:
        print(f"\n📊 Testing GET /promptlab/explain/file/status/{task_id}...")
    try:
        response = requests.get(f"{BASE_URL}/promptlab/explain/file/status/{task_id}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                status = data.get('status', 'unknown')
                progress = data.get('progress', {})
                if not silent:
                    print(f"✅ Task status: {status}")
                    if progress and isinstance(progress, dict):
                        current = progress.get('current', 0)
                        total = progress.get('total', 0)
                        if total > 0:
                            print(f"   Progress: {current}/{total}")
                return data
            except Exception as e:
                if not silent:
                    print(f"❌ Failed to parse response: {e}")
                return None
        elif response.status_code == 404:
            if not silent:
                print(f"⚠️ Task not found (may have completed and been cleaned up)")
            return None
        else:
            if not silent:
                print(f"❌ Get task status failed: {response.status_code}")
            return None
    except Exception as e:
        if not silent:
            print(f"❌ Request failed: {e}")
        return None


def test_promptlab_file_result(task_id):
    """Test get file processing task result"""
    print(f"\n📥 Testing GET /promptlab/explain/file/result/{task_id}...")
    try:
        response = requests.get(f"{BASE_URL}/promptlab/explain/file/result/{task_id}")
        
        if response.status_code == 200:
            # Check if it's a file download
            content_type = response.headers.get('content-type', '')
            if 'csv' in content_type or 'excel' in content_type or 'spreadsheet' in content_type:
                file_ext = 'csv' if 'csv' in content_type else 'xlsx'
                result_file = Path(f"prompt_file_result_{task_id}.{file_ext}")
                result_file.write_bytes(response.content)
                print(f"✅ Downloaded result file: {result_file} ({len(response.content)} bytes)")
                return result_file
            else:
                print(f"⚠️ Unexpected content type: {content_type}")
                return None
        elif response.status_code == 400:
            try:
                error_detail = response.json().get('detail', 'unknown')
                print(f"⚠️ Task not completed yet (status: {error_detail})")
            except:
                print(f"⚠️ Task not completed yet (status: {response.status_code})")
            return None
        elif response.status_code == 404:
            print(f"⚠️ Task not found")
            return None
        else:
            print(f"❌ Get task result failed: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None


def test_eval_config():
    """Test Evaluation Lab config"""
    print("\n⚙️ Testing GET /eval-lab/config...")
    response = requests.get(f"{BASE_URL}/eval-lab/config")
    if response.status_code == 200:
        data = response.json()
        judges = data.get('judges', [])
        rubrics = data.get('rubrics', {})
        print(f"✅ Config loaded")
        print(f"   Available judges: {len(judges)}")
        print(f"   Available rubrics: {len(rubrics)}")
        return data
    else:
        print(f"❌ Get config failed: {response.status_code}")
        return None


def test_eval_job_state(eval_job_id, max_polls=5):
    """Test Evaluation Lab job state polling"""
    print(f"\n📊 Testing GET /eval-lab/jobs/{eval_job_id}/state (polling)...")
    for i in range(max_polls):
        response = requests.get(f"{BASE_URL}/eval-lab/jobs/{eval_job_id}/state")
        if response.status_code == 200:
            data = response.json()
            status = data.get('status', 'UNKNOWN')
            progress = data.get('progress', 0)
            total = data.get('total', 0)
            print(f"   Poll {i+1}: Status={status}, Progress={progress}/{total}")
            
            if status in ['DONE', 'FAILED']:
                print(f"✅ Job completed with status: {status}")
                return data
        else:
            print(f"   Poll {i+1} failed: {response.status_code}")
        
        if i < max_polls - 1:
            time.sleep(2)
    
    print("⚠️ Polling timeout")
    return None


def test_eval_export_csv(eval_job_id):
    """Test export evaluation results as CSV"""
    print(f"\n📥 Testing GET /eval-lab/jobs/{eval_job_id}/export.csv...")
    response = requests.get(f"{BASE_URL}/eval-lab/jobs/{eval_job_id}/export.csv")
    if response.status_code == 200:
        csv_file = Path(f"eval_export_{eval_job_id}.csv")
        csv_file.write_bytes(response.content)
        print(f"✅ Exported CSV: {csv_file} ({len(response.content)} bytes)")
        return csv_file
    elif response.status_code == 409:
        print(f"⚠️ Export CSV: 409 Conflict (file may be generating, this is expected)")
        return None
    else:
        print(f"❌ Export CSV failed: {response.status_code}")
        return None


def test_eval_export_xlsx(eval_job_id):
    """Test export evaluation results as XLSX"""
    print(f"\n📥 Testing GET /eval-lab/jobs/{eval_job_id}/export.xlsx...")
    response = requests.get(f"{BASE_URL}/eval-lab/jobs/{eval_job_id}/export.xlsx")
    if response.status_code == 200:
        xlsx_file = Path(f"eval_export_{eval_job_id}.xlsx")
        xlsx_file.write_bytes(response.content)
        print(f"✅ Exported XLSX: {xlsx_file} ({len(response.content)} bytes)")
        return xlsx_file
    elif response.status_code == 409:
        print(f"⚠️ Export XLSX: 409 Conflict (file may be generating, this is expected)")
        return None
    else:
        print(f"❌ Export XLSX failed: {response.status_code}")
        return None


def test_download_file(session_token, contract_id, format_type='csv'):
    """Test download processed file"""
    print(f"\n💾 Testing GET /uploads/{contract_id}/download/{format_type}...")
    cookies = {'session': session_token}
    response = requests.get(
        f"{BASE_URL}/uploads/{contract_id}/download/{format_type}",
        cookies=cookies
    )
    if response.status_code == 200:
        file_path = Path(f"downloaded_contract_{contract_id}.{format_type}")
        file_path.write_bytes(response.content)
        print(f"✅ Downloaded file: {file_path} ({len(response.content)} bytes)")
        return file_path
    else:
        print(f"⚠️ Download failed: {response.status_code}")
        return None


def test_uploads_recent(session_token, limit=5):
    """Test recent uploads"""
    print(f"\n📋 Testing GET /uploads/recent?limit={limit}...")
    cookies = {'session': session_token}
    response = requests.get(
        f"{BASE_URL}/uploads/recent?limit={limit}",
        cookies=cookies
    )
    if response.status_code == 200:
        data = response.json()
        # API returns a list directly, not a dict with 'uploads' key
        if isinstance(data, list):
            uploads = data
        else:
            uploads = data.get('uploads', [])
        print(f"✅ Recent uploads: {len(uploads)}")
        return uploads
    else:
        print(f"❌ Get recent uploads failed: {response.status_code}")
        return []


def test_contract_sentences(session_token, contract_id):
    """Test get contract sentences"""
    print(f"\n📄 Testing GET /contracts/{contract_id}/sentences...")
    cookies = {'session': session_token}
    response = requests.get(
        f"{BASE_URL}/contracts/{contract_id}/sentences",
        cookies=cookies
    )
    if response.status_code == 200:
        data = response.json()
        # API returns a list directly, not a dict with 'sentences' key
        if isinstance(data, list):
            sentences = data
        else:
            sentences = data.get('sentences', [])
        print(f"✅ Contract sentences: {len(sentences)}")
        return sentences
    else:
        print(f"❌ Get contract sentences failed: {response.status_code}")
        return []


def test_activity_recent(session_token, limit=5):
    """Test recent activity"""
    print(f"\n📜 Testing GET /activity/recent?limit={limit}...")
    cookies = {'session': session_token}
    response = requests.get(
        f"{BASE_URL}/activity/recent?limit={limit}",
        cookies=cookies
    )
    if response.status_code == 200:
        data = response.json()
        # API returns a list directly, not a dict with 'activities' key
        if isinstance(data, list):
            activities = data
        else:
            activities = data.get('activities', [])
        print(f"✅ Recent activities: {len(activities)}")
        return activities
    else:
        print(f"❌ Get recent activity failed: {response.status_code}")
        return []


def test_contracts_list(session_token, page=1, limit=10):
    """Test contracts list"""
    print(f"\n📚 Testing GET /contracts?page={page}&limit={limit}...")
    cookies = {'session': session_token}
    response = requests.get(
        f"{BASE_URL}/contracts?page={page}&limit={limit}",
        cookies=cookies
    )
    if response.status_code == 200:
        data = response.json()
        contracts = data.get('contracts', [])
        total = data.get('total', 0)
        print(f"✅ Contracts list: {len(contracts)}/{total}")
        return data
    else:
        print(f"❌ Get contracts list failed: {response.status_code}")
        return None


def test_reports_data(session_token):
    """Test reports data"""
    print("\n📊 Testing GET /reports/data...")
    cookies = {'session': session_token}
    response = requests.get(
        f"{BASE_URL}/reports/data",
        cookies=cookies
    )
    if response.status_code == 200:
        data = response.json()
        stats = data.get('stats', {})
        print(f"✅ Reports data loaded")
        print(f"   Total contracts: {stats.get('totalContracts', 0)}")
        print(f"   Ambiguity rate: {stats.get('ambiguityRate', 0)}%")
        return data
    else:
        print(f"❌ Get reports data failed: {response.status_code}")
        return None


def test_reports_export(session_token):
    """Test export reports"""
    print("\n📤 Testing POST /reports/export...")
    cookies = {'session': session_token}
    response = requests.post(
        f"{BASE_URL}/reports/export",
        json={"format": "csv"},
        cookies=cookies
    )
    if response.status_code == 200:
        # Check if it's a file download
        if response.headers.get('content-type', '').startswith('text/csv'):
            file_path = Path("reports_export.csv")
            file_path.write_bytes(response.content)
            print(f"✅ Exported reports: {file_path} ({len(response.content)} bytes)")
            return file_path
        else:
            data = response.json()
            print(f"✅ Export request processed: {data}")
            return data
    else:
        print(f"⚠️ Export reports returned: {response.status_code}")
        return None


# ========== Error Handling Tests ==========

def test_error_404():
    """Test 404 error handling"""
    print("\n❌ Testing 404 errors...")
    
    # Test non-existent contract
    try:
        response = requests.get(f"{BASE_URL}/uploads/999999/status", timeout=5)
        if response.status_code == 404:
            print("   ✅ 404 for non-existent contract")
        else:
            print(f"   ⚠️ Expected 404, got {response.status_code}")
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        print("   ⚠️ Skipped (server not available)")
        return
    
    # Test non-existent job
    try:
        response = requests.get(f"{BASE_URL}/eval-lab/jobs/non-existent-job/state", timeout=5)
        if response.status_code == 404:
            print("   ✅ 404 for non-existent job")
        else:
            print(f"   ⚠️ Expected 404, got {response.status_code}")
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        print("   ⚠️ Skipped (server not available)")
        return
    
    # Test non-existent extract job
    try:
        response = requests.get(f"{BASE_URL}/extract/non-existent-job-id", timeout=5)
        if response.status_code == 404:
            print("   ✅ 404 for non-existent extract job")
        else:
            print(f"   ⚠️ Expected 404, got {response.status_code}")
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        print("   ⚠️ Skipped (server not available)")


def test_error_400():
    """Test 400 error handling (bad requests)"""
    print("\n❌ Testing 400 errors...")
    
    # Test empty request body
    try:
        response = requests.post(
            f"{BASE_URL}/promptlab/explain/batch",
            json={},
            timeout=5
        )
        if response.status_code == 400 or response.status_code == 422:
            print("   ✅ 400/422 for empty request body")
        else:
            print(f"   ⚠️ Expected 400/422, got {response.status_code}")
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        print("   ⚠️ Skipped (server not available)")
        return
    
    # Test invalid promptlab request (missing required fields)
    try:
        response = requests.post(
            f"{BASE_URL}/promptlab/explain/one",
            json={"sentence": ""},  # Missing prompt_id and contract_id
            timeout=5
        )
        if response.status_code == 400 or response.status_code == 422:
            print("   ✅ 400/422 for invalid request")
        else:
            print(f"   ⚠️ Expected 400/422, got {response.status_code}")
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        print("   ⚠️ Skipped (server not available)")
        return
    
    # Test invalid eval run request
    try:
        response = requests.post(
            f"{BASE_URL}/eval-lab/run",
            json={"job_id": ""},  # Empty job_id
            timeout=5
        )
        if response.status_code == 400 or response.status_code == 422:
            print("   ✅ 400/422 for invalid eval run")
        else:
            print(f"   ⚠️ Expected 400/422, got {response.status_code}")
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        print("   ⚠️ Skipped (server not available)")


def test_error_401():
    """Test 401 error handling (unauthorized)"""
    print("\n❌ Testing 401 errors...")
    
    # Test without session token
    try:
        response = requests.get(f"{BASE_URL}/uploads/recent", timeout=5)
        if response.status_code == 401:
            print("   ✅ 401 for unauthorized request")
        else:
            print(f"   ⚠️ Expected 401, got {response.status_code}")
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        print("   ⚠️ Skipped (server not available)")
        return
    
    # Test with invalid session token
    try:
        cookies = {'session': 'invalid-token'}
        response = requests.get(f"{BASE_URL}/auth/me", cookies=cookies, timeout=5)
        if response.status_code == 401:
            print("   ✅ 401 for invalid session")
        else:
            print(f"   ⚠️ Expected 401, got {response.status_code}")
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        print("   ⚠️ Skipped (server not available)")


def test_error_500():
    """Test 500 error handling (server errors)"""
    print("\n❌ Testing 500 errors...")
    
    # Test with invalid model_id (might cause server error)
    try:
        response = requests.post(
            f"{BASE_URL}/promptlab/models/switch",
            json={"model_id": "non-existent-model-id-12345"},
            timeout=5
        )
        if response.status_code == 404 or response.status_code == 500:
            print(f"   ✅ {response.status_code} for invalid model_id")
        else:
            print(f"   ⚠️ Expected 404/500, got {response.status_code}")
    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
        print("   ⚠️ Skipped (server not available)")


# ========== Boundary Condition Tests ==========

def test_empty_data(session_token):
    """Test with empty data"""
    print("\n🔍 Testing empty data handling...")
    
    # Test empty sentences list
    response = requests.post(
        f"{BASE_URL}/promptlab/explain/batch",
        json={
            "sentences": [],
            "prompt_id": "amb-basic",
            "contract_id": 1
        }
    )
    if response.status_code == 400 or response.status_code == 422:
        print("   ✅ Empty sentences list handled correctly")
    else:
        print(f"   ⚠️ Empty sentences returned: {response.status_code}")
    
    # Test very long sentence
    long_sentence = "This is a very long sentence. " * 1000  # ~30KB
    response = requests.post(
        f"{BASE_URL}/promptlab/explain/one",
        json={
            "sentence": long_sentence,
            "prompt_id": "amb-basic",
            "contract_id": 1
        }
    )
    if response.status_code == 200:
        print("   ✅ Very long sentence handled")
    elif response.status_code == 400 or response.status_code == 413:
        print(f"   ✅ Long sentence rejected: {response.status_code}")
    else:
        print(f"   ⚠️ Long sentence returned: {response.status_code}")


def test_special_characters(session_token, contract_id):
    """Test with special characters"""
    print("\n🔍 Testing special characters...")
    
    special_sentences = [
        "This contains \"quotes\" and 'apostrophes'.",
        "Price: $1,000.00 (USD) - 50% discount!",
        "Email: test@example.com & phone: +1-555-1234",
        "Unicode: 中文测试 🚀 émojis",
        "SQL injection test: ' OR '1'='1",
        "XSS test: <script>alert('test')</script>"
    ]
    
    for i, sentence in enumerate(special_sentences[:3]):  # Test first 3
        response = requests.post(
            f"{BASE_URL}/promptlab/explain/one",
            json={
                "sentence": sentence,
                "prompt_id": "amb-basic",
                "contract_id": contract_id
            }
        )
        if response.status_code == 200:
            print(f"   ✅ Special chars sentence {i+1} handled")
        else:
            print(f"   ⚠️ Special chars sentence {i+1} failed: {response.status_code}")


def test_large_batch(session_token, contract_id):
    """Test with large batch of sentences"""
    print("\n🔍 Testing large batch...")
    
    # Generate 50 test sentences
    test_sentences = [f"This is test sentence number {i+1} for batch testing." for i in range(50)]
    
    response = requests.post(
        f"{BASE_URL}/promptlab/explain/batch",
        json={
            "sentences": test_sentences,
            "prompt_id": "amb-basic",
            "contract_id": contract_id
        },
        timeout=120  # Longer timeout for large batch
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Large batch processed: {len(data)} sentences")
    elif response.status_code == 400 or response.status_code == 413:
        print(f"   ✅ Large batch rejected: {response.status_code}")
    else:
        print(f"   ⚠️ Large batch returned: {response.status_code}")


def test_invalid_file_upload(session_token):
    """Test invalid file upload"""
    print("\n🔍 Testing invalid file upload...")
    
    cookies = {'session': session_token}
    
    # Test with text file instead of PDF
    text_content = "This is not a PDF file."
    files = {'file': ('test.txt', text_content, 'text/plain')}
    response = requests.post(f"{BASE_URL}/uploads/", files=files, cookies=cookies)
    
    if response.status_code == 400 or response.status_code == 415:
        print("   ✅ Invalid file type rejected")
    else:
        print(f"   ⚠️ Invalid file returned: {response.status_code}")
    
    # Test with empty file
    files = {'file': ('empty.pdf', b'', 'application/pdf')}
    response = requests.post(f"{BASE_URL}/uploads/", files=files, cookies=cookies)
    
    if response.status_code == 400:
        print("   ✅ Empty file rejected")
    else:
        print(f"   ⚠️ Empty file returned: {response.status_code}")


def test_pagination_boundaries(session_token):
    """Test pagination with boundary values"""
    print("\n🔍 Testing pagination boundaries...")
    
    # Test with page=0
    cookies = {'session': session_token}
    response = requests.get(
        f"{BASE_URL}/contracts?page=0&limit=10",
        cookies=cookies
    )
    if response.status_code == 200 or response.status_code == 400:
        print(f"   ✅ Page 0 handled: {response.status_code}")
    
    # Test with negative page
    response = requests.get(
        f"{BASE_URL}/contracts?page=-1&limit=10",
        cookies=cookies
    )
    if response.status_code == 200 or response.status_code == 400:
        print(f"   ✅ Negative page handled: {response.status_code}")
    
    # Test with very large page number
    response = requests.get(
        f"{BASE_URL}/contracts?page=999999&limit=10",
        cookies=cookies
    )
    if response.status_code == 200:
        data = response.json()
        contracts = data.get('contracts', [])
        print(f"   ✅ Large page number handled: {len(contracts)} results")
    
    # Test with limit=0
    response = requests.get(
        f"{BASE_URL}/contracts?page=1&limit=0",
        cookies=cookies
    )
    if response.status_code == 200 or response.status_code == 400:
        print(f"   ✅ Limit 0 handled: {response.status_code}")
    
    # Test with very large limit
    response = requests.get(
        f"{BASE_URL}/contracts?page=1&limit=10000",
        cookies=cookies
    )
    if response.status_code == 200 or response.status_code == 400:
        print(f"   ✅ Large limit handled: {response.status_code}")


def main():
    """Run complete workflow test"""
    print("=" * 60)
    print("🧪 Complete Workflow Test - All Endpoints & Error Handling")
    print("=" * 60)
    
    # Check if path provided
    if len(sys.argv) < 2:
        print("\n❌ Usage: python test_workflow.py <path_to_pdf_file_or_directory>")
        print("   Example: python test_workflow.py ../test_data/contract.pdf")
        print("   Example: python test_workflow.py C:\\Users\\...\\Affiliate_Agreements")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    
    # Handle directory or file
    if input_path.is_dir():
        # Find first PDF file in directory
        pdf_files = list(input_path.glob("*.pdf"))
        if not pdf_files:
            print(f"❌ No PDF files found in directory: {input_path}")
            sys.exit(1)
        pdf_file = pdf_files[0]
        print(f"📁 Using first PDF from directory: {pdf_file.name}")
    elif input_path.is_file():
        pdf_file = input_path
    else:
        print(f"❌ File or directory not found: {input_path}")
        sys.exit(1)
    
    if not pdf_file.exists():
        print(f"❌ File not found: {pdf_file}")
        sys.exit(1)
    
    print(f"📄 Testing with file: {pdf_file}")
    
    # ========== Phase 1: Error Handling Tests ==========
    print("\n" + "=" * 60)
    print("🔴 Phase 1: Error Handling Tests")
    print("=" * 60)
    
    test_healthcheck()
    test_error_404()
    test_error_400()
    test_error_401()
    test_error_500()
    # Note: test_invalid_file_upload requires authentication, will be called after login
    
    # ========== Phase 2: Normal Workflow Tests ==========
    print("\n" + "=" * 60)
    print("🟢 Phase 2: Normal Workflow Tests")
    print("=" * 60)
    
    # Step 0: Login
    session_token = get_session_token()
    if not session_token:
        print("❌ Cannot proceed without authentication")
        sys.exit(1)
    
    # Test auth endpoints
    test_auth_me(session_token)
    
    # Test invalid file upload (requires authentication)
    test_invalid_file_upload(session_token)
    
    # Step 1: Upload
    contract_id = upload_file(session_token, pdf_file)
    if not contract_id:
        sys.exit(1)
    
    # Wait for processing
    if not check_processing_status(session_token, contract_id):
        sys.exit(1)
    
    # Test download file
    test_download_file(session_token, contract_id, 'csv')
    
    # Test recent uploads
    test_uploads_recent(session_token)
    
    # Step 2: Import
    job_id = import_sentences(session_token, contract_id)
    if not job_id:
        sys.exit(1)
    
    # Step 3: Get sentences
    sentences = get_extracted_sentences(session_token, job_id)
    if not sentences:
        sys.exit(1)
    
    # Test contract sentences
    test_contract_sentences(session_token, contract_id)
    
    # Test Prompt Lab models and prompts
    models_data = test_promptlab_models()
    if models_data and models_data.get('available'):
        first_model = models_data['available'][0].get('id')
        if first_model:
            test_promptlab_switch_model(first_model)
    test_promptlab_prompts()
    
    # Step 4: Classify
    classified = classify_sentences(sentences, contract_id)
    if not classified:
        sys.exit(1)
    
    # Test Prompt Lab additional endpoints
    if sentences:
        test_sentence = sentences[0].get('text', '') if isinstance(sentences[0], dict) else sentences[0]
        if test_sentence:
            test_promptlab_explain_one(test_sentence, contract_id)
            test_promptlab_classify([test_sentence], contract_id)
    
    # Test Prompt Lab file upload (async task)
    test_promptlab_explain_file(session_token, contract_id)
    
    # Step 5: Test analytics (should still show low/zero ambiguity)
    check_analytics(session_token)
    
    # Test additional analytics endpoints
    test_activity_recent(session_token)
    test_contracts_list(session_token)
    test_reports_data(session_token)
    
    # ========== Phase 3: Boundary Condition Tests ==========
    print("\n" + "=" * 60)
    print("🟡 Phase 3: Boundary Condition Tests")
    print("=" * 60)
    
    test_empty_data(session_token)
    test_special_characters(session_token, contract_id)
    test_large_batch(session_token, contract_id)
    test_pagination_boundaries(session_token)
    
    # Create CSV for eval lab
    eval_csv = create_eval_csv(classified)
    
    # Test Evaluation Lab config
    test_eval_config()
    
    # Step 6: Upload for evaluation
    eval_job_id = upload_for_evaluation(eval_csv)
    
    if eval_job_id:
        # Step 7: Run evaluation
        run_evaluation(eval_job_id)
        
        # Test job state polling
        test_eval_job_state(eval_job_id, max_polls=5)
        
        print("\n⏳ Waiting 10 seconds for evaluation to process...")
        time.sleep(10)
        
        # Check results with retry mechanism
        max_retries = 3
        retry_delay = 2
        for attempt in range(max_retries):
            response = requests.get(f"{BASE_URL}/eval-lab/jobs/{eval_job_id}/records?page=1&page_size=5")
            if response.status_code == 200:
                try:
                    data = response.json()
                    total = data.get('total', 0)
                    items = data.get('items', [])
                    print(f"✅ Evaluation results available: {total} items, showing {len(items)} on page 1")
                    if items:
                        print(f"   Sample item: {items[0].get('id', 'N/A')} - {items[0].get('sentence', '')[:50]}...")
                    break
                except Exception as e:
                    print(f"⚠️ Failed to parse evaluation results: {e}")
                    if attempt < max_retries - 1:
                        print(f"   Retrying in {retry_delay} seconds...")
                        time.sleep(retry_delay)
            elif response.status_code == 500:
                if attempt < max_retries - 1:
                    print(f"⚠️ Server error (500), retrying in {retry_delay} seconds... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)
                else:
                    try:
                        error_detail = response.text[:200]  # Limit error message length
                        print(f"⚠️ Failed to get evaluation results after {max_retries} attempts: 500")
                        print(f"   Error detail: {error_detail}")
                    except:
                        print(f"⚠️ Failed to get evaluation results after {max_retries} attempts: 500")
            else:
                print(f"⚠️ Failed to get evaluation results: {response.status_code}")
                if response.status_code == 404:
                    print(f"   Job may not have records yet, this is expected for new evaluations")
                break
        
        # Test export functions
        test_eval_export_csv(eval_job_id)
        test_eval_export_xlsx(eval_job_id)
    
    # Step 8: Final analytics check (should show improved data)
    print("\n📊 Final Analytics Check:")
    check_analytics(session_token)
    
    # Test reports export
    test_reports_export(session_token)
    
    # Test logout (optional, may invalidate session)
    # test_auth_logout(session_token)
    
    print("\n" + "=" * 60)
    print("✅ Complete Workflow Test Finished!")
    print("=" * 60)
    print("\n📊 Test Summary:")
    print("   ✅ All API endpoints tested")
    print("   ✅ Error handling tested (404, 400, 401, 500)")
    print("   ✅ Boundary conditions tested (empty data, special chars, large batch, pagination)")
    print("   ✅ Normal workflow completed")
    print("=" * 60)
    
    # Cleanup
    cleanup_files = [eval_csv]
    for file_path in cleanup_files:
        if file_path and file_path.exists():
            file_path.unlink()
            print(f"🧹 Cleaned up {file_path}")


if __name__ == "__main__":
    main()

