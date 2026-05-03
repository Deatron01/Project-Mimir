import requests
import os
import json
import time
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# --- KONFIGURÁCIÓ ---
SERVICES = {
    "wellspring": "http://localhost:8001/api/v1/extract",
    "runecarver": "http://localhost:8002/api/v1/chunk",
    "bifrost_ingest": "http://localhost:8003/api/v1/ingest",
    "bifrost_search": "http://localhost:8003/api/v1/search",
    "bifrost_generate": "http://localhost:8003/api/v1/generate",
    "skald": "http://localhost:8005/api/v1/export"
}

# --- KÖNYVTÁRAK BEÁLLÍTÁSA ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEST_DOCS_DIR = os.path.join(BASE_DIR, "TestDocs")
BASELINE_DIR = os.path.join(BASE_DIR, "TestBaseline")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
REPORT_DIR = os.path.join(BASE_DIR, f"Test_Result_{timestamp}")
os.makedirs(REPORT_DIR, exist_ok=True)

# A tesztelendő nehézségi szintek
DIFFICULTIES = ["Easy", "Medium", "Hard"]
results_log = []

def compare_with_baseline(generated_json, baseline_path):
    """Összehasonlítja a generált JSON-t a baseline-nal."""
    if not os.path.exists(baseline_path):
        return "Nincs Baseline fájl"
    
    try:
        with open(baseline_path, 'r', encoding='utf-8') as f:
            baseline_json = json.load(f)
            
        gen_q_count = len(generated_json.get("kerdesek", generated_json.get("questions", [])))
        base_q_count = len(baseline_json.get("kerdesek", baseline_json.get("questions", [])))
        
        # Lehet bővíteni komplexebb NLP hasonlósági méréssel (pl. cosine similarity)
        if gen_q_count == base_q_count:
            return f"Egyezik (Kérdések száma: {gen_q_count})"
        else:
            return f"Eltér (Generált: {gen_q_count}, Baseline: {base_q_count})"
    except Exception as e:
        return f"Hiba az összehasonlításkor: {str(e)}"

def run_pipeline_for_difficulty(difficulty):
    doc_path = os.path.join(TEST_DOCS_DIR, f"{difficulty}Doc.txt")
    baseline_path = os.path.join(BASELINE_DIR, f"{difficulty}Base.json")
    
    if not os.path.exists(doc_path):
        print(f"⚠️ Nem található a dokumentum: {doc_path} - Kihagyva.")
        return

    print(f"\n[{difficulty.upper()}] Dokumentum feldolgozása megkezdve...")
    
    # --- 1. WELLSPRING ---
    start_time = time.time()
    extracted_text = ""
    try:
        with open(doc_path, "rb") as f:
            res = requests.post(SERVICES["wellspring"], files={"file": (f"{difficulty}Doc.txt", f, "text/plain")})
        latency = time.time() - start_time
        if res.status_code == 200:
            extracted_text = res.json().get("content", "")
            results_log.append({"Nehézség": difficulty, "Modul": "Wellspring", "Válaszidő (s)": latency, "Státusz": "OK"})
        else:
            raise Exception(res.text)
    except Exception as e:
        results_log.append({"Nehézség": difficulty, "Modul": "Wellspring", "Válaszidő (s)": latency, "Státusz": "Hiba"})
        return

    # --- 2. RUNECARVER (Mentjük a chunkokat!) ---
    start_time = time.time()
    chunks = []
    try:
        res = requests.post(SERVICES["runecarver"], json={"filename": f"{difficulty}.txt", "extension": "txt", "content": extracted_text})
        latency = time.time() - start_time
        if res.status_code == 200:
            chunks = res.json().get("chunks", [])
            # Chunkok kimentése
            with open(os.path.join(REPORT_DIR, f"{difficulty}_chunks.json"), "w", encoding="utf-8") as f:
                json.dump({"chunks": chunks}, f, ensure_ascii=False, indent=4)
            results_log.append({"Nehézség": difficulty, "Modul": "RuneCarver", "Válaszidő (s)": latency, "Státusz": "OK"})
        else:
            raise Exception(res.text)
    except Exception as e:
        results_log.append({"Nehézség": difficulty, "Modul": "RuneCarver", "Válaszidő (s)": latency, "Státusz": "Hiba"})
        return

    # --- 3. BIFROST INGEST ---
    start_time = time.time()
    try:
        res = requests.post(SERVICES["bifrost_ingest"], json={"chunks": chunks})
        latency = time.time() - start_time
        if res.status_code == 200:
            results_log.append({"Nehézség": difficulty, "Modul": "Bifrost Ingest", "Válaszidő (s)": latency, "Státusz": "OK"})
        else:
            raise Exception(res.text)
    except Exception as e:
        results_log.append({"Nehézség": difficulty, "Modul": "Bifrost Ingest", "Válaszidő (s)": latency, "Státusz": "Hiba"})
        return

    # --- 4. BIFROST GENERATE & BASELINE COMPARE ---
    start_time = time.time()
    global_llm_data = {}
    try:
        query = f"Készíts tesztet a(z) {difficulty} szintű dokumentumból."
        res = requests.post(SERVICES["bifrost_generate"], json={"query": query, "limit": 3})
        latency = time.time() - start_time
        if res.status_code == 200:
            global_llm_data = res.json().get("data", {})
            # Eredmény kimentése
            generated_path = os.path.join(REPORT_DIR, f"{difficulty}_Generated.json")
            with open(generated_path, "w", encoding="utf-8") as f:
                json.dump(global_llm_data, f, ensure_ascii=False, indent=4)
            
            # Összehasonlítás a baseline-nal
            baseline_status = compare_with_baseline(global_llm_data, baseline_path)
            print(f"  -> Baseline összehasonlítás ({difficulty}): {baseline_status}")
            
            results_log.append({"Nehézség": difficulty, "Modul": "Bifrost LLM", "Válaszidő (s)": latency, "Státusz": baseline_status})
        else:
            raise Exception(res.text)
    except Exception as e:
        results_log.append({"Nehézség": difficulty, "Modul": "Bifrost LLM", "Válaszidő (s)": latency, "Státusz": "Hiba"})
        return

    # --- 5. SKALD ---
    start_time = time.time()
    try:
        res = requests.post(SERVICES["skald"], json=global_llm_data) 
        latency = time.time() - start_time
        if res.status_code == 200:
            pdf_path = os.path.join(REPORT_DIR, f"{difficulty}_Output.pdf")
            with open(pdf_path, "wb") as f:
                f.write(res.content)
            results_log.append({"Nehézség": difficulty, "Modul": "Skald", "Válaszidő (s)": latency, "Státusz": "OK"})
        else:
            raise Exception(res.text)
    except Exception as e:
        results_log.append({"Nehézség": difficulty, "Modul": "Skald", "Válaszidő (s)": latency, "Státusz": "Hiba"})

def generate_visuals_and_report():
    print("\n📊 Vizualizációk és Report generálása a publikációhoz...")
    df = pd.DataFrame(results_log)
    
    if df.empty:
        print("Nincs generálható adat.")
        return

    # --- 1. Csoportosított Oszlopdiagram generálása (Publikációhoz kiváló) ---
    pivot_df = df.pivot(index="Modul", columns="Nehézség", values="Válaszidő (s)")
    
    # Rendezzük a modulokat futási sorrendbe
    module_order = ["Wellspring", "RuneCarver", "Bifrost Ingest", "Bifrost LLM", "Skald"]
    pivot_df = pivot_df.reindex(module_order)
    
    plt.figure(figsize=(12, 7))
    # Publikációhoz illő, letisztult színek
    colors = {"Easy": "#2ecc71", "Medium": "#f39c12", "Hard": "#e74c3c"} 
    
    ax = pivot_df.plot(kind='bar', color=[colors.get(x, '#333') for x in pivot_df.columns], figsize=(12, 7), edgecolor='black')
    
    plt.title(f"Project Mimir: Feldolgozási idő (Latency) modulonként és nehézségenként\n(Mérés azonosítója: {timestamp})", fontsize=14, fontweight='bold')
    plt.ylabel("Válaszidő (másodperc)", fontsize=12)
    plt.xlabel("Mikroszolgáltatás modulok", fontsize=12)
    plt.xticks(rotation=15, ha='right', fontsize=11)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.legend(title="Dokumentum Komplexitás")
    plt.tight_layout()
    
    chart_filename = f"mimir_latency_comparison_{timestamp}.png"
    plt.savefig(os.path.join(REPORT_DIR, chart_filename), dpi=300) # Magas DPI a publikációhoz
    plt.close()

    # --- 2. Összesített Markdown Report ---
    md_path = os.path.join(REPORT_DIR, f"publikacios_report_{timestamp}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# ⚙️ Project Mimir - Publikációs E2E és Baseline Jelentés\n\n")
        f.write(f"**Teszt futtatás dátuma:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("## 📈 Teljesítmény Összehasonlítás (Latency)\n")
        f.write(f"A mellékelt diagram (`{chart_filename}`) vizuálisan ábrázolja, hogyan skálázódik a RAG pipeline az adatok komplexitásával.\n\n")
        
        f.write("## 🧪 Részletes Eredmények (Audit Log)\n\n")
        f.write(df.to_markdown(index=False))
        
        f.write("\n\n## 📂 Generált Artifaktok\n")
        f.write("A futás során az alábbi adatok lettek kimentve a jelentés mappájába (későbbi analízishez és cikkhez mellékletként):\n")
        f.write("- **Chunkok (Szemantikai darabolás eredményei):** `*_chunks.json`\n")
        f.write("- **AI Generált Tesztek:** `*_Generated.json`\n")
        f.write("- **Végeredmény (PDF-ek):** `*_Output.pdf`\n")

    print(f"✅ [KÉSZ] Minden adat, JSON és grafikon elmentve ide: '{REPORT_DIR}'")

if __name__ == "__main__":
    print(f"🚀 [START] Mimir Multi-Difficulty Baseline Teszt ({timestamp})")
    for diff in DIFFICULTIES:
        run_pipeline_for_difficulty(diff)
    generate_visuals_and_report()