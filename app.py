from datetime import datetime
import io
import random
import pandas as pd
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore

# ---------------------------------------------------------
# CONFIGURACIÓN E INICIALIZACIÓN DE FIREBASE
# ---------------------------------------------------------
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

# Inicializar Firebase Admin SDK si no está cargado
if not firebase_admin._apps:
    try:
        # Intenta cargar desde Streamlit Secrets si existe, de lo contrario del archivo local
        if "firebase" in st.secrets:
            cred_dict = dict(st.secrets["firebase"])
            cred = credentials.Certificate(cred_dict)
        else:
            cred = credentials.Certificate("firebase_credentials.json")
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"⚠️ Error al inicializar Firebase: {e}")
        st.stop()

db = firestore.client()

# Ocultar estilos de Streamlit
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# ESTILOS CSS PERSONALIZADOS
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@600;700;800&family=Inter:wght@400;500;600&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    section[data-testid="stSidebar"] { background-color: #0F172A !important; padding-top: 1rem; }
    section[data-testid="stSidebar"] * { color: #F8FAFC !important; }

    section[data-testid="stSidebar"] div[role="radiogroup"] { gap: 0.3rem !important; }
    section[data-testid="stSidebar"] div[role="radiogroup"] label {
        background-color: transparent !important;
        border: none !important;
        padding: 0.4rem 0.6rem !important;
        border-radius: 8px !important;
    }
    section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
        background-color: rgba(255, 255, 255, 0.08) !important;
    }

    .app-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%) !important;
        padding: 1.8rem 2rem; 
        border-radius: 16px; 
        margin-bottom: 2rem; 
        text-align: center;
        box-shadow: 0 10px 15px -3px rgba(15, 23, 42, 0.3);
    }
    .app-header h1 { font-family: 'Poppins', sans-serif; font-size: 2.2rem; font-weight: 800; margin: 0; color: #FFFFFF !important; }
    .app-header p { margin: 0.4rem 0 0 0; color: #94A3B8 !important; font-weight: 500; }

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
    div[data-testid="stMetric"] label { color: #94A3B8 !important; font-weight: 600; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #38BDF8 !important; font-weight: 800; }

    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #2563EB 0%, #1D4ED8 100%) !important;
        color: #FFFFFF !important; 
        border: none; border-radius: 10px; padding: 0.75rem 1.5rem; font-weight: 600; width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# FUNCIONES AUXILIARES DE FIREBASE
# ---------------------------------------------------------
def buscar_estudiante_padron_db(dni):
    dni_limpio = str(dni).strip().replace(".", "").replace(" ", "")
    if not dni_limpio:
        return []
    try:
        docs = db.collection("padron").where("dni", "==", dni_limpio).stream()
        res = [doc.to_dict() for doc in docs]
        return res
    except Exception as e:
        st.error(f"Error consultando padrón: {e}")
        return []

def obtener_codigos_equipos_db():
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
opcion = st.sidebar.radio(
    "Navegación",
    ["Cargar Evaluación", "Generar Códigos / Equipos (Multi-Dupla)", "📌 Acreditación de Presentes", "📊 Reportes y Exportación Excel"],
    label_visibility="collapsed",
)

# ---------------------------------------------------------
# MÓDULO 1: EVALUACIÓN DTCABA
# ---------------------------------------------------------
if evento_seleccionado == "📐 Desafíos Técnicos DTCABA" and opcion == "Cargar Evaluación":
    st.markdown("""<div class="app-header"><h1>📐 Desafíos Técnicos DTCABA ⚙️</h1><p>Sistema de Evaluación Firestore</p></div>""", unsafe_allow_html=True)
    st.header("Carga de Evaluación DTCABA")
    
    lista_codigos = obtener_codigos_equipos_db()

    with st.container(border=True):
        col1, col2 = st.columns(2)
        with col1:
            dni_evaluador = st.text_input("DNI del Evaluador", placeholder="Ingresa tu DNI", key="eval_dni").strip().replace(".", "")
        with col2:
            if lista_codigos:
                seleccion = st.selectbox("Código Único del Examen", options=["-- Seleccionar --"] + lista_codigos + ["✏️ Tipear manualmente"], key="eval_codigo_select")
                codigo_unico = st.text_input("Código Manual", key="eval_cod_manual").upper() if seleccion == "✏️ Tipear manualmente" else (seleccion if seleccion != "-- Seleccionar --" else "")
            else:
                codigo_unico = st.text_input("Código Único del Examen", key="eval_codigo_directo").strip().upper()

        materia = st.selectbox("Materia", ["Lengua", "Matemática", "Tecnología de la Representación Nivel 1", "Tecnología de la Representación Nivel 2"], key="eval_materia")

    if not codigo_unico:
        st.info("💡 Por favor, selecciona o ingresa el Código Único del Examen.")
        st.stop()

    st.subheader(f"📋 Rúbrica de Evaluación: {materia}")

    if materia == "Lengua":
        map_len = {4: "4 - Avanzado", 3: "3 - Satisfactorio", 2: "2 - En desarrollo", 1: "1 - Inicial"}
        c1 = st.radio("Apropiación del texto fuente (50%):", [4, 3, 2, 1], format_func=lambda x: map_len[x], key="len_c1")
        obs1 = st.text_area("Observaciones Criterio 1:", key="obs_c1", height=70)
        c2 = st.radio("Transformación del género (50%):", [4, 3, 2, 1], format_func=lambda x: map_len[x], key="len_c2")
        obs2 = st.text_area("Observaciones Criterio 2:", key="obs_c2", height=70)
        puntaje_100 = round((((c1 * 0.5) + (c2 * 0.5)) / 4) * 100, 2)
        eval_respuestas = {"c1_desc": map_len[c1], "obs1": obs1, "c2_desc": map_len[c2], "obs2": obs2}
    else:
        c1 = st.radio("Evaluación General (100%):", [4, 3, 2, 1], key="tdr_c1")
        obs1 = st.text_area("Observaciones:", key="obs_tdr1", height=70)
        puntaje_100 = round((c1 / 4) * 100, 2)
        eval_respuestas = {"c1_desc": f"Nivel {c1}", "obs1": obs1}

    st.metric(label="Puntaje Total", value=f"{puntaje_100} / 100 pts")

    if st.button("💾 Guardar Evaluación DTCABA", type="primary"):
        doc_data = {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "codigo_unico": codigo_unico,
            "evento": "DTCABA",
            "materia": materia,
            "evaluador_id": dni_evaluador,
            "evaluador_nombre": f"Evaluador DNI {dni_evaluador}",
            "promedio": puntaje_100,
            "especialidad": "General",
            "respuestas": eval_respuestas
        }
        db.collection("evaluaciones").add(doc_data)
        st.success(f"✅ Evaluación guardada con éxito para el código {codigo_unico}.")

# ---------------------------------------------------------
# MÓDULO 2: EVALUACIÓN HACKATHON (8 CRITERIOS Y OBSERVACIONES)
# ---------------------------------------------------------
elif evento_seleccionado == "🏆 Hackathon 2026" and opcion == "Cargar Evaluación":
    st.markdown("""<div class="app-header"><h1>🏆 Hackathon 2026 🚀</h1><p>Sistema de Evaluación Firestore</p></div>""", unsafe_allow_html=True)
    st.header("Carga de Evaluación Hackathon 2026")
    
    with st.container(border=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            dni_evaluador = st.text_input("DNI Evaluador", key="hk_eval_dni").strip().replace(".", "")
        with col2:
            codigo_equipo = st.text_input("Código de Equipo / Proyecto", key="hk_cod_equipo").strip().upper()
        with col3:
            especialidad_hk = st.selectbox("Especialidad del Proyecto", ESPECIALIDADES, key="hk_esp_select")

    st.subheader("📊 Rúbrica de Evaluación (8 Criterios / 100 pts)")

    map_criterios = {12.5: "12.5 - Excelente", 9.0: "9.0 - Satisfactorio", 5.0: "5.0 - En Desarrollo", 0.0: "0.0 - Inicial"}

    criterios_titulos = [
        "1. Definición del Problema / Escenario",
        "2. Innovación y Creatividad de la Solución",
        "3. Viabilidad Técnica e Infraestructura",
        "4. Enfoque Interdisciplinario y Aplicación de Especialidad",
        "5. Comunicación y Presentación del Pitch",
        "6. Impacto y Atención a la Comunidad",
        "7. Operación, Logística y Trabajo en Equipo",
        "8. Prototipado o Modelo Funcional Presentado"
    ]

    respuestas_hk = {}
    suma_puntos = 0.0

    for i in range(1, 9):
        with st.container(border=True):
            st.markdown(f"#### {criterios_titulos[i-1]}")
            val = st.radio(f"Puntaje Criterio {i}:", [12.5, 9.0, 5.0, 0.0], format_func=lambda x: map_criterios[x], key=f"hk_c{i}")
            obs = st.text_area(f"Observación Criterio {i}:", key=f"hk_obs{i}", height=65)
            
            suma_puntos += val
            respuestas_hk[f"c{i}_desc"] = map_criterios[val]
            respuestas_hk[f"obs{i}"] = obs

    puntaje_final_hk = round(suma_puntos, 2)
    st.metric(label="🎯 Puntaje Total Hackathon", value=f"{puntaje_final_hk} / 100 pts")

    if st.button("🚀 Guardar Evaluación Hackathon", type="primary"):
        if not dni_evaluador or not codigo_equipo:
            st.warning("⚠️ Completa el DNI del evaluador y el código del equipo.")
        else:
            doc_data = {
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "codigo_unico": codigo_equipo,
                "evento": "Hackathon 2026",
                "materia": "HACKATHON",
                "evaluador_id": dni_evaluador,
                "evaluador_nombre": f"Jurado DNI {dni_evaluador}",
                "promedio": puntaje_final_hk,
                "especialidad": especialidad_hk,
                "respuestas": respuestas_hk
            }
            db.collection("evaluaciones").add(doc_data)
            st.success("🎉 ¡Evaluación de Hackathon guardada en Firebase!")

# ---------------------------------------------------------
# MÓDULO 3: GENERADOR DE EQUIPOS MULTI-DUPLA / MULTI-INTEGRANTE
# ---------------------------------------------------------
elif opcion == "Generar Códigos / Equipos (Multi-Dupla)":
    st.header(f"Generador de Equipos (Múltiples Integrantes / Duplas) - {evento_seleccionado}")
    clave = st.text_input("Contraseña de Acceso", type="password")

    if clave == ADMIN_PASSWORD:
        st.success("🔓 Acceso habilitado.")
        
        col_a, col_b = st.columns(2)
        with col_a:
            prefijo_mat = st.selectbox("Materia / Categoría", ["HACKATHON", "MAT", "LEN", "TDR1", "TDR2"])
        with col_b:
            especialidad_equipo = st.selectbox("Especialidad Técnica", ESPECIALIDADES)

        nombre_equipo = st.text_input("Nombre del Equipo / Proyecto", placeholder="Ej: Los Ingenieros 2026")

        st.markdown("#### 👥 Carga de Integrantes y Duplas")
        cant_integrantes = st.number_input("Cantidad Total de Estudiantes en el Equipo", min_value=1, max_value=20, value=2)

        integrantes = []
        for idx in range(1, cant_integrantes + 1):
            with st.container(border=True):
                st.markdown(f"**Estudiante #{idx}**")
                col1, col2, col3, col4 = st.columns([2, 3, 3, 3])
                
                with col1:
                    dni_in = st.text_input(f"DNI #{idx}", key=f"multi_dni_{idx}").strip().replace(".", "")
                
                nom_val, esc_val, mail_val = "", "", ""
                if dni_in:
                    padron_res = buscar_estudiante_padron_db(dni_in)
                    if padron_res:
                        nom_val = padron_res[0].get("nombre", "")
                        esc_val = padron_res[0].get("escuela", "")
                        mail_val = padron_res[0].get("email", "")

                with col2:
                    nom_in = st.text_input(f"Nombre #{idx}", value=nom_val, key=f"multi_nom_{idx}")
                with col3:
                    esc_in = st.text_input(f"Escuela #{idx}", value=esc_val, key=f"multi_esc_{idx}")
                with col4:
                    mail_in = st.text_input(f"Email #{idx}", value=mail_val, key=f"multi_mail_{idx}")

                integrantes.append({
                    "posicion": idx,
                    "dni": dni_in,
                    "nombre": nom_in,
                    "escuela": esc_in,
                    "email": mail_in
                })

        if st.button("🎲 Generar / Guardar Equipo en Firebase", type="primary"):
            tres_aleatorios = "".join(random.choices(CARACTERES_SEGUROS, k=3))
            primer_dni = integrantes[0]["dni"] if integrantes else "000"
            codigo_generado = f"{tres_aleatorios}{primer_dni[-3:] if len(primer_dni) >= 3 else primer_dni.zfill(3)}"

            doc_equipo = {
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "codigo_unico": codigo_generado,
                "nombre_equipo": nombre_equipo,
                "evento": evento_seleccionado,
                "materia": prefijo_mat,
                "especialidad": especialidad_equipo,
                "cant_integrantes": len(integrantes),
                "integrantes": integrantes
            }

            db.collection("equipos").add(doc_equipo)
            st.success(f"✅ Equipo Guardado. Código Único Asignado: **{codigo_generado}**")
            st.code(codigo_generado)

# ---------------------------------------------------------
# MÓDULO 4: ACREDITACIÓN DE PRESENTES UNIFICADA
# ---------------------------------------------------------
elif opcion == "📌 Acreditación de Presentes":
    st.header(f"📌 Acreditación de Presentes ({evento_seleccionado})")
    dni_acreditar = st.text_input("Ingresar DNI a Acreditar", placeholder="Ej: 39098198").strip().replace(".", "")

    if dni_acreditar:
        coincidencias = buscar_estudiante_padron_db(dni_acreditar)

        if coincidencias:
            st.success(f"✅ Estudiante Encontrado en Padrón ({len(coincidencias)} registros)")
            
            for idx, estudiante in enumerate(coincidencias):
                with st.container(border=True):
                    st.markdown(f"### ✏️ Validar Registro #{idx+1}")
                    col1, col2 = st.columns(2)
                    with col1:
                        nombre_edit = st.text_input("Nombre y Apellido", value=estudiante.get("nombre", ""), key=f"acred_nom_{idx}")
                        escuela_edit = st.text_input("Escuela", value=estudiante.get("escuela", ""), key=f"acred_esc_{idx}")
                        inscripcion_edit = st.text_input("Inscripción / Desafío", value=estudiante.get("inscripcion", ""), key=f"acred_insc_{idx}")
                        nivel_edit = st.text_input("Nivel", value=estudiante.get("nivel", ""), key=f"acred_niv_{idx}")
                    
                    with col2:
                        email_est_edit = st.text_input("Email Estudiante", value=estudiante.get("email", ""), key=f"acred_mail_est_{idx}")
                        docente_val = estudiante.get("email_docente", "")
                        email_doc_edit = st.text_input("Mail Docente", value="" if docente_val == "Sin Datos" else docente_val, key=f"acred_mail_doc_{idx}")
                        
                        esp_padr = estudiante.get("especialidad", "General")
                        idx_esp = ESPECIALIDADES.index(esp_padr) if esp_padr in ESPECIALIDADES else 6
                        especialidad_edit = st.selectbox("Especialidad Técnica", ESPECIALIDADES, index=idx_esp, key=f"acred_esp_{idx}")

                    if st.button(f"✅ Confirmar Presente en {evento_seleccionado} - Reg #{idx+1}", key=f"acreditar_{idx}", type="primary"):
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
                            "evento": evento_seleccionado
                        }
                        db.collection("acreditaciones").add(doc_presente)
                        st.success(f"🎉 ¡{nombre_edit} acreditado/a con éxito en {evento_seleccionado}!")
        else:
            st.warning("⚠️ No se encontró el DNI en el padrón.")

# ---------------------------------------------------------
# MÓDULO 5: REPORTES Y EXPORTACIÓN A EXCEL / CSV
# ---------------------------------------------------------
elif opcion == "📊 Reportes y Exportación Excel":
    st.header("📊 Centro de Descargas y Reportes en Vivo")
    st.markdown("Cualquier usuario con la clave de autorización puede generar y descargar el reporte consolidado en **Excel** o **CSV**.")

    clave_rep = st.text_input("Ingresar Clave de Acceso para Descargar Reportes", type="password")

    if clave_rep == ADMIN_PASSWORD:
        st.success("🔓 Clave correcta. Generando reportes desde Firebase...")

        # 1. Obtener Evaluaciones
        docs_evals = db.collection("evaluaciones").stream()
        list_evals = [d.to_dict() for d in docs_evals]
        df_evals = pd.DataFrame(list_evals) if list_evals else pd.DataFrame()

        # 2. Obtener Equipos
        docs_equipos = db.collection("equipos").stream()
        list_equipos = [d.to_dict() for d in docs_equipos]
        df_equipos = pd.DataFrame(list_equipos) if list_equipos else pd.DataFrame()

        # 3. Obtener Acreditaciones (Presentes)
        docs_acred = db.collection("acreditaciones").stream()
        list_acred = [d.to_dict() for d in docs_acred]
        df_acred = pd.DataFrame(list_acred) if list_acred else pd.DataFrame()

        st.subheader("📈 Vista Previa de los Datos")
        tab1, tab2, tab3 = st.tabs(["📊 Evaluaciones", "🔑 Equipos / Codigos", "📌 Acreditaciones"])

        with tab1:
            st.dataframe(df_evals, use_container_width=True)
        with tab2:
            st.dataframe(df_equipos, use_container_width=True)
        with tab3:
            st.dataframe(df_acred, use_container_width=True)

        st.markdown("---")
        st.subheader("📥 Descargar Reporte Completo")

        # Preparar diccionario de DataFrames para el Excel
        dict_dfs = {
            "Evaluaciones": df_evals,
            "Equipos": df_equipos,
            "Presentes_Acreditados": df_acred
        }

        excel_data = generar_excel_descarga(dict_dfs)

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.download_button(
                label="🟢 Descargar Libro Excel Completo (.xlsx)",
                data=excel_data,
                file_name=f"Reporte_Consolidado_DTCABA_Hackathon_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with col_d2:
            if not df_evals.empty:
                csv_data = df_evals.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📄 Descargar Solo Evaluaciones (CSV)",
                    data=csv_data,
                    file_name="evaluaciones.csv",
                    mime="text/csv"
                )
