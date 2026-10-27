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
# Web App 1: Padrón principal de estudiantes
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwpYoAthfaViejGHAAThgQkAllbMrSsxfi-AC6vrcrtUtIeG-VtI5knuGPyGlGZhHl7tA/exec"

ADMIN_PASSWORD = "admin123"
CARACTERES_SEGUROS = "BCDFGHJKLMNPQRSTVWXYZ0123456789"

st.set_page_config(
    page_title="Plataforma de Evaluación de Eventos",
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

    header[data-testid="stHeader"] {
        display: none !important;
    }

    .block-container {
        padding-top: 1.5rem !important;
    }

    button[data-baseweb="tab"] {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        padding: 0.75rem 1rem !important;
        border-radius: 8px 8px 0px 0px !important;
    }

    .app-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%) !important;
        padding: 1.5rem 1.25rem; 
        border-radius: 16px; 
        margin-bottom: 1.5rem; 
        text-align: center;
        box-shadow: 0 10px 15px -3px rgba(15, 23, 42, 0.3);
    }
    .app-header h1 { 
        font-family: 'Poppins', sans-serif; 
        font-size: 1.8rem; 
        font-weight: 800; 
        margin: 0; 
        color: #FFFFFF !important; 
    }
    .app-header p { 
        margin: 0.4rem 0 0 0; 
        color: #94A3B8 !important; 
        font-weight: 500;
        font-size: 0.9rem;
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
    """Consulta la Web App 1 (Padrón)."""
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

def obtener_datos_equipo_por_codigo(codigo):
    """Recupera los integrantes y datos de un equipo guardado en Firestore."""
    try:
        docs = db.collection("equipos").where("codigo_unico", "==", codigo).stream()
        for doc in docs:
            return doc.to_dict()
    except Exception:
        pass
    return None

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
            "especialidad": eq.get("especialidad", ""),
            "url_stl": eq.get("url_stl", "")
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
# SELECCIÓN DE EVENTOS EN LA MISMA PANTALLA (PESTAÑAS)
# ---------------------------------------------------------
tab_dtcaba, tab_hackathon, tab_agua, tab_admin = st.tabs([
    "📐 Desafíos Técnicos DTCABA",
    "🏆 Hackathon 2026 (CIREC)",
    "💧 Desafíos del Agua",
    "⚙️ Administración General"
])

# =========================================================
# EVENTO 1: DESAFÍOS TÉCNICOS DTCABA
# =========================================================
with tab_dtcaba:
    st.markdown(
        """
        <div class="app-header">
            <h1>📐 Desafíos Técnicos DTCABA ⚙️</h1>
            <p>Plataforma de Evaluación y Gestión de Equipos</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    opcion_dtcaba = st.radio(
        "Módulo DTCABA",
        ["Cargar Evaluación DTCABA", "Generar Códigos de Equipos", "📌 Acreditación de Presentes"],
        horizontal=True,
        label_visibility="collapsed",
        key="nav_dtcaba_main"
    )

    st.markdown("---")

    if opcion_dtcaba == "Cargar Evaluación DTCABA":
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

            elif materia == "Matemática":
                map_mat1 = {
                    5: "5 - Destacado: Figura original y de alta complejidad en la representación.",
                    4: "4 - Avanzado: Figura tridimensional bien construida, muestra originalidad.",
                    3: "3 - Satisfactorio: La figura es adecuada y realizada de manera correcta.",
                    2: "2 - Básico: La figura no presenta complejidad.",
                    1: "1 - Inicial: La figura no es original y presenta errores de representación.",
                }
                map_mat2 = {
                    5: "5 - Destacado: Problema original, explícita la intervención de la figura y de integración.",
                    4: "4 - Avanzado: Situación problemática planteada explícita en la intervención.",
                    3: "3 - Satisfactorio: El problema es correcto pero no se evidencia la figura construida.",
                    2: "2 - Básico: El problema presenta inconsistencias matemáticas.",
                    1: "1 - Inicial: No logra contextualizar la situación problemática.",
                }
                map_mat3 = {
                    5: "5 - Destacado: Procedimiento completo, utiliza datos y justifica cada paso.",
                    4: "4 - Avanzado: Aplica procedimiento correcto y justifica cada paso.",
                    3: "3 - Satisfactorio: Procedimiento correcto pero con justificación parcial.",
                    2: "2 - Básico: Procedimiento correcto sin justificación.",
                    1: "1 - Inicial: No presenta procedimiento ni justificación.",
                }
                map_mat4 = {
                    5: "5 - Destacado: Términos, símbolos y expresiones matemáticas precisos y rigurosos.",
                    4: "4 - Avanzado: Expresiones matemáticas correctas en su mayoría.",
                    3: "3 - Satisfactorio: Uso impreciso o escaso de expresiones matemáticas.",
                    2: "2 - Básico: Explica el desarrollo de forma coloquial o ambigua.",
                    1: "1 - Inicial: Comunicación del desarrollo imprecisa.",
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

            elif materia == "Tecnología de la Representación Nivel 1":
                st.markdown("### ✏️ Rúbrica 1.er Año: 100% Analógico (Lámina en Papel)")
                st.caption("Alineado estrictamente a la Lista de Cotejo y Rúbrica DTR (Análisis, Trazado, Normas e Integración).")

                map_tdr1_c1 = {
                    4: "4 - Destacado / Avanzado: Excelente interpretación espacial. Identifica y representa con absoluta precisión todas las figuras geométricas y sus relaciones en la estructura.",
                    3: "3 - Satisfactorio: Reconoce correctamente las figuras geométricas principales e interpreta adecuadamente sus relaciones espaciales.",
                    2: "2 - En desarrollo / Básico: Reconoce algunas figuras geométricas, pero presenta imprecisiones o necesita asistencia para interpretar su espacialidad.",
                    1: "1 - Inicial: Muestra serias dificultades para identificar las figuras y representar sus relaciones espaciales."
                }

                map_tdr1_c2 = {
                    4: "4 - Destacado / Avanzado: Acotación impecable. Flechas, tipos de línea, posición y separación aplicados con total rigurosidad según norma.",
                    3: "3 - Satisfactorio: Acotación correcta y legible. Mantiene flechas, líneas de cota y ubicación con mínimos detalles a corregir.",
                    2: "2 - En desarrollo / Básico: Acotación parcial o incompleta. Presenta inconsistencias en tipos de línea, flechas o ubicación de cotas.",
                    1: "1 - Inicial: Ausencia o aplicación errónea del sistema de acotado; dificulta la lectura métrica de la lámina."
                }

                map_tdr1_c3 = {
                    4: "4 - Destacado / Avanzado: Dominio sobresaliente de los métodos de trazado (bisectriz, mediatriz, óvalos, ovoides) con cierres y empalmes perfectos.",
                    3: "3 - Satisfactorio: Correcta resolución de construcciones geométricas y empalmes con buena precisión de trazado.",
                    2: "2 - En desarrollo / Básico: Trazados con imprecisiones visibles; empalmes o cierres de figuras parcialmente resueltos.",
                    1: "1 - Inicial: Errores graves en la aplicación de métodos geométricos; cierres y empalmes defectuosos o inexistentes."
                }

                map_tdr1_c4 = {
                    4: "4 - Destacado / Avanzado: Aplicación rigurosa de Normas IRAM. Perfecta diferenciación y jerarquía de tipos de líneas y trazos.",
                    3: "3 - Satisfactorio: Correcta diferenciación de líneas y trazos respetando los criterios normativos fundamentales.",
                    2: "2 - En desarrollo / Básico: Inconsistencia en la jerarquía de trazos o uso confuso de los tipos de línea IRAM.",
                    1: "1 - Inicial: Incumplimiento de las normas IRAM en el uso de líneas, espesores y trazos."
                }

                map_tdr1_c5 = {
                    4: "4 - Destacado / Avanzado: Organización espacial simétrica y equilibrada. Caligrafía técnica perfecta en rótulo y plegado a 2 pliegues impecable.",
                    3: "3 - Satisfactorio: Buena ubicación en el plano (centrado y proporción), caligrafía prolija y plegado a 2 pliegues correcto.",
                    2: "2 - En desarrollo / Básico: Presentación con fallas de centrado, caligrafía irregular o plegado defectuoso.",
                    1: "1 - Inicial: Lámina desorganizada, sin centrado ni proporción, caligrafía deficiente y plegado incorrecto."
                }

                st.markdown("#### BLOQUE 1: Análisis e Interpretación Geométrica (40%)")
                with st.container(border=True):
                    st.markdown("##### 1.1 Identificación y Representación de Figuras (20%)")
                    st.caption("Reconocimiento de figuras geométricas, cantidad y relaciones espaciales en la estructura.")
                    tdr1_c1 = st.radio("Nivel:", [4, 3, 2, 1], format_func=lambda x: map_tdr1_c1[x], key="tdr1_c1")
                    tdr1_obs1 = st.text_area("Observaciones:", key="tdr1_obs1", height=60)

                with st.container(border=True):
                    st.markdown("##### 1.2 Acotaciones e Interpretación Espacial (20%)")
                    st.caption("Normas de acotado: flechas, tipos de línea, separación, posición y lectura métrica.")
                    tdr1_c2 = st.radio("Nivel:", [4, 3, 2, 1], format_func=lambda x: map_tdr1_c2[x], key="tdr1_c2")
                    tdr1_obs2 = st.text_area("Observaciones:", key="tdr1_obs2", height=60)

                st.markdown("#### BLOQUE 2: Método de Construcción y Trazado (20%)")
                with st.container(border=True):
                    st.markdown("##### 2.1 Métodos de Trazado, Construcciones y Empalmes (20%)")
                    st.caption("Precisión en métodos geométricos (bisectriz, mediatriz, óvalos, ovoides) y empalmes/cierres correctos.")
                    tdr1_c3 = st.radio("Nivel:", [4, 3, 2, 1], format_func=lambda x: map_tdr1_c3[x], key="tdr1_c3")
                    tdr1_obs3 = st.text_area("Observaciones:", key="tdr1_obs3", height=60)

                st.markdown("#### BLOQUE 3: Aplicación de Normas IRAM (20%)")
                with st.container(border=True):
                    st.markdown("##### 3.1 Normas IRAM, Líneas y Jerarquía de Trazos (20%)")
                    st.caption("Uso normado de tipos de líneas, intensidad de trazos y precisión técnica.")
                    tdr1_c4 = st.radio("Nivel:", [4, 3, 2, 1], format_func=lambda x: map_tdr1_c4[x], key="tdr1_c4")
                    tdr1_obs4 = st.text_area("Observaciones:", key="tdr1_obs4", height=60)

                st.markdown("#### BLOQUE 4: Presentación Técnica y Organización (20%)")
                with st.container(border=True):
                    st.markdown("##### 4.1 Ubicación, Caligrafía, Rótulo y Plegado (20%)")
                    st.caption("Centrado, proporción, equilibrio compositivo, caligrafía técnica (15%) y plegado a 2 pliegues (5%).")
                    tdr1_c5 = st.radio("Nivel:", [4, 3, 2, 1], format_func=lambda x: map_tdr1_c5[x], key="tdr1_c5")
                    tdr1_obs5 = st.text_area("Observaciones:", key="tdr1_obs5", height=60)

                promedio_base4 = (tdr1_c1 * 0.20) + (tdr1_c2 * 0.20) + (tdr1_c3 * 0.20) + (tdr1_c4 * 0.20) + (tdr1_c5 * 0.20)
                puntaje_100 = round((promedio_base4 / 4) * 100, 2)

                eval_respuestas = {
                    "identificacion_figuras_pts": tdr1_c1, "identificacion_figuras_obs": tdr1_obs1,
                    "acotacion_espacial_pts": tdr1_c2, "acotacion_espacial_obs": tdr1_obs2,
                    "metodos_trazado_empalmes_pts": tdr1_c3, "metodos_trazado_empalmes_obs": tdr1_obs3,
                    "normas_iram_lineas_pts": tdr1_c4, "normas_iram_lineas_obs": tdr1_obs4,
                    "presentacion_caligrafia_plegado_pts": tdr1_c5, "presentacion_caligrafia_plegado_obs": tdr1_obs5,
                }

            elif materia == "Tecnología de la Representación Nivel 2":
                st.markdown("### 🎛️ Rúbrica 2.º Año: Modalidad Híbrida (60% Tinkercad + 40% Lámina Técnica)")
                st.caption("Estructurado según los Lineamientos DTR: 60% Modelado 3D Digital + 40% Lámina Técnica en Papel.")

                equipo_info = obtener_datos_equipo_por_codigo(codigo_unico)
                if equipo_info:
                    url_stl = equipo_info.get("url_stl", "").strip()
                    
                    with st.container(border=True):
                        st.markdown("#### 📦 Entrega Digital 3D en Tinkercad (.stl / .obj)")
                        if url_stl:
                            st.success("✅ El equipo tiene un modelo 3D registrado en el sistema:")
                            col_b1, col_b2 = st.columns([1, 2])
                            with col_b1:
                                st.link_button("📥 Abrir / Descargar Modelo 3D", url_stl, type="primary")
                            with col_b2:
                                st.caption("Haz clic para abrir el archivo o diseño en una nueva pestaña y evaluarlo.")
                        else:
                            st.warning("⚠️ Este equipo no tiene ningún enlace a archivo STL / 3D asociado en Firebase.")
                else:
                    st.info("💡 Este código no tiene integrantes asociados en Firebase aún.")

                map_tdr2_c1 = {
                    4: "4 - Destacado / Avanzado: Medición exacta de la pieza física, boceto de análisis riguroso y reconstrucción completa del volumen faltante.",
                    3: "3 - Satisfactorio: Correcta medición e interpretación con mínimos desajustes dimensionales en la reconstrucción.",
                    2: "2 - En desarrollo / Básico: Medición imprecisa o reconstrucción volumétrica con inconsistencias geométricas visibles.",
                    1: "1 - Inicial: Fallas graves en la lectura dimensional; no logra interpretar ni reconstruir el volumen faltante."
                }

                map_tdr2_c2 = {
                    4: "4 - Destacado / Avanzado: Modelado 3D impecable. Correcta elección de formas, encastres perfectos y archivo (.stl/.obj) listo para producción.",
                    3: "3 - Satisfactorio: Modelo 3D bien resuelto en Tinkercad con pequeñas imprecisiones en tolerancias de encastre.",
                    2: "2 - En desarrollo / Básico: Modelo 3D incompleto, con errores de escala, desalineación o fallas en operaciones booleanas.",
                    1: "1 - Inicial: No logra construir el modelo 3D digital o presenta una estructura tridimensional incoherente."
                }

                map_tdr2_c3 = {
                    4: "4 - Destacado / Avanzado: Proyección rigurosa de vistas ortogonales alineadas e isométrica impecable con excelente coherencia espacial.",
                    3: "3 - Satisfactorio: Representación correcta de vistas e isométrica que permiten comprender perfectamente la pieza.",
                    2: "2 - En desarrollo / Básico: Vistas desalineadas o perspectiva isométrica con errores de trazado y proporción.",
                    1: "1 - Inicial: Múltiples errores en el sistema de vistas e isométrica; falta de coherencia espacial entre proyecciones."
                }

                map_tdr2_c4 = {
                    4: "4 - Destacado / Avanzado: Aplicación perfecta de normas IRAM (líneas, acotado), caligrafía técnica pulcra y plegado a 2 pliegues normado.",
                    3: "3 - Satisfactorio: Correcta aplicación de tipos de línea, acotación legible, rótulo ordenado y plegado correcto.",
                    2: "2 - En desarrollo / Básico: Errores en acotaciones o tipos de línea; presentación con falta de prolijidad gráfica.",
                    1: "1 - Inicial: Incumplimiento de normas IRAM, caligrafía deficiente y desorganización general de la lámina."
                }

                st.markdown("---")
                st.markdown("### 🖥️ PARTE 1: Modelado Digital 3D en Tinkercad (60%)")
                
                with st.container(border=True):
                    st.markdown("##### 1. Medición, Bocetado e Interpretación de la Pieza (30%)")
                    st.caption("Medición métrica de la pieza recuperada, boceto inicial de análisis y resolución del volumen faltante.")
                    tdr2_c1 = st.radio("Nivel:", [4, 3, 2, 1], format_func=lambda x: map_tdr2_c1[x], key="tdr2_c1")
                    tdr2_obs1 = st.text_area("Observaciones Tinkercad - Medición e Interpretación:", key="tdr2_obs1", height=60)

                with st.container(border=True):
                    st.markdown("##### 2. Modelado 3D, Operaciones y Encastres (30%)")
                    st.caption("Proporcionalidad, resolución de encastres, tolerancia métrica y calidad del modelo digital exportado (.obj / .stl).")
                    tdr2_c2 = st.radio("Nivel:", [4, 3, 2, 1], format_func=lambda x: map_tdr2_c2[x], key="tdr2_c2")
                    tdr2_obs2 = st.text_area("Observaciones Tinkercad - Modelado y Encastres:", key="tdr2_obs2", height=60)

                st.markdown("---")
                st.markdown("### 📜 PARTE 2: Lámina Técnica en Papel (40%)")

                with st.container(border=True):
                    st.markdown("##### 3. Representación de Vistas y Perspectiva Isométrica (20%)")
                    st.caption("Representación ortogonal alineada de vistas principales, perspectiva isométrica y coherencia espacial.")
                    tdr2_c3 = st.radio("Nivel:", [4, 3, 2, 1], format_func=lambda x: map_tdr2_c3[x], key="tdr2_c3")
                    tdr2_obs3 = st.text_area("Observaciones Lámina - Vistas e Isométrica:", key="tdr2_obs3", height=60)

                with st.container(border=True):
                    st.markdown("##### 4. Normas IRAM, Acotación, Caligrafía y Plegado (20%)")
                    st.caption("Tipos de línea IRAM, acotación normada (flechas, posición, valores), caligrafía técnica y plegado a 2 pliegues.")
                    tdr2_c4 = st.radio("Nivel:", [4, 3, 2, 1], format_func=lambda x: map_tdr2_c4[x], key="tdr2_c4")
                    tdr2_obs4 = st.text_area("Observaciones Lámina - Normas y Presentación:", key="tdr2_obs4", height=60)

                pts_tinkercad = round((((tdr2_c1 * 0.30) + (tdr2_c2 * 0.30)) / 4) * 100, 2)
                pts_lamina = round((((tdr2_c3 * 0.20) + (tdr2_c4 * 0.20)) / 4) * 100, 2)
                
                promedio_base4 = (tdr2_c1 * 0.30) + (tdr2_c2 * 0.30) + (tdr2_c3 * 0.20) + (tdr2_c4 * 0.20)
                puntaje_100 = round((promedio_base4 / 4) * 100, 2)

                col_m1, col_m2 = st.columns(2)
                with col_m1:
                    st.metric(label="💻 Subtotal Tinkercad (60% Máx)", value=f"{pts_tinkercad} / 60 pts")
                with col_m2:
                    st.metric(label="📜 Subtotal Lámina (40% Máx)", value=f"{pts_lamina} / 40 pts")

                eval_respuestas = {
                    "medicion_bocetado_pts": tdr2_c1, "medicion_bocetado_obs": tdr2_obs1,
                    "modelado_encastres_pts": tdr2_c2, "modelado_encastres_obs": tdr2_obs2,
                    "vistas_isometrica_pts": tdr2_c3, "vistas_isometrica_obs": tdr2_obs3,
                    "normas_acotacion_plegado_pts": tdr2_c4, "normas_acotacion_plegado_obs": tdr2_obs4,
                    "subtotal_tinkercad_60": pts_tinkercad,
                    "subtotal_lamina_40": pts_lamina,
                }

            st.metric(label="Puntaje Total Ponderado (sobre 100)", value=f"{puntaje_100} / 100 pts")

            if st.button("💾 Guardar Evaluación", type="primary", key="btn_save_dtcaba"):
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

    elif opcion_dtcaba == "Generar Códigos de Equipos":
        st.header("Generador de Códigos para Equipos / Duplas")
        clave = st.text_input("Contraseña de Acceso", type="password", key="pass_gen_dtc")

        if clave == ADMIN_PASSWORD:
            st.success("🔓 Acceso habilitado.")
            cant_integrantes = st.number_input("Cantidad de Integrantes del Equipo", min_value=1, max_value=10, value=2, key="num_integ")
            prefijo = st.selectbox("Materia / Categoría", ["MAT", "LEN", "TDR1", "TDR2", "HACKATHON", "AGUA"], key="prefijo_mat")

            url_stl_input = st.text_input(
                "🔗 URL de Entrega 3D / STL (Opcional - Google Drive, Tinkercad, etc.)", 
                placeholder="https://drive.google.com/file/d/...", 
                key="input_url_stl_gen"
            ).strip()

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

            if st.button("🎲 Generar Código de Equipo", type="primary", key="btn_gen_code"):
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
                    "url_stl": url_stl_input,
                    "integrantes": datos_integrantes
                }
                db.collection("equipos").add(doc_equipo)
                st.success(f"✅ Código Único Generado: **{codigo_generado}**")
                st.code(codigo_generado, language="text")

    elif opcion_dtcaba == "📌 Acreditación de Presentes":
        st.header("📌 Acreditación de Presentes (DTCABA)")
        st.markdown("Busca al estudiante por DNI en el padrón o ingresa sus datos manualmente si no se encuentra registrado.")

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
                val_nom = estudiante.get("nombre", "")
                val_esc = estudiante.get("escuela", "")
                val_insc = estudiante.get("inscripcion", "")
                val_niv = estudiante.get("nivel", "")
                val_mail_est = estudiante.get("email", "")
                val_mail_doc = estudiante.get("email_docente", "")
                if val_mail_doc == "Sin Datos":
                    val_mail_doc = ""
                val_esp = estudiante.get("especialidad", "General")
            else:
                st.info("ℹ️ El DNI no se encuentra en el padrón. Puedes ingresar los datos manualmente a continuación:")
                val_nom = ""
                val_esc = ""
                val_insc = ""
                val_niv = ""
                val_mail_est = ""
                val_mail_doc = ""
                val_esp = "General"

            with st.container(border=True):
                st.markdown("### ✏️ Datos del Registro de Acreditación")
                col1, col2 = st.columns(2)
                with col1:
                    nombre_edit = st.text_input("Nombre y Apellido*", value=val_nom, key="acred_nom_sel")
                    escuela_edit = st.text_input("Escuela*", value=val_esc, key="acred_esc_sel")
                    inscripcion_edit = st.text_input("Desafío / Inscripción", value=val_insc, key="acred_insc_sel")
                    nivel_edit = st.text_input("Nivel", value=val_niv, key="acred_niv_sel")
                
                with col2:
                    email_est_edit = st.text_input("Email Estudiante", value=val_mail_est, key="acred_mail_est_sel")
                    email_doc_edit = st.text_input("Mail Docente / Acompañante", value=val_mail_doc, placeholder="ejemplo@docente.edu.ar", key="acred_mail_doc_sel")
                    especialidad_edit = st.text_input("Especialidad", value=val_esp, key="acred_esp_sel")

            if st.button("✅ Confirmar Presente DTCABA", key="acreditar_btn_sel", type="primary"):
                if not nombre_edit.strip() or not escuela_edit.strip():
                    st.warning("⚠️ Por favor completa el Nombre y la Escuela del estudiante.")
                else:
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

# =========================================================
# EVENTO 2: HACKATHON CIREC 2026
# =========================================================
with tab_hackathon:
    st.markdown(
        """
        <div class="app-header">
            <h1>🏆 Rúbrica de Evaluación — Desafíos CIREC</h1>
            <p>Centro Integral de Respuesta ante Emergencias Climáticas</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    opcion_hk = st.radio(
        "Módulo Hackathon",
        ["Cargar Evaluación Hackathon", "📌 Acreditación Hackathon"],
        horizontal=True,
        label_visibility="collapsed",
        key="nav_hk_main"
    )

    st.markdown("---")

    if opcion_hk == "Cargar Evaluación Hackathon":
        if st.session_state.get("eval_hk_guardada_exito"):
            st.success("✅ ¡Evaluación cargada con éxito! El formulario se ha reiniciado.")
            st.session_state["eval_hk_guardada_exito"] = False

        lista_escenarios_oficiales = [
            "-- Seleccionar Escenario --",
            "Región Litoral – Corrientes",
            "Región Centro – Córdoba",
            "Región Cuyo – Mendoza",
            "Región Patagonia – Chubut",
            "Región Noroeste Argentino (NOA) – Jujuy",
            "Región Metropolitana – Área Metropolitana de Buenos Aires (AMBA)",
        ]

        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                evaluador = st.text_input("Evaluador/a*", placeholder="Ej. Gustavo", key="hk_eval")
                equipo = st.text_input("Equipo*", placeholder="Ej. Equipo Alpha", key="hk_equipo")
            with col2:
                escenario_sel = st.selectbox(
                    "Escenario Asignado*",
                    options=lista_escenarios_oficiales,
                    key="hk_escenario_select"
                )

        if escenario_sel == "-- Seleccionar Escenario --":
            escenario = ""
        else:
            escenario = escenario_sel

        st.subheader("📊 Indicadores de Evaluación CIREC (4 Niveles de Desempeño - Total: 100 pts)")

        map_hk_10 = {
            10.0: "Alto desempeño (10 pts): Coherencia total, alta rigurosidad técnica y adaptación completa al escenario.",
            7.0: "Desempeño medio (7 pts): Propuesta sólida con imprecisiones menores en la adaptación o ejecución.",
            4.0: "Desempeño regular (4 pts): Esquema básico o parcial, con vacíos funcionales o viabilidad técnica dudosa.",
            1.0: "Bajo desempeño (1 pt): Propuesta incoherente, muy limitada o sin responder al criterio."
        }

        map_hk_15 = {
            15.0: "Alto desempeño (15 pts): Cobertura integral, diseño redundante de contingencia y enfoque amplio.",
            10.5: "Desempeño medio (10.5 pts): Respuesta operativa sólida con omisiones secundarias de respaldo.",
            6.0: "Desempeño regular (6 pts): Esquema funcional básico pero vulnerable o desorganizado ante situaciones de crisis.",
            1.5: "Bajo desempeño (1.5 pts): No contempla suministros esenciales, continuidad ni asistencia adecuada."
        }

        st.markdown("### 1. Diseño de infraestructura y energía (25 pts)")
        with st.container(border=True):
            st.markdown("#### Diseño conceptual del CIREC (Máx. 10 pts)")
            st.caption("El edificio/complejo y la organización de espacios funcionales responden de forma coherente al escenario climático y geográfico asignado.")
            hk_c1 = st.radio("Nivel:", [10.0, 7.0, 4.0, 1.0], format_func=lambda x: map_hk_10[x], key="hk_c1")
            hk_obs1 = st.text_area("Observaciones del Diseño Conceptual:", key="hk_obs1", height=60)

        with st.container(border=True):
            st.markdown("#### Energía y agua (Máx. 15 pts)")
            st.caption("Se define el abastecimiento de energía y agua, y la continuidad operativa de los servicios esenciales ante el corte de suministros habituales.")
            hk_c2 = st.radio("Nivel:", [15.0, 10.5, 6.0, 1.5], format_func=lambda x: map_hk_15[x], key="hk_c2")
            hk_obs2 = st.text_area("Observaciones de Energía y Agua:", key="hk_obs2", height=60)

        st.markdown("### 2. Comunicación y gestión de la información (20 pts)")
        with st.container(border=True):
            st.markdown("#### Monitoreo y comunicaciones (Máx. 10 pts)")
            st.caption("Existen sistemas de monitoreo permanente y de comunicación interna/externa robustos ante la caída de infraestructura habitual.")
            hk_c3 = st.radio("Nivel:", [10.0, 7.0, 4.0, 1.0], format_func=lambda x: map_hk_10[x], key="hk_c3")
            hk_obs3 = st.text_area("Observaciones de Monitoreo y Comunicaciones:", key="hk_obs3", height=60)

        with st.container(border=True):
            st.markdown("#### Interfaz digital (Máx. 10 pts)")
            st.caption("La interfaz propuesta para acceder a la información es clara, rápida e intuitiva, y está adaptada a quien debe usarla en una crisis.")
            hk_c4 = st.radio("Nivel:", [10.0, 7.0, 4.0, 1.0], format_func=lambda x: map_hk_10[x], key="hk_c4")
            hk_obs4 = st.text_area("Observaciones de Interfaz Digital:", key="hk_obs4", height=60)

        st.markdown("### 3. Coordinación y logística (20 pts)")
        with st.container(border=True):
            st.markdown("#### Coordinación interinstitucional (Máx. 10 pts)")
            st.caption("Se explicita cómo se coordina con los organismos de respuesta (bomberos, salud, defensa civil, etc.) y cómo se resuelven conflictos de prioridad.")
            hk_c5 = st.radio("Nivel:", [10.0, 7.0, 4.0, 1.0], format_func=lambda x: map_hk_10[x], key="hk_c5")
            hk_obs5 = st.text_area("Observaciones de Coordinación Interinstitucional:", key="hk_obs5", height=60)

        with st.container(border=True):
            st.markdown("#### Logística y distribución de recursos (Máx. 10 pts)")
            st.caption("El sistema de distribución de recursos es viable, considera el escenario geográfico y prioriza según necesidad.")
            hk_c6 = st.radio("Nivel:", [10.0, 7.0, 4.0, 1.0], format_func=lambda x: map_hk_10[x], key="hk_c6")
            hk_obs6 = st.text_area("Observaciones de Logística y Recursos:", key="hk_obs6", height=60)

        st.markdown("### 4. Atención a la población (15 pts)")
        with st.container(border=True):
            st.markdown("#### Asistencia a la población afectada (Máx. 15 pts)")
            st.caption("La propuesta contempla mecanismos concretos de asistencia y comunicación directa con la comunidad, incluyendo grupos vulnerables.")
            hk_c7 = st.radio("Nivel:", [15.0, 10.5, 6.0, 1.5], format_func=lambda x: map_hk_15[x], key="hk_c7")
            hk_obs7 = st.text_area("Observaciones de Asistencia a la Población:", key="hk_obs7", height=60)

        st.markdown("### 5. Operación durante la emergencia (10 pts)")
        with st.container(border=True):
            st.markdown("#### Funcionamiento dinámico del sistema (Máx. 10 pts)")
            st.caption("Se describe cómo el CIREC detecta, decide, prioriza y se adapta a medida que evoluciona el evento (no solo el diseño estático).")
            hk_c8 = st.radio("Nivel:", [10.0, 7.0, 4.0, 1.0], format_func=lambda x: map_hk_10[x], key="hk_c8")
            hk_obs8 = st.text_area("Observaciones del Funcionamiento Dinámico:", key="hk_obs8", height=60)

        st.markdown("### 6. Enfoque interdisciplinario y fundamentación (10 pts)")
        with st.container(border=True):
            st.markdown("#### Integración de especialidades y fundamentación técnica (Máx. 10 pts)")
            st.caption("Las distintas disciplinas están integradas de forma coherente y las decisiones se justifican con criterios técnicos, ambientales, sociales y económicos.")
            hk_c9 = st.radio("Nivel:", [10.0, 7.0, 4.0, 1.0], format_func=lambda x: map_hk_10[x], key="hk_c9")
            hk_obs9 = st.text_area("Observaciones de Integración y Fundamentación:", key="hk_obs9", height=60)

        total_score_hk = hk_c1 + hk_c2 + hk_c3 + hk_c4 + hk_c5 + hk_c6 + hk_c7 + hk_c8 + hk_c9
        st.metric(label="🎯 Puntaje Total CIREC", value=f"{total_score_hk:.2f} / 100.00 pts")

        if st.button("🚀 Guardar Evaluación CIREC", type="primary", key="btn_save_hk"):
            if not evaluador.strip() or not equipo.strip() or not escenario.strip():
                st.warning("⚠️ Por favor completa el Evaluador/a, el Equipo y selecciona el Escenario asignado.")
            else:
                eval_respuestas_hk = {
                    "diseno_conceptual_pts": hk_c1, "diseno_conceptual_desc": map_hk_10[hk_c1], "diseno_conceptual_obs": hk_obs1,
                    "energia_agua_pts": hk_c2, "energia_agua_desc": map_hk_15[hk_c2], "energia_agua_obs": hk_obs2,
                    "monitoreo_comunicaciones_pts": hk_c3, "monitoreo_comunicaciones_desc": map_hk_10[hk_c3], "monitoreo_comunicaciones_obs": hk_obs3,
                    "interfaz_digital_pts": hk_c4, "interfaz_digital_desc": map_hk_10[hk_c4], "interfaz_digital_obs": hk_obs4,
                    "coordinacion_interinstitucional_pts": hk_c5, "coordinacion_interinstitucional_desc": map_hk_10[hk_c5], "coordinacion_interinstitucional_obs": hk_obs5,
                    "logistica_recursos_pts": hk_c6, "logistica_recursos_desc": map_hk_10[hk_c6], "logistica_recursos_obs": hk_obs6,
                    "asistencia_poblacion_pts": hk_c7, "asistencia_poblacion_desc": map_hk_15[hk_c7], "asistencia_poblacion_obs": hk_obs7,
                    "funcionamiento_dinamico_pts": hk_c8, "funcionamiento_dinamico_desc": map_hk_10[hk_c8], "funcionamiento_dinamico_obs": hk_obs8,
                    "integracion_fundamentacion_pts": hk_c9, "integracion_fundamentacion_desc": map_hk_10[hk_c9], "integracion_fundamentacion_obs": hk_obs9,
                }

                doc_eval_hk = {
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "evaluador": evaluador,
                    "equipo": equipo,
                    "escenario_asignado": escenario,
                    "evento": "Hackathon 2026 CIREC",
                    "promedio": total_score_hk,
                    "respuestas": eval_respuestas_hk
                }
                db.collection("evaluaciones").add(doc_eval_hk)
                st.session_state["eval_hk_guardada_exito"] = True

                keys_hk_limpiar = [
                    "hk_eval", "hk_equipo", "hk_escenario_select",
                    "hk_c1", "hk_obs1", "hk_c2", "hk_obs2", "hk_c3", "hk_obs3",
                    "hk_c4", "hk_obs4", "hk_c5", "hk_obs5", "hk_c6", "hk_obs6",
                    "hk_c7", "hk_obs7", "hk_c8", "hk_obs8", "hk_c9", "hk_obs9"
                ]
                for k in keys_hk_limpiar:
                    if k in st.session_state:
                        del st.session_state[k]

                st.rerun()

    elif opcion_hk == "📌 Acreditación Hackathon":
        st.header("📌 Módulo de Acreditación de Presentes (Hackathon CIREC)")
        st.markdown("Busca al participante por DNI en el padrón o ingresa sus datos manualmente si no figura en el sistema.")

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
                val_nom_hk = participante.get("nombre", "")
                val_esc_hk = participante.get("escuela", "")
                val_insc_hk = participante.get("inscripcion", "")
                val_mail_hk = participante.get("email", "")
                val_doc_hk = participante.get("email_docente", "")
                if val_doc_hk == "Sin Datos":
                    val_doc_hk = ""
                val_esp_hk = participante.get("especialidad", "General")
            else:
                st.info("ℹ️ El DNI no figura en el padrón. Puedes ingresar los datos manualmente a continuación:")
                val_nom_hk = ""
                val_esc_hk = ""
                val_insc_hk = ""
                val_mail_hk = ""
                val_doc_hk = ""
                val_esp_hk = "General"

            with st.container(border=True):
                st.markdown("### ✏️ Datos del Registro Hackathon")
                col1, col2 = st.columns(2)
                with col1:
                    nombre_hk = st.text_input("Nombre y Apellido*", value=val_nom_hk, key="hk_nom_sel")
                    escuela_hk = st.text_input("Escuela / Institución*", value=val_esc_hk, key="hk_esc_sel")
                    equipo_hk = st.text_input("Equipo / Proyecto / Inscripción", value=val_insc_hk, key="hk_insc_sel")
                
                with col2:
                    email_hk = st.text_input("Email Participante", value=val_mail_hk, key="hk_mail_sel")
                    email_doc_hk = st.text_input("Mail Tutor / Docente", value=val_doc_hk, placeholder="ejemplo@tutor.edu.ar", key="hk_mail_doc_sel")
                    especialidad_hk_acred = st.text_input("Especialidad", value=val_esp_hk, key="hk_esp_acred_sel")

            if st.button("🚀 Confirmar Acreditación Hackathon", key="acred_hk_btn_sel", type="primary"):
                if not nombre_hk.strip() or not escuela_hk.strip():
                    st.warning("⚠️ Por favor completa el Nombre y la Escuela del participante.")
                else:
                    doc_hk_presente = {
                        "fecha_acreditacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "dni": dni_hk_acred,
                        "estudiante": nombre_hk,
                        "escuela": escuela_hk,
                        "email_estudiante": email_hk,
                        "email_docente": email_doc_hk if email_doc_hk.strip() else "Sin Datos",
                        "inscripcion": equipo_hk,
                        "especialidad": especialidad_hk_acred,
                        "evento": "Hackathon 2026 CIREC"
                    }
                    db.collection("presentes").add(doc_hk_presente)
                    st.success(f"🎉 ¡{nombre_hk} ha sido acreditado/a en la Hackathon CIREC!")

# =========================================================
# EVENTO 3: DESAFÍOS CIENTÍFICOS DEL AGUA
# =========================================================
with tab_agua:
    st.markdown(
        """
        <div class="app-header">
            <h1>💧 Desafíos Científicos del Agua 🧪</h1>
            <p>Plataforma de Evaluación de Proyectos Científicos desarrollada por la DET con el apoyo de la GOES</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    opcion_agua = st.radio(
        "Módulo Desafíos del Agua",
        ["Cargar Evaluación Desafíos del Agua", "📌 Acreditación Desafíos del Agua"],
        horizontal=True,
        label_visibility="collapsed",
        key="nav_agua_main"
    )

    st.markdown("---")

    if opcion_agua == "Cargar Evaluación Desafíos del Agua":
        if st.session_state.get("eval_agua_guardada_exito"):
            st.success("✅ ¡Evaluación de Desafíos del Agua cargada con éxito! El formulario se ha reiniciado.")
            st.session_state["eval_agua_guardada_exito"] = False

        with st.container(border=True):
            col1, col2 = st.columns(2)
            with col1:
                evaluador_agua = st.text_input("Evaluador/a*", placeholder="Ej. Gustavo", key="agua_eval")
            with col2:
                equipo_agua = st.text_input("Equipo / Proyecto*", placeholder="Ej. HydroTech", key="agua_equipo")

        st.subheader("📋 Rúbrica de Evaluación — Desafíos del Agua (Total: 100 pts)")

        map_agua_25 = {
            25.0: "Alto desempeño (25 pts): Análisis riguroso, viabilidad completa y fundamentación científica sólida",
            18.75: "Desempeño medio (18.75 pts): Análisis correcto con fundamentos o planificación parciales",
            12.5: "Desempeño regular (12.5 pts): Análisis o viabilidad limitados, con vacíos técnicos significativos",
            5.0: "Bajo desempeño (5 pts): Análisis incorrecto, sin sustento o inviable"
        }

        map_agua_15 = {
            15.0: "Alto desempeño (15 pts): Propuesta original, bien estructurada y funcional",
            11.25: "Desempeño medio (11.25 pts): Propuesta funcional con algunos elementos innovadores o incompletos",
            7.5: "Desempeño regular (7.5 pts): Propuesta tradicional, poco clara o con desarrollo incipiente",
            3.0: "Bajo desempeño (3 pts): Sin innovación ni desarrollo tecnológico"
        }

        map_agua_10 = {
            10.0: "Alto desempeño (10 pts): Excelente presentación y/o trabajo en equipo interdisciplinario fluído",
            7.5: "Desempeño medio (7.5 pts): Presentación comprensible y/o buena colaboración con leves problemas",
            5.0: "Desempeño regular (5 pts): Presentación confusa o poca integración de los miembros",
            2.0: "Bajo desempeño (2 pts): Exposición deficiente o sin trabajo en equipo visible"
        }

        with st.container(border=True):
            st.markdown("#### 1. Rigor Técnico (Máx. 25 pts)")
            agua_c1 = st.radio("Nivel:", [25.0, 18.75, 12.5, 5.0], format_func=lambda x: map_agua_25[x], key="agua_c1")
            agua_obs1 = st.text_area("Observaciones de Rigor Técnico:", key="agua_obs1", height=60)

        with st.container(border=True):
            st.markdown("#### 2. Viabilidad (Máx. 25 pts)")
            agua_c3 = st.radio("Nivel:", [25.0, 18.75, 12.5, 5.0], format_func=lambda x: map_agua_25[x], key="agua_c3")
            agua_obs3 = st.text_area("Observaciones de Viabilidad:", key="agua_obs3", height=60)

        with st.container(border=True):
            st.markdown("#### 3. Innovación (Máx. 15 pts)")
            agua_c2 = st.radio("Nivel:", [15.0, 11.25, 7.5, 3.0], format_func=lambda x: map_agua_15[x], key="agua_c2")
            agua_obs2 = st.text_area("Observaciones de Innovación:", key="agua_obs2", height=60)

        with st.container(border=True):
            st.markdown("#### 4. Desarrollo Tecnológico (Máx. 15 pts)")
            agua_c4 = st.radio("Nivel:", [15.0, 11.25, 7.5, 3.0], format_func=lambda x: map_agua_15[x], key="agua_c4")
            agua_obs4 = st.text_area("Observaciones de Desarrollo Tecnológico:", key="agua_obs4", height=60)

        with st.container(border=True):
            st.markdown("#### 5. Comunicación (Máx. 10 pts)")
            agua_c5 = st.radio("Nivel:", [10.0, 7.5, 5.0, 2.0], format_func=lambda x: map_agua_10[x], key="agua_c5")
            agua_obs5 = st.text_area("Observaciones de Comunicación:", key="agua_obs5", height=60)

        with st.container(border=True):
            st.markdown("#### 6. Trabajo en Equipo (Máx. 10 pts)")
            agua_c6 = st.radio("Nivel:", [10.0, 7.5, 5.0, 2.0], format_func=lambda x: map_agua_10[x], key="agua_c6")
            agua_obs6 = st.text_area("Observaciones de Trabajo en Equipo:", key="agua_obs6", height=60)

        total_score_agua = agua_c1 + agua_c3 + agua_c2 + agua_c4 + agua_c5 + agua_c6

        st.metric(label="🎯 Puntaje Total Ponderado", value=f"{total_score_agua:.2f} / 100.00 pts")

        if st.button("💧 Guardar Evaluación Desafíos del Agua", type="primary", key="btn_save_agua"):
            if not evaluador_agua.strip() or not equipo_agua.strip():
                st.warning("⚠️ Por favor ingresa el Evaluador/a y el Equipo o Proyecto.")
            else:
                eval_respuestas_agua = {
                    "rigor_tecnico_pts": agua_c1, "rigor_tecnico_desc": map_agua_25[agua_c1], "rigor_tecnico_obs": agua_obs1,
                    "viabilidad_pts": agua_c3, "viabilidad_desc": map_agua_25[agua_c3], "viabilidad_obs": agua_obs3,
                    "innovacion_pts": agua_c2, "innovacion_desc": map_agua_15[agua_c2], "innovacion_obs": agua_obs2,
                    "desarrollo_tecnologico_pts": agua_c4, "desarrollo_tecnologico_desc": map_agua_15[agua_c4], "desarrollo_tecnologico_obs": agua_obs4,
                    "comunicacion_pts": agua_c5, "comunicacion_desc": map_agua_10[agua_c5], "comunicacion_obs": agua_obs5,
                    "trabajo_en_equipo_pts": agua_c6, "trabajo_en_equipo_desc": map_agua_10[agua_c6], "trabajo_en_equipo_obs": agua_obs6,
                }

                doc_eval_agua = {
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "evaluador": evaluador_agua,
                    "equipo": equipo_agua,
                    "evento": "Desafíos Científicos del Agua",
                    "promedio": total_score_agua,
                    "respuestas": eval_respuestas_agua
                }
                db.collection("evaluaciones").add(doc_eval_agua)
                st.session_state["eval_agua_guardada_exito"] = True

                keys_agua_limpiar = [
                    "agua_eval", "agua_equipo",
                    "agua_c1", "agua_obs1", "agua_c2", "agua_obs2",
                    "agua_c3", "agua_obs3", "agua_c4", "agua_obs4",
                    "agua_c5", "agua_obs5", "agua_c6", "agua_obs6"
                ]
                for k in keys_agua_limpiar:
                    if k in st.session_state:
                        del st.session_state[k]

                st.rerun()

    elif opcion_agua == "📌 Acreditación Desafíos del Agua":
        st.header("📌 Módulo de Acreditación de Presentes (Desafíos del Agua)")
        st.markdown("Busca al participante por DNI en el padrón o ingresa sus datos manualmente si no se encuentra registrado.")

        dni_agua_acred = st.text_input("Ingresar DNI del Participante a Acreditar", placeholder="Ej: 39098198", key="acred_dni_agua").strip().replace(".", "")

        if dni_agua_acred:
            coincidencias = buscar_estudiantes_por_dni(dni_agua_acred)

            if coincidencias:
                st.success(f"✅ Participante Encontrado en Padrón ({len(coincidencias)} registro/s)")
                idx_agua_sel = 0
                if len(coincidencias) > 1:
                    opciones_agua_acred = [f"Inscripción #{i+1}: {c.get('inscripcion', 'Sin datos')} ({c.get('escuela', '')})" for i, c in enumerate(coincidencias)]
                    idx_agua_sel = st.selectbox("Seleccionar la inscripción a acreditar:", range(len(opciones_agua_acred)), format_func=lambda x: opciones_agua_acred[x], key="sel_agua_acred_multi")

                participante = coincidencias[idx_agua_sel]
                val_nom_ag = participante.get("nombre", "")
                val_esc_ag = participante.get("escuela", "")
                val_insc_ag = participante.get("inscripcion", "")
                val_mail_ag = participante.get("email", "")
                val_doc_ag = participante.get("email_docente", "")
                if val_doc_ag == "Sin Datos":
                    val_doc_ag = ""
                val_esp_ag = participante.get("especialidad", "General")
            else:
                st.info("ℹ️ El DNI no figura en el padrón. Puedes ingresar los datos manualmente a continuación:")
                val_nom_ag = ""
                val_esc_ag = ""
                val_insc_ag = ""
                val_mail_ag = ""
                val_doc_ag = ""
                val_esp_ag = "General"

            with st.container(border=True):
                st.markdown("### ✏️ Datos del Registro Desafíos del Agua")
                col1, col2 = st.columns(2)
                with col1:
                    nombre_agua = st.text_input("Nombre y Apellido*", value=val_nom_ag, key="agua_nom_sel")
                    escuela_agua = st.text_input("Escuela / Institución*", value=val_esc_ag, key="agua_esc_sel")
                    equipo_agua_acred = st.text_input("Proyecto / Inscripción", value=val_insc_ag, key="agua_insc_sel")
                
                with col2:
                    email_agua = st.text_input("Email Participante", value=val_mail_ag, key="agua_mail_sel")
                    email_doc_agua = st.text_input("Mail Tutor / Docente", value=val_doc_ag, placeholder="ejemplo@tutor.edu.ar", key="agua_mail_doc_sel")
                    especialidad_agua_acred = st.text_input("Especialidad", value=val_esp_ag, key="agua_esp_acred_sel")

            if st.button("💧 Confirmar Acreditación Desafíos del Agua", key="acred_agua_btn_sel", type="primary"):
                if not nombre_agua.strip() or not escuela_agua.strip():
                    st.warning("⚠️ Por favor completa el Nombre y la Escuela del participante.")
                else:
                    doc_agua_presente = {
                        "fecha_acreditacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "dni": dni_agua_acred,
                        "estudiante": nombre_agua,
                        "escuela": escuela_agua,
                        "email_estudiante": email_agua,
                        "email_docente": email_doc_agua if email_doc_agua.strip() else "Sin Datos",
                        "inscripcion": equipo_agua_acred,
                        "especialidad": especialidad_agua_acred,
                        "evento": "Desafíos Científicos del Agua"
                    }
                    db.collection("presentes").add(doc_agua_presente)
                    st.success(f"🎉 ¡{nombre_agua} ha sido acreditado/a en los Desafíos del Agua!")

# =========================================================
# ADMINISTRACIÓN Y REPORTES CONSOLIDADOS
# =========================================================
with tab_admin:
    st.header("⚙️ Panel de Administración Consolidado")
    clave = st.text_input("Contraseña Administrador", type="password", key="admin_pass_main")

    if clave == ADMIN_PASSWORD:
        st.success("🔓 Acceso de Administración concedido.")

        evals_raw = [d.to_dict() for d in db.collection("evaluaciones").stream()]
        equipos_raw = [d.to_dict() for d in db.collection("equipos").stream()]
        presentes_raw = [d.to_dict() for d in db.collection("presentes").stream()]

        df_evals = pd.json_normalize(evals_raw) if evals_raw else pd.DataFrame()
        df_equipos = aplanar_equipos(equipos_raw) if equipos_raw else pd.DataFrame()
        df_presentes = pd.DataFrame(presentes_raw) if presentes_raw else pd.DataFrame()

        subtab1, subtab2, subtab3 = st.tabs(["📊 Evaluaciones Registradas", "🔑 Base de Códigos / Equipos", "📌 Lista de Presentes"])
        
        with subtab1:
            if not df_evals.empty:
                st.dataframe(df_evals, use_container_width=True)
            else:
                st.info("No hay evaluaciones registradas aún.")

        with subtab2:
            if not df_equipos.empty:
                st.dataframe(df_equipos, use_container_width=True)
            else:
                st.info("No hay equipos guardados aún.")

        with subtab3:
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
                file_name=f"Reporte_Consolidado_Eventos_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="btn_down_excel"
            )
        with col_d2:
            if not df_evals.empty:
                st.download_button(
                    label="📄 Descargar Evaluaciones (CSV)",
                    data=df_evals.to_csv(index=False).encode("utf-8"),
                    file_name="evaluaciones.csv",
                    mime="text/csv",
                    key="btn_down_csv"
                )
