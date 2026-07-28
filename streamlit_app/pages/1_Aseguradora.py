"""
Página: GeoRisk Finder — Panel Aseguradora
Simulador ilustrativo de prima relativa por zona, basado en el
mismo grid de riesgo (K-Means/DBSCAN) usado en el mapa global.

Se ejecuta como página dentro de main.py (st.navigation), no de forma
independiente. NO lleva st.set_page_config aquí.
"""

import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "processed"

GRID_ENRIQUECIDO_PATH = DATA_DIR / "grid_features_enriquecido.csv"
CLUSTERS_PATH = DATA_DIR / "cluster_labels.csv"
INTERPRETACION_PATH = DATA_DIR / "interpretacion_clusters.csv"
CASOS_ESTUDIO_PATH = DATA_DIR / "casos_estudio.csv"

# Paleta compartida con globo.py y financiero.py (tema Nexus teal),
# reutilizada aquí para que las tres páginas se vean como una sola app.
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

NOMBRES_DISPLAY = {
    "Japon": "Japón",
    "Espana": "España",
    "Chile": "Chile",
    "Venezuela": "Venezuela",
}

COUNTRY_BBOXES = {
    "Japon":     (24.0, 46.0, 122.0, 146.0),
    "Chile":     (-56.0, -17.5, -76.0, -66.0),
    "Venezuela": (0.6, 12.5, -73.5, -59.5),
    "Espana":    (35.9, 43.9, -9.5, 4.4),
}

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
    section[data-testid="stSidebar"] .stTextInput label { color: #9AB0B4; }
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
# Utilidades de texto (búsqueda insensible a tildes)
# ──────────────────────────────────────────────

def _sin_tildes(texto: str) -> str:
    if not isinstance(texto, str):
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


def _centro_bbox(pais):
    bbox = COUNTRY_BBOXES.get(pais)
    if bbox is None:
        return None
    lat_min, lat_max, lon_min, lon_max = bbox
    return ((lat_min + lat_max) / 2, (lon_min + lon_max) / 2)


# ──────────────────────────────────────────────
# Carga de datos (con caché) — cae a datos sintéticos si el fichero no existe
# ──────────────────────────────────────────────

def _datos_sinteticos_clusters(n=300, seed=42):
    rng = np.random.default_rng(seed)
    lat = rng.uniform(-60, 70, n)
    lon = rng.uniform(-180, 180, n)
    cluster_kmeans = rng.integers(0, 4, n)
    cluster_dbscan = np.where(rng.random(n) < 0.08, -1, cluster_kmeans)
    return pd.DataFrame(
        {
            "cell_id": [f"cell_{i}" for i in range(n)],
            "lat": lat,
            "lon": lon,
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
            "nivel_riesgo": ["verde", "verde", "naranja", "rojo"],
        }
    )


def _datos_sinteticos_casos_estudio():
    return pd.DataFrame(
        {
            "pais": ["Japon", "Chile", "Venezuela", "Espana"],
            "n_celdas": [503, 331, 172, 85],
            "cluster_dominante": [2, 4, 1, 4],
            "pct_cluster_dominante": [65.8, 62.2, 57.0, 76.5],
            "nombre_negocio_dominante": [
                "Riesgo ciclonico alto, cercania volcanica alta",
                "Riesgo sismico alto",
                "Riesgo sismico bajo, ciclonico bajo",
                "Riesgo sismico alto",
            ],
        }
    )


def _datos_sinteticos_grid_enriquecido(n=300, seed=1):
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "cell_id": [f"cell_{i}" for i in range(n)],
            "lat": rng.uniform(-60, 70, n),
            "lon": rng.uniform(-180, 180, n),
            "eq_count": rng.integers(0, 50, n),
            "eq_mag_mean": np.round(rng.uniform(2, 7, n), 1),
            "eq_mag_max": np.round(rng.uniform(3, 8.5, n), 1),
            "cyclone_count": rng.integers(0, 15, n),
            "wind_mean": np.round(rng.uniform(20, 120, n), 1),
            "wind_max": np.round(rng.uniform(40, 280, n), 1),
            "dist_nearest_volcano_km": np.round(rng.uniform(0, 800, n), 1),
            "volcano_count": rng.integers(0, 5, n),
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


def limpiar_nan_global(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    columnas_numericas = df.select_dtypes(include=[np.number]).columns
    df[columnas_numericas] = df[columnas_numericas].fillna(0)
    columnas_texto = df.select_dtypes(include=["object"]).columns
    df[columnas_texto] = df[columnas_texto].fillna("")
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
            rango_max = df[niveles_presentes].applymap(
                lambda v: NIVEL_RANGO.get(v, 0)
            ).max(axis=1)
            df["nivel_riesgo"] = rango_max.map(RANGO_A_COLOR)
        else:
            df["nivel_riesgo"] = "desconocido"

    return df


def normalizar_casos_estudio(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    if "pais" in df.columns and "nombre_lugar" not in df.columns:
        df = df.rename(columns={"pais": "nombre_lugar"})

    df["nombre_lugar_display"] = df["nombre_lugar"].map(lambda p: NOMBRES_DISPLAY.get(p, p))
    df["nombre_lugar_normalizado"] = df["nombre_lugar_display"].map(_sin_tildes).str.lower()

    if "lat" not in df.columns or "lon" not in df.columns:
        centros = df["nombre_lugar"].map(_centro_bbox)
        df["lat"] = centros.map(lambda c: c[0] if c else None)
        df["lon"] = centros.map(lambda c: c[1] if c else None)
        df = df.dropna(subset=["lat", "lon"])

    df = asegurar_columnas(
        df,
        {
            "cluster_dominante": "", "pct_cluster_dominante": "",
            "nombre_negocio_dominante": "", "n_celdas": "",
        },
    )
    df["texto_caso_estudio"] = (
        "Perfil dominante: " + df["nombre_negocio_dominante"].astype(str)
        + " (" + df["pct_cluster_dominante"].astype(str) + "% de las "
        + df["n_celdas"].astype(str) + " celdas). "
        + "El resto puede pertenecer a otros perfiles de riesgo."
    )

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

    casos_estudio = normalizar_casos_estudio(
        cargar_csv_o_sintetico(CASOS_ESTUDIO_PATH, _datos_sinteticos_casos_estudio)
    )
    casos_estudio = limpiar_nan_global(casos_estudio)

    grid_enriquecido = cargar_csv_o_sintetico(
        GRID_ENRIQUECIDO_PATH, _datos_sinteticos_grid_enriquecido
    )
    grid_sin_geo = grid_enriquecido.drop(columns=["lat", "lon"], errors="ignore")

    mapa = clusters.merge(interpretacion, on="cluster_kmeans", how="left").merge(
        grid_sin_geo, on="cell_id", how="left"
    )

    mapa = asegurar_columnas(
        mapa,
        {
            "eq_count": 0, "eq_mag_mean": 0, "eq_mag_max": 0,
            "cyclone_count": 0, "wind_mean": 0, "wind_max": 0,
            "dist_nearest_volcano_km": 0, "volcano_count": 0,
            "nombre_cluster": "Sin clasificar", "descripcion_negocio": "",
            "nivel_riesgo": "desconocido",
        },
    )
    mapa = limpiar_nan_global(mapa)

    componente_sismico = (mapa["eq_mag_mean"] / 9).clip(0, 1)
    componente_ciclonico = (mapa["wind_max"] / 250).clip(0, 1)
    componente_volcanico = (50 / (50 + mapa["dist_nearest_volcano_km"])).clip(0, 1)
    mapa["severidad"] = pd.concat(
        [componente_sismico, componente_ciclonico, componente_volcanico], axis=1
    ).max(axis=1)

    return mapa, casos_estudio


# ──────────────────────────────────────────────
# Carga
# ──────────────────────────────────────────────

mapa, casos_estudio = cargar_datos()


# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────

st.sidebar.title("🏢 Panel Aseguradora")
st.sidebar.markdown("---")
st.sidebar.markdown("**Simulador ilustrativo de prima relativa**")
st.sidebar.markdown(
    "Compara la severidad física de una zona frente a la media global, "
    "usando el mismo grid de riesgo del mapa principal."
)
st.sidebar.markdown("---")
st.sidebar.markdown("""
<div class="callout-warn">
<p>⚠️ El multiplicador mostrado es <b>ilustrativo</b>, basado en severidad
física relativa. No constituye una tarifa actuarial real.</p>
</div>
""", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.caption("© 2026 | Perplexity Computer")


# ──────────────────────────────────────────────
# Layout de la página
# ──────────────────────────────────────────────

st.title("🏢 GeoRisk Finder — Panel Aseguradora")
st.caption(
    "Simulador ilustrativo de prima relativa por zona, basado en el mismo "
    "grid de clusters de riesgo (K-Means/DBSCAN) del mapa global."
)

lugar = st.selectbox("Selecciona una zona", casos_estudio["nombre_lugar_display"])
fila_caso = casos_estudio.loc[casos_estudio["nombre_lugar_display"] == lugar].iloc[0]

mapa_tmp = mapa.copy()
mapa_tmp["_dist"] = (mapa_tmp["lat"] - fila_caso["lat"]) ** 2 + (mapa_tmp["lon"] - fila_caso["lon"]) ** 2
celda = mapa_tmp.loc[mapa_tmp["_dist"].idxmin()]

severidad_base_global = mapa['severidad'].mean()
prima_relativa = celda['severidad'] / severidad_base_global
exposicion_estimada = celda['severidad'] * celda['pib_per_capita']  # proxy simple: severidad × riqueza expuesta

col1, col2, col3 = st.columns(3)
col1.metric("Prima relativa sugerida", f"{prima_relativa:.1f}x media global")
col2.metric("Pérdida potencial estimada (proxy)", f"${exposicion_estimada:,.0f} / celda")
col3.metric(
    "Clasificación de suscripción",
    "Rechazar / revisar manual" if celda['cluster_dbscan'] == -1
    else ("Prima alta" if prima_relativa > 2 else "Prima estándar")
)

st.caption("⚠️ Multiplicador y pérdida potencial ilustrativos, basados en severidad física y PIB per cápita como proxy — no son una tarifa actuarial real.")

st.markdown("---")

st.subheader("Detalle de la celda seleccionada")
st.markdown(f"""
<div class="callout">
<p>{celda.get('descripcion_negocio', '')}</p>
</div>
""", unsafe_allow_html=True)

col_a, col_b, col_c, col_d = st.columns(4)
with col_a:
    st.metric("Magnitud media sísmica", f"{celda['eq_mag_mean']:.1f}")
with col_b:
    st.metric("Viento máx. (ciclones)", f"{celda['wind_max']:.0f} km/h")
with col_c:
    st.metric("Distancia a volcán", f"{celda['dist_nearest_volcano_km']:.0f} km")
with col_d:
    st.metric("Severidad normalizada", f"{celda['severidad']:.2f}")

st.markdown("---")

st.subheader("Zonas comparables en el mundo")
mismo_cluster = mapa[mapa['cluster_kmeans'] == celda['cluster_kmeans']]
comparables = mismo_cluster.sample(min(5, len(mismo_cluster)))

comparables_mostrar = comparables[
    ['iso_a3', 'nombre_cluster', 'eq_mag_mean', 'wind_max', 'pib_per_capita']
].rename(columns={
    'iso_a3': 'País', 'nombre_cluster': 'Perfil de riesgo',
    'eq_mag_mean': 'Magnitud sísmica media', 'wind_max': 'Viento máx. (km/h)', 'pib_per_capita': 'PIB per cápita'
})
st.dataframe(comparables_mostrar, hide_index=True)