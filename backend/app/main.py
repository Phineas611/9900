# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
import logging
from pathlib import Path
from dotenv import load_dotenv

# logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# load .env from backend/.env
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

# existing routers
from app.presentation.routes.healthcheck import router as health_router
from app.presentation.routes.auth import router as auth_router
from app.presentation.routes.upload import router as upload_router
from app.presentation.routes.analytics import router as analytics_router
from app.presentation.routes.eval_lab import router as eval_lab_router

# NEW: prompt lab router
from app.presentation.routes.promptlab import router as promptlab_router

from app.database.setup import create_tables
from app.database import models

# extra analytics/dashboards
from legal_analytics_api.app.routers.analytics import router as la_analytics_router
from legal_analytics_api.app.routers.dashboard import router as la_dashboard_router

# Use environment variable for SECRET_KEY (same as security.py)
# This ensures session middleware uses the same key as token signing
import os
SECRET_KEY = os.getenv("SECRET_KEY", "123456")

app = FastAPI(title="Legal Contract Analyzer API", version="1.0.0")

# session
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="lax",
    https_only=False,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# register routers
app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(eval_lab_router, prefix="/api")
app.include_router(la_analytics_router, prefix="/api")
app.include_router(la_dashboard_router, prefix="/api")

# promptlab endpoints
app.include_router(promptlab_router, prefix="/api")

# create tables
create_tables()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000, reload=True)
