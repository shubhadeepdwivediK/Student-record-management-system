import unittest

from srms.exceptions import DuplicateError, NotFoundError, ValidationError
from tests.base import BaseTest


class StudentCrudTests(BaseTest):
    def test_create_and_get(self):
        self.add_student()
        s = self.students.get("24bce1001")            # case-insensitive lookup
        self.assertEqual((s.name, s.department), ("Aarav Sharma", "CSE"))

    def test_duplicate_roll_and_email_rejected(self):
        self.add_student()
        with self.assertRaises(DuplicateError):
            self.add_student(email="other@example.com")           # same roll
        with self.assertRaises(DuplicateError):
            self.add_student(roll="24BCE1002")                    # same email

    def test_invalid_data_rejected(self):
        with self.assertRaises(ValidationError):
            self.students.create("24BCE1001", "Aarav", "bad-email", "CSE", 2)

    def test_update(self):
        self.add_student()
        self.students.update("24BCE1001", name="new name", year=3)
        s = self.students.get("24BCE1001")
        self.assertEqual((s.name, s.year), ("New Name", 3))

    def test_update_unknown_field_blocked(self):
        self.add_student()
        with self.assertRaises(KeyError):
            self.students.update("24BCE1001", roll_no="HACKED123")

    def test_delete_and_missing(self):
        self.add_student()
        self.students.delete("24BCE1001")
        with self.assertRaises(NotFoundError):
            self.students.get("24BCE1001")
        with self.assertRaises(NotFoundError):
            self.students.delete("24BCE1001")

    def test_list_filter_and_search(self):
        self.add_student()
        self.add_student("24BEC2001", "Rohan Verma", "r@example.com", "ece", 1)
        self.assertEqual(len(self.students.list()), 2)
        self.assertEqual([s.roll_no for s in self.students.list(department="ece")], ["24BEC2001"])
        self.assertEqual(len(self.students.search("rohan")), 1)
        self.assertEqual(self.students.search("   "), [])

    def test_sql_injection_is_inert(self):
        self.add_student()
        self.assertEqual(self.students.search("'; DROP TABLE students; --"), [])
        self.assertEqual(len(self.students.list()), 1)


if __name__ == "__main__":
    unittest.main()
