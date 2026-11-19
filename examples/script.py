import requests, time
import sys
import os
import subprocess
import sqlite3, bcrypt

server_url = "http://localhost:3000"

import helpers.creation_and_login as creation_and_login
from helpers.setup import init_db
from helpers.creation_and_login import login

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATABASE_DIR = BASE_DIR / "database"

db_path = DATABASE_DIR / "hospital.db"

INIT_SQL_PATH = DATABASE_DIR / "init.sql"


def create_demo_manager() -> tuple[int, str]:
    print("\nCreating a demo manager...")

    payload = {
        "name": "B Subhodh",
        "email": "b.subhodh@hospital.com",
        "phone": "9971548918",
        "password": "sub@1234",
        "age": 55,
        "employee_id": "MGR004",
        "dept": "Administration",
        "salary": 180000,
    }

    password_hash = bcrypt.hashpw(
        payload["password"].encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    db = sqlite3.connect(db_path)
    db.row_factory = sqlite3.Row

    try:
        with db:
            cursor = db.execute(
                """
                INSERT INTO users (
                    name, email, phone, password_hash, role, is_active
                )
                VALUES (?, ?, ?, ?, 'manager', 1)
                """,
                (
                    payload["name"],
                    payload["email"],
                    payload["phone"],
                    password_hash,
                ),
            )

            manager_id = cursor.lastrowid

            db.execute(
                """
                INSERT INTO managers (
                    id, age, employee_id, dept, salary
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    manager_id,
                    payload["age"],
                    payload["employee_id"],
                    payload["dept"],
                    payload["salary"],
                ),
            )

        if not manager_id:
            raise ValueError("Manager ID couldn't be retrieved")
        manager_token = login(manager_id, payload["password"])

        print(f"Demo manager created. ID: {manager_id}, Token: {manager_token}")
        return manager_id, manager_token

    finally:
        db.close()


def create_accounts(manager_token: str):
    patient_id, patient_token = creation_and_login.create_patient_and_login()

    receptionist_id, receptionist_token = (
        creation_and_login.create_receptionist_and_login(manager_token)
    )

    doctor_id, doctor_token = creation_and_login.create_doctor_and_login(manager_token)

    return {
        "patient": [patient_id, patient_token],
        "receptionist": [receptionist_id, receptionist_token],
        "doctor": [doctor_id, doctor_token],
    }


def request_appointment(patient_token: str) -> int:
    """
    Patient requests an appointment for a particular specialization.
    The appointment remains pending until a receptionist assigns a doctor.
    """
    print("\nRequesting a cardiology appointment...")

    route = f"{server_url}/appointments/request"

    headers = {
        "Authorization": f"Bearer {patient_token}",
        "Accept": "application/json",
    }

    payload = {
        "specialization": "Cardiology",
        "appointment_date": "2026-11-20T10:00:00",
    }

    response = requests.post(
        route,
        headers=headers,
        json=payload,
        timeout=15,
    )
    response.raise_for_status()

    result = response.json()
    appointment_id = result.get("appointment_id") or result.get("id")

    if appointment_id is None:
        raise ValueError(f"Appointment ID missing from response: {result}")

    print("Appointment requested successfully.")

    return appointment_id


def accept_appointment(
    receptionist_token: str,
    appointment_id: int,
    doctor_id: int,
):
    """
    Receptionist assigns an available doctor to the pending appointment.
    """
    print(f"Accepting appointment {appointment_id}...")

    route = f"{server_url}/appointments/{appointment_id}/assign"

    headers = {
        "Authorization": f"Bearer {receptionist_token}",
        "Accept": "application/json",
    }

    payload = {
        "doctor_id": doctor_id,
    }

    response = requests.post(
        route,
        headers=headers,
        json=payload,
        timeout=15,
    )
    response.raise_for_status()

    result = response.json()

    print("Appointment accepted and doctor assigned successfully.")

    return result


def create_medical_record(doctor_token: str, patient_id: int, payload: dict):
    """
    Create a medical record for the user. This can enhance the LLM summary output since this too is sent along with the patient information.

    This record is included in the patient's history used for LLM summarization.
    """
    print(f"Creating a medical record for patient {patient_id}...")

    route = f"{server_url}/medical-records/"

    headers = {
        "Authorization": f"Bearer {doctor_token}",
        "Accept": "application/json",
    }

    response = requests.post(
        route,
        headers=headers,
        json=payload,
        timeout=15,
    )
    response.raise_for_status()

    result = response.json()
    print("Medical record created successfully.")

    return result


def generate_patient_summary(
    patient_id: int,
    doctor_token: str,
) -> int:
    print(f"Generating medical summary for patient {patient_id}...")

    route = f"{server_url}/medical-records/patient/{patient_id}/summary"

    headers = {
        "Authorization": f"Bearer {doctor_token}",
        "Accept": "application/json",
    }

    response = requests.post(route, headers=headers, timeout=180)
    response.raise_for_status()

    result = response.json()

    summary_id = result.get("summary_id")
    if summary_id is None:
        raise ValueError(f"Summary ID missing from response: {result}")

    print(result["message"])

    return summary_id


def download_report(doctor_token, patient_id, summary_id) -> str:
    print("Downloading the patient report...")

    route = (
        f"{server_url}/medical-records/patient/{patient_id}"
        f"/summary/{summary_id}/report.pdf"
    )

    response = requests.get(
        route,
        headers={
            "Authorization": f"Bearer {doctor_token}",
            "Accept": "application/pdf",
        },
        timeout=30,
    )
    response.raise_for_status()

    filename = f"patient_{patient_id}_summary_{summary_id}.pdf"

    with open(filename, "wb") as pdf_file:
        pdf_file.write(response.content)

    print(f"Report saved as {filename}")
    return filename


def show_database_changes():
    pass


def deactivate_employee(manager_token, employee_id):
    print("\nDeactivating the doctor..")
    route = server_url + f"/managers/employees/{employee_id}/deactivate"

    response = requests.patch(
        route,
        headers={
            "Authorization": f"Bearer {manager_token}",
            "Content-Type": "application/json",
        },
        timeout=15,
    )
    response.raise_for_status()
    print(response.json())


def deactivate_patient(patient_token):
    print("\nDeactivating the patient")
    route = server_url + "/patients/me"
    response = requests.delete(
        route,
        headers={"Authorization": f"Bearer {patient_token}", "Accept": "*/*"},
        timeout=15,
    )
    response.raise_for_status()

    print("Patient deactivated successfully..")


def main():
    start = time.time()

    init_db(db_path)
    manager_id, os.environ["MANAGER_TOKEN"] = create_demo_manager()
    MANAGER_TOKEN = os.getenv("MANAGER_TOKEN")
    if not MANAGER_TOKEN:
        raise RuntimeError("MANAGER_TOKEN couldn't be set")

    id_tokens = create_accounts(MANAGER_TOKEN)

    patient, receptionist, doctor = (
        id_tokens["patient"],
        id_tokens["receptionist"],
        id_tokens["doctor"],
    )

    print(patient[0], receptionist[0], doctor[0])

    appointment_id = request_appointment(patient[1])

    appointment_result_json = accept_appointment(
        receptionist[1], appointment_id, doctor[0]
    )

    from configs import get_medical_records

    print("\nSimulating a previous diagnosis by adding some medical records")
    medical_records = get_medical_records(patient[0], appointment_id)
    create_medical_record(doctor[1], patient[0], medical_records[0])
    create_medical_record(doctor[1], patient[0], medical_records[1])
    create_medical_record(doctor[1], patient[0], medical_records[2])

    # Get the summary from the LLM.
    summary_id = generate_patient_summary(patient[0], doctor[1])

    # Download the report.
    report_file_name = download_report(doctor[1], patient[0], summary_id)

    open_report = input("Open the report(y/N): ")
    if open_report.lower() == "y":
        subprocess.run(["librewolf", report_file_name])

    # Deactivate the doctor.
    deactivate_employee(MANAGER_TOKEN, doctor[0])

    # Deactivate the patient
    deactivate_patient(patient[1])

    print(f"Complete in: {time.time() - start} s")

    print("Popping the manager access token..")
    os.environ.pop("MANAGER_TOKEN", None)


if __name__ == "__main__":
    sys.exit(main())
