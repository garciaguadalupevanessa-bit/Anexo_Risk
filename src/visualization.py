"""
Visualizacion profesional para resultados de PCA de riesgo geologico global.

Incluye:
  - Varianza acumulada (estatica)
  - Scatter 2D PC1 vs PC2 (estatico, estilo publicacion)
  - Biplot (flechas de variables originales)
  - Scatter interactivo (plotly, HTML)
  - Mapa geografico de riesgo (Folium)
  - Pairplot de componentes (Seaborn)
  - Loadings heatmap (Seaborn)
  - PCA 3D interactivo (Plotly)
"""

import branca
import folium
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
from matplotlib.figure import Figure
from plotly.subplots import make_subplots
from sklearn.decomposition import PCA

sns.set_theme(
    style="whitegrid",
    context="paper",
    font="sans-serif",
    font_scale=1.2,
    palette="mako",
)

plt.rcParams.update(
    {
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "font.family": "sans-serif",
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)

COLOR_PRIMARY = "#2c3e50"
COLOR_ACCENT = "#e74c3c"
COLOR_FILL = "#3498db"
COLOR_GRADIENT = "plasma"


def plot_varianza_acumulada(
    pca_model: PCA,
    threshold: float = 0.85,
    figsize: tuple = (10, 6),
    save_path: str | None = None,
) -> Figure:
    explained_var = pca_model.explained_variance_ratio_
    cum_var = np.cumsum(explained_var)
    n_components = np.arange(1, len(cum_var) + 1)
    n_keep = int(np.searchsorted(cum_var, threshold) + 1)

    fig, ax = plt.subplots(figsize=figsize)
    ax.fill_between(
        n_components, 0, cum_var, alpha=0.25, color=COLOR_FILL
    )
    ax.plot(
        n_components,
        cum_var,
        "o-",
        color=COLOR_PRIMARY,
        linewidth=2.5,
        markersize=7,
        zorder=5,
        markerfacecolor=COLOR_FILL,
        markeredgecolor=COLOR_PRIMARY,
    )
    ax.axhline(
        y=threshold,
        color=COLOR_ACCENT,
        linestyle="--",
        linewidth=1.8,
        alpha=0.8,
        label=f"Umbral {threshold*100:.0f}%",
    )
    ax.axvline(
        x=n_keep,
        color=COLOR_ACCENT,
        linestyle=":",
        linewidth=1.5,
        alpha=0.6,
    )
    ax.annotate(
        f"{n_keep} componentes\n({cum_var[n_keep-1]*100:.1f}% varianza)",
        xy=(n_keep, cum_var[n_keep - 1]),
        xytext=(n_keep + 0.8, cum_var[n_keep - 1] - 0.1),
        fontsize=11,
        color=COLOR_ACCENT,
        weight="bold",
        arrowprops=dict(
            arrowstyle="->", color=COLOR_ACCENT, lw=1.5
        ),
    )
    ax.set_xlabel("Numero de componentes principales", fontsize=13)
    ax.set_ylabel("Varianza explicada acumulada", fontsize=13)
    ax.set_title(
        "Varianza Explicada Acumulada vs. Componentes Principales",
        fontsize=14,
        weight="bold",
    )
    ax.set_xlim(0, len(cum_var) + 1)
    ax.set_ylim(0, 1.05)
    ax.legend(loc="lower right", frameon=True, fancybox=True)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300)
    return fig


def plot_pca_2d(
    df_pca: pd.DataFrame,
    color_col: str | None = None,
    color_data: pd.Series | np.ndarray | None = None,
    pca_model: PCA | None = None,
    figsize: tuple = (10, 8),
    cmap: str = "plasma",
    save_path: str | None = None,
) -> Figure:
    x = df_pca["PC1"].values
    y = df_pca["PC2"].values

    x_label = "PC1"
    y_label = "PC2"
    if pca_model is not None:
        vr = pca_model.explained_variance_ratio_
        x_label = f"PC1 ({vr[0]*100:.1f}% varianza)"
        y_label = f"PC2 ({vr[1]*100:.1f}% varianza)"

    if color_col and color_col in df_pca.columns:
        c = df_pca[color_col].values
        label = color_col
    elif color_data is not None:
        c = np.asarray(color_data)
        label = "Valor"
    else:
        c = None
        label = None

    fig, ax = plt.subplots(figsize=figsize)

    if c is not None and np.issubdtype(np.asarray(c).dtype, np.number):
        scatter = ax.scatter(
            x,
            y,
            c=c,
            cmap=cmap,
            s=45,
            alpha=0.75,
            edgecolors="w",
            linewidth=0.4,
            zorder=3,
        )
        cbar = fig.colorbar(scatter, ax=ax, shrink=0.7)
        cbar.set_label(label or "Valor", fontsize=12, weight="bold")
    elif c is not None:
        unique = np.unique(c)
        palette = sns.color_palette("mako", len(unique))
        for i, val in enumerate(unique):
            mask = np.asarray(c) == val
            ax.scatter(
                x[mask],
                y[mask],
                c=[palette[i]],
                s=45,
                alpha=0.75,
                edgecolors="w",
                linewidth=0.4,
                label=str(val),
                zorder=3,
            )
        ax.legend(frameon=True, fancybox=True)
    else:
        ax.scatter(
            x,
            y,
            s=35,
            alpha=0.65,
            c=COLOR_PRIMARY,
            edgecolors="w",
            linewidth=0.3,
            zorder=3,
        )

    ax.set_xlabel(x_label, fontsize=13)
    ax.set_ylabel(y_label, fontsize=13)
    ax.set_title(
        "Proyeccion 2D de Componentes Principales",
        fontsize=14,
        weight="bold",
    )
    ax.axhline(0, color="gray", linewidth=0.5, alpha=0.3)
    ax.axvline(0, color="gray", linewidth=0.5, alpha=0.3)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300)
    return fig


def plot_biplot(
    df_pca: pd.DataFrame,
    pca_model: PCA,
    feature_names: list[str],
    figsize: tuple = (12, 10),
    scale_factor: float = None,
    save_path: str | None = None,
) -> Figure:
    x = df_pca["PC1"].values
    y = df_pca["PC2"].values
    comps = pca_model.components_[:2, :]
    vr = pca_model.explained_variance_ratio_

    if scale_factor is None:
        x_range = x.max() - x.min()
        y_range = y.max() - y.min()
        scale_factor = min(x_range, y_range) * 0.8

    fig, ax = plt.subplots(figsize=figsize)

    ax.scatter(
        x,
        y,
        c=COLOR_PRIMARY,
        s=20,
        alpha=0.4,
        edgecolors="w",
        linewidth=0.2,
        zorder=2,
    )

    for i, name in enumerate(feature_names):
        dx = comps[0, i] * scale_factor
        dy = comps[1, i] * scale_factor
        ax.arrow(
            0,
            0,
            dx,
            dy,
            head_width=scale_factor * 0.04,
            head_length=scale_factor * 0.04,
            fc=COLOR_ACCENT,
            ec=COLOR_ACCENT,
            alpha=0.85,
            linewidth=1.8,
            zorder=5,
        )
        label_offset = scale_factor * 0.06
        ax.text(
            dx + label_offset,
            dy + label_offset,
            name,
            fontsize=10,
            color=COLOR_ACCENT,
            weight="bold",
            zorder=6,
        )

    ax.set_xlabel(f"PC1 ({vr[0]*100:.1f}%)", fontsize=13)
    ax.set_ylabel(f"PC2 ({vr[1]*100:.1f}%)", fontsize=13)
    ax.set_title(
        "Biplot: Proyeccion 2D con vectores de variables originales",
        fontsize=14,
        weight="bold",
    )
    ax.axhline(0, color="gray", linewidth=0.5, alpha=0.3)
    ax.axvline(0, color="gray", linewidth=0.5, alpha=0.3)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300)
    return fig


def plot_pca_interactivo(
    df_pca: pd.DataFrame,
    color_col: str | None = None,
    pca_model: PCA | None = None,
    save_path: str | None = "pca_interactivo.html",
) -> str:
    x_label = "PC1"
    y_label = "PC2"
    if pca_model is not None:
        vr = pca_model.explained_variance_ratio_
        x_label = f"PC1 ({vr[0]*100:.1f}%)"
        y_label = f"PC2 ({vr[1]*100:.1f}%)"

    if color_col and color_col in df_pca.columns:
        fig = px.scatter(
            df_pca,
            x="PC1",
            y="PC2",
            color=color_col,
            color_continuous_scale="plasma",
            title="PCA Interactivo - Proyeccion 2D",
            labels={"PC1": x_label, "PC2": y_label},
            width=1000,
            height=700,
        )
    else:
        fig = px.scatter(
            df_pca,
            x="PC1",
            y="PC2",
            title="PCA Interactivo - Proyeccion 2D",
            labels={"PC1": x_label, "PC2": y_label},
            width=1000,
            height=700,
        )

    fig.update_traces(marker=dict(size=7, opacity=0.75, line=dict(width=0.3, color="white")))
    fig.update_layout(
        template="plotly_white",
        hovermode="closest",
        font=dict(family="sans-serif", size=12),
    )

    if save_path:
        fig.write_html(save_path)
    return save_path


def plot_mapa_riesgo(
    df: pd.DataFrame,
    lat_col: str = "lat",
    lon_col: str = "lon",
    color_col: str | None = None,
    popup_cols: list[str] | None = None,
    radius_scale: float = 3.0,
    save_path: str | None = "mapa_riesgo.html",
) -> folium.Map:
    """Mapa interactivo Folium con puntos geograficos coloreados por riesgo.

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame con lat, lon y columna de color.
    lat_col, lon_col : str
        Nombres de columnas de coordenadas.
    color_col : str, optional
        Columna para colorear (ej. PC1, magnitud). Mapa de gradient.
    popup_cols : list, optional
        Columnas a mostrar en el popup al hacer clic.
    radius_scale : float
        Factor de escala para el radio de los circulos.
    save_path : str or None
        Ruta del HTML de salida.

    Returns
    -------
    folium.Map
    """
    center_lat = df[lat_col].mean()
    center_lon = df[lon_col].mean()

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=2,
        tiles="CartoDB positron",
        control_scale=True,
    )

    folium.TileLayer(
        "OpenStreetMap", name="Calles"
    ).add_to(m)
    folium.TileLayer(
        "CartoDB dark_matter", name="Oscuro"
    ).add_to(m)

    if color_col and color_col in df.columns:
        values = df[color_col].values
        vmin, vmax = float(values.min()), float(values.max())
        colormap = branca.colormap.LinearColormap(
            colors=["#2c3e50", "#e74c3c"],
            vmin=vmin,
            vmax=vmax,
            caption=color_col,
        )
        colormap.add_to(m)

        for idx, row in df.iterrows():
            normalized = (row[color_col] - vmin) / (vmax - vmin + 1e-10)
            radius = max(3, normalized * 15 * radius_scale)

            popup_text = f"<b>{color_col}: {row[color_col]:.3f}</b><br>"
            if popup_cols:
                for col in popup_cols:
                    if col in df.columns:
                        val = row[col]
                        if isinstance(val, float):
                            popup_text += f"{col}: {val:.2f}<br>"
                        else:
                            popup_text += f"{col}: {val}<br>"

            folium.CircleMarker(
                location=[row[lat_col], row[lon_col]],
                radius=radius,
                color=colormap(row[color_col]),
                fill=True,
                fillColor=colormap(row[color_col]),
                fillOpacity=0.7,
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=f"{color_col}: {row[color_col]:.3f}",
            ).add_to(m)
    else:
        for idx, row in df.iterrows():
            folium.CircleMarker(
                location=[row[lat_col], row[lon_col]],
                radius=5,
                color=COLOR_FILL,
                fill=True,
                fillColor=COLOR_FILL,
                fillOpacity=0.6,
                popup=f"({row[lat_col]:.2f}, {row[lon_col]:.2f})",
            ).add_to(m)

    folium.LayerControl().add_to(m)

    if save_path:
        m.save(save_path)
    return m


def plot_pairplot_pca(
    df_pca: pd.DataFrame,
    n_components: int = 4,
    color_col: str | None = None,
    palette: str = "mako",
    save_path: str | None = None,
) -> sns.PairGrid:
    """Pairplot de los primeros N componentes principales.

    Parameters
    ----------
    df_pca : pd.DataFrame
        DataFrame con columnas PC1, PC2, ...
    n_components : int
        Numero de componentes a incluir.
    color_col : str, optional
        Columna para colorear los puntos.
    palette : str
        Paleta de colores Seaborn.
    save_path : str, optional
        Ruta para guardar la figura.

    Returns
    -------
    sns.PairGrid
    """
    comp_cols = [f"PC{i+1}" for i in range(min(n_components, len(df_pca.columns)))]

    if color_col and color_col in df_pca.columns:
        g = sns.pairplot(
            df_pca,
            vars=comp_cols,
            hue=color_col,
            palette=palette,
            diag_kind="kde",
            plot_kws={
                "alpha": 0.6,
                "s": 30,
                "edgecolor": "w",
                "linewidth": 0.3,
            },
            diag_kws={"fill": True, "alpha": 0.4},
        )
    else:
        g = sns.pairplot(
            df_pca,
            vars=comp_cols,
            diag_kind="kde",
            plot_kws={
                "alpha": 0.5,
                "s": 25,
                "color": COLOR_PRIMARY,
                "edgecolor": "w",
                "linewidth": 0.3,
            },
            diag_kws={
                "fill": True,
                "alpha": 0.3,
                "color": COLOR_FILL,
            },
        )

    g.fig.suptitle(
        "Pairplot de Componentes Principales",
        fontsize=14,
        weight="bold",
        y=1.02,
    )

    if save_path:
        g.savefig(save_path, dpi=300)
    return g


def plot_loadings_heatmap(
    pca_model: PCA,
    feature_names: list[str],
    n_components: int = 6,
    figsize: tuple = (12, 8),
    save_path: str | None = None,
) -> Figure:
    """Mapa de calor de loadings (contribucion features a componentes).

    Parameters
    ----------
    pca_model : PCA
        Modelo PCA entrenado.
    feature_names : list
        Nombres de las features originales.
    n_components : int
        Numero de componentes a mostrar.
    figsize : tuple
        Tamano de figura.
    save_path : str, optional
        Ruta para guardar.

    Returns
    -------
    Figure
    """
    n_comp = min(n_components, pca_model.components_.shape[0])
    loadings = pca_model.components_[:n_comp, :]

    comp_labels = [f"PC{i+1}" for i in range(n_comp)]

    fig, ax = plt.subplots(figsize=figsize)
    sns.heatmap(
        loadings,
        xticklabels=feature_names,
        yticklabels=comp_labels,
        cmap="RdBu_r",
        center=0,
        annot=True,
        fmt=".2f",
        linewidths=0.8,
        cbar_kws={"label": "Loading", "shrink": 0.8},
        ax=ax,
    )
    ax.set_title(
        "Loadings: Contribucion de variables originales a componentes",
        fontsize=14,
        weight="bold",
    )
    ax.set_xlabel("Variables originales", fontsize=12)
    ax.set_ylabel("Componentes principales", fontsize=12)
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=9)
    plt.setp(ax.get_yticklabels(), rotation=0, fontsize=10)
    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300)
    return fig


def plot_pca_3d(
    df_pca: pd.DataFrame,
    color_col: str | None = None,
    pca_model: PCA | None = None,
    save_path: str | None = "pca_3d.html",
) -> str:
    """Scatter 3D interactivo de PC1, PC2, PC3 con Plotly.

    Parameters
    ----------
    df_pca : pd.DataFrame
        DataFrame con columnas PC1, PC2, PC3.
    color_col : str, optional
        Columna para colorear los puntos.
    pca_model : PCA, optional
        Para etiquetar ejes con % varianza.
    save_path : str, optional
        Ruta HTML de salida.

    Returns
    -------
    str
    """
    x_label, y_label, z_label = "PC1", "PC2", "PC3"
    if pca_model is not None:
        vr = pca_model.explained_variance_ratio_
        x_label = f"PC1 ({vr[0]*100:.1f}%)"
        y_label = f"PC2 ({vr[1]*100:.1f}%)"
        z_label = f"PC3 ({vr[2]*100:.1f}%)"

    if color_col and color_col in df_pca.columns:
        fig = px.scatter_3d(
            df_pca,
            x="PC1",
            y="PC2",
            z="PC3",
            color=color_col,
            color_continuous_scale="plasma",
            title="PCA 3D - Espacio de componentes principales",
            labels={
                "PC1": x_label,
                "PC2": y_label,
                "PC3": z_label,
            },
            width=1000,
            height=750,
        )
    else:
        fig = px.scatter_3d(
            df_pca,
            x="PC1",
            y="PC2",
            z="PC3",
            title="PCA 3D - Espacio de componentes principales",
            labels={
                "PC1": x_label,
                "PC2": y_label,
                "PC3": z_label,
            },
            width=1000,
            height=750,
        )

    fig.update_traces(
        marker=dict(size=4, opacity=0.7, line=dict(width=0.2, color="white"))
    )
    fig.update_layout(
        template="plotly_white",
        hovermode="closest",
        font=dict(family="sans-serif", size=12),
        scene=dict(
            xaxis=dict(showbackground=True, backgroundcolor="rgba(240,240,240,0.8)"),
            yaxis=dict(showbackground=True, backgroundcolor="rgba(240,240,240,0.8)"),
            zaxis=dict(showbackground=True, backgroundcolor="rgba(240,240,240,0.8)"),
        ),
    )

    if save_path:
        fig.write_html(save_path)
    return save_path
