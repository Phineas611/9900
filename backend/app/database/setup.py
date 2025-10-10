from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# ==========================
# Database setup
# ==========================
DATABASE_URL = "sqlite:///./app.db"  # 生成在 backend/app/app.db

engine = create_engine(DATABASE_URL,connect_args={"check_same_thread": False})

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
