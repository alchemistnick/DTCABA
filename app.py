import random
from datetime import datetime
import pandas as pd
import requests
import streamlit as st

# ---------------------------------------------------------
# LECTURA DE CONFIGURACIÓN Y CREDENCIALES DESDE ST.SECRETS
# ---------------------------------------------------------
try:
  WEBAPP_URL = st.secrets["WEBAPP_URL"]
  SHEET_ID_EVALS = st.secrets["SHEET_ID_EVALS"]
  ADMIN_PASSWORD = st.secrets["ADMIN_PASSWORD"]
except KeyError as e:
  st.error(f"❌ Error de configuración: Falta definir la clave {e} en `.streamlit/secrets.toml` o en las opciones de Streamlit Cloud.")
  st.stop()

CARACTERES_SEGUROS = "BCDFGHJKLMNPQRSTVWXYZ0123456789"

st.set_page_config(
    page_title="Evaluaciones DTCABA 2026",
    page_icon="📐",
    layout="centered",
    initial_sidebar_state="expanded",
)
