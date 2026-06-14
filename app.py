import os
import random
import string
from datetime import datetime, date, time as dtime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, flash, session
from model import db, User, Patient, Hospital, Doctor, Appointment, MedicalRecord, AlertLog, HospitalEnrolment, HospitalCard
from utils import send_alert_email
# ── App factory ───────────────────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "carelix-dev-secret-change-in-prod")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///carelix.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

with app.app_context():
    db.create_all()


# ── Helpers ───────────────────────────────────────────────────────────────────

def generate_emergency_code() -> str:
    """Generate a unique 5-digit + 3-uppercase-letter code e.g. 84729-XKP."""
    while True:
        digits  = "".join(random.choices(string.digits, k=5))
        letters = "".join(random.choices(string.ascii_uppercase, k=3))
        code    = f"{digits}-{letters}"
        if not Patient.query.filter_by(emergency_code=code).first():
            return code


def login_required(role=None):
    """Decorator: require login, optionally for a specific role."""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                flash("Please log in to continue.", "error")
                return redirect(url_for("index"))
            if role and session.get("role") != role:
                flash("You do not have access to that page.", "error")
                return redirect(url_for("index"))
            return f(*args, **kwargs)
        return wrapper
    return decorator


def current_patient():
    user = User.query.get(session.get("user_id"))
    return user.patient if user else None


def current_hospital():
    user = User.query.get(session.get("user_id"))
    return user.hospital if user else None


# ── Landing ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── Register choice page ──────────────────────────────────────────────────────

@app.route("/register")
def register_choice():
    return render_template("register_choice.html")


# ═════════════════════════════════════════════════════════════════════════════
# PATIENT ROUTES
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/patient/register", methods=["GET", "POST"])
def patient_register():
    if request.method == "GET":
        return render_template("patientregister.html")

    # ── Collect form data ────────────────────────────────────────────────
    first_name   = request.form.get("first_name", "").strip()
    last_name    = request.form.get("last_name",  "").strip()
    email        = request.form.get("email",      "").strip().lower()
    password     = request.form.get("password",   "")
    confirm_pw   = request.form.get("confirm_password", "")
    dob_str      = request.form.get("date_of_birth", "")
    gender       = request.form.get("gender",     "")
    blood_type   = request.form.get("blood_type", "")
    genotype     = request.form.get("genotype",   "")
    allergies    = request.form.get("allergies",  "")
    conditions   = request.form.get("chronic_conditions",  "")
    medications  = request.form.get("current_medications", "")
    ec_name      = request.form.get("emergency_contact_name",  "").strip()
    ec_email     = request.form.get("emergency_contact_email", "").strip().lower()
    ec_phone     = request.form.get("emergency_contact_phone", "").strip()

    # ── Validation ───────────────────────────────────────────────────────
    errors = []
    if not all([first_name, last_name, email, password, dob_str, ec_name, ec_email]):
        errors.append("Please fill in all required fields.")
    if password != confirm_pw:
        errors.append("Passwords do not match.")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if User.query.filter_by(email=email).first():
        errors.append("An account with this email already exists.")

    if errors:
        for e in errors:
            flash(e, "error")
        return render_template("patientregister.html")

    # ── Parse date ───────────────────────────────────────────────────────
    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
    except ValueError:
        flash("Invalid date of birth.", "error")
        return render_template("patientregister.html")

    # ── Create User + Patient rows ────────────────────────────────────────
    user = User(role="patient", email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()   # get user.id before commit

    patient = Patient(
        user_id                 = user.id,
        full_name               = f"{first_name} {last_name}",
        date_of_birth           = dob,
        gender                  = gender,
        blood_type              = blood_type,
        genotype                = genotype,
        allergies               = allergies,
        chronic_conditions      = conditions,
        current_medications     = medications,
        emergency_code          = generate_emergency_code(),
        emergency_contact_name  = ec_name,
        emergency_contact_email = ec_email,
        emergency_contact_phone = ec_phone,
    )
    db.session.add(patient)
    db.session.commit()

    # Store the code in the session so the success page can display it once
    session["new_emergency_code"] = patient.emergency_code
    session["new_patient_name"]   = patient.full_name
    return redirect(url_for("patient_register_success"))


@app.route("/patient/register/success")
def patient_register_success():
    """Show the newly generated emergency code once, then clear it from session."""
    code = session.pop("new_emergency_code", None)
    name = session.pop("new_patient_name",   None)
    if not code:
        # Guard against direct URL access with no session data
        return redirect(url_for("index"))
    return render_template("patient_register_success.html", emergency_code=code, patient_name=name)


@app.route("/patient/login", methods=["GET", "POST"])
def patient_login():
    """Patient login — email + password authentication."""
    if request.method == "GET":
        if session.get("role") == "patient":
            return redirect(url_for("patient_dashboard"))
        return render_template("patientlogin.html")

    # ── Collect form data ────────────────────────────────────────────────
    email    = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    remember = request.form.get("remember")

    # ── Validation ───────────────────────────────────────────────────────
    if not all([email, password]):
        flash("Please provide both email and password.", "error")
        return render_template("patientlogin.html")

    # ── Authenticate ─────────────────────────────────────────────────────
    user = User.query.filter_by(email=email, role="patient").first()
    if not user or not user.check_password(password):
        flash("Invalid email or password.", "error")
        return render_template("patientlogin.html")

    # ── Store session ────────────────────────────────────────────────────
    session["user_id"] = user.id
    session["role"] = "patient"
    if remember:
        session.permanent = True

    flash(f"Welcome back, {user.patient.full_name.split()[0]}!", "success")
    return redirect(url_for("patient_dashboard"))


# ── Patient dashboard ──────────────────────────────────────────────────────────

@app.route("/patient/dashboard")
@login_required(role="patient")
def patient_dashboard():
    patient = current_patient()

    appointments = (
        Appointment.query
        .filter_by(patient_id=patient.id)
        .order_by(Appointment.appointment_datetime.desc())
        .all()
    )

    now = datetime.utcnow()
    upcoming_appointments = [
        a for a in appointments
        if a.appointment_datetime >= now and a.status in ("pending", "confirmed")
    ]
    upcoming_appointments.sort(key=lambda a: a.appointment_datetime)

    records = (
        MedicalRecord.query
        .filter_by(patient_id=patient.id)
        .order_by(MedicalRecord.visit_date.desc())
        .all()
    )

    alerts = (
        AlertLog.query
        .filter_by(patient_id=patient.id)
        .order_by(AlertLog.sent_at.desc())
        .all()
    )

    hospitals = Hospital.query.order_by(Hospital.name).all()
    doctors   = Doctor.query.join(Hospital).order_by(Doctor.name).all()

    # ── Hospitals this patient is registered under ──────────────────────
    enrolments = HospitalEnrolment.query.filter_by(patient_id=patient.id).all()
    my_hospitals = []
    for e in enrolments:
        h = e.hospital
        card = HospitalCard.query.filter_by(patient_id=patient.id, hospital_id=h.id).first()
        card_status = card.status if card else None
        my_hospitals.append({
            "id": h.id,
            "name": h.name,
            "address": h.address,
            "phone": h.phone,
            "card_price": h.card_price,
            "card_status": card_status,
        })

    # ── Profile completeness ────────────────────────────────────────────
    fields_to_check = [
        patient.full_name, patient.date_of_birth, patient.gender,
        patient.blood_type, patient.genotype, patient.allergies,
        patient.chronic_conditions, patient.current_medications,
        patient.emergency_contact_name, patient.emergency_contact_email,
        patient.emergency_contact_phone,
    ]
    filled = sum(1 for f in fields_to_check if f)
    profile_completeness = round((filled / len(fields_to_check)) * 100)

    return render_template(
        "patient_dashboard.html",
        patient=patient,
        appointments=appointments,
        upcoming_appointments=upcoming_appointments,
        upcoming_count=len(upcoming_appointments),
        records=records,
        alerts=alerts,
        hospitals=hospitals,
        doctors=doctors,
        my_hospitals=my_hospitals,
        profile_completeness=profile_completeness,
        today=date.today().isoformat(),
    )


@app.route("/patient/book", methods=["POST"])
@login_required(role="patient")
def patient_book_appointment():
    patient = current_patient()

    hospital_id = request.form.get("hospital_id", "")
    doctor_id   = request.form.get("doctor_id", "")
    appt_date   = request.form.get("appointment_date", "")
    appt_time   = request.form.get("appointment_time", "")
    reason      = request.form.get("reason", "").strip()

    if not hospital_id or not appt_date or not appt_time:
        flash("Please fill in all required fields.", "error")
        return redirect(url_for("patient_dashboard") + "#book")

    hospital = Hospital.query.get(int(hospital_id))
    if not hospital:
        flash("Selected hospital not found.", "error")
        return redirect(url_for("patient_dashboard") + "#book")

    doctor = None
    if doctor_id:
        doctor = Doctor.query.get(int(doctor_id))
        if not doctor or doctor.hospital_id != hospital.id:
            flash("Selected doctor does not belong to that hospital.", "error")
            return redirect(url_for("patient_dashboard") + "#book")

    try:
        appointment_dt = datetime.strptime(f"{appt_date} {appt_time}", "%Y-%m-%d %H:%M")
    except ValueError:
        flash("Invalid date or time.", "error")
        return redirect(url_for("patient_dashboard") + "#book")

    if appointment_dt < datetime.utcnow():
        flash("Appointment time must be in the future.", "error")
        return redirect(url_for("patient_dashboard") + "#book")

    # ── Conflict check ───────────────────────────────────────────────────
    if doctor:
        clash = Appointment.query.filter(
            Appointment.doctor_id == doctor.id,
            Appointment.appointment_datetime == appointment_dt,
            Appointment.status.in_(["pending", "confirmed"]),
        ).first()
        if clash:
            flash("That doctor already has an appointment at this time. Please choose another slot.", "error")
            return redirect(url_for("patient_dashboard") + "#book")

        # ── Daily limit check ───────────────────────────────────────────
        day_start = datetime.combine(appointment_dt.date(), dtime.min)
        day_end   = datetime.combine(appointment_dt.date(), dtime.max)
        day_count = Appointment.query.filter(
            Appointment.doctor_id == doctor.id,
            Appointment.appointment_datetime.between(day_start, day_end),
            Appointment.status.in_(["pending", "confirmed"]),
        ).count()
        if day_count >= doctor.max_daily_appointments:
            flash(f"Dr. {doctor.name} has reached the maximum appointments for that day. Please choose another date.", "error")
            return redirect(url_for("patient_dashboard") + "#book")

    appointment = Appointment(
        patient_id           = patient.id,
        doctor_id            = doctor.id if doctor else None,
        hospital_id          = hospital.id,
        appointment_datetime = appointment_dt,
        status               = Appointment.STATUS_PENDING,
        reason               = reason,
    )
    db.session.add(appointment)
    db.session.commit()

    flash("Appointment booked successfully! Awaiting hospital confirmation.", "success")
    return redirect(url_for("patient_dashboard") + "#appointments")


@app.route("/patient/appointment/<int:appt_id>/cancel", methods=["POST"])
@login_required(role="patient")
def patient_cancel_appointment(appt_id):
    patient = current_patient()
    appt = Appointment.query.get(appt_id)

    if not appt or appt.patient_id != patient.id:
        flash("Appointment not found.", "error")
        return redirect(url_for("patient_dashboard") + "#appointments")

    if appt.status not in (Appointment.STATUS_PENDING, Appointment.STATUS_CONFIRMED):
        flash("This appointment cannot be cancelled.", "error")
        return redirect(url_for("patient_dashboard") + "#appointments")

    appt.status = Appointment.STATUS_CANCELLED
    db.session.commit()
    flash("Appointment cancelled.", "success")
    return redirect(url_for("patient_dashboard") + "#appointments")


@app.route("/patient/profile", methods=["POST"])
@login_required(role="patient")
def patient_update_profile():
    patient = current_patient()

    full_name = request.form.get("full_name", "").strip()
    dob_str   = request.form.get("date_of_birth", "")
    ec_name   = request.form.get("emergency_contact_name", "").strip()
    ec_email  = request.form.get("emergency_contact_email", "").strip().lower()

    if not all([full_name, dob_str, ec_name, ec_email]):
        flash("Please fill in all required fields.", "error")
        return redirect(url_for("patient_dashboard") + "#profile")

    try:
        dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
    except ValueError:
        flash("Invalid date of birth.", "error")
        return redirect(url_for("patient_dashboard") + "#profile")

    patient.full_name               = full_name
    patient.date_of_birth           = dob
    patient.gender                  = request.form.get("gender", "")
    patient.blood_type              = request.form.get("blood_type", "")
    patient.genotype                = request.form.get("genotype", "")
    patient.allergies               = request.form.get("allergies", "")
    patient.chronic_conditions      = request.form.get("chronic_conditions", "")
    patient.current_medications     = request.form.get("current_medications", "")
    patient.emergency_contact_name  = ec_name
    patient.emergency_contact_email = ec_email
    patient.emergency_contact_phone = request.form.get("emergency_contact_phone", "").strip()

    db.session.commit()
    flash("Profile updated successfully.", "success")
    return redirect(url_for("patient_dashboard") + "#profile")


# ═════════════════════════════════════════════════════════════════════════════
# HOSPITAL ROUTES
# ═════════════════════════════════════════════════════════════════════════════

@app.route("/hospital/register", methods=["GET", "POST"])
def hospital_register():
    if request.method == "GET":
        return render_template("hospitalregister.html")

    # ── Collect form data ────────────────────────────────────────────────
    hospital_name       = request.form.get("hospital_name",       "").strip()
    cac_number          = request.form.get("cac_number",          "").strip()
    address             = request.form.get("address",             "").strip()
    card_price          = request.form.get("card_price",          "0").strip()
    phone               = request.form.get("phone",               "").strip()
    opay_account_number = request.form.get("opay_account_number", "").strip()
    opay_account_name   = request.form.get("opay_account_name",   "").strip()
    email               = request.form.get("email",               "").strip().lower()
    password            = request.form.get("password",            "")
    confirm_pw          = request.form.get("confirm_password",    "")

    # ── Validation ───────────────────────────────────────────────────────
    errors = []
    if not all([hospital_name, cac_number, address, card_price,
                phone, opay_account_number, opay_account_name, email, password]):
        errors.append("Please fill in all required fields.")
    if password != confirm_pw:
        errors.append("Passwords do not match.")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if User.query.filter_by(email=email).first():
        errors.append("An account with this email already exists.")

    if errors:
        for e in errors:
            flash(e, "error")
        return render_template("hospitalregister.html")

    # ── Create User + Hospital rows ───────────────────────────────────────
    user = User(role="hospital_staff", email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    hospital = Hospital(
        user_id             = user.id,
        name                = hospital_name,
        address             = address,
        phone               = phone,
        cac_number          = cac_number,
        opay_account_number = opay_account_number,
        opay_account_name   = opay_account_name,
        card_price          = float(card_price),
        verified            = False,   # admin approves separately
    )
    db.session.add(hospital)
    db.session.commit()

    flash("Hospital registered successfully! Please log in to your dashboard.", "success")
    return redirect(url_for("hospital_login"))


@app.route("/hospital/login", methods=["GET", "POST"])
def hospital_login():
    """Hospital staff login — email + password authentication."""
    if request.method == "GET":
        if session.get("role") == "hospital_staff":
            return redirect(url_for("hospital_dashboard"))
        return render_template("hospitallogin.html")

    # ── Collect form data ────────────────────────────────────────────────
    email    = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    remember = request.form.get("remember")

    # ── Validation ───────────────────────────────────────────────────────
    if not all([email, password]):
        flash("Please provide both email and password.", "error")
        return render_template("hospitallogin.html")

    # ── Authenticate ─────────────────────────────────────────────────────
    user = User.query.filter_by(email=email, role="hospital_staff").first()
    if not user or not user.check_password(password):
        flash("Invalid email or password.", "error")
        return render_template("hospitallogin.html")

    # ── Store session ────────────────────────────────────────────────────
    session["user_id"] = user.id
    session["role"] = "hospital_staff"
    if remember:
        session.permanent = True

    flash(f"Welcome back, {user.hospital.name}!", "success")
    return redirect(url_for("hospital_dashboard"))


# ── Hospital dashboard ─────────────────────────────────────────────────────────

@app.route("/hospital/dashboard")
@login_required(role="hospital_staff")
def hospital_dashboard():
    hospital = current_hospital()

    doctors = (
        Doctor.query
        .filter_by(hospital_id=hospital.id)
        .order_by(Doctor.name)
        .all()
    )

    appointments = (
        Appointment.query
        .filter_by(hospital_id=hospital.id)
        .order_by(Appointment.appointment_datetime.desc())
        .all()
    )

    today = date.today()
    day_start = datetime.combine(today, dtime.min)
    day_end   = datetime.combine(today, dtime.max)
    today_appointments = [
        a for a in appointments
        if day_start <= a.appointment_datetime <= day_end
    ]
    today_appointments.sort(key=lambda a: a.appointment_datetime)

    medical_records = (
        MedicalRecord.query
        .filter_by(hospital_id=hospital.id)
        .order_by(MedicalRecord.visit_date.desc())
        .all()
    )

    alerts = (
        AlertLog.query
        .filter_by(hospital_id=hospital.id)
        .order_by(AlertLog.sent_at.desc())
        .all()
    )

    enrolled_patients_count = (
        db.session.query(Appointment.patient_id)
        .filter_by(hospital_id=hospital.id)
        .distinct()
        .count()
    )

    appointments_today_count = len(today_appointments)

    return render_template(
        "hospital_dashboard.html",
        hospital=hospital,
        doctors=doctors,
        appointments=appointments,
        today_appointments=today_appointments,
        medical_records=medical_records,
        alerts=alerts,
        enrolled_patients_count=enrolled_patients_count,
        appointments_today_count=appointments_today_count,
        today=date.today().isoformat(),
        search_code=None,
        search_error=None,
        searched_patient=None,
        alert_sent=False,
        show_record_modal=False,
    )


@app.route("/hospital/search")
@login_required(role="hospital_staff")
def hospital_search():
    hospital = current_hospital()
    code = request.args.get("code", "").strip().upper()

    doctors = (
        Doctor.query
        .filter_by(hospital_id=hospital.id)
        .order_by(Doctor.name)
        .all()
    )

    appointments = (
        Appointment.query
        .filter_by(hospital_id=hospital.id)
        .order_by(Appointment.appointment_datetime.desc())
        .all()
    )

    today = date.today()
    day_start = datetime.combine(today, dtime.min)
    day_end   = datetime.combine(today, dtime.max)
    today_appointments = [
        a for a in appointments
        if day_start <= a.appointment_datetime <= day_end
    ]
    today_appointments.sort(key=lambda a: a.appointment_datetime)

    medical_records = (
        MedicalRecord.query
        .filter_by(hospital_id=hospital.id)
        .order_by(MedicalRecord.visit_date.desc())
        .all()
    )

    alerts = (
        AlertLog.query
        .filter_by(hospital_id=hospital.id)
        .order_by(AlertLog.sent_at.desc())
        .all()
    )

    enrolled_patients_count = (
        db.session.query(Appointment.patient_id)
        .filter_by(hospital_id=hospital.id)
        .distinct()
        .count()
    )

    searched_patient = None
    search_error = None
    alert_sent = False

    if code:
        searched_patient = Patient.query.filter_by(emergency_code=code).first()
        if not searched_patient:
            search_error = f"No patient found with emergency code '{code}'."
        else:
            # ── Trigger the next-of-kin email alert via Brevo ──────────
            alert = send_alert_email(searched_patient, hospital)
            alert_sent = (alert.status == AlertLog.STATUS_SENT)
            # Refresh alerts list to include the new one
            alerts = (
                AlertLog.query
                .filter_by(hospital_id=hospital.id)
                .order_by(AlertLog.sent_at.desc())
                .all()
            )

    return render_template(
        "hospital_dashboard.html",
        hospital=hospital,
        doctors=doctors,
        appointments=appointments,
        today_appointments=today_appointments,
        medical_records=medical_records,
        alerts=alerts,
        enrolled_patients_count=enrolled_patients_count,
        appointments_today_count=len(today_appointments),
        today=date.today().isoformat(),
        search_code=code,
        search_error=search_error,
        searched_patient=searched_patient,
        alert_sent=alert_sent,
        show_record_modal=False,
    )


@app.route("/hospital/doctors/add", methods=["POST"])
@login_required(role="hospital_staff")
def hospital_add_doctor():
    hospital = current_hospital()

    name       = request.form.get("name", "").strip()
    specialty  = request.form.get("specialty", "").strip()
    days       = request.form.getlist("available_days")
    start_str  = request.form.get("start_time", "")
    end_str    = request.form.get("end_time", "")
    slot_mins  = request.form.get("slot_duration_mins", "30")
    max_daily  = request.form.get("max_daily_appointments", "20")

    if not all([name, specialty, days, start_str, end_str]):
        flash("Please fill in all required doctor fields.", "error")
        return redirect(url_for("hospital_dashboard") + "#doctors")

    try:
        start_time = datetime.strptime(start_str, "%H:%M").time()
        end_time   = datetime.strptime(end_str, "%H:%M").time()
    except ValueError:
        flash("Invalid time format.", "error")
        return redirect(url_for("hospital_dashboard") + "#doctors")

    if end_time <= start_time:
        flash("End time must be after start time.", "error")
        return redirect(url_for("hospital_dashboard") + "#doctors")

    doctor = Doctor(
        hospital_id            = hospital.id,
        name                   = name,
        specialty              = specialty,
        available_days         = ",".join(days),
        start_time             = start_time,
        end_time               = end_time,
        slot_duration_mins     = int(slot_mins) if slot_mins else 30,
        max_daily_appointments = int(max_daily) if max_daily else 20,
    )
    db.session.add(doctor)
    db.session.commit()

    flash(f"Dr. {name} added successfully.", "success")
    return redirect(url_for("hospital_dashboard") + "#doctors")


@app.route("/hospital/doctors/<int:doctor_id>/delete", methods=["POST"])
@login_required(role="hospital_staff")
def hospital_delete_doctor(doctor_id):
    hospital = current_hospital()
    doctor = Doctor.query.get(doctor_id)

    if not doctor or doctor.hospital_id != hospital.id:
        flash("Doctor not found.", "error")
        return redirect(url_for("hospital_dashboard") + "#doctors")

    db.session.delete(doctor)
    db.session.commit()
    flash("Doctor removed.", "success")
    return redirect(url_for("hospital_dashboard") + "#doctors")


@app.route("/hospital/appointment/<int:appt_id>/status", methods=["POST"])
@login_required(role="hospital_staff")
def hospital_update_appointment_status(appt_id):
    hospital = current_hospital()
    appt = Appointment.query.get(appt_id)
    new_status = request.form.get("status", "")

    if not appt or appt.hospital_id != hospital.id:
        flash("Appointment not found.", "error")
        return redirect(url_for("hospital_dashboard") + "#appointments")

    valid_statuses = [
        Appointment.STATUS_PENDING, Appointment.STATUS_CONFIRMED,
        Appointment.STATUS_COMPLETED, Appointment.STATUS_CANCELLED,
    ]
    if new_status not in valid_statuses:
        flash("Invalid status.", "error")
        return redirect(url_for("hospital_dashboard") + "#appointments")

    appt.status = new_status
    db.session.commit()
    flash(f"Appointment marked as {new_status}.", "success")
    return redirect(url_for("hospital_dashboard") + "#appointments")


@app.route("/hospital/records/add", methods=["POST"])
@login_required(role="hospital_staff")
def hospital_add_record():
    hospital = current_hospital()

    patient_id   = request.form.get("patient_id", "")
    visit_date_s = request.form.get("visit_date", "")
    doctor_id    = request.form.get("doctor_id", "")
    diagnosis    = request.form.get("diagnosis", "").strip()
    prescription = request.form.get("prescription", "").strip()
    test_results = request.form.get("test_results", "").strip()
    notes        = request.form.get("notes", "").strip()

    patient = Patient.query.get(int(patient_id)) if patient_id else None
    if not patient:
        flash("Patient not found.", "error")
        return redirect(url_for("hospital_dashboard") + "#search")

    try:
        visit_date = datetime.strptime(visit_date_s, "%Y-%m-%d").date()
    except ValueError:
        flash("Invalid visit date.", "error")
        return redirect(url_for("hospital_dashboard") + "#search")

    doctor = None
    if doctor_id:
        doctor = Doctor.query.get(int(doctor_id))
        if not doctor or doctor.hospital_id != hospital.id:
            doctor = None

    record = MedicalRecord(
        patient_id          = patient.id,
        hospital_id         = hospital.id,
        doctor_id           = doctor.id if doctor else None,
        created_by_staff_id = session.get("user_id"),
        visit_date          = visit_date,
        diagnosis           = diagnosis,
        prescription        = prescription,
        test_results        = test_results,
        notes               = notes,
    )
    db.session.add(record)
    db.session.commit()

    flash(f"Medical record added for {patient.full_name}.", "success")
    return redirect(url_for("hospital_search", code=patient.emergency_code) + "#search")


@app.route("/hospital/settings", methods=["POST"])
@login_required(role="hospital_staff")
def hospital_update_settings():
    hospital = current_hospital()

    hospital_name = request.form.get("hospital_name", "").strip()
    address       = request.form.get("address", "").strip()

    if not all([hospital_name, address]):
        flash("Hospital name and address are required.", "error")
        return redirect(url_for("hospital_dashboard") + "#settings")

    hospital.name = hospital_name
    hospital.address = address
    hospital.phone = request.form.get("phone", "").strip()

    card_price = request.form.get("card_price", "")
    if card_price:
        try:
            hospital.card_price = float(card_price)
        except ValueError:
            pass

    hospital.opay_account_number = request.form.get("opay_account_number", "").strip()
    hospital.opay_account_name   = request.form.get("opay_account_name", "").strip()

    db.session.commit()
    flash("Hospital settings updated.", "success")
    return redirect(url_for("hospital_dashboard") + "#settings")
@app.route("/patient/search-hospitals")
@login_required(role="patient")
def patient_search_hospitals():
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return {"hospitals": []}
    results = Hospital.query.filter(Hospital.name.ilike(f"%{q}%")).limit(10).all()
    return {"hospitals": [
        {"id": h.id, "name": h.name, "address": h.address, "phone": h.phone}
        for h in results
    ]}

@app.route("/patient/enroll-hospital", methods=["POST"])
@login_required(role="patient")
def patient_enroll_hospital():
    patient = current_patient()
    hospital_id = request.form.get("hospital_id", "")
    hospital = Hospital.query.get(int(hospital_id)) if hospital_id else None
    if not hospital:
        flash("Hospital not found.", "error")
        return redirect(url_for("patient_dashboard") + "#hospitals")

    existing = HospitalEnrolment.query.filter_by(
        patient_id=patient.id, hospital_id=hospital.id
    ).first()
    if existing:
        flash("You are already registered under this hospital.", "error")
        return redirect(url_for("patient_dashboard") + "#hospitals")

    db.session.add(HospitalEnrolment(patient_id=patient.id, hospital_id=hospital.id))
    db.session.commit()
    flash(f"You are now registered under {hospital.name}.", "success")
    return redirect(url_for("patient_dashboard") + "#hospitals")





# ── Logout ───────────────────────────────────────────────────────────────────

@app.route("/logout")
def logout():
    """Clear session and redirect to home."""
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)