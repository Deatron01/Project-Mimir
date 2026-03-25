# ⚒️ The Forge (A Gépterem)
*Jira feladatok: DEV-P6*

Saját fejlesztésű, aszinkron worker-pool és feladat-orkesztrátor a külső message brokerek (pl. RabbitMQ) kiváltására.

## 🛠 Felelősségi körök
* **Orkesztráció:** A PostgreSQL adatbázis "feladatsor" táblájának pásztázása `FOR UPDATE SKIP LOCKED` logikával.
* **Erőforrás-elosztás:** A CPU és GPU igényes AI feladatok optimális kiosztása a worker node-ok között.
* **Folyamatvezérlés:** A Bifrost modul meghívása a generálási feladatokhoz.