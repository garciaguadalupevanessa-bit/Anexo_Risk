"""
K-Means and DBSCAN clustering for geological risk segmentation.

K-Means gives a clean K-way business segmentation of cells. DBSCAN is run
in parallel over the same feature space to flag cells that don't fit any
dense region — those "noise" points are treated as a signal of atypical,
high-value risk (e.g. a cell with a rare combination of extreme seismic
and cyclonic activity), not as errors to discard.
"""

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN, KMeans
from sklearn.metrics import silhouette_score
from sklearn.neighbors import NearestNeighbors


def compute_elbow(X, k_range=range(2, 16), random_state: int = 42) -> pd.DataFrame:
    rows = []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        km.fit(X)
        rows.append({"k": k, "inertia": km.inertia_})
    return pd.DataFrame(rows)


def compute_silhouette_by_k(
    X,
    k_range=range(2, 16),
    random_state: int = 42,
    sample_size: int | None = 5000,
) -> pd.DataFrame:
    n = np.asarray(X).shape[0]
    effective_sample = min(sample_size, n) if sample_size else None
    rows = []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        labels = km.fit_predict(X)
        score = silhouette_score(
            X, labels, sample_size=effective_sample, random_state=random_state
        )
        rows.append({"k": k, "silhouette": score})
    return pd.DataFrame(rows)


def find_knee_point(y_values) -> int:
    """Index of the point of maximum distance to the chord (start-end line).

    Standard "kneedle" heuristic, works for elbow (inertia vs k) and for
    k-distance curves (DBSCAN eps selection) alike.
    """
    y = np.asarray(y_values, dtype=float)
    x = np.arange(len(y), dtype=float)
    x_norm = (x - x.min()) / (x.max() - x.min() + 1e-12)
    y_norm = (y - y.min()) / (y.max() - y.min() + 1e-12)

    p1 = np.array([x_norm[0], y_norm[0]])
    p2 = np.array([x_norm[-1], y_norm[-1]])
    line_vec = p2 - p1
    line_vec_norm = line_vec / (np.linalg.norm(line_vec) + 1e-12)

    points = np.column_stack([x_norm, y_norm])
    vec_from_first = points - p1
    scalar_proj = vec_from_first @ line_vec_norm
    proj = np.outer(scalar_proj, line_vec_norm)
    dist_to_line = np.linalg.norm(vec_from_first - proj, axis=1)
    return int(np.argmax(dist_to_line))


def fit_kmeans(X, n_clusters: int, random_state: int = 42):
    km = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    labels = km.fit_predict(X)
    return labels, km


def k_distance_values(X, k: int = 5) -> np.ndarray:
    """Sorted distance to each point's k-th nearest neighbor.

    The knee of this curve (ascending) is the standard heuristic for
    picking DBSCAN's `eps` (Ester et al., 1996).
    """
    nn = NearestNeighbors(n_neighbors=k)
    nn.fit(X)
    distances, _ = nn.kneighbors(X)
    return np.sort(distances[:, -1])


def suggest_eps(X, k: int = 5) -> float:
    distances = k_distance_values(X, k=k)
    knee_idx = find_knee_point(distances)
    return float(distances[knee_idx])


def fit_dbscan(X, eps: float, min_samples: int = 5):
    db = DBSCAN(eps=eps, min_samples=min_samples)
    labels = db.fit_predict(X)
    return labels, db


def cluster_summary(labels, noise_label: int = -1) -> dict:
    labels = np.asarray(labels)
    unique, counts = np.unique(labels, return_counts=True)
    sizes = dict(zip(unique.tolist(), counts.tolist()))
    n_noise = sizes.pop(noise_label, 0)
    return {
        "n_clusters": len(sizes),
        "n_noise": int(n_noise),
        "noise_pct": float(n_noise / len(labels) * 100) if len(labels) else 0.0,
        "cluster_sizes": sizes,
    }


def silhouette_excluding_noise(
    X,
    labels,
    noise_label: int = -1,
    sample_size: int | None = 5000,
    random_state: int = 42,
) -> float | None:
    """Silhouette score computed only over non-noise points.

    Returns None when there are fewer than 2 real clusters left after
    dropping noise (silhouette is undefined in that case).
    """
    X = np.asarray(X)
    labels = np.asarray(labels)
    mask = labels != noise_label
    if mask.sum() == 0 or len(np.unique(labels[mask])) < 2:
        return None
    effective_sample = min(sample_size, int(mask.sum())) if sample_size else None
    return silhouette_score(
        X[mask], labels[mask], sample_size=effective_sample, random_state=random_state
    )
