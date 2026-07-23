import matplotlib

matplotlib.use("Agg")

import numpy as np
import pandas as pd
import pytest
from sklearn.decomposition import PCA

from src.visualization import (
    plot_cumulative_variance,
    plot_pca_2d,
    plot_biplot,
    plot_loadings_heatmap,
    plot_pairplot_pca,
    plot_pca_interactive,
)


@pytest.fixture(scope="module")
def pca_model_and_data():
    np.random.seed(42)
    n = 100
    X = np.random.randn(n, 6)
    pca = PCA(random_state=42)
    X_pca = pca.fit_transform(X)
    df_pca = pd.DataFrame(X_pca[:, :3], columns=["PC1", "PC2", "PC3"])
    return pca, df_pca, [f"feat_{i}" for i in range(6)]


class TestVisualizationSmoke:
    def test_cumulative_variance_runs(self, pca_model_and_data, tmp_path):
        pca, _, _ = pca_model_and_data
        fig = plot_cumulative_variance(pca, save_path=str(tmp_path / "var.png"))
        import matplotlib.figure

        assert isinstance(fig, matplotlib.figure.Figure)

    def test_pca_2d_runs(self, pca_model_and_data, tmp_path):
        _, df_pca, _ = pca_model_and_data
        fig = plot_pca_2d(df_pca, save_path=str(tmp_path / "pca2d.png"))
        import matplotlib.figure

        assert isinstance(fig, matplotlib.figure.Figure)

    def test_biplot_runs(self, pca_model_and_data, tmp_path):
        pca, df_pca, feat_names = pca_model_and_data
        fig = plot_biplot(
            df_pca, pca, feat_names, save_path=str(tmp_path / "biplot.png")
        )
        import matplotlib.figure

        assert isinstance(fig, matplotlib.figure.Figure)

    def test_loadings_heatmap_runs(self, pca_model_and_data, tmp_path):
        pca, _, feat_names = pca_model_and_data
        fig = plot_loadings_heatmap(
            pca, feat_names, n_components=3, save_path=str(tmp_path / "loadings.png")
        )
        import matplotlib.figure

        assert isinstance(fig, matplotlib.figure.Figure)

    def test_pairplot_runs(self, pca_model_and_data, tmp_path):
        _, df_pca, _ = pca_model_and_data
        g = plot_pairplot_pca(
            df_pca, n_components=3, save_path=str(tmp_path / "pairplot.png")
        )
        import seaborn

        assert isinstance(g, seaborn.PairGrid)

    def test_interactive_returns_path(self, pca_model_and_data, tmp_path):
        pca, df_pca, _ = pca_model_and_data
        path = plot_pca_interactive(
            df_pca, pca_model=pca, save_path=str(tmp_path / "interactive.html")
        )
        assert path.endswith(".html")
