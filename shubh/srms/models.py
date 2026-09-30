"""Domain models and the grading scale."""
from dataclasses import dataclass, asdict
from typing import Optional

# (minimum marks, letter grade, grade points) - highest band first
GRADE_SCALE = [(90, "S", 10), (80, "A", 9), (70, "B", 8), (60, "C", 7),
               (50, "D", 6), (45, "E", 5), (0, "F", 0)]
PASS_MARK = 45


def marks_to_grade(marks: float):
    """Return (letter, grade_points) for a marks value."""
    for lower, letter, points in GRADE_SCALE:
        if marks >= lower:
            return letter, points
    return "F", 0


def compute_cgpa(rows) -> float:
    """Credit-weighted CGPA. `rows` are mappings with 'credits' and 'marks'."""
    total_credits = sum(r["credits"] for r in rows)
    if total_credits == 0:
        return 0.0
    weighted = sum(marks_to_grade(r["marks"])[1] * r["credits"] for r in rows)
    return round(weighted / total_credits, 2)


@dataclass
class Student:
    roll_no: str
    name: str
    email: str
    department: str
    year: int
    phone: str = ""
    id: Optional[int] = None

    @classmethod
    def from_row(cls, row):
        return cls(id=row["id"], roll_no=row["roll_no"], name=row["name"],
                   email=row["email"], phone=row["phone"] or "",
                   department=row["department"], year=row["year"])

    def to_dict(self):
        return asdict(self)


@dataclass
class Course:
    code: str
    title: str
    credits: int
    id: Optional[int] = None

    @classmethod
    def from_row(cls, row):
        return cls(id=row["id"], code=row["code"], title=row["title"], credits=row["credits"])

    def to_dict(self):
        return asdict(self)
