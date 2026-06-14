"""
models.py — Carelix Database Models
====================================
Owner  : M1 (Backend Lead)
ORM    : SQLAlchemy (declarative base)
Dev DB : SQLite  →  switch to PostgreSQL via DATABASE_URL in .env
Version: v2 (Brevo Email)

All models are registered here and imported by app.py via:
    from models import db
    db.init_app(app)

Do NOT define routes in this file.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now() -> datetime:
    """UTC timestamp helper — used as column defaults throughout."""
    return datetime.utcnow()


# ===========================================================================
# M O D E L S
# ===========================================================================


# ---------------------------------------------------------------------------
# 1. users  (authentication layer — shared by patients, hospital staff, admin)
# ---------------------------------------------------------------------------

class User(db.Model):
    """
    Central authentication record.
    Every human actor in the system (patient, hospital_staff, admin)
    owns exactly one User row.  Domain-specific data lives in the
    sibling tables (Patient, Hospital).
    """
    __tablename__ = "users"

    id            = db.Column(db.Integer,      primary_key=True, autoincrement=True)
    role          = db.Column(db.String(20),   nullable=False)
    email         = db.Column(db.String(120),  unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256),  nullable=False)
    created_at    = db.Column(db.DateTime,     nullable=False, default=_now)

    # -- Relationships -------------------------------------------------------
    patient        = db.relationship("Patient",       back_populates="user", uselist=False, cascade="all, delete-orphan")
    hospital       = db.relationship("Hospital",      back_populates="user", uselist=False, cascade="all, delete-orphan")
    records_added  = db.relationship("MedicalRecord", back_populates="created_by_staff", foreign_keys="MedicalRecord.created_by_staff_id")

    def set_password(self, password: str) -> None:
        """Hash and store a plain-text password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Return True if the plain-text password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User id={self.id} role={self.role} email={self.email}>"


# ---------------------------------------------------------------------------
# 2. patients
# ---------------------------------------------------------------------------

class Patient(db.Model):
    """
    Full patient profile.
    Emergency-critical fields (blood_type, allergies, emergency_contact_*)
    are intentionally kept at the top of the column list for quick
    developer readability.
    """
    __tablename__ = "patients"

    id                      = db.Column(db.Integer,     primary_key=True, autoincrement=True)
    user_id                 = db.Column(db.Integer,     db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # -- Identity ------------------------------------------------------------
    full_name               = db.Column(db.String(120), nullable=False)
    date_of_birth           = db.Column(db.Date,        nullable=False)
    gender                  = db.Column(db.String(10),  nullable=True)
    photo_url               = db.Column(db.String(256), nullable=True)

    # -- Medical summary (emergency-critical) --------------------------------
    blood_type              = db.Column(db.String(5),   nullable=True)   # e.g. A+, O-
    genotype                = db.Column(db.String(5),   nullable=True)   # AA, AS, SS …
    allergies               = db.Column(db.Text,        nullable=True)   # comma-separated or JSON
    chronic_conditions      = db.Column(db.Text,        nullable=True)
    current_medications     = db.Column(db.Text,        nullable=True)

    # -- Emergency code (unique, server-generated) ---------------------------
    emergency_code          = db.Column(db.String(9),   unique=True, nullable=False, index=True)  # e.g. 84729-XKP

    # -- Emergency contact ---------------------------------------------------
    emergency_contact_name  = db.Column(db.String(120), nullable=False)
    emergency_contact_email = db.Column(db.String(120), nullable=False)  # Brevo alert target
    emergency_contact_phone = db.Column(db.String(15),  nullable=True)   # optional fallback / display only

    # -- Biometrics ----------------------------------------------------------
    fingerprint_credential_id = db.Column(db.Text,     nullable=True)   # WebAuthn credential ID
    fingerprint_template      = db.Column(db.LargeBinary, nullable=True) # hospital-scanned raw template (BYTEA)

    # -- Relationships -------------------------------------------------------
    user            = db.relationship("User",          back_populates="patient")
    appointments    = db.relationship("Appointment",   back_populates="patient",    cascade="all, delete-orphan")
    hospital_cards  = db.relationship("HospitalCard",  back_populates="patient",    cascade="all, delete-orphan")
    medical_records = db.relationship("MedicalRecord", back_populates="patient",    cascade="all, delete-orphan")
    opay_payments   = db.relationship("OPayPayment",   back_populates="patient",    cascade="all, delete-orphan")
    alert_logs      = db.relationship("AlertLog",      back_populates="patient",    cascade="all, delete-orphan")
    hospital_enrolments = db.relationship("HospitalEnrolment", back_populates="patient", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Patient id={self.id} code={self.emergency_code} name={self.full_name}>"


# ---------------------------------------------------------------------------
# 3. hospitals
# ---------------------------------------------------------------------------

class Hospital(db.Model):
    """
    Subscribed hospital / clinic.
    Requires admin approval (verified=True) before staff can log in.
    """
    __tablename__ = "hospitals"

    id                  = db.Column(db.Integer,      primary_key=True, autoincrement=True)
    user_id             = db.Column(db.Integer,      db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    # -- Identity & contact --------------------------------------------------
    name                = db.Column(db.String(200),  nullable=False)
    address             = db.Column(db.Text,         nullable=False)
    phone               = db.Column(db.String(15),   nullable=True)

    # -- Regulatory ----------------------------------------------------------
    cac_number          = db.Column(db.String(50),   nullable=False)   # Nigerian CAC registration

    # -- Payment settlement --------------------------------------------------
    opay_account_number = db.Column(db.String(20),   nullable=False)   # 10-digit OPay account
    opay_account_name   = db.Column(db.String(120),  nullable=False)
    card_price          = db.Column(db.Numeric(10, 2), nullable=False) # NGN price for hospital card

    # -- Admin gate ----------------------------------------------------------
    verified            = db.Column(db.Boolean,      nullable=False, default=False)

    # -- Relationships -------------------------------------------------------
    user            = db.relationship("User",          back_populates="hospital")
    doctors         = db.relationship("Doctor",        back_populates="hospital",   cascade="all, delete-orphan")
    appointments    = db.relationship("Appointment",   back_populates="hospital",   cascade="all, delete-orphan")
    hospital_cards  = db.relationship("HospitalCard",  back_populates="hospital",   cascade="all, delete-orphan")
    medical_records = db.relationship("MedicalRecord", back_populates="hospital",   cascade="all, delete-orphan")
    opay_payments   = db.relationship("OPayPayment",   back_populates="hospital",   cascade="all, delete-orphan")
    alert_logs      = db.relationship("AlertLog",      back_populates="hospital",   cascade="all, delete-orphan")
    hospital_enrolments = db.relationship("HospitalEnrolment", back_populates="hospital", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Hospital id={self.id} name={self.name} verified={self.verified}>"


# ---------------------------------------------------------------------------
# 4. doctors
# ---------------------------------------------------------------------------

class Doctor(db.Model):
    """
    A doctor listed by a hospital.
    Availability is encoded as comma-separated days + a time window.
    Slot generation happens at runtime in M2 booking logic.
    """
    __tablename__ = "doctors"

    id                     = db.Column(db.Integer,    primary_key=True, autoincrement=True)
    hospital_id            = db.Column(db.Integer,    db.ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False, index=True)

    # -- Profile -------------------------------------------------------------
    name                   = db.Column(db.String(120), nullable=False)
    specialty              = db.Column(db.String(100), nullable=False)  # e.g. Cardiology

    # -- Availability --------------------------------------------------------
    available_days         = db.Column(db.String(50),  nullable=False)  # e.g. 'Mon,Wed,Fri'
    start_time             = db.Column(db.Time,         nullable=False)  # e.g. 08:00
    end_time               = db.Column(db.Time,         nullable=False)  # e.g. 17:00
    slot_duration_mins     = db.Column(db.Integer,      nullable=False, default=30)
    max_daily_appointments = db.Column(db.Integer,      nullable=False, default=20)

    # -- Relationships -------------------------------------------------------
    hospital        = db.relationship("Hospital",      back_populates="doctors")
    appointments    = db.relationship("Appointment",   back_populates="doctor",  cascade="all, delete-orphan")
    medical_records = db.relationship("MedicalRecord", back_populates="doctor")

    def __repr__(self) -> str:
        return f"<Doctor id={self.id} name={self.name} specialty={self.specialty}>"


# ---------------------------------------------------------------------------
# 5. appointments
# ---------------------------------------------------------------------------

class Appointment(db.Model):
    """
    A patient-booked slot with a doctor at a hospital.
    Conflict detection (double-booking) is enforced at the route level (M2).
    """
    __tablename__ = "appointments"

    # Valid status values
    STATUS_PENDING   = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"

    id                   = db.Column(db.Integer,    primary_key=True, autoincrement=True)
    patient_id           = db.Column(db.Integer,    db.ForeignKey("patients.id",  ondelete="CASCADE"), nullable=False, index=True)
    doctor_id            = db.Column(db.Integer,    db.ForeignKey("doctors.id",   ondelete="SET NULL"), nullable=True,  index=True)
    hospital_id          = db.Column(db.Integer,    db.ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False, index=True)

    appointment_datetime = db.Column(db.DateTime,   nullable=False)
    status               = db.Column(db.String(20), nullable=False, default=STATUS_PENDING)
    reason               = db.Column(db.Text,       nullable=True)
    created_at           = db.Column(db.DateTime,   nullable=False, default=_now)

    # -- Relationships -------------------------------------------------------
    patient  = db.relationship("Patient",  back_populates="appointments")
    doctor   = db.relationship("Doctor",   back_populates="appointments")
    hospital = db.relationship("Hospital", back_populates="appointments")

    def __repr__(self) -> str:
        return f"<Appointment id={self.id} patient={self.patient_id} dt={self.appointment_datetime} status={self.status}>"


# ---------------------------------------------------------------------------
# 6. hospital_cards
# ---------------------------------------------------------------------------

class HospitalCard(db.Model):
    """
    Issued to a patient upon successful OPay payment.
    Activated automatically via /pay/webhook (M4).
    One patient can hold cards for multiple hospitals (post-MVP feature;
    schema supports it today).
    """
    __tablename__ = "hospital_cards"

    STATUS_PENDING = "pending"
    STATUS_ACTIVE  = "active"
    STATUS_REVOKED = "revoked"

    id                 = db.Column(db.Integer,     primary_key=True, autoincrement=True)
    patient_id         = db.Column(db.Integer,     db.ForeignKey("patients.id",  ondelete="CASCADE"), nullable=False, index=True)
    hospital_id        = db.Column(db.Integer,     db.ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False, index=True)

    payment_reference  = db.Column(db.String(100), nullable=False, unique=True)   # OPay transaction ref
    status             = db.Column(db.String(20),  nullable=False, default=STATUS_PENDING)
    issued_at          = db.Column(db.DateTime,    nullable=True)                  # set when webhook confirms
    expires_at         = db.Column(db.DateTime,    nullable=True)                  # optional 1-year validity

    # -- Relationships -------------------------------------------------------
    patient  = db.relationship("Patient",  back_populates="hospital_cards")
    hospital = db.relationship("Hospital", back_populates="hospital_cards")

    def __repr__(self) -> str:
        return f"<HospitalCard id={self.id} patient={self.patient_id} hospital={self.hospital_id} status={self.status}>"


# ---------------------------------------------------------------------------
# 7. medical_records
# ---------------------------------------------------------------------------

class MedicalRecord(db.Model):
    """
    Clinical notes added by hospital staff after a patient visit.
    Patients can VIEW these (read-only via M3); only staff can CREATE/UPDATE.
    test_results stores JSON for structured lab data or plain text.
    """
    __tablename__ = "medical_records"

    id                  = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id          = db.Column(db.Integer, db.ForeignKey("patients.id",  ondelete="CASCADE"), nullable=False, index=True)
    hospital_id         = db.Column(db.Integer, db.ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False, index=True)
    doctor_id           = db.Column(db.Integer, db.ForeignKey("doctors.id",   ondelete="SET NULL"), nullable=True,  index=True)
    created_by_staff_id = db.Column(db.Integer, db.ForeignKey("users.id",     ondelete="SET NULL"), nullable=True)

    visit_date   = db.Column(db.Date,     nullable=False)
    diagnosis    = db.Column(db.Text,     nullable=True)
    prescription = db.Column(db.Text,     nullable=True)
    test_results = db.Column(db.Text,     nullable=True)  # plain text or serialised JSON
    notes        = db.Column(db.Text,     nullable=True)
    created_at   = db.Column(db.DateTime, nullable=False, default=_now)

    # -- Relationships -------------------------------------------------------
    patient          = db.relationship("Patient",  back_populates="medical_records")
    hospital         = db.relationship("Hospital", back_populates="medical_records")
    doctor           = db.relationship("Doctor",   back_populates="medical_records")
    created_by_staff = db.relationship("User",     back_populates="records_added", foreign_keys=[created_by_staff_id])

    def __repr__(self) -> str:
        return f"<MedicalRecord id={self.id} patient={self.patient_id} visit={self.visit_date}>"


# ---------------------------------------------------------------------------
# 8. opay_payments
# ---------------------------------------------------------------------------
class HospitalEnrolment(db.Model):
    __tablename__ = "hospital_enrolments"

    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    patient_id  = db.Column(db.Integer, db.ForeignKey("patients.id",  ondelete="CASCADE"), nullable=False, index=True)
    hospital_id = db.Column(db.Integer, db.ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at  = db.Column(db.DateTime, nullable=False, default=_now)

    __table_args__ = (db.UniqueConstraint("patient_id", "hospital_id", name="uq_patient_hospital_enrolment"),)

    # -- Relationships -------------------------------------------------------
    patient  = db.relationship("Patient",  back_populates="hospital_enrolments")
    hospital = db.relationship("Hospital", back_populates="hospital_enrolments")

    def __repr__(self) -> str:
        return f"<HospitalEnrolment id={self.id} patient={self.patient_id} hospital={self.hospital_id}>"
class OPayPayment(db.Model):
    """
    Tracks every OPay payment attempt from initiation through webhook
    confirmation.  The raw webhook_payload is stored for audit & replay.
    HMAC verification happens in M4 before any DB update.
    """
    __tablename__ = "opay_payments"

    STATUS_INITIATED = "initiated"
    STATUS_SUCCESS   = "success"
    STATUS_FAILED    = "failed"

    id              = db.Column(db.Integer,      primary_key=True, autoincrement=True)
    patient_id      = db.Column(db.Integer,      db.ForeignKey("patients.id",  ondelete="CASCADE"), nullable=False, index=True)
    hospital_id     = db.Column(db.Integer,      db.ForeignKey("hospitals.id", ondelete="CASCADE"), nullable=False, index=True)

    amount          = db.Column(db.Numeric(10, 2), nullable=False)              # NGN
    reference       = db.Column(db.String(100),    nullable=False, unique=True) # unique OPay ref
    status          = db.Column(db.String(20),     nullable=False, default=STATUS_INITIATED)
    opay_order_no   = db.Column(db.String(100),    nullable=True)               # returned by OPay API
    webhook_payload = db.Column(db.Text,           nullable=True)               # raw JSON — audit only
    created_at      = db.Column(db.DateTime,       nullable=False, default=_now)
    confirmed_at    = db.Column(db.DateTime,       nullable=True)               # set on webhook success

    # -- Relationships -------------------------------------------------------
    patient  = db.relationship("Patient",  back_populates="opay_payments")
    hospital = db.relationship("Hospital", back_populates="opay_payments")

    def __repr__(self) -> str:
        return f"<OPayPayment id={self.id} ref={self.reference} status={self.status}>"


# ---------------------------------------------------------------------------
# 9. alert_logs
# ---------------------------------------------------------------------------

class AlertLog(db.Model):
    """
    Immutable audit trail of every Brevo email alert fired when an emergency
    profile is accessed (M2 calls utils.send_alert_email → logs here).
    Never delete rows; this table is append-only for compliance.
    """
    __tablename__ = "alert_logs"

    STATUS_SENT   = "sent"
    STATUS_FAILED = "failed"

    id                = db.Column(db.Integer,     primary_key=True, autoincrement=True)
    patient_id        = db.Column(db.Integer,     db.ForeignKey("patients.id",  ondelete="SET NULL"), nullable=True,  index=True)
    hospital_id       = db.Column(db.Integer,     db.ForeignKey("hospitals.id", ondelete="SET NULL"), nullable=True,  index=True)

    # -- Recipient snapshot (denormalised intentionally for audit integrity) --
    recipient_email   = db.Column(db.String(120), nullable=False)   # emergency contact email
    recipient_name    = db.Column(db.String(120), nullable=True)    # emergency contact name

    # -- Email content snapshot ----------------------------------------------
    subject           = db.Column(db.String(200), nullable=False)
    message_html      = db.Column(db.Text,        nullable=False)   # full HTML body sent

    # -- Delivery tracking ---------------------------------------------------
    brevo_message_id  = db.Column(db.String(100), nullable=True)    # returned by Brevo API
    status            = db.Column(db.String(20),  nullable=False, default=STATUS_SENT)
    sent_at           = db.Column(db.DateTime,    nullable=False, default=_now)

    # -- Relationships -------------------------------------------------------
    patient  = db.relationship("Patient",  back_populates="alert_logs")
    hospital = db.relationship("Hospital", back_populates="alert_logs")

    def __repr__(self) -> str:
        return f"<AlertLog id={self.id} patient={self.patient_id} status={self.status} sent={self.sent_at}>"