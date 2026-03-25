# 🌈 Bifrost (A Navigátor)
*Jira feladatok: DEV-P4*

A rendszer RAG (Retrieval-Augmented Generation) karmestere. 

## 🛠 Felelősségi körök
* **Vektorkeresés:** Szemantikus keresés a vektoradatbázisban a releváns kontextusért.
* **Prompt Engine:** A tökéletes kontextus-prompt összeállítása (Framework-less RAG Layer).
* **LLM Kommunikáció:** Közvetlen kapcsolat a külső/belső LLM API-val a tesztkérdések generálásához.
* **Továbbítás:** A nyers AI JSON válasz átadása a Heimdallnak.