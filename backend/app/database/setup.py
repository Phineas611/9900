import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

# ==========================
# Database setup - SQLite only
# ==========================
# Use SQLite database
backend_dir = Path(__file__).parent.parent.parent
db_dir = backend_dir / "data"

# Create data directory if it doesn't exist
try:
    db_dir.mkdir(parents=True, exist_ok=True)
    db_path = str(db_dir / "app.db")
except (PermissionError, OSError):
    # Fallback to /tmp if we can't write to project directory (e.g., Render read-only filesystem)
    if os.path.exists("/tmp"):
        db_path = "/tmp/app.db"
    else:
        # Last resort: use backend directory
        db_path = str(backend_dir / "app.db")

DATABASE_URL = f"sqlite:///{db_path}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """手动调用时创建所有模型对应的表"""
    Base.metadata.create_all(bind=engine)
