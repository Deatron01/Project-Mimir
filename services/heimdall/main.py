from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from judge import LLMJudge
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Környezeti változók betöltése (.env)
load_dotenv()

app = FastAPI(title="👁️ Heimdall Service", description="AI Cenzor és Validációs Réteg")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "[https://mimir-ai.hu](https://mimir-ai.hu)",
        "[https://www.mimir-ai.hu](https://www.mimir-ai.hu)"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializáljuk a minőségbiztosító motort paraméterek nélkül (beépített fallback)
judge_engine = LLMJudge()

# Adatmodell a bejövő kérésekhez
class ValidationRequest(BaseModel):
    content: str
    schema_type: str = "general"

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "heimdall"}

@app.post("/api/v1/evaluate")
async def evaluate_content(request: ValidationRequest):
    """
    Kiszámolja a szöveg koherencia pontszámát valós LLM API / Ollama hívásokon keresztül,
    és eldönti, hogy megfelelő-e.
    """
    try:
        # Értékelés a judge.py alapján ASZINKRON módon
        score = await judge_engine.evaluate_coherence(request.content)
        
        # A 7-es határt a pipeline.py fallback logikájából emeltük át
        is_valid = score >= 7
        
        return {
            "status": "success",
            "content_length": len(request.content),
            "qa_score": score,
            "is_valid": is_valid,
            "action": "pass" if is_valid else "fallback_required"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validációs hiba: {str(e)}")