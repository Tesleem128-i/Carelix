
import os
from flask import Flask
from model import db, User
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

    existing_user = User.query.filter_by(email="test@example.com").first()
# test user creation
    if not existing_user:
        print("Inserting a test user...")
        test_user = User(
            role="admin",
            email="test@example.com"
        )
        test_user.set_password("SecurePassword123")
# commit the test user to the database
        db.session.add(test_user)
        db.session.commit()
        print("Test user saved successfully!")
    else:
        print("Test user already exists in the database.")
# make sure to query the database to see if the user was added
    all_users = User.query.all()
    print("\n--- Current Users in Database ---")
    for user in all_users:
        print(f"ID: {user.id} | Email: {user.email} | Role: {user.role} | Created: {user.created_at}")