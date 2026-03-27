# ⚙️ Projekt Mimir - Mikroszolgáltatások (Services)

Ez a mappa tartalmazza a Projekt Mimir (Intelligens Dokumentum-alapú Tesztgenerátor) magját alkotó, lazán csatolt backend mikroszolgáltatásokat. Minden egyes modul egy önálló FastAPI/Python alkalmazás, amely saját felelősségi körrel rendelkezik.

A szolgáltatások egymással HTTP kéréseken (REST API) és egy aszinkron PostgreSQL feladatsoron (`The Forge`) keresztül kommunikálnak.

## 🏛️ A Modulok Listája és Szerepük

A rendszer adatfolyama balról jobbra (feldolgozástól az exportálásig) haladva az alábbi modulokon megy keresztül:

* **[🌊 Wellspring](./wellspring/) (Az Archivista):**
  * **Feladat:** Szinkron belépési pont a fájlokhoz. Fogadja a feltöltött PDF/DOCX dokumentumokat, elmenti az eredetit a MinIO objektumtárolóba, majd saját bináris vagy OCR logikával kinyeri belőle a nyers szöveget.
  
* **[ᛋ RuneCarver](./runecarver/) (A Szobrász):**
  * **Feladat:** Szemantikai szövegtördelő. A nyers szöveget veszi át, és okos, koszinusz-hasonlóságon alapuló logikával, a témaváltások mentén kisebb egységekre (chunk-okra) darabolja az AI token-limitjéhez igazodva.

* **[🌈 Bifrost](./bifrost/) (A Navigátor):**
  * **Feladat:** A rendszer RAG (Retrieval-Augmented Generation) karmestere és AI hídja. Vektorizálja a chunkokat, kezeli a Qdrant vektoradatbázist, és összeállítja a kontextushoz kötött promptokat a nagy nyelvi modellek (LLM) számára.

* **[👁️ Heimdall](./heimdall/) (A Cenzor):**
  * **Feladat:** Biztonsági és minőségbiztosítási réteg. Szigorú JSON-sémákkal validálja az AI-tól érkező válaszokat, kiszűri a hallucinációkat, és értékeli a kérdések koherenciáját (LLM Judge).

* **[⚒️ The Forge](./the-forge/) (A Gépterem):**
  * **Feladat:** Natív aszinkron feladat-orkesztrátor. Külső message broker (pl. RabbitMQ) helyett PostgreSQL alapú, `FOR UPDATE SKIP LOCKED` technikával pásztázza az adatbázist, és skálázhatóan osztja el a hosszú futású AI feladatokat a workerek között.

* **[📜 Skald](./skald/) (Az Írnok):**
  * **Feladat:** Véglegesítő és exportáló motor. A legenerált, validált adatokat alakítja át a felhasználó által kért letölthető formátummá: Moodle XML (MathJax/CDATA támogatással) vagy koordináta-alapú, natív nyomtatható PDF.

## 🛠️ Fejlesztési Irányelvek
* Minden modulnak **saját `Docker/Dockerfile` és `Docker/requirements.txt`** fájlja van a teljes izoláció érdekében.
* A közös típusok és segédfüggvények a gyökérkönyvtár `../shared/` mappájában találhatók.
* A lokális teszteléshez az indítás a gyökérben lévő `docker-compose.yml` segítségével történik (`docker-compose up --build`).