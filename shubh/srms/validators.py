"""Pure input-validation functions. Each returns the cleaned value or raises ValidationError."""
import re

from .config import MIN_PASSWORD_LENGTH
from .exceptions import ValidationError

_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z .'-]{1,59}$")
_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
_ROLL_RE = re.compile(r"^[A-Za-z0-9]{5,15}$")
_PHONE_RE = re.compile(r"^[6-9]\d{9}$")
_CODE_RE = re.compile(r"^[A-Za-z]{2,5}\d{3,4}[A-Za-z]?$")
_USER_RE = re.compile(r"^[A-Za-z0-9_]{3,20}$")


def _text(value) -> str:
    return "" if value is None else str(value).strip()


def _int(value, label: str) -> int:
    try:
        return int(_text(value))
    except ValueError:
        raise ValidationError(f"{label} must be a whole number.")


def name(value) -> str:
    v = _text(value)
    if not _NAME_RE.match(v):
        raise ValidationError("Name must be 2-60 letters (spaces, . ' - allowed).")
    return " ".join(v.split()).title()


def email(value) -> str:
    v = _text(value).lower()
    if not _EMAIL_RE.match(v):
        raise ValidationError("Enter a valid email address (e.g. name@example.com).")
    return v


def roll_no(value) -> str:
    v = _text(value).upper()
    if not _ROLL_RE.match(v):
        raise ValidationError("Roll number must be 5-15 letters/digits (e.g. 24BCE1001).")
    return v


def phone(value) -> str:
    """Optional field: empty string is accepted."""
    v = _text(value)
    if v and not _PHONE_RE.match(v):
        raise ValidationError("Phone must be a 10-digit Indian mobile number.")
    return v


def department(value) -> str:
    v = _text(value).upper()
    if not 2 <= len(v) <= 30:
        raise ValidationError("Department must be 2-30 characters.")
    return v


def year(value) -> int:
    v = _int(value, "Year")
    if not 1 <= v <= 5:
        raise ValidationError("Year of study must be between 1 and 5.")
    return v


def course_code(value) -> str:
    v = _text(value).upper()
    if not _CODE_RE.match(v):
        raise ValidationError("Course code looks like 'BCSE101' or 'MAT1001L'.")
    return v


def course_title(value) -> str:
    v = _text(value)
    if not 3 <= len(v) <= 80:
        raise ValidationError("Course title must be 3-80 characters.")
    return v


def credits(value) -> int:
    v = _int(value, "Credits")
    if not 1 <= v <= 6:
        raise ValidationError("Credits must be between 1 and 6.")
    return v


def semester(value) -> int:
    v = _int(value, "Semester")
    if not 1 <= v <= 12:
        raise ValidationError("Semester must be between 1 and 12.")
    return v


def marks(value) -> float:
    try:
        v = float(_text(value))
    except ValueError:
        raise ValidationError("Marks must be a number.")
    if not 0 <= v <= 100:
        raise ValidationError("Marks must be between 0 and 100.")
    return round(v, 2)


def username(value) -> str:
    v = _text(value)
    if not _USER_RE.match(v):
        raise ValidationError("Username must be 3-20 letters, digits or underscores.")
    return v.lower()


def password(value) -> str:
    v = value or ""
    if len(v) < MIN_PASSWORD_LENGTH or not re.search(r"[A-Za-z]", v) or not re.search(r"\d", v):
        raise ValidationError(
            f"Password needs at least {MIN_PASSWORD_LENGTH} characters with a letter and a digit."
        )
    return v
