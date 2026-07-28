"""
Página: GeoRisk Finder — Priorización de Ayuda Humanitaria
Índice compuesto de prioridad por país (severidad física + vulnerabilidad
económica + población), sobre el mismo grid de riesgo del mapa global.

Se ejecuta como página dentro de main.py (st.navigation), no de forma
independiente. NO lleva st.set_page_config aquí.
"""

from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "processed"

CLUSTERS_PATH = DATA_DIR / "cluster_labels.csv"
INTERPRETACION_PATH = DATA_DIR / "interpretacion_clusters.csv"
GRID_ENRIQUECIDO_PATH = DATA_DIR / "grid_features_enriquecido.csv"

# Paleta compartida con globo.py / financiero.py / aseguradora.py
# (tema Nexus teal), reutilizada aquí para que todas las páginas
# se vean como una sola app coherente.
COLORS = {
    "bg": "#F7F6F2",
    "surface": "#F9F8F5",
    "text": "#28251D",
    "muted": "#7A7974",
    "primary": "#01696F",
    "primary_dark": "#0C4E54",
    "accent": "#20808D",
    "terra": "#A84B2F",
    "gold": "#D19900",
    "mauve": "#944454",
    "success": "#437A22",
    "warning": "#964219",
}

NIVEL_RANGO = {"Bajo": 0, "Medio": 1, "Alto": 2}
RANGO_A_COLOR = {0: "verde", 1: "naranja", 2: "rojo"}

UMBRAL_ALTO_RIESGO = 0.6

PESO_SEVERIDAD = 0.5
PESO_PIB_INVERTIDO = 0.3
PESO_POBLACION = 0.2

# ──────────────────────────────────────────────
# CSS — mismo tema visual que globo.py / financiero.py
# ──────────────────────────────────────────────
st.markdown("""
<style>
    .stApp { background-color: #F7F6F2; }
    h1, h2, h3 { color: #01696F !important; font-family: 'DM Sans', 'Inter', sans-serif; }
    div[data-testid="stMetric"] {
        background: #F9F8F5;
        border: 1px solid #D4D1CA;
        border-radius: 10px;
        padding: 16px 20px;
    }
    div[data-testid="stMetric"] label { color: #7A7974; font-size: 0.85rem; }
    div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
        color: #01696F;
        font-weight: 800;
    }
    section[data-testid="stSidebar"] { background: #0D1B2A; }
    section[data-testid="stSidebar"] * { color: #E0E1DD; }
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] .stRadio label,
    section[data-testid="stSidebar"] .stCheckbox label,
    section[data-testid="stSidebar"] .stSlider label { color: #9AB0B4; }
    .stDownloadButton > button {
        background: #01696F;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 8px 24px;
        font-weight: 600;
    }
    .stDownloadButton > button:hover { background: #0C4E54; }
    .callout {
        background: #F9F8F5;
        border-left: 4px solid #01696F;
        border-radius: 8px;
        padding: 16px 20px;
        margin: 12px 0;
    }
    .callout-warn {
        background: #FFF8F0;
        border-left: 4px solid #964219;
        border-radius: 8px;
        padding: 16px 20px;
        margin: 12px 0;
    }
    .dataframe { border-radius: 8px; overflow: hidden; }
    .dataframe th { background: #01696F !important; color: white !important; }
    .dataframe td { background: #F9F8F5 !important; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Carga de datos (con caché) — cae a datos sintéticos si el fichero no existe
# ──────────────────────────────────────────────

def _datos_sinteticos_clusters(n=300, seed=42):
    rng = np.random.default_rng(seed)
    cluster_kmeans = rng.integers(0, 4, n)
    cluster_dbscan = np.where(rng.random(n) < 0.08, -1, cluster_kmeans)
    return pd.DataFrame(
        {
            "cell_id": [f"cell_{i}" for i in range(n)],
            "cluster_kmeans": cluster_kmeans,
            "cluster_dbscan": cluster_dbscan,
        }
    )


def _datos_sinteticos_interpretacion():
    return pd.DataFrame(
        {
            "cluster_kmeans": [0, 1, 2, 3],
            "nombre_cluster": [
                "Baja actividad",
                "Sismicidad moderada",
                "Alta sismicidad + ciclones estacionales",
                "Volcánico activo",
            ],
            "descripcion_negocio": [
                "Zona de riesgo bajo, apta para operaciones estándar.",
                "Riesgo sísmico moderado, requiere monitoreo periódico.",
                "Combinación de sismicidad alta y estacionalidad de ciclones.",
                "Proximidad a actividad volcánica activa reciente.",
            ],
            "nivel_sismico": ["Bajo", "Medio", "Alto", "Bajo"],
            "nivel_ciclonico": ["Bajo", "Bajo", "Alto", "Bajo"],
            "nivel_volcanico": ["Bajo", "Bajo", "Medio", "Alto"],
        }
    )


def _datos_sinteticos_grid_enriquecido(n=300, seed=1):
    rng = np.random.default_rng(seed)
    paises_demo = ["JPN", "CHL", "VEN", "ESP", "PHL", "IDN", "MEX", "IND"]
    iso_por_celda = rng.choice(paises_demo, n)
    pib_por_pais = {p: v for p, v in zip(
        paises_demo, rng.uniform(1500, 45000, len(paises_demo))
    )}
    poblacion_por_pais = {p: v for p, v in zip(
        paises_demo, rng.integers(5_000_000, 300_000_000, len(paises_demo))
    )}
    return pd.DataFrame(
        {
            "cell_id": [f"cell_{i}" for i in range(n)],
            "lat": rng.uniform(-60, 70, n),
            "lon": rng.uniform(-180, 180, n),
            "eq_mag_mean": np.round(rng.uniform(2, 7, n), 1),
            "wind_max": np.round(rng.uniform(40, 280, n), 1),
            "dist_nearest_volcano_km": np.round(rng.uniform(0, 800, n), 1),
            "iso_a3": iso_por_celda,
            "pib_per_capita": [pib_por_pais[p] for p in iso_por_celda],
            "poblacion": [poblacion_por_pais[p] for p in iso_por_celda],
        }
    )


@st.cache_data(ttl=600)
def cargar_csv_o_sintetico(path: Path, _generador_sintetico):
    if path.exists():
        return pd.read_csv(path)
    st.sidebar.warning(f"⚠️ No encontrado: {path.name} — usando datos sintéticos de relleno.")
    return _generador_sintetico()


def asegurar_columnas(df: pd.DataFrame, columnas_default: dict) -> pd.DataFrame:
    df = df.copy()
    for col, default in columnas_default.items():
        if col not in df.columns:
            df[col] = default
        else:
            df[col] = df[col].fillna(default)
    return df


def normalizar_interpretacion(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "cluster_kmeans" not in df.columns and "cluster" in df.columns:
        df = df.rename(columns={"cluster": "cluster_kmeans"})
    if "nombre_cluster" not in df.columns and "nombre_negocio" in df.columns:
        df["nombre_cluster"] = df["nombre_negocio"]
    if "descripcion_negocio" not in df.columns and "recomendacion" in df.columns:
        df["descripcion_negocio"] = df["recomendacion"]
    if "nivel_riesgo" not in df.columns:
        niveles_presentes = [
            c for c in ("nivel_sismico", "nivel_ciclonico", "nivel_volcanico") if c in df.columns
        ]
        if niveles_presentes:
            rango_max = df[niveles_presentes].applymap(lambda v: NIVEL_RANGO.get(v, 0)).max(axis=1)
            df["nivel_riesgo"] = rango_max.map(RANGO_A_COLOR)
        else:
            df["nivel_riesgo"] = "desconocido"
    return df


@st.cache_data(ttl=600)
def cargar_datos():
    clusters = cargar_csv_o_sintetico(CLUSTERS_PATH, _datos_sinteticos_clusters)
    clusters = clusters.rename(columns={
        "kmeans_label": "cluster_kmeans",
        "dbscan_label": "cluster_dbscan",
    })

    interpretacion = normalizar_interpretacion(
        cargar_csv_o_sintetico(INTERPRETACION_PATH, _datos_sinteticos_interpretacion)
    )

    # Se lee una sola vez (el original lo leía dos veces por accidente
    # dentro del mismo drop(columns=...)).
    grid_enriquecido = cargar_csv_o_sintetico(
        GRID_ENRIQUECIDO_PATH, _datos_sinteticos_grid_enriquecido
    )
    grid_sin_geo = grid_enriquecido.drop(
        columns=[c for c in ("lat", "lon") if c in grid_enriquecido.columns]
    )

    mapa = clusters.merge(interpretacion, on="cluster_kmeans", how="left").merge(
        grid_sin_geo, on="cell_id", how="left"
    )

    mapa = asegurar_columnas(
        mapa,
        {
            "eq_mag_mean": 0, "wind_max": 0, "dist_nearest_volcano_km": 0,
            "nombre_cluster": "Sin clasificar",
        },
    )

    componente_sismico = (mapa["eq_mag_mean"] / 9).clip(0, 1)
    componente_ciclonico = (mapa["wind_max"] / 250).clip(0, 1)
    componente_volcanico = (50 / (50 + mapa["dist_nearest_volcano_km"])).clip(0, 1)
    mapa["severidad"] = pd.concat(
        [componente_sismico, componente_ciclonico, componente_volcanico], axis=1
    ).max(axis=1)

    return mapa


# ──────────────────────────────────────────────
# Carga
# ──────────────────────────────────────────────

mapa_pais = cargar_datos()

sin_pib = mapa_pais[
    mapa_pais["pib_per_capita"].isna() & mapa_pais["iso_a3"].notna()
]["iso_a3"].unique()

resumen_pais = mapa_pais.groupby("iso_a3").agg(
    severidad_media=("severidad", "mean"),
    pib_per_capita=("pib_per_capita", "first"),
    poblacion=("poblacion", "first"),
    n_celdas_alto_riesgo=("severidad", lambda s: (s > UMBRAL_ALTO_RIESGO).sum()),
).reset_index()

resumen_pais["pib_invertido"] = 1 / resumen_pais["pib_per_capita"].clip(lower=100)
resumen_pais["indice_prioridad"] = (
    resumen_pais["severidad_media"].rank(pct=True) * PESO_SEVERIDAD
    + resumen_pais["pib_invertido"].rank(pct=True) * PESO_PIB_INVERTIDO
    + resumen_pais["poblacion"].rank(pct=True) * PESO_POBLACION
)


# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────

st.sidebar.title("🆘 Ayuda Humanitaria")
st.sidebar.markdown("---")
st.sidebar.markdown("**Índice compuesto de priorización**")
st.sidebar.markdown(
    "Combina severidad física, vulnerabilidad económica y población "
    "para sugerir dónde enfocar intervención preventiva."
)
st.sidebar.markdown("---")
st.sidebar.markdown("**Pesos del índice**")
st.sidebar.markdown(f"""
- Severidad física: **{PESO_SEVERIDAD*100:.0f}%**
- PIB per cápita invertido: **{PESO_PIB_INVERTIDO*100:.0f}%**
- Población: **{PESO_POBLACION*100:.0f}%**
""")
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div class="callout-warn">
<p>⚠️ Los pesos son una decisión de diseño <b>transparente</b>, no un valor
científico fijo — ajustables según la prioridad del organismo que use
esta herramienta.</p>
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.caption("© 2026 | Perplexity Computer")


# ──────────────────────────────────────────────
# Layout de la página
# ──────────────────────────────────────────────

st.title("GeoRisk Finder — Priorización de Ayuda Humanitaria")
st.caption(
    "Ranking de países por índice compuesto de prioridad para intervención "
    "preventiva, calculado sobre el mismo grid de riesgo del mapa global."
)

st.markdown("---")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Países en el ranking", f"{len(resumen_pais)}")
with col2:
    st.metric("Celdas de alto riesgo (global)", f"{(mapa_pais['severidad'] > UMBRAL_ALTO_RIESGO).sum()}")
with col3:
    st.metric("Países sin dato de PIB", f"{len(sin_pib)}")

st.markdown("---")

st.subheader("Top 15 países prioritarios para intervención preventiva")

top_paises = resumen_pais.nlargest(15, "indice_prioridad").copy()
top_paises["pib_per_capita"] = top_paises["pib_per_capita"].apply(
    lambda x: f"${x:,.0f}" if pd.notna(x) else "—"
)
top_paises["indice_prioridad"] = top_paises["indice_prioridad"].apply(lambda x: f"{x:.2f}")
top_paises["severidad_media"] = top_paises["severidad_media"].apply(lambda x: f"{x:.2f}")

st.dataframe(
    top_paises[["iso_a3", "severidad_media", "n_celdas_alto_riesgo", "pib_per_capita", "indice_prioridad"]],
    width="stretch",
    hide_index=True,
)

st.caption(
    "Índice = 50% severidad física + 30% inverso del PIB per cápita + 20% población. "
    "Los pesos son una decisión de diseño transparente, no un valor científico fijo — "
    "ajustables según la prioridad del organismo que use la herramienta."
)

if len(sin_pib) > 0:
    st.markdown(f"""
    <div class="callout-warn">
    <p>⚠️ <b>{len(sin_pib)} países</b> sin dato de PIB del Banco Mundial
    ({', '.join(sin_pib)}) — quedan fuera de este ranking automático
    por falta de datos, no porque su riesgo sea bajo. Requieren revisión manual.</p>
    </div>
    """, unsafe_allow_html=True)