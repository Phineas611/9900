# backend/app/application/services/auth_service.py
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.application.models.auth import RegisterRequest, RegisterResponse,LoginRequest, LoginResponse
from app.persistence.user_repository import get_by_email, create_user
from app.persistence.security import hash_password, verify_password, sign_session


class AuthService:
    @staticmethod
    def register(db: Session, payload: RegisterRequest) -> RegisterResponse:
        if get_by_email(db, payload.email):
            raise HTTPException(status_code=400, detail="Email already registered")
        ph = hash_password(payload.password)
        user = create_user(db, email=payload.email, password_hash=ph, name=payload.name)
        return RegisterResponse(id=user.id, email=user.email, name=user.name)
    @staticmethod
    def login(db: Session, payload: LoginRequest) -> LoginResponse:
        user = get_by_email(db, payload.email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = sign_session(user.id)

        return LoginResponse(id=user.id, email=user.email, name=user.name, token=token)