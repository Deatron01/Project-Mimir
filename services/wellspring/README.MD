# 🌊 Wellspring (Az Archivista)
*Jira feladatok: DEV-P1, DEV-P2*

Szinkron API réteg (FastAPI / Node.js) és bináris szintű fájlfeldolgozó szolgáltatás.

## 🛠 Felelősségi körök
* **Fájlfogadás:** 20MB-ig terjedő PDF és DOCX fájlok fogadása.
* **Bináris Olvasás:** Native PDF Object Scanner (xref tábla, FlateDecode) és DOCX OpenXML Extractor (zipfile + xml.etree).
* **Archiválás:** Az eredeti fájlok elmentése a MinIO (S3) objektumtárolóba.
* **Továbbítás:** A kinyert nyers szöveg átadása a RuneCarver modulnak.

## 🔌 API Referencia

### `POST /api/v1/extract`
Feltöltött fájlok (PDF, TXT, DOCX) nyers szöveggé alakítása.

* **Content-Type:** `multipart/form-data`
* **Request:**
    * `file`: A feltöltendő bináris fájl (pl. `document.pdf`).
* **Response (200 OK):**
    ```json
    {
        "filename": "document.pdf",
        "content": "Ez itt a kinyert nyers szöveg...",
        "extraction_method": "NATIVE_TEXT"
    }
    ```
* **Hibakódok:**
    * `400 Bad Request`: Nincs fájl feltöltve, vagy nem támogatott formátum.
    * `500 Internal Server Error`: Hiba a fájl feldolgozása közben.