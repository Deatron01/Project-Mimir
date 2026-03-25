from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any
import torch
from transformers import AutoTokenizer, AutoModel
from vector_db import RAGVectorStore

app = FastAPI(title="🌈 Bifrost Service", description="RAG Motor és Vektorkezelő")

# --- AI Modellek és DB inicializálása ---
MODEL_NAME = 'intfloat/multilingual-e5-base'
device = 'cpu' # Docker kompatibilitás miatt CPU
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME).to(device)
model.eval()

# A vector_db-ben láttuk, hogy az e5-base 384 dimenziós
vector_store = RAGVectorStore(vector_size=384) 

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