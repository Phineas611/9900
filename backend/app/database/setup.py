import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

# ==========================
# Database setup - SQLite only
# ==========================
logger = logging.getLogger(__name__)

backend_dir = Path(__file__).parent.parent.parent

# Priority order for database path:
# 1. Environment variable (if set)
# 2. backend/app.db (always use this location)

# Check environment variable first
if os.getenv("DATABASE_PATH"):
    db_path = os.getenv("DATABASE_PATH")
    logger.info(f"Using database path from environment variable: {db_path}")
else:
    # Always use backend/app.db
    db_path = str(backend_dir / "app.db")
    if Path(db_path).exists():
        logger.info(f"Using existing database: {db_path}")
    else:
        logger.info(f"Creating new database: {db_path}")

DATABASE_URL = f"sqlite:///{db_path}"
logger.info(f"Database URL: {DATABASE_URL}")

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
