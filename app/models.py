from dataclasses import dataclass
from pydantic import BaseModel, field_validator, EmailStr, Field
from typing import Optional
from datetime import date, datetime
from enum import Enum


# ENUMS
class UserRole(str, Enum):
    PATIENT = "patient"
    DOCTOR = "doctor"
    RECEPTIONIST = "receptionist"
    MANAGER = "manager"


class AppointmentStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


# BASE PERSON CLASS
class Person(BaseModel):
    """Base class defining common person information."""

    name: str
    password: str
    email: EmailStr
    phone: str
    age: int

    @field_validator("age")
    @classmethod
    def validate_age(cls, age):
        age = int(age)
        if not 3 <= age <= 120:
            raise ValueError("Age not in the acceptance region [3, 120]")
        return age


# EMPLOYEE CLASS
class Employee(Person):
    """Base class for all hospital employees."""

    dept: str
    salary: float | None = None


# MANAGER CLASS
class Manager(Employee):
    """Structure of payload required when a manager is created."""

    employee_id: str


class ManagerResponse(BaseModel):
    """Manager information returned by the API."""

    id: int
    name: str
    email: EmailStr
    phone: str
    employee_id: str
    dept: Optional[str] = None
    salary: Optional[float] = None


# PATIENT CLASS
class Patient(Person):
    """Structure of payload required when a patient is created."""

    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None

    allergies: Optional[str] = None
    existing_conditions: Optional[str] = None
    emergency_contact: Optional[str] = None


class PatientResponse(BaseModel):
    """Patient information returned by the API."""

    id: int
    name: str
    email: EmailStr
    phone: str
    age: Optional[int] = None

    gender: Optional[str] = None
    blood_group: Optional[str] = None
    address: Optional[str] = None

    allergies: Optional[str] = None
    existing_conditions: Optional[str] = None
    emergency_contact: Optional[str] = None


# DOCTOR CLASS
class Doctor(Employee):
    """Structure of payload required when a doctor is created."""

    specialization: str

    max_patients: int = Field(default=20, gt=0)

    qualification: Optional[str] = None


class DoctorResponse(BaseModel):
    """Doctor information returned by the API."""

    id: int
    name: str
    email: EmailStr
    phone: str

    dept: str
    specialization: str

    max_patients: int

    qualification: Optional[str] = None


# RECEPTIONIST CLASS
class Receptionist(Employee):
    """Structure of payload required when a receptionist is created."""

    employee_id: str


class ReceptionistResponse(BaseModel):
    """Receptionist information returned by the API."""

    id: int
    name: str
    email: EmailStr
    phone: str
    employee_id: str

    dept: Optional[str] = None
    salary: Optional[float] = None


# APPOINTMENT MODELS
class AppointmentCreate(BaseModel):
    """Payload received when a patient requests an appointment."""

    specialization: str = Field(min_length=2, max_length=100)
    appointment_date: datetime


class AppointmentAssign(BaseModel):
    """Payload used by the receptionist to assign a doctor."""

    doctor_id: int = Field(gt=0)


class AppointmentResponse(BaseModel):
    """Appointment information returned by the API."""

    id: int
    patient_id: int
    doctor_id: Optional[int] = None
    receptionist_id: Optional[int] = None

    specialization: str
    appointment_date: datetime

    status: AppointmentStatus

    created_at: Optional[datetime] = None


class AppointmentStatusUpdate(BaseModel):
    """Payload used by a doctor to update appointment status."""

    status: AppointmentStatus


# DOCTOR-PATIENT ASSIGNMENT MODELS
class AssignmentCreate(BaseModel):
    doctor_id: int
    patient_id: int


class AssignmentResponse(BaseModel):
    id: int
    doctor_id: int
    patient_id: int

    assigned_at: Optional[datetime] = None

    is_active: bool


# MEDICAL RECORD MODELS
class MedicalRecordCreate(BaseModel):
    """Payload for creating a patient's medical record."""

    patient_id: int

    appointment_id: Optional[int] = None

    diagnosis: Optional[str] = None
    symptoms: Optional[str] = None
    prescription: Optional[str] = None
    doctor_notes: Optional[str] = None


class MedicalRecordResponse(BaseModel):
    """Medical record information returned by the API."""

    id: int

    patient_id: int
    doctor_id: int

    appointment_id: Optional[int] = None

    diagnosis: Optional[str] = None
    symptoms: Optional[str] = None
    prescription: Optional[str] = None
    doctor_notes: Optional[str] = None

    recorded_at: Optional[datetime] = None


# MANAGER AUTHORIZATION MODEL
class ManagerInfo(BaseModel):
    """
    Structure used when sending privileged requests
    on routes that a manager can access.
    """

    id: str
    passcode: str


# ACCESS TOKEN CREATION MODELS
class PasswordRequest(BaseModel):
    password: str


class TokenCreationRequest(BaseModel):
    id: str
    r: int = 1
    rw: int = 0
    days: Optional[int] = None
    revoke_on_request: int = 0

    @field_validator("r")
    @classmethod
    def isvalid_r(cls, v: int):
        if v not in (0, 1):
            raise ValueError("r is either 0 or 1")
        return v

    @field_validator("rw")
    @classmethod
    def rw_must_be_0_or_1(cls, v: int):
        if v not in (0, 1):
            raise ValueError("rw must be 0 or 1")
        return v


# PAT REVOCATION MODEL
class PATRevokeRequest(BaseModel):
    """PAT revocation request payload structure."""

    id: str
    password: str


# PAYMENT MODEL
class PaymentRequest(BaseModel):
    card_no: str
    cvv: str
    expiry: tuple[int, int]  # (MM, YYYY)

    @field_validator("expiry")
    @classmethod
    def validate_expiry(cls, value: tuple[int, int]) -> tuple[int, int]:

        month, year = value

        if month not in range(1, 13):
            raise ValueError("Invalid Month Specified")

        today = date.today()

        if year < today.year or (year == today.year and month < today.month):
            raise ValueError("Card has Expired")

        return (month, year)


# JWT Endpoints
class LoginRequest(BaseModel):
    id: int
    password: str = Field(min_length=1, max_length=72)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    id: int


# LLM Output Validation
class PatientSummary(BaseModel):
    """
    We explicity give the LLM instructions to return the answer in this format to us.
    """

    patient_id: str
    generated_summary: str
    known_allergies: list[str] = Field(default_factory=list)
    current_medications: list[str] = Field(default_factory=list)
    relevant_history: list[str] = Field(default_factory=list)
    recent_events: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    clinician_review_required: bool
