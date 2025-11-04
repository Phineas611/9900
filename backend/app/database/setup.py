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
# 2. Old location: backend/app.db
# 3. New location: backend/data/app.db
# 4. Create in new location or backend directory (avoid /tmp for persistence)

# Check environment variable first
if os.getenv("DATABASE_PATH"):
    db_path = os.getenv("DATABASE_PATH")
    logger.info(f"Using database path from environment variable: {db_path}")
else:
    old_db_path = backend_dir / "app.db"
    new_db_dir = backend_dir / "data"
    new_db_path = new_db_dir / "app.db"
    
    # Check for existing database files
    if old_db_path.exists():
        db_path = str(old_db_path)
        logger.info(f"Using existing database from old location: {db_path}")
    elif new_db_path.exists():
        db_path = str(new_db_path)
        logger.info(f"Using existing database from new location: {db_path}")
    else:
        # Create new database - prefer project directory (persistent)
        try:
            new_db_dir.mkdir(parents=True, exist_ok=True)
            db_path = str(new_db_path)
            logger.info(f"Creating new database in: {db_path}")
        except (PermissionError, OSError) as e:
            # Fallback to backend directory if data directory not writable
            db_path = str(old_db_path)
            logger.warning(f"Cannot create data directory, using backend directory: {db_path}, error: {e}")

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
