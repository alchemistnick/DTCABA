import random
import string
from datetime import datetime
import pandas as pd
import requests
import streamlit as st

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzDxDQ_I18Esy5--by666YGaMKQ_VWve9SC80kIOh83Ib6hWaJbfWs8evzu1Eok0in45Q/exec"
SHEET_ID_EVALS = "1V5rWEolARQ3PlZTbVrrhEWUc7bipJF0t2iMznxjvKgk"

CARACTERES_SEGUROS = "BCDFGHJKLMNPQRSTVWXYZ0123456789"

st.set_page_config(
    page_title="Evaluaciones DTCABA 2026",
    page_icon="🧑‍🔧",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# ESTILOS (Adaptado para Modo Claro y Modo Oscuro móvil)
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Variables Modo Claro */
    :root {
        --primary: #4F46E5;
        --primary-dark: #3730A3;
        --accent: #06B6D4;
        --bg-app: linear-gradient(180deg, #F5F6FB 0%, #EEF1FA 100%);
        --bg-card: #FFFFFF;
        --bg-input: #F9FAFB;
        --bg-chip: #F3F4F6;
        --bg-chip-hover: #EEF0FF;
        --border-color: #E5E7EB;
        --text-main: #1F2937;
        --text-muted: #4B5563;
        --header-title: #FFFFFF;
        --header-sub: #E0E7FF;
    }

    /* Variables Modo Oscuro */
    @media (prefers-color-scheme: dark) {
        :root {
            --primary: #6366F1;
            --primary-dark: #4F46E5;
            --accent: #22D3EE;
            --bg-app: #0F172A;
            --bg-card: #1E293B;
            --bg-input: #0F172A;
            --bg-chip: #334155;
            --bg-chip-hover: #475569;
            --border-color: #334155;
            --text-main: #F8FAFC;
            --text-muted: #CBD5E1;
            --header-title: #FFFFFF;
            --header-sub: #E2E8F0;
        }
    }

    /* Override Streamlit Dark Theme */
    [data-theme="dark"] {
        --primary: #6366F1;
        --primary-dark: #4F46E5;
        --accent: #22D3EE;
        --bg-app: #0F172A;
        --bg-card: #1E293B;
        --bg-input: #0F172A;
        --bg-chip: #334155;
        --bg-chip-hover: #475569;
        --border-color: #334155;
        --text-main: #F8FAFC;
        --text-muted: #CBD5E1;
        --header-title: #FFFFFF;
        --header-sub: #E2E8F0;
    }

    .stApp {
        background: var(--bg-app) !important;
    }

    /* Encabezado principal */
    .app-header {
        background: linear-gradient(135deg, var(--primary) 0%, #312E81 100%);
        padding: 2.2rem 1.5rem 1.8rem 1.5rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        box-shadow: 0 10px 28px rgba(0, 0, 0, 0.25);
        color: white;
        text-align: center;
    }
    .app-header h1 {
        font-family: 'Poppins', sans-serif;
        font-size: 2.8rem;
        font-weight: 800;
        margin: 0 0 0.4rem 0;
        color: var(--header-title) !important;
        letter-spacing: -1px;
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }
    .app-header p {
        margin: 0 0 0.2rem 0;
        color: var(--header-sub) !important;
        font-size: 1.1rem;
        font-weight: 500;
    }
    .app-header .sub-caption {
        font-size: 0.92rem;
        color: #C7D2FE !important;
        margin-top: 0.2rem;
    }

    /* Títulos de sección */
    h2, [data-testid="stHeader"] h2 {
        font-family: 'Poppins', sans-serif !important;
        font-weight: 700 !important;
        font-size: 2rem !important;
        color: var(--text-main) !important;
        border-left: 5px solid var(--primary);
        padding-left: 0.7rem;
        margin-top: 1.2rem !important;
    }
    h3, [data-testid="stHeader"] h3 {
        font-family: 'Poppins', sans-serif !important;
        color: var(--text-main) !important;
        font-weight: 600 !important;
    }

    /* Tarjetas contenedoras */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--bg-card) !important;
        border-radius: 16px;
        border: 1px solid var(--border-color) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }

    /* Textos generales del cuerpo */
    .stApp p, .stApp span, .stApp label, .stApp div {
        color: var(--text-main);
    }

    /* Inputs de texto y selectbox */
    div[data-baseweb="input"] input,
    div[data-baseweb="select"] > div,
    textarea {
        background-color: var(--bg-input) !important;
        color: var(--text-main) !important;
        border-radius: 10px !important;
        border: 1.5px solid var(--border-color) !important;
    }
    div[data-baseweb="input"] input:focus {
        border-color: var(--primary) !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.25) !important;
    }

    /* Radio horizontal (rúbrica) */
    div[role="radiogroup"] {
        gap: 0.5rem;
    }
    div[role="radiogroup"] label {
        background: var(--bg-chip) !important;
        border: 1.5px solid var(--border-color) !important;
        border-radius: 10px;
        padding: 0.4rem 1rem !important;
        margin-right: 0.3rem;
        transition: all 0.15s ease;
    }
    div[role="radiogroup"] label p {
        color: var(--text-main) !important;
        font-weight: 600;
    }
    div[role="radiogroup"] label:hover {
        border-color: var(--primary) !important;
        background: var(--bg-chip-hover) !important;
    }

    /* Botones primarios */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%) !important;
        color: #FFFFFF !important;
        border: none;
        border-radius: 12px;
        padding: 0.65rem 1.5rem;
        font-weight: 600;
        letter-spacing: 0.2px;
        box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
        transition: transform 0.12s ease, box-shadow 0.12s ease;
    }
    .stButton > button[kind="primary"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 18px rgba(99, 102, 241, 0.45);
    }

    /* Sidebar (Fuerza color blanco para el menú lateral) */
    section[data-testid="stSidebar"] {
        background: #1E1B4B !important;
    }
    section[data-testid="stSidebar"] h3 {
        color: #FFFFFF !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        background: rgba(255, 255, 255, 0.12) !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        border-radius: 10px;
        padding: 0.6rem 0.9rem !important;
        margin-bottom: 0.4rem;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label * {
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background: rgba(255, 255, 255, 0.25) !important;
    }

    /* Métricas */
    div[data-testid="stMetric"] {
        background: var(--bg-card) !important;
        border-radius: 14px;
        padding: 0.8rem 1rem;
        border: 1px solid var(--border-color) !important;
    }

    /* Dataframes */
    div[data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid var(--border-color) !important;
        background-color: var(--bg-card) !important;
    }

    /* Divider */
    hr {
        border-color: var(--border-color) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# ENCABEZADO
# ---------------------------------------------------------
st.markdown(
    """
    <div class="app-header">
        <h1>🧑‍🔧 Desafíos Técnicos</h1>
        <p>Plataforma de evaluación y gestión</p>
        <p class="sub-caption">Dirección de Educación Técnica · CABA 2026</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.markdown("### 🧭 Navegación")
opcion = st.sidebar.radio(
    "Navegación",
    ["Cargar Evaluación", "Generar Códigos Únicos", "Panel de Administración"],
    label_visibility="collapsed",
)


# Optimización con caché de Streamlit para accesos concurrentes de múltiples usuarios
@st.cache_data(ttl=15, show_spinner=False)
def leer_pestana(sheet_id, nombre_pestana):
  try:
    timestamp = int(datetime.now().timestamp())
    url_csv = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={nombre_pestana}&t={timestamp}"
    return pd.read_csv(url_csv)
  except Exception:
    return pd.DataFrame()


def buscar_estudiantes_por_dni(dni_búsqueda):
  try:
    payload = {"action": "buscar_dni", "dni": str(dni_búsqueda)}
    res = requests.post(WEBAPP_URL, json=payload, timeout=10)
    if res.status_code == 200:
      data = res.json()
      if data.get("status") == "success":
        return data.get("coincidencias", [])
  except Exception as e:
    st.error(f"Error al conectar con el motor de búsqueda: {e}")
  return []


# ---------------------------------------------------------
# 1. CARGAR EVALUACIÓN (RÚBRICA DINÁMICA POR MATERIA)
# ---------------------------------------------------------
if opcion == "Cargar Evaluación":
  st.header("Carga de Evaluación")

  with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
      id_evaluador = st.text_input(
          "ID / Email del Evaluador", placeholder="Ej: EVAL-001 o email"
      ).strip()
    with col2:
      codigo_unico = st.text_input(
          "Código Único del Examen", placeholder="Ej: MAT-2026-X8K9"
      ).strip()

    materia = st.selectbox(
        "Materia",
        [
            "Matemática",
            "Lengua",
            "Tecnología de la Representación Nivel 1",
            "Tecnología de la Representación Nivel 2",
        ],
    )

  st.subheader(f"📋 Rúbrica de Evaluación: {materia}")

  # Definición adaptativa de criterios según la materia elegida
  if materia == "Matemática":
    label_c1 = (
        "Criterio 1: Planteo y Razonamiento (Estrategias de resolución y"
        " lógica)"
    )
    label_c2 = (
        "Criterio 2: Operatoria y Precisión (Cálculos y desarrollo algebraico)"
    )
    label_c3 = (
        "Criterio 3: Interpretación de Resultados (Conclusiones y respuestas"
        " contextualizadas)"
    )

  elif materia == "Lengua":
    label_c1 = (
        "Criterio 1: Comprensión Lectora y Coherencia (Análisis y sentido del"
        " texto)"
    )
    label_c2 = (
        "Criterio 2: Cohesión y Estructuración (Organización de párrafos y"
        " conectores)"
    )
    label_c3 = (
        "Criterio 3: Ortografía y Gramática (Normativa, puntuación y vocabulario)"
    )

  elif materia == "Tecnología de la Representación Nivel 1":
    label_c1 = (
        "Criterio 1: Normalización Básica (Uso de líneas, acotación y escalas)"
    )
    label_c2 = (
        "Criterio 2: Proyección y Visualización Ortogonal (Vistas principales y"
        " trazado)"
    )
    label_c3 = (
        "Criterio 3: Prolijidad y Calidad Gráfica (Legibilidad y presentación"
        " técnica)"
    )

  else:  # Tecnología de la Representación Nivel 2
    label_c1 = (
        "Criterio 1: Modelado / Vistas Complejas (Cortes, secciones y detalles)"
    )
    label_c2 = (
        "Criterio 2: Aplicación Avanzada de Normas (Tolerancias, simbología y"
        " especificaciones)"
    )
    label_c3 = (
        "Criterio 3: Interpretación y Resolución de Conjuntos (Planos de"
        " despiece o ensamble)"
    )

  # Renderizado dinámico de la rúbrica
  with st.container(border=True):
    c1 = st.radio(label_c1, [1, 2, 3, 4], horizontal=True)
    st.divider()
    c2 = st.radio(label_c2, [1, 2, 3, 4], horizontal=True)
    st.divider()
    c3 = st.radio(label_c3, [1, 2, 3, 4], horizontal=True)

  if st.button("💾 Guardar en Google Sheets", type="primary"):
    if not id_evaluador or not codigo_unico:
      st.warning("⚠️ Completa el ID de evaluador y el Código Único.")
    else:
      with st.spinner("Validando evaluador y código de examen..."):
        payload_val = {
            "action": "validar_evaluacion",
            "id_evaluador": id_evaluador,
            "codigo_unico": codigo_unico,
        }
        res_val = requests.post(WEBAPP_URL, json=payload_val, timeout=10)

      if res_val.status_code == 200:
        datos_val = res_val.json()

        evaluador_valido = datos_val.get("evaluador_valido", False)
        nombre_evaluador = datos_val.get("nombre_evaluador", "")
        codigo_valido = datos_val.get("codigo_valido", False)

        if not evaluador_valido:
          st.error(
              "❌ ID / Email de evaluador no registrado o no autorizado en la"
              " pestaña 'Usuarios'."
          )
        elif not codigo_valido:
          st.error(
              "❌ Código Único de examen inexistente en la pestaña"
              " 'Base_codigos'."
          )
        else:
          st.success(
              f"✅ **Datos Validados**: Evaluador **{nombre_evaluador}** | Examen"
              f" Anónimo **{codigo_unico}** Habilitado"
          )

          # ---------------------------------------------------------
          # CÁLCULO DEL PROMEDIO DIFERENCIADO SEGÚN LA MATERIA
          # ---------------------------------------------------------
          if materia == "Matemática":
            promedio_calculado = round((c1 + c2 + c3) / 3, 2)

          elif materia == "Lengua":
            promedio_calculado = round((c1 + c2 + c3) / 3, 2)

          elif materia == "Tecnología de la Representación Nivel 1":
            promedio_calculado = round((c1 + c2 + c3) / 3, 2)

          elif materia == "Tecnología de la Representación Nivel 2":
            promedio_calculado = round((c1 + c2 + c3) / 3, 2)

          else:
            promedio_calculado = round((c1 + c2 + c3) / 3, 2)

          payload = {
              "action": "evaluacion",
              "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              "codigo_unico": codigo_unico,
              "materia": materia,
              "evaluador_id": id_evaluador,
              "evaluador_nombre": nombre_evaluador,
              "c1": c1,
              "c2": c2,
              "c3": c3,
              "promedio": promedio_calculado,
          }

          res = requests.post(WEBAPP_URL, json=payload)
          if res.status_code == 200:
            st.toast(f"✅ Evaluación registrada para {codigo_unico}.")
            # Limpiar caché para que el panel de control se actualice con la nueva fila
            st.cache_data.clear()
          else:
            st.error("Error al enviar la evaluación a Google Sheets.")
      else:
        st.error("Error al conectar con el servidor de validación.")

# ---------------------------------------------------------
# 2. GENERADOR DE CÓDIGOS ÚNICOS
# ---------------------------------------------------------
elif opcion == "Generar Códigos Únicos":
  st.header("Generador de Códigos Únicos")
  clave_codigos = st.text_input(
      "Ingrese Contraseña Autorizada", type="password"
  )

  if clave_codigos == "admin123":
    st.success("🔓 Acceso concedido.")
    st.subheader("🔍 Búsqueda en Padrón de Encuentros Educativos")

    dni_input = st.text_input(
        "DNI del Estudiante (presione Enter para buscar)"
    ).strip()

    nombre_defecto = ""
    escuela_defecto = ""
    puntaje_defecto = "N/A"

    if dni_input:
      with st.spinner("Buscando DNI en el padrón..."):
        coincidencias = buscar_estudiantes_por_dni(dni_input)

      if len(coincidencias) == 1:
        estudiante_sel = coincidencias[0]
        nombre_defecto = estudiante_sel["nombre"]
        escuela_defecto = estudiante_sel["escuela"]
        puntaje_defecto = estudiante_sel["puntaje_anterior"]

        st.info(
            f"ℹ️ **Estudiante Encontrado:** {nombre_defecto} | **Escuela:**"
            f" {escuela_defecto}"
        )
        col_m1, col_m2 = st.columns(2)
        with col_m1:
          if estudiante_sel["evento"]:
            st.caption(f"📌 **Inscripción:** {estudiante_sel['evento']}")
        with col_m2:
          st.metric(
              label="Puntaje Instancia Institucional", value=puntaje_defecto
          )

      elif len(coincidencias) > 1:
        ultima_respuesta = coincidencias[-1]["fecha"]
        st.warning(
            f"⚠️ **Atención:** Se encontraron **{len(coincidencias)}"
            " registros** para este DNI.\n\n"
            f"🕒 **Última respuesta registrada:** `{ultima_respuesta}`"
        )

        opciones_map = {
            f"Opción {i+1} ({c['fecha']}) - {c['nombre']} [{c['escuela']}] -"
            f" Puntaje: {c['puntaje_anterior']}": c
            for i, c in enumerate(coincidencias)
        }

        eleccion = st.selectbox(
            "Seleccione el registro que desea utilizar:",
            options=list(opciones_map.keys()),
            index=len(opciones_map) - 1,
        )

        estudiante_sel = opciones_map[eleccion]
        nombre_defecto = estudiante_sel["nombre"]
        escuela_defecto = estudiante_sel["escuela"]
        puntaje_defecto = estudiante_sel["puntaje_anterior"]

        st.metric(
            label="Puntaje Instancia Institucional (Seleccionado)",
            value=puntaje_defecto,
        )

      else:
        st.warning(
            "⚠️ No se encontró el DNI en el padrón de Encuentros Educativos."
            " Puedes completar los datos manualmente."
        )

    with st.container(border=True):
      col_est1, col_est2 = st.columns(2)
      with col_est1:
        nombre_estudiante = st.text_input(
            "Nombre y Apellido", value=nombre_defecto
        )
      with col_est2:
        escuela_estudiante = st.text_input(
            "Escuela / Institución", value=escuela_defecto
        )

      prefijo = st.selectbox(
          "Materia de la Evaluación", ["MAT", "LEN", "TDR1", "TDR2"]
      )

    if st.button("🎲 Generar y Asignar Código Único", type="primary"):
      if not dni_input or not nombre_estudiante or not escuela_estudiante:
        st.warning("⚠️ Debes completar DNI, Nombre y Escuela.")
      else:
        aleatorio = "".join(random.choices(CARACTERES_SEGUROS, k=4))
        codigo_generado = f"{prefijo}-2026-{aleatorio}"
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        mapa_materias = {
            "MAT": "Matemática",
            "LEN": "Lengua",
            "TDR1": "Tecnología de la Representación Nivel 1",
            "TDR2": "Tecnología de la Representación Nivel 2",
        }
        materia_nombre = mapa_materias.get(prefijo, prefijo)

        payload_codigo = {
            "action": "guardar_codigo",
            "fecha": fecha_actual,
            "dni": dni_input,
            "codigo_unico": codigo_generado,
            "estudiante": nombre_estudiante,
            "escuela": escuela_estudiante,
            "materia": materia_nombre,
            "puntaje_institucional": puntaje_defecto,
        }

        res = requests.post(WEBAPP_URL, json=payload_codigo)
        if res.status_code == 200:
          st.success(
              f"✅ Código **{codigo_generado}** asignado y guardado en"
              " `Base_codigos`."
          )
          st.subheader("Código Asignado")
          st.code(codigo_generado, language="text")

          df_asignacion = pd.DataFrame([{
              "Fecha": fecha_actual,
              "DNI": dni_input,
              "Codigo_Unico": codigo_generado,
              "Estudiante": nombre_estudiante,
              "Escuela": escuela_estudiante,
              "Puntaje_Institucional": puntaje_defecto,
              "Materia": materia_nombre,
          }])
          st.dataframe(df_asignacion, use_container_width=True)
          # Limpiar caché para que el panel de control se actualice con la nueva fila
          st.cache_data.clear()
        else:
          st.error("Error al guardar el código en Google Sheets.")

  elif clave_codigos != "":
    st.error("❌ Contraseña incorrecta.")

# ---------------------------------------------------------
# 3. PANEL DE ADMINISTRACIÓN
# ---------------------------------------------------------
elif opcion == "Panel de Administración":
  st.header("Panel de Administración")
  clave = st.text_input("Clave Administrador", type="password")

  if clave == "admin123":
    tab1, tab2, tab3 = st.tabs([
        "📊 Evaluaciones Registradas",
        "🔑 Base de Códigos",
        "👤 Gestor de Usuarios",
    ])

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
        st.info("No hay códigos guardados en la base de datos.")

    with tab3:
      df_users = leer_pestana(SHEET_ID_EVALS, "Usuarios")
      if not df_users.empty:
        st.dataframe(df_users, use_container_width=True)

      st.markdown("---")
      st.subheader("Autorizar Nuevo Evaluador")

      cant_usuarios = len(df_users) if not df_users.empty else 0
      nuevo_id = f"EVAL-{cant_usuarios + 1:03d}"
      st.info(f"🆔 **ID asignado automáticamente:** `{nuevo_id}`")

      with st.container(border=True):
        nuevo_nombre = st.text_input("Nombre completo del evaluador")
        quien_autoriza = st.text_input(
            "Autorizado por", value="Dirección Técnica"
        )

      if st.button("✅ Autorizar Evaluador", type="primary"):
        if nuevo_nombre:
          payload = {
              "action": "usuario",
              "id_evaluador": nuevo_id,
              "nombre": nuevo_nombre,
              "autorizado_por": quien_autoriza,
          }
          res = requests.post(WEBAPP_URL, json=payload)
          if res.status_code == 200:
            st.success(
                f"Evaluador **{nuevo_nombre}** registrado con éxito con el ID"
                f" **{nuevo_id}**."
            )
            st.cache_data.clear()
            st.rerun()
          else:
            st.error("Error al registrar el usuario en Google Sheets.")
        else:
          st.warning("⚠️ Debes ingresar el Nombre completo del evaluador.")
