# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, glob
from pathlib import Path
from typing import List
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename

from .extractor.pipeline import process_files
from .extractor.utils import ensure_dir

ALLOWED_EXTENSIONS = {"pdf", "docx"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok"})

    @app.route("/api/extract", methods=["POST"])
    def extract():
        out_dir = request.args.get("out", default="./outputs")
        out_path = Path(out_dir)
        ensure_dir(out_path)

        if "files" not in request.files:
            return jsonify({"error": "No 'files' field in form-data"}), 400

        file_storages = request.files.getlist("files")
        saved_paths: List[Path] = []
        upload_dir = Path("./uploaded")
        ensure_dir(upload_dir)

        for fs in file_storages:
            fname = secure_filename(fs.filename or "")
            if not fname or not allowed_file(fname):
                continue
            p = upload_dir / fname
            fs.save(str(p))
            saved_paths.append(p)

        if not saved_paths:
            return jsonify({"error": "No valid PDF/DOCX files uploaded"}), 400

        summary = process_files(saved_paths, out_path, export_formats=["csv", "xlsx", "txt"])
        return jsonify(summary)

    return app

def run_server(host: str = "0.0.0.0", port: int = 5001):
    app = create_app()
    app.run(host=host, port=port, debug=True)

def run_cli(patterns: List[str], out_dir: str, formats: List[str]):
    paths: List[Path] = []
    for pat in patterns:
        paths.extend([Path(p) for p in glob.glob(pat)])
    if not paths:
        print("No files found for the given patterns.")
        return
    summary = process_files(paths, Path(out_dir), export_formats=formats)
    print(summary)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Contract sentence extractor (V3.1 stitched)")
    parser.add_argument("--serve", action="store_true", help="Run Flask API server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5001)
    parser.add_argument("--input", nargs="*", default=[], help="Glob patterns for input files (CLI mode)")
    parser.add_argument("--out", default="./outputs", help="Output directory (CLI mode)")
    parser.add_argument("--formats", nargs="*", default=["csv", "xlsx", "txt"], help="Export formats (CLI mode)")
    args = parser.parse_args()

    if args.serve:
        run_server(args.host, args.port)
    else:
        run_cli(args.input, args.out, args.formats)
