from __future__ import annotations
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers.analytics import router as analytics_router

app = FastAPI(title="Legal Analytics API", version="0.1.0")

# CORS (open for dev; restrict in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analytics_router, prefix="/api")

from .routers.dashboard import router as dashboard_router
app.include_router(dashboard_router, prefix="/api")
