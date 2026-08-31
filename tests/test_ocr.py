import unittest

from app.services.ocr import DocumentConversionError, document_to_images


class DocumentPreparationTests(unittest.TestCase):
    def test_invalid_image_is_rejected(self):
        with self.assertRaises(DocumentConversionError):
            document_to_images(b"not an image", "image/jpeg", "tc.jpg")

    def test_empty_pdf_is_rejected(self):
        with self.assertRaises(DocumentConversionError):
            document_to_images(b"%PDF-invalid", "application/pdf", "tc.pdf")


if __name__ == "__main__":
    unittest.main()
