"""Data-access layer: all SQL lives here. Uses parameterised queries only (no SQL injection)."""
import sqlite3
from typing import List, Optional

from .database import Database
from .exceptions import DuplicateError, NotFoundError
from .models import Course, Student

_STUDENT_SORT = {"roll_no", "name", "department", "year"}


def _duplicate(exc: sqlite3.IntegrityError, what: str) -> DuplicateError:
    return DuplicateError(f"{what} already exists ({exc}).")


class StudentRepository:
    def __init__(self, db: Database):
        self.db = db

    def add(self, s: Student) -> Student:
        try:
            with self.db.connection() as c:
                cur = c.execute(
                    "INSERT INTO students (roll_no, name, email, phone, department, year) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    (s.roll_no, s.name, s.email, s.phone, s.department, s.year))
                s.id = cur.lastrowid
        except sqlite3.IntegrityError as e:
            raise _duplicate(e, "A student with this roll number or email")
        return s

    def get(self, student_id: int) -> Optional[Student]:
        with self.db.connection() as c:
            row = c.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
        return Student.from_row(row) if row else None

    def get_by_roll(self, roll_no: str) -> Optional[Student]:
        with self.db.connection() as c:
            row = c.execute("SELECT * FROM students WHERE roll_no = ?", (roll_no,)).fetchone()
        return Student.from_row(row) if row else None

    def update(self, s: Student) -> None:
        try:
            with self.db.connection() as c:
                cur = c.execute(
                    "UPDATE students SET name=?, email=?, phone=?, department=?, year=? WHERE id=?",
                    (s.name, s.email, s.phone, s.department, s.year, s.id))
                if cur.rowcount == 0:
                    raise NotFoundError(f"Student id {s.id} not found.")
        except sqlite3.IntegrityError as e:
            raise _duplicate(e, "That email")

    def delete(self, student_id: int) -> None:
        with self.db.connection() as c:
            cur = c.execute("DELETE FROM students WHERE id = ?", (student_id,))
            if cur.rowcount == 0:
                raise NotFoundError(f"Student id {student_id} not found.")

    def list_all(self, department: str = None, year: int = None,
                 order_by: str = "roll_no") -> List[Student]:
        if order_by not in _STUDENT_SORT:
            order_by = "roll_no"
        sql, params, clauses = "SELECT * FROM students", [], []
        if department:
            clauses.append("department = ?"); params.append(department)
        if year:
            clauses.append("year = ?"); params.append(year)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += f" ORDER BY {order_by}"          # order_by is whitelisted above
        with self.db.connection() as c:
            return [Student.from_row(r) for r in c.execute(sql, params)]

    def search(self, keyword: str) -> List[Student]:
        like = f"%{keyword}%"
        with self.db.connection() as c:
            rows = c.execute(
                "SELECT * FROM students WHERE name LIKE ? OR roll_no LIKE ? OR email LIKE ? "
                "ORDER BY roll_no", (like, like, like))
            return [Student.from_row(r) for r in rows]


class CourseRepository:
    def __init__(self, db: Database):
        self.db = db

    def add(self, course: Course) -> Course:
        try:
            with self.db.connection() as c:
                cur = c.execute("INSERT INTO courses (code, title, credits) VALUES (?, ?, ?)",
                                (course.code, course.title, course.credits))
                course.id = cur.lastrowid
        except sqlite3.IntegrityError as e:
            raise _duplicate(e, "A course with this code")
        return course

    def get_by_code(self, code: str) -> Optional[Course]:
        with self.db.connection() as c:
            row = c.execute("SELECT * FROM courses WHERE code = ?", (code,)).fetchone()
        return Course.from_row(row) if row else None

    def update(self, course: Course) -> None:
        with self.db.connection() as c:
            cur = c.execute("UPDATE courses SET title=?, credits=? WHERE id=?",
                            (course.title, course.credits, course.id))
            if cur.rowcount == 0:
                raise NotFoundError(f"Course id {course.id} not found.")

    def delete(self, course_id: int) -> None:
        with self.db.connection() as c:
            cur = c.execute("DELETE FROM courses WHERE id = ?", (course_id,))
            if cur.rowcount == 0:
                raise NotFoundError(f"Course id {course_id} not found.")

    def list_all(self) -> List[Course]:
        with self.db.connection() as c:
            return [Course.from_row(r) for r in c.execute("SELECT * FROM courses ORDER BY code")]


class GradeRepository:
    def __init__(self, db: Database):
        self.db = db

    def upsert(self, student_id: int, course_id: int, semester: int, marks: float) -> None:
        with self.db.connection() as c:
            c.execute(
                "INSERT INTO grades (student_id, course_id, semester, marks) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(student_id, course_id) DO UPDATE SET "
                "semester=excluded.semester, marks=excluded.marks",
                (student_id, course_id, semester, marks))

    def delete(self, student_id: int, course_id: int) -> None:
        with self.db.connection() as c:
            cur = c.execute("DELETE FROM grades WHERE student_id=? AND course_id=?",
                            (student_id, course_id))
            if cur.rowcount == 0:
                raise NotFoundError("No grade recorded for that student and course.")

    def for_student(self, student_id: int) -> List[dict]:
        with self.db.connection() as c:
            rows = c.execute(
                "SELECT c.code, c.title, c.credits, g.semester, g.marks FROM grades g "
                "JOIN courses c ON c.id = g.course_id WHERE g.student_id = ? "
                "ORDER BY g.semester, c.code", (student_id,))
            return [dict(r) for r in rows]

    def for_course(self, course_id: int) -> List[dict]:
        with self.db.connection() as c:
            rows = c.execute(
                "SELECT s.roll_no, s.name, g.semester, g.marks FROM grades g "
                "JOIN students s ON s.id = g.student_id WHERE g.course_id = ? "
                "ORDER BY g.marks DESC", (course_id,))
            return [dict(r) for r in rows]

    def all_with_credits(self) -> List[dict]:
        """Every grade joined with student and course info (used for ranking/analytics)."""
        with self.db.connection() as c:
            rows = c.execute(
                "SELECT s.id AS student_id, s.roll_no, s.name, s.department, "
                "c.credits, g.marks FROM grades g "
                "JOIN students s ON s.id = g.student_id JOIN courses c ON c.id = g.course_id")
            return [dict(r) for r in rows]
