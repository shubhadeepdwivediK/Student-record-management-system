import csv
import unittest

from srms.exceptions import NotFoundError, ValidationError
from tests.base import BaseTest


class GradeAndReportTests(BaseTest):
    def setUp(self):
        super().setUp()
        self.add_student("24BCE1001", "aarav sharma", "a@example.com", "cse")
        self.add_student("24BCE1002", "diya patel", "d@example.com", "cse")
        self.add_student("24BEC2001", "rohan verma", "r@example.com", "ece")
        self.courses.create("BCSE101", "Python", 4)
        self.courses.create("BMAT101", "Calculus", 2)

    def test_record_and_overwrite(self):
        self.grades.record("24BCE1001", "BCSE101", 80, 1)
        self.grades.record("24BCE1001", "BCSE101", 91, 1)       # upsert, not duplicate
        t = self.grades.transcript("24BCE1001")
        self.assertEqual(len(t["rows"]), 1)
        self.assertEqual(t["rows"][0]["grade"], "S")

    def test_record_validates_and_checks_existence(self):
        with self.assertRaises(ValidationError):
            self.grades.record("24BCE1001", "BCSE101", 150, 1)
        with self.assertRaises(NotFoundError):
            self.grades.record("24BCE9999", "BCSE101", 50, 1)
        with self.assertRaises(NotFoundError):
            self.grades.record("24BCE1001", "BXXX999", 50, 1)

    def test_transcript_cgpa(self):
        self.grades.record("24BCE1001", "BCSE101", 95, 1)       # 10 x 4
        self.grades.record("24BCE1001", "BMAT101", 65, 1)       # 7 x 2
        t = self.grades.transcript("24BCE1001")
        self.assertEqual(t["total_credits"], 6)
        self.assertEqual(t["cgpa"], 9.0)

    def test_deleting_student_cascades_to_grades(self):
        self.grades.record("24BCE1001", "BCSE101", 95, 1)
        self.students.delete("24BCE1001")
        self.assertEqual(self.grades.course_sheet("BCSE101")["rows"], [])

    def test_course_statistics(self):
        for roll, m in [("24BCE1001", 90), ("24BCE1002", 60), ("24BEC2001", 30)]:
            self.grades.record(roll, "BCSE101", m, 1)
        st = self.reports.course_statistics("BCSE101")
        self.assertEqual((st["count"], st["highest"], st["lowest"]), (3, 90, 30))
        self.assertEqual(st["mean"], 60.0)
        self.assertEqual(st["pass_rate"], 66.7)
        self.assertEqual(st["distribution"]["S"], 1)
        self.assertEqual(self.reports.course_statistics("BMAT101")["count"], 0)

    def test_rank_list_with_ties_and_filter(self):
        self.grades.record("24BCE1001", "BCSE101", 95, 1)
        self.grades.record("24BCE1002", "BCSE101", 96, 1)       # tie on CGPA 10
        self.grades.record("24BEC2001", "BCSE101", 75, 1)
        ranks = self.reports.rank_list()
        self.assertEqual([r[0] for r in ranks], [1, 1, 3])
        self.assertEqual([r[1] for r in self.reports.rank_list("ece")], ["24BEC2001"])

    def test_department_summary(self):
        self.grades.record("24BCE1001", "BCSE101", 95, 1)
        summary = {d["department"]: d for d in self.reports.department_summary()}
        self.assertEqual(summary["CSE"]["students"], 2)
        self.assertEqual(summary["CSE"]["avg_cgpa"], 10.0)
        self.assertIsNone(summary["ECE"]["avg_cgpa"])

    def test_csv_export_import_roundtrip(self):
        out = self.tmp / "students.csv"
        self.assertEqual(self.reports.export_students(out), 3)
        # Import into a fresh, empty system
        other = BaseTest("run"); other.setUp()
        try:
            added, errors = other.reports.import_students(out)
            self.assertEqual((added, errors), (3, []))
        finally:
            other.tearDown()

    def test_import_reports_bad_rows_without_aborting(self):
        path = self.tmp / "in.csv"
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["roll_no", "name", "email", "department", "year"])
            w.writerow(["24BCE7001", "Good Student", "good@example.com", "CSE", 1])
            w.writerow(["bad", "X", "nope", "CSE", 9])
            w.writerow(["24BCE1001", "Dup", "dup@example.com", "CSE", 1])   # duplicate roll
        added, errors = self.reports.import_students(path)
        self.assertEqual(added, 1)
        self.assertEqual(len(errors), 2)

    def test_import_rejects_wrong_columns_and_missing_file(self):
        path = self.tmp / "bad.csv"
        path.write_text("foo,bar\n1,2\n")
        with self.assertRaises(ValidationError):
            self.reports.import_students(path)
        with self.assertRaises(ValidationError):
            self.reports.import_students(self.tmp / "nope.csv")

    def test_transcript_export(self):
        self.grades.record("24BCE1001", "BCSE101", 95, 1)
        p = self.reports.export_transcript("24BCE1001", self.tmp / "t.csv")
        self.assertIn("BCSE101", p.read_text())


if __name__ == "__main__":
    unittest.main()
