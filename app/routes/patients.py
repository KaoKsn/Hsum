import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.models import Patient
from app.auth import get_current_user, require_roles

from ..services.security import PasswordTooLongError, passwordHasher

router = APIRouter()


# Patient Registration
@router.post(
    "/create",
    status_code=status.HTTP_201_CREATED,
    summary="Register a new patient",
    description="Allows a patient to create their own account.",
)
async def add_patient(
    patient: Patient,
    db: sqlite3.Connection = Depends(get_db),
):
    try:
        password_hash = passwordHasher.hash(patient.password)
    except PasswordTooLongError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{e}")

    try:
        with db:
            cursor = db.execute(
                """
                INSERT INTO users
                    (name, email, phone, password_hash, role)
                VALUES (?, ?, ?, ?, 'patient')
                """,
                (
                    patient.name,
                    str(patient.email),
                    patient.phone,
                    password_hash,
                ),
            )

            patient_id = cursor.lastrowid

            db.execute(
                """
                INSERT INTO patients (
                    id, age, gender, blood_group, address,
                    allergies, existing_conditions, emergency_contact
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    patient_id,
                    patient.age,
                    patient.gender,
                    patient.blood_group,
                    patient.address,
                    patient.allergies,
                    patient.existing_conditions,
                    patient.emergency_contact,
                ),
            )

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email or phone number already exists.",
        )

    except sqlite3.Error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Patient registration failed.",
        )

    return {
        "message": "Patient registered successfully.",
        "patient_id": patient_id,
        "name": patient.name,
    }


# Patient Dashboard
@router.get(
    "/dashboard",
    summary="Patient dashboard",
    description="Returns basic information for the logged-in patient.",
)
async def patient_dashboard(
    current_user: dict = Depends(require_roles("patient")),
    db: sqlite3.Connection = Depends(get_db),
):
    patient = db.execute(
        """
        SELECT
            u.id,
            u.name,
            u.email,
            u.phone,
            p.age,
            p.gender,
            p.blood_group
        FROM users AS u
        JOIN patients AS p ON p.id = u.id
        WHERE u.id = ?
        """,
        (current_user["id"],),
    ).fetchone()

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found.",
        )

    return {
        "message": "Welcome to your patient dashboard.",
        "patient": dict(patient),
    }


# Get Own Patient Profile
@router.get(
    "/me",
    summary="Get my profile",
    description="Returns the profile of the authenticated patient.",
)
async def get_patient(
    current_user: dict = Depends(require_roles("patient")),
    db: sqlite3.Connection = Depends(get_db),
):
    patient = db.execute(
        """
        SELECT
            u.id,
            u.name,
            u.email,
            u.phone,
            p.age,
            p.gender,
            p.blood_group,
            p.address,
            p.allergies,
            p.existing_conditions,
            p.emergency_contact
        FROM users AS u
        JOIN patients AS p ON p.id = u.id
        WHERE u.id = ?
        """,
        (current_user["id"],),
    ).fetchone()

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient profile not found.",
        )

    return dict(patient)


# Deactivate Own Account
@router.delete(
    "/me",
    summary="Deactivate my account",
    description="Deactivates the authenticated patient's account.",
)
async def deactivate_patient(
    # Get the current_user information using JWT in auth.py
    current_user: dict = Depends(require_roles("patient")),
    db: sqlite3.Connection = Depends(get_db),
):
    try:
        with db:
            cursor = db.execute(
                """
                UPDATE users
                SET is_active = 0
                WHERE id = ? AND role = 'patient' AND is_active = 1
                """,
                (current_user["id"],),
            )

            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Patient account is already inactive.",
                )

    except sqlite3.Error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not deactivate patient account.",
        )

    return {
        "message": "Your patient account has been deactivated.",
        "patient_id": current_user["id"],
    }
