import random

class LLMJudge:
    def __init__(self, model_name="qwen2:7b"):
        print(f"LLM Judge ({model_name}) inicializálva a minőségbiztosításhoz.")
        self.model_name = model_name

    def evaluate_coherence(self, chunk_text):
        """Értékeli a szövegdarab koherenciáját 1-től 10-ig."""
        if len(chunk_text.split()) < 5:
            return random.randint(3, 5)
        
        # Súlyozott véletlenszám a szimulációhoz (néha bedob egy 6-ost vagy 5-öst, hogy lássuk a Fallback-et)
        return random.choices([9, 8, 7, 6, 5], weights=[40, 30, 10, 10, 10])[0]