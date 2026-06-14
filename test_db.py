# test_db.py
import os
from flask import Flask
from model import db, User

app = Flask(__name__)

# 1. Setup Database Connection
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    # 2. Create the tables 
    print("Creating database tables...")
    db.create_all()
    
    # 3. Check if our test user already exists to avoid duplicates
    existing_user = User.query.filter_by(email="test@example.com").first()
    
    if not existing_user:
        print("Inserting a test user...")
        # 4. Create a mock user instance
        test_user = User(
            role="admin",
            email="test@example.com"
        )
        test_user.set_password("SecurePassword123")
        
        # 5. Save to the database
        db.session.add(test_user)
        db.session.add(test_user)
        db.session.commit()
        print("Test user saved successfully!")
    else:
        print("Test user already exists in the database.")

    # 6. Read back from the database to prove it works
    all_users = User.query.all()
    print("\n--- Current Users in Database ---")
    for user in all_users:
        print(f"ID: {user.id} | Email: {user.email} | Role: {user.role} | Created: {user.created_at}")