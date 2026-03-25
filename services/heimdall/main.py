from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from judge import LLMJudge

app = FastAPI(title="👁️ Heimdall Service", description="AI Cenzor és Validációs Réteg")

# Inicializáljuk a minőségbiztosító motort
judge_engine = LLMJudge(model_name="qwen2:7b")

# Adatmodell a bejövő kérésekhez
class ValidationRequest(BaseModel):
    content: str
    schema_type: str = "general" # Későbbi fejlesztéshez: pl. "mcq", "essay", "json"

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "heimdall"}

@app.post("/api/v1/evaluate")
async def evaluate_content(request: ValidationRequest):
    """
    Kiszámolja a szöveg koherencia pontszámát és eldönti, hogy megfelelő-e.
    """
    try:
        # Értékelés a judge.py alapján
        score = judge_engine.evaluate_coherence(request.content)
        
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