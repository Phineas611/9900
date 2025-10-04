from fastapi import FastAPI, UploadFile, File
from pathlib import Path

app = FastAPI()

# 本地存储目录
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@app.post("/api/upload")
async def upload_file(files: list[UploadFile] = File(...)):
    saved_files = []
    for f in files:
        file_path = UPLOAD_DIR / f.filename
        with open(file_path, "wb") as buffer:
            buffer.write(await f.read())
        saved_files.append(f.filename)
    return {"message": "Upload successful", "files": saved_files}