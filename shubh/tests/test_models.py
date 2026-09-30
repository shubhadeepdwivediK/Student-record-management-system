import unittest

from srms.models import compute_cgpa, marks_to_grade


class GradingTests(unittest.TestCase):
    def test_grade_boundaries(self):
        cases = {100: "S", 90: "S", 89.99: "A", 80: "A", 70: "B", 60: "C",
                 50: "D", 45: "E", 44.99: "F", 0: "F"}
        for marks, letter in cases.items():
            self.assertEqual(marks_to_grade(marks)[0], letter, marks)

    def test_cgpa_is_credit_weighted(self):
        rows = [{"credits": 4, "marks": 95},   # 10 pts x 4
                {"credits": 2, "marks": 65}]   # 7 pts x 2
        self.assertEqual(compute_cgpa(rows), round((40 + 14) / 6, 2))

    def test_cgpa_empty(self):
        self.assertEqual(compute_cgpa([]), 0.0)


if __name__ == "__main__":
    unittest.main()
