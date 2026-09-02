import random
from datetime import datetime
import pandas as pd
import requests
import streamlit as st

# ---------------------------------------------------------
# LECTURA TOLERANTE Y SEGURA DESDE ST.SECRETS
# ---------------------------------------------------------
WEBAPP_URL = st.secrets.get(
    "WEBAPP_URL",
    "https://script.google.com/macros/s/AKfycbzt19tpSOAd8HVEW6q8CU5-d9sK9H7jKGnmgI23HVW-aJ3IIqLDL2M3IiAJcwhTCaU0YQ/exec",
)
SHEET_ID_EVALS = st.secrets.get(
    "SHEET_ID_EVALS", "1V5rWEolARQ3PlZTbVrrhEWUc7bipJF0t2iMznxjvKgk"
)
ADMIN_PASSWORD = st.secrets.get("ADMIN_PASSWORD", "admin123")

CARACTERES_SEGUROS = "BCDFGHJKLMNPQRSTVWXYZ0123456789"

st.set_page_config(
    page_title="Evaluaciones DTCABA 2026",
    page_icon="📐",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# ESTILOS ADAPTABLES CORREGIDOS
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
