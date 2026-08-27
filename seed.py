from app.database import SessionLocal
from app.models import User, Student, RoleEnum
from app.auth import hash_password

db = SessionLocal()

try:
    admin = User(
        username="admin",
        password=hash_password("admin123"),
        role=RoleEnum.ADMIN
    )

    principal = User(
        username="principal",
        password=hash_password("principal123"),
        role=RoleEnum.PRINCIPAL
    )

    teacher = User(
        username="teacher1",
        password=hash_password("teacher123"),
        role=RoleEnum.TEACHER
    )

    student = Student(
        name="Arun Kumar",
        roll_number="STU001",
        email="arun@example.com"
    )

    db.add_all([admin, principal, teacher, student])
    db.commit()

    print("Initial data created successfully!")

finally:
    db.close()