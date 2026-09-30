"""Business logic. Validates input, enforces rules, delegates persistence to repositories."""
from typing import List

from . import validators as v
from .exceptions import NotFoundError
from .logger import get_logger
from .models import Course, Student, compute_cgpa, marks_to_grade
from .repository import CourseRepository, GradeRepository, StudentRepository

log = get_logger("services")


class StudentService:
    def __init__(self, repo: StudentRepository):
        self.repo = repo

    def create(self, roll_no, name, email, department, year, phone="") -> Student:
        student = Student(roll_no=v.roll_no(roll_no), name=v.name(name), email=v.email(email),
                          department=v.department(department), year=v.year(year),
                          phone=v.phone(phone))
        self.repo.add(student)
        log.info("Student created: %s", student.roll_no)
        return student

    def get(self, roll_no) -> Student:
        student = self.repo.get_by_roll(v.roll_no(roll_no))
        if not student:
            raise NotFoundError(f"No student with roll number {str(roll_no).upper()}.")
        return student

    def update(self, roll_no, /, **changes) -> Student:
        student = self.get(roll_no)
        cleaners = {"name": v.name, "email": v.email, "phone": v.phone,
                    "department": v.department, "year": v.year}
        for field, value in changes.items():
            if field not in cleaners:
                raise KeyError(f"Field '{field}' cannot be updated.")
            setattr(student, field, cleaners[field](value))
        self.repo.update(student)
        log.info("Student updated: %s (%s)", student.roll_no, ", ".join(changes))
        return student

    def delete(self, roll_no) -> None:
        student = self.get(roll_no)
        self.repo.delete(student.id)
        log.warning("Student deleted: %s", student.roll_no)

    def list(self, department=None, year=None, order_by="roll_no") -> List[Student]:
        dept = v.department(department) if department else None
        yr = v.year(year) if year else None
        return self.repo.list_all(dept, yr, order_by)

    def search(self, keyword) -> List[Student]:
        keyword = (keyword or "").strip()
        if not keyword:
            return []
        return self.repo.search(keyword)


class CourseService:
    def __init__(self, repo: CourseRepository):
        self.repo = repo

    def create(self, code, title, credits) -> Course:
        course = Course(code=v.course_code(code), title=v.course_title(title),
                        credits=v.credits(credits))
        self.repo.add(course)
        log.info("Course created: %s", course.code)
        return course

    def get(self, code) -> Course:
        course = self.repo.get_by_code(v.course_code(code))
        if not course:
            raise NotFoundError(f"No course with code {str(code).upper()}.")
        return course

    def update(self, code, title=None, credits=None) -> Course:
        course = self.get(code)
        if title is not None:
            course.title = v.course_title(title)
        if credits is not None:
            course.credits = v.credits(credits)
        self.repo.update(course)
        log.info("Course updated: %s", course.code)
        return course

    def delete(self, code) -> None:
        course = self.get(code)
        self.repo.delete(course.id)
        log.warning("Course deleted: %s", course.code)

    def list(self) -> List[Course]:
        return self.repo.list_all()


class GradeService:
    def __init__(self, grades: GradeRepository, students: StudentService, courses: CourseService):
        self.grades, self.students, self.courses = grades, students, courses

    def record(self, roll_no, course_code, marks, semester) -> dict:
        """Create or overwrite a student's marks in a course."""
        student = self.students.get(roll_no)
        course = self.courses.get(course_code)
        marks, semester = v.marks(marks), v.semester(semester)
        self.grades.upsert(student.id, course.id, semester, marks)
        letter, points = marks_to_grade(marks)
        log.info("Grade recorded: %s %s = %s (%s)", student.roll_no, course.code, marks, letter)
        return {"roll_no": student.roll_no, "course": course.code, "marks": marks,
                "grade": letter, "points": points}

    def remove(self, roll_no, course_code) -> None:
        student = self.students.get(roll_no)
        course = self.courses.get(course_code)
        self.grades.delete(student.id, course.id)
        log.warning("Grade removed: %s %s", student.roll_no, course.code)

    def transcript(self, roll_no) -> dict:
        student = self.students.get(roll_no)
        rows = self.grades.for_student(student.id)
        for r in rows:
            r["grade"], r["points"] = marks_to_grade(r["marks"])
        return {"student": student, "rows": rows,
                "total_credits": sum(r["credits"] for r in rows),
                "cgpa": compute_cgpa(rows)}

    def course_sheet(self, course_code) -> dict:
        course = self.courses.get(course_code)
        rows = self.grades.for_course(course.id)
        for r in rows:
            r["grade"] = marks_to_grade(r["marks"])[0]
        return {"course": course, "rows": rows}
