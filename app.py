from datetime import datetime
import io
import random
import pandas as pd
import requests
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# ---------------------------------------------------------
# CONFIGURACIÓN E INICIALIZACIÓN DE FIREBASE Y WEBAPP
# ---------------------------------------------------------
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwpYoAthfaViejGHAAThgQkAllbMrSsxfi-AC6vrcrtUtIeG-VtI5knuGPyGlGZhHl7tA/exec"
ADMIN_PASSWORD = "admin123"

CARACTERES_SEGUROS = "BCDFGHJKLMNPQRSTVWXYZ0123456789"

ESPECIALIDADES = [
    "Computación / Informática",
    "Electrónica",
    "Electromecánica",
    "Química",
    "Construcciones",
    "Automotores",
    "General / Otra"
]

st.set_page_config(
    page_title="Plataforma de Evaluación DTCABA & Hackathon",
    page_icon="🏆",
    layout="centered",
    initial_sidebar_state="expanded",
)

# Inicializar Firebase Admin SDK
if not firebase_admin._apps:
    try:
        if "firebase" in st.secrets:
            cred_dict = dict(st.secrets["firebase"])
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
# FUNCIONES AUXILIARES (PADRÓN OFICIAL VIA WEBAPP)
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

def generar_excel_descarga(dict_dfs):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet_name, df in dict_dfs.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
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

        if materia == "Lengua":
            map_len1 = {4: "4 - Avanzado", 3: "3 - Satisfactorio", 2: "2 - En desarrollo", 1: "1 - Inicial"}
            c1 = st.radio("Apropiación del texto fuente (20%):", [4, 3, 2, 1], format_func=lambda x: map_len1[x], key="len_c1")
            obs1 = st.text_area("Observaciones:", key="obs_c1", height=70)

            c2 = st.radio("Transformación del género (20%):", [4, 3, 2, 1], format_func=lambda x: map_len1[x], key="len_c2")
            obs2 = st.text_area("Observaciones:", key="obs_c2", height=70)

            puntaje_100 = round((((c1 * 0.5) + (c2 * 0.5)) / 4) * 100, 2)
            eval_respuestas = {"c1_desc": map_len1[c1], "obs1": obs1, "c2_desc": map_len1[c2], "obs2": obs2}

        elif materia == "Matemática":
            map_mat1 = {5: "5 - Destacado", 4: "4 - Avanzado", 3: "3 - Satisfactorio", 2: "2 - Básico", 1: "1 - Inicial"}
            c1 = st.radio("Construcción y Representación (50%):", [5, 4, 3, 2, 1], format_func=lambda x: map_mat1[x], key="mat_c1")
            obs1 = st.text_area("Observaciones:", key="obs_mat1", height=70)

            c2 = st.radio("Resolución del Problema (50%):", [5, 4, 3, 2, 1], format_func=lambda x: map_mat1[x], key="mat_c2")
            obs2 = st.text_area("Observaciones:", key="obs_mat2", height=70)

            puntaje_100 = round((((c1 * 0.5) + (c2 * 0.5)) / 5) * 100, 2)
            eval_respuestas = {"c1_desc": map_mat1[c1], "obs1": obs1, "c2_desc": map_mat1[c2], "obs2": obs2}
        else:
            c1 = st.radio("Nivel Gráfico (100%):", [4, 3, 2, 1], key="tdr_c1")
            obs1 = st.text_area("Observaciones:", key="obs_tdr1", height=70)
            puntaje_100 = round((c1 / 4) * 100, 2)
            eval_respuestas = {"c1_desc": f"Nivel {c1}", "obs1": obs1}

        st.metric(label="Puntaje Total", value=f"{puntaje_100} / 100 pts")

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

    # ---------------------------------------------------------
    # GENERACIÓN DE EQUIPOS CON BÚSQUEDA AUTOMÁTICA EN PADRÓN OFICIAL
    # ---------------------------------------------------------
    elif opcion == "Generar Códigos de Equipos":
        st.header("Generador de Códigos para Equipos / Duplas")
        clave = st.text_input("Contraseña de Acceso", type="password")

        if clave == ADMIN_PASSWORD:
            st.success("🔓 Acceso habilitado.")
            cant_integrantes = st.number_input("Cantidad de Integrantes del Equipo", min_value=1, max_value=10, value=2)
            prefijo = st.selectbox("Materia / Categoría", ["MAT", "LEN", "TDR1", "TDR2", "HACKATHON"])
            especialidad_eq = st.selectbox("Especialidad Técnica", ESPECIALIDADES)

            datos_integrantes = []
            for idx in range(1, cant_integrantes + 1):
                st.subheader(f"👤 Integrante {idx}")
                dni_input = st.text_input(f"DNI Integrante {idx}", key=f"dni_{idx}_input").strip().replace(".", "")

                if dni_input:
                    coincidencias = buscar_estudiantes_por_dni(dni_input)
                    if len(coincidencias) >= 1:
                        c = coincidencias[0]
                        st.success(f"✅ Encontrado en padrón: {c.get('nombre','')}")
                        if f"nom_{idx}" not in st.session_state or not st.session_state[f"nom_{idx}"]:
                            st.session_state[f"nom_{idx}"] = c.get("nombre", "")
                        if f"esc_{idx}" not in st.session_state or not st.session_state[f"esc_{idx}"]:
                            st.session_state[f"esc_{idx}"] = c.get("escuela", "")
                        if f"mail_{idx}" not in st.session_state or not st.session_state[f"mail_{idx}"]:
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

            if st.button("🎲 Generar Código de Equipo", type="primary"):
                tres_aleatorios = "".join(random.choices(CARACTERES_SEGUROS, k=3))
                primer_dni = datos_integrantes[0]["dni"] if datos_integrantes else "000"
                ultimos_tres = primer_dni[-3:] if len(primer_dni) >= 3 else primer_dni.zfill(3)
                codigo_generado = f"{tres_aleatorios}{ultimos_tres}"

                doc_equipo = {
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "codigo_unico": codigo_generado,
                    "materia": prefijo,
                    "especialidad": especialidad_eq,
                    "evento": "DTCABA",
                    "integrantes": datos_integrantes
                }
                db.collection("equipos").add(doc_equipo)
                st.success(f"✅ Código Único Generado: **{codigo_generado}**")
                st.code(codigo_generado, language="text")

    elif opcion == "📌 Acreditación de Presentes":
        st.header("📌 Acreditación de Presentes (DTCABA)")
        st.markdown("Busca al estudiante por DNI para verificar e ingresar o modificar sus datos antes de confirmar el presente.")

        dni_acreditar = st.text_input("Ingresar DNI del Estudiante a Acreditar", placeholder="Ej: 39098198", key="acred_dni_dtcaba").strip().replace(".", "")

        if dni_acreditar:
            coincidencias = buscar_estudiantes_por_dni(dni_acreditar)

            if coincidencias:
                st.success(f"✅ Estudiante Encontrado ({len(coincidencias)} inscripción/es detectada/s)")
                
                for idx, estudiante in enumerate(coincidencias):
                    with st.container(border=True):
                        st.markdown(f"### ✏️ Editar / Validar Registro #{idx+1}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            nombre_edit = st.text_input("Nombre y Apellido", value=estudiante.get("nombre", ""), key=f"acred_nom_{idx}")
                            escuela_edit = st.text_input("Escuela", value=estudiante.get("escuela", ""), key=f"acred_esc_{idx}")
                            inscripcion_edit = st.text_input("Desafío / Inscripción", value=estudiante.get("inscripcion", ""), key=f"acred_insc_{idx}")
                            nivel_edit = st.text_input("Nivel", value=estudiante.get("nivel", ""), key=f"acred_niv_{idx}")
                        
                        with col2:
                            email_est_edit = st.text_input("Email Estudiante", value=estudiante.get("email", ""), key=f"acred_mail_est_{idx}")
                            docente_mail_val = estudiante.get("email_docente", "")
                            if docente_mail_val == "Sin Datos":
                                docente_mail_val = ""
                            email_doc_edit = st.text_input("Mail Docente / Acompañante", value=docente_mail_val, placeholder="ejemplo@docente.edu.ar", key=f"acred_mail_doc_{idx}")
                            especialidad_edit = st.selectbox("Especialidad Técnica", ESPECIALIDADES, key=f"acred_esp_{idx}")

                        if st.button(f"✅ Confirmar Presente DTCABA - Reg #{idx+1}", key=f"acreditar_{idx}", type="primary"):
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
# EVENTO 2: HACKATHON 2026 (RÚBRICA COMPLETA Y ORIGINAL)
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
                especialidad_hk = st.selectbox("Especialidad Proyecto", ESPECIALIDADES, key="hk_esp")

        st.subheader("📊 Criterios de Evaluación")

        map_15 = {
            15: "15 - Excelente (Supera ampliamente las expectativas)",
            10: "10 - Satisfactorio (Cumple correctamente con el criterio)",
            5: "5 - En Desarrollo (Presenta aspectos incompletos)",
            0: "0 - Inicial (No cumple con el criterio)"
        }

        map_10 = {
            10: "10 - Excelente (Integración total y profunda)",
            5: "5 - Satisfactorio (Integración parcial de disciplinas)",
            0: "0 - Inicial (Sin enfoque interdisciplinario)"
        }

        with st.container(border=True):
            st.markdown("#### 1. Escenario (Máx. 15 pts)")
            c1 = st.radio("Nivel:", [15, 10, 5, 0], format_func=lambda x: map_15[x], key="hk_1")

        with st.container(border=True):
            st.markdown("#### 2. Infraestructura y Energía (Máx. 15 pts)")
            c2 = st.radio("Nivel:", [15, 10, 5, 0], format_func=lambda x: map_15[x], key="hk_2")

        with st.container(border=True):
            st.markdown("#### 3. Comunicación e Información (Máx. 15 pts)")
            c3 = st.radio("Nivel:", [15, 10, 5, 0], format_func=lambda x: map_15[x], key="hk_3")

        with st.container(border=True):
            st.markdown("#### 4. Coordinación y Logística (Máx. 15 pts)")
            c4 = st.radio("Nivel:", [15, 10, 5, 0], format_func=lambda x: map_15[x], key="hk_4")

        with st.container(border=True):
            st.markdown("#### 5. Atención a la Población (Máx. 15 pts)")
            c5 = st.radio("Nivel:", [15, 10, 5, 0], format_func=lambda x: map_15[x], key="hk_5")

        with st.container(border=True):
            st.markdown("#### 6. Operación de Emergencia (Máx. 15 pts)")
            c6 = st.radio("Nivel:", [15, 10, 5, 0], format_func=lambda x: map_15[x], key="hk_6")

        with st.container(border=True):
            st.markdown("#### 7. Enfoque Interdisciplinario (Máx. 10 pts)")
            c7 = st.radio("Nivel:", [10, 5, 0], format_func=lambda x: map_10[x], key="hk_7")

        total_score = c1 + c2 + c3 + c4 + c5 + c6 + c7
        st.metric(label="🎯 Puntaje Total Hackathon", value=f"{total_score} / 100 pts")

        with st.container(border=True):
            observaciones = st.text_area("💬 Observaciones / Justificación", placeholder="Escribe tus comentarios...", key="hk_obs", height=100)

        if st.button("🚀 Guardar Evaluación Hackathon", type="primary"):
            if not evaluador.strip() or not equipo.strip():
                st.warning("⚠️ Por favor completa el Evaluador y el Equipo.")
            else:
                doc_eval_hk = {
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "evaluador": evaluador,
                    "equipo": equipo,
                    "evento": "Hackathon 2026",
                    "especialidad": especialidad_hk,
                    "escenario": c1,
                    "infraestructura_energia": c2,
                    "comunicacion_info": c3,
                    "coordinacion_logistica": c4,
                    "atencion_poblacion": c5,
                    "operacion_emergencia": c6,
                    "enfoque_interdisciplinario": c7,
                    "promedio": total_score,
                    "observaciones": observaciones
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
                
                for idx, participante in enumerate(coincidencias):
                    with st.container(border=True):
                        st.markdown(f"### ✏️ Validar Registro Hackathon #{idx+1}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            nombre_hk = st.text_input("Nombre y Apellido", value=participante.get("nombre", ""), key=f"hk_nom_{idx}")
                            escuela_hk = st.text_input("Escuela / Institución", value=participante.get("escuela", ""), key=f"hk_esc_{idx}")
                            equipo_hk = st.text_input("Equipo / Proyecto / Inscripción", value=participante.get("inscripcion", ""), key=f"hk_insc_{idx}")
                        
                        with col2:
                            email_hk = st.text_input("Email Participante", value=participante.get("email", ""), key=f"hk_mail_{idx}")
                            docente_hk = participante.get("email_docente", "")
                            if docente_hk == "Sin Datos":
                                docente_hk = ""
                            email_doc_hk = st.text_input("Mail Tutor / Docente", value=docente_hk, placeholder="ejemplo@tutor.edu.ar", key=f"hk_mail_doc_{idx}")
                            especialidad_hk_acred = st.selectbox("Especialidad Técnica", ESPECIALIDADES, key=f"hk_esp_acred_{idx}")

                        if st.button(f"🚀 Confirmar Acreditación Hackathon - Reg #{idx+1}", key=f"acred_hk_btn_{idx}", type="primary"):
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

        evals_data = [d.to_dict() for d in db.collection("evaluaciones").stream()]
        equipos_data = [d.to_dict() for d in db.collection("equipos").stream()]
        presentes_data = [d.to_dict() for d in db.collection("presentes").stream()]

        df_evals = pd.DataFrame(evals_data) if evals_data else pd.DataFrame()
        df_equipos = pd.DataFrame(equipos_data) if equipos_data else pd.DataFrame()
        df_presentes = pd.DataFrame(presentes_data) if presentes_data else pd.DataFrame()

        tab1, tab2, tab3 = st.tabs(["📊 Evaluaciones Registradas", "🔑 Base de Códigos / Equipos", "📌 Lista de Presentes"])
        with tab1:
            st.dataframe(df_evals, use_container_width=True) if not df_evals.empty else st.info("No hay evaluaciones registradas aún.")
        with tab2:
            st.dataframe(df_equipos, use_container_width=True) if not df_equipos.empty else st.info("No hay equipos guardados aún.")
        with tab3:
            st.dataframe(df_presentes, use_container_width=True) if not df_presentes.empty else st.info("No hay asistentes acreditados aún.")

        st.markdown("---")
        st.subheader("📥 Exportar Datos a Excel / CSV")

        dict_export = {
            "Evaluaciones": df_evals,
            "Equipos": df_equipos,
            "Presentes_Acreditados": df_presentes
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
