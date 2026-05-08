from app import create_app
from backend.models import db, User
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    # Check if admin exists
    admin = User.query.filter_by(email="admin@example.com").first()
    if not admin:
        admin = User(
            name="Admin User",
            email="admin@example.com",
            password=generate_password_hash("admin123"),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created!")
    else:
        print(f"Admin exists with role: {admin.role}")
    
    # List all users
    users = User.query.all()
    for u in users:
        print(f"  - {u.email} ({u.role})")
