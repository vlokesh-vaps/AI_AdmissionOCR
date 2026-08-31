import re
from typing import Any

from app.models import TCExtractionResult
from app.services.groq_provider import ExtractionError, LLMProvider

FIELDS = (
    "previous_school_name", "previous_class", "board", "left_year",
    "reason_for_leaving", "school_address",
)
CLASS_MAP = {
    "pre-nursery": "Pre-Nursery", "pre nursery": "Pre-Nursery", "prenursery": "Pre-Nursery",
    "pre-nursury": "Pre-Nursery", "pre nursury": "Pre-Nursery", "preprimary": "Pre-Primary",
    "pre-primary": "Pre-Primary", "pre primary": "Pre-Primary", "nursery": "Nursery",
    "nursury": "Nursery", "lkg": "LKG", "lowerkg": "LKG", "lowerkindergarten": "LKG",
    "ukg": "UKG", "upperkg": "UKG", "upperkindergarten": "UKG",
    "i": "1st", "ii": "2nd", "iii": "3rd", "iv": "4th", "v": "5th",
    "vi": "6th", "vii": "7th", "viii": "8th", "ix": "9th", "x": "10th",
    "xi": "11th", "xii": "12th", "first": "1st", "second": "2nd",
    "third": "3rd", "fourth": "4th", "fifth": "5th", "sixth": "6th",
    "seventh": "7th", "eighth": "8th", "ninth": "9th", "tenth": "10th",
    "eleventh": "11th", "twelfth": "12th",
}


def normalize_class(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    text = re.sub(r"\s+", " ", value.strip().lower())
    if text in CLASS_MAP:
        return CLASS_MAP[text]
    match = re.fullmatch(r"(\d{1,2})(?:st|nd|rd|th)?", text)
    if match:
        number = int(match.group(1))
        return f"{number}{'th' if 10 <= number % 100 <= 20 else {1:'st',2:'nd',3:'rd'}.get(number % 10, 'th')}"
    return None


def normalize_fields(raw: dict[str, Any]) -> TCExtractionResult:
    if not isinstance(raw, dict):
        raise ExtractionError("LLM response is not a JSON object")
    unexpected = set(raw) - set(FIELDS)
    if unexpected:
        raise ExtractionError("LLM response contains unexpected fields")
    data = {key: raw.get(key) if isinstance(raw.get(key), str) else None for key in FIELDS}
    for key in ("previous_school_name", "reason_for_leaving", "school_address"):
        if data[key] is not None:
            data[key] = data[key].strip() or None
    data["previous_class"] = normalize_class(data["previous_class"])
    if data["board"]:
        board = data["board"].strip()
        data["board"] = "CBSE" if board.casefold() == "cbse" else board or None
    if data["left_year"] and not re.fullmatch(r"\d{4}", data["left_year"].strip()):
        data["left_year"] = None
    elif data["left_year"]:
        data["left_year"] = data["left_year"].strip()
    return TCExtractionResult.model_validate(data)


def extract_tc_fields(ocr_text: str, provider: LLMProvider) -> TCExtractionResult:
    if not isinstance(ocr_text, str) or not ocr_text.strip():
        raise ExtractionError("OCR text is empty")
    raw = provider.extract(ocr_text)
    if not isinstance(raw, dict):
        raise ExtractionError("LLM response is not a JSON object")
    return normalize_fields(raw)
