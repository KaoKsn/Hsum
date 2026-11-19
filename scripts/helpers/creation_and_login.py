import requests, sys, json, time, os

server_url = "http://localhost:3000"


def login(user_id: int, password: str) -> str:
    """
    Returns the JWT token after logging in as the user
    """
    payload = {"id": user_id, "password": password}

    response = requests.post(url=server_url + "/auth/login", json=payload)

    response.raise_for_status()

    token = response.json().get("access_token")

    if not token:
        raise ValueError("Login succeeded but no access token was returned.")

    return token


def create_account_and_login(
    route: str, payload: dict, token: str | None
) -> tuple[int, str]:
    """
    Create a user account and return the user id and JWT token after the login
    Token lives for an hour.
    """
    headers = {"Content-Type": "application/json"}

    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.post(route, json=payload, headers=headers, timeout=15)
    response.raise_for_status()

    response_json = response.json()
    user_id = (
        response_json.get("id")
        or response_json.get("patient_id")
        or response_json.get("doctor_id")
        or response_json.get("receptionist_id")
        or response_json.get("manager_id")
    )

    if user_id is None:
        raise ValueError(f"User ID missing from response: {response_json}")

    login_token = login(user_id, payload["password"])

    print(f"Created account ID {user_id}: {response_json}")

    return user_id, login_token


def create_patient_and_login() -> tuple:
    print("\nCreating a patient..")
    payload = {
        "name": "Alex Johnson",
        "email": "alex.johnson@example.com",
        "phone": "9876543210",
        "password": "Alex@1234",
        "age": 25,
        "gender": "Male",
        "blood_group": "O+",
        "address": "MIT Hostels, Bengaluru",
        "allergies": "Dust, pollen",
        "existing_conditions": "Cholesterol",
        "emergency_contact": "9876501234",
    }

    route = server_url + "/patients/create"
    patient_id, patient_token = create_account_and_login(route, payload, None)
    return patient_id, patient_token


def create_receptionist_and_login(manager_token) -> tuple:
    print("\nCreating a receptionist..")
    payload = {
        "name": "Sarah Williams",
        "email": "sarah.williams@hospital.com",
        "phone": "9876543211",
        "password": "Sarah@1234",
        "age": 28,
        "employee_id": "REC002",
        "dept": "Administration",
        "salary": 32000,
    }
    route = server_url + "/receptionists/create"
    receptionist_id, receptionist_token = create_account_and_login(
        route, payload, manager_token
    )
    return receptionist_id, receptionist_token


def create_doctor_and_login(manager_token: str) -> tuple:
    print("\nCreating a doctor who specializes in Cardiology..")
    payload = {
        "name": "Dr. Subhash",
        "email": "m.subhash@hospital.com",
        "phone": "9876543212",
        "password": "Subhash@1234",
        "age": 42,
        "dept": "Cardiology",
        "salary": 95000,
        "specialization": "Cardiology",
        "max_patients": 20,
        "qualification": "MBBS, MD (Cardiology)",
    }
    route = server_url + "/doctors/create"

    doctor_id, doctor_token = create_account_and_login(route, payload, manager_token)

    return doctor_id, doctor_token
