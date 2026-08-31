import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.services.groq_provider import ExtractionError
from app.services.tc_extractor import extract_tc_fields, normalize_fields


class FakeProvider:
    def __init__(self, value): self.value = value
    def extract(self, _): return self.value


class TCExtractorTests(unittest.TestCase):
    def test_normal_tc(self):
        result = extract_tc_fields("sample OCR", FakeProvider({
            "previous_school_name": " A.N.M. International School ", "previous_class": "Ninth",
            "board": "cbse", "left_year": "2020", "reason_for_leaving": "Parent's Request",
            "school_address": "Tahliwal, Tehsil Haroli, Distt. Una (H.P.)",
        }))
        self.assertEqual(result.previous_class, "9th")
        self.assertEqual(result.board, "CBSE")
        self.assertEqual(result.left_year, "2020")

    def test_missing_reason_is_null(self):
        result = extract_tc_fields("sample OCR", FakeProvider({"previous_class": "IX"}))
        self.assertIsNone(result.reason_for_leaving)
        self.assertEqual(result.previous_class, "9th")

    def test_invalid_year_is_null(self):
        result = extract_tc_fields("DOB 15.06.2005", FakeProvider({"left_year": "15.06.2005"}))
        self.assertIsNone(result.left_year)

    def test_unexpected_fields_are_rejected(self):
        with self.assertRaises(ExtractionError):
            normalize_fields({"board": "CBSE", "student_name": "Someone"})


if __name__ == "__main__":
    unittest.main()
