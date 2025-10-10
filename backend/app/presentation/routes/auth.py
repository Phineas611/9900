# backend/app/presentation/routes/auth.py
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from app.application.models.auth import RegisterRequest, RegisterResponse, LoginRequest, LoginResponse
from app.application.services.auth_service import AuthService
from app.database.setup import get_db
from app.application.auth import get_current_user


router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=RegisterResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    return AuthService.register(db, payload)
@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, response: Response, db: Session = Depends(get_db)):
    res = AuthService.login(db, payload)
    response.set_cookie(
        key="session", value=res.token,
        httponly=True, samesite="lax", max_age=86400, path="/"
    )
    return res
@router.get("/me")
def me(user = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "name": user.name}

from fastapi import APIRouter, Depends, Response, status

from fastapi import APIRouter, Response, status

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response):
    response.delete_cookie(
        key="session",
        path="/",
        samesite="lax",
        httponly=True,         
    )

