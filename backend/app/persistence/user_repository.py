# backend/app/persistence/user_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database.models.user import User

def get_by_email(db: Session, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    return db.scalar(stmt)

def get_by_id(db: Session, user_id: int) -> User | None:
    stmt = select(User).where(User.id == user_id)
    return db.scalar(stmt)

def create_user(db: Session, *, email: str, password_hash: str, name: str) -> User:
    user = User(email=email, password_hash=password_hash, name=name) 
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
