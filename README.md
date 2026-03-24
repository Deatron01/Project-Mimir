# 🌳 Projekt Mimir
**Intelligens Dokumentum-alapú Tesztgenerátor (IDTG)**

> *"Mímir kútjából fakad a tudás és a megértés. Aki iszik belőle, meglátja a rendet a káoszban."*

A **Projekt Mimir** egy mesterséges intelligencia által vezérelt, mikroszolgáltatás-alapú rendszer, amely képes nyers dokumentumokból automatikusan strukturált, oktatási célú teszteket és vizsgakérdéseket generálni. A projekt különlegessége, hogy a dokumentum-feldolgozástól kezdve az AI-vezérlésen át a PDF/XML exportálásig mindent saját, "kézzel írt", mélyreható algoritmusok hajtanak végre, mellőzve a túlzottan absztrakt külső keretrendszereket.

---

## ✨ Főbb funkciók

* **Dokumentum-feldolgozás:** PDF, DOCX és TXT formátumok támogatása egészen 20MB-os fájlméretig.
* **Intelligens Tesztgenerálás:** Feleletválasztós (MCQ), igaz-hamis és kifejtős (esszé) kérdések automatikus létrehozása.
* **Dinamikus nehézség:** A generált kérdések szintje paraméterezhető (Kezdő, Közép, Haladó).
* **RAG-alapú pontosság:** Beépített Retrieval-Augmented Generation logika a hallucinációk minimalizálása érdekében.
* **Interaktív Szerkesztő:** A generált tesztek valós idejű módosítása, törlése és kiegészítése a véglegesítés előtt.
* **Multi-formátumú Export:** A kész tesztek letöltése JSON (adatcsere), Moodle XML (LMS integráció) és nyomtatható PDF formátumban.

---

## 🏛️ Architektúra és Modulok

A rendszer lazán csatolt, skálázható mikroszolgáltatásokból áll. A modulok az északi mitológia tudással és teremtéssel kapcsolatos elemeiről kapták a nevüket:

1. **🌊 Wellspring (Az Archivista):** Bináris szintű fájlfeldolgozó, amely saját logikával nyeri ki a tiszta szöveget és táblázatokat a PDF/DOCX fájlokból.
2. **ᛋ RuneCarver (A Szobrász):** Szemantikai daraboló modul, amely mondatokra bontja a szöveget, és koszinusz-hasonlóság alapján, a témaváltásoknál hoz létre vágási pontokat.
3. **🌈 Bifrost (A Navigátor):** A RAG-karmester. Közvetlenül kommunikál a vektoradatbázissal és az LLM API-val, összeállítva a tökéletes kontextus-promptot.
4. **👁️ Heimdall (A Cenzor):** Szigorú JSON-sémák és megbízhatósági logikák alapján szűri az AI válaszait, megakadályozva a hallucinációkat és a prompt injection támadásokat.
5. **⚒️ The Forge (A Gépterem):** A PostgreSQL adatbázisra és `FOR UPDATE SKIP LOCKED` logikára épülő saját worker-pool, amely optimálisan elosztja a CPU és GPU igényes feladatokat.
6. **📜 Skald (Az Írnok):** Az exportáló motor, amely manuálisan fűzi össze a Moodle XML-t (CDATA és MathJax támogatással), és saját rajzoló logikával készíti a PDF-eket.

---

## 🛠️ Technológiai Stack

* **Háttérrendszer:** Python (FastAPI) és Node.js a szolgáltatásokhoz.
* **Adatbázisok:** PostgreSQL a strukturált metaadatokhoz, MinIO (S3 kompatibilis) a bináris fájlokhoz.
* **Gyorsítótár:** Redis a gyakori lekérdezések és session-ök tárolására, optimalizálva a költségeket.
* **Biztonság:** JWT (JSON Web Token) alapú autentikáció és TLS titkosítás.
* **Infrastruktúra:** Docker konténerizáció és Kubernetes (HPA) a felhős skálázhatóságért.
