# Smoke Test

1) Start the API:
```
python -m app.main --serve --host 0.0.0.0 --port 5001
```
2) In another terminal, POST two files:
```
curl -X POST "http://localhost:5001/api/extract?out=./outputs" \
  -F "files=@/path/to/contract1.pdf" \
  -F "files=@/path/to/contract2.docx"
```
3) Check `./outputs/sentences.csv`.
