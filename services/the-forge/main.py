import asyncio
import os
import json
import httpx
import asyncpg
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="⚒️ The Forge Service", description="Natív aszinkron feladat-orkesztrátor")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://mimir-ai.hu",
        "https://www.mimir-ai.hu"
    ], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Környezeti változók a Dockerből
DB_URL = os.getenv("POSTGRES_URL", "postgresql://mimir_user:mimir_password@postgres:5432/mimir_db")
BIFROST_URL = os.getenv("BIFROST_URL", "http://bifrost:8000")

async def init_db():
    """Létrehozza a feladatsor táblát, ha még nem létezik."""
    try:
        conn = await asyncpg.connect(DB_URL)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS task_queue (
                id SERIAL PRIMARY KEY,
                task_type VARCHAR(50),
                payload JSONB,
                status VARCHAR(20) DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        await conn.close()
        print("Gépterem (DB) inicializálva.")
    except Exception as e:
        print(f"Hiba az adatbázis csatlakozáskor: {e}")

async def worker_loop():
    """
    A fő aszinkron worker ciklus javított változata:
    - Connection Pool a stabil adatbázis-kezeléshez.
    - Megemelt HTTP timeout a Bifrost hívásokhoz.
    - Robusztus hibakezelés.
    """
    print("⚒️ The Forge Worker elindult és figyeli a 'pending' feladatokat...")
    
    # 1. Késleltetés induláskor az infrastruktúra (Postgres) beállásához
    await asyncio.sleep(5)
    
    # 2. Connection Pool létrehozása
    try:
        pool = await asyncpg.create_pool(
            DB_URL, 
            min_size=1, 
            max_size=10,
            command_timeout=60
        )
        print("⚒️ Adatbázis Pool sikeresen létrehozva.")
    except Exception as e:
        print(f"❌ Kritikus hiba: Nem sikerült csatlakozni az adatbázishoz: {e}")
        return

    while True:
        try:
            # 3. Élő kapcsolat kérése a pool-ból minden ciklusban
            async with pool.acquire() as conn:
                # Tranzakció indítása a feladat biztonságos lefoglalásához
                async with conn.transaction():
                    task = await conn.fetchrow('''
                        SELECT id, task_type, payload 
                        FROM task_queue 
                        WHERE status = 'pending' 
                        ORDER BY created_at ASC
                        FOR UPDATE SKIP LOCKED 
                        LIMIT 1
                    ''')
                    
                    if task:
                        task_id = task['id']
                        task_type = task['task_type']
                        # Payload biztonságos betöltése
                        payload = json.loads(task['payload']) if isinstance(task['payload'], str) else task['payload']
                        
                        print(f"[{task_id}] Feladat lefoglalva. Típus: {task_type}")
                        
                        # Feldolgozás megkezdése
                        await conn.execute("UPDATE task_queue SET status = 'processing' WHERE id = $1", task_id)
                        
                        # 4. Orkesztráció végrehajtása (Bifrost hívás hosszú timeouttal)
                        if task_type == 'index_chunks':
                            # 300 másodperc (5 perc) várakozási idő az AI generálásra
                            async with httpx.AsyncClient(timeout=300.0) as client:
                                response = await client.post(f"{BIFROST_URL}/api/v1/ingest", json=payload)
                                response.raise_for_status()
                        
                        # 5. Sikeres befejezés adminisztrálása
                        await conn.execute("UPDATE task_queue SET status = 'completed' WHERE id = $1", task_id)
                        print(f"[{task_id}] Feladat sikeresen befejezve!")
                    
                    else:
                        # Nincs új feladat, pihentetjük a ciklust
                        await asyncio.sleep(2)

        except Exception as e:
            # Bármilyen hiba (hálózati szakadás, timeout stb.) esetén várakozás, majd újrapróbálkozás
            print(f"⚠️ Hiba a feladat végrehajtása közben: {e}. Újrapróbálkozás 5 másodperc múlva...")
            await asyncio.sleep(5)

@app.on_event("startup")
async def startup_event():
    # Először inicializáljuk a táblát
    await init_db()
    # Majd elindítjuk a háttérben a végtelenített worker ciklust
    asyncio.create_task(worker_loop())

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "the-forge"}

@app.post("/api/v1/tasks")
async def create_task(task_type: str, payload: dict):
    """Végpont egy új feladat manuális vagy szolgáltatás általi beküldésére."""
    try:
        conn = await asyncpg.connect(DB_URL)
        await conn.execute('''
            INSERT INTO task_queue (task_type, payload) VALUES ($1, $2)
        ''', task_type, json.dumps(payload))
        await conn.close()
        return {"status": "success", "message": "Feladat sikeresen beütemezve a Gépterembe."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))