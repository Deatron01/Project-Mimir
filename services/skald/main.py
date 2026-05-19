from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import uuid
import sqlite3
from datetime import datetime
from pdf_drawer import PDFDrawer # Feltételezve, hogy ez rajzolja a PDF-et

app = FastAPI(title="📝 Skald Export & Storage Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Az API Gateway mögött biztonságos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "/app/storage/history.db"
STORAGE_DIR = "/app/storage/pdf_files/"

# Biztosítjuk a mappa meglétét
os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_tests (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT,
            file_path TEXT,
            file_size TEXT,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# Kiterjesztjük a bejövő modellt a felhasználó azonosítójával
class ExportRequest(BaseModel):
    title: Optional[str] = "Mimir AI Vizsga"
    format: Optional[str] = "pdf"
    questions: List[Dict[str, Any]]
    user_id: Optional[str] = None # Itt érkezik a felhasználó emailje/ID-ja

def format_file_size(num_bytes: int) -> str:
    """Szépen formázott fájlméret (KB vagy MB)"""
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes / (1024 * 1024):.1f} MB"

@app.post("/api/v1/export")
async def export_pdf(request: ExportRequest):
    """PDF generálás és opcionális automatikus mentés a felhasználó tárhelyébe."""
    try:
        # A meglévő PDFDrawer meghívása (vagy a te egyedi PDF generáló logikád)
        drawer = PDFDrawer()
        pdf_bytes = drawer.generate(request.dict()) # Feltételezett generáló metódus, ami byte-okat ad vissza
        
        # Ha be van jelentkezve a felhasználó, elmentjük a személyes tárába is
        if request.user_id:
            job_id = str(uuid.uuid4())
            safe_title = request.title.replace(" ", "_").strip()
            filename = f"{job_id}_{safe_title}.pdf"
            file_path = os.path.join(STORAGE_DIR, filename)
            
            # Fájl kiírása a lemezre
            with open(file_path, "wb") as f:
                f.write(pdf_bytes)
                
            # Metaadatok összeszedése
            file_size = format_file_size(os.path.getsize(file_path))
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # Mentés az SQLite-ba
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO user_tests (id, user_id, title, file_path, file_size, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (job_id, request.user_id, request.title, file_path, file_size, current_date)
            )
            conn.commit()
            conn.close()
            print(f"💾 Teszt elmentve a felhasználóhoz ({request.user_id}). Méret: {file_size}")

        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generálási/mentési hiba: {str(e)}")

@app.get("/api/v1/tests")
async def list_user_tests(user_id: str):
    """Felhasználóhoz tartozó elmentett tesztek listázása."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, file_size, created_at FROM user_tests WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        rows = cursor.fetchall()
        conn.close()
        
        return [{"id": r["id"], "title": r["title"], "file_size": r["file_size"], "created_at": r["created_at"]} for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/tests/download/{test_id}")
async def download_specific_test(test_id: str):
    """Egy konkrét korábbi teszt újbóli letöltése ID alapján."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT file_path, title FROM user_tests WHERE id = ?", (test_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="A keresett fájl nem található.")
            
        file_path, title = row
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="A fájl fizikailag törlődött a szerverről.")
            
        return FileResponse(path=file_path, media_type="application/pdf", filename=f"{title}.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))