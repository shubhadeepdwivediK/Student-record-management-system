"""Load demo data (handy for testing and screenshots):  python scripts/seed_demo.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from srms.cli import App  # noqa: E402
from srms.exceptions import DuplicateError  # noqa: E402

STUDENTS = [
    ("24BCE1001", "Aarav Sharma", "aarav@example.com", "CSE", 2, "9876543210"),
    ("24BCE1002", "Diya Patel", "diya@example.com", "CSE", 2, "9123456780"),
    ("24BEC2001", "Rohan Verma", "rohan@example.com", "ECE", 2, ""),
    ("24BEC2002", "Ananya Iyer", "ananya@example.com", "ECE", 2, "9988776655"),
    ("23BCE3001", "Kabir Singh", "kabir@example.com", "CSE", 3, ""),
]
COURSES = [("BCSE101", "Programming in Python", 4), ("BMAT101", "Calculus", 3), ("BPHY101", "Physics", 3)]
GRADES = [  # roll, course, marks, semester
    ("24BCE1001", "BCSE101", 92, 1), ("24BCE1001", "BMAT101", 85, 1), ("24BCE1001", "BPHY101", 78, 1),
    ("24BCE1002", "BCSE101", 88, 1), ("24BCE1002", "BMAT101", 64, 1), ("24BCE1002", "BPHY101", 71, 1),
    ("24BEC2001", "BCSE101", 55, 1), ("24BEC2001", "BMAT101", 42, 1), ("24BEC2001", "BPHY101", 67, 1),
    ("24BEC2002", "BCSE101", 95, 1), ("24BEC2002", "BMAT101", 91, 1),
    ("23BCE3001", "BCSE101", 73, 1), ("23BCE3001", "BMAT101", 80, 1),
]

app = App()
if not app.auth.has_users():
    app.auth.register("admin", "Admin1234", "admin")
    app.auth.register("faculty1", "Faculty123", "faculty")
for row in STUDENTS:
    try: app.students.create(*row[:5], phone=row[5])
    except DuplicateError: pass
for row in COURSES:
    try: app.courses.create(*row)
    except DuplicateError: pass
for g in GRADES:
    app.grades.record(*g)
print("Demo data loaded. Logins -> admin / Admin1234   faculty1 / Faculty123")
