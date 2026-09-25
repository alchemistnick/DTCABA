import random
from datetime import datetime
import pandas as pd
import requests
import streamlit as st

# ---------------------------------------------------------
# CONFIGURACIÓN DIRECTA DE SERVIDORES Y HOJAS
# ---------------------------------------------------------
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbwpYoAthfaViejGHAAThgQkAllbMrSsxfi-AC6vrcrtUtIeG-VtI5knuGPyGlGZhHl7tA/exec"
WEBHOOK_HACKATHON = "https://script.google.com/macros/s/AKfycbyM8feFteFynfKVBk_L_ypJ6NP08ufGHODv6iGu8v7E8jkUoSRuic54mgPmYfvn2m5gEg/exec"
SHEET_ID_EVALS = "1V5rWEolARQ3PlZTbVrrhEWUc7bipJF0t2iMznxjvKgk"
ADMIN_PASSWORD = "admin123"

CARACTERES_SEGUROS = "BCDFGHJKLMNPQRSTVWXYZ0123456789"

st.set_page_config(
    page_title="Plataforma de Evaluación DTCABA & Hackathon",
    page_icon="🏆",
    layout="centered",
    initial_sidebar_state="expanded",
)

hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# ---------------------------------------------------------
# ESTILOS CSS CON FORZADO TOTAL DE VISIBILIDAD EN SELECTBOX
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Inter', sans-serif; 
    }

    /* BARRA LATERAL (SIDEBAR) BASE */
    section[data-testid="stSidebar"] { 
        background-color: #0F172A !important; 
    }
    section[data-testid="stSidebar"] * { 
        color: #F8FAFC !important; 
    }

    /* CORRECCIÓN DE CONTRASTE TOTAL EN SELECTBOX DE LA BARRA LATERAL */
    section[data-testid="stSidebar"] div[data-baseweb="select"] {
        background-color: #1E293B !important;
        border-radius: 8px !important;
    }
    section[data-testid="stSidebar"] div[data-baseweb="select"] * {
        background-color: transparent !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] div[data-baseweb="select"] [data-testid="stMarkdownContainer"] p {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    /* ENCABEZADO PRINCIPAL HERO */
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

    /* TARJETAS DE CONTENIDO */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: var(--background-secondary, #FFFFFF) !important;
        border-radius: 14px;
        border: 1px solid #CBD5E1 !important;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }

    /* TARJETA MÉTRICA PUNTAJE TOTAL */
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

    /* BOTONES PRINCIPALES */
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
# FUNCIONES AUXILIARES CON CACHÉ
# ---------------------------------------------------------
@st.cache_data(ttl=600, show_spinner=False)
def leer_pestana(sheet_id, nombre_pestana):
    try:
        timestamp = int(datetime.now().timestamp() / 600)
        url_csv = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={nombre_pestana}&t={timestamp}"
        return pd.read_csv(url_csv)
    except Exception:
        return pd.DataFrame()

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

@st.cache_data(ttl=600, show_spinner=False)
def obtener_lista_codigos():
    df_codigos = leer_pestana(SHEET_ID_EVALS, "Base_codigos")
    if not df_codigos.empty and "Codigo_Unico" in df_codigos.columns:
        codigos_limpios = (
            df_codigos["Codigo_Unico"]
            .dropna()
            .astype(str)
            .str.strip()
            .str.upper()
            .unique()
            .tolist()
        )
        codigos_limpios.sort()
        return codigos_limpios
    return []

# ---------------------------------------------------------
# NAVEGACIÓN PRINCIPAL
# ---------------------------------------------------------
st.sidebar.markdown("### ⚙️ Selección de Evento")
evento_seleccionado = st.sidebar.selectbox(
    "Evento", ["📐 Desafíos Técnicos DTCABA", "🏆 Hackathon 2026"]
)

st.sidebar.markdown("### 🧭 Navegación")
if evento_seleccionado == "📐 Desafíos Técnicos DTCABA":
    opcion = st.sidebar.radio(
        "Navegación DTCABA",
        ["Cargar Evaluación DTCABA", "Generar Códigos de Equipos", "📌 Acreditación de Presentes", "Panel de Administración"],
        label_visibility="collapsed",
    )
else:
    opcion = st.sidebar.radio(
        "Navegación Hackathon",
        ["Cargar Evaluación Hackathon", "Panel de Administración"],
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
        lista_codigos = obtener_lista_codigos()

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
                payload = {
                    "action": "evaluacion",
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "codigo_unico": codigo_unico,
                    "materia": materia,
                    "evaluador_id": dni_evaluador,
                    "evaluador_nombre": f"Evaluador DNI {dni_evaluador}",
                    "promedio": puntaje_100,
                    "respuestas": eval_respuestas,
                }
                try:
                    res = requests.post(WEBAPP_URL, json=payload, timeout=10)
                    if res.status_code == 200:
                        st.session_state["exito_msj"] = f"✅ ¡Evaluación del código {codigo_unico} guardada con éxito!"
                        
                        for k in ["eval_dni", "eval_codigo_select", "eval_codigo_manual", "eval_codigo_directo", 
                                  "len_c1", "obs_c1", "len_c2", "obs_c2", "mat_c1", "obs_mat1", "mat_c2", "obs_mat2", "tdr_c1", "obs_tdr1"]:
                            if k in st.session_state:
                                del st.session_state[k]
                        st.rerun()
                except Exception as e:
                    st.error(f"Error al conectar: {e}")

        if "exito_msj" in st.session_state:
            st.success(st.session_state["exito_msj"])
            del st.session_state["exito_msj"]

    elif opcion == "Generar Códigos de Equipos":
        st.header("Generador de Códigos para Equipos / Duplas")
        clave = st.text_input("Contraseña de Acceso", type="password")

        if clave == ADMIN_PASSWORD:
            st.success("🔓 Acceso habilitado.")
            cant_integrantes = st.number_input("Cantidad de Integrantes del Equipo", min_value=1, max_value=8, value=2)
            prefijo = st.selectbox("Materia", ["MAT", "LEN", "TDR1", "TDR2"])

            datos_integrantes = {}
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

                datos_integrantes[f"dni{idx}"] = dni_input
                datos_integrantes[f"estudiante{idx}"] = nom_i
                datos_integrantes[f"escuela{idx}"] = esc_i
                datos_integrantes[f"email{idx}"] = mail_i

            if st.button("🎲 Generar Código de Equipo", type="primary"):
                tres_aleatorios = "".join(random.choices(CARACTERES_SEGUROS, k=3))
                primer_dni = datos_integrantes.get("dni1", "000")
                ultimos_tres = primer_dni[-3:] if len(primer_dni) >= 3 else primer_dni.zfill(3)
                codigo_generado = f"{tres_aleatorios}{ultimos_tres}"

                payload_codigo = {
                    "action": "guardar_codigo_dupla",
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "codigo_unico": codigo_generado,
                    "materia": prefijo,
                    **datos_integrantes
                }

                try:
                    res = requests.post(WEBAPP_URL, json=payload_codigo, timeout=10)
                    if res.status_code == 200:
                        st.success(f"✅ Código Único Generado: **{codigo_generado}**")
                        st.code(codigo_generado, language="text")
                        obtener_lista_codigos.clear()
                except Exception as e:
                    st.error(f"Error de conexión: {e}")

    # ---------------------------------------------------------
    # MÓDULO ACREDITACIÓN DE PRESENTES
    # ---------------------------------------------------------
    elif opcion == "📌 Acreditación de Presentes":
        st.header("📌 Módulo de Acreditación de Presentes al Evento")
        st.markdown("Busca al estudiante por DNI para verificar e ingresar o modificar sus datos antes de confirmar el presente.")

        dni_acreditar = st.text_input("Ingresar DNI del Estudiante a Acreditar", placeholder="Ej: 39098198").strip().replace(".", "")

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
                            st.text_input("Fecha Registro Padrón (Solo Lectura)", value=estudiante.get("fecha", ""), disabled=True, key=f"acred_fch_{idx}")

                        if st.button(f"✅ Confirmar Presente con Datos Actualizados - Reg #{idx+1}", key=f"acreditar_{idx}", type="primary"):
                            payload_presente = {
                                "action": "marcar_presente",
                                "fecha_acreditacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "dni": dni_acreditar,
                                "estudiante": nombre_edit,
                                "escuela": escuela_edit,
                                "email_estudiante": email_est_edit,
                                "email_docente": email_doc_edit if email_doc_edit.strip() else "Sin Datos",
                                "inscripcion": inscripcion_edit,
                                "nivel": nivel_edit
                            }
                            try:
                                res = requests.post(WEBAPP_URL, json=payload_presente, timeout=10)
                                if res.status_code == 200:
                                    st.success(f"🎉 ¡{nombre_edit} ha sido acreditado/a con éxito!")
                                else:
                                    st.error("Error al registrar el presente en Google Sheets.")
                            except Exception as e:
                                st.error(f"Error de conexión: {e}")
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
            col1, col2 = st.columns(2)
            with col1:
                evaluador = st.text_input("Evaluador*", placeholder="Ej. Gustavo", key="hk_eval")
            with col2:
                equipo = st.text_input("Equipo / Proyecto*", placeholder="Ej. Nicolas", key="hk_equipo")

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
            c4 = st.radio("Nivel:", [15, 10, 5, 0], format_func=lambda x: map_10[x], key="hk_4")

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
                payload = {
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "evaluador": evaluador,
                    "equipo": equipo,
                    "escenario": c1,
                    "infraestructura_energia": c2,
                    "comunicacion_info": c3,
                    "coordinacion_logistica": c4,
                    "atencion_poblacion": c5,
                    "operacion_emergencia": c6,
                    "enfoque_interdisciplinario": c7,
                    "puntaje_total": total_score,
                    "observaciones": observaciones
                }
                try:
                    res = requests.post(WEBHOOK_HACKATHON, json=payload, timeout=10)
                    if res.status_code in [200, 201]:
                        st.session_state["exito_msj_hk"] = f"✅ ¡Evaluación del equipo '{equipo}' guardada correctamente!"
                        
                        for k in ["hk_eval", "hk_equipo", "hk_1", "hk_2", "hk_3", "hk_4", "hk_5", "hk_6", "hk_7", "hk_obs"]:
                            if k in st.session_state:
                                del st.session_state[k]
                        st.rerun()
                except Exception as e:
                    st.error(f"Error de conexión: {e}")

        if "exito_msj_hk" in st.session_state:
            st.success(st.session_state["exito_msj_hk"])
            st.balloons()
            del st.session_state["exito_msj_hk"]

# ---------------------------------------------------------
# PANEL DE ADMINISTRACIÓN COMPARTIDO
# ---------------------------------------------------------
if opcion == "Panel de Administración":
    st.header("Panel de Administración")
    clave = st.text_input("Contraseña Administrador", type="password")

    if clave == ADMIN_PASSWORD:
        tab1, tab2, tab3 = st.tabs(["📊 Evaluaciones DTCABA", "🔑 Base de Códigos DTCABA", "📌 Lista de Presentes"])
        with tab1:
            df_evals = leer_pestana(SHEET_ID_EVALS, "Evaluaciones")
            if not df_evals.empty:
                st.dataframe(df_evals, use_container_width=True)
            else:
                st.info("No hay evaluaciones registradas aún.")

        with tab2:
            df_codigos = leer_pestana(SHEET_ID_EVALS, "Base_codigos")
            if not df_codigos.empty:
                st.dataframe(df_codigos, use_container_width=True)
            else:
                st.info("No hay códigos guardados aún.")

        with tab3:
            df_presentes = leer_pestana(SHEET_ID_EVALS, "Acreditados_Presentes")
            if not df_presentes.empty:
                st.dataframe(df_presentes, use_container_width=True)
            else:
                st.info("No hay asistentes acreditados aún.")
