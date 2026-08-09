"""
OmniMind AI — Authentication API Endpoints (/auth)
"""
import re
import logging
from pydantic import BaseModel, Field, field_validator
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from omnimind.db.base import get_db
from omnimind.db.models import User
from omnimind.db.crud import get_user_by_email, create_user
from omnimind.backend.api.auth import hash_password, verify_password, create_access_token, get_authenticated_user

logger = logging.getLogger("omnimind.backend.api.routes.auth")

router = APIRouter(prefix="/auth", tags=["Authentication"])


class SignupRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password")
    name: str = Field(..., description="User full name")

    @field_validator("email")
    def validate_email(cls, v: str) -> str:
        if "@" not in v or "." not in v:
            raise ValueError("Invalid email address format.")
        return v.lower().strip()


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")

    @field_validator("email")
    def validate_email(cls, v: str) -> str:
        return v.lower().strip()


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    name: str
    api_key: str


@router.post("/signup", response_model=AuthResponse, status_code=201)
async def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """Register a new SaaS user and generate access token & API Key."""
    existing = get_user_by_email(db, request.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is already registered.",
        )

    user = create_user(db, email=request.email, name=request.name)
    user.hashed_password = hash_password(request.password)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.id, "email": user.email})
    return AuthResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        name=user.name,
        api_key=user.api_key,
    )


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate user and return JWT access token."""
    user = get_user_by_email(db, request.email)
    if not user or not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
        )

    token = create_access_token({"sub": user.id, "email": user.email})
    return AuthResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        name=user.name,
        api_key=user.api_key,
    )


@router.get("/me")
async def get_me(current_user: User = Depends(get_authenticated_user)):
    """Get profile info for currently authenticated user."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "api_key": current_user.api_key,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else "",
    }
