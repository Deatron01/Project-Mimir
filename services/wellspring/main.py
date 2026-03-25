from fastapi import FastAPI, UploadFile, File, HTTPException
from pdf_processor import PDFProcessor

app = FastAPI(title="🌊 Wellspring Service", description="Bináris fájlfeldolgozó és szövegkinyerő")
pdf_processor = PDFProcessor()

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "wellspring"}

@app.post("/api/v1/extract")
async def extract_text(file: UploadFile = File(...)):
    """Fájl fogadása és szöveg kinyerése hálózaton keresztül."""
    ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
    
    if ext == 'pdf':
        try:
            pdf_bytes = await file.read()
            extracted_text, used_route = pdf_processor.process_pdf_bytes(pdf_bytes)
            return {
                "filename": file.filename,
                "extension": ext,
                "extraction_method": used_route,
                "content": extracted_text
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Hiba a PDF feldolgozása közben: {str(e)}")
            
    elif ext in ['md', 'markdown', 'txt', 'py']:
        try:
            content_bytes = await file.read()
            extracted_text = content_bytes.decode('utf-8')
            return {
                "filename": file.filename,
                "extension": ext,
                "extraction_method": "NATIVE_TEXT",
                "content": extracted_text
            }
        except Exception as e:
             raise HTTPException(status_code=400, detail=f"A fájl nem olvasható UTF-8 szövegként: {str(e)}")
             
    else:
        raise HTTPException(status_code=400, detail=f"Nem támogatott fájlformátum: {ext}")  