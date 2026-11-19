import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.auth import get_current_user, require_roles
from app.models import Doctor

from ..services.security import PasswordTooLongError, passwordHasher

router = APIRouter()


# Create a doctor account (Manager only)
@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_doctor(
    doctor: Doctor,
    current_user: dict = Depends(require_roles("manager")),
    db: sqlite3.Connection = Depends(get_db),
):
    try:
        password_hash = passwordHasher.hash(doctor.password)
    except PasswordTooLongError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"{e}")

    try:
        with db:
            # Create the user account
            cursor = db.execute(
                """
                INSERT INTO users
                (name, email, phone, password_hash, role)
                VALUES (?, ?, ?, ?, 'doctor')
                """,
                (doctor.name, str(doctor.email), doctor.phone, password_hash),
            )

            doctor_id = cursor.lastrowid

            # Create the doctor profile
            db.execute(
                """
                INSERT INTO doctors
                (id, dept, age, salary, specialization,
                 max_patients, qualification)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    doctor_id,
                    doctor.dept,
                    doctor.age,
                    doctor.salary,
                    doctor.specialization,
                    doctor.max_patients,
                    doctor.qualification,
                ),
            )

    except sqlite3.IntegrityError as e:

        error = str(e)

        if "users.email" in error:
            detail = "This email address is already registered"
        elif "users.phone" in error:
            detail = "This phone number is already registered"
        else:
            detail = "A databse constraint was violated"
        raise HTTPException(
            status_code=409,
            detail=detail,
        )

    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Doctor registration failed.")

    return {
        "message": "Doctor account created successfully.",
        "doctor_id": doctor_id,
        "name": doctor.name,
    }


# Doctor dashboard (Doctor only)
@router.get("/dashboard")
async def doctor_dashboard(
    current_user: dict = Depends(require_roles("doctor")),
    db: sqlite3.Connection = Depends(get_db),
):
    doctor = db.execute(
        """
        SELECT
            u.id,
            u.name,
            u.email,
            u.phone,
            d.dept,
            d.age,
            d.specialization,
            d.qualification,
            d.max_patients
        FROM users u
        JOIN doctors d ON d.id = u.id
        WHERE u.id = ?
        """,
        (current_user["id"],),
    ).fetchone()

    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor profile not found.")

    appointment_count = db.execute(
        """
        SELECT COUNT(*) AS total
        FROM appointments
        WHERE doctor_id = ?
          AND status IN ('pending', 'confirmed')
        """,
        (current_user["id"],),
    ).fetchone()["total"]

    return {
        "message": "Welcome to your doctor dashboard.",
        "doctor": dict(doctor),
        "active_appointments": appointment_count,
    }


# Get doctor's own profile
@router.get("/me")
async def get_doctor_profile(
    current_user: dict = Depends(require_roles("doctor")),
    db: sqlite3.Connection = Depends(get_db),
):
    doctor = db.execute(
        """
        SELECT
            u.id,
            u.name,
            u.email,
            u.phone,
            d.dept,
            d.age,
            d.salary,
            d.specialization,
            d.max_patients,
            d.qualification
        FROM users u
        JOIN doctors d ON d.id = u.id
        WHERE u.id = ?
        """,
        (current_user["id"],),
    ).fetchone()

    if doctor is None:
        raise HTTPException(status_code=404, detail="Doctor profile not found.")

    return dict(doctor)


# List doctors by specialization
# Manager and receptionist only
@router.get("/specialization/{specialization}")
async def get_doctors_by_specialization(
    specialization: str,
    current_user: dict = Depends(require_roles("manager", "receptionist")),
    db: sqlite3.Connection = Depends(get_db),
):
    doctors = db.execute(
        """
        SELECT
            u.id,
            u.name,
            d.dept,
            d.specialization,
            d.qualification,
            d.max_patients
        FROM users u
        JOIN doctors d ON d.id = u.id
        WHERE LOWER(d.specialization) = LOWER(?)
          AND u.is_active = 1
        ORDER BY u.name
        """,
        (specialization,),
    ).fetchall()

    return {
        "specialization": specialization,
        "total_doctors": len(doctors),
        "doctors": [dict(doctor) for doctor in doctors],
    }


# 5. Update doctor's own contact information
@router.patch("/me/contact")
async def update_doctor_contact(
    name: str,
    phone: str,
    current_user: dict = Depends(require_roles("doctor")),
    db: sqlite3.Connection = Depends(get_db),
):
    try:
        with db:
            cursor = db.execute(
                """
                UPDATE users
                SET name = ?, phone = ?
                WHERE id = ? AND role = 'doctor'
                """,
                (name, phone, current_user["id"]),
            )

            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Doctor account not found.")

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409, detail="This phone number is already registered."
        )

    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Could not update doctor details.")

    return {"message": "Doctor contact details updated successfully."}
