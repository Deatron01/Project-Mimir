# 🌈 Bifrost (A Navigátor)
*Jira feladatok: DEV-P4*

A rendszer RAG (Retrieval-Augmented Generation) karmestere. 

## 🛠 Felelősségi körök
* **Vektorkeresés:** Szemantikus keresés a vektoradatbázisban a releváns kontextusért.
* **Prompt Engine:** A tökéletes kontextus-prompt összeállítása (Framework-less RAG Layer).
* **LLM Kommunikáció:** Közvetlen kapcsolat a külső/belső LLM API-val a tesztkérdések generálásához.
* **Továbbítás:** A nyers AI JSON válasz átadása a Heimdallnak.

## 🔌 API Referencia

A Bifrost modul három végponttal rendelkezik: Vektorizálás (Ingest), Keresés (Search) és LLM Generálás (Generate).

### 1. `POST /api/v1/ingest`
Szöveg-chunkok beágyazása (embedding) és elmentése a Qdrant vektoradatbázisba.

* **Content-Type:** `application/json`
* **Request:**
    ```json
    {
        "chunks": [
            "Első bekezdés...", 
            "Második bekezdés..."
        ]
    }
    ```
* **Response (200 OK):**
    ```json
    {
        "message": "Sikeres indexelés",
        "indexed_chunks": 2
    }
    ```

### 2. `POST /api/v1/search`
Szemantikus RAG keresés a vektoradatbázisban egy kérdés alapján.

* **Content-Type:** `application/json`
* **Request:**
    ```json
    {
        "query": "Kik voltak a vikingek?",
        "limit": 3
    }
    ```
* **Response (200 OK):** Visszaadja a `limit` paraméternek megfelelő számú leginkább releváns bekezdést és azok hasonlósági pontszámát (score) a Qdrant adatbázisból.

### 3. `POST /api/v1/generate`
Keres a Qdrantban, majd a releváns kontextust átadja a lokális LLM-nek (pl. Qwen), amely egy strukturált vizsgakérdést generál.

* **Content-Type:** `application/json`
* **Request:**
    ```json
    {
        "query": "Kik vettek részt az Apollo-11 küldetésben?",
        "limit": 1,
        "format": "pdf"
    }
    ```
* **Response (200 OK):**
    ```json
    {
        "status": "success",
        "data": {
            "title": "Mimir AI Teszt",
            "format": "pdf",
            "questions": [
                {
                    "type": "mcq",
                    "text": "Kérdés szövege...",
                    "answers": [
                        {"text": "Helyes válasz", "is_correct": true},
                        {"text": "Rossz válasz", "is_correct": false}
                    ]
                }
            ]
        }
    }
    ```