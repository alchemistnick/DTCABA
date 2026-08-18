import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import random
import string

# URL limpia de la planilla DTCABA_2026
URL_SHEET = "https://docs.google.com/spreadsheets/d/1V5rWEolARQ3PlZTbVrrhEWUc7bipJF0t2iMznxjvKgk/edit"

st.set_page_config(page_title="Evaluaciones DTCABA 2026", page_icon="📝", layout="centered")

st.title("Plataforma de Evaluaciones Técnicas")
st.caption("Dirección Técnica - CABA 2026")

# Conexión a Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

opcion = st.sidebar.radio("Navegación", ["Cargar Evaluación", "Generar Códigos Únicos", "Panel de Administración"])

# ---------------------------------------------------------
# 1. CARGAR EVALUACIÓN (EVALUADORES)
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
            try:
                # Lectura de la pestaña "Usuarios"
                df_usuarios = conn.read(spreadsheet=URL_SHEET, worksheet="Usuarios", ttl=0)
                usuario_row = df_usuarios[df_usuarios["id_evaluador"].astype(str) == id_evaluador]

                if usuario_row.empty:
                    st.error("❌ El ID de evaluador no existe en la pestaña 'Usuarios'.")
                else:
                    autorizado = usuario_row.iloc[0]["autorizado"]
                    nombre_evaluador = usuario_row.iloc[0]["nombre"]

                    if str(autorizado).upper() not in ["TRUE", "1", "VERDADERO"]:
                        st.error("❌ Evaluador no autorizado por la Dirección Técnica.")
                    else:
                        # Lectura y actualización de la pestaña "Evaluaciones"
                        df_evaluaciones = conn.read(spreadsheet=URL_SHEET, worksheet="Evaluaciones", ttl=0)

                        nueva_fila = pd.DataFrame([{
                            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "codigo_unico": codigo_unico,
                            "materia": materia,
                            "evaluador_id": id_evaluador,
                            "evaluador_nombre": nombre_evaluador,
                            "c1": c1,
                            "c2": c2,
                            "c3": c3,
                            "promedio": round((c1 + c2 + c3) / 3, 2)
                        }])

                        df_actualizado = pd.concat([df_evaluaciones, nueva_fila], ignore_index=True)
                        conn.update(spreadsheet=URL_SHEET, worksheet="Evaluaciones", data=df_actualizado)

                        st.success(f"✅ Evaluación guardada con éxito para el examen **{codigo_unico}**.")
            except Exception as e:
                st.error(f"Error de conexión con Google Sheets: {e}")

# ---------------------------------------------------------
# 2. GENERADOR DE CÓDIGOS ÚNICOS (PROTEGIDO)
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
# 3. PANEL DE ADMINISTRACIÓN (PROTEGIDO)
# ---------------------------------------------------------
elif opcion == "Panel de Administración":
    st.header("Panel de Administración")
    clave = st.text_input("Clave Administrador", type="password")

    if clave == "admin123":
        tab1, tab2 = st.tabs(["📊 Evaluaciones Registradas", "👤 Gestor de Usuarios"])

        with tab1:
            try:
                st.dataframe(conn.read(spreadsheet=URL_SHEET, worksheet="Evaluaciones", ttl=0), use_container_width=True)
            except Exception as e:
                st.error(f"Error al leer la pestaña 'Evaluaciones': {e}")

        with tab2:
            try:
                df_users = conn.read(spreadsheet=URL_SHEET, worksheet="Usuarios", ttl=0)
                st.dataframe(df_users, use_container_width=True)

                st.markdown("---")
                st.subheader("Autorizar Nuevo Evaluador")
                nuevo_id = st.text_input("ID / Email del evaluador")
                nuevo_nombre = st.text_input("Nombre completo")
                quien_autoriza = st.text_input("Autorizado por", value="Dirección Técnica")

                if st.button("Autorizar Evaluador"):
                    if nuevo_id and nuevo_nombre:
                        df_users = df_users[df_users["id_evaluador"].astype(str) != nuevo_id]
                        nueva_usr = pd.DataFrame([{
                            "id_evaluador": nuevo_id,
                            "nombre": nuevo_nombre,
                            "autorizado": True,
                            "autorizado_por": quien_autoriza
                        }])
                        conn.update(spreadsheet=URL_SHEET, worksheet="Usuarios", data=pd.concat([df_users, nueva_usr], ignore_index=True))
                        st.success(f"Evaluador {nuevo_nombre} guardado en Google Sheets.")
                        st.rerun()
            except Exception as e:
                st.error(f"Error al leer la pestaña 'Usuarios': {e}")
