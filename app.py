from datetime import datetime
import io
import random
import pandas as pd
import requests
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# ---------------------------------------------------------
# CONFIGURACIÓN DE SERVIDORES Y FIREBASE
# ---------------------------------------------------------
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwpYoAthfaViejGHAAThgQkAllbMrSsxfi-AC6vrcrtUtIeG-VtI5knuGPyGlGZhHl7tA/exec"
ADMIN_PASSWORD = "admin123"

CARACTERES_SEGUROS = "BCDFGHJKLMNPQRSTVWXYZ0123456789"

st.set_page_config(
    page_title="Plataforma de Evaluación DTCABA & Hackathon CIREC",
    page_icon="🏆",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# Inicializar Firebase Admin SDK corrigiendo formato de private_key en Secrets
if not firebase_admin._apps:
    try:
        if "firebase" in st.secrets:
            cred_dict = dict(st.secrets["firebase"])
            if "private_key" in cred_dict:
                cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")
            cred = credentials.Certificate(cred_dict)
        else:
            cred = credentials.Certificate("firebase_credentials.json")
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"⚠️ Error al conectar con Firebase: {e}")
        st.stop()

db = firestore.client()

# ---------------------------------------------------------
# ESTILOS CSS CON OCULTAMIENTO DE BARRA SUPERIOR
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Inter', sans-serif; 
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* OCULTAR COMPLETAMENTE LA BARRA SUPERIOR DE STREAMLIT */
    header[data-testid="stHeader"] {
        display: none !important;
    }

    /* AJUSTE DEL ESPACIADO SUPERIOR PARA COMPENSAR LA BARRA OCULTA */
    .block-container {
        padding-top: 1.5rem !important;
    }

    .app-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%) !important;
        padding: 1.5rem 1.25rem; 
        border-radius: 16px; 
        margin-bottom: 1.2rem; 
        text-align: center;
        box-shadow: 0 10px 15px -3px rgba(15, 23, 42, 0.3);
    }
    .app-header h1 { 
        font-family: 'Poppins', sans-serif; 
        font-size: 1.6rem; 
        font-weight: 800; 
        margin: 0; 
        color: #FFFFFF !important; 
    }
    .app-header p { 
        margin: 0.4rem 0 0 0; 
        color: #94A3B8 !important; 
        font-weight: 500;
        font-size: 0.85rem;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: var(--background-secondary, #FFFFFF) !important;
        border-radius: 14px;
        border: 1px solid #CBD5E1 !important;
        padding: 1rem;
        margin-bottom: 0.8rem;
    }

    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%) !important;
        padding: 1rem 1.2rem;
        border-radius: 12px;
        border: 1px solid #334155 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        text-align: center;
        margin: 1.2rem 0;
    }
    div[data-testid="stMetric"] label {
        color: #94A3B8 !important;
        font-weight: 600;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #38BDF8 !important;
        font-weight: 800;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
        color: #FFFFFF !important; 
        border: none; 
        border-radius: 10px; 
        padding: 0.75rem 1.25rem; 
        font-weight: 600; 
        width: 100%;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# FUNCIONES AUXILIARES
# ---------------------------------------------------------
@st.cache_data(ttl=600, show_spinner=False)
def buscar_estudiantes_por_dni(dni):
    try:
        dni_limpio = str(dni).strip().replace(".", "").replace(" ", "")
        if not dni_limpio:
            return []
        payload = {"action": "buscar_dni", "dni": dni_limpio}
        res = requests.post(WEBAPP_URL, json=payload, timeout=20)
        if res.status_code == 200:
            data = res.json()
            if data.get("status") == "success":
                return data.get("coincidencias", [])
    except Exception:
        pass
    return []

def obtener_lista_codigos_fb():
    try:
        docs = db.collection("equipos").stream()
        codigos = [doc.to_dict().get("codigo_unico") for doc in docs if doc.to_dict().get("codigo_unico")]
        return sorted(list(set(codigos)))
    except Exception:
        return []

def aplanar_equipos(equipos_list):
    filas_aplanadas = []
    for eq in equipos_list:
        base = {
            "fecha": eq.get("fecha", ""),
            "codigo_unico": eq.get("codigo_unico", ""),
            "evento": eq.get("evento", ""),
            "materia": eq.get("materia", ""),
            "especialidad": eq.get("especialidad", "")
        }
        integrantes = eq.get("integrantes", [])
        if isinstance(integrantes, list):
            for idx, member in enumerate(integrantes, start=1):
                if isinstance(member, dict):
                    base[f"integrante_{idx}_dni"] = member.get("dni", "")
                    base[f"integrante_{idx}_estudiante"] = member.get("estudiante", "")
                    base[f"integrante_{idx}_escuela"] = member.get("escuela", "")
                    base[f"integrante_{idx}_email"] = member.get("email", "")
        filas_aplanadas.append(base)
    return pd.DataFrame(filas_aplanadas)

def generar_excel_descarga(dict_raw_data):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if dict_raw_data.get("Evaluaciones"):
            df_evals = pd.json_normalize(dict_raw_data["Evaluaciones"])
            df_evals.
