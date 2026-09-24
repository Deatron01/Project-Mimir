from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import torch
from transformers import AutoTokenizer, AutoModel
from vector_db import RAGVectorStore
from prompts import build_naive_prompt
from jobs import JobStore
import os
import json
import httpx
import uuid
import hashlib
from dotenv import load_dotenv
from datetime import datetime

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

MODEL_NAME = 'intfloat/multilingual-e5-base'
device = 'cpu'
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME).to(device)
model.eval()

vector_store = RAGVectorStore(vector_size=768) 

# --- GDPR / zéró megőrzés beállítások ---
# LOCAL_ONLY=true: a dokumentum szövege nem kerül külső (egyetemi GenAI) API-hoz, csak a helyi Ollamához.
LOCAL_ONLY = os.getenv("LOCAL_ONLY", "false").strip().lower() in ("1", "true", "yes")
# A generált tesztek (feladateredmények) legfeljebb ennyi ideig maradnak a memóriában.
JOB_TTL_SECONDS = int(os.getenv("JOB_TTL_SECONDS", "3600"))
# Lokális Ollama modell és cím (README: qwen2.5:7b fér el 8 GB VRAM-ban; a 14b nem).
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434/api/generate")

GENAI_URL = "https://genai.uni-obuda.hu/api/chat/completions"
# A szerveren elérhető modellek változnak (2026-09: a Qwen3.5-122B és a nemotron már nincs fent,
# lásd GET /api/models). Sorrend: GENAI_MODELS env, vesszővel elválasztva.
GENAI_MODELS = [m.strip() for m in os.getenv("GENAI_MODELS", "gpt-oss:120b,Qwen3.8-Flash-Next").split(",") if m.strip()]
LOCAL_MODEL_ID = "local"

# Feladatok: állapot, szakasz, előrehaladás, becsült hátralévő idő (a lejárt eredményeket eldobja).
jobs = JobStore(ttl_seconds=JOB_TTL_SECONDS)


def _external_available() -> bool:
    return bool(os.getenv("OE_GENAI_API_KEY")) and not LOCAL_ONLY


def _extract_json(raw: str) -> dict:
    cleaned = raw.replace('```json', '').replace('```', '').strip()
    start, end = cleaned.find('{'), cleaned.rfind('}')
    if start != -1 and end != -1:
        cleaned = cleaned[start:end + 1]
    return json.loads(cleaned)


def _purge_document_data():
    """A feladat végén törli a dokumentumból származó chunkokat és vektorokat (zéró megőrzés)."""
    try:
        vector_store.clear_database()
    except Exception as e:
        print(f"⚠️ Vektortár törlési hiba: {type(e).__name__}")


def _sha256(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()

class IngestRequest(BaseModel):
    chunks: List[Dict[str, Any]]

class SearchRequest(BaseModel):
    query: str
    limit: int = 3

class GenerateRequest(BaseModel):
    query: str
    limit: int = 3
    format: str = "pdf"
    # None / "auto": a szerver modelljei sorban, majd helyi tartalék; "local": csak helyi Ollama;
    # egy GENAI_MODELS-beli név: azzal kezd (FE-11 modellválasztó). Lista: GET /api/v1/models
    model: Optional[str] = None

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

async def _process_generation(job_id: str, request: GenerateRequest):
    """Háttérfeladat. A végén (sikertől függetlenül) törli a dokumentum adatait a vektortárból."""
    try:
        await _run_generation(job_id, request)
    finally:
        _purge_document_data()


async def _run_generation(job_id: str, request: GenerateRequest):
    """Ez a függvény a háttérben fut, és nem blokkolja a webszervert."""
    try:
        # 1. Keresés a Qdrantban
        jobs.stage(job_id, "retrieving")
        query_vector = _get_embeddings([request.query], is_query=True)[0]
        results = vector_store.search(query_vector, limit=request.limit)
        
        if not results:
            jobs.fail(job_id, "Nem található releváns kontextus.")
            return
            
        # 2. Kontextus összeállítása
        context_text = "\n\n".join([res.payload.get("text", "") for res in results])
        
        # 3. Dinamikus Prompt (a te eredeti promptod marad változatlan)
        prompt = build_naive_prompt(context_text, request.query, request.format)
        
        # 4. Hívás az Óbudai Egyetem GenAI szerveréhez (Modell lista iterációja)
        api_key = os.getenv("OE_GENAI_API_KEY")
        models_to_try = list(GENAI_MODELS)
        if request.model and request.model in GENAI_MODELS:   # a választott modell az első
            models_to_try.remove(request.model)
            models_to_try.insert(0, request.model)
        use_external = _external_available() and request.model != LOCAL_MODEL_ID
        
        genai_success = False

        if use_external:
            async with httpx.AsyncClient(proxy=None, trust_env=False) as client:
                for model_name in models_to_try:
                    try:
                        print(f"🔄 Próbálkozás a '{model_name}' modellel (Job ID: {job_id}) STREAMING módban...")
                        jobs.stage(job_id, "generating", model=model_name, location="external")
                        llm_response = ""
                        
                        async with client.stream(
                            "POST",
                            GENAI_URL,
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
                                "stream": True 
                            }, 
                            timeout=300.0
                        ) as response:
                            response.raise_for_status()
                            
                            async for line in response.aiter_lines():
                                if line.startswith("data: "):
                                    data_str = line[6:].strip()
                                    if data_str == "[DONE]":
                                        break
                                    try:
                                        data_json = json.loads(data_str)
                                        chunk = data_json.get("choices", [{}])[0].get("delta", {}).get("content", "")
                                        if chunk:
                                            llm_response += chunk
                                            jobs.generating(job_id, len(llm_response))
                                    except json.JSONDecodeError:
                                        continue

                        if not llm_response or llm_response.strip() == "":
                            raise ValueError("Üres válasz érkezett a stream végén.")

                        generated_json = _extract_json(llm_response)
                        cleaned_response = json.dumps(generated_json, ensure_ascii=False)
                        print(f"✅ Sikeres generálás a '{model_name}' modellel!")
                        
                        jobs.stage(job_id, "validating")
                        await send_audit_log(job_id, request.query, prompt, context_text, model_name, cleaned_response)
                        
                        generated_json["metadata"] = {
                            "model_used": model_name,
                            "processing_location": "external",
                            "tokens_generated": "Streamed", 
                            "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "system_prompt_version": "v1.0"
                        }
                        
                        jobs.complete(job_id, generated_json)
                        genai_success = True
                        break # Ha sikerült, kilép a for ciklusból
                        
                    except Exception as e:
                        print(f"⚠️ Hiba a '{model_name}' modellel (GenAI API): {str(e)}. Ugrás a következőre...")
                        continue # Ha hiba van, megy a következő modellre
                        
        # 5. Lokális Ollama Fallback (Csak akkor fut le, ha a GenAI_success False maradt)
        if not genai_success:
            print(f"⚠️ Külső modell nem használható vagy hibázott. Lokális Ollama ({OLLAMA_MODEL})...")
            jobs.stage(job_id, "generating", model=OLLAMA_MODEL, location="local")
            try:
                raw_content = ""
                async with httpx.AsyncClient(trust_env=False) as client:
                    # Streaming: a generált karakterek száma adja az előrehaladást.
                    async with client.stream(
                        "POST",
                        OLLAMA_URL,
                        json={
                            "model": OLLAMA_MODEL,
                            "prompt": prompt,
                            "stream": True,
                            "format": "json",
                            "options": {
                                "num_ctx": 16384,
                                "temperature": 0.0
                            }
                        },
                        timeout=300.0
                    ) as ollama_response:
                        if ollama_response.status_code != 200:
                            raise ValueError(f"Lokális hiba kód: {ollama_response.status_code}")
                        async for line in ollama_response.aiter_lines():
                            if not line.strip():
                                continue
                            try:
                                part = json.loads(line)
                            except json.JSONDecodeError:
                                continue
                            raw_content += part.get("response", "")
                            jobs.generating(job_id, len(raw_content))
                            if part.get("done"):
                                break

                local_json = _extract_json(raw_content)
                cleaned_local = json.dumps(local_json, ensure_ascii=False)
                print(f"✅ Sikeres generálás lokális Ollama ({OLLAMA_MODEL}) modellel!")
                
                jobs.stage(job_id, "validating")
                await send_audit_log(job_id, request.query, prompt, context_text, f"{OLLAMA_MODEL} (local fallback)", cleaned_local)
                
                local_json["metadata"] = {
                    "model_used": f"{OLLAMA_MODEL} (local fallback)", 
                    "processing_location": "local",
                    "tokens_generated": "N/A", 
                    "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "system_prompt_version": "v1.0"
                }

                jobs.complete(job_id, local_json)
                return
            except Exception as e:
                print(f"❌ Lokális fallback is sikertelen: {str(e)}")

            # 6. Végső biztonsági JSON
            print("❌ Minden lehetőség kimerült. Biztonsági JSON visszaküldése.")
            fallback_json = {
                "title": "Mimir AI - Generálási Hiba",
                "format": request.format,
                "questions": [
                    {
                        "type": "mcq",
                        "text": "Sajnos az AI modellek jelenleg túlterheltek. Kérlek, próbáld újra egy kicsit később!",
                        "answers": [
                            {"text": "Megértettem", "is_correct": True},
                            {"text": "Hiba történt", "is_correct": False}
                        ]
                    }
                ],
                "metadata": {"model_used": "fallback_hardcoded", "is_fallback": True,
                             "generation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            }
            await send_audit_log(job_id, request.query, prompt, context_text, "fallback_hardcoded", json.dumps(fallback_json))
            jobs.complete(job_id, fallback_json, record=False)

    except Exception as e:
        jobs.fail(job_id, f"Váratlan hiba történt a generálás során: {str(e)}")

# --- Végpontok ---
@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "bifrost"}

@app.post("/api/v1/ingest")
async def ingest_chunks(request: IngestRequest):
    try:
        texts = [c.get('content', '') for c in request.chunks]
        if not texts:
            return {"status": "ignored", "message": "Nem érkezett tartalom."}
            
        embeddings = _get_embeddings(texts, is_query=False)
        
        # --- ÚJ SOR: Kiürítjük a vektortárat az új dokumentum érkezésekor ---
        vector_store.clear_database() 
        
        indexed_count = vector_store.upload_chunks(request.chunks, embeddings)
        return {"status": "success", "indexed_chunks": indexed_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingest hiba: {str(e)}")
    
@app.post("/api/v1/search")
async def search_knowledge(request: SearchRequest):
    try:
        query_vector = _get_embeddings([request.query], is_query=True)[0]
        results = vector_store.search(query_vector, limit=request.limit)
        
        formatted_results = [
            {"score": res.score, "payload": res.payload} for res in results
        ]
        return {"status": "success", "query": request.query, "results": formatted_results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Keresési hiba: {str(e)}")

@app.get("/api/v1/models")
async def list_models():
    """FE-11 / BIF-09: választható modellek és a várható generálási idő. Helyi modell mindig van;
    a szerver modelljei csak akkor, ha van API kulcs és nincs LOCAL_ONLY (GDPR-06)."""
    external = _external_available()
    models = [{"id": m, "label": m, "location": "external"} for m in GENAI_MODELS] if external else []
    models.append({"id": LOCAL_MODEL_ID, "label": OLLAMA_MODEL, "location": "local"})
    return {"local_only": LOCAL_ONLY, "external_available": external, "default": "auto",
            "models": models, "estimates_s": jobs.estimates()}


@app.post("/api/v1/generate")
async def start_generation(request: GenerateRequest, background_tasks: BackgroundTasks):
    """Azonnal visszaad egy Job ID-t, a generálás a háttérben indul."""
    if request.model not in (None, "", "auto", LOCAL_MODEL_ID) and request.model not in GENAI_MODELS:
        raise HTTPException(status_code=400, detail={"code": "MODEL_UNAVAILABLE"})
    if request.model in GENAI_MODELS and not _external_available():
        raise HTTPException(status_code=400, detail={"code": "EXTERNAL_DISABLED"})
    job_id = str(uuid.uuid4())
    location = "external" if _external_available() and request.model != LOCAL_MODEL_ID else "local"
    job = jobs.create(job_id, location)
    background_tasks.add_task(_process_generation, job_id, request)
    return {"status": "success", "job_id": job_id, "expected_total_s": job["expected_total_s"],
            "location": location}

@app.get("/api/v1/status/{job_id}")
async def get_generation_status(job_id: str):
    """Állapot, szakasz (queued/retrieving/generating/validating/done), előrehaladás (0..1),
    eltelt és becsült hátralévő idő másodpercben."""
    jobs.purge_expired()
    job = jobs.public(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Feladat nem található.")
    return job


async def send_audit_log(job_id: str, user_query: str, prompt: str, context: str, model_name: str, generated_content: str):
    qa_score = None
    
    try:
        heimdall_url = os.getenv("HEIMDALL_URL", "http://heimdall:8000")
        async with httpx.AsyncClient() as client:
            print(f"👁️ Tartalom küldése a Heimdall felé elemzésre (Job ID: {job_id})...")
            heimdall_res = await client.post(
                f"{heimdall_url}/api/v1/evaluate",
                json={
                    "content": generated_content,
                    "schema_type": "exam_json"
                },
                timeout=60.0
            )
            
            if heimdall_res.status_code == 200:
                qa_score = heimdall_res.json().get("qa_score")
                print(f"✅ Heimdall értékelés sikeres (Job ID: {job_id}): {qa_score}/10 pont")
            else:
                print(f"⚠️ Heimdall visszautasította a kérést: {heimdall_res.status_code} - {heimdall_res.text}")
                
    except Exception as e:
        print(f"⚠️ Hiba a Heimdall minőségbiztosítóval való kommunikációban: {e}")

    try:
        forge_url = os.getenv("FORGE_URL", "http://the-forge:8000")
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{forge_url}/api/v1/audit",
                # GDPR: a naplóba csak metaadat és kriptográfiai lenyomat kerül, a dokumentum szövege nem.
                json={
                    "job_id": job_id,
                    "model_name": model_name,
                    "qa_score": qa_score,
                    "prompt_version": "v1.0",
                    "query_sha256": _sha256(user_query),
                    "prompt_sha256": _sha256(prompt),
                    "context_sha256": _sha256(context),
                    "query_chars": len(user_query or ""),
                    "context_chars": len(context or ""),
                },
                timeout=10.0
            )
            print(f"📝 AI Act Audit log rögzítve (Job ID: {job_id}, QA Score: {qa_score})")
    except Exception as e:
        print(f"⚠️ Audit log mentési hiba (a generálás folytatódik, a log elvész): {e}")