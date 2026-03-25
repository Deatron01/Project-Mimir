import time
import os
import webbrowser
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from difflib import SequenceMatcher
from pipeline import RAGPipeline

class RAGBenchmarker:
    def __init__(self):
        print("--- RAG Benchmarker Indítása (Ground Truth támogatással) ---")
        self.pipeline = RAGPipeline(device='cuda')
        self.results = []

    def _calculate_accuracy(self, actual_chunks, expected_chunks):
        """Kiszámolja, hogy a generált chunkok mennyire egyeznek a várt eredményekkel (0-100%)."""
        if not expected_chunks:
            return 100.0 # Ha nincs megadva elvárt eredmény, 100%-nak vesszük

        total_similarity = 0
        for expected in expected_chunks:
            best_match_score = 0
            for actual in actual_chunks:
                # Kiszámoljuk a szöveges hasonlóságot az elvárt és a kapott chunk között
                sim = SequenceMatcher(None, expected.strip(), actual['content'].strip()).ratio()
                if sim > best_match_score:
                    best_match_score = sim
            total_similarity += best_match_score

        # Átlagoljuk a hasonlóságot az összes elvárt chunkra
        accuracy = (total_similarity / len(expected_chunks)) * 100
        return round(accuracy, 2)

    def run_benchmark(self, test_documents):
        print("\n--- Tesztelés Megkezdése ---")
        
        for doc in test_documents:
            doc_name = doc['name']
            text = doc['text']
            ext = doc['ext']
            complexity = doc['complexity']
            expected_chunks = doc.get('expected_chunks', [])
            
            print(f"Tesztelés alatt: {doc_name} (Komplexitás: {complexity})")
            
            # Feldolgozás és mérés
            start_time = time.time()
            chunks = self.pipeline.process_document(text, ext, percentile=95.0)
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            # Metrikák
            num_chunks = len(chunks)
            qa_scores = [c['metadata']['qa_score'] for c in chunks if 'qa_score' in c['metadata']]
            avg_qa = sum(qa_scores) / len(qa_scores) if qa_scores else 10.0
            fallback_count = sum(1 for score in qa_scores if score < 7)
            
            # Ground Truth (Elvárt) Eredmények összevetése
            expected_count = len(expected_chunks) if expected_chunks else num_chunks
            count_diff = abs(expected_count - num_chunks)
            accuracy = self._calculate_accuracy(chunks, expected_chunks)
            
            self.results.append({
                "Dokumentum": doc_name,
                "Komplexitás": complexity,
                "Hossz (Kar.)": len(text),
                "Feldolgozási Idő (s)": round(processing_time, 4),
                "Elvárt Chunkok": expected_count,
                "Generált Chunkok": num_chunks,
                "Eltérés (Darab)": count_diff,
                "Tartalmi Pontosság (%)": accuracy,
                "Átlagos QA Pont": round(avg_qa, 2),
                "Fallback Események": fallback_count
            })
            
        print("--- Tesztelés Befejezve ---\n")
        return pd.DataFrame(self.results)

    def visualize_results(self, df):
        print("Grafikonok generálása...")
        plt.style.use('bmh')
        
        # 3x2-es rácsot hozunk létre, hogy az új metrikák is elférjenek
        fig, axes = plt.subplots(3, 2, figsize=(15, 14))
        fig.suptitle('RAG Szemantikai Chunker Teljesítmény és Pontosság', fontsize=18)

        # 1. Feldolgozási idő
        scatter = axes[0, 0].scatter(df['Hossz (Kar.)'], df['Feldolgozási Idő (s)'], 
                                     c=df['Komplexitás'], cmap='viridis', s=100, alpha=0.8)
        axes[0, 0].set_title('Feldolgozási Idő vs. Karakterhossz')
        axes[0, 0].set_xlabel('Hossz (Karakter)')
        axes[0, 0].set_ylabel('Idő (s)')
        fig.colorbar(scatter, ax=axes[0, 0], label='Komplexitás')

        # 2. Elvárt vs Generált Chunkok száma (Csoportosított Oszlopdiagram)
        x = np.arange(len(df['Dokumentum']))
        width = 0.35
        axes[0, 1].bar(x - width/2, df['Elvárt Chunkok'], width, label='Elvárt', color='lightgray')
        axes[0, 1].bar(x + width/2, df['Generált Chunkok'], width, label='Generált', color='royalblue')
        axes[0, 1].set_title('Elvárt vs. Generált Chunkok Száma')
        axes[0, 1].set_xticks(x)
        axes[0, 1].set_xticklabels(df['Dokumentum'], rotation=45)
        axes[0, 1].legend()

        # 3. Tartalmi Pontosság (%)
        axes[1, 0].plot(df['Dokumentum'], df['Tartalmi Pontosság (%)'], marker='s', color='purple', linewidth=2)
        axes[1, 0].axhline(y=90.0, color='r', linestyle='--', label='90% Célkitűzés')
        axes[1, 0].set_title('Tartalmi Egyezés az Elvárttal (%)')
        axes[1, 0].set_ylim(0, 110)
        axes[1, 0].tick_params(axis='x', rotation=45)
        axes[1, 0].legend()

        # 4. Chunk Darabszám Eltérés (Hiba)
        axes[1, 1].bar(df['Dokumentum'], df['Eltérés (Darab)'], color='crimson')
        axes[1, 1].set_title('Darabszám Eltérés (Hiba)')
        axes[1, 1].tick_params(axis='x', rotation=45)

        # 5. Átlagos QA Pontszám
        axes[2, 0].plot(df['Dokumentum'], df['Átlagos QA Pont'], marker='o', color='forestgreen', linewidth=2)
        axes[2, 0].axhline(y=7.0, color='r', linestyle='--', label='Kritikus Határ (7.0)')
        axes[2, 0].set_title('Átlagos Koherencia (QA) Pontszám')
        axes[2, 0].set_ylim(0, 10)
        axes[2, 0].tick_params(axis='x', rotation=45)
        axes[2, 0].legend()

        # 6. Fallback Események
        axes[2, 1].bar(df['Dokumentum'], df['Fallback Események'], color='darkorange')
        axes[2, 1].set_title('Fallback (STD 2.0) Események')
        axes[2, 1].tick_params(axis='x', rotation=45)

        plt.tight_layout()
        plt.savefig('rag_benchmark_results.png', dpi=300)
        print("✅ Grafikon mentve: 'rag_benchmark_results.png'")

def generate_html_report(df, image_path="rag_benchmark_results.png", output_file="rag_report.html"):
    print("\nRiport generálása...")
    html_content = f"""
    <!DOCTYPE html>
    <html lang="hu">
    <head>
        <meta charset="UTF-8">
        <title>RAG Pipeline Analitikai Riport</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; color: #333; background-color: #f9f9f9; }}
            .container {{ max-width: 1200px; margin: auto; background: white; padding: 30px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border-radius: 8px; }}
            h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
            h2 {{ color: #2980b9; margin-top: 30px; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; font-size: 14px; }}
            th, td {{ padding: 12px; border: 1px solid #ddd; text-align: center; }}
            th {{ background-color: #3498db; color: white; font-weight: bold; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            tr:hover {{ background-color: #e8f4f8; }}
            .img-container {{ text-align: center; margin-top: 30px; }}
            img {{ max-width: 100%; height: auto; border: 1px solid #ddd; border-radius: 4px; padding: 5px; }}
            .good {{ color: green; font-weight: bold; }}
            .bad {{ color: red; font-weight: bold; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>RAG Szemantikai Chunker - Pontossági és Teljesítmény Riport</h1>
            <p><strong>Cél:</strong> A dinamikus szemantikai vágás pontosságának (Ground Truth) és feldolgozási sebességének ellenőrzése.</p>
            
            <h2>📊 Részletes Metrikák (Elvárt vs. Kapott)</h2>
            {df.to_html(index=False, classes="table")}
            
            <h2>📈 Teljesítmény és Minőség Vizualizáció</h2>
            <div class="img-container">
                <img src="{image_path}" alt="Benchmark Grafikonok">
            </div>
        </div>
    </body>
    </html>
    """
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    full_path = 'file://' + os.path.realpath(output_file)
    webbrowser.open(full_path)


if __name__ == "__main__":
    
    # --- Tesztdokumentumok PDF integrációval ---
    test_docs = [
        {
            "name": "Éles_Témaváltás_Teszt",
            "ext": "txt",
            "complexity": 1,
            "text": "Az almák pirosak és ropogósak. A gyümölcsök nagyon egészségesek. A traktorok hatalmas mezőgazdasági gépek. Erős dízelmotorral vannak felszerelve.",
            "expected_chunks": [
                "Az almák pirosak és ropogósak. A gyümölcsök nagyon egészségesek.",
                "A traktorok hatalmas mezőgazdasági gépek. Erős dízelmotorral vannak felszerelve."
            ]
        },
        {
            "name": "Kód_és_Narratíva",
            "ext": "md",
            "complexity": 3,
            "text": "Íme egy egyszerű Python függvény a számoláshoz:\n\n" + 
                    "```python\n" + 
                    "def add(a, b):\n" + 
                    "    return a + b\n" + 
                    "```\n\n" + 
                    "Most pedig beszéljünk a felhő alapú számítástechnikáról. Az AWS és az Azure a két legnagyobb szolgáltató.",
            "expected_chunks": [
                "Íme egy egyszerű Python függvény a számoláshoz:",
                "def add(a, b):\n    return a + b",
                "Most pedig beszéljünk a felhő alapú számítástechnikáról. Az AWS és az Azure a két legnagyobb szolgáltató."
            ]
        },
        {
            "name": "Tiszta_Digitális_PDF",
            "ext": "pdf",
            "complexity": 2,
            "text": "test_1_native.pdf", 
            "expected_chunks": []
        },
        {
            "name": "Szkennelt_Képes_PDF",
            "ext": "pdf",
            "complexity": 3, 
            "text": "test_2_scanned.pdf", 
            "expected_chunks": []
        }
    ]

    # VÉGREHAJTÁS: Pontosan 4 szóközzel beljebb az 'if' alatt!
    benchmarker = RAGBenchmarker()
    df_results = benchmarker.run_benchmark(test_docs)
    benchmarker.visualize_results(df_results)
    generate_html_report(df_results)