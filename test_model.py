import os
import glob
import torch
import pandas as pd
from datetime import datetime
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from peft import PeftModel
from datasets import load_dataset

# ==========================================
# 0. DINAMIKUS MAPPAKERESŐ
# ==========================================
def get_latest_model_paths(base_dir="."):
    search_pattern = os.path.join(base_dir, "evaluation_results_*")
    directories = glob.glob(search_pattern)
    if not directories:
        raise FileNotFoundError("❌ Nem találtam egyetlen 'evaluation_results_' mappát sem!")
    
    directories.sort()
    latest_dir = directories[-1]
    final_path = os.path.join(latest_dir, "final_lora_model")
    
    if not os.path.exists(final_path):
        raise FileNotFoundError(f"❌ A legújabb mappában ({latest_dir}) nincs 'final_lora_model'!")
        
    return latest_dir, final_path

# ==========================================
# 1. MODELL ÉS TOKENIZER BETÖLTÉSE
# ==========================================
model_id = "google/flan-t5-base"
tokenizer = AutoTokenizer.from_pretrained(model_id)
base_model = AutoModelForSeq2SeqLM.from_pretrained(model_id, device_map="auto")

try:
    target_dir, lora_model_path = get_latest_model_paths()
    print(f"✅ Legújabb modell megtalálva itt: {target_dir}")
except Exception as e:
    print(e)
    exit()

print("⏳ Betanított modell betöltése a memóriába...")
model = PeftModel.from_pretrained(base_model, lora_model_path)
model.eval()

device = "cuda" if torch.cuda.is_available() else "cpu"

# ==========================================
# 2. FELHASZNÁLÓI BEMENET (IGAZI FELUGRÓ ABLAK)
# ==========================================
import tkinter as tk
from tkinter import simpledialog

# Létrehozunk egy láthatatlan főablakot
ROOT = tk.Tk()
ROOT.withdraw()

# Felugró ablak megjelenítése
user_input = simpledialog.askinteger(
    title="Tesztelés indítása",
    prompt="Hány tesztkérdést szeretnél generálni? (pl. 5, 15, 50):",
    minvalue=1,
    maxvalue=10000
)

if user_input is None:
    print("❌ Tesztelés megszakítva a felhasználó által.")
    exit()

num_samples = user_input
print(f"👉 Kiválasztott mennyiség: {num_samples} db")

# ==========================================
# 3. TESZT ADATHALMAZ BETÖLTÉSE
# ==========================================
print("📥 SQuAD validációs adathalmaz betöltése...")
full_val_dataset = load_dataset("squad", split="validation")
max_available = len(full_val_dataset)

# Biztonsági ellenőrzés, ha túl nagy számot adna meg valaki
if num_samples > max_available:
    print(f"⚠️ A kért mennyiség ({num_samples}) nagyobb, mint az elérhető tesztszövegek száma ({max_available}).")
    print(f"⚠️ Automatikus beállítás a maximumra: {max_available}")
    num_samples = max_available

current_seed = int(datetime.now().timestamp())
test_dataset = full_val_dataset.shuffle(seed=current_seed).select(range(num_samples))

# ==========================================
# 4. AUTOMATIZÁLT TESZTELÉSI CIKLUS
# ==========================================
print(f"⚙️ Tesztelés indítása {num_samples} dokumentumon...")

results = []
run_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

for i, example in enumerate(test_dataset):
    print(f"⏳ Feldolgozás: {i+1}/{num_samples}...")
    
    context = example["context"]
    
    # --- A) KÉRDÉS GENERÁLÁSA (LoRA BEKAPCSOLVA) ---
    q_prompt = "Generate question based on context: " + context
    q_inputs = tokenizer(q_prompt, return_tensors="pt", max_length=256, truncation=True).to(device)
    
    with torch.no_grad():
        q_outputs = model.generate(**q_inputs, max_length=64, num_beams=4, early_stopping=True)
    generated_question = tokenizer.decode(q_outputs[0], skip_special_tokens=True)
    
    # --- B) VÁLASZ GENERÁLÁSA (LoRA KIKAPCSOLVA) ---
    with model.disable_adapter():
        a_prompt = f"Answer the question based on the context. Context: {context} Question: {generated_question}"
        a_inputs = tokenizer(a_prompt, return_tensors="pt", max_length=256, truncation=True).to(device)
        
        with torch.no_grad():
            a_outputs = model.generate(**a_inputs, max_length=64, num_beams=4, early_stopping=True)
        generated_answer = tokenizer.decode(a_outputs[0], skip_special_tokens=True)
        
    results.append({
        "Run Timestamp": run_timestamp,
        "ID": i + 1,
        "Context (Nyers szöveg)": context,
        "Generated Question (AI Kérdés)": generated_question,
        "Generated Answer (AI Válasz)": generated_answer,
        "Original Human Question": example["question"],
        "Original Human Answer": example["answers"]["text"][0] if example["answers"]["text"] else ""
    })

# ==========================================
# 5. EXPORTÁLÁS ÉS HOZZÁFŰZÉS (APPEND) EXCELBE
# ==========================================
print("\n📊 Adatok feldolgozása és mentése...")
df_new = pd.DataFrame(results)
excel_filename = os.path.join(target_dir, "automated_qa_tests.xlsx")

if os.path.exists(excel_filename):
    print("📝 Meglévő tesztnapló (Excel) megtalálva, új adatok hozzáfűzése...")
    df_existing = pd.read_excel(excel_filename)
    
    last_id = df_existing["ID"].max() if not df_existing.empty else 0
    df_new["ID"] = df_new["ID"] + last_id
    
    df_final = pd.concat([df_existing, df_new], ignore_index=True)
else:
    print("📝 Új tesztnapló (Excel) létrehozása...")
    df_final = df_new

df_final.to_excel(excel_filename, index=False)
print(f"🎉 Kész! A teszteredmények sikeresen frissítve az Excelben:\n👉 {excel_filename}")