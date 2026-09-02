import random
from datetime import datetime
import pandas as pd
import requests
import streamlit as st

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzuztbd7aTJa1Yq5APE663F_PeOY3AaprmCXR2meJDesR4a_CZzDap8FesLaVzZww8zYA/exec"
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
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    :root {
        --primary: #4F46E5;
        --primary-dark: #3730A3;
        --bg-app: linear-gradient(180deg, #F5F6FB 0%, #EEF1FA 100%);
        --bg-card: #FFFFFF;
        --border-color: #E5E7EB;
        --text-main: #1F2937;
    }
    .stApp { background: var(--bg-app) !important; }
    .app-header {
        background: linear-gradient(135deg, var(--primary) 0%, #312E81 100%);
        padding: 2rem 1.5rem; border-radius: 20px; margin-bottom: 2rem; color: white; text-align: center;
    }
    .app-header h1 { font-family: 'Poppins', sans-serif; font-size: 2.5rem; font-weight: 800; margin: 0; color: #FFFFFF !important; }
    .app-header p { margin: 0.2rem 0 0 0; color: #E0E7FF !important; }
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #FFFFFF !important; border-radius: 16px; border: 1px solid #E5E7EB !important; padding: 1rem;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #4F46E5 0%, #3730A3 100%) !important;
        color: #FFFFFF !important; border: none; border-radius: 12px; padding: 0.65rem 1.5rem; font-weight: 600; width: 100%;
    }
    section[data-testid="stSidebar"] { background: #1E1B4B !important; }
    section[data-testid="stSidebar"] * { color: #FFFFFF !important; }
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
# 1. CARGAR EVALUACIÓN (CON OBSERVACIONES POR CRITERIO)
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
              placeholder="Ej: LEN2026X8K198",
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

  if materia == "Lengua":
    st.markdown("### A. Comprender para transformar (40%)")

    with st.container(border=True):
      st.markdown("**1. Apropiación del texto fuente** *(Ponderación 20%)*")
      c1 = st.radio(
          "Nivel:",
          [4, 3, 2, 1],
          format_func=lambda x: {
              4: "4 - Avanzado (Conserva e integra el sentido central)",
              3: (
                  "3 - Satisfactorio (Conserva ideas principales con pequeñas"
                  " simplificaciones)"
              ),
              2: "2 - En desarrollo (Recupera solo parte de la información)",
              1: "1 - Inicial (Pierde o modifica el sentido del texto)",
          }[x],
          horizontal=True,
          key="len_c1",
      )
      obs1 = st.text_area(
          "Observaciones para Apropiación del texto fuente:",
          key="obs_c1",
          height=70,
      )

      st.divider()

      st.markdown("**2. Transformación del género** *(Ponderación 20%)*")
      c2 = st.radio(
          "Nivel:",
          [4, 3, 2, 1],
          format_func=lambda x: {
              4: "4 - Avanzado (Se transforma completamente en relato)",
              3: "3 - Satisfactorio (Predomina el relato con rasgos expositivos)",
              2: "2 - En desarrollo (Alterna explicación y narración sin integrar)",
              1: "1 - Inicial (Predomina texto expositivo / no transforma)",
          }[x],
          horizontal=True,
          key="len_c2",
      )
      obs2 = st.text_area(
          "Observaciones para Transformación del género:", key="obs_c2", height=70
      )

    st.markdown("### B. Escribir para construir sentido (40%)")

    with st.container(border=True):
      st.markdown("**3. Voz narrativa**")
      c3 = st.radio(
          "Nivel:",
          [4, 3, 2, 1],
          format_func=lambda x: {
              4: "4 - Avanzado (Voz consistente y verosímil)",
              3: "3 - Satisfactorio (Voz se sostiene con inconsistencias)",
              2: "2 - En desarrollo (Voz de manera parcial o irregular)",
              1: "1 - Inicial (No logra construir voz narrativa)",
          }[x],
          horizontal=True,
          key="len_c3",
      )
      obs3 = st.text_area(
          "Observaciones para Voz narrativa:", key="obs_c3", height=70
      )

      st.divider()

      st.markdown("**4. Resignificación del lenguaje técnico**")
      c4 = st.radio(
          "Nivel:",
          [4, 3, 2, 1],
          format_func=lambda x: {
              4: "4 - Avanzado (Construye experiencias/emociones/vínculos)",
              3: "3 - Satisfactorio (Integra vocabulario de manera pertinente)",
              2: "2 - En desarrollo (Lenguaje aparece aislado o forzado)",
              1: "1 - Inicial (No incorpora o utiliza incorrectamente)",
          }[x],
          horizontal=True,
          key="len_c4",
      )
      obs4 = st.text_area(
          "Observaciones para Resignificación del lenguaje técnico:",
          key="obs_c4",
          height=70,
      )

      st.divider()

      st.markdown("**5. Construcción literaria**")
      c5 = st.radio(
          "Nivel:",
          [4, 3, 2, 1],
          format_func=lambda x: {
              4: "4 - Avanzado (Integra descripciones, metáforas o comparaciones)",
              3: "3 - Satisfactorio (Utiliza recursos expresivos adecuados)",
              2: "2 - En desarrollo (Recursos escasos o poco pertinentes)",
              1: "1 - Inicial (No utiliza recursos literarios significativos)",
          }[x],
          horizontal=True,
          key="len_c5",
      )
      obs5 = st.text_area(
          "Observaciones para Construcción literaria:", key="obs_c5", height=70
      )

    st.markdown("### C. Comunicar con claridad (20%)")

    with st.container(border=True):
      st.markdown("**6. Organización del relato** *(Ponderación 10%)*")
      c6 = st.radio(
          "Nivel:",
          [4, 3, 2, 1],
          format_func=lambda x: {
              4: "4 - Avanzado (Secuencia clara, coherente y cohesionada)",
              3: (
                  "3 - Satisfactorio (Relato comprensible con pequeñas"
                  " dificultades)"
              ),
              2: "2 - En desarrollo (Reiteraciones o saltos)",
              1: "1 - Inicial (Organización dificulta la comprensión)",
          }[x],
          horizontal=True,
          key="len_c6",
      )
      obs6 = st.text_area(
          "Observaciones para Organización del relato:", key="obs_c6", height=70
      )

      st.divider()

      st.markdown("**7. Normativa** *(Ponderación 10%)*")
      c7 = st.radio(
          "Nivel:",
          [4, 3, 2, 1],
          format_func=lambda x: {
              4: "4 - Avanzado (Emplea correctamente la normativa)",
              3: "3 - Satisfactorio (Pocos errores que no dificultan)",
              2: "2 - En desarrollo (Errores que dificultan en parte)",
              1: "1 - Inicial (Errores afectan significativamente)",
          }[x],
          horizontal=True,
          key="len_c7",
      )
      obs7 = st.text_area(
          "Observaciones para Normativa:", key="obs_c7", height=70
      )

    promedio_calculado = round(
        (c1 * 0.20)
        + (c2 * 0.20)
        + (c3 * 0.1333)
        + (c4 * 0.1333)
        + (c5 * 0.1334)
        + (c6 * 0.10)
        + (c7 * 0.10),
        2,
    )

    eval_respuestas = {
        "c1": c1,
        "obs1": obs1,
        "c2": c2,
        "obs2": obs2,
        "c3": c3,
        "obs3": obs3,
        "c4": c4,
        "obs4": obs4,
        "c5": c5,
        "obs5": obs5,
        "c6": c6,
        "obs6": obs6,
        "c7": c7,
        "obs7": obs7,
    }

  else:
    with st.container(border=True):
      c1 = st.radio("Criterio 1", [1, 2, 3, 4], horizontal=True, key="gen_c1")
      obs1 = st.text_area(
          "Observaciones Criterio 1:", key="obs_gen1", height=70
      )
      st.divider()
      c2 = st.radio("Criterio 2", [1, 2, 3, 4], horizontal=True, key="gen_c2")
      obs2 = st.text_area(
          "Observaciones Criterio 2:", key="obs_gen2", height=70
      )
      st.divider()
      c3 = st.radio("Criterio 3", [1, 2, 3, 4], horizontal=True, key="gen_c3")
      obs3 = st.text_area(
          "Observaciones Criterio 3:", key="obs_gen3", height=70
      )

    promedio_calculado = round((c1 + c2 + c3) / 3, 2)
    eval_respuestas = {
        "c1": c1,
        "obs1": obs1,
        "c2": c2,
        "obs2": obs2,
        "c3": c3,
        "obs3": obs3,
    }

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
          "promedio": promedio_calculado,
          "respuestas": eval_respuestas,
      }
      try:
        requests.post(WEBAPP_URL, json=payload, timeout=10)
        st.success(
            f"✅ Evaluación guardada con éxito (Promedio:"
            f" {promedio_calculado})!"
        )
        st.cache_data.clear()
      except Exception:
        st.error("⚠️ Error de conexión al guardar la evaluación.")

# ---------------------------------------------------------
# 2. GENERADOR DE CÓDIGOS PARA DUPLAS (6 DÍGITOS ALFANUMÉRICOS + GARANTÍA DE UNICIDAD)
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
              # Integrante 1
              "dni1": dni1,
              "estudiante1": nom1,
              "escuela1": esc1,
              "email1": mail1,
              "puntaje1": punt1,
              # Integrante 2
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
