# ᛋ RuneCarver (A Szobrász)
*Jira feladatok: DEV-P3*

Szemantikai daraboló (chunker) szolgáltatás a Wellspring mögött.

## 🛠 Felelősségi körök
* **Szövegfeldolgozás:** A nyers szöveg mondatokra bontása.
* **Szemantikai Chunking:** Koszinusz-hasonlóság alapján, a témaváltásoknál vágási pontok létrehozása (NumPy).
* **Feladatkiírás:** A darabolt szövegek (chunk-ok) mentése és "Feldolgozásra vár" státuszú feladat kiírása a PostgreSQL adatbázisba (The Forge számára).

## 🔌 API Referencia

### `POST /api/v1/chunk`
Nyers szöveg intelligens, szemantikai darabokra (chunkokra) bontása token-limit alapján.

* **Content-Type:** `application/json`
* **Request:**
    ```json
    {
        "filename": "document.txt",
        "extension": "txt",
        "content": "Ide jön a Wellspringből kapott hosszú nyers szöveg..."
    }
    ```
* **Response (200 OK):**
    ```json
    {
        "chunks": [
            "Első logikai bekezdés vagy téma...",
            "Második logikai bekezdés vagy téma..."
        ]
    }
    ```
* **Hibakódok:**
    * `422 Unprocessable Entity`: Hiányzó JSON paraméterek.
    * `500 Internal Server Error`: Hiba a darabolási algoritmusban.