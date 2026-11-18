import sqlite3
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.auth import require_roles

from app.models import (
    AppointmentCreate,
    AppointmentAssign,
    AppointmentStatus,
    AppointmentStatusUpdate,
)

router = APIRouter()


# Patient requests an appointment
@router.post("/request", status_code=status.HTTP_201_CREATED)
async def request_appointment(
    appointment: AppointmentCreate,
    current_user: dict = Depends(require_roles("patient")),
    db: sqlite3.Connection = Depends(get_db),
):
    # Ensure the appointment is in the future.
    # This version expects local, timezone-naive datetimes.
    if appointment.appointment_date.tzinfo is not None:
        raise HTTPException(
            status_code=400,
            detail="Please provide appointment date without timezone information.",
        )

    if appointment.appointment_date <= datetime.now():
        raise HTTPException(
            status_code=400, detail="Appointment date must be in the future."
        )

    try:
        with db:
            cursor = db.execute(
                """
                INSERT INTO appointments
                (patient_id, specialization, appointment_date)
                VALUES (?, ?, ?)
                """,
                (
                    current_user["id"],
                    appointment.specialization.strip(),
                    appointment.appointment_date.isoformat(),
                ),
            )

            appointment_id = cursor.lastrowid

    except sqlite3.Error:
        raise HTTPException(
            status_code=500, detail="Could not create appointment request."
        )

    return {
        "message": "Appointment request submitted successfully.",
        "appointment_id": appointment_id,
        "status": AppointmentStatus.PENDING.value,
    }


# Patient views their appointments
@router.get("/my")
async def get_my_appointments(
    current_user: dict = Depends(require_roles("patient")),
    db: sqlite3.Connection = Depends(get_db),
):
    appointments = db.execute(
        """
        SELECT
            a.id,
            a.patient_id,
            a.doctor_id,
            a.receptionist_id,
            a.specialization,
            a.appointment_date,
            a.status,
            a.created_at,
            doctor_user.name AS doctor_name
        FROM appointments a
        LEFT JOIN users doctor_user
            ON doctor_user.id = a.doctor_id
        WHERE a.patient_id = ?
        ORDER BY a.appointment_date DESC
        """,
        (current_user["id"],),
    ).fetchall()

    return {
        "total": len(appointments),
        "appointments": [dict(row) for row in appointments],
    }


# Patient cancels their own appointment
@router.patch("/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: int,
    current_user: dict = Depends(require_roles("patient")),
    db: sqlite3.Connection = Depends(get_db),
):
    try:
        with db:
            cursor = db.execute(
                """
                UPDATE appointments
                SET status = ?
                WHERE id = ?
                  AND patient_id = ?
                  AND status IN (?, ?)
                """,
                (
                    AppointmentStatus.CANCELLED.value,
                    appointment_id,
                    current_user["id"],
                    AppointmentStatus.PENDING.value,
                    AppointmentStatus.CONFIRMED.value,
                ),
            )

            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="Appointment not found or cannot be cancelled.",
                )

    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Could not cancel appointment.")

    return {
        "message": "Appointment cancelled successfully.",
        "appointment_id": appointment_id,
        "status": AppointmentStatus.CANCELLED.value,
    }


# Receptionist views pending appointments
@router.get("/pending")
async def get_pending_appointments(
    current_user: dict = Depends(require_roles("receptionist")),
    db: sqlite3.Connection = Depends(get_db),
):
    appointments = db.execute(
        """
        SELECT
            a.id,
            a.patient_id,
            patient_user.name AS patient_name,
            a.specialization,
            a.appointment_date,
            a.created_at
        FROM appointments a
        JOIN users patient_user
            ON patient_user.id = a.patient_id
        WHERE a.status = ?
          AND patient_user.is_active = 1
        ORDER BY a.appointment_date ASC
        """,
        (AppointmentStatus.PENDING.value,),
    ).fetchall()

    return {
        "total": len(appointments),
        "appointments": [dict(row) for row in appointments],
    }


# Receptionist assigns a doctor
@router.post("/{appointment_id}/assign")
async def assign_doctor(
    appointment_id: int,
    assignment: AppointmentAssign,
    current_user: dict = Depends(require_roles("receptionist")),
    db: sqlite3.Connection = Depends(get_db),
):
    try:
        # Begin an immediate transaction to prevent concurrent
        # assignments from exceeding doctor capacity.
        db.execute("BEGIN IMMEDIATE")

        appointment = db.execute(
            """
            SELECT
                id,
                patient_id,
                specialization,
                status
            FROM appointments
            WHERE id = ?
            """,
            (appointment_id,),
        ).fetchone()

        if appointment is None:
            raise HTTPException(status_code=404, detail="Appointment not found.")

        if appointment["status"] != AppointmentStatus.PENDING.value:
            raise HTTPException(
                status_code=400, detail="This appointment is no longer pending."
            )

        doctor = db.execute(
            """
            SELECT
                d.id,
                d.specialization,
                d.max_patients,
                u.name,
                u.is_active
            FROM doctors d
            JOIN users u ON u.id = d.id
            WHERE d.id = ?
            """,
            (assignment.doctor_id,),
        ).fetchone()

        if doctor is None or not doctor["is_active"]:
            raise HTTPException(status_code=404, detail="Active doctor not found.")

        if (
            doctor["specialization"].strip().lower()
            != appointment["specialization"].strip().lower()
        ):
            raise HTTPException(
                status_code=400,
                detail="Doctor specialization does not match the appointment.",
            )

        # Count currently active appointments assigned to this doctor.
        active_count = db.execute(
            """
            SELECT COUNT(*) AS total
            FROM appointments
            WHERE doctor_id = ?
              AND status IN (?, ?)
            """,
            (
                assignment.doctor_id,
                AppointmentStatus.PENDING.value,
                AppointmentStatus.CONFIRMED.value,
            ),
        ).fetchone()["total"]

        if active_count >= doctor["max_patients"]:
            raise HTTPException(
                status_code=409, detail="Doctor has reached their appointment capacity."
            )

        # Assign doctor and receptionist.
        db.execute(
            """
            UPDATE appointments
            SET doctor_id = ?,
                receptionist_id = ?,
                status = ?
            WHERE id = ?
            """,
            (
                assignment.doctor_id,
                current_user["id"],
                AppointmentStatus.CONFIRMED.value,
                appointment_id,
            ),
        )

        # Grant doctor access to this patient's medical history.
        # Existing assignments are reactivated rather than duplicated.
        db.execute(
            """
            INSERT INTO doctor_patient_assignments
            (doctor_id, patient_id, is_active)
            VALUES (?, ?, 1)
            ON CONFLICT(doctor_id, patient_id)
            DO UPDATE SET is_active = 1
            """,
            (assignment.doctor_id, appointment["patient_id"]),
        )

        db.commit()

    except HTTPException:
        db.rollback()
        raise

    except sqlite3.Error:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Could not assign doctor to appointment."
        )

    return {
        "message": "Doctor assigned successfully.",
        "appointment_id": appointment_id,
        "doctor_id": assignment.doctor_id,
        "doctor_name": doctor["name"],
        "status": AppointmentStatus.CONFIRMED.value,
    }


# Doctor views their appointments
@router.get("/doctor/my")
async def get_doctor_appointments(
    current_user: dict = Depends(require_roles("doctor")),
    db: sqlite3.Connection = Depends(get_db),
):
    appointments = db.execute(
        """
        SELECT
            a.id,
            a.patient_id,
            patient_user.name AS patient_name,
            a.specialization,
            a.appointment_date,
            a.status
        FROM appointments a
        JOIN users patient_user
            ON patient_user.id = a.patient_id
        WHERE a.doctor_id = ?
        ORDER BY a.appointment_date ASC
        """,
        (current_user["id"],),
    ).fetchall()

    return {
        "total": len(appointments),
        "appointments": [dict(row) for row in appointments],
    }


# Doctor updates appointment status
@router.patch("/{appointment_id}/status")
async def update_appointment_status(
    appointment_id: int,
    body: AppointmentStatusUpdate,
    current_user: dict = Depends(require_roles("doctor")),
    db: sqlite3.Connection = Depends(get_db),
):
    # Doctors can complete or cancel confirmed appointments.
    allowed_statuses = {AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED}

    if body.status not in allowed_statuses:
        raise HTTPException(
            status_code=400, detail="Doctor can only complete or cancel an appointment."
        )

    try:
        with db:
            cursor = db.execute(
                """
                UPDATE appointments
                SET status = ?
                WHERE id = ?
                  AND doctor_id = ?
                  AND status = ?
                """,
                (
                    body.status.value,
                    appointment_id,
                    current_user["id"],
                    AppointmentStatus.CONFIRMED.value,
                ),
            )

            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="Appointment not found or cannot be updated.",
                )

    except sqlite3.Error:
        raise HTTPException(
            status_code=500, detail="Could not update appointment status."
        )

    return {
        "message": "Appointment status updated successfully.",
        "appointment_id": appointment_id,
        "status": body.status.value,
    }
