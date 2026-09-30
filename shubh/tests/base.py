"""Shared fixture: a fresh temporary database and fully wired services for each test."""
import shutil
import tempfile
import unittest
from pathlib import Path

from srms.auth import AuthService
from srms.database import Database
from srms.repository import CourseRepository, GradeRepository, StudentRepository
from srms.reports import ReportService
from srms.services import CourseService, GradeService, StudentService


class BaseTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.db = Database(self.tmp / "test.db")
        self.db.initialise()
        g_repo = GradeRepository(self.db)
        self.students = StudentService(StudentRepository(self.db))
        self.courses = CourseService(CourseRepository(self.db))
        self.grades = GradeService(g_repo, self.students, self.courses)
        self.reports = ReportService(self.students, self.courses, self.grades, g_repo)
        self.auth = AuthService(self.db)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def add_student(self, roll="24BCE1001", name="aarav sharma", email="a@example.com", dept="cse", year=2):
        return self.students.create(roll, name, email, dept, year)
