"""
GeoRisk Finder — Utilidades de datos compartidas.

Carga robusta de CSV con fallback sintético, normalización de esquemas
de clusters/casos de estudio, y helpers de texto. Usado por todas las
páginas del dashboard para evitar duplicación de lógica.
"""

import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

from theme import NIVEL_RANGO, RANGO_A_COLOR, RANGO_A_NIVEL

NOMBRES_DISPLAY = {"Japon": "Japón", "Espana": "España", "Chile": "Chile", "Venezuela": "Venezuela"}

COUNTRY_BBOXES = {
    "Japon":     (24.0, 46.0, 122.0, 146.0),
    "Chile":     (-56.0, -17.5, -76.0, -66.0),
    "Venezuela": (0.6, 12.5, -73.5, -59.5),
    "Espana":    (35.9, 43.9, -9.5, 4.4),
}


def sin_tildes(texto: str) -> str:
    if not isinstance(texto, str):
        return ""
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def centro_bbox(pais):
    bbox = COUNTRY_BBOXES.get(pais)
    if bbox is None:
        return None
    lat_min, lat_max, lon_min, lon_max = bbox
    return ((lat_min + lat_max) / 2, (lon_min + lon_max) / 2)


@st.cache_data(ttl=600)
def cargar_csv_o_sintetico(path: Path, _generador_sintetico, etiqueta: str = ""):
    if path.exists():
        return pd.read_csv(path)
    st.sidebar.warning(f"Fuente no disponible: {etiqueta or path.name}. Usando datos de referencia sintéticos.")
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
    num_cols = df.select_dtypes(include=[np.number]).columns
    df[num_cols] = df[num_cols].fillna(0)
    txt_cols = df.select_dtypes(include=["object"]).columns
    df[txt_cols] = df[txt_cols].fillna("")
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
        niveles = [c for c in ("nivel_sismico", "nivel_ciclonico", "nivel_volcanico") if c in df.columns]
        if niveles:
            rango_max = df[niveles].map(lambda v: NIVEL_RANGO.get(v, 0)).max(axis=1)
            df["nivel_riesgo"] = rango_max.map(RANGO_A_COLOR)
        else:
            df["nivel_riesgo"] = "desconocido"
    return df


def normalizar_casos_estudio(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "pais" in df.columns and "nombre_lugar" not in df.columns:
        df = df.rename(columns={"pais": "nombre_lugar"})

    df["nombre_lugar_display"] = df["nombre_lugar"].map(lambda p: NOMBRES_DISPLAY.get(p, p))
    df["nombre_lugar_normalizado"] = df["nombre_lugar_display"].map(sin_tildes).str.lower()

    if "lat" not in df.columns or "lon" not in df.columns:
        centros = df["nombre_lugar"].map(centro_bbox)
        df["lat"] = centros.map(lambda c: c[0] if c else None)
        df["lon"] = centros.map(lambda c: c[1] if c else None)
        df = df.dropna(subset=["lat", "lon"])

    df = asegurar_columnas(df, {
        "cluster_dominante": "", "pct_cluster_dominante": "",
        "nombre_negocio_dominante": "", "n_celdas": "",
    })
    df["texto_caso_estudio"] = (
        "Perfil dominante: " + df["nombre_negocio_dominante"].astype(str)
        + " (" + df["pct_cluster_dominante"].astype(str) + "% de " + df["n_celdas"].astype(str) + " celdas)."
    )
    return df


def riesgo_dominante(row):
    niveles = {
        "sismico": NIVEL_RANGO.get(row.get("nivel_sismico", "Bajo"), 0),
        "ciclonico": NIVEL_RANGO.get(row.get("nivel_ciclonico", "Bajo"), 0),
        "volcanico": NIVEL_RANGO.get(row.get("nivel_volcanico", "Bajo"), 0),
    }
    tipo = max(niveles, key=niveles.get)
    return tipo, RANGO_A_NIVEL[niveles[tipo]]


def calcular_severidad(df: pd.DataFrame) -> pd.Series:
    sismico = (df["eq_mag_mean"] / 9).clip(0, 1)
    ciclonico = (df["wind_max"] / 250).clip(0, 1)
    volcanico = (50 / (50 + df["dist_nearest_volcano_km"])).clip(0, 1)
    return pd.concat([sismico, ciclonico, volcanico], axis=1).max(axis=1)


# ── Generadores sintéticos (fallback cuando faltan CSV) ─────────────

def datos_sinteticos_clusters(n=300, seed=42):
    rng = np.random.default_rng(seed)
    cluster_kmeans = rng.integers(0, 4, n)
    cluster_dbscan = np.where(rng.random(n) < 0.08, -1, cluster_kmeans)
    return pd.DataFrame({
        "cell_id": [f"cell_{i}" for i in range(n)],
        "lat": rng.uniform(-60, 70, n), "lon": rng.uniform(-180, 180, n),
        "cluster_kmeans": cluster_kmeans, "cluster_dbscan": cluster_dbscan,
    })


def datos_sinteticos_interpretacion():
    return pd.DataFrame({
        "cluster_kmeans": [0, 1, 2, 3],
        "nombre_cluster": ["Baja actividad", "Sismicidad moderada",
                            "Alta sismicidad y ciclones estacionales", "Volcanico activo"],
        "descripcion_negocio": [
            "Zona de riesgo bajo, apta para operaciones estandar.",
            "Riesgo sismico moderado, requiere monitoreo periodico.",
            "Combinacion de sismicidad alta y estacionalidad de ciclones.",
            "Proximidad a actividad volcanica activa reciente.",
        ],
        "nivel_sismico": ["Bajo", "Medio", "Alto", "Bajo"],
        "nivel_ciclonico": ["Bajo", "Bajo", "Alto", "Bajo"],
        "nivel_volcanico": ["Bajo", "Bajo", "Medio", "Alto"],
        "nivel_riesgo": ["verde", "verde", "naranja", "rojo"],
    })


def datos_sinteticos_casos_estudio():
    return pd.DataFrame({
        "pais": ["Japon", "Chile", "Venezuela", "Espana"],
        "n_celdas": [503, 331, 172, 85],
        "cluster_dominante": [2, 4, 1, 4],
        "pct_cluster_dominante": [65.8, 62.2, 57.0, 76.5],
        "nombre_negocio_dominante": [
            "Riesgo ciclonico alto, cercania volcanica alta", "Riesgo sismico alto",
            "Riesgo sismico bajo, ciclonico bajo", "Riesgo sismico alto",
        ],
    })


def datos_sinteticos_grid_features(n=300, seed=1):
    rng = np.random.default_rng(seed)
    return pd.DataFrame({
        "cell_id": [f"cell_{i}" for i in range(n)],
        "lat": rng.uniform(-60, 70, n), "lon": rng.uniform(-180, 180, n),
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
    })


def datos_sinteticos_grid_enriquecido(n=300, seed=1):
    base = datos_sinteticos_grid_features(n, seed)
    return base[["cell_id", "lat", "lon", "eq_count", "eq_mag_mean", "eq_mag_max",
                 "cyclone_count", "wind_mean", "wind_max", "dist_nearest_volcano_km", "volcano_count"]]


def datos_sinteticos_grid_pais(n=300, seed=1):
    rng = np.random.default_rng(seed)
    paises = ["JPN", "CHL", "VEN", "ESP", "PHL", "IDN", "MEX", "IND"]
    iso = rng.choice(paises, n)
    pib = dict(zip(paises, rng.uniform(1500, 45000, len(paises))))
    pob = dict(zip(paises, rng.integers(5_000_000, 300_000_000, len(paises))))
    return pd.DataFrame({
        "cell_id": [f"cell_{i}" for i in range(n)],
        "lat": rng.uniform(-60, 70, n), "lon": rng.uniform(-180, 180, n),
        "eq_mag_mean": np.round(rng.uniform(2, 7, n), 1),
        "wind_max": np.round(rng.uniform(40, 280, n), 1),
        "dist_nearest_volcano_km": np.round(rng.uniform(0, 800, n), 1),
        "iso_a3": iso,
        "pib_per_capita": [pib[p] for p in iso],
        "poblacion": [pob[p] for p in iso],
    })
    
NOMBRES_PAIS_ISO = {
    "JPN": "Japón", "CHL": "Chile", "VEN": "Venezuela", "ESP": "España",
    "PHL": "Filipinas", "IDN": "Indonesia", "MEX": "México", "IND": "India",
    "RWA": "Ruanda", "TJK": "Tayikistán", "MWI": "Malaui", "COM": "Comoras",
    "AFG": "Afganistán", "TZA": "Tanzania", "BDI": "Burundi", "SLV": "El Salvador",
    "IRN": "Irán", "CHN": "China", "USA": "Estados Unidos", "TUR": "Turquía",
    "GRC": "Grecia", "ITA": "Italia", "NZL": "Nueva Zelanda", "PER": "Perú",
    "ECU": "Ecuador", "COL": "Colombia", "PAK": "Pakistán", "BGD": "Bangladés",
    "MMR": "Myanmar", "VUT": "Vanuatu", "TON": "Tonga", "FJI": "Fiyi",
    "PNG": "Papúa Nueva Guinea", "SLB": "Islas Salomón", "MDG": "Madagascar",
    "MOZ": "Mozambique", "HTI": "Haití", "NIC": "Nicaragua", "GTM": "Guatemala",
    "NPL": "Nepal", "ETH": "Etiopía", "SOM": "Somalia", "YEM": "Yemen",
}


def nombre_pais(codigo_iso: str) -> str:
    if not isinstance(codigo_iso, str) or not codigo_iso.strip():
        return None
    return NOMBRES_PAIS_ISO.get(codigo_iso.upper(), codigo_iso.upper())


def filtrar_paises_validos(df: pd.DataFrame, col_iso="iso_a3", col_pib="pib_per_capita") -> pd.DataFrame:
    """Descarta filas sin pais identificable o sin PIB real (0 o NaN).
    Un dato incompleto no debe mostrarse como si fuera valido: se excluye
    en vez de rellenarse con 0, que rompe la credibilidad de la tabla."""
    df = df.copy()
    df = df[df[col_iso].notna() & (df[col_iso].astype(str).str.strip() != "")]
    df = df[df[col_pib].notna() & (df[col_pib] > 0)]
    df["pais_nombre"] = df[col_iso].map(nombre_pais)
    return df[df["pais_nombre"].notna()]