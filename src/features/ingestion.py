"""
Fusión e ingesta de fuentes sísmicas crudas (pre-agregación).

Este módulo se encarga de combinar catálogos sísmicos de distinta
procedencia (USGS global, IGN regional España/Canarias) en un único
DataFrame de eventos, ANTES de que ese resultado se pase a
`engineering.compute_seismic_features` para la agregación por celda H3.

No hace agregación por celda ni asignación H3 — eso sigue siendo
responsabilidad de `grid.py` / `engineering.py`. Este módulo solo
resuelve el problema de "tengo dos catálogos que se solapan
geográficamente, ¿cómo los combino sin contar el mismo sismo dos
veces?".
"""

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree


def deduplicar_usgs_vs_ign(
    df_usgs: pd.DataFrame,
    df_ign: pd.DataFrame,
    radio_km: float = 50.0,
    ventana_horas: float = 6.0,
) -> pd.DataFrame:
    """Elimina de USGS los eventos que probablemente sean el mismo sismo
    físico ya presente en el catálogo IGN (más detallado para España,
    Canarias y zonas fronterizas cercanas: sur de Francia, norte de
    Argelia/Marruecos).

    Motivación: IGN no es un catálogo estrictamente "España" (incluye
    eventos transfronterizos, ej. Bagneres-de-Bigorre.FRA, ORAN.ARG),
    así que un simple filtro por bounding-box de España deja fuera
    casos de solape real con USGS. En vez de eso, se compara evento a
    evento por cercanía espacio-temporal.

    Parameters
    ----------
    df_usgs : pd.DataFrame
        Catálogo global USGS. Debe tener columnas 'timestamp', 'lat', 'lon'.
    df_ign : pd.DataFrame
        Catálogo IGN (España/Canarias). Debe tener columnas
        'timestamp', 'lat', 'lon'.
    radio_km : float, optional
        Distancia máxima (km) entre un evento USGS y uno IGN para
        considerarlos el mismo sismo físico. Default 50 km.
    ventana_horas : float, optional
        Diferencia horaria máxima entre ambos registros para
        considerarlos el mismo evento. Default 6 horas.

    Returns
    -------
    pd.DataFrame
        Copia de df_usgs sin las filas identificadas como duplicadas
        de IGN. Conserva todas las columnas originales de df_usgs
        (se añade y luego se elimina una columna auxiliar 'fecha').

    Notes
    -----
    La comparación se hace por bloques de mismo día (con margen de
    ±1 día para no perder matches cerca de medianoche en distintas
    zonas horarias) para evitar un cruce O(n_usgs * n_ign) completo.
    Dentro de cada bloque se usa un cKDTree sobre coordenadas en
    radianes para encontrar, de cada evento USGS, el vecino IGN más
    cercano en distancia great-circle aproximada.

    Ajustar `radio_km` / `ventana_horas` si el número de duplicados
    detectado parece demasiado bajo o demasiado alto para el volumen
    de datos con el que se está trabajando.
    """
    usgs = df_usgs.copy()
    ign = df_ign.copy()

    usgs['timestamp'] = pd.to_datetime(
        usgs['timestamp'], utc=True, format='mixed'
    ).dt.tz_convert(None)
    ign['timestamp'] = pd.to_datetime(
        ign['timestamp'], utc=True, format='mixed'
    ).dt.tz_convert(None)

    usgs['fecha'] = usgs['timestamp'].dt.normalize()
    ign['fecha'] = ign['timestamp'].dt.normalize()

    R = 6371.0  # radio de la Tierra en km
    es_duplicado = pd.Series(False, index=usgs.index)

    # Solo tiene sentido comparar días en los que IGN tiene algo que ofrecer
    fechas_relevantes = set(ign['fecha'].unique())

    for fecha in fechas_relevantes:
        # margen de ±1 día por si el sismo ocurre cerca de medianoche
        # en zonas horarias distintas entre ambos catálogos
        mask_ign_dia = ign['fecha'].between(
            pd.Timestamp(fecha) - pd.Timedelta(days=1),
            pd.Timestamp(fecha) + pd.Timedelta(days=1),
        )
        ign_dia = ign[mask_ign_dia]
        mask_usgs_dia = usgs['fecha'] == fecha
        usgs_dia = usgs[mask_usgs_dia]

        if ign_dia.empty or usgs_dia.empty:
            continue

        ign_coords = np.radians(ign_dia[['lat', 'lon']].values)
        usgs_coords = np.radians(usgs_dia[['lat', 'lon']].values)

        tree = cKDTree(ign_coords)
        dist_rad, idx = tree.query(usgs_coords)
        dist_km = dist_rad * R

        horas_diff = np.abs(
            (usgs_dia['timestamp'].values - ign_dia['timestamp'].values[idx])
            / np.timedelta64(1, 'h')
        )

        es_match = (dist_km <= radio_km) & (horas_diff <= ventana_horas)
        es_duplicado.loc[usgs_dia.index[es_match]] = True

    n_dup = es_duplicado.sum()
    print(
        f"USGS: {n_dup:,} eventos identificados como duplicados de IGN "
        f"(de {len(usgs):,} totales) -> se descartan"
    )

    usgs_sin_duplicados = usgs[~es_duplicado].drop(columns=['fecha'])
    return usgs_sin_duplicados


def combinar_sismos_usgs_ign(
    df_usgs: pd.DataFrame,
    df_ign: pd.DataFrame,
    cols_comunes: list | None = None,
    radio_km: float = 50.0,
    ventana_horas: float = 6.0,
) -> pd.DataFrame:
    """Combina USGS (global) + IGN (España/Canarias, mayor detalle) en un
    único DataFrame de sismos, deduplicando por proximidad espacio-temporal.

    Wrapper de conveniencia sobre `deduplicar_usgs_vs_ign` que además
    selecciona las columnas comunes y concatena el resultado, listo
    para pasarse a `engineering.compute_seismic_features`.

    Parameters
    ----------
    df_usgs, df_ign : pd.DataFrame
        Catálogos crudos ya limpios (usgs_earthquakes_clean.csv,
        espana_clean.csv).
    cols_comunes : list, optional
        Columnas a conservar tras la fusión. Por defecto
        ['timestamp', 'lat', 'lon', 'depth_km', 'magnitude'].
    radio_km, ventana_horas : float, optional
        Ver `deduplicar_usgs_vs_ign`.

    Returns
    -------
    pd.DataFrame
        Sismos combinados sin duplicados, con solo `cols_comunes`.
    """
    if cols_comunes is None:
        cols_comunes = ["timestamp", "lat", "lon", "depth_km", "magnitude"]

    usgs_dedup = deduplicar_usgs_vs_ign(
        df_usgs, df_ign, radio_km=radio_km, ventana_horas=ventana_horas
    )

    df_sismos = pd.concat(
        [usgs_dedup[cols_comunes], df_ign[cols_comunes]],
        ignore_index=True,
    )
    return df_sismos
