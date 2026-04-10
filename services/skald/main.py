from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Dict, Any
from moodle_xml import MoodleXMLExporter
from pdf_drawer import NativePDFDrawer
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="📜 Skald Service", description="Teszt Exportáló Motor (PDF, XML, JSON)")
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
xml_exporter = MoodleXMLExporter()
pdf_drawer = NativePDFDrawer()

class ExportRequest(BaseModel):
    title: str = "Projekt Mimir Teszt"
    format: str # 'json', 'xml', vagy 'pdf'
    questions: List[Dict[str, Any]]

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "skald"}

@app.post("/api/v1/export")
async def export_test(request: ExportRequest):
    """Kész tesztek formázása a kért kimenetre."""
    try:
        if request.format == 'json':
            return {"status": "success", "data": request.questions}
            
        elif request.format == 'xml':
            xml_content = xml_exporter.export_test(request.questions)
            return Response(
                content=xml_content, 
                media_type="application/xml",
                headers={"Content-Disposition": f"attachment; filename=test.xml"}
            )
            
        elif request.format == 'pdf':
            pdf_bytes = pdf_drawer.draw_test(request.questions, title=request.title)
            return Response(
                content=pdf_bytes, 
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=test.pdf"}
            )
            
        else:
            raise HTTPException(status_code=400, detail="Nem támogatott formátum. Használj: json, xml, pdf")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hiba az exportálás során: {str(e)}")