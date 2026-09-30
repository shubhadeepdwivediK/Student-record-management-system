import unittest

from srms import validators as v
from srms.exceptions import ValidationError


class ValidatorTests(unittest.TestCase):
    def test_name_is_cleaned_and_titlecased(self):
        self.assertEqual(v.name("  aarav   sharma "), "Aarav Sharma")

    def test_bad_names_rejected(self):
        for bad in ["", "A", "12345", "Bob<script>"]:
            with self.assertRaises(ValidationError):
                v.name(bad)

    def test_email(self):
        self.assertEqual(v.email(" A@Example.COM "), "a@example.com")
        for bad in ["plain", "a@b", "@x.com", "a b@x.com"]:
            with self.assertRaises(ValidationError):
                v.email(bad)

    def test_roll_no(self):
        self.assertEqual(v.roll_no("24bce1001"), "24BCE1001")
        for bad in ["abc", "24-BCE-1001", "X" * 20]:
            with self.assertRaises(ValidationError):
                v.roll_no(bad)

    def test_phone_optional_but_checked(self):
        self.assertEqual(v.phone(""), "")
        self.assertEqual(v.phone("9876543210"), "9876543210")
        for bad in ["12345", "1234567890", "98765abcde"]:
            with self.assertRaises(ValidationError):
                v.phone(bad)

    def test_numeric_ranges(self):
        self.assertEqual(v.marks("87.456"), 87.46)
        self.assertEqual(v.credits("4"), 4)
        for fn, bad in [(v.marks, "101"), (v.marks, "-1"), (v.marks, "abc"),
                        (v.credits, "0"), (v.credits, "7"), (v.year, "9"),
                        (v.semester, "13"), (v.semester, "x")]:
            with self.assertRaises(ValidationError):
                fn(bad)

    def test_course_code(self):
        self.assertEqual(v.course_code("bcse101"), "BCSE101")
        with self.assertRaises(ValidationError):
            v.course_code("101BCSE")

    def test_password_strength(self):
        self.assertEqual(v.password("abcd1234"), "abcd1234")
        for bad in ["short1", "onlyletters", "12345678"]:
            with self.assertRaises(ValidationError):
                v.password(bad)


if __name__ == "__main__":
    unittest.main()
