import random
from datetime import datetime
import pandas as pd
import requests
import streamlit as st

# ---------------------------------------------------------
# CONFIGURACIÓN DIRECTA DE SERVIDORES Y HOJAS
# ---------------------------------------------------------
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzAvwbkuokN3MaAkpg5DTdLV5UbhuBNg8zN-hFJTX4rDtKpPE7GzyUpBj759PHaechNrQ/exec"
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
# ESTILOS ADAPTABLES COMPATIBLES CON MODO OSCURO Y MODO CLARO
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] { 
        font-family: 'Inter', sans-serif; 
    }

    /* Variables Tema Claro por Defecto */
    :root {
        --primary-btn: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%);
        --header-bg: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        --card-bg: #FFFFFF;
        --card-border: #CBD5E1;
        --text-color: #0F172A;
        --metric-bg: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
    }

    /* Variables Tema Oscuro Automático */
    @media (prefers-color-scheme: dark) {
        :root {
            --primary-btn: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%);
            --header-bg: linear-gradient(135deg, #020617 0%, #0F172A 100%);
            --card-bg: #1E293B;
            --card-border: #334155;
            --text-color: #F8FAFC;
            --metric-bg: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        }
    }

    /* Header Principal */
    .app-header {
        background: var(--header-bg);
        padding: 1.5rem 2rem; 
        border-radius: 16px; 
        margin-bottom: 2rem; 
        color: #FFFFFF !important; 
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
        margin: 0.3rem 0 0 0; 
        color: #94A3B8 !important; 
    }

    /* Tarjetas de Contenido (Adapta texto e interior al modo oscuro) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: var(--card-bg) !important;
        border-radius: 14px;
        border: 1px solid var(--card-border) !important;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] *,
    .stRadio label, .stMarkdown p, .stMarkdown h3, .stMarkdown h4 {
        color: var(--text-color) !important;
    }

    /* Métrica de Puntaje Total */
    div[data-testid="stMetric"] {
        background: var(--metric-bg) !important;
        padding: 1.2rem 1.8rem;
        border-radius: 12px;
        border: 1px solid var(--card-border) !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        text-align: center;
        margin: 1.5rem 0;
    }
    div[data-testid="stMetric"] label {
        color: var(--text-color) !important;
        font-weight: 600;
    }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #38BDF8 !important;
        font-weight: 800;
    }

    /* Botón Principal */
    .stButton > button[kind="primary"] {
        background: var(--primary-btn) !important;
        color: #FFFFFF !important; 
        border: none; 
        border-radius: 10px; 
        padding: 0.75rem 1.5rem; 
        font-weight: 600; 
        width: 100%;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }

    /* Sidebar Oscura Estilizada */
    section[data-testid="stSidebar"] { 
        background-color: #020617 !important; 
    }
    section[data-testid="stSidebar"] * { 
        color: #F8FAFC !important; 
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
        ["Cargar Evaluación DTCABA", "Generar Códigos de Equipos", "Panel de Administración"],
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
            <h1>📐 Desafíos Técnicos DTCABA⚙️</h1>
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
                dni_i = st.text_input(f"DNI Integrante {idx}", key=f"dni_{idx}").strip().replace(".", "")
                
                n_def, esc_def, mail_def, punt_def, niv_def, insc_def = "", "", "", "N/A", "N/A", "N/A"
                if dni_i:
                    coincidencias = buscar_estudiantes_por_dni(dni_i)
                    if len(coincidencias) >= 1:
                        c = coincidencias[0]
                        st.success(f"✅ Encontrado en padrón: {c.get('nombre','')}")
                        n_def, esc_def, mail_def, punt_def, niv_def, insc_def = (
                            c.get("nombre", ""), c.get("escuela", ""), c.get("email", ""),
                            c.get("puntaje_anterior", "N/A"), c.get("nivel", "N/A"), c.get("inscripcion", "N/A")
                        )

                nom_i = st.text_input(f"Nombre Integrante {idx}", value=n_def, key=f"nom_{idx}")
                esc_i = st.text_input(f"Escuela Integrante {idx}", value=esc_def, key=f"esc_{idx}")
                mail_i = st.text_input(f"Email Integrante {idx}", value=mail_def, key=f"mail_{idx}")

                datos_integrantes[f"dni{idx}"] = dni_i
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
# EVENTO 2: HACKATHON 2026 (FORMATO DE RÚBRICA CON TARJETAS Y RADIO)
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

        # Mapas de Opciones para las Rúbricas
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
                        
                        # RESETEO DE CAMPOS TRAS GUARDADO
                        for k in ["hk_eval", "hk_equipo", "hk_1", "hk_2", "hk_3", "hk_4", "hk_5", "hk_6", "hk_7", "hk_obs"]:
                            if k in st.session_state:
                                del st.session_state[k]
                        st.rerun()
                except Exception as e:
                    st.error(f"Error de conexión: {e}")

        # Mensaje de confirmación colocado en la parte inferior
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
        tab1, tab2 = st.tabs(["📊 Evaluaciones DTCABA", "🔑 Base de Códigos DTCABA"])
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
