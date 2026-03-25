# ᛋ RuneCarver (A Szobrász)
*Jira feladatok: DEV-P3*

Szemantikai daraboló (chunker) szolgáltatás a Wellspring mögött.

## 🛠 Felelősségi körök
* **Szövegfeldolgozás:** A nyers szöveg mondatokra bontása.
* **Szemantikai Chunking:** Koszinusz-hasonlóság alapján, a témaváltásoknál vágási pontok létrehozása (NumPy).
* **Feladatkiírás:** A darabolt szövegek (chunk-ok) mentése és "Feldolgozásra vár" státuszú feladat kiírása a PostgreSQL adatbázisba (The Forge számára).