import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from app.database import get_db
from app.auth import require_roles
from app.models import Receptionist

from ..services.security import passwordHasher, PasswordTooLongError

router = APIRouter()


# Create receptionist account (Manager only)
@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_receptionist(
    receptionist: Receptionist,
    current_user: dict = Depends(require_roles("manager")),
    db: sqlite3.Connection = Depends(get_db),
):
    try:
        password_hash = passwordHasher.hash(receptionist.password)
    except PasswordTooLongError as e:
        raise HTTPException(status_code=HTTP_400_BAD_REQUEST, detail=f"e")

    try:
        with db:
            # Insert shared account information
            cursor = db.execute(
                """
                INSERT INTO users
                (name, email, phone, password_hash, role)
                VALUES (?, ?, ?, ?, 'receptionist')
                """,
                (
                    receptionist.name,
                    str(receptionist.email),
                    receptionist.phone,
                    password_hash,
                ),
            )

            receptionist_id = cursor.lastrowid

            # Insert receptionist-specific information
            db.execute(
                """
                INSERT INTO receptionists
                (id, age, employee_id, dept, salary)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    receptionist_id,
                    receptionist.age,
                    receptionist.employee_id,
                    receptionist.dept,
                    receptionist.salary,
                ),
            )

    except sqlite3.IntegrityError as exc:
        message = str(exc)

        if "employee_id" in message:
            detail = "This employee ID is already registered."
        else:
            detail = "An account with this email or phone number already exists."

        raise HTTPException(status_code=409, detail=detail)

    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Receptionist registration failed.")

    return {
        "message": "Receptionist account created successfully.",
        "receptionist_id": receptionist_id,
        "employee_id": receptionist.employee_id,
        "name": receptionist.name,
    }


# Receptionist dashboard
@router.get("/dashboard")
async def receptionist_dashboard(
    current_user: dict = Depends(require_roles("receptionist")),
    db: sqlite3.Connection = Depends(get_db),
):
    receptionist = db.execute(
        """
        SELECT
            u.id,
            u.name,
            u.email,
            u.phone,
            r.employee_id,
            r.age,
            r.dept
        FROM users u
        JOIN receptionists r ON r.id = u.id
        WHERE u.id = ?
        """,
        (current_user["id"],),
    ).fetchone()

    if receptionist is None:
        raise HTTPException(status_code=404, detail="Receptionist profile not found.")

    pending_appointments = db.execute("""
        SELECT COUNT(*) AS total
        FROM appointments
        WHERE status = 'pending'
        """).fetchone()["total"]

    return {
        "message": "Welcome to your receptionist dashboard.",
        "receptionist": dict(receptionist),
        "pending_appointments": pending_appointments,
    }


# Get receptionist's own profile
@router.get("/me")
async def get_receptionist_profile(
    current_user: dict = Depends(require_roles("receptionist")),
    db: sqlite3.Connection = Depends(get_db),
):
    receptionist = db.execute(
        """
        SELECT
            u.id,
            u.name,
            u.email,
            u.phone,
            r.employee_id,
            r.age,
            r.dept,
            r.salary
        FROM users u
        JOIN receptionists r ON r.id = u.id
        WHERE u.id = ?
        """,
        (current_user["id"],),
    ).fetchone()

    if receptionist is None:
        raise HTTPException(status_code=404, detail="Receptionist profile not found.")

    return dict(receptionist)


# Update receptionist contact details
@router.patch("/me/contact")
async def update_receptionist_contact(
    name: str,
    phone: str,
    current_user: dict = Depends(require_roles("receptionist")),
    db: sqlite3.Connection = Depends(get_db),
):
    try:
        with db:
            cursor = db.execute(
                """
                UPDATE users
                SET name = ?, phone = ?
                WHERE id = ? AND role = 'receptionist'
                """,
                (name, phone, current_user["id"]),
            )

            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=404, detail="Receptionist account not found."
                )

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409, detail="This phone number is already registered."
        )

    except sqlite3.Error:
        raise HTTPException(
            status_code=500, detail="Could not update receptionist details."
        )

    return {"message": "Receptionist contact details updated successfully."}


@router.delete("/{receptionist_id}/deactivate")
def deactivate_receptionist(
    receptionist_id: int,
    current_user: dict = Depends(require_roles("manager")),  # Manager
    db: sqlite3.Connection = Depends(get_db),
):
    try:
        with db:
            cursor = db.execute(
                """
                UPDATE users
                SET is_active=0
                WHERE id = ? and role = 'receptionist'
                AND is_active = 1
                """,
                (receptionist_id,),
            )

            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=HTTP_404_NOT_FOUND,
                    detail="Receptionist not found or is already inactive",
                )
    except sqlite3.Error:
        raise HTTPException(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Couldn not deactive the receptionist account",
        )
    return {"message": "Receptionist deactivated successfully."}
