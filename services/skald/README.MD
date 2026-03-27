# 📜 Skald (Az Írnok)
*Jira feladatok: DEV-P7, DEV-P8*

Szinkron API réteg és exportáló motor a validált, kész tesztek formázására.

## 🛠 Felelősségi körök
* **Lekérdezés:** A generált, véglegesített adatok kinyerése a PostgreSQL adatbázisból export kérés (pl. `/api/v1/tests`) esetén.
* **Moodle XML:** Moodle XML Template Engine működtetése (CDATA és MathJax támogatással).
* **PDF Rajzolás:** Native PDF Test Drawer koordináta-alapú PDF rajzolással és automatikus tördeléssel.
* **JSON Export:** Szabványos JSON kimenet biztosítása.

## 🔌 API Referencia

### `POST /api/v1/export`
Szabványosított JSON vizsgaadatok fogadása és nyomtatásra kész, formázott PDF fájl rajzolása.

* **Content-Type:** `application/json`
* **Request:** (A Bifrost `generate` végpontja által visszaadott `data` objektum)
    ```json
    {
        "title": "Mimir AI Teszt",
        "format": "pdf",
        "questions": [
            {
                "type": "mcq",
                "text": "Kérdés szövege",
                "answers": [
                    {"text": "Válasz", "is_correct": true}
                ]
            }
        ]
    }
    ```
* **Response (200 OK):**
    * **Content-Type:** `application/pdf`
    * **Visszatérési érték:** Egy letölthető, bináris PDF fájlfolyam (stream).
* **Hibakódok:**
    * `422 Unprocessable Entity`: Érvénytelen JSON struktúra (pl. hiányzó mezők).
    * `500 Internal Server Error`: Hiba a PDF renderelése során.