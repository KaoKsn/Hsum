from datetime import datetime, timedelta, timezone
from typing import Callable

import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import os
import sqlite3

from app.database import get_db

# Load environment variables.
load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is missing from environment variables.")


# Extracts the Bearer token from the Authorization header.
"""
GET /patients/me HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
Host: https://server.example.com
"""
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
# Every since priveleged operation that requires authentication has a depedency chains that ends up getting to this


# Create JWT
def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),
        "exp": expire,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# Get Current Authenticated User
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: sqlite3.Connection = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication token.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        user_id = int(payload.get("sub"))

    except (jwt.InvalidTokenError, TypeError, ValueError):
        raise credentials_exception

    user = db.execute(
        """
        SELECT id, name, email, phone, role, is_active
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    ).fetchone()

    if user is None or not user["is_active"]:
        raise credentials_exception

    return dict(user)


# Role-Based Access Control
def require_roles(*allowed_roles: str) -> Callable:
    async def role_checker(
        current_user: dict = Depends(get_current_user),
    ):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this resource.",
            )

        return current_user

    return role_checker
