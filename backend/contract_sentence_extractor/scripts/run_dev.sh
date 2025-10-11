#!/usr/bin/env bash
set -euo pipefail
python -m app.main --serve --host 0.0.0.0 --port 5001
