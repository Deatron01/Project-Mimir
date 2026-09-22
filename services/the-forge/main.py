import asyncio
import os
import json
import httpx
import asyncpg
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import hashlib

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

# GDPR: az MI működési napló megőrzési ideje (nap). A régebbi sorokat óránként töröljük.
AUDIT_RETENTION_DAYS = int(os.getenv("AUDIT_RETENTION_DAYS", "30"))


async def init_db():
    try:
        conn = await asyncpg.connect(DB_URL)
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS task_queue (
                id SERIAL PRIMARY KEY,
                task_type VARCHAR(100) NOT NULL,
                payload JSONB,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Audit napló az MI-rendelet miatt – GDPR szerint CSAK metaadat és lenyomat, dokumentumszöveg nélkül.
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id SERIAL PRIMARY KEY,
                job_id VARCHAR(255),
                user_query TEXT,
                used_prompt TEXT,
                rag_context TEXT,
                model_name VARCHAR(100),
                qa_score FLOAT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        for column, ctype in (
            ("prompt_version", "VARCHAR(50)"),
            ("query_sha256", "CHAR(64)"),
            ("prompt_sha256", "CHAR(64)"),
            ("context_sha256", "CHAR(64)"),
            ("query_chars", "INTEGER"),
            ("context_chars", "INTEGER"),
        ):
            await conn.execute(f"ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS {column} {ctype}")

        # Régi (a GDPR-javítás előtti) sorok: a tartalmat tartalmazó oszlopok kiürítése.
        scrubbed = await conn.execute('''
            UPDATE audit_logs SET user_query = NULL, used_prompt = NULL, rag_context = NULL
            WHERE user_query IS NOT NULL OR used_prompt IS NOT NULL OR rag_context IS NOT NULL
        ''')
        await conn.close()
        print(f"Gépterem (DB) és audit napló inicializálva. Régi tartalom kiürítve: {scrubbed}")
    except Exception as e:
        print(f"Hiba az adatbázis csatlakozáskor: {e}")


async def purge_audit_logs_loop():
    """Óránként törli a megőrzési időn túli audit sorokat (GDPR tárolási korlátozás)."""
    await asyncio.sleep(10)
    while True:
        try:
            conn = await asyncpg.connect(DB_URL)
            result = await conn.execute(
                "DELETE FROM audit_logs WHERE created_at < NOW() - make_interval(days => $1)",
                AUDIT_RETENTION_DAYS,
            )
            await conn.close()
            print(f"🧹 Audit napló megőrzési törlés ({AUDIT_RETENTION_DAYS} nap): {result}")
        except Exception as e:
            print(f"⚠️ Audit napló törlési hiba: {e}")
        await asyncio.sleep(3600)


class AuditLogRequest(BaseModel):
    """Csak metaadat. A régi kliensek által küldött szöveges mezőket elfogadjuk, de NEM tároljuk."""
    job_id: str
    model_name: str
    qa_score: Optional[float] = None
    prompt_version: Optional[str] = None
    query_sha256: Optional[str] = None
    prompt_sha256: Optional[str] = None
    context_sha256: Optional[str] = None
    query_chars: Optional[int] = None
    context_chars: Optional[int] = None
    # Elavult mezők (figyelmen kívül hagyva):
    user_query: Optional[str] = None
    used_prompt: Optional[str] = None
    rag_context: Optional[str] = None

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
    # GDPR: az audit napló automatikus törlése
    asyncio.create_task(purge_audit_logs_loop())

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
    
@app.post("/api/v1/audit")
async def create_audit_log(log: AuditLogRequest):
    # Ha régi kliens szöveget küld, abból is csak lenyomat és hossz kerül tárolásra.
    def digest(value, given):
        if given:
            return given
        return hashlib.sha256(value.encode("utf-8")).hexdigest() if value else None

    try:
        conn = await asyncpg.connect(DB_URL)
        await conn.execute('''
            INSERT INTO audit_logs (job_id, model_name, qa_score, prompt_version,
                                    query_sha256, prompt_sha256, context_sha256, query_chars, context_chars)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ''',
            log.job_id, log.model_name, log.qa_score, log.prompt_version,
            digest(log.user_query, log.query_sha256),
            digest(log.used_prompt, log.prompt_sha256),
            digest(log.rag_context, log.context_sha256),
            log.query_chars if log.query_chars is not None else (len(log.user_query) if log.user_query else None),
            log.context_chars if log.context_chars is not None else (len(log.rag_context) if log.rag_context else None),
        )
        await conn.close()
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
