# 👁️ Heimdall (A Cenzor)
*Jira feladatok: DEV-P5*

Validációs és biztonsági réteg az AI kimenetek ellenőrzésére.

## 🛠 Felelősségi körök
* **JSON Schema Guard:** Az LLM-től érkező nyers válaszok manuális validációja szigorú sémák alapján.
* **Hallucináció-szűrés:** Megbízhatósági logikák futtatása a téves vagy oda nem illő válaszok kiszűrésére.
* **Biztonság:** Prompt injection támadások elleni védelem biztosítása.

## 🔌 API Referencia

A Heimdall az AI (LLM) által generált kérdések minőségbiztosításáért (Cenzor/Judge) felelős modul. 

### `POST /api/v1/evaluate`
Automatikusan leellenőrzi a generált kérdést tartalmi, logikai és pedagógiai szempontból, majd egy 0-10-es skálán pontozza azt.

* **Content-Type:** `application/json`
* **Request:** (A kiértékelendő JSON kérdéssor és opcionálisan a kontextus)
    ```json
    {
        "question": {
            "type": "mcq",
            "text": "Ki volt a parancsnok az Apollo-11 küldetés során?",
            "answers": [
                {"text": "Neil Armstrong", "is_correct": true},
                {"text": "Yuri Gagarin", "is_correct": false}
            ]
        },
        "context": "Az Apollo-11 küldetés során..."
    }
    ```
* **Response (200 OK):**
    ```json
    {
        "is_approved": true,
        "score": 9,
        "feedback": "Kiváló kérdés, a disztraktorok történelmileg hitelesek, a helyes válasz egyértelmű.",
        "flagged_issues": []
    }
    ```
* **Hibakódok:**
    * `422 Unprocessable Entity`: Hiányzó vagy hibás formátumú kérdés objektum.
    * `500 Internal Server Error`: Hiba az AI kiértékelő (LLM Judge) futtatása közben.