"""
Pagina: Priorizacion de ayuda humanitaria.

Indice compuesto de prioridad por pais (severidad fisica, vulnerabilidad
economica y poblacion) para orientar la asignacion de fondos de
adaptacion climatica.
"""

import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.append(str(Path(__file__).parent.parent))
from theme import inyectar_tema, encabezado_pagina, pie_sidebar, CHART_SCALE_RIESGO, tabla_estilizada, callout_alcance
from data_utils import (
    cargar_csv_o_sintetico, asegurar_columnas, calcular_severidad,
    normalizar_interpretacion, datos_sinteticos_clusters,
    datos_sinteticos_interpretacion, datos_sinteticos_grid_pais,
)

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "processed"
CLUSTERS_PATH = DATA_DIR / "cluster_labels.csv"
INTERPRETACION_PATH = DATA_DIR / "interpretacion_clusters.csv"
GRID_ENRIQUECIDO_PATH = DATA_DIR / "grid_features_enriquecido.csv"

UMBRAL_ALTO_RIESGO = 0.6
PESO_SEVERIDAD, PESO_PIB_INVERTIDO, PESO_POBLACION = 0.5, 0.3, 0.2

inyectar_tema()


@st.cache_data(ttl=600)
def cargar_datos():
    clusters = cargar_csv_o_sintetico(CLUSTERS_PATH, datos_sinteticos_clusters, "cluster_labels.csv")
    clusters = clusters.rename(columns={"kmeans_label": "cluster_kmeans", "dbscan_label": "cluster_dbscan"})

    interpretacion = normalizar_interpretacion(
        cargar_csv_o_sintetico(INTERPRETACION_PATH, datos_sinteticos_interpretacion, "interpretacion_clusters.csv")
    )

    grid = cargar_csv_o_sintetico(GRID_ENRIQUECIDO_PATH, datos_sinteticos_grid_pais, "grid_features_enriquecido.csv")
    grid_sin_geo = grid.drop(columns=[c for c in ("lat", "lon") if c in grid.columns])

    mapa = clusters.merge(interpretacion, on="cluster_kmeans", how="left").merge(grid_sin_geo, on="cell_id", how="left")
    mapa = asegurar_columnas(mapa, {
        "eq_mag_mean": 0, "wind_max": 0, "dist_nearest_volcano_km": 0, "nombre_cluster": "Sin clasificar",
    })
    mapa["severidad"] = calcular_severidad(mapa)
    return mapa


mapa_pais = cargar_datos()

sin_pib = mapa_pais[mapa_pais["pib_per_capita"].isna() & mapa_pais["iso_a3"].notna()]["iso_a3"].unique()

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

st.sidebar.title("Ayuda humanitaria")
st.sidebar.caption("Priorizacion de intervencion preventiva por pais.")
st.sidebar.markdown("---")
st.sidebar.markdown("**Composicion del indice**")
st.sidebar.markdown(f"""
- Severidad fisica: **{PESO_SEVERIDAD*100:.0f}%**
- PIB per capita invertido: **{PESO_PIB_INVERTIDO*100:.0f}%**
- Poblacion: **{PESO_POBLACION*100:.0f}%**
""")
st.sidebar.markdown("""
<div class="callout-warn">
<p>Los pesos del indice son una decision de diseno transparente, no un valor cientifico fijo.
Pueden ajustarse segun la prioridad del organismo que use esta herramienta.</p>
</div>
""", unsafe_allow_html=True)
pie_sidebar("Ayuda humanitaria")

encabezado_pagina(
    "Cooperacion internacional",
    "Priorizacion de ayuda humanitaria por pais",
    "Ranking de paises segun un indice compuesto de prioridad para intervencion preventiva, "
    "calculado sobre el mismo grid de riesgo del mapa global.",
)

with st.expander("¿Qué es la 'severidad' y por qué importa?"):
    st.markdown("""
La **severidad** combina tres peligros físicos en un único número de 0 a 1:
magnitud sísmica media, viento máximo de ciclones y cercanía a un volcán activo.
Para cada celda del grid, tomamos el peligro más alto de los tres (no el promedio) —
porque una zona con riesgo volcánico extremo sigue siendo extremadamente peligrosa
aunque no tenga ciclones. Es el mismo indicador que usamos en el mapa global y en
el simulador de aseguradora: una sola escala común para comparar amenazas de
naturaleza muy distinta.

**Por qué importa para ayuda humanitaria:** la severidad física por sí sola no dice
dónde intervenir — un terremoto de magnitud 7 en una zona rica y bien preparada
causa muchas menos muertes que el mismo terremoto en una zona pobre sin
infraestructura de respuesta. Por eso el índice de prioridad no ordena solo por
severidad, sino por severidad **combinada con** vulnerabilidad económica y
población expuesta — la pregunta real no es "¿dónde tiembla más?" sino
"¿dónde un desastre haría más daño humano si ocurriera?".
""")

callout_alcance(
    "Qué predice este modelo — y qué no.",
    "No predecimos <i>cuándo</i> ocurrirá un terremoto o ciclón: eso corresponde a "
    "sismología y meteorología, no a clustering no supervisado. Lo que el modelo aporta "
    "es identificar de forma sistemática y a escala global <b>qué zonas combinan "
    "alta exposición física con baja capacidad de respuesta</b> — para que la "
    "preparación (almacenes de ayuda, protocolos de alerta temprana, refuerzo de "
    "infraestructura) se planifique antes del desastre, no después."
)

st.markdown("---")

col1, col2, col3 = st.columns(3)
col1.metric("Paises en el ranking", f"{len(resumen_pais)}")
col2.metric("Celdas de alto riesgo (global)", f"{(mapa_pais['severidad'] > UMBRAL_ALTO_RIESGO).sum():,}")
col3.metric("Paises sin dato de PIB", f"{len(sin_pib)}")

st.markdown("---")
st.subheader("Los 15 paises prioritarios para intervencion preventiva")

top_paises = resumen_pais.nlargest(15, "indice_prioridad").copy()

fig = px.bar(
    top_paises.sort_values("indice_prioridad"), x="indice_prioridad", y="iso_a3", orientation="h",
    color="indice_prioridad", color_continuous_scale=CHART_SCALE_RIESGO,
    text=top_paises.sort_values("indice_prioridad")["indice_prioridad"].apply(lambda x: f"{x:.2f}"),
    labels={"indice_prioridad": "Indice de prioridad", "iso_a3": "Pais"},
)
fig.update_layout(height=440, showlegend=False, plot_bgcolor="#F7F6F2", paper_bgcolor="#F7F6F2")
fig.update_traces(textposition="outside")
fig.update_coloraxes(showscale=False)
st.plotly_chart(fig, use_container_width=True)

top_display = top_paises.copy()
top_display["pib_per_capita"] = top_display["pib_per_capita"].apply(lambda x: x if pd.notna(x) else 0)

tabla_estilizada(
    top_display[["iso_a3", "severidad_media", "n_celdas_alto_riesgo", "pib_per_capita", "indice_prioridad"]]
    .rename(columns={"iso_a3": "Pais", "severidad_media": "Severidad media",
                      "n_celdas_alto_riesgo": "Celdas de alto riesgo", "pib_per_capita": "PIB per capita",
                      "indice_prioridad": "Indice de prioridad"}),
    columnas_progreso={"Severidad media": (0, 1), "Indice de prioridad": (0, 1)},
)

st.caption(
    "Indice = 50% severidad fisica + 30% inverso del PIB per capita + 20% poblacion. "
    "Los pesos son ajustables segun la prioridad del organismo que use esta herramienta."
)

if len(sin_pib) > 0:
    st.markdown(f"""
    <div class="callout-warn">
    <p><b>{len(sin_pib)} paises</b> sin dato de PIB del Banco Mundial ({', '.join(sin_pib)}) quedan
    fuera de este ranking automatico por falta de datos, no porque su riesgo sea bajo. Requieren
    revision manual por parte del equipo tecnico.</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")
st.subheader("De la tabla a la acción")
st.markdown("""
Un organismo humanitario puede usar este ranking para:

- **Preposicionar suministros** (agua, refugios, kits médicos) en los países del
  top 15 antes de la temporada de mayor riesgo, en vez de reaccionar después del evento.
- **Priorizar programas de alerta temprana** en los países con más celdas de alto
  riesgo pero menos capacidad económica para desplegarlos por sí mismos.
- **Ajustar los pesos del índice** (barra lateral) según su mandato específico —
  una ONG centrada en infancia puede querer ponderar población más que severidad,
  por ejemplo.
""")