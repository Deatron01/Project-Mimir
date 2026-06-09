import os
import json
import httpx

class LLMJudge:
    def __init__(self):
        print("👁️ LLM Judge inicializálva a minőségbiztosításhoz.")
        self.genai_url = "https://genai.uni-obuda.hu/api/chat/completions"
        
        # Szigorúan a legintelligensebb modellekkel kezdünk (minőség > sebesség)
        self.models_to_try = [
            "Qwen3.5-122B",          # Legjobb logikai képességek RAG-hoz
            "gpt-oss:120b",          # Második számú gigamodell
            "nemotron-3-super:120b", # Harmadik számú biztonsági háló
            "gpt-oss:20b"            # Kisebb szerveres fallback
        ]

    async def evaluate_coherence(self, chunk_text: str) -> int:
        """Értékeli a szövegdarab koherenciáját 1-től 10-ig valós LLM segítségével."""
        
        if len(chunk_text.split()) < 5:
            return 5
            
        prompt = f"""Te egy szigorú és precíz minőségbiztosítási ellenőr (AI Judge) vagy.
        Kérlek értékeld az alábbi generált szöveg/kérdés koherenciáját, szakmai helyességét és érthetőségét egy 1-től 10-ig terjedő skálán.
        
        Vizsgálandó szöveg:
        "{chunk_text}"
        
        KIMENETI FORMÁTUM:
        KIZÁRÓLAG egy érvényes JSON objektummal válaszolj, markdown formázás (```json) nélkül! 
        Az objektum tartalmazzon egy 'score' (szám) és egy 'feedback' (szöveg) mezőt:
        {{
            "score": 8,
            "feedback": "Rövid indoklás..."
        }}"""

        api_key = os.getenv("OE_GENAI_API_KEY")
        
        # 1. Hívás az Óbudai Egyetem GenAI szerveréhez (Iteratív próbálkozás)
        if api_key:
            async with httpx.AsyncClient() as client:
                for model_name in self.models_to_try:
                    try:
                        print(f"👁️ Heimdall: Próbálkozás a '{model_name}' modellel...")
                        response = await client.post(
                            self.genai_url,
                            headers={
                                "Authorization": f"Bearer {api_key}",
                                "Content-Type": "application/json"
                            },
                            json={
                                "model": model_name,
                                "messages": [
                                    {"role": "system", "content": "Te egy AI Judge vagy. Kizárólag érvényes JSON formátumban válaszolj!"},
                                    {"role": "user", "content": prompt}
                                ],
                                "response_format": {"type": "json_object"},
                                "stream": False
                            },
                            timeout=120.0
                        )
                        response.raise_for_status()
                        
                        llm_response = response.json()["choices"][0]["message"]["content"]
                        
                        # JSON tisztítás
                        cleaned_response = llm_response.replace('```json', '').replace('```', '').strip()
                        start = cleaned_response.find('{')
                        end = cleaned_response.rfind('}')
                        if start != -1 and end != -1:
                            cleaned_response = cleaned_response[start:end+1]
                            
                        result = json.loads(cleaned_response)
                        score = int(result.get("score", 5))
                        print(f"✅ Heimdall: Sikeres értékelés a '{model_name}' modellel! Pont: {score}")
                        return score
                        
                    except Exception as e:
                        print(f"⚠️ Heimdall: Hiba a '{model_name}' modellel: {str(e)}. Lépés a következőre...")
                        continue

        # 2. Fallback a lokális Ollama-ra (Javított URL formátummal)
        print("⚠️ Heimdall: Külső API sikertelen. Próbálkozás lokális Ollama-val (qwen2.5:14b)...")
        try:
            ollama_url = "[http://host.docker.internal:11434/api/generate](http://host.docker.internal:11434/api/generate)"
            async with httpx.AsyncClient() as client:
                ollama_response = await client.post(
                    ollama_url,
                    json={
                        "model": "qwen2.5:14b", # Lokális erős fallback
                        "prompt": prompt,
                        "stream": False,
                        "format": "json",
                        "options": {
                            "num_ctx": 16384,
                            "temperature": 0.0
                        }
                    },
                    timeout=300.0
                )
                
                if ollama_response.status_code == 200:
                    raw_content = ollama_response.json().get("response", "")
                    
                    cleaned_local = raw_content.replace('```json', '').replace('```', '').strip()
                    start = cleaned_local.find('{')
                    end = cleaned_local.rfind('}')
                    if start != -1 and end != -1:
                        cleaned_local = cleaned_local[start:end+1]
                        
                    local_json = json.loads(cleaned_local)
                    score = int(local_json.get("score", 5))
                    print(f"✅ Heimdall: Sikeres értékelés lokális Ollama modellel! Pont: {score}")
                    return score
                else:
                    print(f"⚠️ Heimdall: Lokális Ollama hiba: {ollama_response.status_code}")
        except Exception as e:
            print(f"❌ Heimdall: Lokális fallback is sikertelen: {str(e)}")

        return 5