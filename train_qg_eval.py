import os
import time
from datetime import datetime
import torch
import pandas as pd
import matplotlib.pyplot as plt
from transformers import (
    AutoTokenizer, AutoModelForSeq2SeqLM, Seq2SeqTrainingArguments, 
    Seq2SeqTrainer, DataCollatorForSeq2Seq, TrainerCallback
)
from peft import get_peft_model, LoraConfig, TaskType
from datasets import Dataset, load_dataset, load_from_disk # <-- ÚJ IMPORT

# ==========================================
# 1. KÖNYVTÁR STRUKTÚRA ÉS DÁTUMOZÁS
# ==========================================
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = f"./evaluation_results_{timestamp}"
os.makedirs(output_dir, exist_ok=True)
print(f"📁 Eredmények mentése ide: {output_dir}")

# ==========================================
# 2. CUSTOM CALLBACK A METRIKÁK GYŰJTÉSÉRE
# ==========================================
class ComprehensiveMetricsTracker(TrainerCallback):
    """
    Ez a modul rögzíti az AI metrikákat (Loss) és a PC/Hardver metrikákat (VRAM, Idő)
    minden logolási lépésnél.
    """
    def __init__(self):
        self.metrics_history = []
        self.start_time = time.time()

    def on_log(self, args, state, control, logs=None, **kwargs):
        if logs is not None:
            # GPU VRAM mérése (MB-ban)
            vram_alloc_mb = torch.cuda.memory_allocated() / (1024**2) if torch.cuda.is_available() else 0
            vram_max_mb = torch.cuda.max_memory_allocated() / (1024**2) if torch.cuda.is_available() else 0
            
            elapsed_time = time.time() - self.start_time
            
            record = {
                "Step": state.global_step,
                "Epoch": round(state.epoch, 2) if state.epoch else None,
                "Training Loss": logs.get("loss", None),
                "Eval Loss": logs.get("eval_loss", None),
                "Learning Rate": logs.get("learning_rate", None),
                "VRAM Allocated (MB)": round(vram_alloc_mb, 2),
                "VRAM Max Peak (MB)": round(vram_max_mb, 2),
                "Elapsed Time (sec)": round(elapsed_time, 2)
            }
            self.metrics_history.append(record)

# ==========================================
# 3. MODELL ÉS SQUAD ADATBÁZIS ELŐKÉSZÍTÉSE
# ==========================================
model_id = "google/flan-t5-base"
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForSeq2SeqLM.from_pretrained(model_id, device_map="auto")

peft_config = LoraConfig(
    task_type=TaskType.SEQ_2_SEQ_LM,
    inference_mode=False,
    r=16,          # <-- Növelve 8-ról 16-ra a jobb tanulásért!
    lora_alpha=32,
    lora_dropout=0.1
)
model = get_peft_model(model, peft_config)

# --- ÚJ: LOKÁLIS ADATBÁZIS KEZELÉS ---
dataset_dir = "./squad_local_dataset"

if not os.path.exists(dataset_dir):
    print(f"📥 SQuAD letöltése a netről és mentése lokálisan ide: {dataset_dir}...")
    raw_datasets = load_dataset("squad")
    raw_datasets.save_to_disk(dataset_dir)
else:
    print(f"📂 Lokális adathalmaz betöltése a lemezről ({dataset_dir})...")
    raw_datasets = load_from_disk(dataset_dir)

# A megnövelt adatmennyiség a komolyabb tanításhoz
train_dataset = raw_datasets["train"].shuffle(seed=42)
eval_dataset = raw_datasets["validation"].shuffle(seed=42)

def preprocess_function(examples):
    inputs = ["Generate question based on context: " + doc for doc in examples["context"]]
    model_inputs = tokenizer(inputs, max_length=256, truncation=True, padding="max_length")
    labels = tokenizer(examples["question"], max_length=64, truncation=True, padding="max_length")
    model_inputs["labels"] = labels["input_ids"]
    return model_inputs

print("⚙️ Adatok tokenizálása...")
train_tokenized = train_dataset.map(
    preprocess_function, 
    batched=True, 
    remove_columns=train_dataset.column_names
)
eval_tokenized = eval_dataset.map(
    preprocess_function, 
    batched=True, 
    remove_columns=eval_dataset.column_names
)

data_collator = DataCollatorForSeq2Seq(tokenizer=tokenizer, model=model)

# ==========================================
# 4. TANÍTÁS ÉS METRIKA RÖGZÍTÉS
# ==========================================
metrics_tracker = ComprehensiveMetricsTracker()

training_args = Seq2SeqTrainingArguments(
    output_dir=f"{output_dir}/checkpoints",
    learning_rate=3e-4,
    per_device_train_batch_size=64, # 3090-en a 64 tökéletes. Ha 3070 Ti-n/3060-on futtatod, vedd le 16-ra!
    per_device_eval_batch_size=32,
    num_train_epochs=5,
    logging_steps=50,             # <-- Visszaállítva 50-re a fagyás elkerülése végett
    eval_strategy="steps",
    eval_steps=50,                # <-- Visszaállítva 50-re
    save_strategy="epoch",
    report_to="none"              
)

trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=train_tokenized,
    eval_dataset=eval_tokenized,
    processing_class=tokenizer,
    data_collator=data_collator,
    callbacks=[metrics_tracker]
)

print("🚀 Tanítás indítása és mérések gyűjtése...")
trainer.train()

# ==========================================
# 5. ADATOK EXPORTÁLÁSA ÉS DIAGRAMOK GENERÁLÁSA
# ==========================================
print("📊 Mérések feldolgozása és exportálása...")

df_metrics = pd.DataFrame(metrics_tracker.metrics_history)
df_metrics["Training Loss"] = df_metrics["Training Loss"].ffill()
df_metrics["Eval Loss"] = df_metrics["Eval Loss"].ffill()

excel_path = os.path.join(output_dir, "training_metrics.xlsx")
df_metrics.to_excel(excel_path, index=False)
print(f"✅ Excel elmentve: {excel_path}")

plt.figure(figsize=(10, 6))
if "Training Loss" in df_metrics.columns:
    plt.plot(df_metrics["Step"], df_metrics["Training Loss"], label="Training Loss", marker='o')
if "Eval Loss" in df_metrics.columns:
    plt.plot(df_metrics["Step"], df_metrics["Eval Loss"], label="Validation Loss", marker='x')
plt.title("Modell Tanulási Görbéje (Loss)")
plt.xlabel("Lépések (Steps)")
plt.ylabel("Veszteség (Loss)")
plt.legend()
plt.grid(True)
loss_plot_path = os.path.join(output_dir, "loss_curve.png")
plt.savefig(loss_plot_path)
plt.close()
print(f"✅ Loss diagram elmentve: {loss_plot_path}")

plt.figure(figsize=(10, 6))
plt.plot(df_metrics["Step"], df_metrics["VRAM Allocated (MB)"], label="Aktív VRAM (MB)", color='orange')
plt.plot(df_metrics["Step"], df_metrics["VRAM Max Peak (MB)"], label="Max VRAM Csúcs (MB)", color='red', linestyle='dashed')
plt.fill_between(df_metrics["Step"], df_metrics["VRAM Allocated (MB)"], color='orange', alpha=0.3)
plt.title("GPU Memória (VRAM) Felhasználás a Tanítás Során")
plt.xlabel("Lépések (Steps)")
plt.ylabel("Memória (MB)")
plt.legend()
plt.grid(True)
vram_plot_path = os.path.join(output_dir, "vram_usage.png")
plt.savefig(vram_plot_path)
plt.close()
print(f"✅ VRAM diagram elmentve: {vram_plot_path}")

final_model_dir = os.path.join(output_dir, "final_lora_model")
trainer.model.save_pretrained(final_model_dir)
tokenizer.save_pretrained(final_model_dir)
print(f"🎉 Kész! A betanított modell itt található: {final_model_dir}")