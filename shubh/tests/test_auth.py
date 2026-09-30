import unittest

from srms.exceptions import AuthError, DuplicateError, PermissionDenied, ValidationError
from tests.base import BaseTest


class AuthTests(BaseTest):
    def test_register_and_login(self):
        self.auth.register("Admin", "Secret123", "admin")
        user = self.auth.login("admin", "Secret123")
        self.assertEqual((user.username, user.role), ("admin", "admin"))

    def test_password_is_not_stored_in_plaintext(self):
        self.auth.register("admin", "Secret123", "admin")
        with self.db.connection() as c:
            row = c.execute("SELECT * FROM users").fetchone()
        self.assertNotIn("Secret123", tuple(row))
        self.assertEqual(len(row["password_hash"]), 64)

    def test_same_password_gets_different_hash(self):
        self.auth.register("user_a", "Secret123")
        self.auth.register("user_b", "Secret123")
        with self.db.connection() as c:
            hashes = {r[0] for r in c.execute("SELECT password_hash FROM users")}
        self.assertEqual(len(hashes), 2)

    def test_bad_credentials_share_one_message(self):
        self.auth.register("admin", "Secret123", "admin")
        msgs = set()
        for u, p in [("admin", "wrong"), ("ghost", "Secret123")]:
            with self.assertRaises(AuthError) as ctx:
                self.auth.login(u, p)
            msgs.add(str(ctx.exception))
        self.assertEqual(len(msgs), 1)

    def test_duplicate_and_weak_password(self):
        self.auth.register("admin", "Secret123", "admin")
        with self.assertRaises(DuplicateError):
            self.auth.register("admin", "Another123")
        with self.assertRaises(ValidationError):
            self.auth.register("newuser", "weak")

    def test_role_permissions(self):
        admin = self.auth.register("boss", "Secret123", "admin")
        faculty = self.auth.register("teach", "Secret123", "faculty")
        admin.require("delete")
        faculty.require("write")
        with self.assertRaises(PermissionDenied):
            faculty.require("delete")
        with self.assertRaises(PermissionDenied):
            faculty.require("manage_users")

    def test_has_users(self):
        self.assertFalse(self.auth.has_users())
        self.auth.register("admin", "Secret123", "admin")
        self.assertTrue(self.auth.has_users())


if __name__ == "__main__":
    unittest.main()
