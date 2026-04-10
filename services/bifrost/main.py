from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import torch
from transformers import AutoTokenizer, AutoModel
from vector_db import RAGVectorStore
import os
import json
import httpx


app = FastAPI(title="🌈 Bifrost Service", description="RAG Motor és Vektorkezelő")
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
# --- AI Modellek és DB inicializálása ---
MODEL_NAME = 'intfloat/multilingual-e5-base'
device = 'cpu' # Docker kompatibilitás miatt CPU
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME).to(device)
model.eval()

# A vector_db-ben láttuk, hogy az e5-base 768 dimenziós
vector_store = RAGVectorStore(vector_size=768) 

# --- Adatmodellek ---
class IngestRequest(BaseModel):
    chunks: List[Dict[str, Any]]

class SearchRequest(BaseModel):
    query: str
    limit: int = 3

# --- Segédfüggvény az embeddinghez (A régi rag_system.py alapján) ---
def _get_embeddings(texts: List[str], is_query=False):
    prefix = "query: " if is_query else "passage: "
    prefixed_texts = [prefix + t for t in texts]
    
    with torch.no_grad():
        inputs = tokenizer(prefixed_texts, padding=True, truncation=True, return_tensors='pt', max_length=512).to(device)
        outputs = model(**inputs)
        
        # Mean pooling
        attention_mask = inputs['attention_mask']
        token_embeddings = outputs.last_hidden_state
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        
        sum_embeddings = torch.sum(token_embeddings * input_mask_expanded, 1)
        sum_mask = torch.clamp(input_mask_expanded.sum(1), min=1e-9)
        embeddings = (sum_embeddings / sum_mask).cpu().numpy()
        
    return embeddings

# --- Végpontok ---
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "bifrost"}

@app.post("/api/v1/ingest")
async def ingest_chunks(request: IngestRequest):
    """Chunkok fogadása, vektorizálása és adatbázisba mentése."""
    try:
        texts = [c.get('content', '') for c in request.chunks]
        if not texts:
            return {"status": "ignored", "message": "Nem érkezett tartalom."}
            
        embeddings = _get_embeddings(texts, is_query=False)
        indexed_count = vector_store.upload_chunks(request.chunks, embeddings)
        
        return {"status": "success", "indexed_chunks": indexed_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingest hiba: {str(e)}")

@app.post("/api/v1/search")
async def search_knowledge(request: SearchRequest):
    """Szemantikus keresés a felépített RAG tudásbázisban."""
    try:
        query_vector = _get_embeddings([request.query], is_query=True)[0]
        results = vector_store.search(query_vector, limit=request.limit)
        
        formatted_results = [
            {"score": res.score, "payload": res.payload} for res in results
        ]
        return {"status": "success", "query": request.query, "results": formatted_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Keresési hiba: {str(e)}")

class GenerateRequest(BaseModel):
    query: str
    limit: int = 3
    format: str = "pdf"

@app.post("/api/v1/generate")
async def generate_questions(request: GenerateRequest):
    """Szemantikus keresés + LLM (Qwen) alapú kérdésgenerálás."""
    # 1. Keresés a Qdrantban
    query_vector = _get_embeddings([request.query], is_query=True)[0]
    results = vector_store.search(query_vector, limit=request.limit)
    
    if not results:
        raise HTTPException(status_code=404, detail="Nem található releváns kontextus.")
        
    # 2. Kontextus összeállítása
    context_text = "\n\n".join([res.payload.get("text", "") for res in results])
    
    # 3. Zseniális Prompt a Qwen-nek
    prompt = f"""Te egy kiemelkedő tudású oktatásmódszertani szakértő és professzionális vizsgakészítő vagy. Feladatod magas minőségű, pedagógiailag helyes tesztkérdések írása.

    KÖTELEZŐ SZABÁLYOK, AMIKET SZIGORÚAN BE KELL TARTANOD:
    1. ZÉRÓ HALLUCINÁCIÓ: KIZÁRÓLAG a megadott KONTEXTUS alapján dolgozz! Tilos bármilyen külső ismeretet, feltételezést vagy kitalált tényt hozzáadnod. Ha a kontextus nem tartalmazza a választ, ne találj ki semmit!
    2. DISZTRAKTOROK MINŐSÉGE: A három helytelen válasz (disztraktor) legyen logikus, szakmai és hihető egy diák számára, de a kontextus alapján egyértelműen helytelen. Ne használj komolytalan, vicces vagy oda nem illő opciókat!
    3. TISZTA SZÖVEGEZÉS: A kérdés és a válaszok legyenek rövidek, egyértelműek. Ne tartalmazzanak rejtett sortöréseket (\\n) vagy felesleges írásjeleket.

    KONTEXTUS:
    {context_text}

    FELADAT:
    Készíts pontosan 1 darab feleletválasztós (MCQ) tesztkérdést a következő fókusszal: "{request.query}"

    KIMENETI FORMÁTUM:
    A válaszod KIZÁRÓLAG egy érvényes, nyers JSON objektum lehet! 
    Szigorúan TILOS markdown formázást (pl. ```json) használni a JSON körül! TILOS bármilyen bevezető vagy lezáró mondatot írni (pl. "Íme a tesztkérdés:"). Csak a tiszta, parszerolható JSON-t add vissza az alábbi struktúrában:

    {{
        "title": "Mimir AI Teszt",
        "format": "{request.format}",
        "questions": [
            {{
                "type": "mcq",
                "text": "A pontos és egyértelmű kérdés szövege?",
                "answers": [
                    {{"text": "A kontextus alapján egyértelműen helyes válasz", "is_correct": true}},
                    {{"text": "Hihető, szakmai, de helytelen válasz 1", "is_correct": false}},
                    {{"text": "Hihető, szakmai, de helytelen válasz 2", "is_correct": false}},
                    {{"text": "Hihető, szakmai, de helytelen válasz 3", "is_correct": false}}
                ]
            }}
        ]
    }}
    """
    
    # 4. Hívás a lokális Ollama szerverhez a Dockerből kifelé
    ollama_url = "http://host.docker.internal:11434/api/generate"
    try:
        async with httpx.AsyncClient() as client:
            # Az Ollama "format": "json" paramétere garantálja, hogy a Qwen nem kezd el rizsázni a JSON előtt/után
            response = await client.post(ollama_url, json={
                "model": "qwen2.5:7b", # Vagy ahogy pontosan hívják az Ollamádban (pl. "qwen:7b", "qwen2.5:7b")
                "prompt": prompt,
                "stream": False,
                "format": "json" 
            }, timeout=120.0) # Adunk neki 2 percet, ha épp fel kell pörgetnie a GPU-t
            
            response.raise_for_status()
            llm_response = response.json().get("response", "{}")
            
            # JSON validálás és visszaadás
            generated_json = json.loads(llm_response)
            return {"status": "success", "data": generated_json}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hiba a Qwen LLM hívása során: {str(e)}")