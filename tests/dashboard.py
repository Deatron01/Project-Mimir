import streamlit as st
import os
import pandas as pd
from rag_system import IntegratedRAGSystem
from qdrant_client import models

# Oldal konfiguráció
st.set_page_config(page_title="RAG Analitikai Központ", layout="wide", page_icon="🚀")

# Rendszer inicializálása
@st.cache_resource
def load_system():
    return IntegratedRAGSystem()

rag = load_system()

st.title("🚀 Szemantikai RAG Analitikai Központ")

# --- OLDALSÁV: ADATKEZELÉS ---
st.sidebar.header("📁 Adatforrás Kezelő")
uploaded_file = st.sidebar.file_uploader("Fájl feltöltése (PDF, MD, TXT)", type=['pdf', 'md', 'txt'])

st.sidebar.divider()
st.sidebar.subheader("⚙️ Szemantikai Beállítások")
st.sidebar.caption("Itt szabályozhatod a dinamikus tördelés finomságát.")

# Dinamikus paraméterek a Soft-Limit logikához
p_val = st.sidebar.slider(
    "Vágási érzékenység (Percentile)", 
    50, 99, 85, 
    help="Alacsonyabb érték = több vágási pont (sűrűbb tördelés)."
)
t_size = st.sidebar.number_input(
    "Cél chunk méret (karakter)", 
    200, 5000, 1000,
    help="Ez a 'Soft-Limit': a rendszer törekszik erre a méretre, de nem vágja el a mondatokat."
)

if uploaded_file:
    # Fájl mentése ideiglenesen
    with open(uploaded_file.name, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    if st.sidebar.button("Indexelés Indítása", use_container_width=True):
        with st.spinner("Szemantikai feldolgozás folyamatban..."):
            ext = uploaded_file.name.split('.')[-1]
            # Átadjuk az új paramétereket a pipeline-nak
            rag.ingest_file(uploaded_file.name, ext, percentile=p_val, target_size=t_size)
            st.sidebar.success(f"Sikeresen indexelve: {uploaded_file.name}")
            st.rerun()

# --- FŐABLAK: FÜLEK ---
tab1, tab2 = st.tabs(["🔍 Intelligens Keresés", "🔬 Dokumentum Struktúra"])

# --- 1. FÜL: KERESÉS ---
with tab1:
    st.subheader("Kérdezz a Tudásbázistól")
    query = st.text_input("Írd be a kérdésed:", placeholder="Pl.: Hogyan működik a dinamikus küszöb?")
    
    if query:
        query_vector = rag._get_embedding([query], is_query=True)[0]
        search_result = rag.qdrant.query_points(
            collection_name=rag.collection_name,
            query=query_vector.tolist(),
            limit=3
        ).points

        if search_result:
            for i, res in enumerate(search_result):
                with st.expander(f"Találat #{i+1} — Relevancia: {res.score:.4f}"):
                    col1, col2 = st.columns([1, 3])
                    with col1:
                        st.info(f"**Forrás:**\n{res.payload.get('source', 'Ismeretlen')}")
                        st.warning(f"**Típus:**\n{res.payload.get('type', 'N/A')}")
                        if 'qa_score' in res.payload:
                            st.metric("QA Minőség", f"{res.payload['qa_score']}/10")
                    with col2:
                        st.write("**Kinyert Tartalom:**")
                        st.markdown(res.payload['text'])
        else:
            st.error("Nincs találat a megadott kifejezésre.")

# --- 2. FÜL: STRUKTÚRA ANALÍZIS ---
with tab2:
    st.subheader("Szemantikai Egységek Elemzése")
    
    try:
        # Lekérjük az összes egyedi forrást
        all_points, _ = rag.qdrant.scroll(collection_name=rag.collection_name, limit=500)
        available_sources = list(set([p.payload['source'] for p in all_points])) if all_points else []
        
        if not available_sources:
            st.info("Még nincsenek adatok az adatbázisban. Tölts fel egy fájlt az oldalsávon!")
        else:
            selected_source = st.selectbox("Válassz ki egy forrást az elemzéshez:", available_sources)
            
            if selected_source:
                # Szűrt lekérdezés
                doc_chunks, _ = rag.qdrant.scroll(
                    collection_name=rag.collection_name,
                    scroll_filter=models.Filter(
                        must=[models.FieldCondition(key="source", match=models.MatchValue(value=selected_source))]
                    ),
                    limit=200
                )
                
                # Statisztikák
                avg_size = int(sum(len(p.payload['text']) for p in doc_chunks) / len(doc_chunks))
                c1, c2, c3 = st.columns(3)
                c1.metric("Egységek száma", len(doc_chunks))
                c2.metric("Átlagos méret", f"{avg_size} karakter")
                c3.metric("Célméret eltérés", f"{avg_size - t_size} kar.")

                # Táblázat összeállítása
                df_data = []
                for i, p in enumerate(doc_chunks):
                    df_data.append({
                        "Sorszám": i+1,
                        "Típus": p.payload.get('type', 'ismeretlen'),
                        "Méret (karakter)": len(p.payload.get('text', '')),
                        "QA Pont": p.payload.get('qa_score', 'N/A'),
                        "Szöveg eleje": p.payload.get('text', '')[:100] + "..."
                    })
                
                st.dataframe(pd.DataFrame(df_data), use_container_width=True)
                
                # Részletes vizuális lista
                st.write("### Részletes tartalom")
                for i, p in enumerate(doc_chunks):
                    with st.expander(f"{i+1}. egység — {p.payload.get('type')} ({len(p.payload['text'])} kar.)"):
                        st.text_area("Szöveg", p.payload.get('text'), height=150, key=f"text_area_{i}")

    except Exception as e:
        st.error(f"Hiba az analízis során: {str(e)}")

# --- LÁBJEGYZET ---
st.divider()
try:
    info = rag.qdrant.get_collection(collection_name=rag.collection_name)
    st.caption(f"Status: {info.points_count} vektor indexelve | Kollekció: {rag.collection_name} | Eszköz: CUDA")
except:
    st.caption("Status: Adatbázis offline vagy üres.")