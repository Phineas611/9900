import requests

url = "http://127.0.0.1:8000/api/eval-lab/upload"
files = {'file': open('test_eval_upload.csv', 'rb')}

response = requests.post(url, files=files)

print(response.json())