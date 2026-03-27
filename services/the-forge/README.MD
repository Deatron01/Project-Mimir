# ⚒️ The Forge (A Gépterem)
*Jira feladatok: DEV-P6*

Saját fejlesztésű, aszinkron worker-pool és feladat-orkesztrátor a külső message brokerek (pl. RabbitMQ) kiváltására.

## 🛠 Felelősségi körök
* **Orkesztráció:** A PostgreSQL adatbázis "feladatsor" táblájának pásztázása `FOR UPDATE SKIP LOCKED` logikával.
* **Erőforrás-elosztás:** A CPU és GPU igényes AI feladatok optimális kiosztása a worker node-ok között.
* **Folyamatvezérlés:** A Bifrost modul meghívása a generálási feladatokhoz.

## 🔌 API Referencia

A The Forge a Mimir aszinkron feladatkezelője. Felelős a hosszú ideig futó folyamatok (pl. 100 oldalas PDF feldolgozása) háttérben történő menedzseléséért PostgreSQL (és opcionálisan Celery/Redis) segítségével, hogy a felhasználói felület ne fagyjon le.

### 1. `POST /api/v1/jobs`
Új aszinkron vizsgagenerálási feladat (Job) beküldése a feldolgozási sorba.

* **Content-Type:** `multipart/form-data` vagy `application/json` (attól függően, hogy fájlt vagy nyers szöveget kap)
* **Request (Példa fájlfeltöltésre):**
    * `file`: `történelem_anyag.pdf`
    * `query`: "Készíts 5 kérdést a hidegháborúról!"
* **Response (202 Accepted):** (Azonnal visszatér, nem várja meg a generálást)
    ```json
    {
        "job_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "PENDING",
        "message": "A feladat bekerült a várakozási sorba."
    }
    ```

### 2. `GET /api/v1/jobs/{job_id}`
Egy adott feladat aktuális állapotának lekérdezése (Polling).

* **Path Parameter:** `job_id` (UUID formátumban)
* **Response (200 OK) - Ha még dolgozik:**
    ```json
    {
        "job_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "PROCESSING",
        "progress": "Bifrost RAG keresés folyamatban..."
    }
    ```
* **Response (200 OK) - Ha elkészült:**
    ```json
    {
        "job_id": "550e8400-e29b-41d4-a716-446655440000",
        "status": "COMPLETED",
        "result_url": "/api/v1/downloads/550e8400-e29b-41d4-a716-446655440000.pdf",
        "completed_at": "2026-03-27T12:50:46Z"
    }
    ```
* **Hibakódok:**
    * `404 Not Found`: A megadott `job_id` nem létezik az adatbázisban.
    * `500 Internal Server Error`: Adatbázis kapcsolati hiba.