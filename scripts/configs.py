init_db_script = """

BEGIN TRANSACTION;

-- Patient summaries
DELETE FROM patient_summaries;

-- Medical records
DELETE FROM medical_records;

-- Doctor-patient assignments
DELETE FROM doctor_patient_assignments;

-- Appointments
DELETE FROM appointments;

-- Patient profiles
DELETE FROM patients;

-- Doctor profiles
DELETE FROM doctors;

-- Receptionist profiles
DELETE FROM receptionists;

-- Manager profiles
DELETE FROM managers;

-- All users
DELETE FROM users;

COMMIT;
"""


def get_medical_records(patient_id: int, appointment_id: int) -> list:
    medical_records = [
        {
            "patient_id": patient_id,
            "appointment_id": appointment_id,
            "diagnosis": "Suspected cardiac arrhythmia (unconfirmed)",
            "symptoms": "Occasional palpitations, brief episodes of dizziness, and intermittent fatigue.",
            "prescription": "No prescription recorded. Further evaluation required.",
            "doctor_notes": (
                "Fictional test entry for demonstration purposes. "
                "Patient reports intermittent palpitations and dizziness. "
                "Cardiac arrhythmia is suspected but has not been confirmed. "
                "Recommend clinical assessment and ECG evaluation."
            ),
        },
        {
            "patient_id": patient_id,
            "appointment_id": appointment_id,
            "diagnosis": "Essential hypertension (confirmed)",
            "symptoms": "No significant symptoms reported. Elevated blood pressure documented during repeated clinical measurements.",
            "prescription": "No prescription recorded.",
            "doctor_notes": (
                "Fictional test entry for demonstration purposes. "
                "Essential hypertension has been confirmed following repeated "
                "elevated blood pressure measurements by a clinician. "
                "Regular blood pressure monitoring and medical follow-up advised."
            ),
        },
        {
            "patient_id": patient_id,
            "appointment_id": appointment_id,
            "diagnosis": "Suspected atrial fibrillation (unconfirmed)",
            "symptoms": (
                "Episodes of irregular heartbeat, occasional palpitations, "
                "mild breathlessness during physical activity, and occasional fatigue."
            ),
            "prescription": (
                "No medication prescribed in this fictional test entry. "
                "Illustrative medication considerations: anticoagulation may be "
                "considered after stroke-risk assessment, and rate-control medication "
                "may be considered after clinical evaluation."
            ),
            "doctor_notes": (
                "Fictional test entry for demonstration purposes. "
                "Patient reports intermittent palpitations and an irregular heartbeat. "
                "Atrial fibrillation is suspected but has not been confirmed. "
                "ECG and further cardiac evaluation are required. "
                "Treatment decisions, including rate control and anticoagulation, "
                "must be made by the treating clinician after appropriate assessment."
            ),
        },
    ]
    return medical_records
