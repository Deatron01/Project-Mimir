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
from dotenv import load_dotenv

load_dotenv()

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
    """Szemantikus keresés + Egyetemi LLM (GenAI) alapú kérdésgenerálás."""
    # 1. Keresés a Qdrantban
    query_vector = _get_embeddings([request.query], is_query=True)[0]
    results = vector_store.search(query_vector, limit=request.limit)
    
    if not results:
        raise HTTPException(status_code=404, detail="Nem található releváns kontextus.")
        
    # 2. Kontextus összeállítása
    context_text = "\n\n".join([res.payload.get("text", "") for res in results])
    
    # 3. Dinamikus Prompt a felhasználó kérése alapján
    prompt = f"""Te egy kiemelkedő tudású oktatásmódszertani szakértő és professzionális vizsgakészítő vagy.

    KÖTELEZŐ SZABÁLYOK, AMIKET SZIGORÚAN BE KELL TARTANOD:
    1. ZÉRÓ HALLUCINÁCIÓ: KIZÁRÓLAG a megadott KONTEXTUS alapján dolgozz! Ha a kontextus nem tartalmazza a választ, ne találj ki semmit!
    2. FELHASZNÁLÓI UTASÍTÁS KÖVETÉSE: Alább a FELADAT részben megkapod a felhasználó pontos kérését. Ebből kell kiolvasnod, hogy HÁNY DARAB és MILYEN TÍPUSÚ (pl. feleletválasztós, igaz-hamis, kifejtős) kérdést kér. Pontosan a kért mennyiséget és típust generáld le!
    3. DISZTRAKTOROK: Feleletválasztós (mcq) kérdés esetén 1 helyes és 3 hihető, de helytelen válasz legyen.
    4. NO LATEX: Szigorúan TILOS LaTeX formázást vagy dollárjeleket ($) használni!
    5. META-REFERENCIA TILALOM: Szigorúan TILOS a dokumentum szerkezetére kérdezni (pl. "Mi van a 4.3 pontban?"). Úgy fogalmazz, mintha egy általános vizsgát írnál.

    KONTEXTUS:
    {context_text}

    FELADAT (A felhasználó pontos kérése):
    "{request.query}"

    KIMENETI FORMÁTUM:
    A válaszod KIZÁRÓLAG egy tiszta, érvényes JSON objektum lehet! Szigorúan TILOS markdown formázást (```json) és megjegyzéseket (//) használni!
    
    A struktúrának pontosan így kell kinéznie:
    {{
        "title": "Mimir AI Vizsga",
        "format": "{request.format}",
        "questions": [
            {{
                "type": "mcq",
                "text": "A pontos és egyértelmű kérdés szövege?",
                "answers": [
                    {{"text": "Helyes válasz", "is_correct": true}},
                    {{"text": "Helytelen válasz 1", "is_correct": false}},
                    {{"text": "Helytelen válasz 2", "is_correct": false}},
                    {{"text": "Helytelen válasz 3", "is_correct": false}}
                ]
            }}
        ]
    }}

    SZABÁLYOK A VÁLASZOKHOZ:
    - Ha a típus "mcq" (feleletválasztós): kövesd a fenti példát (1 true, 3 false).
    - Ha a típus "tf" (igaz-hamis): pontosan 2 válasz legyen (az egyik true, a másik false).
    - Ha a típus "open" (kifejtős): pontosan 1 válasz legyen (is_correct: true), ami a megoldókulcsot tartalmazza.
    """
    
   # 4. Hívás az Óbudai Egyetem GenAI szerveréhez (Modell Fallback logikával)
    genai_url = "https://genai.uni-obuda.hu/api/chat/completions"
    api_key = os.getenv("OE_GENAI_API_KEY")
    
    if not api_key:
        raise HTTPException(status_code=500, detail="Hiányzik az OE_GENAI_API_KEY környezeti változó a szerverről!")

    # A preferált modellek listája sorrendben
    models_to_try = [
        "Qwen3.5-122B",          # 1. Választás: 122 milliárd paraméteres Qwen
        "gpt-oss:120b",          # 2. Választás: 120 milliárd paraméteres GPT-OSS
        "nemotron-3-super:120b", # 3. Választás: 120 milliárd paraméteres Nemotron
        "gpt-oss:20b",           # 4. Választás: 20 milliárd paraméteres GPT-OSS
        "qwen3.5:9b",            # 5. Választás: 9 milliárd paraméteres Qwen
        "qwen3-vl:8b"            # 6. Választás: Vészhelyzeti tartalék (8 milliárdos Vision-Language modell)
    ]

    async with httpx.AsyncClient() as client:
        for model_name in models_to_try:
            try:
                print(f"🔄 Próbálkozás a '{model_name}' modellel...")
                response = await client.post(
                    genai_url,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model_name, 
                        "messages": [
                            {"role": "system", "content": "Te egy kiemelkedő tudású oktatásmódszertani szakértő és vizsgakészítő vagy. Kizárólag érvényes JSON formátumban válaszolj, markdown formázás nélkül!"},
                            {"role": "user", "content": prompt}
                        ],
                        "response_format": {"type": "json_object"},
                        "stream": False
                    }, 
                    timeout=180.0  # 3 percet hagyunk, hogy a DeepSeek is tudjon gondolkodni
                )
                
                response.raise_for_status()
                
                # Válasz kibontása
                llm_response = response.json()["choices"][0]["message"]["content"]
                
                # Beépített, gyors JSON tisztítás, ha az AI véletlenül markdownba tenné (pl. ```json ... ```)
                cleaned_response = llm_response.replace('```json', '').replace('```', '').strip()
                start = cleaned_response.find('{')
                end = cleaned_response.rfind('}')
                if start != -1 and end != -1:
                    cleaned_response = cleaned_response[start:end+1]
                
                # JSON validálás
                generated_json = json.loads(cleaned_response)
                
                print(f"✅ Sikeres generálás a '{model_name}' modellel!")
                return {"status": "success", "data": generated_json}
                
            except Exception as e:
                # Ha bármi hiba történik (Hálózati hiba, 500-as szerverhiba, vagy JSON parse hiba),
                # kiírjuk, és a 'continue' miatt a ciklus megy a következő modellre!
                print(f"⚠️ Hiba a '{model_name}' modellel: {str(e)}. Lépés a következőre...")
                continue
                
    print("⚠️ Az összes külső API elhasalt. Próbálkozás lokális Ollama-val (qwen2.5:3b)...")
    try:
        # A 'host.docker.internal' a Docker konténerből a Windows host gépre mutat
        ollama_url = "http://host.docker.internal:11434/api/generate"
        
        async with httpx.AsyncClient() as client:
            ollama_response = await client.post(
                ollama_url,
                json={
                    "model": "qwen2.5:3b",
                    "prompt": prompt,
                    "stream": False,
                    "format": "json", # Az Ollama kényszeríti a JSON kimenetet
                    "options": {
                        "num_ctx": 32768, # Megemelt kontextus a PDF feldolgozáshoz
                        "temperature": 0.1
                    }
                },
                timeout=180.0
            )
            
            if ollama_response.status_code == 200:
                raw_content = ollama_response.json().get("response", "")
                
                # Ugyanaz a tisztító logika, mint a távoli modelleknél
                cleaned_local = raw_content.replace('```json', '').replace('```', '').strip()
                start = cleaned_local.find('{')
                end = cleaned_local.rfind('}')
                if start != -1 and end != -1:
                    cleaned_local = cleaned_local[start:end+1]
                
                local_json = json.loads(cleaned_local)
                print("✅ Sikeres generálás lokális Ollama (qwen2.5:3b) modellel!")
                return {"status": "success", "data": local_json}
            else:
                print(f"⚠️ Lokális Ollama hiba: {ollama_response.status_code}")
                
    except Exception as e:
        print(f"❌ Lokális fallback is sikertelen: {str(e)}")

    # ----------------------------------------------------------------------
    # VÉGSŐ BIZTONSÁGI MEGOLDÁS (Csak ha tényleg semmi nem működött)
    # ----------------------------------------------------------------------
    print("❌ Minden lehetőség kimerült. Biztonsági JSON visszaküldése.")
    fallback_json = {
        "title": "Mimir AI - Generálási Hiba",
        "format": request.format,
        "questions": [
            {
                "type": "mcq",
                "text": "Sajnos az AI modellek túlterheltek, vagy a kérés túl bonyolult volt. Kérlek, próbáld újra!",
                "answers": [
                    {"text": "Megértettem", "is_correct": True},
                    {"text": "Hiba történt", "is_correct": False}
                ]
            }
        ]
    }
    return {"status": "success", "data": fallback_json}