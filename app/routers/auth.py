from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError

from app.db import get_db
from app.services.auth_service import (
    create_user,
    get_user_by_email,
    verify_password,
    create_access_token,
    create_refresh_token,
    get_secret_key,
    get_user_count,
)
from app.models.user import User
from app.deps import get_current_user_optional


router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    role: Optional[str] = Field(default="staff", pattern="^(admin|staff)$")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str


@router.post("/register", response_model=dict, status_code=201)
async def register(
    payload: RegisterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional)
):
    """
    Create a user.
    - If no users exist yet, allow open registration (bootstrap).
    - Otherwise, require current user to be admin.
    """
    total = await get_user_count(db)
    if total > 0 and (not current_user or current_user.role != "admin"):
        raise HTTPException(status_code=403, detail="Only admin can register users")
    user, error = await create_user(db, payload.email, payload.password, role=payload.role or "staff")
    if error:
        raise HTTPException(status_code=400, detail=error)
    return {"id": user.id, "email": user.email, "role": user.role}


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, role=user.role)


def decode_token(token: str) -> dict:
    return jwt.decode(token, get_secret_key(), algorithms=["HS256"])


@router.get("/me", response_model=dict)
async def me(authorization: str = "", db: AsyncSession = Depends(get_db)):
    """
    Simple /me using Authorization: Bearer <token>
    """
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
        user_id = int(payload.get("sub", "0"))
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    result = await db.get(User, user_id)
    if not result:
        raise HTTPException(status_code=401, detail="User not found")
    return {"id": result.id, "email": result.email, "role": result.role}


