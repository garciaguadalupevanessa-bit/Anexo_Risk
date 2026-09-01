"""
Pagina: Mapa global de riesgo geologico compuesto.

Visualizacion de los clusters K-Means/DBSCAN sobre el grid H3 global,
con capa en vivo de incidentes activos (GDACS) y modo satelite para
inspeccion detallada de zonas concretas.
"""

import sys
import time
from pathlib import Path

import folium
import pandas as pd
import pydeck as pdk
import requests
import streamlit as st
import streamlit.components.v1 as components
from streamlit_deckgl import st_deckgl
from streamlit_folium import st_folium

sys.path.append(str(Path(__file__).parent.parent))
from theme import COLORS, inyectar_tema, encabezado_pagina, pie_sidebar
from data_utils import (
    sin_tildes, cargar_csv_o_sintetico, asegurar_columnas, limpiar_nan_global,
    normalizar_interpretacion, normalizar_casos_estudio, riesgo_dominante, calcular_severidad,
    datos_sinteticos_clusters, datos_sinteticos_interpretacion,
    datos_sinteticos_casos_estudio, datos_sinteticos_grid_features,
)

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "processed"
CLUSTERS_PATH = DATA_DIR / "cluster_labels.csv"
INTERPRETACION_PATH = DATA_DIR / "interpretacion_clusters.csv"
CASOS_ESTUDIO_PATH = DATA_DIR / "casos_estudio.csv"
GRID_FEATURES_PATH = DATA_DIR / "grid_features.csv"

COLOR_POR_TIPO_RIESGO = {
    "sismico":     {"Bajo": [58, 107, 30], "Medio": [179, 125, 0], "Alto": [168, 75, 47]},
    "ciclonico":   {"Bajo": [58, 107, 30], "Medio": [179, 125, 0], "Alto": [32, 128, 141]},
    "volcanico":   {"Bajo": [58, 107, 30], "Medio": [179, 125, 0], "Alto": [122, 55, 20]},
    "desconocido": {"Bajo": [107, 106, 100], "Medio": [107, 106, 100], "Alto": [107, 106, 100]},
}
COLOR_RUIDO_DBSCAN = [107, 106, 100]
COLOR_CASO_ESTUDIO = [179, 125, 0]
COLOR_GDACS = [122, 59, 73]
COLOR_OCEANO = [13, 27, 42]
COLOR_TIERRA = [34, 32, 25]
COLOR_BORDES_PAISES = [90, 89, 83]

GDACS_EVENTS_URL = "https://www.gdacs.org/gdacsapi/api/events/geteventlist/EVENTS4APP"
SATELLITE_TILE_URL = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
COUNTRIES_GEOJSON = "https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_50m_admin_0_scale_rank.geojson"
POLIGONO_OCEANO = [{"polygon": [[-180, 90], [0, 90], [180, 90], [180, -90], [0, -90], [-180, -90]]}]

RADIO_MIN_M, RADIO_MAX_M = 15_000, 60_000
ZOOM_GLOBO_LUGAR, ZOOM_SATELITE_LUGAR = 3, 13

inyectar_tema()


# ── Tooltips ──────────────────────────────────────────────

def _tooltip_celda(row) -> str:
    aviso = ""
    if row.get("cluster_dbscan") == -1:
        aviso = (
            "<br/><span style='color:#B37D00'>Celda atipica (ruido DBSCAN): "
            "el perfil asignado puede no representar los datos reales de esta celda.</span>"
        )
    return (
        f"<b>{row.get('nombre_cluster', '')}</b> "
        f"<span style='opacity:0.75'>&mdash; {row.get('tipo_riesgo_dominante','')}: {row.get('nivel_riesgo_dominante','')}</span><br/>"
        f"{row.get('descripcion_negocio', '')}<br/>"
        f"Sismos: {row.get('eq_count', 0)} | Mag. media: {row.get('eq_mag_mean', 0)} | Mag. max: {row.get('eq_mag_max', 0)}<br/>"
        f"Ciclones: {row.get('cyclone_count', 0)} | Viento max: {row.get('wind_max', 0)} km/h<br/>"
        f"Volcan mas cercano: {row.get('dist_nearest_volcano_km', 0):.0f} km"
        f"{aviso}"
    )


def _tooltip_caso(row) -> str:
    nombre = row.get("nombre_lugar_display", row.get("nombre_lugar", ""))
    return f"<b>{nombre}</b><br/>{row.get('texto_caso_estudio', '')}"


def _tooltip_gdacs(row) -> str:
    return f"<b>{row.get('nombre', '')}</b><br/>{row.get('tipo_evento', '')} &mdash; nivel {row.get('alerta', '')}"


@st.cache_data(ttl=300)
def cargar_incidentes_gdacs():
    try:
        resp = requests.get(GDACS_EVENTS_URL, timeout=8)
        resp.raise_for_status()
        registros = []
        for feature in resp.json().get("features", []):
            geom, props = feature.get("geometry", {}), feature.get("properties", {})
            coords = geom.get("coordinates")
            if geom.get("type") != "Point" or not coords:
                continue
            registros.append({
                "lon": coords[0], "lat": coords[1],
                "tipo_evento": props.get("eventtype"),
                "nombre": props.get("eventname") or props.get("name"),
                "alerta": props.get("alertlevel"), "fecha": props.get("fromdate"),
            })
        df = pd.DataFrame(registros)
        return asegurar_columnas(df, {"nombre": "", "tipo_evento": "", "alerta": "", "fecha": ""})
    except Exception as exc:
        st.sidebar.error(f"Fuente GDACS no disponible en este momento ({exc}).")
        return pd.DataFrame(columns=["lon", "lat", "tipo_evento", "nombre", "alerta", "fecha"])


def _muestrear_preservando_riesgo(df, max_puntos, col="severidad", umbral=0.5):
    if col not in df.columns:
        return df.sample(max_puntos, random_state=0) if len(df) > max_puntos else df
    prioritarios = df[df[col] >= umbral]
    resto = df[df[col] < umbral]
    if len(prioritarios) > max_puntos:
        return prioritarios.sample(max_puntos, random_state=0)
    cupo_resto = max(0, max_puntos - len(prioritarios))
    if len(resto) > cupo_resto:
        resto = resto.sample(cupo_resto, random_state=0)
    return pd.concat([prioritarios, resto])


# ── Carga y enriquecimiento ──────────────────────────────

@st.cache_data(ttl=600)
def cargar_datos():
    clusters = cargar_csv_o_sintetico(CLUSTERS_PATH, datos_sinteticos_clusters, "cluster_labels.csv")
    clusters = clusters.rename(columns={"kmeans_label": "cluster_kmeans", "dbscan_label": "cluster_dbscan"})

    interpretacion = normalizar_interpretacion(
        cargar_csv_o_sintetico(INTERPRETACION_PATH, datos_sinteticos_interpretacion, "interpretacion_clusters.csv")
    )
    casos_estudio = normalizar_casos_estudio(
        cargar_csv_o_sintetico(CASOS_ESTUDIO_PATH, datos_sinteticos_casos_estudio, "casos_estudio.csv")
    )
    casos_estudio = limpiar_nan_global(casos_estudio)
    casos_estudio["tooltip_html"] = casos_estudio.apply(_tooltip_caso, axis=1)

    grid = cargar_csv_o_sintetico(GRID_FEATURES_PATH, datos_sinteticos_grid_features, "grid_features.csv")
    grid_sin_geo = grid.drop(columns=[c for c in ("lat", "lon") if c in grid.columns])

    mapa = clusters.merge(interpretacion, on="cluster_kmeans", how="left").merge(
        grid_sin_geo, on="cell_id", how="left"
    )
    mapa = asegurar_columnas(mapa, {
        "eq_count": 0, "eq_mag_mean": 0, "eq_mag_max": 0, "eq_depth_mean": 0,
        "eq_energy_log": 0, "eq_days_since_last_major": 0, "cyclone_count": 0,
        "wind_mean": 0, "wind_max": 0, "pressure_min_mean": 0,
        "dist_nearest_volcano_km": 0, "volcano_count": 0,
        "nombre_cluster": "Sin clasificar", "descripcion_negocio": "", "nivel_riesgo": "desconocido",
        "nivel_sismico": "Bajo", "nivel_ciclonico": "Bajo", "nivel_volcanico": "Bajo",
    })
    mapa = limpiar_nan_global(mapa)

    dominante = mapa.apply(riesgo_dominante, axis=1)
    mapa["tipo_riesgo_dominante"] = dominante.map(lambda t: t[0])
    mapa["nivel_riesgo_dominante"] = dominante.map(lambda t: t[1])
    mapa["color_rgb"] = mapa.apply(
        lambda r: COLOR_POR_TIPO_RIESGO.get(r["tipo_riesgo_dominante"], COLOR_POR_TIPO_RIESGO["desconocido"])
        .get(r["nivel_riesgo_dominante"], [107, 106, 100]),
        axis=1,
    )
    mapa["tooltip_html"] = mapa.apply(_tooltip_celda, axis=1)
    mapa["severidad"] = calcular_severidad(mapa)
    mapa["radio_m"] = RADIO_MIN_M + mapa["severidad"] * (RADIO_MAX_M - RADIO_MIN_M)

    return mapa, casos_estudio


mapa, casos_estudio = cargar_datos()


# ── Sidebar ───────────────────────────────────────────────

st.sidebar.title("Mapa global")
st.sidebar.caption("Exploracion de clusters de riesgo compuesto sobre grid H3.")
st.sidebar.markdown("---")

modo_vista = st.sidebar.radio(
    "Modo de visualizacion",
    ["Globo estilizado (vision general)", "Satelite (inspeccion de zona)"],
    help=(
        "El globo estilizado revela patrones globales de clusters. "
        "El modo satelite usa imagenes reales (Esri) para analizar una zona concreta."
    ),
)
mostrar_dbscan = st.sidebar.checkbox("Resaltar celdas atipicas (DBSCAN)", value=True)
mostrar_casos = st.sidebar.checkbox("Mostrar casos de estudio validados", value=True)
mostrar_gdacs = st.sidebar.checkbox("Incidentes activos en vivo (GDACS)", value=True)

busqueda_lugar = st.sidebar.text_input("Buscar caso de estudio por nombre")

# ── Estado de rotacion automatica del globo ──────────────
if "globo_longitud" not in st.session_state:
    st.session_state.globo_longitud = 0.0
if "globo_rotando" not in st.session_state:
    st.session_state.globo_rotando = True

if not modo_vista.startswith("Satelite"):
    st.sidebar.markdown("---")
    st.session_state.globo_rotando = st.sidebar.toggle(
        "Rotacion automatica del globo", value=st.session_state.globo_rotando
    )

if busqueda_lugar:
    q = sin_tildes(busqueda_lugar).lower()
    coincidencias = casos_estudio[casos_estudio["nombre_lugar_normalizado"].str.contains(q, na=False)]
    if not coincidencias.empty:
        fila = coincidencias.iloc[0]
        zoom = ZOOM_SATELITE_LUGAR if modo_vista.startswith("Satelite") else ZOOM_GLOBO_LUGAR
        vista_inicial = pdk.ViewState(latitude=float(fila["lat"]), longitude=float(fila["lon"]), zoom=zoom)
    else:
        st.sidebar.caption("Sin coincidencias.")
        vista_inicial = pdk.ViewState(latitude=20, longitude=0, zoom=0)
else:
    if modo_vista.startswith("Satelite"):
        vista_inicial = pdk.ViewState(latitude=20, longitude=0, zoom=2)
    else:
        lon_actual = st.session_state.globo_longitud if st.session_state.globo_rotando else 0.0
        vista_inicial = pdk.ViewState(latitude=20, longitude=lon_actual, zoom=0)

st.sidebar.markdown("---")
st.sidebar.markdown("**Leyenda**")
for etiqueta, color in [
    ("Riesgo sismico alto", COLOR_POR_TIPO_RIESGO["sismico"]["Alto"]),
    ("Riesgo ciclonico alto", COLOR_POR_TIPO_RIESGO["ciclonico"]["Alto"]),
    ("Riesgo volcanico alto", COLOR_POR_TIPO_RIESGO["volcanico"]["Alto"]),
    ("Riesgo bajo (cualquier tipo)", [58, 107, 30]),
]:
    st.sidebar.markdown(
        f"<span style='color: rgb({color[0]},{color[1]},{color[2]})'>&#9632;</span>&nbsp; {etiqueta}",
        unsafe_allow_html=True,
    )
st.sidebar.markdown(
    f"<span style='color: rgb({COLOR_RUIDO_DBSCAN[0]},{COLOR_RUIDO_DBSCAN[1]},{COLOR_RUIDO_DBSCAN[2]})'>&#9632;</span>&nbsp; Ruido DBSCAN",
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    f"<span style='color: rgb({COLOR_CASO_ESTUDIO[0]},{COLOR_CASO_ESTUDIO[1]},{COLOR_CASO_ESTUDIO[2]})'>&#9632;</span>&nbsp; Caso de estudio",
    unsafe_allow_html=True,
)
st.sidebar.markdown(
    f"<span style='color: rgb({COLOR_GDACS[0]},{COLOR_GDACS[1]},{COLOR_GDACS[2]})'>&#9632;</span>&nbsp; Incidente en vivo",
    unsafe_allow_html=True,
)
pie_sidebar("Mapa global de riesgo")


# ── Render modo satelite (Folium) ───────────────────────────

def _color_hex(rgb):
    return "#%02x%02x%02x" % tuple(int(c) for c in rgb)


def render_mapa_satelite(vista, mapa, casos, dbscan, casos_flag, gdacs_flag, max_puntos=1500):
    m = folium.Map(location=[vista.latitude, vista.longitude], zoom_start=int(round(vista.zoom)),
                    tiles=None, control_scale=True)
    folium.TileLayer(tiles=SATELLITE_TILE_URL, attr="Esri, Maxar, Earthstar Geographics, USDA, USGS, AeroGRID, IGN",
                      name="Satelite", overlay=False, control=False).add_to(m)

    puntos = _muestrear_preservando_riesgo(mapa[mapa["cluster_dbscan"] != -1] if dbscan else mapa, max_puntos)
    for _, fila in puntos.iterrows():
        folium.CircleMarker(
            location=[fila["lat"], fila["lon"]], radius=max(3, float(fila.get("severidad", 0)) * 10 + 3),
            color=_color_hex(fila.get("color_rgb", [107, 106, 100])), fill=True, fill_opacity=0.75, weight=1,
            tooltip=folium.Tooltip(fila["tooltip_html"]),
        ).add_to(m)

    if dbscan:
        ruido = _muestrear_preservando_riesgo(mapa[mapa["cluster_dbscan"] == -1], max_puntos)
        for _, fila in ruido.iterrows():
            folium.CircleMarker(
                location=[fila["lat"], fila["lon"]], radius=max(4, float(fila.get("severidad", 0)) * 10 + 5),
                color=_color_hex(COLOR_RUIDO_DBSCAN), fill=True, fill_opacity=0.9, weight=1,
                tooltip=folium.Tooltip(fila["tooltip_html"]),
            ).add_to(m)

    if casos_flag and not casos.empty:
        for _, fila in casos.iterrows():
            folium.CircleMarker(
                location=[fila["lat"], fila["lon"]], radius=10, color="#0D1B2A", weight=2, fill=True,
                fill_color=_color_hex(COLOR_CASO_ESTUDIO), fill_opacity=0.92,
                tooltip=folium.Tooltip(fila["tooltip_html"]),
            ).add_to(m)

    if gdacs_flag:
        incidentes = limpiar_nan_global(cargar_incidentes_gdacs())
        if not incidentes.empty:
            incidentes["tooltip_html"] = incidentes.apply(_tooltip_gdacs, axis=1)
            for _, fila in incidentes.iterrows():
                folium.CircleMarker(
                    location=[fila["lat"], fila["lon"]], radius=8, color=_color_hex(COLOR_GDACS),
                    fill=True, fill_opacity=0.92, tooltip=folium.Tooltip(fila["tooltip_html"]),
                ).add_to(m)
    return m


# ── Render modo globo (pydeck) ───────────────────────────

def construir_deck_globo(vista, mapa, casos, dbscan, casos_flag, gdacs_flag, max_puntos=5000):
    puntos = _muestrear_preservando_riesgo(mapa[mapa["cluster_dbscan"] != -1] if dbscan else mapa, max_puntos)

    capas = [
        pdk.Layer("SolidPolygonLayer", id="oceano", data=POLIGONO_OCEANO, get_polygon="polygon",
                  stroked=False, filled=True, get_fill_color=COLOR_OCEANO),
        pdk.Layer("GeoJsonLayer", id="paises", data=COUNTRIES_GEOJSON, stroked=True, filled=True,
                  get_fill_color=COLOR_TIERRA, get_line_color=COLOR_BORDES_PAISES, line_width_min_pixels=1),
        pdk.Layer("ScatterplotLayer", id="clusters", data=puntos, get_position=["lon", "lat"],
                  get_fill_color="color_rgb", get_radius="radio_m", radius_min_pixels=1, radius_max_pixels=15,
                  pickable=True, opacity=0.62),
    ]

    if dbscan:
        ruido = _muestrear_preservando_riesgo(mapa[mapa["cluster_dbscan"] == -1], max_puntos)
        if not ruido.empty:
            ruido = ruido.copy()
            ruido["radio_m"] *= 1.3
            capas.append(pdk.Layer("ScatterplotLayer", id="ruido", data=ruido, get_position=["lon", "lat"],
                                    get_fill_color=COLOR_RUIDO_DBSCAN, get_radius="radio_m",
                                    radius_min_pixels=2, radius_max_pixels=20, pickable=True, opacity=0.72))

    if casos_flag and not casos.empty:
        capas.append(pdk.Layer("ScatterplotLayer", id="casos", data=casos, get_position=["lon", "lat"],
                                get_fill_color=COLOR_CASO_ESTUDIO, get_radius=200000, pickable=True,
                                stroked=True, get_line_color=[13, 27, 42], line_width_min_pixels=2, opacity=1.0))

    if gdacs_flag:
        incidentes = limpiar_nan_global(cargar_incidentes_gdacs())
        if not incidentes.empty:
            incidentes["tooltip_html"] = incidentes.apply(_tooltip_gdacs, axis=1)
            capas.append(pdk.Layer("ScatterplotLayer", id="gdacs", data=incidentes, get_position=["lon", "lat"],
                                    get_fill_color=COLOR_GDACS, get_radius=180000, pickable=True, opacity=1.0,
                                    stroked=True, get_line_color=[247, 246, 242], line_width_min_pixels=1))

    deck = pdk.Deck(
        views=[pdk.View(type="_GlobeView", controller=True)], initial_view_state=vista, layers=capas,
        map_provider=None, parameters={"cull": True},
        tooltip={"html": "{tooltip_html}", "style": {"backgroundColor": "#0D1B2A", "color": "#F7F6F2"}},
    )
    deck.css_background_color = COLORS["ink"]
    return deck


# ── Layout ────────────────────────────────────────────────

encabezado_pagina(
    "Vision global",
    "Mapa global de riesgo geologico compuesto",
    "Clusters de K-Means y DBSCAN sobre un grid hexagonal H3, combinados con incidentes activos "
    "en tiempo real (GDACS). El color representa el tipo de riesgo dominante de cada celda "
    "(sismico, ciclonico o volcanico), y su intensidad refleja el nivel de severidad.",
)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Celdas analizadas", f"{len(mapa):,}")
with col2:
    st.metric("Celdas atipicas (DBSCAN)", f"{(mapa['cluster_dbscan'] == -1).sum():,}")
with col3:
    st.metric("Severidad media global", f"{mapa['severidad'].mean():.2f}")
with col4:
    st.metric("Casos de estudio validados", f"{len(casos_estudio)}")

st.markdown("---")

if modo_vista.startswith("Satelite"):
    render = render_mapa_satelite(vista_inicial, mapa, casos_estudio, mostrar_dbscan, mostrar_casos, mostrar_gdacs)
    st_folium(render, height=780, use_container_width=True, key="georisk-satelite")
    st.caption("Imagenes satelitales: Esri, Maxar, Earthstar Geographics, USDA, USGS, AeroGRID, IGN.")
else:
    deck = construir_deck_globo(vista_inicial, mapa, casos_estudio, mostrar_dbscan, mostrar_casos, mostrar_gdacs)
    evento = st_deckgl(deck, height=780, key="georisk-globe")

    objeto_click = None
    if isinstance(evento, dict):
        objeto_click = evento.get("object") or evento.get("picked") or evento.get("data")

    if objeto_click:
        st.session_state.globo_rotando = False
        st.markdown("---")
        titulo = (objeto_click.get("nombre_cluster") or objeto_click.get("nombre_lugar_display")
                  or objeto_click.get("nombre") or "Detalle del punto seleccionado")
        st.subheader(titulo)

        if "nivel_sismico" in objeto_click:
            c1, c2, c3 = st.columns(3)
            c1.metric("Riesgo sismico", objeto_click.get("nivel_sismico", "N/D"))
            c2.metric("Riesgo ciclonico", objeto_click.get("nivel_ciclonico", "N/D"))
            c3.metric("Riesgo volcanico", objeto_click.get("nivel_volcanico", "N/D"))
            if objeto_click.get("cluster_dbscan") == -1:
                st.markdown("""
                <div class="callout-warn">
                <p>Esta celda es ruido DBSCAN: sus datos individuales no encajan bien con el perfil
                promedio de su cluster asignado. Se recomienda tratar su clasificacion con cautela.</p>
                </div>
                """, unsafe_allow_html=True)

        st.write(objeto_click.get("descripcion_negocio") or objeto_click.get("texto_caso_estudio") or "")
        with st.expander("Ver datos completos del punto seleccionado"):
            st.json(objeto_click)
    else:
        st.caption("Selecciona un punto del globo para ver su ficha de detalle.")

        if st.session_state.globo_rotando and not busqueda_lugar:
            st.session_state.globo_longitud = (st.session_state.globo_longitud + 0.6) % 360
            time.sleep(0.12)
            st.rerun()

with st.expander("Metodologia de esta visualizacion"):
    st.markdown("""
- **Color:** tipo de riesgo dominante de la celda. Tonos terra para sismico, teal para ciclonico,
  marron oscuro para volcanico. La intensidad del color indica el nivel (bajo, medio, alto).
- **Puntos grises:** celdas marcadas como ruido por DBSCAN — la etiqueta de cluster puede no
  representar bien los datos individuales de esa celda.
- **Puntos dorados:** casos de estudio validados manualmente (Japon, Chile, Venezuela, Espana).
- **Puntos granate:** incidentes activos en este momento, via la API publica de GDACS.

El muestreo de puntos en pantalla prioriza siempre las celdas de mayor severidad individual, de modo
que zonas pequenas pero criticas (por ejemplo, archipielagos volcanicos) no desaparecen por azar.
""")

st.caption(f"Ultima sincronizacion de incidentes GDACS: {time.strftime('%Y-%m-%d %H:%M:%S')} UTC")