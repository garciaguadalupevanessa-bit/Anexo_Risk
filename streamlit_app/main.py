import streamlit as st

st.set_page_config(
    page_title="GeoRisk Finder + Catástrofes vs EWS",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

pagina_financiero = st.Page("pages/financiero.py", title="Catástrofes vs Alerta Temprana", icon="💰", default=True)
pagina_globo = st.Page("pages/globo.py", title="Mapa de Riesgo Global", icon="🌐")
pagina_aseguradora = st.Page("pages/1_Aseguradora.py", title="Panel Aseguradora", icon="🏢")  # pon el nombre exacto del archivo
pagina_humanitaria = st.Page("pages/2_Ayuda_Humanitaria.py", title="Ayuda Humanitaria", icon="🆘")   # idem

navegacion = st.navigation([pagina_financiero, pagina_globo, pagina_aseguradora, pagina_humanitaria])
navegacion.run()