"""
Script to create a teacher account
Run with: python create_teacher.py
"""
from database import SessionLocal, test_connection
from models import Student
from auth import get_password_hash

def create_teacher():
    print("="*60)
    print("CREATE TEACHER ACCOUNT")
    print("="*60)

    if not test_connection():
        print("❌ Database connection failed!")
        return

    db = SessionLocal()

    try:
        # Check if teacher exists
        existing = db.query(Student).filter(Student.username == "teacher").first()

        if existing:
            print("⚠️  Teacher account already exists!")
            print(f"   Username: {existing.username}")
            print(f"   Email: {existing.email}")
            return

        # Create teacher
        teacher = Student(
            username="teacher",
            email="teacher@example.com",
            hashed_password=get_password_hash("teacher123"),
            full_name="Teacher Admin",
            is_teacher=True,
            is_active=True
        )

        db.add(teacher)
        db.commit()
        db.refresh(teacher)

        print("✅ Teacher account created successfully!")
        print(f"\n📝 Login credentials:")
        print(f"   Username: teacher")
        print(f"   Password: teacher123")
        print(f"   Email: teacher@example.com")
        print(f"\n🔑 Teacher ID: {teacher.id}")

    except Exception as e:
        print(f"❌ Error creating teacher: {e}")
        db.rollback()

    finally:
        db.close()

    print("\n" + "="*60)

if __name__ == "__main__":
    create_teacher()
