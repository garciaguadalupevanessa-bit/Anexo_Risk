"""
Visualizacion profesional para resultados de PCA.

Incluye:
  - Varianza acumulada (estatica)
  - Scatter 2D PC1 vs PC2 (estatico, estilo publicacion)
  - Biplot (flechas de variables originales)
  - Scatter interactivo (plotly, HTML)
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.figure import Figure
from sklearn.decomposition import PCA

sns.set_theme(
    style="whitegrid",
    context="paper",
    font="sans-serif",
    font_scale=1.3,
    palette="viridis",
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

COLOR_PCA = "#2c3e50"
COLOR_THRESHOLD = "#e74c3c"
COLOR_FILL = "#3498db"


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
        n_components, 0, cum_var, alpha=0.3, color=COLOR_FILL
    )
    ax.plot(
        n_components,
        cum_var,
        "o-",
        color=COLOR_PCA,
        linewidth=2.5,
        markersize=6,
        zorder=5,
    )
    ax.axhline(
        y=threshold,
        color=COLOR_THRESHOLD,
        linestyle="--",
        linewidth=1.8,
        alpha=0.8,
        label=f"Umbral {threshold*100:.0f}%",
    )
    ax.axvline(
        x=n_keep,
        color=COLOR_THRESHOLD,
        linestyle=":",
        linewidth=1.5,
        alpha=0.6,
    )
    ax.annotate(
        f"{n_keep} componentes\n({cum_var[n_keep-1]*100:.1f}% varianza)",
        xy=(n_keep, cum_var[n_keep - 1]),
        xytext=(n_keep + 0.5, cum_var[n_keep - 1] - 0.08),
        fontsize=11,
        color=COLOR_THRESHOLD,
        weight="bold",
        arrowprops=dict(
            arrowstyle="->", color=COLOR_THRESHOLD, lw=1.5
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
        fig.savefig(save_path.replace(".png", ".pdf"), dpi=300)
    return fig


def plot_pca_2d(
    df_pca: pd.DataFrame,
    color_col: str | None = None,
    color_data: pd.Series | np.ndarray | None = None,
    pca_model: PCA | None = None,
    figsize: tuple = (10, 8),
    cmap: str = "viridis",
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
    elif color_data is not None:
        c = np.asarray(color_data)
    else:
        c = None

    fig, ax = plt.subplots(figsize=figsize)

    if c is not None and np.issubdtype(np.asarray(c).dtype, np.number):
        scatter = ax.scatter(
            x,
            y,
            c=c,
            cmap=cmap,
            s=30,
            alpha=0.7,
            edgecolors="w",
            linewidth=0.3,
            zorder=3,
        )
        fig.colorbar(scatter, ax=ax, shrink=0.7).set_label(
            color_col or "Valor", fontsize=12, weight="bold"
        )
    else:
        ax.scatter(
            x,
            y,
            s=30,
            alpha=0.7,
            c=COLOR_PCA,
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
    """Biplot: scatter PC1 vs PC2 con vectores de las variables originales.

    Parameters
    ----------
    df_pca : pd.DataFrame
        DataFrame con columnas PC1, PC2.
    pca_model : PCA
        Modelo PCA entrenado (debe tener components_).
    feature_names : list
        Nombres de las features originales.
    figsize : tuple, optional
        Tamano de figura.
    scale_factor : float, optional
        Escala para las flechas. Auto si None.
    save_path : str, optional
        Ruta para guardar.
    """
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
        c=COLOR_PCA,
        s=20,
        alpha=0.5,
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
            fc=COLOR_THRESHOLD,
            ec=COLOR_THRESHOLD,
            alpha=0.8,
            linewidth=1.5,
            zorder=5,
        )
        label_offset = scale_factor * 0.06
        ax.text(
            dx + label_offset,
            dy + label_offset,
            name,
            fontsize=9,
            color=COLOR_THRESHOLD,
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
    """Scatter 2D interactivo con plotly (hover, zoom).

    Parameters
    ----------
    df_pca : pd.DataFrame
        DataFrame con PC1, PC2.
    color_col : str, optional
        Columna para colorear.
    pca_model : PCA, optional
        Para etiquetar ejes con % varianza.
    save_path : str, optional
        Ruta HTML de salida.

    Returns
    -------
    str
        Ruta del archivo HTML generado.
    """
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

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

    fig.update_traces(marker=dict(size=6, opacity=0.7, line=dict(width=0.3, color="white")))
    fig.update_layout(
        template="simple_white",
        hovermode="closest",
        font=dict(family="sans-serif", size=12),
    )

    if save_path:
        fig.write_html(save_path)
    return save_path
