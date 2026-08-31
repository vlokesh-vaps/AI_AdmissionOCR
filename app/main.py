"""FastAPI application for TC field extraction via Groq vision."""

import logging
import sys

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse

from app.config import settings
from app.models import TCExtractionResponse
from app.services.groq_provider import ExtractionError, GroqProvider
from app.services.ocr import DocumentConversionError, document_to_images
from app.services.tc_extractor import normalize_fields

# --- Structured logging ---
_formatter = logging.Formatter(
    '{"timestamp":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}',
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(_formatter)
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    handlers=[_handler],
    force=True,
)
for _noisy in ("urllib3", "httpx", "httpcore"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

_MAX_UPLOAD_BYTES = settings.max_upload_mb * 1024 * 1024

app = FastAPI(title="AIOCR Admission API", version="1.0.1")


@app.exception_handler(Exception)
async def _global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled_error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "An internal error occurred."})


@app.get("/health")
def health() -> dict:
    """Health check endpoint for load balancers and orchestration."""
    return {
        "status": "ok",
        "service": "ocr_service",
        "groq_model": settings.groq_model,
    }


@app.post("/api/ai/ocr/transfer-certificate", response_model=TCExtractionResponse)
async def transfer_certificate(file: UploadFile | None = File(None)):
    if file is None:
        raise HTTPException(status_code=400, detail="Missing file")
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing file")
    try:
        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail="Empty file")
        if len(data) > _MAX_UPLOAD_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum upload size is {settings.max_upload_mb} MB.",
            )
        images = document_to_images(data, file.content_type, file.filename)
        logger.info("Processing TC upload: filename=%s, content_type=%s, pages=%d",
                     file.filename, file.content_type, len(images))
        fields = normalize_fields(GroqProvider().extract_document(images))
        return TCExtractionResponse(success=True, fields=fields)
    except DocumentConversionError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except ExtractionError as exc:
        logger.warning("TC extraction failed: %s", exc)
        raise HTTPException(status_code=502, detail="TC extraction failed") from exc
