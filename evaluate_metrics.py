import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from difflib import SequenceMatcher

# ==========================================
# 0. MAPPA ÉS ADATOK BETÖLTÉSE
# ==========================================
def get_latest_model_dir(base_dir="."):
    search_pattern = os.path.join(base_dir, "evaluation_results_*")
    directories = glob.glob(search_pattern)
    if not directories:
        raise FileNotFoundError("❌ Nem találtam 'evaluation_results_' mappát!")
    directories.sort()
    return directories[-1]

target_dir = get_latest_model_dir()
excel_path = os.path.join(target_dir, "automated_qa_tests.xlsx")

if not os.path.exists(excel_path):
    print(f"❌ Nem találtam tesztadatokat ({excel_path})! Futtasd le előbb a tesztelőt.")
    exit()

# --- ÚJ: Dedikált mappa a riportoknak ---
reports_dir = os.path.join(target_dir, "evaluation_reports")
os.makedirs(reports_dir, exist_ok=True)
print(f"📁 Riport mappa létrehozva: {reports_dir}")

print(f"📥 Tesztadatok betöltése innen: {excel_path}")
df = pd.read_excel(excel_path)

# ==========================================
# 1. METRIKÁK KISZÁMÍTÁSA
# ==========================================
print("⚙️ Hasonlósági metrikák és statisztikák számítása...")

# Egyszerű szöveges hasonlóság (0-100%)
def similarity(a, b):
    if pd.isna(a) or pd.isna(b): return 0
    return SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio() * 100

df["Question Similarity (%)"] = df.apply(lambda x: similarity(x["Generated Question (AI Kérdés)"], x["Original Human Question"]), axis=1)
df["Answer Similarity (%)"] = df.apply(lambda x: similarity(x["Generated Answer (AI Válasz)"], x["Original Human Answer"]), axis=1)

df["AI Question Length (words)"] = df["Generated Question (AI Kérdés)"].astype(str).apply(lambda x: len(x.split()))
df["Human Question Length (words)"] = df["Original Human Question"].astype(str).apply(lambda x: len(x.split()))

# Eredmények mentése az új almappába
eval_excel_path = os.path.join(reports_dir, "evaluated_qa_metrics.xlsx")
df.to_excel(eval_excel_path, index=False)
print(f"✅ Részletes kiértékelés elmentve: {eval_excel_path}")

# ==========================================
# 2. DIAGRAMOK GENERÁLÁSA (Komplementer színekkel)
# ==========================================
print("📊 Diagramok rajzolása...")

# Színpaletták (Komplementer: Kék-Narancs, Bíbor-Zöld, stb.)
color_ai_blue = '#1F77B4'    # Mélykék
color_human_orange = '#FF7F0E' # Narancs
color_ai_purple = '#542788'  # Bíbor
color_human_green = '#5AAE61' # Zöld

# --- 1. Ábra: Átlagos Hasonlósági Pontszámok (Bar Chart) ---
plt.figure(figsize=(8, 6))
avg_q_sim = df["Question Similarity (%)"].mean()
avg_a_sim = df["Answer Similarity (%)"].mean()

bars = plt.bar(["Kérdések Hasonlósága", "Válaszok Hasonlósága"], [avg_q_sim, avg_a_sim], color=[color_ai_blue, color_human_orange])
plt.title("AI vs Emberi Generálás Hasonlósága (Átlagos %)")
plt.ylabel("Átlagos Hasonlóság (%)")
plt.ylim(0, 100)

for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 1, f"{round(yval, 1)}%", ha='center', va='bottom', fontweight='bold')

plt.savefig(os.path.join(reports_dir, "01_plot_similarity_averages.png"))
plt.close()

# --- 2. Ábra: Kérdések hosszának eloszlása ---
plt.figure(figsize=(10, 5))
x = np.arange(len(df))
width = 0.35

plt.bar(x - width/2, df["AI Question Length (words)"], width, label='AI Kérdés (Szavak)', color=color_ai_purple)
plt.bar(x + width/2, df["Human Question Length (words)"], width, label='Emberi Kérdés (Szavak)', color=color_human_green)

plt.title("Kérdések Hosszának Összehasonlítása (AI vs Ember)")
plt.xlabel("Teszteset (Sorszám)")
plt.ylabel("Szavak száma")
plt.legend()
plt.grid(axis='y', linestyle='--', alpha=0.7)

plt.savefig(os.path.join(reports_dir, "02_plot_question_lengths.png"))
plt.close()

# --- 3. Ábra: Válaszok helyességének eloszlása (Kördiagram) ---
# Kategóriák létrehozása a hasonlóság alapján
conditions = [
    (df["Answer Similarity (%)"] >= 80),
    (df["Answer Similarity (%)"] >= 40) & (df["Answer Similarity (%)"] < 80),
    (df["Answer Similarity (%)"] < 40)
]
choices = ["Kiváló Egyezés (>=80%)", "Részleges (40-79%)", "Gyenge/Téves (<40%)"]
df["Answer Category"] = np.select(conditions, choices, default="Ismeretlen")

category_counts = df["Answer Category"].value_counts()
colors_pie = ['#2CA02C', '#FFBB78', '#D62728'] # Zöld, Pasztell Narancs, Piros

plt.figure(figsize=(8, 6))
plt.pie(category_counts, labels=category_counts.index, autopct='%1.1f%%', startangle=140, colors=colors_pie, wedgeprops={'edgecolor': 'white'})
plt.title("Generált Válaszok Helyességének Eloszlása")

plt.savefig(os.path.join(reports_dir, "03_plot_answer_correctness_pie.png"))
plt.close()

# --- 4. Ábra: Szórásdiagram (Kérdés hasonlóság vs Válasz hasonlóság) ---
plt.figure(figsize=(8, 6))
plt.scatter(df["Question Similarity (%)"], df["Answer Similarity (%)"], color=color_ai_blue, alpha=0.7, edgecolors='black', s=80)

# Trendvonal számítása (ha van elég adat)
if len(df) > 1:
    z = np.polyfit(df["Question Similarity (%)"], df["Answer Similarity (%)"], 1)
    p = np.poly1d(z)
    plt.plot(df["Question Similarity (%)"], p(df["Question Similarity (%)"]), color=color_human_orange, linestyle="--", label="Trendvonal")

plt.title("Összefüggés a Kérdés és a Válasz Minősége Között")
plt.xlabel("Kérdés Hasonlósága az Emberihez (%)")
plt.ylabel("Válasz Hasonlósága az Emberihez (%)")
plt.legend()
plt.grid(True, linestyle='--', alpha=0.5)

plt.savefig(os.path.join(reports_dir, "04_plot_correlation_scatter.png"))
plt.close()

print(f"🎉 Kész! A 4 db diagram és az Excel sikeresen legenerálva az 'evaluation_reports' mappába!")