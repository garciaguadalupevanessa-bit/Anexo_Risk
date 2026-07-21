"""
Visualización profesional para resultados de PCA.

Gráficos estilo publicación para el análisis de componentes principales.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
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
    """Gráfico de varianza explicada acumulada vs número de componentes.

    Parameters
    ----------
    pca_model : PCA
        Modelo PCA ya entrenado.
    threshold : float, optional
        Línea de corte de varianza a retener, por defecto 0.85.
    figsize : tuple, optional
        Tamaño de la figura, por defecto (10, 6).
    save_path : str or None, optional
        Ruta para guardar la figura. Si None, no se guarda.

    Returns
    -------
    Figure
        Objeto figure de matplotlib.
    """
    explained_var = pca_model.explained_variance_ratio_
    cum_var = np.cumsum(explained_var)
    n_components = np.arange(1, len(cum_var) + 1)

    n_keep = int(np.searchsorted(cum_var, threshold) + 1)

    fig, ax = plt.subplots(figsize=figsize)

    ax.fill_between(
        n_components,
        0,
        cum_var,
        alpha=0.3,
        color=COLOR_FILL,
        label="Varianza acumulada",
    )
    ax.plot(
        n_components,
        cum_var,
        "o-",
        color=COLOR_PCA,
        linewidth=2.5,
        markersize=6,
        label="Varianza explicada acumulada",
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

    ax.set_xlabel("Número de componentes principales", fontsize=13)
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
    """Scatter 2D de PC1 vs PC2.

    Parameters
    ----------
    df_pca : pd.DataFrame
        DataFrame con columnas PC1, PC2...
    color_col : str or None, optional
        Nombre de la columna para colorear los puntos (debe estar en df_pca
        o se usará 'color_data').
    color_data : pd.Series or np.ndarray or None, optional
        Array con valores para colorear (alternativa a color_col).
    pca_model : PCA or None, optional
        Modelo PCA entrenado (para etiquetar ejes con % varianza).
    figsize : tuple, optional
        Tamaño de la figura, por defecto (10, 8).
    cmap : str, optional
        Mapa de colores de matplotlib, por defecto "viridis".
    save_path : str or None, optional
        Ruta para guardar la figura.

    Returns
    -------
    Figure
    """
    fig, ax = plt.subplots(figsize=figsize)

    x_label = "PC1"
    y_label = "PC2"

    if pca_model is not None and hasattr(pca_model, "explained_variance_ratio_"):
        var_pc1 = pca_model.explained_variance_ratio_[0] * 100
        var_pc2 = pca_model.explained_variance_ratio_[1] * 100
        x_label = f"PC1 ({var_pc1:.1f}% varianza)"
        y_label = f"PC2 ({var_pc2:.1f}% varianza)"

    x = df_pca["PC1"].values
    y = df_pca["PC2"].values

    if color_col and color_col in df_pca.columns:
        c = df_pca[color_col].values
    elif color_data is not None:
        c = np.asarray(color_data)
    else:
        c = None

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
        cbar = fig.colorbar(scatter, ax=ax, shrink=0.7)
        cbar.set_label(
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
        "Proyección 2D de Componentes Principales",
        fontsize=14,
        weight="bold",
    )
    ax.grid(True, alpha=0.3)

    # Líneas de referencia en cero
    ax.axhline(0, color="gray", linestyle="-", linewidth=0.5, alpha=0.3)
    ax.axvline(0, color="gray", linestyle="-", linewidth=0.5, alpha=0.3)

    fig.tight_layout()

    if save_path:
        fig.savefig(save_path, dpi=300)

    return fig
