# 🌊 Wellspring (Az Archivista)
*Jira feladatok: DEV-P1, DEV-P2*

Szinkron API réteg (FastAPI / Node.js) és bináris szintű fájlfeldolgozó szolgáltatás.

## 🛠 Felelősségi körök
* **Fájlfogadás:** 20MB-ig terjedő PDF és DOCX fájlok fogadása.
* **Bináris Olvasás:** Native PDF Object Scanner (xref tábla, FlateDecode) és DOCX OpenXML Extractor (zipfile + xml.etree).
* **Archiválás:** Az eredeti fájlok elmentése a MinIO (S3) objektumtárolóba.
* **Továbbítás:** A kinyert nyers szöveg átadása a RuneCarver modulnak.