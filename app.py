import random
import string
from datetime import datetime
import pandas as pd
import requests
import streamlit as st

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbzyiTybfkEMkM_x_-Ist_7DlWObsTN9T3QtCnLyvz-oLpvvDkEYGI_bQTiHKwdTFx9oUw/exec"
SHEET_ID_EVALS = "1V5rWEolARQ3PlZTbVrrhEWUc7bipJF0t2iMznxjvKgk"

# Conjunto seguro sin vocales (evita la formación de cualquier palabra)
CARACTERES_SEGUROS = "BCDFGHJKLMNPQRSTVWXYZ0123456789"

st.set_page_config(
    page_title="Evaluaciones DTCABA 2026", page_icon="📝", layout="centered"
)

st.title("Plataforma de Evaluaciones Técnicas")
st.caption("Dirección Técnica - CABA 2026")

opcion = st.sidebar.radio(
    "Navegación",
    ["Cargar Evaluación", "Generar Códigos Únicos", "Panel de Administración"],
)


# Lectura auxiliar
def leer_pestana(sheet_id, nombre_pestana):
  try:
    url_csv = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={nombre_pestana}"
    return pd.read_csv(url_csv)
  except Exception:
    return pd.DataFrame()


# Búsqueda por DNI a través del receptor de Apps Script
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
# 1. CARGAR EVALUACIÓN
# ---------------------------------------------------------
if opcion == "Cargar Evaluación":
  st.header("Carga de Evaluación")

  col1, col2 = st.columns(2)
  with col1:
    id_evaluador = st.text_input(
        "ID del Evaluador", placeholder="Ej: EVAL-001"
    ).strip()
  with col2:
    codigo_unico = st.text_input(
        "Código Único del Examen", placeholder="Ej: MAT-2026-X8K9"
    ).strip()

  materia = st.selectbox("Materia", ["Matemática", "Lengua"])

  st.subheader("Rúbrica de Evaluación")
  c1 = st.radio(
      "Criterio 1: Razonamiento / Comprensión", [1, 2, 3, 4], horizontal=True
  )
  c2 = st.radio(
      "Criterio 2: Coherencia / Resolución", [1, 2, 3, 4], horizontal=True
  )
  c3 = st.radio(
      "Criterio 3: Dominio Técnico / Gramática", [1, 2, 3, 4], horizontal=True
  )

  if st.button("Guardar en Google Sheets", type="primary"):
    if not id_evaluador or not codigo_unico:
      st.warning("⚠️ Completa el ID de evaluador y el Código Único.")
    else:
      df_usuarios = leer_pestana(SHEET_ID_EVALS, "Usuarios")
      if not df_usuarios.empty and "id_evaluador" in df_usuarios.columns:
        usuario_row = df_usuarios[
            df_usuarios["id_evaluador"].astype(str) == id_evaluador
        ]

        if usuario_row.empty:
          st.error(
              "❌ El ID de evaluador no existe en la pestaña 'Usuarios'."
          )
        else:
          autorizado = usuario_row.iloc[0]["autorizado"]
          nombre_evaluador = usuario_row.iloc[0]["nombre"]

          if str(autorizado).upper() not in ["TRUE", "1", "VERDADERO"]:
            st.error("❌ Evaluador no autorizado por la Dirección Técnica.")
          else:
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
                "promedio": round((c1 + c2 + c3) / 3, 2),
            }

            res = requests.post(WEBAPP_URL, json=payload)
            if res.status_code == 200:
              st.success(
                  f"✅ Evaluación guardada con éxito para el examen"
                  f" **{codigo_unico}**."
              )
              st.rerun()
            else:
              st.error("Error al enviar los datos a Google Sheets.")
      else:
        st.error("Error al acceder a la lista de usuarios en Google Sheets.")

# ---------------------------------------------------------
# 2. GENERADOR DE CÓDIGOS ÚNICOS (SEGURO)
# ---------------------------------------------------------
elif opcion == "Generar Códigos Únicos":
  st.header("Generador de Códigos Únicos")
  clave_codigos = st.text_input(
      "Ingrese Contraseña Autorizada", type="password"
  )

  if clave_codigos == "admin123":
    st.success("Acceso concedido.")
    st.subheader("Búsqueda en Padrón de Encuentros Educativos")

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

    col_est1, col_est2 = st.columns(2)
    with col_est1:
      nombre_estudiante = st.text_input(
          "Nombre y Apellido", value=nombre_defecto
      )
    with col_est2:
      escuela_estudiante = st.text_input(
          "Escuela / Institución", value=escuela_defecto
      )

    prefijo = st.selectbox("Materia de la Evaluación", ["MAT", "LEN"])

    if st.button("Generar y Asignar Código Único", type="primary"):
      if not dni_input or not nombre_estudiante or not escuela_estudiante:
        st.warning("⚠️ Debes completar DNI, Nombre y Escuela.")
      else:
        # Selección segura utilizando únicamente el conjunto sin vocales
        aleatorio = "".join(random.choices(CARACTERES_SEGUROS, k=4))
        codigo_generado = f"{prefijo}-2026-{aleatorio}"

        st.subheader("Código Asignado")
        st.code(codigo_generado, language="text")

        df_asignacion = pd.DataFrame([{
            "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "DNI": dni_input,
            "Codigo_Unico": codigo_generado,
            "Estudiante": nombre_estudiante,
            "Escuela": escuela_estudiante,
            "Puntaje_Institucional": puntaje_defecto,
            "Materia": "Matemática" if prefijo == "MAT" else "Lengua",
        }])
        st.dataframe(df_asignacion, use_container_width=True)

  elif clave_codigos != "":
    st.error("❌ Contraseña incorrecta.")

# ---------------------------------------------------------
# 3. PANEL DE ADMINISTRACIÓN
# ---------------------------------------------------------
elif opcion == "Panel de Administración":
  st.header("Panel de Administración")
  clave = st.text_input("Clave Administrador", type="password")

  if clave == "admin123":
    tab1, tab2 = st.tabs(
        ["📊 Evaluaciones Registradas", "👤 Gestor de Usuarios"]
    )

    with tab1:
      df_evals = leer_pestana(SHEET_ID_EVALS, "Evaluaciones")
      if not df_evals.empty:
        st.dataframe(df_evals, use_container_width=True)
      else:
        st.info("No hay evaluaciones registradas aún.")

    with tab2:
      df_users = leer_pestana(SHEET_ID_EVALS, "Usuarios")
      if not df_users.empty:
        st.dataframe(df_users, use_container_width=True)

      st.markdown("---")
      st.subheader("Autorizar Nuevo Evaluador")

      cant_usuarios = len(df_users) if not df_users.empty else 0
      nuevo_id = f"EVAL-{cant_usuarios + 1:03d}"
      st.info(f"🆔 **ID asignado automáticamente:** `{nuevo_id}`")

      nuevo_nombre = st.text_input("Nombre completo del evaluador")
      quien_autoriza = st.text_input(
          "Autorizado por", value="Dirección Técnica"
      )

      if st.button("Autorizar Evaluador", type="primary"):
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
            st.rerun()
          else:
            st.error("Error al registrar el usuario en Google Sheets.")
        else:
          st.warning("⚠️ Debes ingresar el Nombre completo del evaluador.")
