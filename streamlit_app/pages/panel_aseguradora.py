"""
Pagina: Panel aseguradora — simulador de prima relativa.

Simulador ilustrativo de prima relativa y perdida potencial por zona,
sobre el mismo grid de riesgo (K-Means/DBSCAN) del mapa global.
"""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).parent.parent))
from theme import inyectar_tema, encabezado_pagina, pie_sidebar, tabla_estilizada, callout_alcance
from data_utils import (
    cargar_csv_o_sintetico, asegurar_columnas, limpiar_nan_global,
    normalizar_interpretacion, normalizar_casos_estudio, calcular_severidad,
    filtrar_paises_validos,
    datos_sinteticos_clusters, datos_sinteticos_interpretacion,
    datos_sinteticos_casos_estudio, datos_sinteticos_grid_enriquecido,
)

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "processed"
GRID_ENRIQUECIDO_PATH = DATA_DIR / "grid_features_enriquecido.csv"
CLUSTERS_PATH = DATA_DIR / "cluster_labels.csv"
INTERPRETACION_PATH = DATA_DIR / "interpretacion_clusters.csv"
CASOS_ESTUDIO_PATH = DATA_DIR / "casos_estudio.csv"

inyectar_tema()


@st.cache_data(ttl=600)
def cargar_datos():
    clusters = cargar_csv_o_sintetico(CLUSTERS_PATH, datos_sinteticos_clusters, "cluster_labels.csv")
    clusters = clusters.rename(columns={"kmeans_label": "cluster_kmeans", "dbscan_label": "cluster_dbscan"})

    interpretacion = normalizar_interpretacion(
        cargar_csv_o_sintetico(INTERPRETACION_PATH, datos_sinteticos_interpretacion, "interpretacion_clusters.csv")
    )
    casos_estudio = limpiar_nan_global(normalizar_casos_estudio(
        cargar_csv_o_sintetico(CASOS_ESTUDIO_PATH, datos_sinteticos_casos_estudio, "casos_estudio.csv")
    ))

    grid = cargar_csv_o_sintetico(GRID_ENRIQUECIDO_PATH, datos_sinteticos_grid_enriquecido, "grid_features_enriquecido.csv")
    grid_sin_geo = grid.drop(columns=["lat", "lon"], errors="ignore")

    mapa = clusters.merge(interpretacion, on="cluster_kmeans", how="left").merge(grid_sin_geo, on="cell_id", how="left")
    mapa = asegurar_columnas(mapa, {
        "eq_count": 0, "eq_mag_mean": 0, "eq_mag_max": 0, "cyclone_count": 0, "wind_mean": 0,
        "wind_max": 0, "dist_nearest_volcano_km": 0, "volcano_count": 0,
        "nombre_cluster": "Sin clasificar", "descripcion_negocio": "", "nivel_riesgo": "desconocido",
        "iso_a3": "", "pib_per_capita": 0,
    })
    mapa = limpiar_nan_global(mapa)
    mapa["severidad"] = calcular_severidad(mapa)
    return mapa, casos_estudio


mapa, casos_estudio = cargar_datos()

st.sidebar.title("Panel aseguradora")
st.sidebar.caption("Simulador ilustrativo de prima relativa por zona.")
st.sidebar.markdown("---")
st.sidebar.markdown(
    "Compara la severidad fisica de una zona frente a la media global, usando el mismo "
    "grid de riesgo del mapa principal, y estima una perdida potencial de referencia."
)
st.sidebar.markdown("""
<div class="callout-warn">
<p>El multiplicador y la perdida potencial mostrados son ilustrativos, basados en severidad
fisica relativa y PIB per capita como proxy de exposicion. No constituyen una tarifa
actuarial real.</p>
</div>
""", unsafe_allow_html=True)
pie_sidebar("Panel aseguradora")

encabezado_pagina(
    "Suscripcion y pricing",
    "Simulador de prima relativa por zona",
    "Estimacion ilustrativa del multiplicador de prima y la perdida potencial de una zona, "
    "calculada sobre el mismo grid de clusters de riesgo (K-Means y DBSCAN) del mapa global.",
)

with st.expander("¿Qué es la 'severidad' y por qué la usamos para prima?"):
    st.markdown("""
La **severidad** combina magnitud sísmica media, viento máximo de ciclones y
cercanía a un volcán activo en un único número de 0 a 1 por celda del grid —
tomando el peligro más alto de los tres, no el promedio, porque un riesgo
volcánico extremo no se "diluye" solo porque no haya ciclones en esa zona.

**Por qué es la base de la prima relativa:** en suscripción de seguros, la prima
no depende de "si va a pasar algo" sino de la **exposición física acumulada** de
la zona a lo largo del tiempo. Una zona con severidad 0.9 no significa que vaya a
haber un desastre este año — significa que, en el histórico usado para entrenar
el modelo, esa zona concentra sistemáticamente más magnitud sísmica, más viento
extremo o más cercanía volcánica que la media global. Es la misma lógica que usan
los modelos catastróficos (cat models) de las reaseguradoras reales, simplificada
a una sola escala comparable.
""")

callout_alcance(
    "Qué predice este modelo — y qué no.",
    "No predecimos siniestros individuales ni la probabilidad de que ocurra un evento "
    "concreto este año: eso requiere series temporales y modelos actuariales con "
    "histórico de pérdidas reales, que no tenemos aquí. Lo que el modelo aporta es "
    "<b>una capa de screening geográfico</b> — comparar la exposición física relativa "
    "de una zona frente al resto del mundo, en segundos, para decidir dónde merece la "
    "pena invertir tiempo de un actuario en tarificar en detalle, y dónde el riesgo "
    "físico ya es lo bastante alto como para exigir revisión manual antes de suscribir."
)

st.markdown("---")

lugar = st.selectbox("Zona de analisis", casos_estudio["nombre_lugar_display"])
fila_caso = casos_estudio.loc[casos_estudio["nombre_lugar_display"] == lugar].iloc[0]

mapa_tmp = mapa.copy()
mapa_tmp["_dist"] = (mapa_tmp["lat"] - fila_caso["lat"]) ** 2 + (mapa_tmp["lon"] - fila_caso["lon"]) ** 2
celda = mapa_tmp.loc[mapa_tmp["_dist"].idxmin()]

severidad_base_global = mapa["severidad"].mean()
prima_relativa = celda["severidad"] / severidad_base_global if severidad_base_global else 0
exposicion_estimada = celda["severidad"] * celda.get("pib_per_capita", 0)

if celda["cluster_dbscan"] == -1:
    clasificacion = "Revision manual requerida"
elif prima_relativa > 2:
    clasificacion = "Prima alta"
else:
    clasificacion = "Prima estandar"

col1, col2, col3 = st.columns(3)
col1.metric("Prima relativa sugerida", f"{prima_relativa:.1f}x media global")
col2.metric("Perdida potencial estimada", f"${exposicion_estimada:,.0f} por celda")
col3.metric("Clasificacion de suscripcion", clasificacion)

st.caption(
    "Multiplicador y perdida potencial ilustrativos, calculados a partir de severidad fisica "
    "y PIB per capita como proxy de exposicion economica."
)

st.markdown("---")
st.subheader("Detalle de la zona seleccionada")
st.markdown(f'<div class="callout"><p>{celda.get("descripcion_negocio", "")}</p></div>', unsafe_allow_html=True)

col_a, col_b, col_c, col_d = st.columns(4)
col_a.metric("Magnitud sismica media", f"{celda['eq_mag_mean']:.1f}")
col_b.metric("Viento maximo (ciclones)", f"{celda['wind_max']:.0f} km/h")
col_c.metric("Distancia a volcan", f"{celda['dist_nearest_volcano_km']:.0f} km")
col_d.metric("Severidad normalizada", f"{celda['severidad']:.2f}")

st.markdown("---")
st.subheader("Zonas comparables por perfil de riesgo")

mismo_cluster = mapa[mapa["cluster_kmeans"] == celda["cluster_kmeans"]]
mismo_cluster_validas = filtrar_paises_validos(mismo_cluster)

if mismo_cluster_validas.empty:
    st.info("No hay zonas comparables con datos de pais completos para este perfil de riesgo.")
else:
    comparables = mismo_cluster_validas.sample(min(5, len(mismo_cluster_validas)), random_state=0)
    comparables_mostrar = comparables[
        ["pais_nombre", "nombre_cluster", "eq_mag_mean", "wind_max", "pib_per_capita", "severidad"]
    ].rename(columns={
        "pais_nombre": "Pais", "nombre_cluster": "Perfil de riesgo",
        "eq_mag_mean": "Magnitud sismica media", "wind_max": "Viento maximo (km/h)",
        "pib_per_capita": "PIB per capita", "severidad": "Severidad",
    })
    tabla_estilizada(comparables_mostrar, columnas_progreso={"Severidad": (0, 1)})
    st.caption(
        "Se muestran solo zonas con pais identificable y dato de PIB per capita disponible. "
        "Las celdas sin esta informacion quedan excluidas para no mostrar datos incompletos."
    )

st.markdown("---")
st.subheader("De la prima relativa a la decisión de suscripción")
st.markdown("""
Una aseguradora puede usar este simulador para:

- **Filtrar solicitudes de cobertura** por región antes de tarificar en detalle —
  priorizando revisión manual en zonas con prima relativa >2x o marcadas como
  "atípicas" por DBSCAN (riesgo fuera de los patrones habituales, no capturado bien
  por el cluster general).
- **Comparar exposición entre zonas candidatas** de un mismo perfil de riesgo
  (tabla de "zonas comparables") para decidir dónde diversificar cartera en vez de
  concentrar pólizas en zonas con correlación de riesgo similar.
- **Justificar de forma transparente** ante el cliente por qué una zona tiene
  prima más alta — con el desglose físico (magnitud sísmica, viento, distancia
  a volcán) en vez de una caja negra.
""")