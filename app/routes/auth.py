import sqlite3
import bcrypt

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.models import LoginRequest, LoginResponse
from app.auth import create_access_token

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest, db: sqlite3.Connection = Depends(get_db)):
    # Find user by ID
    user = db.execute(
        """
        SELECT id, password_hash, role, is_active
        FROM users
        WHERE id = ?
        """,
        (body.id,),
    ).fetchone()

    # Check whether user exists
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ID or password."
        )

    # Check whether account is active
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="This account is inactive."
        )

    # Check password
    password_matches = bcrypt.checkpw(
        body.password.encode("utf-8"), user["password_hash"].encode("utf-8")
    )

    if not password_matches:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ID or password."
        )

    # Generate JWT
    token = create_access_token(user["id"])

    return LoginResponse(
        access_token=token, token_type="bearer", role=user["role"], id=user["id"]
    )
