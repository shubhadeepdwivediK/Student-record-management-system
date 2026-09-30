"""Analytics and CSV import/export."""
import csv
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import List, Tuple

from .exceptions import SRMSError, ValidationError
from .logger import get_logger
from .models import PASS_MARK, GRADE_SCALE, compute_cgpa, marks_to_grade
from .repository import GradeRepository
from .services import CourseService, GradeService, StudentService

log = get_logger("reports")
CSV_FIELDS = ["roll_no", "name", "email", "phone", "department", "year"]


class ReportService:
    def __init__(self, students: StudentService, courses: CourseService,
                 grades: GradeService, grade_repo: GradeRepository):
        self.students, self.courses, self.grades, self.grade_repo = students, courses, grades, grade_repo

    # ---------- analytics ----------
    def course_statistics(self, course_code) -> dict:
        sheet = self.grades.course_sheet(course_code)
        marks = [r["marks"] for r in sheet["rows"]]
        if not marks:
            return {"course": sheet["course"], "count": 0}
        dist = Counter(r["grade"] for r in sheet["rows"])
        return {
            "course": sheet["course"], "count": len(marks),
            "mean": round(statistics.mean(marks), 2),
            "median": round(statistics.median(marks), 2),
            "stdev": round(statistics.stdev(marks), 2) if len(marks) > 1 else 0.0,
            "highest": max(marks), "lowest": min(marks),
            "pass_rate": round(100 * sum(m >= PASS_MARK for m in marks) / len(marks), 1),
            "distribution": {g: dist.get(g, 0) for _, g, _ in GRADE_SCALE},
        }

    def _cgpa_by_student(self):
        grouped = defaultdict(list)
        info = {}
        for r in self.grade_repo.all_with_credits():
            grouped[r["student_id"]].append(r)
            info[r["student_id"]] = (r["roll_no"], r["name"], r["department"])
        return [(*info[sid], compute_cgpa(rows)) for sid, rows in grouped.items()]

    def rank_list(self, department=None, top=10) -> List[Tuple]:
        """Return [(rank, roll_no, name, department, cgpa)], ties share a rank."""
        rows = self._cgpa_by_student()
        if department:
            rows = [r for r in rows if r[2] == department.strip().upper()]
        rows.sort(key=lambda r: (-r[3], r[0]))
        ranked, last_cgpa, last_rank = [], None, 0
        for i, (roll, name, dept, cgpa) in enumerate(rows, start=1):
            rank = last_rank if cgpa == last_cgpa else i
            ranked.append((rank, roll, name, dept, cgpa))
            last_cgpa, last_rank = cgpa, rank
        return ranked[:top]

    def department_summary(self) -> List[dict]:
        counts = Counter(s.department for s in self.students.list())
        cgpas = defaultdict(list)
        for _, _, dept, cgpa in self._cgpa_by_student():
            cgpas[dept].append(cgpa)
        return [{"department": d, "students": n,
                 "avg_cgpa": round(statistics.mean(cgpas[d]), 2) if cgpas[d] else None}
                for d, n in sorted(counts.items())]

    # ---------- CSV ----------
    def export_students(self, path) -> int:
        students = self.students.list()
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
            w.writeheader()
            for s in students:
                w.writerow({k: getattr(s, k) for k in CSV_FIELDS})
        log.info("Exported %d students to %s", len(students), path)
        return len(students)

    def export_transcript(self, roll_no, path) -> Path:
        t = self.grades.transcript(roll_no)
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Roll No", t["student"].roll_no, "Name", t["student"].name])
            w.writerow(["Semester", "Course", "Title", "Credits", "Marks", "Grade"])
            for r in t["rows"]:
                w.writerow([r["semester"], r["code"], r["title"], r["credits"], r["marks"], r["grade"]])
            w.writerow(["CGPA", t["cgpa"], "Total credits", t["total_credits"]])
        log.info("Exported transcript for %s", t["student"].roll_no)
        return path

    def import_students(self, path) -> Tuple[int, List[str]]:
        """Bulk-import students; bad rows are reported, not fatal. Returns (added, errors)."""
        added, errors = 0, []
        try:
            with open(path, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                missing = {"roll_no", "name", "email", "department", "year"} - set(reader.fieldnames or [])
                if missing:
                    raise ValidationError(f"CSV is missing columns: {', '.join(sorted(missing))}")
                for line, row in enumerate(reader, start=2):
                    try:
                        self.students.create(row["roll_no"], row["name"], row["email"],
                                             row["department"], row["year"], row.get("phone", ""))
                        added += 1
                    except SRMSError as e:
                        errors.append(f"line {line}: {e}")
        except FileNotFoundError:
            raise ValidationError(f"File not found: {path}")
        log.info("Import from %s: %d added, %d rejected", path, added, len(errors))
        return added, errors
