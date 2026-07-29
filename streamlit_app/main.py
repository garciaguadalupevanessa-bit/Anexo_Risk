"""
GeoRisk Finder — Punto de entrada del dashboard.

Configura la app y define la navegación multipagina. Cada página vive
en streamlit_app/pages/ y comparte el tema visual definido en theme.py.
"""

from pathlib import Path

import streamlit as st

ASSETS = Path(__file__).parent / "assets"

st.set_page_config(
    page_title="GeoRisk Finder",
    page_icon=str(ASSETS / "favicon.png") if (ASSETS / "favicon.png").exists() else "🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

pagina_mapa = st.Page(
    "pages/mapa_global.py", title="Mapa global de riesgo", icon=":material/public:", default=True
)
pagina_financiero = st.Page(
    "pages/modelo_financiero.py", title="Modelo financiero EWS", icon=":material/finance_mode:"
)
pagina_aseguradora = st.Page(
    "pages/panel_aseguradora.py", title="Panel aseguradora", icon=":material/domain:"
)
pagina_humanitaria = st.Page(
    "pages/ayuda_humanitaria.py", title="Ayuda humanitaria", icon=":material/emergency:"
)

nav = st.navigation([pagina_mapa, pagina_financiero, pagina_aseguradora, pagina_humanitaria])
nav.run()