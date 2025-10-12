# backend/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import uvicorn

from app.presentation.routes.healthcheck import router as health_router
from app.presentation.routes.auth import router as auth_router  
from app.presentation.routes.upload import router as upload_router
from app.database.setup import create_tables
from app.database import models  
SECRET_KEY = "123456"
app = FastAPI(title="test API", version="1.0.0")

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
app.include_router(health_router, prefix="/api")
app.include_router(auth_router,    prefix="/api")  
app.include_router(upload_router, prefix="/api")
create_tables()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000, reload=True)
