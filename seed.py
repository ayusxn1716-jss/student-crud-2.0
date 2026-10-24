"""Load DUMMY students for demo/testing. Run: python seed.py"""
from app import crud
from app.database import connect, init_db

DUMMY = [
    ("Aarav Sharma", "2004-03-12", "aarav.sharma@example.com", "9876500001", "B.Tech CSE", "2022-08-01"),
    ("Diya Verma", "2005-07-25", "diya.verma@example.com", "9876500002", "B.Tech AIML", "2023-08-01"),
    ("Rohan Gupta", "2006-01-09", "rohan.gupta@example.com", "9876500003", "B.Tech AIML", "2024-08-01"),
    ("Ananya Singh", "2003-11-30", "ananya.singh@example.com", None, "BCA", "2021-08-01"),
    ("Kabir Mehta", "2005-12-02", None, "9876500005", "B.Tech CSE", "2023-08-01"),
    ("Isha Patel", "2006-05-18", "isha.patel@example.com", "9876500006", "BBA", "2024-08-01"),
    ("Vivaan Joshi", "2004-09-14", "vivaan.joshi@example.com", "9876500007", "BCA", "2022-08-01"),
    ("Meera Nair", "2007-02-21", "meera.nair@example.com", "9876500008", "B.Tech AIML", "2025-08-01"),
]


def main():
    init_db()
    conn = connect()
    added = 0
    for name, dob, email, phone, course, enrolled in DUMMY:
        if email and conn.execute("SELECT 1 FROM students WHERE email = ?", (email,)).fetchone():
            continue
        crud.create_student(conn, dict(name=name, date_of_birth=dob, email=email, phone=phone,
                                       course=course, enrollment_date=enrolled))
        added += 1
    conn.close()
    print(f"Seeded {added} dummy students.")


if __name__ == "__main__":
    main()
