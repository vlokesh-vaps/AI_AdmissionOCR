import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.services.groq_provider import ExtractionError, _parse_json_object


class JSONParserTests(unittest.TestCase):
    def test_plain_json(self):
        self.assertEqual(_parse_json_object('{"board": "CBSE"}'), {"board": "CBSE"})

    def test_markdown_json(self):
        self.assertEqual(_parse_json_object('```json\n{"board": "CBSE"}\n```'), {"board": "CBSE"})

    def test_json_inside_explanation(self):
        self.assertEqual(_parse_json_object('Here is the result:\n{"board": "CBSE"}'), {"board": "CBSE"})

    def test_empty_response_fails(self):
        with self.assertRaises(ExtractionError):
            _parse_json_object("")
