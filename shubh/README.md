# Student Record Management System (SRMS)

A menu-driven Python application to manage students, courses and grades, with secure login,
analytics and CSV import/export. Built for the **VITyarthi – Build Your Own Project** evaluation.

## Overview
SRMS replaces scattered spreadsheets with one validated SQLite database. Faculty can enter
student details and marks; the system calculates letter grades and credit-weighted CGPA,
ranks students and produces course statistics. Everything runs offline using only the Python
standard library.

## Features
- **Authentication & roles** – Admin / Faculty, PBKDF2-SHA256 salted hashes, 3-attempt login limit
- **Student management** – Create, Read, Update, Delete, search, filter by department, sort
- **Course management** – course catalogue with credits
- **Grades** – marks per course, letter grade, grade points, CGPA, transcripts, grade sheets
- **Analytics** – mean / median / std-dev / pass rate, text grade histogram, rank list (ties handled), department summary
- **CSV** – bulk import students, export students and transcripts
- **Robustness** – strict validation, custom exceptions, parameterised SQL, rotating log file

## Technologies used
Python 3.8+ (standard library only): `sqlite3`, `hashlib`, `csv`, `statistics`, `logging`,
`dataclasses`, `unittest`. Git for version control.

## Project structure
```
student_record_system/
├── main.py                 # entry point
├── srms/
│   ├── config.py           # paths & settings
│   ├── exceptions.py       # custom exception hierarchy
│   ├── logger.py           # rotating file logger
│   ├── validators.py       # input validation
│   ├── models.py           # Student, Course, grading scale, CGPA
│   ├── database.py         # SQLite connection + schema
│   ├── repository.py       # data-access layer (all SQL)
│   ├── services.py         # business logic
│   ├── auth.py             # login, hashing, roles
│   ├── reports.py          # analytics + CSV import/export
│   └── cli.py              # menu interface
├── tests/                  # 37 unit tests
├── scripts/seed_demo.py    # demo data loader
├── docs/DESIGN.md          # architecture & UML diagrams
├── statement.md
└── README.md
```

## Install & run
```bash
git clone <your-repo-url>
cd student_record_system
python main.py
```
No `pip install` is needed. On the first run you will be asked to create the administrator account.

**Try it with demo data (optional):**
```bash
python scripts/seed_demo.py     # creates admin / Admin1234 and faculty1 / Faculty123
python main.py
```

## Testing
```bash
python -m unittest discover -s tests -t . -v
```
Tests cover validators, grading/CGPA maths, CRUD, duplicate handling, SQL-injection safety,
cascading deletes, analytics, rank ties, CSV round-trip, bad-CSV handling, password hashing
and role permissions. Each test uses its own temporary database.

## Configuration (optional environment variables)
`SRMS_DATA_DIR`, `SRMS_DB_PATH`, `SRMS_LOG_DIR`, `SRMS_EXPORT_DIR`

## Grading scale
| Marks | Grade | Points |
|-------|-------|--------|
| 90–100 | S | 10 |
| 80–89 | A | 9 |
| 70–79 | B | 8 |
| 60–69 | C | 7 |
| 50–59 | D | 6 |
| 45–49 | E | 5 |
| < 45 | F | 0 |

CGPA = Σ(grade points × credits) ÷ Σ credits

## Screenshots
Add screenshots of the login screen, a student list, a transcript and the course statistics
here (e.g. `![Transcript](docs/screenshots/transcript.png)`).

## Author
Your Name – Reg. No. – Course name
