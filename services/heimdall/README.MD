# 👁️ Heimdall (A Cenzor)
*Jira feladatok: DEV-P5*

Validációs és biztonsági réteg az AI kimenetek ellenőrzésére.

## 🛠 Felelősségi körök
* **JSON Schema Guard:** Az LLM-től érkező nyers válaszok manuális validációja szigorú sémák alapján.
* **Hallucináció-szűrés:** Megbízhatósági logikák futtatása a téves vagy oda nem illő válaszok kiszűrésére.
* **Biztonság:** Prompt injection támadások elleni védelem biztosítása.