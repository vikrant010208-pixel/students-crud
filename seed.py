"""Load DUMMY sample students (no real personal data)."""
from datetime import date

from app import crud
from app.database import init_db

SAMPLES = [
    ("Aarav Sharma", "2004-05-17", "aarav@example.com", "+91 90000 00001", "BCA", "Dehradun", "2024-08-01"),
    ("Diya Verma", "2005-11-02", "diya@example.com", "+91 90000 00002", "BCA", "Haridwar", "2024-08-01"),
    ("Kabir Singh", "2003-01-25", "kabir@example.com", None, "B.Sc IT", "Rishikesh", "2023-08-01"),
    ("Meera Nair", "2006-03-09", "meera@example.com", "+91 90000 00004", "BBA", "Dehradun", "2025-08-01"),
    ("Rohan Gupta", "2005-07-30", None, "+91 90000 00005", "B.Sc IT", "Roorkee", "2024-08-01"),
]

if __name__ == "__main__":
    init_db()
    if crud.count_students():
        print("Database already has data - skipping seed.")
    else:
        for n, dob, email, phone, course, addr, enr in SAMPLES:
            crud.create_student(dict(name=n, date_of_birth=date.fromisoformat(dob), email=email,
                                     phone=phone, course=course, address=addr,
                                     enrollment_date=date.fromisoformat(enr)))
        print(f"Inserted {len(SAMPLES)} dummy students.")
