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
            df_evals.to_excel(writer, sheet_name="Evaluaciones", index=False)
        else:
            pd.DataFrame().to_excel(writer, sheet_name="Evaluaciones", index=False)

        if dict_raw_data.get("Equipos"):
            df_equipos = aplanar_equipos(dict_raw_data["Equipos"])
            df_equipos.to_excel(writer, sheet_name="Equipos", index=False)
        else:
            pd.DataFrame().to_excel(writer, sheet_name="Equipos", index=False)

        if dict_raw_data.get("Presentes_Acreditados"):
            df_presentes = pd.DataFrame(dict_raw_data["Presentes_Acreditados"])
            df_presentes.to_excel(writer, sheet_name="Presentes_Acreditados", index=False)
        else:
            pd.DataFrame().to_excel(writer, sheet_name="Presentes_Acreditados", index=False)

    return output.getvalue()

# ---------------------------------------------------------
# NAVEGACIÓN PRINCIPAL EN PANTALLA
# ---------------------------------------------------------
opcion_dtcaba = "📐 Desafíos Técnicos DTCABA"
opcion_hackathon = "🏆 Hackathon 2026 (CIREC)"

evento_seleccionado = st.radio(
    "Selección de Evento",
    [opcion_dtcaba, opcion_hackathon],
    horizontal=True
)

# ---------------------------------------------------------
# EVENTO 1: DESAFÍOS TÉCNICOS DTCABA
# ---------------------------------------------------------
if evento_seleccionado == opcion_dtcaba:
    st.markdown(
        """
        <div class="app-header">
            <h1>📐 Desafíos Técnicos DTCABA ⚙️</h1>
            <p>Plataforma de Evaluación y Gestión de Equipos</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_eval, tab_cod, tab_acred, tab_admin = st.tabs([
        "📝 Evaluar", 
        "🎲 Códigos", 
        "📌 Acreditación", 
        "⚙️ Admin"
    ])

    with tab_eval:
        st.header("Carga de Evaluación DTCABA")
        lista_codigos = obtener_lista_codigos_fb()

        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                dni_evaluador = st.text_input(
                    "DNI del Evaluador", placeholder="Ingresa tu DNI", key="eval_dni"
                ).strip().replace(".", "")

            with col2:
                if lista_codigos:
                    opciones_desplegable = (
                        ["-- Buscar o seleccionar código --"]
                        + lista_codigos
                        + ["✏️ Tipear código manualmente"]
                    )
                    seleccion = st.selectbox(
                        "Código Único del Examen",
                        options=opciones_desplegable,
                        key="eval_codigo_select",
                    )
                    if seleccion == "✏️ Tipear código manualmente":
                        codigo_unico = st.text_input(
                            "Escribe el Código Único", placeholder="Ej: X8K198", key="eval_codigo_manual"
                        ).strip().upper()
                    elif seleccion != "-- Buscar o seleccionar código --":
                        codigo_unico = seleccion
                    else:
                        codigo_unico = ""
                else:
                    codigo_unico = st.text_input(
                        "Código Único del Examen", placeholder="Ej: X8K198", key="eval_codigo_directo"
                    ).strip().upper()

            materia = st.selectbox(
                "Materia",
                [
                    "Lengua",
                    "Matemática",
                    "Tecnología de la Representación Nivel 1",
                    "Tecnología de la Representación Nivel 2",
                ],
                key="eval_materia",
            )

        if not codigo_unico:
            st.info("💡 Por favor, selecciona o ingresa el Código Único del Examen.")
        else:
            st.subheader(f"📋 Rúbrica de Evaluación: {materia}")

            if materia == "Lengua":
                map_len1 = {
                    4: "4 - Avanzado: Conserva e integra el sentido central del texto técnico.",
                    3: "3 - Satisfactorio: Conserva ideas principales con pequeñas simplificaciones.",
                    2: "2 - En desarrollo: Recupera solo parte de la información relevante.",
                    1: "1 - Inicial: Pierde o modifica el sentido del texto fuente.",
                }
                map_len2 = {
                    4: "4 - Avanzado: El texto se transforma completamente en un relato literario.",
                    3: "3 - Satisfactorio: Predomina el relato aunque mantiene rasgos expositivos.",
                    2: "2 - En desarrollo: Alterna explicación y narración sin integrarlas completamente.",
                    1: "1 - Inicial: Predomina el texto expositivo o no logra la transformación.",
                }
                map_len3 = {
                    4: "4 - Avanzado: Construye una voz en primera persona consistente y verosímil.",
                    3: "3 - Satisfactorio: La voz se sostiene con algunas inconsistencias.",
                    2: "2 - En desarrollo: La voz aparece de manera parcial o irregular.",
                    1: "1 - Inicial: No logra construir una voz narrativa.",
                }
                map_len4 = {
                    4: "4 - Avanzado: Utiliza el lenguaje técnico para construir experiencias.",
                    3: "3 - Satisfactorio: Integra el vocabulario técnico de manera pertinente.",
                    2: "2 - En desarrollo: El lenguaje técnico aparece de forma aislada.",
                    1: "1 - Inicial: No incorpora o utiliza incorrectamente el lenguaje técnico.",
                }
                map_len5 = {
                    4: "4 - Avanzado: Integra descripciones, metáforas o comparaciones enriquecedoras.",
                    3: "3 - Satisfactorio: Utiliza algunos recursos expresivos adecuados.",
                    2: "2 - En desarrollo: Utiliza un recurso expresivo de forma adecuada.",
                    1: "1 - Inicial: No utiliza recursos literarios significativos.",
                }
                map_len6 = {
                    4: "4 - Avanzado: Presenta una secuencia clara, coherente y cohesiva.",
                    3: "3 - Satisfactorio: Relato comprensible con pequeñas dificultades lógicas.",
                    2: "2 - En desarrollo: La organización presenta reiteraciones o saltos.",
                    1: "1 - Inicial: La organización dificulta la comprensión.",
                }
                map_len7 = {
                    4: "4 - Avanzado: Emplea correctamente ortografía, puntuación y sintaxis.",
                    3: "3 - Satisfactorio: Presenta errores que no dificultan la comprensión.",
                    2: "2 - En desarrollo: Errores que dificultan parcialmente la comprensión.",
                    1: "1 - Inicial: Los errores afectan significativamente la comprensión.",
                }

                st.markdown("### BLOQUE A: Comprender para transformar (40%)")
                with st.container(border=True):
                    st.markdown("#### 1. Apropiación del texto fuente (20%)")
                    c1 = st.radio("Nivel:", [4, 3, 2, 1], format_func=lambda x: map_len1[x], key="len_c1")
                    obs1 = st.text_area("Observaciones / Justificación:", key="obs_c1", height=70)

                with st.container(border=True):
                    st.markdown("#### 2. Transformación del género (20%)")
                    c2 = st.radio("Nivel:", [4, 3, 2, 1], format_func=lambda x: map_len2[x], key="len_c2")
                    obs2 = st.text_area("Observaciones / Justificación:", key="obs_c2", height=70)

                st.markdown("### BLOQUE B: Escribir para construir sentido (40%)")
                with st.container(border=True):
                    st.markdown("#### 3. Voz narrativa")
                    c3 = st.radio("Nivel:", [4, 3, 2, 1], format_func=lambda x: map_len3[x], key="len_c3")
                    obs3 = st.text_area("Observaciones / Justificación:", key="obs_c3", height=70)

                with st.container(border=True):
                    st.markdown("#### 4. Resignificación del lenguaje técnico")
                    c4 = st.radio("Nivel:", [4, 3, 2, 1], format_func=lambda x: map_len4[x], key="len_c4")
                    obs4 = st
