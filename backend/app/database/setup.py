import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pathlib import Path

# ==========================
# Database setup - SQLite only
# ==========================
# Use SQLite database
backend_dir = Path(__file__).parent.parent.parent

# Check for existing database files in order of preference
old_db_path = backend_dir / "app.db"
new_db_dir = backend_dir / "data"
new_db_path = new_db_dir / "app.db"
tmp_db_path = Path("/tmp/app.db")

# Priority: old location > new location > /tmp
if old_db_path.exists():
    # Use existing database from old location
    db_path = str(old_db_path)
elif new_db_path.exists():
    # Use existing database from new location
    db_path = str(new_db_path)
else:
    # Create new database - try new location first
    try:
        new_db_dir.mkdir(parents=True, exist_ok=True)
        db_path = str(new_db_path)
    except (PermissionError, OSError):
        # Fallback to /tmp if we can't write to project directory
        if os.path.exists("/tmp"):
            db_path = str(tmp_db_path)
        else:
            # Last resort: use backend directory
            db_path = str(old_db_path)

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
