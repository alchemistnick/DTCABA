import random
from datetime import datetime
import pandas as pd
import requests
import streamlit as st

# ---------------------------------------------------------
# CONFIGURACIÓN DIRECTA DE SERVIDORES Y HOJAS
# ---------------------------------------------------------
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzt19tpSOAd8HVEW6q8CU5-d9sK9H7jKGnmgI23HVW-aJ3IIqLDL2M3IiAJcwhTCaU0YQ/exec"
SHEET_ID_EVALS = "1V5rWEolARQ3PlZTbVrrhEWUc7bipJF0t2iMznxjvKgk"
ADMIN_PASSWORD = "admin123"

CARACTERES_SEGUROS = "BCDFGHJKLMNPQRSTVWXYZ0123456789"

st.set_page_config(
    page_title="Evaluaciones DTCABA 2026",
    page_icon="📐",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# ESTILOS ADAPTABLES (MODO CLARO Y MODO OSCURO)
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
        --header-bg: linear-gradient(135deg, #4F46E5 0%, #312E81 100%);
        --card-bg: #FFFFFF;
        --card-border: #E5E7EB;
        --text-color: #1F2937;
        --subtext-color: #4B5563;
    }

    @media (prefers-color-scheme: dark) {
        :root {
            --primary: #6366F1;
            --primary-dark: #4F46E5;
            --header-bg: linear-gradient(135deg, #1E1B4B 0%, #312E81 100%);
            --card-bg: #1E293B;
            --card-border: #334155;
            --text-color: #F9FAFB;
            --subtext-color: #CBD5E1;
        }
    }

    .app-header {
        background: var(--header-bg);
        padding: 2rem 1.5rem; 
        border-radius: 20px; 
        margin-bottom: 2rem; 
        color: #FFFFFF !important; 
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
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
        background-color: var(--card-bg) !important;
        border-radius: 16px;
        border: 1px solid var(--card-border) !important;
        padding: 1.25rem;
        margin-bottom: 1rem;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] h4, 
    div[data-testid="stVerticalBlockBorderWrapper"] p,
    div[data-testid="stVerticalBlockBorderWrapper"] span {
        color: var(--text-color) !important;
    }

    .stRadio > label {
        font-weight: 600 !important;
        color: var(--text-color) !important;
        margin-bottom: 0.5rem;
    }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%) !important;
        color: #FFFFFF !important; 
        border: none; 
        border-radius: 12px; 
        padding: 0.65rem 1.5rem; 
        font-weight: 600; 
        width: 100%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.15);
    }

    section[data-testid="stSidebar"] { 
        background-color: #0F172A !important; 
    }
    section[data-testid="stSidebar"] * { 
        color: #F8FAFC !important; 
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
        <p>Plataforma de Evaluación y Gestión de Duplas</p>
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


# ---------------------------------------------------------
# 1. CARGAR EVALUACIÓN (PONDERACIÓN SOBRE 100 PUNTOS)
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
              placeholder="Ej: X8K198",
              key="eval_codigo",
          )
          .strip()
          .upper()
      )

    materia = st.selectbox(
        "Materia",
        [
            "Lengua",
            "Matemática",
            "Tecnología de la Representación Nivel 1",
            "Tecnología de la Representación Nivel 2",
        ],
    )

  st.subheader(f"📋 Rúbrica de Evaluación: {materia}")

  # ---------------------------------------------------------
  # RÚBRICA DE LENGUA
  # ---------------------------------------------------------
  if materia == "Lengua":
    map_len1 = {
        4: (
            "4 - Avanzado: Conserva e integra el sentido central del texto"
            " técnico."
        ),
        3: (
            "3 - Satisfactorio: Conserva ideas principales con pequeñas"
            " simplificaciones."
        ),
        2: "2 - En desarrollo: Recupera solo parte de la información relevante.",
        1: "1 - Inicial: Pierde o modifica el sentido del texto fuente.",
    }
    map_len2 = {
        4: (
            "4 - Avanzado: El texto se transforma completamente en un relato"
            " literario."
        ),
        3: (
            "3 - Satisfactorio: Predomina el relato aunque mantiene rasgos"
            " expositivos."
        ),
        2: (
            "2 - En desarrollo: Alterna explicación y narración sin"
            " integrarlas."
        ),
        1: (
            "1 - Inicial: Predomina el texto expositivo o no logra la"
            " transformación."
        ),
    }
    map_len3 = {
        4: (
            "4 - Avanzado: Construye una voz en primera persona consistente y"
            " verosímil."
        ),
        3: "3 - Satisfactorio: La voz se sostiene con algunas inconsistencias.",
        2: "2 - En desarrollo: La voz aparece de manera parcial o irregular.",
        1: "1 - Inicial: No logra construir una voz narrativa.",
    }
    map_len4 = {
        4: (
            "4 - Avanzado: Utiliza el lenguaje técnico para construir"
            " experiencias y emociones."
        ),
        3: (
            "3 - Satisfactorio: Integra el vocabulario técnico de manera"
            " pertinente."
        ),
        2: (
            "2 - En desarrollo: El lenguaje técnico aparece de forma aislada o"
            " forzada."
        ),
        1: (
            "1 - Inicial: No incorpora o utiliza incorrectamente el lenguaje"
            " técnico."
        ),
    }
    map_len5 = {
        4: (
            "4 - Avanzado: Integra descripciones, metáforas o comparaciones"
            " enriquecedoras."
        ),
        3: (
            "3 - Satisfactorio: Utiliza algunos recursos expresivos"
            " adecuados."
        ),
        2: "2 - En desarrollo: Los recursos son escasos o poco pertinentes.",
        1: "1 - Inicial: No utiliza recursos literarios significativos.",
    }
    map_len6 = {
        4: (
            "4 - Avanzado: Presenta una secuencia clara, coherente y"
            " cohesionada."
        ),
        3: (
            "3 - Satisfactorio: El relato es comprensible con pequeñas"
            " dificultades."
        ),
        2: (
            "2 - En desarrollo: La organización presenta reiteraciones o"
            " saltos."
        ),
        1: "1 - Inicial: La organización dificulta la comprensión.",
    }
    map_len7 = {
        4: "4 - Avanzado: Emplea correctamente la normativa ortográfica.",
        3: (
            "3 - Satisfactorio: Presenta pocos errores que no dificultan la"
            " lectura."
        ),
        2: (
            "2 - En desarrollo: Presenta errores que dificultan la lectura en"
            " parte."
        ),
        1: (
            "1 - Inicial: Los errores afectan significativamente la"
            " comprensión."
        ),
    }

    st.markdown("### BLOQUE A: Comprender para transformar (40%)")
    with st.container(border=True):
      st.markdown("#### 1. Apropiación del texto fuente (20%)")
      c1 = st.radio(
          "Nivel:",
          [4, 3, 2, 1],
          format_func=lambda x: map_len1[x],
          key="len_c1",
      )
      obs1 = st.text_area(
          "Observaciones / Justificación:", key="obs_c1", height=70
      )

    with st.container(border=True):
      st.markdown("#### 2. Transformación del género (20%)")
      c2 = st.radio(
          "Nivel:",
          [4, 3, 2, 1],
          format_func=lambda x: map_len2[x],
          key="len_c2",
      )
      obs2 = st.text_area(
          "Observaciones / Justificación:", key="obs_c2", height=70
      )

    st.markdown("### BLOQUE B: Escribir para construir sentido (40%)")
    with st.container(border=True):
      st.markdown("#### 3. Voz narrativa")
      c3 = st.radio(
          "Nivel:",
          [4, 3, 2, 1],
          format_func=lambda x: map_len3[x],
          key="len_c3",
      )
      obs3 = st.text_area(
          "Observaciones / Justificación:", key="obs_c3", height=70
      )

    with st.container(border=True):
      st.markdown("#### 4. Resignificación del lenguaje técnico")
      c4 = st.radio(
          "Nivel:",
          [4, 3, 2, 1],
          format_func=lambda x: map_len4[x],
          key="len_c4",
      )
      obs4 = st.text_area(
          "Observaciones / Justificación:", key="obs_c4", height=70
      )

    with st.container(border=True):
      st.markdown("#### 5. Construcción literaria")
      c5 = st.radio(
          "Nivel:",
          [4, 3, 2, 1],
          format_func=lambda x: map_len5[x],
          key="len_c5",
      )
      obs5 = st.text_area(
          "Observaciones / Justificación:", key="obs_c5", height=70
      )

    st.markdown("### BLOQUE C: Comunicar con claridad (20%)")
    with st.container(border=True):
      st.markdown("#### 6. Organización del relato (10%)")
      c6 = st.radio(
          "Nivel:",
          [4, 3, 2, 1],
          format_func=lambda x: map_len6[x],
          key="len_c6",
      )
      obs6 = st.text_area(
          "Observaciones / Justificación:", key="obs_c6", height=70
      )

    with st.container(border=True):
      st.markdown("#### 7. Normativa (10%)")
      c7 = st.radio(
          "Nivel:",
          [4, 3, 2, 1],
          format_func=lambda x: map_len7[x],
          key="len_c7",
      )
      obs7 = st.text_area(
          "Observaciones / Justificación:", key="obs_c7", height=70
      )

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
        "c1_desc": map_len1[c1],
        "obs1": obs1,
        "c2_desc": map_len2[c2],
        "obs2": obs2,
        "c3_desc": map_len3[c3],
        "obs3": obs3,
        "c4_desc": map_len4[c4],
        "obs4": obs4,
        "c5_desc": map_len5[c5],
        "obs5": obs5,
        "c6_desc": map_len6[c6],
        "obs6": obs6,
        "c7_desc": map_len7[c7],
        "obs7": obs7,
    }

  # ---------------------------------------------------------
  # RÚBRICA DE MATEMÁTICA
  # ---------------------------------------------------------
  elif materia == "Matemática":
    map_mat1 = {
        5: (
            "5 - Destacado: Figura original y de alta complejidad con"
            " excelente representación."
        ),
        4: (
            "4 - Avanzado: Figura tridimensional bien construida, muestra"
            " originalidad y calidad."
        ),
        3: (
            "3 - Satisfactorio: La figura es adecuada y realizada de manera"
            " correcta."
        ),
        2: "2 - Básico: La figura es muy básica con representación incompleta.",
        1: "1 - Inicial: La figura no es clara y presenta muchos errores.",
    }
    map_mat2 = {
        5: (
            "5 - Destacado: Problema original, explícito y de integración"
            " impecable."
        ),
        4: (
            "4 - Avanzado: Situación problemática bien planteada con"
            " coherencia."
        ),
        3: (
            "3 - Satisfactorio: El problema es correcto aunque la figura no"
            " sea central."
        ),
        2: (
            "2 - Básico: El problema presenta inconsistencias en su"
            " desarrollo."
        ),
        1: (
            "1 - Inicial: No logra contextualizar en una situación"
            " problemática."
        ),
    }
    map_mat3 = {
        5: (
            "5 - Destacado: Procedimiento impecable, utilizando datos y"
            " justificando cada paso."
        ),
        4: (
            "4 - Avanzado: Aplica el procedimiento correcto y presenta"
            " justificación sólida."
        ),
        3: (
            "3 - Satisfactorio: El planteo es correcto pero con algunas"
            " imprecisiones."
        ),
        2: (
            "2 - Básico: Reconoce datos pero presenta problemas al plantear el"
            " problema."
        ),
        1: (
            "1 - Inicial: No reconoce los datos necesarios para poder plantear"
            " la situación."
        ),
    }
    map_mat4 = {
        5: (
            "5 - Destacado: La utilización del lenguaje presenta gran"
            " precisión y soltura."
        ),
        4: (
            "4 - Avanzado: Utiliza de forma correcta y formal el lenguaje"
            " técnico."
        ),
        3: "3 - Satisfactorio: Exposición comprensible, cumple con la consigna.",
        2: (
            "2 - Básico: Utiliza lenguaje informal o impreciso en su"
            " explicación."
        ),
        1: "1 - Inicial: La presentación es desorganizada y no cumple pautas.",
    }

    st.markdown("### 📐 Criterios de Evaluación: Matemática")
    with st.container(border=True):
      st.markdown(
          "#### 1. Construcción y Representación de la Figura Tridimensional"
          " (20%)"
      )
      c1 = st.radio(
          "Nivel:",
          [5, 4, 3, 2, 1],
          format_func=lambda x: map_mat1[x],
          key="mat_c1",
      )
      obs1 = st.text_area(
          "Observaciones / Justificación:", key="obs_mat1", height=70
      )

    with st.container(border=True):
      st.markdown(
          "#### 2. Diseño del Problema Matemático e Interdisciplinariedad"
          " (30%)"
      )
      c2 = st.radio(
          "Nivel:",
          [5, 4, 3, 2, 1],
          format_func=lambda x: map_mat2[x],
          key="mat_c2",
      )
      obs2 = st.text_area(
          "Observaciones / Justificación:", key="obs_mat2", height=70
      )

    with st.container(border=True):
      st.markdown("#### 3. Resolución y Justificación del Problema (30%)")
      c3 = st.radio(
          "Nivel:",
          [5, 4, 3, 2, 1],
          format_func=lambda x: map_mat3[x],
          key="mat_c3",
      )
      obs3 = st.text_area(
          "Observaciones / Justificación:", key="obs_mat3", height=70
      )

    with st.container(border=True):
      st.markdown("#### 4. Presentación y Comunicación (20%)")
      c4 = st.radio(
          "Nivel:",
          [5, 4, 3, 2, 1],
          format_func=lambda x: map_mat4[x],
          key="mat_c4",
      )
      obs4 = st.text_area(
          "Observaciones / Justificación:", key="obs_mat4", height=70
      )

    promedio_base5 = (c1 * 0.20) + (c2 * 0.30) + (c3 * 0.30) + (c4 * 0.20)
    puntaje_100 = round((promedio_base5 / 5) * 100, 2)

    eval_respuestas = {
        "c1_desc": map_mat1[c1],
        "obs1": obs1,
        "c2_desc": map_mat2[c2],
        "obs2": obs2,
        "c3_desc": map_mat3[c3],
        "obs3": obs3,
        "c4_desc": map_mat4[c4],
        "obs4": obs4,
    }

  # ---------------------------------------------------------
  # RÚBRICAS DE TECNOLOGÍA DE LA REPRESENTACIÓN
  # ---------------------------------------------------------
  else:
    st.markdown(f"### ⚙️ Criterios de Evaluación: {materia}")

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
      c1 = st.radio(
          "Nivel:",
          [4, 3, 2, 1],
          format_func=lambda x: {
              4: "4 - Avanzado (Excelente aplicación)",
              3: "3 - Satisfactorio (Correcta aplicación con mínimos detalles)",
              2: "2 - En desarrollo (Aplicación parcial o incompleta)",
              1: "1 - Inicial (Dificultades significativas)",
          }[x],
          key="tdr_c1",
      )
      obs1 = st.text_area(
          "Observaciones / Justificación:", key="obs_tdr1", height=70
      )

    with st.container(border=True):
      st.markdown(f"#### {lbl2}")
      c2 = st.radio(
          "Nivel:",
          [4, 3, 2, 1],
          format_func=lambda x: {
              4: "4 - Avanzado (Excelente proyección)",
              3: "3 - Satisfactorio (Proyección adecuada)",
              2: "2 - En desarrollo (Proyección parcial)",
              1: "1 - Inicial (Errores en la proyección)",
          }[x],
          key="tdr_c2",
      )
      obs2 = st.text_area(
          "Observaciones / Justificación:", key="obs_tdr2", height=70
      )

    with st.container(border=True):
      st.markdown(f"#### {lbl3}")
      c3 = st.radio(
          "Nivel:",
          [4, 3, 2, 1],
          format_func=lambda x: {
              4: "4 - Avanzado (Alta calidad y prolijidad)",
              3: "3 - Satisfactorio (Prolijidad adecuada)",
              2: "2 - En desarrollo (Prolijidad mejorable)",
              1: "1 - Inicial (Baja calidad gráfica)",
          }[x],
          key="tdr_c3",
      )
      obs3 = st.text_area(
          "Observaciones / Justificación:", key="obs_tdr3", height=70
      )

    promedio_base4 = (c1 * 0.35) + (c2 * 0.35) + (c3 * 0.30)
    puntaje_100 = round((promedio_base4 / 4) * 100, 2)

    eval_respuestas = {
        "c1_desc": f"Nivel {c1} - {lbl1}",
        "obs1": obs1,
        "c2_desc": f"Nivel {c2} - {lbl2}",
        "obs2": obs2,
        "c3_desc": f"Nivel {c3} - {lbl3}",
        "obs3": obs3,
    }

  st.metric(
      label="Puntaje Total Ponderado (sobre 100)", value=f"{puntaje_100} / 100 pts"
  )
  st.divider()

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
        requests.post(WEBAPP_URL, json=payload, timeout=10)
        st.success(
            f"✅ Evaluación guardada con éxito (Puntaje Total: {puntaje_100} /"
            " 100 pts)!"
        )
        st.cache_data.clear()
      except Exception:
        st.error("⚠️ Error de conexión al guardar la evaluación.")

# ---------------------------------------------------------
# 2. GENERADOR DE CÓDIGOS PARA DUPLAS (6 DÍGITOS ALFANUMÉRICOS + UNICIDAD)
# ---------------------------------------------------------
elif opcion == "Generar Códigos Únicos":
  st.header("Generador de Códigos para Duplas")
  clave = st.text_input("Contraseña de Acceso", type="password")

  if clave == ADMIN_PASSWORD:
    st.success("🔓 Acceso habilitado.")

    prefijo = st.selectbox(
        "Materia de Evaluación", ["MAT", "LEN", "TDR1", "TDR2"]
    )
    st.divider()

    col_m1, col_m2 = st.columns(2)

    # INTEGRANTE 1
    with col_m1:
      st.subheader("👤 Integrante 1")
      dni1 = (
          st.text_input("DNI Integrante 1", key="dni1")
          .strip()
          .replace(".", "")
      )

      n1_def, esc1_def, mail1_def, punt1_def, niv1_def, insc1_def = (
          "",
          "",
          "",
          "N/A",
          "N/A",
          "N/A",
      )

      if dni1:
        coincidencias1 = buscar_estudiantes_por_dni(dni1)

        if len(coincidencias1) == 1:
          c = coincidencias1[0]
          st.success("✅ Encontrado en padrón")
          n1_def, esc1_def, mail1_def, punt1_def, niv1_def, insc1_def = (
              c.get("nombre", ""),
              c.get("escuela", ""),
              c.get("email", ""),
              c.get("puntaje_anterior", "N/A"),
              c.get("nivel", "N/A"),
              c.get("inscripcion", "N/A"),
          )
        elif len(coincidencias1) > 1:
          st.warning(
              f"⚠️ DNI duplicado: {len(coincidencias1)} registros encontrados."
          )
          opciones1 = {
              f"Reg {i+1} ({c.get('fecha','')}) - {c.get('escuela','')} -"
              f" Desafío: {c.get('inscripcion','N/A')} - Nivel:"
              f" {c.get('nivel','N/A')}": c
              for i, c in enumerate(coincidencias1)
          }
          sel1 = st.selectbox(
              "Seleccionar inscripción Integrante 1:",
              options=list(opciones1.keys()),
              key="sel1",
          )
          c = opciones1[sel1]
          n1_def, esc1_def, mail1_def, punt1_def, niv1_def, insc1_def = (
              c.get("nombre", ""),
              c.get("escuela", ""),
              c.get("email", ""),
              c.get("puntaje_anterior", "N/A"),
              c.get("nivel", "N/A"),
              c.get("inscripcion", "N/A"),
          )

      nom1 = st.text_input("Nombre y Apellido 1", value=n1_def)
      esc1 = st.text_input("Escuela Técnica Nº 1", value=esc1_def)
      mail1 = st.text_input("Correo Electrónico 1", value=mail1_def)
      insc1 = st.text_input(
          "Inscripción a Desafío de... (1)", value=str(insc1_def)
      )
      niv1 = st.text_input("Nivel de la dupla (1)", value=str(niv1_def))
      punt1 = st.text_input("Puntaje Institucional 1", value=str(punt1_def))

    # INTEGRANTE 2
    with col_m2:
      st.subheader("👤 Integrante 2")
      dni2 = (
          st.text_input("DNI Integrante 2", key="dni2")
          .strip()
          .replace(".", "")
      )

      n2_def, esc2_def, mail2_def, punt2_def, niv2_def, insc2_def = (
          "",
          "",
          "",
          "N/A",
          "N/A",
          "N/A",
      )

      if dni2:
        coincidencias2 = buscar_estudiantes_por_dni(dni2)

        if len(coincidencias2) == 1:
          c = coincidencias2[0]
          st.success("✅ Encontrado en padrón")
          n2_def, esc2_def, mail2_def, punt2_def, niv2_def, insc2_def = (
              c.get("nombre", ""),
              c.get("escuela", ""),
              c.get("email", ""),
              c.get("puntaje_anterior", "N/A"),
              c.get("nivel", "N/A"),
              c.get("inscripcion", "N/A"),
          )
        elif len(coincidencias2) > 1:
          st.warning(
              f"⚠️ DNI duplicado: {len(coincidencias2)} registros encontrados."
          )
          opciones2 = {
              f"Reg {i+1} ({c.get('fecha','')}) - {c.get('escuela','')} -"
              f" Desafío: {c.get('inscripcion','N/A')} - Nivel:"
              f" {c.get('nivel','N/A')}": c
              for i, c in enumerate(coincidencias2)
          }
          sel2 = st.selectbox(
              "Seleccionar inscripción Integrante 2:",
              options=list(opciones2.keys()),
              key="sel2",
          )
          c = opciones2[sel2]
          n2_def, esc2_def, mail2_def, punt2_def, niv2_def, insc2_def = (
              c.get("nombre", ""),
              c.get("escuela", ""),
              c.get("email", ""),
              c.get("puntaje_anterior", "N/A"),
              c.get("nivel", "N/A"),
              c.get("inscripcion", "N/A"),
          )

      nom2 = st.text_input("Nombre y Apellido 2", value=n2_def)
      esc2 = st.text_input("Escuela Técnica Nº 2", value=esc2_def)
      mail2 = st.text_input("Correo Electrónico 2", value=mail2_def)
      insc2 = st.text_input(
          "Inscripción a Desafío de... (2)", value=str(insc2_def)
      )
      niv2 = st.text_input("Nivel de la dupla (2)", value=str(niv2_def))
      punt2 = st.text_input("Puntaje Institucional 2", value=str(punt2_def))

    st.divider()

    if st.button("🎲 Generar Código de Dupla", type="primary"):
      if not dni1 or not nom1 or not dni2 or not nom2:
        st.warning(
            "⚠️ Debes completar los datos de ambos integrantes de la dupla."
        )
      else:
        guardado_exitoso = False
        intentos = 0

        while not guardado_exitoso and intentos < 5:
          intentos += 1

          tres_aleatorios = "".join(random.choices(CARACTERES_SEGUROS, k=3))
          ultimos_tres_dni = dni1[-3:] if len(dni1) >= 3 else dni1.zfill(3)
          codigo_generado = f"{tres_aleatorios}{ultimos_tres_dni}"

          fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

          mapa_materias = {
              "MAT": "Matemática",
              "LEN": "Lengua",
              "TDR1": "Tecnología de la Representación Nivel 1",
              "TDR2": "Tecnología de la Representación Nivel 2",
          }
          materia_nombre = mapa_materias.get(prefijo, prefijo)

          nivel_consolidado = (
              f"Int1: {niv1} | Int2: {niv2}" if niv1 != niv2 else niv1
          )
          inscripcion_consolidada = (
              f"Int1: {insc1} | Int2: {insc2}" if insc1 != insc2 else insc1
          )

          payload_codigo = {
              "action": "guardar_codigo_dupla",
              "fecha": fecha_actual,
              "codigo_unico": codigo_generado,
              "materia": materia_nombre,
              "inscripcion_desafio": inscripcion_consolidada,
              "nivel_dupla": nivel_consolidado,
              "dni1": dni1,
              "estudiante1": nom1,
              "escuela1": esc1,
              "email1": mail1,
              "puntaje1": punt1,
              "dni2": dni2,
              "estudiante2": nom2,
              "escuela2": esc2,
              "email2": mail2,
              "puntaje2": punt2,
          }

          try:
            res = requests.post(WEBAPP_URL, json=payload_codigo, timeout=10)
            if res.status_code == 200:
              respuesta = res.json()
              if respuesta.get("status") == "success":
                guardado_exitoso = True
                st.success(
                    f"✅ Código Único Generado: **{codigo_generado}** (DNI"
                    f" ...{ultimos_tres_dni})"
                )
                st.code(codigo_generado, language="text")
                st.cache_data.clear()
              elif respuesta.get("message") == "DUPLICADO":
                continue
              else:
                st.error("Error devuelto por el servidor.")
                break
          except Exception:
            st.error("Error de conexión al guardar el código.")
            break

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
