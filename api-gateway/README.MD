# 🚪 API Gateway & Auth

A Projekt Mimir publikus belépési pontja. 

## 🛠 Felelősségi körök
* **Forgalomirányítás:** Bejövő REST API kérések (`/api/v1/documents`, `/api/v1/tests`) elosztása a megfelelő szinkron szolgáltatások felé.
* **Biztonság:** JWT alapú hitelesítés ellenőrzése az Auth Service bevonásával.
* **Rate Limiting:** Túlterhelés elleni védelem (Redis cache támogatással).

## ⚙️ Technológia
* Nginx / Kong
* HTTPS / TLS