"""
GeoRisk Finder — Sistema de diseño compartido.

Centraliza paleta de color, CSS y componentes de UI reutilizables para
que las cuatro páginas del dashboard (mapa global, modelo financiero,
panel aseguradora, ayuda humanitaria) compartan una identidad visual
única y coherente.
"""

import streamlit as st

# ──────────────────────────────────────────────
# PALETA — Nexus (teal profesional, tonos tierra)
# ──────────────────────────────────────────────
COLORS = {
    "bg": "#F7F6F2",
    "surface": "#FFFFFF",
    "surface_alt": "#F9F8F5",
    "border": "#E3E0D8",
    "text": "#1C1A15",
    "text_muted": "#6B6A64",
    "primary": "#01696F",
    "primary_dark": "#0C4E54",
    "primary_light": "#20808D",
    "terra": "#A84B2F",
    "gold": "#B37D00",
    "mauve": "#7A3B49",
    "success": "#3A6B1E",
    "warning": "#7A3714",
    "ink": "#0D1B2A",
}

CHART_PALETTE = [
    "#01696F", "#A84B2F", "#0C4E54", "#B37D00",
    "#7A3B49", "#3A6B1E", "#20808D", "#6B6A64",
]

CHART_SCALE_RIESGO = ["#3A6B1E", "#B37D00", "#A84B2F"]
CHART_SCALE_TEAL = ["#D7E9EA", "#20808D", "#0C4E54"]

NIVEL_RANGO = {"Bajo": 0, "Medio": 1, "Alto": 2}
RANGO_A_COLOR = {0: "verde", 1: "naranja", 2: "rojo"}
RANGO_A_NIVEL = {0: "Bajo", 1: "Medio", 2: "Alto"}


def inyectar_tema():
    """Inyecta el CSS global. Llamar una sola vez al principio de cada página."""
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500&display=swap');

        html, body, [class*="css"] { font-family: 'DM Sans', 'Inter', sans-serif; }

        .stApp { background-color: #F7F6F2; }

        #MainMenu, header[data-testid="stHeader"] { background: transparent; }

        h1 {
            color: #0C4E54 !important;
            font-weight: 800 !important;
            letter-spacing: -0.02em;
            border-bottom: 3px solid #01696F;
            padding-bottom: 0.4rem;
            margin-bottom: 0.2rem !important;
        }
        h2, h3 { color: #0C4E54 !important; font-weight: 700 !important; }
        h4 { color: #01696F !important; font-weight: 600 !important; }

        p, li, label { color: #1C1A15; }

        .georisk-kicker {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.72rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: #6B6A64;
            margin-bottom: 0.3rem;
        }

        .georisk-subtitle {
            color: #6B6A64;
            font-size: 1.02rem;
            max-width: 900px;
            margin-bottom: 1.4rem;
            line-height: 1.55;
        }

        div[data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid #E3E0D8;
            border-top: 3px solid #01696F;
            border-radius: 6px;
            padding: 18px 20px 14px 20px;
            box-shadow: 0 1px 3px rgba(13,27,42,0.04);
        }
        div[data-testid="stMetric"] label {
            color: #6B6A64;
            font-size: 0.78rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.04em;
        }
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
            color: #0C4E54;
            font-weight: 800;
            font-size: 1.9rem;
        }
        div[data-testid="stMetricDelta"] { font-size: 0.82rem; }

        section[data-testid="stSidebar"] { background: #0D1B2A; }
        section[data-testid="stSidebar"] * { color: #C9D4D6; }
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3 { color: #F7F6F2 !important; }
        section[data-testid="stSidebar"] hr { border-color: #253746; }
        section[data-testid="stSidebar"] .stSelectbox label,
        section[data-testid="stSidebar"] .stRadio label,
        section[data-testid="stSidebar"] .stCheckbox label,
        section[data-testid="stSidebar"] .stTextInput label,
        section[data-testid="stSidebar"] .stSlider label { color: #8FA3A8 !important; }

        .stTabs [data-baseweb="tab-list"] { gap: 4px; border-bottom: 1px solid #E3E0D8; }
        .stTabs [data-baseweb="tab"] {
            font-weight: 600;
            color: #6B6A64;
            padding: 10px 18px;
        }
        .stTabs [aria-selected="true"] {
            color: #01696F !important;
            border-bottom: 2px solid #01696F !important;
        }

        .stDownloadButton > button, .stButton > button {
            background: #01696F;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 9px 22px;
            font-weight: 600;
            font-size: 0.88rem;
            transition: background 0.15s ease;
        }
        .stDownloadButton > button:hover, .stButton > button:hover { background: #0C4E54; }

        .callout {
            background: #F0F5F5;
            border-left: 3px solid #01696F;
            border-radius: 4px;
            padding: 16px 20px;
            margin: 14px 0;
        }
        .callout h4 { margin-top: 0; }
        .callout p:last-child { margin-bottom: 0; }

        .callout-warn {
            background: #FBF3EC;
            border-left: 3px solid #A84B2F;
            border-radius: 4px;
            padding: 16px 20px;
            margin: 14px 0;
        }
        .callout-warn h4 { margin-top: 0; color: #7A3714 !important; }
        .callout-warn p:last-child { margin-bottom: 0; }

        .badge {
            display: inline-block;
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.72rem;
            font-weight: 600;
            padding: 3px 10px;
            border-radius: 3px;
            letter-spacing: 0.03em;
        }
        .badge-verde { background: #E3EEDA; color: #3A6B1E; }
        .badge-naranja { background: #F5E7CE; color: #7A5A00; }
        .badge-rojo { background: #F2DAD1; color: #7A3714; }
        .badge-gris { background: #E9E8E4; color: #6B6A64; }

        .georisk-footer {
            font-family: 'IBM Plex Mono', monospace;
            font-size: 0.72rem;
            color: #4A5A60;
            letter-spacing: 0.03em;
        }

        .dataframe { border-radius: 6px; overflow: hidden; }
        .dataframe th {
            background: #0C4E54 !important;
            color: #F7F6F2 !important;
            font-weight: 600 !important;
        }
        .dataframe td { background: #FFFFFF !important; }

        hr { border-color: #E3E0D8; margin: 1.4rem 0; }
        
        div[data-testid="stProgress"] > div > div {
            background-color: #01696F !important;
        }
        
    </style>
    """, unsafe_allow_html=True)


def encabezado_pagina(kicker: str, titulo: str, subtitulo: str):
    """Encabezado estandarizado: kicker en mayúsculas + título + subtítulo descriptivo."""
    st.markdown(f'<div class="georisk-kicker">{kicker}</div>', unsafe_allow_html=True)
    st.title(titulo)
    st.markdown(f'<div class="georisk-subtitle">{subtitulo}</div>', unsafe_allow_html=True)


def badge_nivel(nivel: str) -> str:
    mapa_clase = {"verde": "badge-verde", "naranja": "badge-naranja", "rojo": "badge-rojo"}
    clase = mapa_clase.get(nivel, "badge-gris")
    return f'<span class="badge {clase}">{nivel.upper() if nivel else "N/D"}</span>'


def pie_sidebar(seccion: str):
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f'<div class="georisk-footer">GEORISK FINDER<br/>{seccion}<br/>© 2026</div>',
        unsafe_allow_html=True,
    )

def tabla_estilizada(df, columnas_progreso: dict | None = None, **kwargs):
    """
    Envoltorio sobre st.dataframe que anade barras de progreso a columnas
    numericas clave (severidad, indice de prioridad, ROI...) para que las
    tablas mantengan la misma calidad visual que el resto del dashboard.

    columnas_progreso: dict {nombre_columna: (min, max)} para las columnas
    que deben mostrarse como barra de progreso en vez de numero plano.
    """
    import streamlit as st

    column_config = {}
    if columnas_progreso:
        for col, (vmin, vmax) in columnas_progreso.items():
            if col in df.columns:
                column_config[col] = st.column_config.ProgressColumn(
                    col, min_value=vmin, max_value=vmax, format="%.2f"
                )

    st.dataframe(
        df,
        use_container_width=kwargs.pop("use_container_width", True),
        hide_index=kwargs.pop("hide_index", True),
        column_config=column_config,
        **kwargs,
    )


def callout_alcance(titulo: str, cuerpo_html: str):
    """Bloque estandar para explicar que predice el modelo y que no."""
    import streamlit as st
    st.markdown(f"""
    <div class="callout">
    <p><b>{titulo}</b><br>{cuerpo_html}</p>
    </div>
    """, unsafe_allow_html=True)