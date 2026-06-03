from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import io
import uuid
import sqlite3
from datetime import datetime

# --- REPORTLAB IMPORTOK A USER KÓDJA ALAPJÁN ---
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import PageBreak

app = FastAPI(title="📝 Skald Export & Storage Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- PERZISZTENS ADATBÁZIS ÉS TÁRHELY BEÁLLÍTÁSA ---
DB_PATH = "/app/storage/history.db"
STORAGE_DIR = "/app/storage/pdf_files/"

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


# --- A FELHASZNÁLÓ NATIV PDF RAJZOLÓ OSZTÁLYA ---
class NativePDFDrawer:
    def __init__(self):
        # --- BETŰTÍPUS REGISZTRÁLÁSA ---
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        font_bold_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        
        try:
            pdfmetrics.registerFont(TTFont('DejaVu', font_path))
            pdfmetrics.registerFont(TTFont('DejaVu-Bold', font_bold_path))
            self.font_regular = 'DejaVu'
            self.font_bold = 'DejaVu-Bold'
        except Exception as e:
            print(f"Figyelem: Fallback Helvetica-ra. Hiba: {e}")
            self.font_regular = 'Helvetica'
            self.font_bold = 'Helvetica-Bold'

    def draw_test(self, questions: list, title="Generált Vizsgateszt", metadata: dict = None) -> bytes:
        buffer = io.BytesIO()
        
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4, 
            rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50
        )
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'TitleStyle',
            fontName=self.font_bold,
            fontSize=20,
            alignment=1,
            spaceAfter=30
        )
        
        question_style = ParagraphStyle(
            'QuestionStyle',
            fontName=self.font_bold,
            fontSize=12,
            leading=16,
            spaceBefore=15,
            spaceAfter=10
        )
        
        answer_style = ParagraphStyle(
            'AnswerStyle',
            fontName=self.font_regular,
            fontSize=11,
            leftIndent=20,
            spaceAfter=6
        )

        elements = []

        elements.append(Paragraph(title, title_style))
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceAfter=20))

        for idx, q in enumerate(questions, 1):
            q_text = q.get('text', '').replace('$', '')
            elements.append(Paragraph(f"{idx}. {q_text}", question_style))
            
            if q.get('type') in ['mcq', 'tf']:
                labels = ['A)', 'B)', 'C)', 'D)', 'E)']
                for i, ans in enumerate(q.get('answers', [])):
                    label = labels[i] if i < len(labels) else "•"
                    ans_text = ans.get('text', '').replace('$', '')
                    elements.append(Paragraph(f"{label} {ans_text}", answer_style))
            
            elif q.get('type') == 'open':
                elements.append(Paragraph("_" * 80, answer_style))
                elements.append(Spacer(1, 10))

        if metadata:
            elements.append(PageBreak()) # Új oldal kezdete
            elements.append(Paragraph("Vizsga metaadatok", title_style))
            
            meta_style = ParagraphStyle('MetaStyle', fontName=self.font_regular, fontSize=10, spaceAfter=6)
            
            elements.append(Paragraph(f"<b>Használt modell:</b> {metadata.get('model_used')}", meta_style))
            elements.append(Paragraph(f"<b>Token szám:</b> {metadata.get('tokens_generated')}", meta_style))
            elements.append(Paragraph(f"<b>Generálás ideje:</b> {metadata.get('generation_date')}", meta_style))
            elements.append(Spacer(1, 20))
            elements.append(Paragraph("<i>Ez a dokumentum automatizált folyamattal, AI asszisztens segítségével készült.</i>", meta_style))

        doc.build(elements)
        pdf_value = buffer.getvalue()
        buffer.close()
        return pdf_value


# --- FASTAPI ADATMODELLEK ---
class ExportRequest(BaseModel):
    title: Optional[str] = "Mimir AI Vizsga"
    format: Optional[str] = "pdf"
    questions: List[Dict[str, Any]]
    user_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


def format_file_size(num_bytes: int) -> str:
    if num_bytes < 1024 * 1024:
        return f"{num_bytes / 1024:.1f} KB"
    return f"{num_bytes / (1024 * 1024):.1f} MB"


# --- VÉGPONTOK ---

@app.post("/api/v1/export")
async def export_pdf(request: ExportRequest):
    """PDF generálása és mentése a felhasználó történetébe, ha be van jelentkezve."""
    try:
        metadata = getattr(request, 'metadata', None)
        # Meghívjuk a beépített ReportLab rajzolót
        drawer = NativePDFDrawer()
        pdf_bytes = drawer.draw_test(questions=request.questions, title=request.title,metadata=metadata)
        
        # Ha érkezett felhasználói azonosító, elmentjük a perzisztens tárhelyre
        if request.user_id:
            job_id = str(uuid.uuid4())
            safe_title = "".join([c if c.isalnum() or c in [' ', '_', '-'] else '' for c in request.title]).replace(' ', '_')
            filename = f"{job_id}_{safe_title}.pdf"
            file_path = os.path.join(STORAGE_DIR, filename)
            
            with open(file_path, "wb") as f:
                f.write(pdf_bytes)
                
            file_size = format_file_size(os.path.getsize(file_path))
            current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            
            # Mentés az SQLite adatbázisba
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO user_tests (id, user_id, title, file_path, file_size, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (job_id, request.user_id, request.title, file_path, file_size, current_date)
            )
            conn.commit()
            conn.close()
            print(f"💾 PDF sikeresen mentve a tárhelyre. Felhasználó: {request.user_id} | Méret: {file_size}")

        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Skald Export hiba: {str(e)}")


@app.get("/api/v1/tests")
async def list_user_tests(user_id: str):
    """Visszaadja a felhasználóhoz tartozó összes korábbi generált tesztet."""
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
    """Letölt egy korábban elmentett tesztet az egyedi ID-ja alapján."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT file_path, title FROM user_tests WHERE id = ?", (test_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="A keresett teszt nem található.")
            
        file_path, title = row
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="A PDF fájl fizikailag nem található a tárhelyen.")
            
        return FileResponse(path=file_path, media_type="application/pdf", filename=f"{title}.pdf")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))