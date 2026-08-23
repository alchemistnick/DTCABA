import random
from datetime import datetime
import pandas as pd
import requests
import streamlit as st

WEBAPP_URL ="https://script.google.com/macros/s/AKfycbzgdCGAxtSrFcZP7A7KlDlkaWzbc9_3R1-rpPN6yuR0JblvPADa2hPDL7etnUWMB4xyng/exec"
SHEET_ID_EVALS = "1V5rWEolARQ3PlZTbVrrhEWUc7bipJF0t2iMznxjvKgk"

CARACTERES_SEGUROS = "BCDFGHJKLMNPQRSTVWXYZ0123456789"
ADMIN_PASSWORD = "admin123"

st.set_page_config(
    page_title="Evaluaciones DTCABA 2026",
    page_icon="📐",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# ESTILOS
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    :root {
        --primary: #4F46E5;
        --primary-dark: #3730A3;
        --bg-app: linear-gradient(180deg, #F5F6FB 0%, #EEF1FA 100%);
        --bg-card: #FFFFFF;
        --bg-input: #F9FAFB;
        --border-color: #E5E7EB;
        --text-main: #1F2937;
    }

    .stApp {
        background: var(--bg-app) !important;
    }

    .app-header {
        background: linear-gradient(135deg, var(--primary) 0%, #312E81 100%);
        padding: 2rem 1.5rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .app-header h1 {
        font-family: 'Poppins', sans-serif;
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0;
        color: #FFFFFF !important;
    }
    .app-header p {
        margin: 0.2rem 0 0 0;
        color: #E0E7FF !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #FFFFFF !important;
        border-radius: 16px;
        border: 1px solid #E5E7EB !important;
        padding: 1rem;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #4F46E5 0%, #3730A3 100%) !important;
        color: #FFFFFF !important;
        border: none;
        border-radius: 12px;
        padding: 0.65rem 1.5rem;
        font-weight: 600;
        width: 100%;
    }

    section[data-testid="stSidebar"] {
        background: #1E1B4B !important;
    }
    section[data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# ENCABEZADO Y NAVEGACIÓN
# ---------------------------------------------------------
st.markdown(
    """
    <div class="app-header">
        <h1>📐 Desafíos Técnicos⚙️</h1>
        <p>Plataforma de Evaluación y Gestión</p>
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
    dni_limpio = str(dni_búsqueda).strip().replace(".", "").replace(" ", "")
    payload = {"action": "buscar_dni", "dni": dni_limpio}
    res = requests.post(WEBAPP_URL, json=payload, timeout=25)
    if res.status_code == 200:
      try:
        data = res.json()
        if data.get("status") == "success":
          return data.get("coincidencias", [])
      except Exception:
        pass
  except Exception:
    pass
  return []


# ---------------------------------------------------------
# 1. CARGAR EVALUACIÓN (CON DNI DE EVALUADOR DIRECTO)
# ---------------------------------------------------------
if opcion == "Cargar Evaluación":
  st.header("Carga de Evaluación")

  with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
      dni_evaluador = (
          st.text_input(
              "DNI del Evaluador",
              placeholder="Ingresa tu DNI",
              key="eval_dni",
          )
          .strip()
          .replace(".", "")
      )
    with col2:
      codigo_unico = (
          st.text_input(
              "Código Único del Examen",
              placeholder="Ej: MAT-2026-X8K9",
              key="eval_codigo",
          )
          .strip()
          .upper()
      )

    materia = st.selectbox(
        "Materia",
        [
            "Matemática",
            "Lengua",
            "Tecnología de la Representación Nivel 1",
            "Tecnología de la Representación Nivel 2",
        ],
    )

  st.subheader(f"📋 Rúbrica: {materia}")

  if materia == "Matemática":
    label_c1 = "Criterio 1: Planteo y Razonamiento"
    label_c2 = "Criterio 2: Operatoria y Precisión"
    label_c3 = "Criterio 3: Interpretación de Resultados"
  elif materia == "Lengua":
    label_c1 = "Criterio 1: Comprensión Lectora y Coherencia"
    label_c2 = "Criterio 2: Cohesión y Estructuración"
    label_c3 = "Criterio 3: Ortografía y Gramática"
  elif materia == "Tecnología de la Representación Nivel 1":
    label_c1 = "Criterio 1: Normalización Básica"
    label_c2 = "Criterio 2: Proyección Ortogonal"
    label_c3 = "Criterio 3: Prolijidad y Calidad Gráfica"
  else:
    label_c1 = "Criterio 1: Modelado / Vistas Complejas"
    label_c2 = "Criterio 2: Aplicación de Normas"
    label_c3 = "Criterio 3: Resolución de Conjuntos"

  with st.container(border=True):
    c1 = st.radio(label_c1, [1, 2, 3, 4], horizontal=True)
    st.divider()
    c2 = st.radio(label_c2, [1, 2, 3, 4], horizontal=True)
    st.divider()
    c3 = st.radio(label_c3, [1, 2, 3, 4], horizontal=True)

  if st.button("💾 Guardar Evaluación", type="primary"):
    if not dni_evaluador or not codigo_unico:
      st.warning("⚠️ Debes ingresar el DNI del evaluador y el Código Único.")
    else:
      promedio = round((c1 + c2 + c3) / 3, 2)
      payload = {
          "action": "evaluacion",
          "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
          "codigo_unico": codigo_unico,
          "materia": materia,
          "evaluador_id": dni_evaluador,
          "evaluador_nombre": f"Evaluador DNI {dni_evaluador}",
          "c1": c1,
          "c2": c2,
          "c3": c3,
          "promedio": promedio,
      }

      try:
        res = requests.post(WEBAPP_URL, json=payload, timeout=10)
        st.success(
            f"✅ Evaluación guardada con éxito para el examen **{codigo_unico}**!"
        )
        st.cache_data.clear()
      except Exception:
        st.error(
            "⚠️ No se pudo enviar el registro. Revisa la conexión e intenta"
            " nuevamente."
        )

# ---------------------------------------------------------
# 2. GENERADOR DE CÓDIGOS CON BÚSQUEDA EN PADRÓN
# ---------------------------------------------------------
elif opcion == "Generar Códigos Únicos":
  st.header("Generador de Códigos Únicos")
  clave = st.text_input("Contraseña de Acceso", type="password")

  if clave == ADMIN_PASSWORD:
    st.success("🔓 Acceso habilitado.")
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
        nombre_defecto = estudiante_sel.get("nombre", "")
        escuela_defecto = estudiante_sel.get("escuela", "")
        puntaje_defecto = estudiante_sel.get("puntaje_anterior", "N/A")

        st.info(
            f"ℹ️ **Estudiante Encontrado:** {nombre_defecto} | **Escuela:**"
            f" {escuela_defecto}"
        )
        col_m1, col_m2 = st.columns(2)
        with col_m1:
          if estudiante_sel.get("evento"):
            st.caption(f"📌 **Inscripción:** {estudiante_sel['evento']}")
        with col_m2:
          st.metric(
              label="Puntaje Instancia Institucional", value=puntaje_defecto
          )

      elif len(coincidencias) > 1:
        st.warning(
            f"⚠️ Se encontraron **{len(coincidencias)} registros** para este"
            " DNI."
        )
        opciones_map = {
            f"Opción {i+1} - {c.get('nombre', '')} [{c.get('escuela', '')}] -"
            f" Puntaje: {c.get('puntaje_anterior', 'N/A')}": c
            for i, c in enumerate(coincidencias)
        }
        eleccion = st.selectbox(
            "Seleccione el registro a utilizar:",
            options=list(opciones_map.keys()),
        )
        estudiante_sel = opciones_map[eleccion]
        nombre_defecto = estudiante_sel.get("nombre", "")
        escuela_defecto = estudiante_sel.get("escuela", "")
        puntaje_defecto = estudiante_sel.get("puntaje_anterior", "N/A")
      else:
        st.warning(
            "⚠️ No se encontró el DNI en el padrón. Puedes completar los datos"
            " manualmente."
        )

    with st.container(border=True):
      col_a, col_b = st.columns(2)
      with col_a:
        dni_estudiante = st.text_input("DNI Estudiante", value=dni_input)
        nombre_estudiante = st.text_input(
            "Nombre y Apellido", value=nombre_defecto
        )
      with col_b:
        escuela_estudiante = st.text_input(
            "Escuela / Institución", value=escuela_defecto
        )
        prefijo = st.selectbox(
            "Materia de Evaluación", ["MAT", "LEN", "TDR1", "TDR2"]
        )

    if st.button("🎲 Generar Código", type="primary"):
      if not dni_estudiante or not nombre_estudiante or not escuela_estudiante:
        st.warning("⚠️ Completa DNI, Nombre y Escuela para continuar.")
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
            "dni": dni_estudiante,
            "codigo_unico": codigo_generado,
            "estudiante": nombre_estudiante,
            "escuela": escuela_estudiante,
            "materia": materia_nombre,
            "puntaje_institucional": puntaje_defecto,
        }

        try:
          requests.post(WEBAPP_URL, json=payload_codigo, timeout=10)
          st.success(f"✅ Código Generado: **{codigo_generado}**")
          st.code(codigo_generado, language="text")
          st.cache_data.clear()
        except Exception:
          st.error("Error al registrar el código en Google Sheets.")

  elif clave != "":
    st.error("❌ Contraseña incorrecta.")

# ---------------------------------------------------------
# 3. PANEL DE ADMINISTRACIÓN
# ---------------------------------------------------------
elif opcion == "Panel de Administración":
  st.header("Panel de Administración")
  clave = st.text_input("Contraseña Administrador", type="password")

  if clave == ADMIN_PASSWORD:
    tab1, tab2 = st.tabs(["📊 Evaluaciones Guardadas", "🔑 Base de Códigos"])

    with tab1:
      df_evals = leer_pestana(SHEET_ID_EVALS, "Evaluaciones")
      if not df_evals.empty:
        st.dataframe(df_evals, width="stretch")
      else:
        st.info("No hay evaluaciones guardadas aún.")

    with tab2:
      df_codigos = leer_pestana(SHEET_ID_EVALS, "Base_codigos")
      if not df_codigos.empty:
        st.dataframe(df_codigos, width="stretch")
      else:
        st.info("No hay códigos guardados aún.")
