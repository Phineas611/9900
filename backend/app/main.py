from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
import logging
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Load environment variables from backend/.env explicitly
load_dotenv(dotenv_path=Path(__file__).resolve().parents[1] / ".env")

# existing routers
from app.presentation.routes.healthcheck import router as health_router
from app.presentation.routes.auth import router as auth_router
from app.presentation.routes.upload import router as upload_router
from app.presentation.routes.analytics import router as analytics_router
<<<<<<< HEAD

# NEW: prompt lab router
from app.presentation.routes.promptlab import router as promptlab_router

=======
from app.presentation.routes.eval_lab import router as eval_lab_router
>>>>>>> bdea9e0aeb59332a6958f19b2717a3ab7b92fefe
from app.database.setup import create_tables
from app.database import models

# these two seem to be in your repo for analytics/dashboard
from legal_analytics_api.app.routers.analytics import router as la_analytics_router
from legal_analytics_api.app.routers.dashboard import router as la_dashboard_router

SECRET_KEY = "123456"

app = FastAPI(title="Legal Contract Analyzer API", version="1.0.0")

# session + CORS (kept as in repo)
app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="lax",
    https_only=False,
)

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

# existing routers
app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(upload_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(eval_lab_router, prefix="/api")
app.include_router(la_analytics_router, prefix="/api")
app.include_router(la_dashboard_router, prefix="/api")

# NEW: prompt lab
app.include_router(promptlab_router, prefix="/api")

# create tables at startup (kept from your repo)
create_tables()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000, reload=True)
