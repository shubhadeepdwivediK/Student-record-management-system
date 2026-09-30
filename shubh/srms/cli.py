"""Menu-driven command-line interface (presentation layer only - no business logic here)."""
import getpass
from datetime import datetime

from . import validators as v
from .auth import AuthService, User
from .config import DB_PATH, EXPORT_DIR, MAX_LOGIN_ATTEMPTS
from .database import Database
from .exceptions import SRMSError, ValidationError
from .logger import get_logger
from .repository import CourseRepository, GradeRepository, StudentRepository
from .reports import ReportService
from .services import CourseService, GradeService, StudentService

log = get_logger("cli")


# ---------------- helpers ----------------
def ask(label, validator=None, default=None):
    """Prompt until the validator accepts the input. Blank returns `default` if given."""
    while True:
        suffix = f" [{default}]" if default not in (None, "") else ""
        raw = input(f"  {label}{suffix}: ").strip()
        if raw == "" and default is not None:
            return default
        if validator is None:
            return raw
        try:
            return validator(raw)
        except ValidationError as e:
            print(f"  ! {e}")


def positive_int(raw) -> int:
    if not raw.isdigit() or int(raw) < 1:
        raise ValidationError("Enter a positive whole number.")
    return int(raw)


def role_choice(raw) -> str:
    if raw not in ("admin", "faculty"):
        raise ValidationError("Role must be 'admin' or 'faculty'.")
    return raw


def confirm(message) -> bool:
    return input(f"  {message} (y/N): ").strip().lower() == "y"


def table(headers, rows):
    if not rows:
        print("  (no records)")
        return
    rows = [[str(c) for c in r] for r in rows]
    widths = [max(len(h), *(len(r[i]) for r in rows)) for i, h in enumerate(headers)]
    line = "  " + "-+-".join("-" * w for w in widths)
    print("  " + " | ".join(h.ljust(w) for h, w in zip(headers, widths)))
    print(line)
    for r in rows:
        print("  " + " | ".join(c.ljust(w) for c, w in zip(r, widths)))


def menu(title, options):
    print(f"\n=== {title} ===")
    for key, (label, _) in options.items():
        print(f"  {key}. {label}")
    return input("  Choose: ").strip()


def student_rows(students):
    return [(s.roll_no, s.name, s.department, s.year, s.email, s.phone or "-") for s in students]


STUDENT_HEADERS = ["Roll No", "Name", "Dept", "Year", "Email", "Phone"]


# ---------------- application ----------------
class App:
    def __init__(self, db: Database = None):
        self.db = db or Database(DB_PATH)
        self.db.initialise()
        s_repo, c_repo, g_repo = StudentRepository(self.db), CourseRepository(self.db), GradeRepository(self.db)
        self.auth = AuthService(self.db)
        self.students = StudentService(s_repo)
        self.courses = CourseService(c_repo)
        self.grades = GradeService(g_repo, self.students, self.courses)
        self.reports = ReportService(self.students, self.courses, self.grades, g_repo)
        self.user: User = None

    # ----- login -----
    def login(self) -> bool:
        if not self.auth.has_users():
            print("\nFirst run: create the administrator account.")
            while True:
                try:
                    username = ask("Admin username", v.username)
                    pw = getpass.getpass("  Password: ")
                    if pw != getpass.getpass("  Confirm password: "):
                        print("  ! Passwords do not match.")
                        continue
                    self.user = self.auth.register(username, pw, "admin")
                    return True
                except SRMSError as e:
                    print(f"  ! {e}")
        for attempt in range(1, MAX_LOGIN_ATTEMPTS + 1):
            username = input("  Username: ")
            pw = getpass.getpass("  Password: ")
            try:
                self.user = self.auth.login(username, pw)
                return True
            except SRMSError as e:
                print(f"  ! {e} ({MAX_LOGIN_ATTEMPTS - attempt} attempts left)")
        print("Too many failed attempts. Exiting.")
        return False

    # ----- safe execution -----
    def run_action(self, func):
        try:
            func()
        except SRMSError as e:
            print(f"  ! {e}")
        except (KeyboardInterrupt, EOFError):
            print("\n  (cancelled)")
        except Exception:                      # last-resort guard: log details, show friendly text
            log.exception("Unexpected error")
            print("  ! Something went wrong. Details were written to logs/srms.log")

    # ----- students -----
    def add_student(self):
        self.user.require("write")
        s = self.students.create(
            ask("Roll number", v.roll_no), ask("Full name", v.name), ask("Email", v.email),
            ask("Department (e.g. CSE)", v.department), ask("Year (1-5)", v.year),
            ask("Phone (optional)", v.phone, default=""))
        print(f"  Added {s.name} ({s.roll_no}).")

    def view_student(self):
        s = self.students.get(ask("Roll number", v.roll_no))
        t = self.grades.transcript(s.roll_no)
        print(f"\n  {s.name} | {s.roll_no} | {s.department} year {s.year}")
        print(f"  {s.email} | {s.phone or 'no phone'} | CGPA {t['cgpa']} ({t['total_credits']} credits)")

    def list_students(self):
        dept = input("  Filter by department (blank = all): ").strip() or None
        order = input("  Sort by roll_no/name/department/year [roll_no]: ").strip() or "roll_no"
        table(STUDENT_HEADERS, student_rows(self.students.list(department=dept, order_by=order)))

    def update_student(self):
        self.user.require("write")
        s = self.students.get(ask("Roll number", v.roll_no))
        print("  Press Enter to keep the current value.")
        changes = {
            "name": ask("Name", v.name, s.name), "email": ask("Email", v.email, s.email),
            "department": ask("Department", v.department, s.department),
            "year": ask("Year", v.year, s.year), "phone": ask("Phone", v.phone, s.phone),
        }
        self.students.update(s.roll_no, **changes)
        print("  Updated.")

    def delete_student(self):
        self.user.require("delete")
        s = self.students.get(ask("Roll number", v.roll_no))
        if confirm(f"Delete {s.name} and all their grades?"):
            self.students.delete(s.roll_no)
            print("  Deleted.")

    def search_students(self):
        table(STUDENT_HEADERS, student_rows(self.students.search(ask("Search text"))))

    # ----- courses -----
    def add_course(self):
        self.user.require("write")
        c = self.courses.create(ask("Course code", v.course_code), ask("Title", v.course_title),
                                ask("Credits (1-6)", v.credits))
        print(f"  Added {c.code}.")

    def list_courses(self):
        table(["Code", "Title", "Credits"], [(c.code, c.title, c.credits) for c in self.courses.list()])

    def update_course(self):
        self.user.require("write")
        c = self.courses.get(ask("Course code", v.course_code))
        self.courses.update(c.code, ask("Title", v.course_title, c.title),
                            ask("Credits", v.credits, c.credits))
        print("  Updated.")

    def delete_course(self):
        self.user.require("delete")
        c = self.courses.get(ask("Course code", v.course_code))
        if confirm(f"Delete {c.code} and all its grades?"):
            self.courses.delete(c.code)
            print("  Deleted.")

    # ----- grades -----
    def record_grade(self):
        self.user.require("write")
        r = self.grades.record(ask("Roll number", v.roll_no), ask("Course code", v.course_code),
                               ask("Marks (0-100)", v.marks), ask("Semester (1-12)", v.semester))
        print(f"  Saved: {r['roll_no']} {r['course']} -> {r['marks']} (grade {r['grade']}).")

    def show_transcript(self):
        t = self.grades.transcript(ask("Roll number", v.roll_no))
        print(f"\n  Transcript: {t['student'].name} ({t['student'].roll_no})")
        table(["Sem", "Course", "Title", "Cr", "Marks", "Grade"],
              [(r["semester"], r["code"], r["title"], r["credits"], r["marks"], r["grade"]) for r in t["rows"]])
        print(f"  CGPA: {t['cgpa']}   Total credits: {t['total_credits']}")

    def course_sheet(self):
        sheet = self.grades.course_sheet(ask("Course code", v.course_code))
        print(f"\n  {sheet['course'].code} - {sheet['course'].title}")
        table(["Roll No", "Name", "Sem", "Marks", "Grade"],
              [(r["roll_no"], r["name"], r["semester"], r["marks"], r["grade"]) for r in sheet["rows"]])

    def delete_grade(self):
        self.user.require("delete")
        self.grades.remove(ask("Roll number", v.roll_no), ask("Course code", v.course_code))
        print("  Grade removed.")

    # ----- reports -----
    def course_stats(self):
        self.user.require("reports")
        st = self.reports.course_statistics(ask("Course code", v.course_code))
        if st["count"] == 0:
            print("  No grades recorded for this course yet.")
            return
        print(f"\n  {st['course'].code} - {st['course'].title}  ({st['count']} students)")
        print(f"  Mean {st['mean']} | Median {st['median']} | Std dev {st['stdev']}")
        print(f"  Highest {st['highest']} | Lowest {st['lowest']} | Pass rate {st['pass_rate']}%")
        print("  Grade distribution:")
        for grade, n in st["distribution"].items():
            print(f"    {grade} | {'#' * n} {n}")

    def rank_list(self):
        self.user.require("reports")
        dept = input("  Department (blank = all): ").strip() or None
        top = ask("How many to show", positive_int, default=10)
        table(["Rank", "Roll No", "Name", "Dept", "CGPA"], self.reports.rank_list(dept, int(top)))

    def dept_summary(self):
        self.user.require("reports")
        table(["Department", "Students", "Avg CGPA"],
              [(d["department"], d["students"], d["avg_cgpa"] if d["avg_cgpa"] is not None else "-")
               for d in self.reports.department_summary()])

    def export_students(self):
        self.user.require("reports")
        path = EXPORT_DIR / f"students_{datetime.now():%Y%m%d_%H%M%S}.csv"
        print(f"  Exported {self.reports.export_students(path)} students to {path}")

    def export_transcript(self):
        self.user.require("reports")
        roll = ask("Roll number", v.roll_no)
        path = EXPORT_DIR / f"transcript_{roll}.csv"
        print(f"  Saved {self.reports.export_transcript(roll, path)}")

    def import_students(self):
        self.user.require("write")
        added, errors = self.reports.import_students(ask("CSV file path"))
        print(f"  Imported {added} student(s); {len(errors)} row(s) rejected.")
        for e in errors[:10]:
            print(f"    - {e}")

    # ----- users -----
    def create_user(self):
        self.user.require("manage_users")
        username = ask("New username", v.username)
        role = ask("Role (admin/faculty)", role_choice, default="faculty")
        u = self.auth.register(username, getpass.getpass("  Password: "), role)
        print(f"  Created user {u.username} ({u.role}).")

    def list_users(self):
        self.user.require("manage_users")
        table(["Username", "Role"], [(u.username, u.role) for u in self.auth.list_users()])

    # ----- menus -----
    def submenu(self, title, options):
        while True:
            choice = menu(title, options)
            if choice == "0":
                return
            if choice in options:
                self.run_action(options[choice][1])
            else:
                print("  ! Invalid choice.")

    def main_menu(self):
        top = {
            "1": ("Student management", lambda: self.submenu("Students", {
                "1": ("Add student", self.add_student), "2": ("View student", self.view_student),
                "3": ("List students", self.list_students), "4": ("Update student", self.update_student),
                "5": ("Delete student (admin)", self.delete_student), "6": ("Search", self.search_students),
                "0": ("Back", None)})),
            "2": ("Course management", lambda: self.submenu("Courses", {
                "1": ("Add course", self.add_course), "2": ("List courses", self.list_courses),
                "3": ("Update course", self.update_course), "4": ("Delete course (admin)", self.delete_course),
                "0": ("Back", None)})),
            "3": ("Grades & transcripts", lambda: self.submenu("Grades", {
                "1": ("Record / update marks", self.record_grade), "2": ("Student transcript", self.show_transcript),
                "3": ("Course grade sheet", self.course_sheet), "4": ("Delete a grade (admin)", self.delete_grade),
                "0": ("Back", None)})),
            "4": ("Reports & analytics", lambda: self.submenu("Reports", {
                "1": ("Course statistics", self.course_stats), "2": ("Rank list", self.rank_list),
                "3": ("Department summary", self.dept_summary), "4": ("Export students to CSV", self.export_students),
                "5": ("Export a transcript to CSV", self.export_transcript),
                "6": ("Import students from CSV", self.import_students), "0": ("Back", None)})),
        }
        if self.user.can("manage_users"):
            top["5"] = ("User management", lambda: self.submenu("Users", {
                "1": ("Create user", self.create_user), "2": ("List users", self.list_users),
                "0": ("Back", None)}))
        top["0"] = ("Logout & exit", None)
        while True:
            choice = menu(f"MAIN MENU  (user: {self.user.username}, role: {self.user.role})", top)
            if choice == "0":
                log.info("Logout: %s", self.user.username)
                print("Goodbye!")
                return
            if choice in top:
                self.run_action(top[choice][1])
            else:
                print("  ! Invalid choice.")


def main():
    print("=" * 46 + "\n   STUDENT RECORD MANAGEMENT SYSTEM  v1.0\n" + "=" * 46)
    try:
        app = App()
        if app.login():
            app.main_menu()
    except (KeyboardInterrupt, EOFError):
        print("\nGoodbye!")
