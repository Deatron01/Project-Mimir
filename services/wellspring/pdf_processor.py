import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import re
import os
import base64
import httpx

class PDFProcessor:
    def __init__(self):
        tesseract_path = os.getenv("TESSERACT_CMD", "/usr/bin/tesseract")
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
        print(f"🌊 Wellspring PDF Processor inicializálva. Tesseract: {tesseract_path}")

    def _is_text_readable(self, text):
        """Ellenőrzi, hogy a kinyert szöveg értelmes-e (nem csak kódolási hibás szemét)."""
        if not text or len(text.strip()) == 0:
            return 0.0, False
        text_no_spaces = re.sub(r'\s+', '', text)
        normal_chars = len(re.findall(r'[\w\.,\-\?!:\(\)\[\]/@+]', text_no_spaces))
        if len(text_no_spaces) == 0:
            return 0.0, False
        ratio = normal_chars / len(text_no_spaces)
        return ratio, ratio >= 0.85 

    def _extract_via_vlm(self, image_bytes: bytes) -> str:
        """Kép feldolgozása a Qwen3-VL (Vision) modellel a GenAI szerveren."""
        api_key = os.getenv("OE_GENAI_API_KEY")
        if not api_key:
            return None # Ha nincs kulcs, egyből menjen az OCR fallback-re

        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        genai_url = "https://genai.uni-obuda.hu/api/chat/completions"
        model_name = "qwen3-vl:8b"

        prompt = """Te egy precíz adatkinyerő AI vagy. Kérlek, olvasd el és alakítsd pontos szöveggé a képen látható dokumentum-részletet. 
        A táblázatokat, listákat és képleteket tartsd meg markdown formátumban. 
        CSAK a leolvasott szöveget add vissza, semmilyen bevezetőt vagy kommentárt ne írj!"""

        try:
            print(f"👁️ Wellspring: Komplex oldal észlelve, küldés a '{model_name}' VLM-nek...")
            # Szinkron httpx kliens, mivel a fájlfeldolgozásod jelenleg szinkron fut
            with httpx.Client(timeout=120.0, trust_env=False) as client:
                response = client.post(
                    genai_url,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model_name,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                                ]
                            }
                        ]
                    }
                )
                response.raise_for_status()
                vlm_text = response.json()["choices"][0]["message"]["content"].strip()
                print("✅ Wellspring: VLM sikeresen leolvasta az oldalt.")
                return vlm_text
        except Exception as e:
            print(f"⚠️ Wellspring: VLM hiba ({e}), átállás natív OCR-re...")
            return None

    def _extract_via_ocr(self, image_bytes: bytes) -> str:
        """Hagyományos Tesseract OCR fallback."""
        img = Image.open(io.BytesIO(image_bytes))
        return pytesseract.image_to_string(img, lang='hun+eng')

    def process_pdf_bytes(self, pdf_bytes: bytes):
        """Oldalankénti intelligens feldolgozás: Natív szöveg -> VLM -> OCR."""
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        full_extracted_text = ""
        processing_methods = set()
        
        for page_num, page in enumerate(doc):
            text = page.get_text()
            img_list = page.get_images(full=True)
            
            ratio, readable = self._is_text_readable(text)

            # 1. ESET: Tiszta, natívan olvasható szöveg (képek nélkül vagy kevés képpel)
            if readable and len(img_list) == 0:
                full_extracted_text += text + "\n\n"
                processing_methods.add("NATIVE")
            
            # 2. ESET: Komplex oldal (Képek, ábrák, vagy olvashatatlan vektoros fontok)
            else:
                # Kép renderelése az adott oldalról
                pix = page.get_pixmap(dpi=300)
                img_bytes = pix.tobytes("png")

                # Próba a Qwen3-VL modellel
                extracted_content = self._extract_via_vlm(img_bytes)

                if extracted_content:
                    full_extracted_text += extracted_content + "\n\n"
                    processing_methods.add("VLM_VISION")
                else:
                    # Végső mentsvár: Tesseract OCR
                    ocr_text = self._extract_via_ocr(img_bytes)
                    full_extracted_text += ocr_text + "\n\n"
                    processing_methods.add("OCR_FALLBACK")

        # Metódusok összefűzése a frontend/audit számára (pl. "NATIVE + VLM_VISION")
        final_method = " + ".join(sorted(list(processing_methods))) if processing_methods else "UNKNOWN"
        
        return full_extracted_text, final_method