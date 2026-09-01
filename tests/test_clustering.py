import numpy as np
import pytest
from sklearn.cluster import DBSCAN, KMeans

from src.clustering import (
    cluster_summary,
    compute_elbow,
    compute_silhouette_by_k,
    fit_dbscan,
    fit_kmeans,
    find_knee_point,
    k_distance_values,
    silhouette_excluding_noise,
    suggest_eps,
)
from src.preprocessing import preprocessing_pca_pipeline


@pytest.fixture(scope="module")
def X_pca(sample_df):
    df_pca, _, _ = preprocessing_pca_pipeline(sample_df, save_path=None)
    return df_pca.values


class TestElbowAndSilhouette:
    def test_compute_elbow_shape(self, X_pca):
        result = compute_elbow(X_pca, k_range=range(2, 6))
        assert list(result.columns) == ["k", "inertia"]
        assert len(result) == 4
        assert result["inertia"].is_monotonic_decreasing

    def test_compute_silhouette_by_k_shape(self, X_pca):
        result = compute_silhouette_by_k(X_pca, k_range=range(2, 5), sample_size=100)
        assert len(result) == 3
        assert result["silhouette"].between(-1, 1).all()

    def test_find_knee_point_on_synthetic_elbow(self):
        y = np.concatenate([np.linspace(10, 2, 5), np.linspace(2, 1.8, 5)])
        knee = find_knee_point(y)
        assert 3 <= knee <= 6


class TestKMeans:
    def test_fit_kmeans_returns_labels_and_model(self, X_pca):
        labels, model = fit_kmeans(X_pca, n_clusters=3)
        assert isinstance(model, KMeans)
        assert len(labels) == len(X_pca)
        assert len(set(labels)) == 3


class TestDBSCAN:
    def test_k_distance_values_sorted(self, X_pca):
        distances = k_distance_values(X_pca, k=5)
        assert len(distances) == len(X_pca)
        assert np.all(np.diff(distances) >= -1e-9)

    def test_suggest_eps_positive(self, X_pca):
        eps = suggest_eps(X_pca, k=5)
        assert eps > 0

    def test_fit_dbscan_returns_labels_and_model(self, X_pca):
        eps = suggest_eps(X_pca, k=5)
        labels, model = fit_dbscan(X_pca, eps=eps, min_samples=5)
        assert isinstance(model, DBSCAN)
        assert len(labels) == len(X_pca)


class TestSummaryAndComparison:
    def test_cluster_summary_counts_noise_separately(self):
        labels = np.array([0, 0, 1, 1, 1, -1, -1])
        summary = cluster_summary(labels)
        assert summary["n_clusters"] == 2
        assert summary["n_noise"] == 2
        assert summary["cluster_sizes"] == {0: 2, 1: 3}

    def test_cluster_summary_no_noise(self):
        labels = np.array([0, 0, 1, 1])
        summary = cluster_summary(labels)
        assert summary["n_noise"] == 0
        assert summary["noise_pct"] == 0.0

    def test_silhouette_excluding_noise_returns_float(self, X_pca):
        labels, _ = fit_kmeans(X_pca, n_clusters=3)
        score = silhouette_excluding_noise(X_pca, labels, sample_size=100)
        assert score is not None
        assert -1 <= score <= 1

    def test_silhouette_excluding_noise_none_when_all_noise(self, X_pca):
        labels = np.full(len(X_pca), -1)
        assert silhouette_excluding_noise(X_pca, labels) is None
