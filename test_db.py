# test_db.py
import os
from flask import Flask
from model import (
    db, User, Patient, Hospital, HospitalLocation, Doctor,
    Appointment, HospitalCard, MedicalRecord, HospitalEnrolment,
    OPayPayment, AlertLog
)
from dotenv import load_dotenv

load_dotenv()

print("DATABASE_URL LOADED AS:", os.environ.get('DATABASE_URL'))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    print("Creating database tables...")
    db.create_all()
    print("All tables created successfully!")

    all_users = User.query.all()
    print("\n--- Current Users in Database ---")
    for user in all_users:
        print(f"ID: {user.id} | Email: {user.email} | Role: {user.role}")