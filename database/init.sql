-- HOSPITAL MANAGEMENT SYSTEM
-- Database: SQLite3.54

PRAGMA foreign_keys = ON;


-- 1. COMMON USERS TABLE (Parent)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    name TEXT NOT NULL,

    email TEXT NOT NULL UNIQUE,

    phone TEXT NOT NULL UNIQUE,

    password_hash TEXT NOT NULL,

    role TEXT NOT NULL CHECK (
        role IN ('patient', 'doctor', 'receptionist', 'manager')
    ),

    is_active INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0, 1)),

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- 2. PATIENTS TABLE

CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY,

    age INTEGER NOT NULL CHECK (age BETWEEN 3 AND 120),

    gender TEXT,

    blood_group TEXT,

    address TEXT,

    allergies TEXT,

    existing_conditions TEXT,

    emergency_contact TEXT,

    FOREIGN KEY (id)
        REFERENCES users(id) ON DELETE CASCADE
);


-- 3. DOCTORS TABLE

CREATE TABLE IF NOT EXISTS doctors (
    id INTEGER PRIMARY KEY,

    dept TEXT NOT NULL,

    age INTEGER NOT NULL CHECK (age BETWEEN 3 AND 120),
    salary REAL,

    specialization TEXT NOT NULL,

    max_patients INTEGER NOT NULL DEFAULT 20
        CHECK (max_patients > 0),

    qualification TEXT,

    FOREIGN KEY (id)
        REFERENCES users(id) ON DELETE CASCADE
);


-- 4. RECEPTIONISTS TABLE

CREATE TABLE IF NOT EXISTS receptionists (
    id INTEGER PRIMARY KEY,

    age INTEGER NOT NULL CHECK (age BETWEEN 3 AND 120),

    employee_id TEXT NOT NULL UNIQUE,

    dept TEXT,

    salary REAL,

    FOREIGN KEY (id)
        REFERENCES users(id) ON DELETE CASCADE
);


-- 5. MANAGERS TABLE

CREATE TABLE IF NOT EXISTS managers (
    id INTEGER PRIMARY KEY,

    age INTEGER NOT NULL CHECK (age BETWEEN 3 AND 120),

    employee_id TEXT NOT NULL UNIQUE,

    dept TEXT,

    salary REAL,

    FOREIGN KEY (id)
        REFERENCES users(id) ON DELETE CASCADE
);


-- 6. APPOINTMENTS TABLE

CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    patient_id INTEGER NOT NULL,

    doctor_id INTEGER,

    receptionist_id INTEGER,

    specialization TEXT NOT NULL,

    appointment_date TEXT NOT NULL,

    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (
            status IN (
                'pending',
                'confirmed',
                'completed',
                'cancelled'
            )
        ),

    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (patient_id)
        REFERENCES patients(id),

    FOREIGN KEY (doctor_id)
        REFERENCES doctors(id),

    FOREIGN KEY (receptionist_id)
        REFERENCES receptionists(id)
);


-- 7. DOCTOR-PATIENT ASSIGNMENTS TABLE

CREATE TABLE IF NOT EXISTS doctor_patient_assignments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    doctor_id INTEGER NOT NULL,

    patient_id INTEGER NOT NULL,

    assigned_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    is_active INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0, 1)),

    FOREIGN KEY (doctor_id)
        REFERENCES doctors(id),

    FOREIGN KEY (patient_id)
        REFERENCES patients(id),

    UNIQUE (doctor_id, patient_id)
);


-- 9. MEDICAL RECORDS TABLE

CREATE TABLE IF NOT EXISTS medical_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    patient_id INTEGER NOT NULL,

    doctor_id INTEGER NOT NULL,

    appointment_id INTEGER,

    diagnosis TEXT,

    symptoms TEXT,

    prescription TEXT,

    doctor_notes TEXT,

    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (patient_id)
        REFERENCES patients(id),

    FOREIGN KEY (doctor_id)
        REFERENCES doctors(id),

    FOREIGN KEY (appointment_id)
        REFERENCES appointments(id)
);

-- 9.
CREATE TABLE IF NOT EXISTS patient_summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    doctor_id INTEGER NOT NULL,
    summary_json TEXT NOT NULL,
    generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id) REFERENCES doctors(id)
);

-- 10. INDEXES

CREATE INDEX IF NOT EXISTS idx_users_email
ON users(email);

CREATE INDEX IF NOT EXISTS idx_users_name
ON users(name);

CREATE INDEX IF NOT EXISTS idx_appointments_patient
ON appointments(patient_id);

CREATE INDEX IF NOT EXISTS idx_appointments_doctor
ON appointments(doctor_id);

CREATE INDEX IF NOT EXISTS idx_appointments_date
ON appointments(appointment_date);

CREATE INDEX IF NOT EXISTS idx_medical_records_patient
ON medical_records(patient_id);

CREATE INDEX IF NOT EXISTS idx_assignments_doctor
ON doctor_patient_assignments(doctor_id);

CREATE INDEX IF NOT EXISTS idx_patient_summaries_patient
ON patient_summaries(patient_id);
