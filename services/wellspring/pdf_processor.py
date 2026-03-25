import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import re
import os

class PDFProcessor:
    def __init__(self):
        tesseract_path = os.getenv("TESSERACT_CMD", "/usr/bin/tesseract")
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        print(f"Wellspring PDF Processor inicializálva. Tesseract útvonal: {tesseract_path}")

    def _is_text_readable(self, text):
        if not text or len(text.strip()) == 0:
            return 0.0, False
        text_no_spaces = re.sub(r'\s+', '', text)
        normal_chars = len(re.findall(r'[\w\.,\-\?!:\(\)\[\]/@+]', text_no_spaces))
        if len(text_no_spaces) == 0:
            return 0.0, False
        ratio = normal_chars / len(text_no_spaces)
        return ratio, ratio >= 0.85 

    def _extract_via_ocr(self, doc):
        extracted_text = ""
        for page in doc:
            pix = page.get_pixmap(dpi=300)
            img = Image.open(io.BytesIO(pix.tobytes("png")))
            text = pytesseract.image_to_string(img, lang='hun+eng')
            extracted_text += text + "\n\n"
        return extracted_text

    def process_pdf_bytes(self, pdf_bytes: bytes):
        """Közvetlenül bájtokból olvas, API-barát megközelítés."""
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)
        text_pages, image_heavy_pages = 0, 0
        full_extracted_text = ""
        
        for page in doc:
            text = page.get_text()
            full_extracted_text += text
            img_list = page.get_images(full=True)
            
            if len(text.strip()) > 50 and len(img_list) == 0:
                text_pages += 1
            else:
                image_heavy_pages += 1

        if image_heavy_pages == total_pages and text_pages == 0:
            return self._extract_via_ocr(doc), "OCR"
        
        ratio, readable = self._is_text_readable(full_extracted_text)
        if readable:
            return full_extracted_text, "NATIVE"
        else:
            return self._extract_via_ocr(doc), "OCR"