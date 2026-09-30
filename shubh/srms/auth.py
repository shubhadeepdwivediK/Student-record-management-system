"""Authentication (salted PBKDF2 password hashing) and role-based permissions."""
import hashlib
import hmac
import os
import sqlite3
from dataclasses import dataclass
from typing import List

from . import validators as v
from .config import PBKDF2_ITERATIONS
from .database import Database
from .exceptions import AuthError, DuplicateError, PermissionDenied
from .logger import get_logger

log = get_logger("auth")

ROLE_PERMISSIONS = {
    "admin": {"read", "write", "delete", "reports", "manage_users"},
    "faculty": {"read", "write", "reports"},
}


@dataclass
class User:
    username: str
    role: str

    def can(self, action: str) -> bool:
        return action in ROLE_PERMISSIONS.get(self.role, set())

    def require(self, action: str) -> None:
        if not self.can(action):
            log.warning("Permission denied: %s tried '%s'", self.username, action)
            raise PermissionDenied(f"Your role ({self.role}) is not allowed to do that.")


def hash_password(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS).hex()


class AuthService:
    def __init__(self, db: Database):
        self.db = db

    def has_users(self) -> bool:
        with self.db.connection() as c:
            return c.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0

    def register(self, username: str, password: str, role: str = "faculty") -> User:
        username, password = v.username(username), v.password(password)
        if role not in ROLE_PERMISSIONS:
            raise AuthError(f"Unknown role '{role}'.")
        salt = os.urandom(16)
        try:
            with self.db.connection() as c:
                c.execute("INSERT INTO users (username, password_hash, salt, role) VALUES (?,?,?,?)",
                          (username, hash_password(password, salt), salt.hex(), role))
        except sqlite3.IntegrityError:
            raise DuplicateError(f"Username '{username}' is already taken.")
        log.info("User registered: %s (%s)", username, role)
        return User(username, role)

    def login(self, username: str, password: str) -> User:
        with self.db.connection() as c:
            row = c.execute("SELECT * FROM users WHERE username = ?",
                            ((username or "").strip().lower(),)).fetchone()
        # Same generic error for unknown user / wrong password (no user enumeration).
        if row is None:
            hash_password(password or "", b"\x00" * 16)   # equalise timing
            log.warning("Failed login (unknown user)")
            raise AuthError("Invalid username or password.")
        expected = hash_password(password or "", bytes.fromhex(row["salt"]))
        if not hmac.compare_digest(expected, row["password_hash"]):
            log.warning("Failed login for %s", row["username"])
            raise AuthError("Invalid username or password.")
        log.info("Login: %s", row["username"])
        return User(row["username"], row["role"])

    def list_users(self) -> List[User]:
        with self.db.connection() as c:
            return [User(r["username"], r["role"])
                    for r in c.execute("SELECT username, role FROM users ORDER BY username")]
