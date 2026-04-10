from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from chunker import ContextualChunker
import re
import ast


app = FastAPI(title="ᛋ RuneCarver Service", description="Szemantikai daraboló modul")

# Inicializáljuk a darabolót (Kezdetben CPU-n futtatjuk a Docker kompatibilitás miatt)
chunker = ContextualChunker(device='cpu')
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
class DocumentRequest(BaseModel):
    filename: str
    extension: str
    content: str
    percentile: float = 85.0
    target_size: int = 1000

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "runecarver"}

@app.post("/api/v1/chunk")
async def process_document(request: DocumentRequest):
    """
    Szöveg fogadása és feldarabolása kiterjesztés és szemantika alapján.
    """
    try:
        ext = request.extension.lower()
        text = request.content
        chunks = []

        # 1. Python kód feldolgozása (AST alapján)
        if ext in ['py', 'python']:
            try:
                tree = ast.parse(text)
                for node in tree.body:
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                        chunks.append({"type": "code_block", "content": ast.unparse(node), "metadata": {"qa_score": 10}})
                    else:
                        chunks.append({"type": "code_snippet", "content": ast.unparse(node), "metadata": {"qa_score": 10}})
                return {"status": "success", "chunks": chunks}
            except SyntaxError:
                return {"status": "success", "chunks": [{"type": "code_error", "content": text, "metadata": {"qa_score": 10}}]}

        # 2. Markdown feldolgozása (Kódblokkok és fejezetek védelme)
        elif ext in ['md', 'markdown']:
            parts = re.split(r'(```.*?```)', text, flags=re.DOTALL)
            for part in parts:
                clean_part = part.strip()
                if not clean_part: continue
                
                if clean_part.startswith('```') and clean_part.endswith('```'):
                    code_content = clean_part.strip('`').strip()
                    chunks.append({"type": "code_block", "content": code_content, "metadata": {"qa_score": 10}})
                else:
                    sections = re.split(r'(?m)^(?:#{1,3}\s+|\d+(?:\.\s*\d+)*\.\s+(?=[A-ZÁÉÍÓÖŐÚÜŰ]))', clean_part)
                    for sec in sections:
                        if sec.strip():
                            # Szemantikai darabolás a narratív részekre
                            s_chunks, _, _ = chunker.embed_and_chunk(sec.strip(), threshold_val=request.percentile, target_chunk_chars=request.target_size)
                            for c in s_chunks:
                                chunks.append({"type": "markdown_section", "content": c, "metadata": {"qa_score": 10}})
            return {"status": "success", "chunks": chunks}

        # 3. Sima szöveg / PDF (Kizárólag narratív szemantikai darabolás)
        else:
            s_chunks, _, _ = chunker.embed_and_chunk(text, threshold_val=request.percentile, target_chunk_chars=request.target_size)
            for c in s_chunks:
                chunks.append({"type": "narrative", "content": c, "metadata": {"qa_score": 10}})
            return {"status": "success", "chunks": chunks}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hiba a darabolás során: {str(e)}")