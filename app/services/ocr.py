import io


class DocumentConversionError(RuntimeError):
    """Raised when an upload cannot be prepared for vision input."""


def document_to_images(data: bytes, content_type: str | None, filename: str | None) -> list[tuple[str, bytes]]:
    """Return (mime type, bytes) page images without performing OCR."""
    is_pdf = content_type == "application/pdf" or (filename or "").lower().endswith(".pdf")
    if not is_pdf:
        if not content_type or not content_type.startswith("image/"):
            raise DocumentConversionError("Only image and PDF files are supported")
        try:
            from PIL import Image
            with Image.open(io.BytesIO(data)) as image:
                image.verify()
        except ImportError as exc:
            raise DocumentConversionError("Image support requires Pillow") from exc
        except Exception as exc:
            raise DocumentConversionError("Could not read image file") from exc
        return [(content_type, data)]
    try:
        import fitz
        document = fitz.open(stream=io.BytesIO(data), filetype="pdf")
        pages = list(document)[:3]
        if not pages:
            raise DocumentConversionError("PDF contains no pages")
        return [("image/png", page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5)).tobytes("png"))
                for page in pages]
    except ImportError as exc:
        raise DocumentConversionError("PDF support requires PyMuPDF") from exc
    except Exception as exc:
        raise DocumentConversionError("Could not convert PDF pages") from exc
