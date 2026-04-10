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
    """A fő aszinkron worker ciklus FOR UPDATE SKIP LOCKED logikával."""
    print("⚒️ The Forge Worker elindult és figyeli a 'pending' feladatokat...")
    
    # Kisebb késleltetés induláskor, hogy a Postgres konténer biztosan készen álljon
    await asyncio.sleep(5)
    
    try:
        conn = await asyncpg.connect(DB_URL)
    except Exception as e:
        print(f"Worker nem tudott csatlakozni a DB-hez: {e}")
        return

    while True:
        try:
            # Tranzakció indítása a feladat lefoglalásához
            async with conn.transaction():
                # Megkeressük a legrégebbi 'pending' feladatot és ZÁROLJUK, 
                # de a SKIP LOCKED miatt nem blokkoljuk a többi workert.
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
                    payload = json.loads(task['payload']) if isinstance(task['payload'], str) else task['payload']
                    
                    print(f"[{task_id}] Feladat lefoglalva. Típus: {task_type}")
                    
                    # 1. Státusz frissítése: feldolgozás alatt
                    await conn.execute("UPDATE task_queue SET status = 'processing' WHERE id = $1", task_id)
                    
                    # 2. FELADAT VÉGREHAJTÁSA (Orkesztráció)
                    if task_type == 'index_chunks':
                        # Ha a feladat a chunkok indexelése, szólunk a Bifrostnak
                        async with httpx.AsyncClient() as client:
                            response = await client.post(f"{BIFROST_URL}/api/v1/ingest", json=payload)
                            response.raise_for_status()
                    
                    # (Ide jöhet a többi task_type logika a jövőben, pl. 'generate_test')
                    
                    # 3. Státusz frissítése: kész
                    await conn.execute("UPDATE task_queue SET status = 'completed' WHERE id = $1", task_id)
                    print(f"[{task_id}] Feladat sikeresen befejezve!")
                else:
                    # Nincs új feladat, várunk egy picit, hogy ne pörgessük a CPU-t feleslegesen
                    await asyncio.sleep(2)
        except Exception as e:
            print(f"Hiba a feladat végrehajtása közben: {e}")
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