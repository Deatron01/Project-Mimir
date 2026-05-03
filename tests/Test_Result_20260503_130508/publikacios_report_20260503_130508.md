# ⚙️ Project Mimir - Publikációs E2E és Baseline Jelentés

**Teszt futtatás dátuma:** 2026-05-03 13:05:40

## 📈 Teljesítmény Összehasonlítás (Latency)
A mellékelt diagram (`mimir_latency_comparison_20260503_130508.png`) vizuálisan ábrázolja, hogyan skálázódik a RAG pipeline az adatok komplexitásával.

## 🧪 Részletes Eredmények (Audit Log)

| Nehézség   | Modul          |   Válaszidő (s) | Státusz                          |
|:-----------|:---------------|----------------:|:---------------------------------|
| Easy       | Wellspring     |      0.0258756  | OK                               |
| Easy       | RuneCarver     |      1.88659    | OK                               |
| Easy       | Bifrost Ingest |      1.51451    | OK                               |
| Easy       | Bifrost LLM    |      8.96913    | Eltér (Generált: 1, Baseline: 4) |
| Easy       | Skald          |      0.0167594  | OK                               |
| Medium     | Wellspring     |      0.011029   | OK                               |
| Medium     | RuneCarver     |      2.01153    | OK                               |
| Medium     | Bifrost Ingest |      0.722842   | OK                               |
| Medium     | Bifrost LLM    |      8.17119    | Eltér (Generált: 1, Baseline: 4) |
| Medium     | Skald          |      0.015408   | OK                               |
| Hard       | Wellspring     |      0.00696015 | OK                               |
| Hard       | RuneCarver     |      2.07108    | OK                               |
| Hard       | Bifrost Ingest |      1.60503    | OK                               |
| Hard       | Bifrost LLM    |      3.99465    | Eltér (Generált: 1, Baseline: 4) |
| Hard       | Skald          |      0.0109282  | OK                               |

## 📂 Generált Artifaktok
A futás során az alábbi adatok lettek kimentve a jelentés mappájába (későbbi analízishez és cikkhez mellékletként):
- **Chunkok (Szemantikai darabolás eredményei):** `*_chunks.json`
- **AI Generált Tesztek:** `*_Generated.json`
- **Végeredmény (PDF-ek):** `*_Output.pdf`
