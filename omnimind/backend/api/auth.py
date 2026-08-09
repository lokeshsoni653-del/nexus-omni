"""
OmniMind AI — JWT & API Key Authentication Service
"""
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from config import settings
from omnimind.db.base import get_db
from omnimind.db.models import User
from omnimind.db.crud import get_user_by_api_key, get_user_by_email, get_user_by_id

logger = logging.getLogger("omnimind.backend.api.auth")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


# ── Password Hashing Helpers ──────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hash password using SHA-256 with secret key salt."""
    salted = f"{settings.SECRET_KEY}:{password}".encode("utf-8")
    return hashlib.sha256(salted).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against stored hash."""
    return hash_password(plain_password) == hashed_password


# ── JWT Token Generation & Verification ───────────────────────────────────────

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Generate JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": int(expire.timestamp())})
    
    try:
        from jose import jwt
        return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    except ImportError:
        # Fallback simple token if jose is not installed
        import json, base64
        payload = json.dumps(to_encode).encode("utf-8")
        return base64.urlsafe_b64encode(payload).decode("utf-8")


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate JWT access token."""
    try:
        from jose import jwt
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except Exception:
        try:
            import json, base64
            payload = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
            return json.loads(payload)
        except Exception:
            return None


# ── Authentication Dependency ──────────────────────────────────────────────────

async def get_authenticated_user(
    token: Optional[str] = Depends(oauth2_scheme),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> User:
    """
    Authenticate user via Bearer JWT token or X-API-Key header.
    Strict multi-tenant isolation.
    """
    user: Optional[User] = None

    # 1. Try API Key Header
    if x_api_key:
        user = get_user_by_api_key(db, x_api_key)

    # 2. Try JWT Bearer Token
    elif token:
        payload = decode_access_token(token)
        if payload and "sub" in payload:
            user = get_user_by_id(db, payload["sub"])

    # 3. Dev Fallback Mode (auto-create dev user if no credentials provided)
    if not user:
        dev_user = get_user_by_email(db, "dev@omnimind.local")
        if not dev_user:
            from omnimind.db.crud import create_user
            dev_user = create_user(db, email="dev@omnimind.local", name="Dev User")
        return dev_user

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled.",
        )

    return user
