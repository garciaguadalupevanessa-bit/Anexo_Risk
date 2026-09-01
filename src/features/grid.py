import h3
import pandas as pd


def build_global_grid(resolution=3):
    """Genera el grid H3 global a la resolución indicada.

    Parte de las 122 celdas de resolución 0 (que cubren todo el planeta)
    y las subdivide hasta la resolución pedida.
    """
    res0_cells = h3.get_res0_cells()
    cells = set()
    for cell in res0_cells:
        if resolution == 0:
            cells.add(cell)
        else:
            cells.update(h3.cell_to_children(cell, resolution))

    grid_df = pd.DataFrame({'cell_id': list(cells)})
    grid_df[['lat', 'lon']] = grid_df['cell_id'].apply(
        lambda c: pd.Series(h3.cell_to_latlng(c))
    )
    return grid_df


def assign_events_to_cells(events_df, resolution=3, lat_col='lat', lon_col='lon'):
    """Asigna cada evento (fila) a su celda H3 correspondiente."""
    df = events_df.copy()
    df['cell_id'] = df.apply(
        lambda r: h3.latlng_to_cell(r[lat_col], r[lon_col], resolution), axis=1
    )
    return df