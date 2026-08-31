# AIOCR — Transfer Certificate Field Extraction

This project accepts a student's Transfer Certificate (TC), School Leaving Certificate, or equivalent document and maps it to the six fields required by the VAPS admission form.

## Processing flow

```text
Image or PDF upload
        ↓
PDF pages converted to images when required
        ↓
Groq vision model
        ↓
JSON parsing and validation
        ↓
Admission form fields
```

The model receives the document image directly. A separate OCR engine is not required by this implementation.

## Extracted fields

```json
{
  "previous_school_name": "string or null",
  "previous_class": "string or null",
  "board": "string or null",
  "left_year": "YYYY or null",
  "reason_for_leaving": "string or null",
  "school_address": "string or null"
}
```

Unknown, missing, or unreliable values are returned as `null`.

## Requirements

- Python 3.10 or newer
- A Groq API key
- An internet connection for Groq API requests

## Installation

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file or export the variables in the shell:

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=qwen/qwen3.6-27b
GROQ_TIMEOUT_SECONDS=30
```

Never commit `.env` or expose `GROQ_API_KEY` in logs or source code. `.env.example` is provided as a template.

## Running the API

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 5007
```

The API will be available at:

```text
http://127.0.0.1:5007
```

Interactive API documentation is available at `/docs`.

## Running with Docker

Make sure `.env` contains a valid `GROQ_API_KEY`, then build and start the service:

```bash
docker compose up --build
```

To force a completely fresh image build:

```bash
docker compose build --no-cache
docker compose up -d
```

The API is exposed on port `5007`:

```text
http://127.0.0.1:5007/docs
```

Stop the service with:

```bash
docker compose down
```

Check container status and health:

```bash
docker compose ps
docker compose logs -f aiocr
```

## API endpoint

### `POST /api/ai/ocr/transfer-certificate`

Upload an image or PDF using the `file` multipart form field.

Example:

```bash
curl -X POST \
  http://127.0.0.1:5007/api/ai/ocr/transfer-certificate \
  -F "file=@sample-transfer-certificate.pdf"
```

Successful response:

```json
{
  "success": true,
  "document_type": "transfer_certificate",
  "fields": {
    "previous_school_name": "A.N.M. International School",
    "previous_class": "9th",
    "board": "CBSE",
    "left_year": "2020",
    "reason_for_leaving": "Parent's Request",
    "school_address": "Tahliwal, Tehsil Haroli, Distt. Una (H.P.)"
  }
}
```

## Supported uploads

- Image files such as JPEG, PNG, and WebP, sent directly to Groq.
- PDF files, rendered locally into images using PyMuPDF. The first three pages are sent to the vision model.

Unsupported files return HTTP `415`. Empty uploads return HTTP `400`.

## Validation

The service validates and normalizes the model output:

- Roman numeral and word-based classes are normalized, for example `IX` and `Ninth` become `9th`.
- `cbse` and `Cbse` become `CBSE`.
- `left_year` must contain exactly four digits; otherwise it becomes `null`.
- Extra model fields are rejected during extraction validation.
- Malformed model responses result in a controlled extraction error.

## Project structure

```text
app/
├── config.py                 Environment configuration
├── main.py                   FastAPI application and upload endpoint
├── models.py                 Pydantic response models
├── prompts.py                Groq system prompt
└── services/
    ├── groq_provider.py      Groq vision integration
    ├── ocr.py                Image/PDF document preparation
    └── tc_extractor.py       Field normalization and validation
tests/
└── test_tc_extractor.py      Unit tests for field validation
```

## Running tests

```bash
python -m unittest discover -s tests -v
```

The unit tests use a fake provider and do not make live Groq requests.

## Error handling

- `400`: missing or empty file
- `413`: file exceeds the configured upload limit
- `415`: unsupported file type or PDF conversion failure
- `502`: Groq failure, timeout, rate limit, malformed JSON, or schema extraction failure

Internal exception details and API keys are not returned to clients.

## Security notes

- Store secrets only in environment configuration.
- Do not log uploaded documents or sensitive student data unnecessarily.
- Do not commit `.env` files.
- Apply authentication, authorization, upload-size limits, and rate limiting before exposing the endpoint publicly.
