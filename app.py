import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import requests
from datetime import datetime
import random
import string

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbymy1q6qXooXlR_C2vJm7J6PUhbKJSlkAZqiD5MkEdWae29F4wmuf-PjbWt6tgACtRsoQ/exec"
URL_SHEET = "https://docs.google.com/spreadsheets/d/1V5rWEolARQ3PlZTbVrrhEWUc7bipJF0t2iMznxjvKgk/edit"

st.set_page_config(page_title="Evaluaciones DTCABA 2026", page_icon="📝", layout="centered")

st.title("Plataforma de Evaluaciones Técnicas")
st.caption("Dirección Técnica - CABA 2026")

conn = st.connection("gsheets", type=GSheetsConnection)

opcion = st.sidebar.radio("Navegación", ["Cargar Evaluación", "Generar Códigos Únicos", "Panel de Administración"])

# Función para lectura pública
def leer_pestana(nombre_pestana):
    try:
        return conn.read(spreadsheet=URL_SHEET, worksheet=nombre_pestana, ttl=0)
    except Exception as e:
        st.warning(f"⚠️ No se pudo leer la pestaña '{nombre_pestana}'. Verifica los nombres en Google Sheets.")
        return pd.DataFrame()

# ---------------------------------------------------------
# 1. CARGAR EVALUACIÓN
# ---------------------------------------------------------
if opcion == "Cargar Evaluación":
    st.header("Carga de Evaluación")

    col1, col2 = st.columns(2)
    with col1:
        id_evaluador = st.text_input("ID / Email del Evaluador").strip()
    with col2:
        codigo_unico = st.text_input("Código Único del Examen").strip()

    materia = st.selectbox("Materia", ["Matemática", "Lengua"])

    st.subheader("Rúbrica de Evaluación")
    c1 = st.radio("Criterio 1: Razonamiento / Comprensión", [1, 2, 3, 4], horizontal=True)
    c2 = st.radio("Criterio 2: Coherencia / Resolución", [1, 2, 3, 4], horizontal=True)
    c3 = st.radio("Criterio 3: Dominio Técnico / Gramática", [1, 2, 3, 4], horizontal=True)

    if st.button("Guardar en Google Sheets", type="primary"):
        if not id_evaluador or not codigo_unico:
            st.warning("⚠️ Completa el ID de evaluador y el Código Único.")
        else:
            df_usuarios = leer_pestana("Usuarios")
            if not df_usuarios.empty and "id_evaluador" in df_usuarios.columns:
                usuario_row = df_usuarios[df_usuarios["id_evaluador"].astype(str) == id_evaluador]

                if usuario_row.empty:
                    st.error("❌ El ID de evaluador no existe en la pestaña 'Usuarios'.")
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
                            "promedio": round((c1 + c2 + c3) / 3, 2)
                        }

                        res = requests.post(WEBAPP_URL, json=payload)
                        if res.status_code == 200:
                            st.success(f"✅ Evaluación guardada con éxito para el examen **{codigo_unico}**.")
                        else:
                            st.error("Error al enviar los datos al receptor Apps Script.")
            else:
                st.error("Error al acceder a la lista de usuarios. Revisa la pestaña 'Usuarios' en Google Sheets.")

# ---------------------------------------------------------
# 2. GENERADOR DE CÓDIGOS ÚNICOS
# ---------------------------------------------------------
elif opcion == "Generar Códigos Únicos":
    st.header("Generador de Códigos Únicos")
    clave_codigos = st.text_input("Ingrese Contraseña Autorizada", type="password")

    if clave_codigos == "admin123":
        st.success("Acceso concedido.")
        st.subheader("Datos del Estudiante")

        col_est1, col_est2 = st.columns(2)
        with col_est1:
            nombre_estudiante = st.text_input("Nombre y Apellido del Estudiante")
        with col_est2:
            escuela_estudiante = st.text_input("Escuela / Institución")

        prefijo = st.selectbox("Materia de la Evaluación", ["MAT", "LEN"])

        if st.button("Generar y Asignar Código Único", type="primary"):
            if not nombre_estudiante or not escuela_estudiante:
                st.warning("⚠️ Debes ingresar el Nombre del estudiante y la Escuela.")
            else:
                aleatorio = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
                codigo_generado = f"{prefijo}-2026-{aleatorio}"

                st.subheader("Código Asignado")
                st.code(codigo_generado, language="text")

                df_asignacion = pd.DataFrame([{
                    "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Codigo_Unico": codigo_generado,
                    "Estudiante": nombre_estudiante,
                    "Escuela": escuela_estudiante,
                    "Materia": "Matemática" if prefijo == "MAT" else "Lengua"
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
        tab1, tab2 = st.tabs(["📊 Evaluaciones Registradas", "👤 Gestor de Usuarios"])

        with tab1:
            df_evals = leer_pestana("Evaluaciones")
            if not df_evals.empty:
                st.dataframe(df_evals, use_container_width=True)
            else:
                st.info("No hay evaluaciones registradas o la pestaña está vacía.")

        with tab2:
            df_users = leer_pestana("Usuarios")
            if not df_users.empty:
                st.dataframe(df_users, use_container_width=True)

            st.markdown("---")
            st.subheader("Autorizar Nuevo Evaluador")
            nuevo_id = st.text_input("ID / Email del evaluador")
            nuevo_nombre = st.text_input("Nombre completo")
            quien_autoriza = st.text_input("Autorizado por", value="Dirección Técnica")

            if st.button("Autorizar Evaluador"):
                if nuevo_id and nuevo_nombre:
                    payload = {
                        "action": "usuario",
                        "id_evaluador": nuevo_id,
                        "nombre": nuevo_nombre,
                        "autorizado_por": quien_autoriza
                    }
                    res = requests.post(WEBAPP_URL, json=payload)
                    if res.status_code == 200:
                        st.success(f"Evaluador {nuevo_nombre} guardado correctamente en Google Sheets.")
                        st.rerun()
                    else:
                        st.error("Error al registrar el usuario mediante Apps Script.")
