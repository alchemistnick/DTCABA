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
    page_title="Plataforma de Evaluación DTCABA & Hackathon",
    page_icon="🏆",
    layout="centered",
    initial_sidebar_state="expanded",
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

hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ---------------------------------------------------------
# ESTILOS CSS
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Inter', sans-serif; 
    }

    section[data-testid="stSidebar"] { 
        background-color: #0F172A !important; 
        padding-top: 1rem;
    }
    section[data-testid="stSidebar"] * { 
        color: #F8FAFC !important; 
    }

    section[data-testid="stSidebar"] div[role="radiogroup"] {
        gap: 0.3rem !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        background-color: transparent !important;
        border: none !important;
        padding: 0.4rem 0.6rem !important;
        border-radius: 8px !important;
        transition: background-color 0.2s ease;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background-color: rgba(255, 255, 255, 0.08) !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label * {
        color: #F8FAFC !important;
        font-size: 0.95rem !important;
        font-weight: 500 !important;
    }

    .app-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%) !important;
        padding: 1.8rem 2rem; 
        border-radius: 16px; 
        margin-bottom: 2rem; 
        text-align: center;
        box-shadow: 0 10px 15px -3px rgba(15, 23, 42, 0.3);
    }
    .app-header h1 { 
        font-family: 'Poppins', sans-serif; 
        font-size: 2.2rem; 
        font-weight: 800; 
        margin: 0; 
        color: #FFFFFF !important; 
    }
    .app-header p { 
        margin: 0.4rem 0 0 0; 
        color: #94A3B8 !important; 
        font-weight: 500;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: var(--background-secondary, #FFFFFF) !important;
        border-radius: 14px;
        border: 1px solid #CBD5E1 !important;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }

    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%) !important;
        padding: 1.2rem 1.8rem;
        border-radius: 12px;
        border: 1px solid #334155 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
        text-align: center;
        margin: 1.5rem 0;
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
        padding: 0.75rem 1.5rem; 
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
# NAVEGACIÓN PRINCIPAL
# ---------------------------------------------------------
st.sidebar.markdown("### ⚙️ Evento")
evento_seleccionado = st.sidebar.radio(
    "Selección de Evento",
    ["📐 Desafíos Técnicos DTCABA", "🏆 Hackathon 2026"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🧭 Menú")

if evento_seleccionado == "📐 Desafíos Técnicos DTCABA":
    opcion = st.sidebar.radio(
        "Navegación DTCABA",
        ["Cargar Evaluación DTCABA", "Generar Códigos de Equipos", "📌 Acreditación de Presentes", "Panel de Administración y Reportes"],
        label_visibility="collapsed",
    )
else:
    opcion = st.sidebar.radio(
        "Navegación Hackathon",
        ["Cargar Evaluación Hackathon", "📌 Acreditación Hackathon", "Panel de Administración y Reportes"],
        label_visibility="collapsed",
    )

# ---------------------------------------------------------
# EVENTO 1: DESAFÍOS TÉCNICOS DTCABA
# ---------------------------------------------------------
if evento_seleccionado == "📐 Desafíos Técnicos DTCABA":
    st.markdown(
        """
        <div class="app-header">
            <h1>📐 Desafíos Técnicos DTCABA ⚙️</h1>
            <p>Plataforma de Evaluación y Gestión de Equipos</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if opcion == "Cargar Evaluación DTCABA":
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
            st.stop()

        st.subheader(f"📋 Rúbrica de Evaluación: {materia}")

        # ---------------------------------------------------------
        # RÚBRICA DE LENGUA
        # ---------------------------------------------------------
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
                3: "3 - Satisfactorio: La voz se sostiene con algunas inconsistencias (ruptura de registro, de focalización, contradicción en la actitud).",
                2: "2 - En desarrollo: La voz aparece de manera parcial o irregular (no presenta uniformidad en la voz en todos los párrafos).",
                1: "1 - Inicial: No logra construir una voz narrativa.",
            }
            map_len4 = {
                4: "4 - Avanzado: Utiliza el lenguaje técnico para construir experiencias y emociones o vínculos.",
                3: "3 - Satisfactorio: Integra el vocabulario técnico de manera pertinente.",
                2: "2 - En desarrollo: El lenguaje técnico aparece de forma aislada o forzada.",
                1: "1 - Inicial: No incorpora o utiliza incorrectamente el lenguaje técnico.",
            }
            map_len5 = {
                4: "4 - Avanzado: Integra descripciones, metáforas o comparaciones que enriquecen el relato.",
                3: "3 - Satisfactorio: Utiliza algunos recursos expresivos adecuados.",
                2: "2 - En desarrollo: Utiliza un recurso expresivo (metáfora o descripción) de forma adecuada.",
                1: "1 - Inicial: No utiliza recursos literarios significativos.",
            }
            map_len6 = {
                4: "4 - Avanzado: Presenta una secuencia clara, coherente y cohesiva.",
                3: "3 - Satisfactorio: El relato es comprensible con pequeñas dificultades que implican ambigüedades o desorden en la claridad lógica.",
                2: "2 - En desarrollo: La organización presenta reiteraciones o saltos.",
                1: "1 - Inicial: La organización dificulta la comprensión.",
            }
            map_len7 = {
                4: "4 - Avanzado: Emplea correctamente ortografía, puntuación y síntaxis.",
                3: "3 - Satisfactorio: Presenta errores que no dificultan la comprensión.",
                2: "2 - En desarrollo: Presenta errores que dificultan parcialmente la comprensión.",
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
                obs4 = st.text_area("Observaciones / Justificación:", key="obs_c4", height=70)

            with st.container(border=True):
                st.markdown("#### 5. Construcción literaria")
                c5 = st.radio("Nivel:", [4, 3, 2, 1], format_func=lambda x: map_len5[x], key="len_c5")
                obs5 = st.text_area("Observaciones / Justificación:", key="obs_c5", height=70)

            st.markdown("### BLOQUE C: Comunicar con claridad (20%)")
            with st.container(border=True):
                st.markdown("#### 6. Organización del relato (10%)")
                c6 = st.radio("Nivel:", [4, 3, 2, 1], format_func=lambda x: map_len6[x], key="len_c6")
                obs6 = st.text_area("Observaciones / Justificación:", key="obs_c6", height=70)

            with st.container(border=True):
                st.markdown("#### 7. Normativa (10%)")
                c7 = st.radio("Nivel:", [4, 3, 2, 1], format_func=lambda x: map_len7[x], key="len_c7")
                obs7 = st.text_area("Observaciones / Justificación:", key="obs_c7", height=70)

            promedio_base4 = (
                (c1 * 0.20)
                + (c2 * 0.20)
                + (c3 * 0.1333)
                + (c4 * 0.1333)
                + (c5 * 0.1334)
                + (c6 * 0.10)
                + (c7 * 0.10)
            )
            puntaje_100 = round((promedio_base4 / 4) * 100, 2)

            eval_respuestas = {
                "c1_apropiacion_texto_pts": c1, "c1_apropiacion_texto_desc": map_len1[c1], "c1_obs": obs1,
                "c2_transformacion_genero_pts": c2, "c2_transformacion_genero_desc": map_len2[c2], "c2_obs": obs2,
                "c3_voz_narrativa_pts": c3, "c3_voz_narrativa_desc": map_len3[c3], "c3_obs": obs3,
                "c4_resignificacion_tecnica_pts": c4, "c4_resignificacion_tecnica_desc": map_len4[c4], "c4_obs": obs4,
                "c5_construccion_literaria_pts": c5, "c5_construccion_literaria_desc": map_len5[c5], "c5_obs": obs5,
                "c6_organizacion_relato_pts": c6, "c6_organizacion_relato_desc": map_len6[c6], "c6_obs": obs6,
                "c7_normativa_pts": c7, "c7_normativa_desc": map_len7[c7], "c7_obs": obs7,
            }

        # ---------------------------------------------------------
        # RÚBRICA DE MATEMÁTICA
        # ---------------------------------------------------------
        elif materia == "Matemática":
            map_mat1 = {
                5: "5 - Destacado: Figura original y de alta complejidad en la representación.",
                4: "4 - Avanzado: Figura tridimensional bien construida, muestra originalidad.",
                3: "3 - Satisfactorio: La figura es adecuada y realizada de manera correcta.",
                2: "2 - Básico: La figura es no presenta complejidad.",
                1: "1 - Inicial: La figura no es original y presenta errores de representación.",
            }
            map_mat2 = {
                5: "5 - Destacado: Problema original, explícito la intervención de la figura y de integración de disciplinas.",
                4: "4 - Avanzado: Situación problemática planteada es explícita en la intervención de la figura y de integración de disciplinas.",
                3: "3 - Satisfactorio: El problema es correcto pero no se evidencia la figura construida.",
                2: "2 - Básico: El problema presenta inconsistencias desde el punto de vista matemático.",
                1: "1 - Inicial: No logra contextualizar la situación problemática.",
            }
            map_mat3 = {
                5: "5 - Destacado: Procedimiento es completo, utiliza datos y justifica cada paso.",
                4: "4 - Avanzado: Aplica el procedimiento correcto y justifica cada paso.",
                3: "3 - Satisfactorio: El procedimient es correcto pero con justificación parcial.",
                2: "2 - Básico: La procedimiento es correcto no presenta justificación",
                1: "1 - Inicial: No presenta procedimiento ni justificación.",
            }
            map_mat4 = {
                5: "5 - Destacado: Utiliza términos, símbolos y expresiones matemáticas de forma precisa y rigurosa.",
                4: "4 - Avanzado: Utiliza términos, símbolos y expresiones matemáticas de forma correcta en su mayoría.",
                3: "3 - Satisfactorio: Muestra un uso impreciso o escazo de términos, símbolos de expresiones matemáticas",
                2: "2 - Básico: Explica el desarrollo de forma coloquial o ambigua.",
                1: "1 - Inicial: La comunicación del desarrollo es imprecisa",
            }

            st.markdown("### 📐 Criterios de Evaluación: Matemática")
            with st.container(border=True):
                st.markdown("#### 1. Construcción y Representación de la Figura Tridimensional (20%)")
                c1 = st.radio("Nivel:", [5, 4, 3, 2, 1], format_func=lambda x: map_mat1[x], key="mat_c1")
                obs1 = st.text_area("Observaciones / Justificación:", key="obs_mat1", height=70)

            with st.container(border=True):
                st.markdown("#### 2. Diseño del Problema Matemático e Interdisciplinariedad (30%)")
                c2 = st.radio("Nivel:", [5, 4, 3, 2, 1], format_func=lambda x: map_mat2[x], key="mat_c2")
                obs2 = st.text_area("Observaciones / Justificación:", key="obs_mat2", height=70)

            with st.container(border=True):
                st.markdown("#### 3. Resolución y Justificación del Problema (30%)")
                c3 = st.radio("Nivel:", [5, 4, 3, 2, 1], format_func=lambda x: map_mat3[x], key="mat_c3")
                obs3 = st.text_area("Observaciones / Justificación:", key="obs_mat3", height=70)

            with st.container(border=True):
                st.markdown("#### 4. Presentación y Comunicación (20%)")
                c4 = st.radio("Nivel:", [5, 4, 3, 2, 1], format_func=lambda x: map_mat4[x], key="mat_c4")
                obs4 = st.text_area("Observaciones / Justificación:", key="obs_mat4", height=70)

            promedio_base5 = (c1 * 0.20) + (c2 * 0.30) + (c3 * 0.30) + (c4 * 0.20)
            puntaje_100 = round((promedio_base5 / 5) * 100, 2)

            eval_respuestas = {
                "c1_construccion_figura_pts": c1, "c1_construccion_figura_desc": map_mat1[c1], "c1_obs": obs1,
                "c2_diseno_problema_pts": c2, "c2_diseno_problema_desc": map_mat2[c2], "c2_obs": obs2,
                "c3_resolucion_justificacion_pts": c3, "c3_resolucion_justificacion_desc": map_mat3[c3], "c3_obs": obs3,
                "c4_comunicacion_matematica_pts": c4, "c4_comunicacion_matematica_desc": map_mat4[c4], "c4_obs": obs4,
            }

        # ---------------------------------------------------------
        # RÚBRICAS DE TECNOLOGÍA DE LA REPRESENTACIÓN
        # ---------------------------------------------------------
        else:
            st.markdown(f"### ⚙️ Criterios de Evaluación: {materia}")

            map_tdr_gen = {
                4: "4 - Avanzado (Excelente aplicación)",
                3: "3 - Satisfactorio (Correcta aplicación con mínimos detalles)",
                2: "2 - En desarrollo (Aplicación parcial o incompleta)",
                1: "1 - Inicial (Dificultades significativas)",
            }

            if "Nivel 1" in materia:
                lbl1 = "1. Normalización Básica (35%)"
                lbl2 = "2. Proyección y Visualización Ortogonal (35%)"
                lbl3 = "3. Prolijidad y Calidad Gráfica (30%)"
            else:
                lbl1 = "1. Modelado y Vistas Complejas (35%)"
                lbl2 = "2. Aplicación Avanzada de Normas (35%)"
                lbl3 = "3. Interpretación y Resolución de Conjuntos (30%)"

            with st.container(border=True):
                st.markdown(f"#### {lbl1}")
                c1 = st.radio("Nivel:", [4, 3, 2, 1], format_func=lambda x: map_tdr_gen[x], key="tdr_c1")
                obs1 = st.text_area("Observaciones / Justificación:", key="obs_tdr1", height=70)

            with st.container(border=True):
                st.markdown(f"#### {lbl2}")
                c2 = st.radio("Nivel:", [4, 3, 2, 1], format_func=lambda x: map_tdr_gen[x], key="tdr_c2")
                obs2 = st.text_area("Observaciones / Justificación:", key="obs_tdr2", height=70)

            with st.container(border=True):
                st.markdown(f"#### {lbl3}")
                c3 = st.radio("Nivel:", [4, 3, 2, 1], format_func=lambda x: map_tdr_gen[x], key="tdr_c3")
                obs3 = st.text_area("Observaciones / Justificación:", key="obs_tdr3", height=70)

            promedio_base4 = (c1 * 0.35) + (c2 * 0.35) + (c3 * 0.30)
            puntaje_100 = round((promedio_base4 / 4) * 100, 2)

            eval_respuestas = {
                "c1_criterio1_pts": c1, "c1_criterio1_desc": f"{lbl1} - {map_tdr_gen[c1]}", "c1_obs": obs1,
                "c2_criterio2_pts": c2, "c2_criterio2_desc": f"{lbl2} - {map_tdr_gen[c2]}", "c2_obs": obs2,
                "c3_criterio3_pts": c3, "c3_criterio3_desc": f"{lbl3} - {map_tdr_gen[c3]}", "c3_obs": obs3,
            }

        st.metric(label="Puntaje Total Ponderado (sobre 100)", value=f"{puntaje_100} / 100 pts")

        if st.button("💾 Guardar Evaluación", type="primary"):
            if not dni_evaluador or not codigo_unico:
                st.warning("⚠️ Debes ingresar el DNI del evaluador y el Código Único.")
            else:
                doc_eval = {
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "codigo_unico": codigo_unico,
                    "materia": materia,
                    "evento": "DTCABA",
                    "evaluador_id": dni_evaluador,
                    "evaluador_nombre": f"Evaluador DNI {dni_evaluador}",
                    "promedio": puntaje_100,
                    "respuestas": eval_respuestas,
                }
                db.collection("evaluaciones").add(doc_eval)
                st.session_state["exito_msj"] = f"✅ ¡Evaluación del código {codigo_unico} guardada con éxito en Firebase!"
                st.rerun()

        if "exito_msj" in st.session_state:
            st.success(st.session_state["exito_msj"])
            del st.session_state["exito_msj"]

    elif opcion == "Generar Códigos de Equipos":
        st.header("Generador de Códigos para Equipos / Duplas")
        clave = st.text_input("Contraseña de Acceso", type="password")

        if clave == ADMIN_PASSWORD:
            st.success("🔓 Acceso habilitado.")
            cant_integrantes = st.number_input("Cantidad de Integrantes del Equipo", min_value=1, max_value=10, value=2)
            prefijo = st.selectbox("Materia / Categoría", ["MAT", "LEN", "TDR1", "TDR2", "HACKATHON"])

            datos_integrantes = []
            especialidad_detectada = "General"

            for idx in range(1, cant_integrantes + 1):
                st.subheader(f"👤 Integrante {idx}")
                dni_input = st.text_input(f"DNI Integrante {idx}", key=f"dni_{idx}_input").strip().replace(".", "")

                if dni_input:
                    coincidencias = buscar_estudiantes_por_dni(dni_input)
                    if len(coincidencias) > 1:
                        st.info(f"🔍 Se encontraron {len(coincidencias)} inscripciones para este DNI.")
                        opciones_insc = [f"{c.get('inscripcion', 'Sin Desafío')} - {c.get('escuela', '')}" for c in coincidencias]
                        idx_sel = st.selectbox(f"Seleccionar inscripción para Integrante {idx}", range(len(opciones_insc)), format_func=lambda x: opciones_insc[x], key=f"sel_insc_{idx}")
                        c = coincidencias[idx_sel]
                    elif len(coincidencias) == 1:
                        c = coincidencias[0]
                        st.success(f"✅ Encontrado en padrón: {c.get('nombre','')}")
                    else:
                        c = {}

                    if c:
                        if c.get("especialidad") and c.get("especialidad") != "N/A":
                            especialidad_detectada = c.get("especialidad")

                        st.session_state[f"nom_{idx}"] = c.get("nombre", "")
                        st.session_state[f"esc_{idx}"] = c.get("escuela", "")
                        st.session_state[f"mail_{idx}"] = c.get("email", "")

                nom_i = st.text_input(f"Nombre Integrante {idx}", key=f"nom_{idx}")
                esc_i = st.text_input(f"Escuela Integrante {idx}", key=f"esc_{idx}")
                mail_i = st.text_input(f"Email Integrante {idx}", key=f"mail_{idx}")

                datos_integrantes.append({
                    "posicion": idx,
                    "dni": dni_input,
                    "estudiante": nom_i,
                    "escuela": esc_i,
                    "email": mail_i
                })

            esp_final = st.text_input("Especialidad del Equipo (Obtenida del Padrón)", value=especialidad_detectada, key="esp_equipo_padron")

            if st.button("🎲 Generar Código de Equipo", type="primary"):
                tres_aleatorios = "".join(random.choices(CARACTERES_SEGUROS, k=3))
                primer_dni = datos_integrantes[0]["dni"] if datos_integrantes else "000"
                ultimos_tres = primer_dni[-3:] if len(primer_dni) >= 3 else primer_dni.zfill(3)
                codigo_generado = f"{tres_aleatorios}{ultimos_tres}"

                doc_equipo = {
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "codigo_unico": codigo_generado,
                    "materia": prefijo,
                    "especialidad": esp_final,
                    "evento": "DTCABA",
                    "integrantes": datos_integrantes
                }
                db.collection("equipos").add(doc_equipo)
                st.success(f"✅ Código Único Generado: **{codigo_generado}**")
                st.code(codigo_generado, language="text")

    elif opcion == "📌 Acreditación de Presentes":
        st.header("📌 Acreditación de Presentes (DTCABA)")
        st.markdown("Busca al estudiante por DNI en el padrón para verificar e ingresar o modificar sus datos antes de confirmar el presente.")

        dni_acreditar = st.text_input("Ingresar DNI del Estudiante a Acreditar", placeholder="Ej: 39098198", key="acred_dni_dtcaba").strip().replace(".", "")

        if dni_acreditar:
            coincidencias = buscar_estudiantes_por_dni(dni_acreditar)

            if coincidencias:
                st.success(f"✅ Estudiante Encontrado en Padrón ({len(coincidencias)} inscripción/es detectada/s)")
                
                idx_seleccionado = 0
                if len(coincidencias) > 1:
                    opciones_acred = [f"Inscripción #{i+1}: {c.get('inscripcion', 'Sin datos')} ({c.get('escuela', '')})" for i, c in enumerate(coincidencias)]
                    idx_seleccionado = st.selectbox("Seleccionar la inscripción a acreditar:", range(len(opciones_acred)), format_func=lambda x: opciones_acred[x], key="sel_acred_multi")

                estudiante = coincidencias[idx_seleccionado]

                with st.container(border=True):
                    st.markdown(f"### ✏️ Editar / Validar Registro (Inscripción #{idx_seleccionado+1})")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        nombre_edit = st.text_input("Nombre y Apellido", value=estudiante.get("nombre", ""), key="acred_nom_sel")
                        escuela_edit = st.text_input("Escuela", value=estudiante.get("escuela", ""), key="acred_esc_sel")
                        inscripcion_edit = st.text_input("Desafío / Inscripción", value=estudiante.get("inscripcion", ""), key="acred_insc_sel")
                        nivel_edit = st.text_input("Nivel", value=estudiante.get("nivel", ""), key="acred_niv_sel")
                    
                    with col2:
                        email_est_edit = st.text_input("Email Estudiante", value=estudiante.get("email", ""), key="acred_mail_est_sel")
                        docente_mail_val = estudiante.get("email_docente", "")
                        if docente_mail_val == "Sin Datos":
                            docente_mail_val = ""
                        email_doc_edit = st.text_input("Mail Docente / Acompañante", value=docente_mail_val, placeholder="ejemplo@docente.edu.ar", key="acred_mail_doc_sel")
                        especialidad_edit = st.text_input("Especialidad (del Padrón)", value=estudiante.get("especialidad", "General"), key="acred_esp_sel")

                    if st.button("✅ Confirmar Presente DTCABA", key="acreditar_btn_sel", type="primary"):
                        doc_presente = {
                            "fecha_acreditacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "dni": dni_acreditar,
                            "estudiante": nombre_edit,
                            "escuela": escuela_edit,
                            "email_estudiante": email_est_edit,
                            "email_docente": email_doc_edit if email_doc_edit.strip() else "Sin Datos",
                            "inscripcion": inscripcion_edit,
                            "nivel": nivel_edit,
                            "especialidad": especialidad_edit,
                            "evento": "DTCABA"
                        }
                        db.collection("presentes").add(doc_presente)
                        st.success(f"🎉 ¡{nombre_edit} ha sido acreditado/a en DTCABA con éxito!")
            else:
                st.warning("⚠️ No se encontró ningún estudiante con ese DNI en el padrón.")

# ---------------------------------------------------------
# EVENTO 2: HACKATHON 2026
# ---------------------------------------------------------
elif evento_seleccionado == "🏆 Hackathon 2026":
    st.markdown(
        """
        <div class="app-header">
            <h1>🏆 Rúbrica de Evaluación Hackathon</h1>
            <p>Portal Oficial del Jurado</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if opcion == "Cargar Evaluación Hackathon":
        with st.container(border=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                evaluador = st.text_input("Evaluador*", placeholder="Ej. Gustavo", key="hk_eval")
            with col2:
                equipo = st.text_input("Equipo / Proyecto*", placeholder="Ej. Nicolas", key="hk_equipo")
            with col3:
                especialidad_hk = st.text_input("Especialidad del Proyecto", placeholder="Ej. Computación", key="hk_esp")

        st.subheader("📊 Criterios de Evaluación Hackathon")

        desc_hk_15 = {
            15: "15 pts - Excelente (Supera ampliamente las expectativas)",
            10: "10 pts - Satisfactorio (Cumple correctamente con el criterio)",
            5: "5 pts - En Desarrollo (Presenta aspectos incompletos)",
            0: "0 pts - Inicial (No cumple con el criterio)"
        }

        desc_hk_10 = {
            10: "10 pts - Excelente (Integración total y profunda)",
            5: "5 pts - Satisfactorio (Integración parcial de disciplinas)",
            0: "0 pts - Inicial (Sin enfoque interdisciplinario)"
        }

        with st.container(border=True):
            st.markdown("#### 1. Escenario (Máx. 15 pts)")
            c1 = st.radio("Nivel Escenario:", [15, 10, 5, 0], format_func=lambda x: desc_hk_15[x], key="hk_1")

        with st.container(border=True):
            st.markdown("#### 2. Infraestructura y Energía (Máx. 15 pts)")
            c2 = st.radio("Nivel Infraestructura:", [15, 10, 5, 0], format_func=lambda x: desc_hk_15[x], key="hk_2")

        with st.container(border=True):
            st.markdown("#### 3. Comunicación e Información (Máx. 15 pts)")
            c3 = st.radio("Nivel Comunicación:", [15, 10, 5, 0], format_func=lambda x: desc_hk_15[x], key="hk_3")

        with st.container(border=True):
            st.markdown("#### 4. Coordinación y Logística (Máx. 15 pts)")
            c4 = st.radio("Nivel Coordinación:", [15, 10, 5, 0], format_func=lambda x: desc_hk_15[x], key="hk_4")

        with st.container(border=True):
            st.markdown("#### 5. Atención a la Población (Máx. 15 pts)")
            c5 = st.radio("Nivel Atención:", [15, 10, 5, 0], format_func=lambda x: desc_hk_15[x], key="hk_5")

        with st.container(border=True):
            st.markdown("#### 6. Operación de Emergencia (Máx. 15 pts)")
            c6 = st.radio("Nivel Operación:", [15, 10, 5, 0], format_func=lambda x: desc_hk_15[x], key="hk_6")

        with st.container(border=True):
            st.markdown("#### 7. Enfoque Interdisciplinario (Máx. 10 pts)")
            c7 = st.radio("Nivel Interdisciplinario:", [10, 5, 0], format_func=lambda x: desc_hk_10[x], key="hk_7")

        total_score = c1 + c2 + c3 + c4 + c5 + c6 + c7
        st.metric(label="🎯 Puntaje Total Hackathon", value=f"{total_score} / 100 pts")

        with st.container(border=True):
            observaciones = st.text_area("💬 Observaciones / Justificación", placeholder="Escribe tus comentarios...", key="hk_obs", height=100)

        if st.button("🚀 Guardar Evaluación Hackathon", type="primary"):
            if not evaluador.strip() or not equipo.strip():
                st.warning("⚠️ Por favor completa el Evaluador y el Equipo.")
            else:
                eval_respuestas_hk = {
                    "criterio_1_escenario_pts": c1,
                    "criterio_1_escenario_desc": desc_hk_15[c1],
                    "criterio_2_infraestructura_energia_pts": c2,
                    "criterio_2_infraestructura_energia_desc": desc_hk_15[c2],
                    "criterio_3_comunicacion_info_pts": c3,
                    "criterio_3_comunicacion_info_desc": desc_hk_15[c3],
                    "criterio_4_coordinacion_logistica_pts": c4,
                    "criterio_4_coordinacion_logistica_desc": desc_hk_15[c4],
                    "criterio_5_atencion_poblacion_pts": c5,
                    "criterio_5_atencion_poblacion_desc": desc_hk_15[c5],
                    "criterio_6_operacion_emergencia_pts": c6,
                    "criterio_6_operacion_emergencia_desc": desc_hk_15[c6],
                    "criterio_7_enfoque_interdisciplinario_pts": c7,
                    "criterio_7_enfoque_interdisciplinario_desc": desc_hk_10[c7],
                    "observaciones_generales": observaciones
                }

                doc_eval_hk = {
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "evaluador": evaluador,
                    "equipo": equipo,
                    "evento": "Hackathon 2026",
                    "especialidad": especialidad_hk if especialidad_hk.strip() else "General",
                    "promedio": total_score,
                    "respuestas": eval_respuestas_hk
                }
                db.collection("evaluaciones").add(doc_eval_hk)
                st.session_state["exito_msj_hk"] = f"✅ ¡Evaluación del equipo '{equipo}' guardada correctamente en Firebase!"
                st.balloons()
                st.rerun()

        if "exito_msj_hk" in st.session_state:
            st.success(st.session_state["exito_msj_hk"])
            del st.session_state["exito_msj_hk"]

    elif opcion == "📌 Acreditación Hackathon":
        st.header("📌 Módulo de Acreditación de Presentes (Hackathon)")
        st.markdown("Busca al participante por DNI en el padrón para confirmar e ingresar su asistencia al Hackathon.")

        dni_hk_acred = st.text_input("Ingresar DNI del Participante a Acreditar", placeholder="Ej: 39098198", key="acred_dni_hk").strip().replace(".", "")

        if dni_hk_acred:
            coincidencias = buscar_estudiantes_por_dni(dni_hk_acred)

            if coincidencias:
                st.success(f"✅ Participante Encontrado en Padrón ({len(coincidencias)} registro/s)")
                
                idx_hk_sel = 0
                if len(coincidencias) > 1:
                    opciones_hk_acred = [f"Inscripción #{i+1}: {c.get('inscripcion', 'Sin datos')} ({c.get('escuela', '')})" for i, c in enumerate(coincidencias)]
                    idx_hk_sel = st.selectbox("Seleccionar la inscripción a acreditar:", range(len(opciones_hk_acred)), format_func=lambda x: opciones_hk_acred[x], key="sel_hk_acred_multi")

                participante = coincidencias[idx_hk_sel]

                with st.container(border=True):
                    st.markdown(f"### ✏️ Validar Registro Hackathon (Inscripción #{idx_hk_sel+1})")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        nombre_hk = st.text_input("Nombre y Apellido", value=participante.get("nombre", ""), key="hk_nom_sel")
                        escuela_hk = st.text_input("Escuela / Institución", value=participante.get("escuela", ""), key="hk_esc_sel")
                        equipo_hk = st.text_input("Equipo / Proyecto / Inscripción", value=participante.get("inscripcion", ""), key="hk_insc_sel")
                    
                    with col2:
                        email_hk = st.text_input("Email Participante", value=participante.get("email", ""), key="hk_mail_sel")
                        docente_hk = participante.get("email_docente", "")
                        if docente_hk == "Sin Datos":
                            docente_hk = ""
                        email_doc_hk = st.text_input("Mail Tutor / Docente", value=docente_hk, placeholder="ejemplo@tutor.edu.ar", key="hk_mail_doc_sel")
                        especialidad_hk_acred = st.text_input("Especialidad (del Padrón)", value=participante.get("especialidad", "General"), key="hk_esp_acred_sel")

                    if st.button("🚀 Confirmar Acreditación Hackathon", key="acred_hk_btn_sel", type="primary"):
                        doc_hk_presente = {
                            "fecha_acreditacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "dni": dni_hk_acred,
                            "estudiante": nombre_hk,
                            "escuela": escuela_hk,
                            "email_estudiante": email_hk,
                            "email_docente": email_doc_hk if email_doc_hk.strip() else "Sin Datos",
                            "inscripcion": equipo_hk,
                            "especialidad": especialidad_hk_acred,
                            "evento": "Hackathon 2026"
                        }
                        db.collection("presentes").add(doc_hk_presente)
                        st.success(f"🎉 ¡{nombre_hk} ha sido acreditado/a en la Hackathon 2026!")
            else:
                st.warning("⚠️ No se encontró ningún participante con ese DNI en el padrón.")

# ---------------------------------------------------------
# PANEL DE ADMINISTRACIÓN Y REPORTE EXCEL / CSV
# ---------------------------------------------------------
if opcion in ["Panel de Administración", "Panel de Administración y Reportes"]:
    st.header("Panel de Administración y Reportes")
    clave = st.text_input("Contraseña Administrador", type="password")

    if clave == ADMIN_PASSWORD:
        st.success("🔓 Acceso de Administración concedido.")

        evals_raw = [d.to_dict() for d in db.collection("evaluaciones").stream()]
        equipos_raw = [d.to_dict() for d in db.collection("equipos").stream()]
        presentes_raw = [d.to_dict() for d in db.collection("presentes").stream()]

        df_evals = pd.json_normalize(evals_raw) if evals_raw else pd.DataFrame()
        df_equipos = aplanar_equipos(equipos_raw) if equipos_raw else pd.DataFrame()
        df_presentes = pd.DataFrame(presentes_raw) if presentes_raw else pd.DataFrame()

        tab1, tab2, tab3 = st.tabs(["📊 Evaluaciones Registradas", "🔑 Base de Códigos / Equipos", "📌 Lista de Presentes"])
        
        with tab1:
            if not df_evals.empty:
                st.dataframe(df_evals, use_container_width=True)
            else:
                st.info("No hay evaluaciones registradas aún.")

        with tab2:
            if not df_equipos.empty:
                st.dataframe(df_equipos, use_container_width=True)
            else:
                st.info("No hay equipos guardados aún.")

        with tab3:
            if not df_presentes.empty:
                st.dataframe(df_presentes, use_container_width=True)
            else:
                st.info("No hay asistentes acreditados aún.")

        st.markdown("---")
        st.subheader("📥 Exportar Datos a Excel / CSV")

        dict_export = {
            "Evaluaciones": evals_raw,
            "Equipos": equipos_raw,
            "Presentes_Acreditados": presentes_raw
        }
        excel_bytes = generar_excel_descarga(dict_export)

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.download_button(
                label="🟢 Descargar Libro Excel Completo (.xlsx)",
                data=excel_bytes,
                file_name=f"Reporte_Consolidado_DTCABA_Hackathon_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with col_d2:
            if not df_evals.empty:
                st.download_button(
                    label="📄 Descargar Evaluaciones (CSV)",
                    data=df_evals.to_csv(index=False).encode("utf-8"),
                    file_name="evaluaciones.csv",
                    mime="text/csv"
                )
