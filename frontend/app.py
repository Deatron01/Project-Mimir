import streamlit as st
import requests
import os
import re
import json
import time
from datetime import datetime
from auth import init_db, register_user, login_user, verify_email

# --- KONFIGURÁCIÓ ÉS STÍLUS (60/30/10 Sötétkék téma) ---
st.set_page_config(
    page_title="Mimir AI | Professzionális Vizsgagenerátor",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Egyedi CSS a 60/30/10 arányhoz és a sötétkék dizájnhoz
st.markdown("""
    <style>
    /* Fő háttér (60%) */
    .stApp {
        background-color: #0a192f;
        color: #ccd6f6;
    }
    
    /* Oldalsáv (30% árnyalat) */
    [data-testid="stSidebar"] {
        background-color: #112240;
        border-right: 1px solid #233554;
    }
    
    /* Kártyák és konténerek */
    .stCard {
        background-color: #112240;
        padding: 2rem;
        border-radius: 10px;
        border: 1px solid #233554;
        margin-bottom: 1rem;
    }
    
    /* Gombok (10% kiemelés) */
    .stButton > button {
        background-color: transparent;
        color: #64ffda;
        border: 1px solid #64ffda;
        padding: 0.5rem 1.5rem;
        border-radius: 4px;
        transition: all 0.3s;
    }
    .stButton > button:hover {
        background-color: rgba(100, 255, 218, 0.1);
        border-color: #64ffda;
        color: #64ffda;
    }
    
    /* Elsődleges gomb */
    div.stButton > button[kind="primary"] {
        background-color: rgba(100, 255, 218, 0.1);
        font-weight: bold;
    }
    
    /* Input mezők */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background-color: #112240;
        color: #64ffda;
        border: 1px solid #233554;
    }
    
    /* Footer */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: #0a192f;
        color: #8892b0;
        text-align: center;
        padding: 10px;
        font-size: 11px;
        border-top: 1px solid #233554;
        z-index: 999;
    }
    
    /* Cookie Popup */
    .cookie-popup {
        position: fixed;
        bottom: 60px;
        right: 20px;
        width: 320px;
        background-color: #112240;
        border: 1px solid #64ffda;
        padding: 20px;
        border-radius: 8px;
        z-index: 1000;
        box-shadow: 0 10px 30px -15px rgba(2,12,27,0.7);
    }
    </style>
    """, unsafe_allow_html=True)

# --- API VÉGPONTOK ---
WELLSPRING_URL = os.getenv("WELLSPRING_URL", "http://localhost:8001/api/v1/extract")
RUNECARVER_URL = os.getenv("RUNECARVER_URL", "http://localhost:8002/api/v1/chunk")
BIFROST_INGEST_URL = os.getenv("BIFROST_INGEST_URL", "http://localhost:8003/api/v1/ingest")
BIFROST_GENERATE_URL = os.getenv("BIFROST_GENERATE_URL", "http://localhost:8003/api/v1/generate")
SKALD_URL = os.getenv("SKALD_URL", "http://localhost:8005/api/v1/export")

# Inicializálás
init_db()

# --- MUNKAMENET KEZELÉS ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'user_email' not in st.session_state:
    st.session_state['user_email'] = ""
if 'cookie_accepted' not in st.session_state:
    st.session_state['cookie_accepted'] = False
if 'saved_tests' not in st.session_state:
    st.session_state['saved_tests'] = []

# --- COOKIE POPUP ---
if not st.session_state['cookie_accepted']:
    st.markdown("""
        <div class="cookie-popup">
            <h4 style="color: #64ffda; margin-top: 0;">🍪 Sütik és Adatvédelem</h4>
            <p style="font-size: 13px; color: #8892b0;">
                Az oldal sütiket használ a munkamenet és a generált tesztek mentéséhez. 
                Az elfogadással hozzájárul az adatok helyi tárolásához.
            </p>
        </div>
    """, unsafe_allow_html=True)
    if st.button("Elfogadom és Bezárom", key="accept_cookies"):
        st.session_state['cookie_accepted'] = True
        st.rerun()

# --- E-MAIL MEGERŐSÍTÉS ---
query_params = st.query_params
if "token" in query_params:
    token = query_params["token"]
    if verify_email(token):
        st.success("✅ E-mail cím sikeresen megerősítve!")
    else:
        st.error("❌ Érvénytelen link!")
    st.query_params.clear()

def logout():
    st.session_state['logged_in'] = False
    st.session_state['user_email'] = ""
    st.rerun()

# --- 1. AUTH KÉPERNYŐ ---
if not st.session_state['logged_in']:
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("<br><br><h1 style='text-align: center; color: #64ffda;'>🧠 MIMIR AI</h1>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["✨ Belépés", "📝 Regisztráció"])
        
        with tab1:
            with st.form("login_form"):
                log_email = st.text_input("E-mail")
                log_pwd = st.text_input("Jelszó", type="password")
                if st.form_submit_button("Bejelentkezés", type="primary", use_container_width=True):
                    success, msg = login_user(log_email, log_pwd)
                    if success:
                        st.session_state['logged_in'] = True
                        st.session_state['user_email'] = log_email
                        st.rerun()
                    else:
                        st.error(msg)
                        
        with tab2:
            with st.form("register_form"):
                reg_email = st.text_input("E-mail")
                reg_pwd = st.text_input("Jelszó", type="password")
                reg_pwd_c = st.text_input("Jelszó újra", type="password")
                if st.form_submit_button("Regisztráció", type="primary", use_container_width=True):
                    if reg_pwd == reg_pwd_c:
                        success, msg = register_user(reg_email, reg_pwd)
                        st.success(msg) if success else st.error(msg)
                    else:
                        st.error("A jelszavak nem egyeznek!")
    
    st.markdown('<div class="footer">Mimir AI © 2024 | Az oldal használatával elfogadja az adatkezelési feltételeket.</div>', unsafe_allow_html=True)
    st.stop()

# --- 2. ALKALMAZÁS ---
with st.sidebar:
    st.markdown("<h2 style='color: #64ffda;'>Mimir AI</h2>", unsafe_allow_html=True)
    st.info(f"👤 {st.session_state['user_email']}")
    menu = st.radio("Navigáció", ["🚀 Generálás", "📚 Tesztek", "⚖️ Jogi Nyilatkozat"])
    st.markdown("---")
    if st.button("🚪 Kijelentkezés", use_container_width=True):
        logout()

if menu == "🚀 Generálás":
    st.markdown("<h2 style='color: #64ffda;'>Új vizsga generálása</h2>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        uploaded_file = st.file_uploader("Forrásdokumentum (PDF/TXT)", type=["pdf", "txt"])
    with c2:
        query = st.text_input("Vizsga témája", placeholder="Pl. Sejtbiológia alapjai")
        limit = st.slider("Részletesség", 1, 5, 2)

    if st.button("🚀 Generálás indítása", type="primary", use_container_width=True):
        if uploaded_file and query:
            with st.status("Feldolgozás folyamatban...", expanded=True) as status:
                try:
                    # 1. Wellspring
                    st.write("🌊 Szöveg kinyerése...")
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/plain")}
                    res_well = requests.post(WELLSPRING_URL, files=files)
                    res_well.raise_for_status()
                    text = res_well.json().get("content", "")
                    
                    # 2. RuneCarver
                    st.write("ᛋ Szövegrészek elemzése...")
                    res_rune = requests.post(RUNECARVER_URL, json={
                        "filename": uploaded_file.name,
                        "extension": uploaded_file.name.split('.')[-1],
                        "content": text
                    })
                    res_rune.raise_for_status()
                    chunks = res_rune.json().get("chunks", [])
                    
                    # 3. Bifrost Ingest
                    st.write("🌈 Vektorizálás...")
                    requests.post(BIFROST_INGEST_URL, json={"chunks": chunks}).raise_for_status()
                    
                    # 4. Bifrost Generate
                    st.write("🧠 AI Kérdésgenerálás...")
                    res_gen = requests.post(BIFROST_GENERATE_URL, json={"query": query, "limit": limit})
                    res_gen.raise_for_status()
                    llm_data = res_gen.json().get("data", {})
                    
                    # 5. Skald (PDF)
                    st.write("📜 PDF összeállítása...")
                    res_skald = requests.post(SKALD_URL, json=llm_data)
                    res_skald.raise_for_status()
                    
                    # Mentés a "Tesztek" közé
                    if st.session_state['cookie_accepted']:
                        st.session_state['saved_tests'].insert(0, {
                            "id": int(time.time()),
                            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "title": query,
                            "file": uploaded_file.name,
                            "data": llm_data,
                            "pdf": res_skald.content
                        })
                    
                    status.update(label="✅ Sikeres generálás!", state="complete")
                    st.success("A vizsga elkészült és mentésre került a 'Tesztek' menüpont alá.")
                except Exception as e:
                    status.update(label="❌ Hiba történt", state="error")
                    st.error(f"Rendszerhiba: {str(e)}")
        else:
            st.warning("Tölts fel fájlt és adj meg témát!")

elif menu == "📚 Tesztek":
    st.markdown("<h2 style='color: #64ffda;'>Mentett vizsgák</h2>", unsafe_allow_html=True)
    if not st.session_state['saved_tests']:
        st.info("Még nincsenek mentett tesztjeid.")
    else:
        for t in st.session_state['saved_tests']:
            with st.expander(f"📅 {t['date']} - {t['title']}"):
                st.write(f"**Forrás:** {t['file']}")
                st.json(t['data'])
                st.download_button("📥 PDF Letöltése", data=t['pdf'], file_name=f"{t['title']}.pdf", key=f"dl_{t['id']}")

elif menu == "⚖️ Jogi Nyilatkozat":
    st.markdown("<h2 style='color: #64ffda;'>Jogi és Adatvédelmi Nyilatkozat</h2>", unsafe_allow_html=True)
    st.write("""
    Az oldal használatával Ön elfogadja az alábbiakat:
    - Az Ön által feltöltött fájlokat és megadott tartalmakat a rendszer kizárólag a vizsgagenerálás céljából dolgozza fel.
    - A generált tartalmak az Ön tulajdonát képezik, de a rendszer nem vállal felelősséget azok szakmai helyességéért.
    - A sütik (cookie-k) elfogadásával hozzájárul, hogy a böngésző munkamenet ideje alatt tároljuk a generált teszteket.
    - Az adatok feldolgozása helyi vagy zárt felhő alapú környezetben történik a maximális biztonság érdekében.
    """)

# --- FIX LÁBLÉC ---
st.markdown("""
    <div class="footer">
        Mimir AI © 2024 | Az oldal használatával elfogadja, hogy kezeljük az Ön által megadott fájlokat és tartalmakat. 
        Minden jog fenntartva.
    </div>
""", unsafe_allow_html=True)