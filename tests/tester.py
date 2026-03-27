import requests
import os
import json
import time
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt

# --- KONFIGURÁCIÓ ---
SERVICES = {
    "wellspring": "http://localhost:8001/api/v1/extract",
    "runecarver": "http://localhost:8002/api/v1/chunk",
    "bifrost_ingest": "http://localhost:8003/api/v1/ingest",
    "bifrost_search": "http://localhost:8003/api/v1/search",
    "bifrost_generate": "http://localhost:8003/api/v1/generate",
    "skald": "http://localhost:8005/api/v1/export"
}

# 1. Megkeressük a jelenlegi fájl (tester.py) mappáját
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
REPORT_DIR = os.path.join(BASE_DIR, f"Test_Result_{timestamp}")
os.makedirs(REPORT_DIR, exist_ok=True)

# --- TESZTADATOK ÉS ELVÁRÁSOK ---
TEST_DOC = {
    "filename": "komplex_tudasbazis_teszt.txt",
    "content": (
        "Az ókori Egyiptom civilizációja a Nílus folyó völgyében alakult ki. A fáraók, akiket istenként tiszteltek, "
        "hatalmas piramisokat építtettek temetkezési helyként, melyek közül a gízai nagy piramis a legismertebb. "
        "Az egyiptomiak fejlett öntözéses földművelést és hieroglif írást alkalmaztak.\n\n"
        
        "Az ipari forradalom a 18. század végén indult el Nagy-Britanniából. A folyamat legfontosabb találmánya "
        "James Watt tökéletesített gőzgépe volt, amely forradalmasította a textilipart, a bányászatot és a közlekedést. "
        "Később a gőzhajók és a gőzmozdonyok megjelenése drasztikusan lecsökkentette az utazási időt.\n\n"
        
        "Az Apollo-11 küldetés során, 1969. július 20-án lépett először ember a Holdra. Neil Armstrong parancsnok "
        "és Buzz Aldrin holdkomppilóta több mint két órát töltött a Hold felszínén, miközben Michael Collins "
        "a parancsnoki modulban keringett az égitest körül. A küldetés a hidegháborús űrverseny csúcspontja volt.\n\n"
        
        "A fotoszintézis az a biológiai folyamat, melynek során a zöld növények a napfény energiáját felhasználva "
        "szervetlen anyagokból (vízből és szén-dioxidból) szerves anyagokat hoznak létre, miközben oxigént bocsátanak ki. "
        "A folyamat a kloroplasztiszokban, a klorofill nevű zöld pigment segítségével megy végbe."
    ),
    "expected_min_chunks": 1, 
    "search_query": "Ki volt a parancsnok az Apollo-11 küldetés során?",
    "expected_search_keyword": "Armstrong" 
}

results_log = []
global_llm_data = {} 

def record_metric(service_name, action, latency, status, expected_met=None, extra_params="-", error=None):
    results_log.append({
        "Service": service_name,
        "Lépés": action,
        "Paraméterek": extra_params, # ÚJ: Itt tároljuk a kinyert számokat!
        "Válaszidő (s)": round(latency, 4),
        "Státusz": "Sikeres" if status else "Sikertelen",
        "Elvárás Teljesült": "Igen" if expected_met else ("Nem" if expected_met is False else "N/A"),
        "Hiba": error or "-"
    })

def run_comprehensive_test():
    global global_llm_data
    print(f"🚀 [START] Átfogó Mimir E2E Teszt Paraméter-követéssel ({timestamp})")
    
    with open(TEST_DOC["filename"], "w", encoding="utf-8") as f:
        f.write(TEST_DOC["content"])

    try:
        # --- 1. WELLSPRING ---
        print("🌊 Wellspring tesztelése...")
        start_time = time.time()
        with open(TEST_DOC["filename"], "rb") as f:
            res = requests.post(SERVICES["wellspring"], files={"file": (TEST_DOC["filename"], f, "text/plain")})
        latency = time.time() - start_time
        
        if res.status_code == 200:
            data = res.json()
            extracted_text = data.get("content", "")
            expected_met = len(extracted_text) > 50
            
            # Paraméterek kinyerése
            params = f"Karakterszám: {len(extracted_text)}, Metódus: {data.get('extraction_method', 'N/A')}"
            record_metric("Wellspring", "Szövegkinyerés", latency, True, expected_met, params)
        else:
            record_metric("Wellspring", "Szövegkinyerés", latency, False, error=res.text)
            return

        # --- 2. RUNECARVER ---
        print("ᛋ RuneCarver tesztelése...")
        start_time = time.time()
        res = requests.post(SERVICES["runecarver"], json={"filename": TEST_DOC["filename"], "extension": "txt", "content": extracted_text})
        latency = time.time() - start_time
        
        if res.status_code == 200:
            chunks = res.json().get("chunks", [])
            expected_met = len(chunks) >= TEST_DOC["expected_min_chunks"]
            
            # Paraméterek kinyerése
            params = f"Legenerált chunkok száma: {len(chunks)} db"
            record_metric("RuneCarver", "Szemantikai Darabolás", latency, True, expected_met, params)
        else:
            record_metric("RuneCarver", "Szemantikai Darabolás", latency, False, error=res.text)
            return

        # --- 3. BIFROST INGEST ---
        print("🌈 Bifrost (Ingest) tesztelése...")
        start_time = time.time()
        res = requests.post(SERVICES["bifrost_ingest"], json={"chunks": chunks})
        latency = time.time() - start_time
        
        if res.status_code == 200:
            indexed = res.json().get("indexed_chunks", 0)
            expected_met = indexed == len(chunks)
            
            # Paraméterek kinyerése
            params = f"Qdrant adatbázisba mentve: {indexed} vektor"
            record_metric("Bifrost", "Vektor Indexelés", latency, True, expected_met, params)
        else:
            record_metric("Bifrost", "Vektor Indexelés", latency, False, error=res.text)
            return

        # --- 4. BIFROST LLM GENERATE ---
        print("🧠 Bifrost (Qwen AI Generálás) tesztelése...")
        start_time = time.time()
        res = requests.post(SERVICES["bifrost_generate"], json={"query": TEST_DOC["search_query"], "limit": 1})
        latency = time.time() - start_time
        
        if res.status_code == 200:
            global_llm_data = res.json().get("data", {})
            json_path = os.path.join(REPORT_DIR, f"test_output_{timestamp}.json")
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(global_llm_data, f, ensure_ascii=False, indent=4)
            
            expected_met = "questions" in global_llm_data and len(global_llm_data["questions"]) > 0
            
            # Paraméterek kinyerése
            q_count = len(global_llm_data.get("questions", []))
            params = f"Kérdések: {q_count} db, Formátum: {global_llm_data.get('format', 'N/A')}"
            record_metric("Bifrost_LLM", "Qwen Generálás", latency, True, expected_met, params)
        else:
            record_metric("Bifrost_LLM", "Qwen Generálás", latency, False, error=res.text)
            return

        # --- 5. SKALD ---
        print("📜 Skald (PDF Export) tesztelése...")
        start_time = time.time()
        res = requests.post(SERVICES["skald"], json=global_llm_data) 
        latency = time.time() - start_time
        
        if res.status_code == 200:
            pdf_path = os.path.join(REPORT_DIR, f"test_output_{timestamp}.pdf")
            with open(pdf_path, "wb") as f:
                f.write(res.content)
            
            file_size_kb = round(os.path.getsize(pdf_path) / 1024, 2)
            params = f"PDF Fájlméret: {file_size_kb} KB"
            record_metric("Skald", "PDF Generálás", latency, True, os.path.exists(pdf_path), params)
        else:
            record_metric("Skald", "PDF Generálás", latency, False, error=res.text)

    finally:
        if os.path.exists(TEST_DOC["filename"]):
            os.remove(TEST_DOC["filename"])
        
        generate_visuals_and_report()

def generate_visuals_and_report():
    print("\n📊 Vizualizációk és Report generálása...")
    df = pd.DataFrame(results_log)
    
    # 1. Grafikon: Válaszidők
    plt.figure(figsize=(10, 6))
    colors = ['#3498db' if s == 'Sikeres' else '#e74c3c' for s in df['Státusz']]
    bars = plt.bar(df['Service'] + "\n(" + df['Lépés'] + ")", df['Válaszidő (s)'], color=colors)
    plt.title(f"Mikroszolgáltatások Válaszideje (Latency) - {timestamp}")
    plt.ylabel("Idő (Másodperc)")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    
    chart_filename = f"latency_chart_{timestamp}.png"
    chart_path = os.path.join(REPORT_DIR, chart_filename)
    plt.savefig(chart_path)
    plt.close()

    # 2. Markdown Report Generálása
    md_filename = f"e2e_report_{timestamp}.md"
    md_path = os.path.join(REPORT_DIR, md_filename)
    
    total_time = df['Válaszidő (s)'].sum()
    all_passed = all(df['Státusz'] == 'Sikeres') and all(df['Elvárás Teljesült'].isin(['Igen', 'N/A']))

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# ⚙️ Projekt Mimir - Átfogó E2E Integrációs Jelentés\n\n")
        f.write(f"**Dátum és Idő:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Végeredmény:** {'🟢 SIKERES' if all_passed else '🔴 HIBÁS'}\n")
        f.write(f"**Teljes feldolgozási idő:** {round(total_time, 3)} másodperc\n\n")
        
        f.write("## 📈 Teljesítmény Metrikák (Latency)\n\n")
        f.write(f"![Latency Chart](./{chart_filename})\n\n")
        
        f.write("## 🧪 Lépésenkénti Eredmények (Audit Log)\n\n")
        f.write(df.to_markdown(index=False))
        
        f.write("\n\n## 📝 Tesztelt Adathalmaz\n\n")
        f.write("**Bemeneti nyers szöveg (Wellspring):**\n")
        f.write("```text\n")
        f.write(f"{TEST_DOC['content']}\n")
        f.write("```\n\n")
        f.write(f"**Keresési Lekérdezés (Bifrost):** `{TEST_DOC['search_query']}`\n\n")
        f.write(f"**Elvárt Keresési Találat:** `{TEST_DOC['expected_search_keyword']}`\n")
        
        f.write("\n\n## 🤖 AI Által Generált Teszt (JSON kimenet)\n\n")
        f.write("```json\n")
        f.write(json.dumps(global_llm_data, ensure_ascii=False, indent=4) if global_llm_data else "{}")
        f.write("\n```\n")

    print(f"✅ [KÉSZ] A jelentés és a grafikon elmentve a '{REPORT_DIR}' mappába!")
    print(f"👉 Nyisd meg a '{md_path}' fájlt a részletekért!")

if __name__ == "__main__":
    run_comprehensive_test()