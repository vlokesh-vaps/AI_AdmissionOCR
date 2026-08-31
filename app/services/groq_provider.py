import base64
import json
import logging
from typing import Any, Protocol

from app.config import settings
from app.prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class LLMProvider(Protocol):
    def extract(self, ocr_text: str) -> dict[str, Any]: ...


class ExtractionError(RuntimeError):
    """Raised when the LLM cannot produce a valid extraction object."""


def _parse_json_object(content: str | None) -> dict[str, Any]:
    """Parse plain or Markdown-wrapped JSON returned by the model."""
    if not content or not content.strip():
        raise ExtractionError("Groq returned an empty response")
    text = content.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise ExtractionError("Groq returned non-JSON content") from None
        try:
            result = json.loads(text[start:end + 1])
        except json.JSONDecodeError as exc:
            raise ExtractionError("Groq returned malformed JSON") from exc
    if not isinstance(result, dict):
        raise ExtractionError("Groq response is not a JSON object")
    return result


class GroqProvider:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or settings.groq_api_key
        self.model = model or settings.groq_model

    def extract(self, ocr_text: str) -> dict[str, Any]:
        if not self.api_key:
            raise ExtractionError("GROQ_API_KEY is not configured")
        try:
            from groq import Groq
        except ImportError as exc:
            raise ExtractionError("Groq dependency is not installed") from exc

        try:
            client = Groq(api_key=self.api_key, timeout=settings.groq_timeout_seconds)
            response = client.chat.completions.create(
                model=self.model,
                temperature=0,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": ocr_text},
                ],
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            return _parse_json_object(content)
        except ExtractionError:
            raise
        except Exception as exc:
            raise ExtractionError("Groq extraction failed") from exc

    def extract_document(self, images: list[tuple[str, bytes]]) -> dict[str, Any]:
        """Send document page images directly to a Groq vision model."""
        if not self.api_key:
            raise ExtractionError("GROQ_API_KEY is not configured")
        try:
            from groq import Groq
            # Qwen vision requests have rejected JSON mode intermittently with
            # json_validate_failed. We validate the JSON locally instead.
            response_format = None
            content: list[dict[str, Any]] = [{"type": "text", "text":
                "Extract the requested fields from this transfer certificate. "
                "Return exactly the six JSON keys specified by the system prompt. "
                "Use JSON null for every missing value."}]
            for mime_type, image in images[:3]:
                encoded = base64.b64encode(image).decode("ascii")
                content.append({"type": "image_url", "image_url": {
                    "url": f"data:{mime_type};base64,{encoded}"
                }})
            logger.info("Groq document request: model=%s, pages=%d", self.model, len(images))
            request = {
                "model": self.model,
                "temperature": 0,
                "max_completion_tokens": 2048,
                "reasoning_effort": "none",
                "messages": [{"role": "system", "content": SYSTEM_PROMPT},
                             {"role": "user", "content": content}],
            }
            response = Groq(api_key=self.api_key, timeout=settings.groq_timeout_seconds).chat.completions.create(**request)
            message_content = response.choices[0].message.content
            logger.debug("Groq document response content=%r", message_content)
            return _parse_json_object(message_content)
        except ExtractionError:
            raise
        except Exception as exc:
            logger.exception("Groq document request failed")
            raise ExtractionError("Groq document extraction failed") from exc
