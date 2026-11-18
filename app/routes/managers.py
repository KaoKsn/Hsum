import sqlite3

from fastapi import APIRouter, Depends, HTTPException, status

from app.database import get_db
from app.auth import require_roles

router = APIRouter()


# Manager dashboard
@router.get("/dashboard")
async def manager_dashboard(
    current_user: dict = Depends(require_roles("manager")),
    db: sqlite3.Connection = Depends(get_db),
):
    statistics = db.execute("""
        SELECT
            (SELECT COUNT(*) FROM users
             WHERE role = 'patient' AND is_active = 1)
             AS total_patients,

            (SELECT COUNT(*) FROM users
             WHERE role = 'doctor' AND is_active = 1)
             AS total_doctors,

            (SELECT COUNT(*) FROM users
             WHERE role = 'receptionist' AND is_active = 1)
             AS total_receptionists,

            (SELECT COUNT(*) FROM appointments
             WHERE status = 'pending')
             AS pending_appointments,

            (SELECT COUNT(*) FROM appointments
             WHERE status = 'confirmed')
             AS confirmed_appointments,

            (SELECT COUNT(*) FROM appointments
             WHERE status = 'completed')
             AS completed_appointments
        """).fetchone()

    return {
        "message": "Welcome to the manager dashboard.",
        "manager_id": current_user["id"],
        "manager_name": current_user["name"],
        "statistics": dict(statistics),
    }


# Manager views all doctors and receptionists
@router.get("/employees")
async def get_employees(
    current_user: dict = Depends(require_roles("manager")),
    db: sqlite3.Connection = Depends(get_db),
):
    employees = db.execute("""
        SELECT
            u.id,
            u.name,
            u.email,
            u.phone,
            u.role,
            u.is_active,
            d.dept,
            d.specialization,
            d.max_patients,
            r.employee_id
        FROM users u
        LEFT JOIN doctors d ON d.id = u.id
        LEFT JOIN receptionists r ON r.id = u.id
        WHERE u.role IN ('doctor', 'receptionist')
        ORDER BY u.role, u.name
        """).fetchall()

    return {
        "total_employees": len(employees),
        "employees": [dict(row) for row in employees],
    }


# Manager deactivates an employee
@router.patch("/employees/{employee_id}/deactivate")
async def deactivate_employee(
    employee_id: int,
    current_user: dict = Depends(require_roles("manager")),
    db: sqlite3.Connection = Depends(get_db),
):
    try:
        with db:
            cursor = db.execute(
                """
                UPDATE users
                SET is_active = 0
                WHERE id = ?
                  AND role IN ('doctor', 'receptionist')
                  AND is_active = 1
                """,
                (employee_id,),
            )

            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="Active doctor or receptionist not found. Or they might already be deactivated.",
                )

    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Could not deactivate employee.")

    return {
        "message": "Employee account deactivated successfully.",
        "employee_id": employee_id,
    }


# Manager reactivates an employee
@router.patch("/employees/{employee_id}/activate")
async def activate_employee(
    employee_id: int,
    current_user: dict = Depends(require_roles("manager")),
    db: sqlite3.Connection = Depends(get_db),
):
    try:
        with db:
            cursor = db.execute(
                """
                UPDATE users
                SET is_active = 1
                WHERE id = ?
                  AND role IN ('doctor', 'receptionist')
                  AND is_active = 0
                """,
                (employee_id,),
            )

            if cursor.rowcount == 0:
                raise HTTPException(
                    status_code=404,
                    detail="Inactive doctor or receptionist not found, or they might already be active",
                )

    except sqlite3.Error:
        raise HTTPException(status_code=500, detail="Could not activate employee.")

    return {
        "message": "Employee account activated successfully.",
        "employee_id": employee_id,
    }
