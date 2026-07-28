"""
GeoRisk Finder — Demo (globo 3D)
=================================
Streamlit + pydeck (deck.gl GlobeView) vía streamlit-deckgl.

Esqueleto listo para enchufar los CSVs reales en cuanto lleguen:
- data/processed/clusters_finales.csv (Persona 5)
- docs/interpretacion_clusters.csv (Persona 6)
- docs/casos_estudio.csv (Persona 6)
- data/processed/grid_features.csv (tú)

Ejecutar con: streamlit run demo/app.py
"""

import time
import unicodedata
from pathlib import Path

import folium
import numpy as np
import pandas as pd
import pydeck as pdk
import requests
import streamlit as st
from streamlit_deckgl import st_deckgl
from streamlit_folium import st_folium

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

DATA_DIR = Path("data/processed")

CLUSTERS_PATH = DATA_DIR / "cluster_labels.csv"
INTERPRETACION_PATH = DATA_DIR / "interpretacion_clusters.csv"
CASOS_ESTUDIO_PATH = DATA_DIR / "casos_estudio.csv"
GRID_FEATURES_PATH = DATA_DIR / "grid_features.csv"

# Paleta fallback por nivel de riesgo genérico (si no se puede calcular
# el riesgo dominante por tipo, ej. faltan columnas nivel_sismico/etc.)
COLOR_POR_RIESGO = {
    "verde": [46, 204, 113],
    "naranja": [230, 126, 34],
    "rojo": [231, 76, 60],
    "desconocido": [127, 140, 141],
}

# Paleta por TIPO de riesgo dominante + severidad. Así dos celdas "en rojo"
# no significan lo mismo si una es sísmica y otra volcánica: cada tipo
# tiene su propia familia de color, y solo la intensidad varía con el nivel.
COLOR_POR_TIPO_RIESGO = {
    "sismico":     {"Bajo": [46, 204, 113], "Medio": [230, 126, 34], "Alto": [192, 57, 43]},   # verde -> rojo tierra
    "ciclonico":   {"Bajo": [46, 204, 113], "Medio": [241, 196, 15], "Alto": [41, 128, 185]},   # verde -> azul viento
    "volcanico":   {"Bajo": [46, 204, 113], "Medio": [230, 126, 34], "Alto": [211, 84, 0]},     # verde -> naranja fuego
    "desconocido": {"Bajo": [127, 140, 141], "Medio": [127, 140, 141], "Alto": [127, 140, 141]},
}

COLOR_RUIDO_DBSCAN = [149, 165, 166]  # gris — celdas "de ruido" / riesgo atípico
COLOR_CASO_ESTUDIO = [241, 196, 15]   # amarillo — marcadores destacados
COLOR_GDACS = [155, 89, 182]          # morado — incidentes en vivo

# Paleta del propio globo (fondo espacial + océano + tierra)
COLOR_FONDO_ESPACIO = "#05070d"
COLOR_OCEANO = [8, 20, 45]
COLOR_TIERRA = [35, 40, 45]
COLOR_BORDES_PAISES = [90, 100, 110]

GDACS_EVENTS_URL = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/EVENTS4APP"

SATELLITE_TILE_URL = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
)

st.set_page_config(page_title="GeoRisk Finder", layout="wide")


# ---------------------------------------------------------------------------
# Utilidades de texto (búsqueda insensible a tildes)
# ---------------------------------------------------------------------------

def _sin_tildes(texto: str) -> str:
    if not isinstance(texto, str):
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )


NOMBRES_DISPLAY = {
    "Japon": "Japón",
    "Espana": "España",
    "Chile": "Chile",
    "Venezuela": "Venezuela",
}


# ---------------------------------------------------------------------------
# Carga de datos (con caché) — cae a datos sintéticos si el fichero no existe
# ---------------------------------------------------------------------------


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


def _datos_sinteticos_grid_features(n=300, seed=1):
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "cell_id": [f"cell_{i}" for i in range(n)],
            "lat": rng.uniform(-60, 70, n),
            "lon": rng.uniform(-180, 180, n),
            "eq_count": rng.integers(0, 50, n),
            "eq_mag_mean": np.round(rng.uniform(2, 7, n), 1),
            "eq_mag_max": np.round(rng.uniform(3, 8.5, n), 1),
            "eq_depth_mean": np.round(rng.uniform(5, 300, n), 1),
            "eq_energy_log": np.round(rng.uniform(8, 18, n), 2),
            "eq_days_since_last_major": rng.integers(0, 4000, n),
            "cyclone_count": rng.integers(0, 15, n),
            "wind_mean": np.round(rng.uniform(20, 120, n), 1),
            "wind_max": np.round(rng.uniform(40, 280, n), 1),
            "pressure_min_mean": np.round(rng.uniform(920, 1010, n), 1),
            "dist_nearest_volcano_km": np.round(rng.uniform(0, 800, n), 1),
            "volcano_count": rng.integers(0, 5, n),
        }
    )


@st.cache_data(ttl=600)
def cargar_csv_o_sintetico(path: Path, _generador_sintetico):
    if path.exists():
        return pd.read_csv(path)
    st.sidebar.warning(f"⚠️ No encontrado: {path} — usando datos sintéticos de relleno.")
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


def _tooltip_celda(row) -> str:
    aviso_ruido = ""
    if row.get("cluster_dbscan") == -1:
        aviso_ruido = (
            "<br/><i style='color:#e67e22'>⚠️ Celda atípica (ruido DBSCAN): "
            "los datos reales de esta celda pueden diferir del perfil "
            "típico de su cluster asignado.</i>"
        )
    return (
        f"<b>{row.get('nombre_cluster', '')}</b> "
        f"<span style='opacity:0.7'>({row.get('tipo_riesgo_dominante','')}: {row.get('nivel_riesgo_dominante','')})</span><br/>"
        f"{row.get('descripcion_negocio', '')}<br/>"
        f"Sismos: {row.get('eq_count', 0)} | Mag. media: {row.get('eq_mag_mean', 0)} | "
        f"Mag. máx: {row.get('eq_mag_max', 0)}<br/>"
        f"Ciclones: {row.get('cyclone_count', 0)} | Viento máx: {row.get('wind_max', 0)} km/h<br/>"
        f"Volcán más cercano: {row.get('dist_nearest_volcano_km', 0):.0f} km"
        f"{aviso_ruido}"
    )


def _tooltip_caso(row) -> str:
    nombre = row.get("nombre_lugar_display", row.get("nombre_lugar", ""))
    return f"<b>{nombre}</b><br/>{row.get('texto_caso_estudio', '')}"


def _tooltip_gdacs(row) -> str:
    return f"{row.get('nombre', '')} ({row.get('tipo_evento', '')}, {row.get('alerta', '')})"


@st.cache_data(ttl=300)
def cargar_incidentes_gdacs():
    try:
        resp = requests.get(GDACS_EVENTS_URL, timeout=8)
        resp.raise_for_status()
        geojson = resp.json()
        registros = []
        for feature in geojson.get("features", []):
            geom = feature.get("geometry", {})
            props = feature.get("properties", {})
            coords = geom.get("coordinates")
            if geom.get("type") != "Point" or not coords:
                continue
            registros.append(
                {
                    "lon": coords[0],
                    "lat": coords[1],
                    "tipo_evento": props.get("eventtype"),
                    "nombre": props.get("eventname") or props.get("name"),
                    "alerta": props.get("alertlevel"),
                    "fecha": props.get("fromdate"),
                }
            )
        df = pd.DataFrame(registros)
        df = asegurar_columnas(df, {"nombre": "", "tipo_evento": "", "alerta": "", "fecha": ""})
        return df
    except Exception as exc:
        st.sidebar.error(f"GDACS no disponible ahora mismo ({exc}). Se omite la capa en vivo.")
        return pd.DataFrame(columns=["lon", "lat", "tipo_evento", "nombre", "alerta", "fecha"])


NIVEL_RANGO = {"Bajo": 0, "Medio": 1, "Alto": 2}
RANGO_A_COLOR = {0: "verde", 1: "naranja", 2: "rojo"}
RANGO_A_NIVEL = {0: "Bajo", 1: "Medio", 2: "Alto"}


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


# Mismos bounding boxes que usó Persona 6 en el notebook 06
COUNTRY_BBOXES = {
    "Japon":     (24.0, 46.0, 122.0, 146.0),
    "Chile":     (-56.0, -17.5, -76.0, -66.0),
    "Venezuela": (0.6, 12.5, -73.5, -59.5),
    "Espana":    (35.9, 43.9, -9.5, 4.4),
}


def _centro_bbox(pais):
    bbox = COUNTRY_BBOXES.get(pais)
    if bbox is None:
        return None
    lat_min, lat_max, lon_min, lon_max = bbox
    return ((lat_min + lat_max) / 2, (lon_min + lon_max) / 2)


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
        "Cluster dominante: " + df["cluster_dominante"].astype(str)
        + " (" + df["pct_cluster_dominante"].astype(str) + "% de celdas). "
        + df["nombre_negocio_dominante"].astype(str)
        + " — " + df["n_celdas"].astype(str) + " celdas analizadas."
    )

    return df


def _riesgo_dominante(row):
    """Determina qué tipo de peligro (sismico/ciclonico/volcanico) es el
    dominante para el CLUSTER de esta celda, y con qué nivel. Se usa para
    colorear por tipo, no solo por severidad genérica."""
    niveles = {
        "sismico": NIVEL_RANGO.get(row.get("nivel_sismico", "Bajo"), 0),
        "ciclonico": NIVEL_RANGO.get(row.get("nivel_ciclonico", "Bajo"), 0),
        "volcanico": NIVEL_RANGO.get(row.get("nivel_volcanico", "Bajo"), 0),
    }
    tipo_dom = max(niveles, key=niveles.get)
    nivel_dom = RANGO_A_NIVEL[niveles[tipo_dom]]
    return tipo_dom, nivel_dom


def _muestrear_preservando_riesgo(df, max_puntos, col_severidad="severidad", umbral=0.5):
    """Muestreo estratificado: conserva SIEMPRE las celdas con severidad
    individual alta (no solo por color heredado de cluster), y solo
    samplea aleatoriamente el resto de baja severidad. Evita que zonas
    pequeñas pero críticas (ej. archipiélagos volcánicos) desaparezcan
    por pura mala suerte del muestreo aleatorio."""
    if col_severidad not in df.columns:
        if len(df) > max_puntos:
            return df.sample(max_puntos, random_state=0)
        return df

    prioritarios = df[df[col_severidad] >= umbral]
    resto = df[df[col_severidad] < umbral]

    if len(prioritarios) > max_puntos:
        prioritarios = prioritarios.sample(max_puntos, random_state=0)
        resto = resto.iloc[0:0]
    else:
        cupo_resto = max(0, max_puntos - len(prioritarios))
        if len(resto) > cupo_resto:
            resto = resto.sample(cupo_resto, random_state=0)

    return pd.concat([prioritarios, resto])


# ---------------------------------------------------------------------------
# Carga y merge
# ---------------------------------------------------------------------------

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
casos_estudio["tooltip_html"] = casos_estudio.apply(_tooltip_caso, axis=1)

grid_features = cargar_csv_o_sintetico(GRID_FEATURES_PATH, _datos_sinteticos_grid_features)

grid_features_sin_geo = grid_features.drop(
    columns=[c for c in ("lat", "lon") if c in grid_features.columns]
)

mapa = clusters.merge(interpretacion, on="cluster_kmeans", how="left").merge(
    grid_features_sin_geo, on="cell_id", how="left"
)

mapa = asegurar_columnas(
    mapa,
    {
        "eq_count": 0, "eq_mag_mean": 0, "eq_mag_max": 0, "eq_depth_mean": 0,
        "eq_energy_log": 0, "eq_days_since_last_major": 0,
        "cyclone_count": 0, "wind_mean": 0, "wind_max": 0, "pressure_min_mean": 0,
        "dist_nearest_volcano_km": 0, "volcano_count": 0,
        "nombre_cluster": "Sin clasificar", "descripcion_negocio": "",
        "nivel_riesgo": "desconocido",
        "nivel_sismico": "Bajo", "nivel_ciclonico": "Bajo", "nivel_volcanico": "Bajo",
    },
)

mapa = limpiar_nan_global(mapa)

# --- Color por TIPO de riesgo dominante (no solo severidad genérica) ---
dominante = mapa.apply(_riesgo_dominante, axis=1)
mapa["tipo_riesgo_dominante"] = dominante.map(lambda t: t[0])
mapa["nivel_riesgo_dominante"] = dominante.map(lambda t: t[1])
mapa["color_rgb"] = mapa.apply(
    lambda r: COLOR_POR_TIPO_RIESGO.get(
        r["tipo_riesgo_dominante"], COLOR_POR_TIPO_RIESGO["desconocido"]
    ).get(r["nivel_riesgo_dominante"], [127, 140, 141]),
    axis=1,
)

mapa["tooltip_html"] = mapa.apply(_tooltip_celda, axis=1)

# ---------------------------------------------------------------------------
# Severidad y radio visual por celda (basado en datos REALES de la celda,
# no en la etiqueta heredada del cluster — así el muestreo estratificado
# prioriza correctamente celdas individualmente peligrosas)
# ---------------------------------------------------------------------------
RADIO_MIN_M = 15_000
RADIO_MAX_M = 60_000

componente_sismico = (mapa["eq_mag_mean"] / 9).clip(0, 1)
componente_ciclonico = (mapa["wind_max"] / 250).clip(0, 1)
componente_volcanico = (50 / (50 + mapa["dist_nearest_volcano_km"])).clip(0, 1)

mapa["severidad"] = pd.concat(
    [componente_sismico, componente_ciclonico, componente_volcanico], axis=1
).max(axis=1)

mapa["radio_m"] = RADIO_MIN_M + mapa["severidad"] * (RADIO_MAX_M - RADIO_MIN_M)


# ---------------------------------------------------------------------------
# Sidebar — controles
# ---------------------------------------------------------------------------

st.sidebar.title("🌍 GeoRisk Finder")
modo_vista = st.sidebar.radio(
    "Modo de vista",
    ["🌐 Globo estilizado (overview)", "🛰️ Satélite (zoom real)"],
    help=(
        "El globo estilizado es mejor para ver patrones globales de clusters. "
        "El modo satélite usa imágenes reales (Esri) y solo tiene sentido "
        "haciendo zoom a una zona concreta — busca un lugar abajo."
    ),
)
mostrar_dbscan = st.sidebar.checkbox("Resaltar ruido DBSCAN (riesgo atípico)", value=True)
mostrar_casos = st.sidebar.checkbox("Mostrar casos de estudio", value=True)
mostrar_gdacs = st.sidebar.checkbox("Incidentes en vivo (GDACS)", value=True)

busqueda_lugar = st.sidebar.text_input("Buscar lugar destacado (por nombre)")
ZOOM_GLOBO_LUGAR = 3
ZOOM_SATELITE_LUGAR = 13

if busqueda_lugar:
    busqueda_normalizada = _sin_tildes(busqueda_lugar).lower()
    coincidencias = casos_estudio[
        casos_estudio["nombre_lugar_normalizado"].str.contains(busqueda_normalizada, na=False)
    ]
    if not coincidencias.empty:
        fila = coincidencias.iloc[0]
        zoom_lugar = ZOOM_SATELITE_LUGAR if modo_vista.startswith("🛰️") else ZOOM_GLOBO_LUGAR
        vista_inicial = pdk.ViewState(
            latitude=float(fila["lat"]), longitude=float(fila["lon"]), zoom=zoom_lugar
        )
    else:
        st.sidebar.caption("Sin coincidencias.")
        vista_inicial = pdk.ViewState(latitude=20, longitude=0, zoom=0)
else:
    if modo_vista.startswith("🛰️"):
        st.sidebar.caption("🛰️ Sin zona buscada: se muestra un zoom mundial de referencia.")
        vista_inicial = pdk.ViewState(latitude=20, longitude=0, zoom=2)
    else:
        vista_inicial = pdk.ViewState(latitude=20, longitude=0, zoom=0)

st.sidebar.markdown("---")
st.sidebar.markdown("**Leyenda — tipo de riesgo dominante**")
LEYENDA_TIPOS = [
    ("Sísmico (Alto)", COLOR_POR_TIPO_RIESGO["sismico"]["Alto"]),
    ("Ciclónico (Alto)", COLOR_POR_TIPO_RIESGO["ciclonico"]["Alto"]),
    ("Volcánico (Alto)", COLOR_POR_TIPO_RIESGO["volcanico"]["Alto"]),
    ("Riesgo bajo (cualquier tipo)", [46, 204, 113]),
]
for etiqueta, color in LEYENDA_TIPOS:
    st.sidebar.markdown(
        f"<span style='color: rgb({color[0]},{color[1]},{color[2]})'>●</span> {etiqueta}",
        unsafe_allow_html=True,
    )
st.sidebar.markdown(
    f"<span style='color: rgb({COLOR_RUIDO_DBSCAN[0]},{COLOR_RUIDO_DBSCAN[1]},{COLOR_RUIDO_DBSCAN[2]})'>●</span> Ruido DBSCAN (atípico)",
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    f"<span style='color: rgb({COLOR_CASO_ESTUDIO[0]},{COLOR_CASO_ESTUDIO[1]},{COLOR_CASO_ESTUDIO[2]})'>●</span> Caso de estudio",
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    f"<span style='color: rgb({COLOR_GDACS[0]},{COLOR_GDACS[1]},{COLOR_GDACS[2]})'>●</span> Incidente en vivo (GDACS)",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Modo satélite (Folium + teselas Esri reales)
# ---------------------------------------------------------------------------

def _color_hex(rgb):
    return "#%02x%02x%02x" % tuple(int(c) for c in rgb)


def render_mapa_satelite(
    vista_inicial, mapa, casos_estudio, mostrar_dbscan, mostrar_casos, mostrar_gdacs,
    max_puntos=1500,
):
    m = folium.Map(
        location=[vista_inicial.latitude, vista_inicial.longitude],
        zoom_start=int(round(vista_inicial.zoom)),
        tiles=None,
        control_scale=True,
    )
    folium.TileLayer(
        tiles=SATELLITE_TILE_URL,
        attr="Esri, Maxar, Earthstar Geographics, USDA, USGS, AeroGRID, IGN, y la comunidad GIS",
        name="Satélite (Esri)",
        overlay=False,
        control=False,
    ).add_to(m)

    puntos_color = mapa[mapa["cluster_dbscan"] != -1] if mostrar_dbscan else mapa
    puntos_color = _muestrear_preservando_riesgo(puntos_color, max_puntos)

    for _, fila in puntos_color.iterrows():
        folium.CircleMarker(
            location=[fila["lat"], fila["lon"]],
            radius=max(3, float(fila.get("severidad", 0)) * 10 + 3),
            color=_color_hex(fila.get("color_rgb", [127, 140, 141])),
            fill=True,
            fill_opacity=0.75,
            weight=1,
            tooltip=folium.Tooltip(fila["tooltip_html"]),
        ).add_to(m)

    if mostrar_dbscan:
        ruido = mapa[mapa["cluster_dbscan"] == -1]
        ruido = _muestrear_preservando_riesgo(ruido, max_puntos)
        for _, fila in ruido.iterrows():
            folium.CircleMarker(
                location=[fila["lat"], fila["lon"]],
                radius=max(4, float(fila.get("severidad", 0)) * 10 + 5),
                color=_color_hex(COLOR_RUIDO_DBSCAN),
                fill=True,
                fill_opacity=0.9,
                weight=1,
                tooltip=folium.Tooltip(fila["tooltip_html"]),
            ).add_to(m)

    if mostrar_casos and not casos_estudio.empty:
        for _, fila in casos_estudio.iterrows():
            folium.CircleMarker(
                location=[fila["lat"], fila["lon"]],
                radius=10,
                color="#000000",
                weight=2,
                fill=True,
                fill_color=_color_hex(COLOR_CASO_ESTUDIO),
                fill_opacity=0.9,
                tooltip=folium.Tooltip(fila["tooltip_html"]),
            ).add_to(m)

    if mostrar_gdacs:
        incidentes = limpiar_nan_global(cargar_incidentes_gdacs())
        if not incidentes.empty:
            incidentes["tooltip_html"] = incidentes.apply(_tooltip_gdacs, axis=1)
            for _, fila in incidentes.iterrows():
                folium.CircleMarker(
                    location=[fila["lat"], fila["lon"]],
                    radius=8,
                    color=_color_hex(COLOR_GDACS),
                    fill=True,
                    fill_opacity=0.9,
                    tooltip=folium.Tooltip(fila["tooltip_html"]),
                ).add_to(m)

    return m


# ---------------------------------------------------------------------------
# Modo globo (pydeck _GlobeView, estilizado)
# ---------------------------------------------------------------------------

COUNTRIES_GEOJSON = (
    "https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_50m_admin_0_scale_rank.geojson"
)

POLIGONO_OCEANO = [
    {
        "polygon": [
            [-180, 90], [0, 90], [180, 90],
            [180, -90], [0, -90], [-180, -90],
        ]
    }
]


def construir_deck_globo(
    vista_inicial, mapa, casos_estudio, mostrar_dbscan, mostrar_casos, mostrar_gdacs,
    max_puntos=5000,
):
    puntos_cluster = mapa[mapa["cluster_dbscan"] != -1] if mostrar_dbscan else mapa
    puntos_cluster = _muestrear_preservando_riesgo(puntos_cluster, max_puntos)

    capas = [
        pdk.Layer(
            "SolidPolygonLayer",
            id="superficie-tierra",
            data=POLIGONO_OCEANO,
            get_polygon="polygon",
            stroked=False,
            filled=True,
            get_fill_color=COLOR_OCEANO,
        ),
        pdk.Layer(
            "GeoJsonLayer",
            id="base-map",
            data=COUNTRIES_GEOJSON,
            stroked=True,
            filled=True,
            get_fill_color=COLOR_TIERRA,
            get_line_color=COLOR_BORDES_PAISES,
            line_width_min_pixels=1,
        ),
        pdk.Layer(
            "ScatterplotLayer",
            id="clusters",
            data=puntos_cluster,
            get_position=["lon", "lat"],
            get_fill_color="color_rgb",
            get_radius="radio_m",
            radius_min_pixels=1,
            radius_max_pixels=15,
            pickable=True,
            opacity=0.6,
        ),
    ]

    if mostrar_dbscan:
        ruido = mapa[mapa["cluster_dbscan"] == -1]
        ruido = _muestrear_preservando_riesgo(ruido, max_puntos)
        if not ruido.empty:
            ruido = ruido.copy()
            ruido["radio_m"] = ruido["radio_m"] * 1.3
            capas.append(
                pdk.Layer(
                    "ScatterplotLayer",
                    id="ruido-dbscan",
                    data=ruido,
                    get_position=["lon", "lat"],
                    get_fill_color=COLOR_RUIDO_DBSCAN,
                    get_radius="radio_m",
                    radius_min_pixels=2,
                    radius_max_pixels=20,
                    pickable=True,
                    opacity=0.7,
                )
            )

    if mostrar_casos and not casos_estudio.empty:
        capas.append(
            pdk.Layer(
                "ScatterplotLayer",
                id="casos-estudio",
                data=casos_estudio,
                get_position=["lon", "lat"],
                get_fill_color=COLOR_CASO_ESTUDIO,
                get_radius=200000,
                pickable=True,
                stroked=True,
                get_line_color=[0, 0, 0],
                line_width_min_pixels=2,
                opacity=1.0,
            )
        )

    if mostrar_gdacs:
        incidentes = limpiar_nan_global(cargar_incidentes_gdacs())
        if not incidentes.empty:
            incidentes["tooltip_html"] = incidentes.apply(_tooltip_gdacs, axis=1)
            capas.append(
                pdk.Layer(
                    "ScatterplotLayer",
                    id="gdacs-live",
                    data=incidentes,
                    get_position=["lon", "lat"],
                    get_fill_color=COLOR_GDACS,
                    get_radius=180000,
                    pickable=True,
                    opacity=1.0,
                    stroked=True,
                    get_line_color=[255, 255, 255],
                    line_width_min_pixels=1,
                )
            )

    deck = pdk.Deck(
        views=[pdk.View(type="_GlobeView", controller=True)],
        initial_view_state=vista_inicial,
        layers=capas,
        map_provider=None,
        parameters={"cull": True},
        tooltip={
            "html": "{tooltip_html}",
            "style": {"backgroundColor": "#1e1e1e", "color": "white"},
        },
    )
    deck.css_background_color = COLOR_FONDO_ESPACIO
    return deck


# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------

st.title("🌍 GeoRisk Finder — Mapa global de riesgo geológico")
st.caption(
    "Clusters de K-Means/DBSCAN sobre grid H3 + incidentes activos en vivo (GDACS). "
    "El color indica el TIPO de riesgo dominante (sísmico/ciclónico/volcánico), no solo su severidad."
)

if modo_vista.startswith("🛰️"):
    mapa_folium = render_mapa_satelite(
        vista_inicial, mapa, casos_estudio, mostrar_dbscan, mostrar_casos, mostrar_gdacs
    )
    st_folium(mapa_folium, height=850, use_container_width=True, key="georisk-satelite")
    st.caption("Imagery © Esri, Maxar, Earthstar Geographics, USDA, USGS, AeroGRID, IGN, y la comunidad GIS.")
else:
    deck = construir_deck_globo(
        vista_inicial, mapa, casos_estudio, mostrar_dbscan, mostrar_casos, mostrar_gdacs
    )
    evento = st_deckgl(deck, height=850, key="georisk-globe")

    # --- Tarjeta de detalle al hacer click sobre un punto ---
    objeto_click = None
    if isinstance(evento, dict):
        objeto_click = evento.get("object") or evento.get("picked") or evento.get("data")

    if objeto_click:
        st.markdown("---")
        titulo = (
            objeto_click.get("nombre_cluster")
            or objeto_click.get("nombre_lugar_display")
            or objeto_click.get("nombre")
            or "Detalle del punto seleccionado"
        )
        st.subheader(f"📍 {titulo}")

        if "nivel_sismico" in objeto_click:
            col1, col2, col3 = st.columns(3)
            col1.metric("Riesgo sísmico", objeto_click.get("nivel_sismico", "—"))
            col2.metric("Riesgo ciclónico", objeto_click.get("nivel_ciclonico", "—"))
            col3.metric("Riesgo volcánico", objeto_click.get("nivel_volcanico", "—"))
            if objeto_click.get("cluster_dbscan") == -1:
                st.warning(
                    "⚠️ Esta celda es **ruido DBSCAN**: sus datos individuales no encajan "
                    "bien con el perfil promedio de su cluster. Trata la etiqueta de "
                    "riesgo con cautela para esta zona en concreto."
                )

        st.write(
            objeto_click.get("descripcion_negocio")
            or objeto_click.get("texto_caso_estudio")
            or ""
        )

        with st.expander("Ver todos los datos crudos de este punto"):
            st.json(objeto_click)
    else:
        st.caption("💡 Haz click sobre un punto del globo para ver su tarjeta de detalle aquí.")

with st.expander("¿Qué se está mostrando?"):
    st.markdown(
        """
- **Color** → tipo de riesgo dominante del cluster de esa celda: rojo tierra = sísmico,
  azul = ciclónico, naranja fuego = volcánico. La intensidad indica el nivel (bajo/medio/alto).
- **Puntos grises** → celdas marcadas como "ruido" por DBSCAN: la etiqueta de su cluster
  puede no representar bien los datos reales de esa celda individual.
- **Puntos amarillos** → casos de estudio destacados (Japón, Chile, Venezuela, España).
- **Puntos morados** → incidentes activos ahora mismo, vía la API pública de GDACS.

El muestreo de puntos en pantalla prioriza siempre las celdas de mayor severidad individual,
para que zonas pequeñas pero críticas (ej. archipiélagos volcánicos) no desaparezcan por azar.
"""
    )

st.caption(f"Última actualización de incidentes GDACS: {time.strftime('%Y-%m-%d %H:%M:%S')}")