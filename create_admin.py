"""Create admin user"""
from src.api.models import get_db, User
from src.api.auth import get_password_hash

db = next(get_db())

admin = User(
    username="admin",
    email="admin@example.com",
    hashed_password=get_password_hash("admin123"),
    is_admin=True,
    monthly_job_limit=999999  # Unlimited for admin
)

db.add(admin)
db.commit()
print("✅ Admin user created!")
print("Username: admin")
print("Password: admin123")
