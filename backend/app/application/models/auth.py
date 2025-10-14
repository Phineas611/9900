# backend/app/application/models/auth.py
from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=1, max_length=100)  

class RegisterResponse(BaseModel):
    id: int
    email: EmailStr
    name: str  


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)

class LoginResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    token: str

class MeResponse(BaseModel):
    id: int
    email: EmailStr
    name: str