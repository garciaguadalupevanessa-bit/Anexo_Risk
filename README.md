# GeoRisk Finder 🌍
Descubrimiento no supervisado de perfiles de riesgo de catástrofes naturales (sismos, ciclones, volcanes) mediante clustering geoespacial.

## Estructura del repo

- `data/raw/` — datos originales sin tocar, tal cual se descargan de cada fuente (NO subir a git si pesan mucho, ver .gitignore)
- `data/processed/` — dataset final "celda x features" listo para modelado
- `notebooks/` — un notebook por bloque de trabajo (ver más abajo)
- `src/` — funciones reutilizables importadas desde los notebooks
- `demo/` — app de la demo interactiva (visualización 3D)
- `outputs/figures/` — gráficas exportadas para la presentación

## Notebooks (orden de ejecución)

1. `01_eda_sismos.ipynb`
2. `02_eda_ciclones_volcanes.ipynb`
3. `03_grid_y_features.ipynb`
4. `04_preprocesamiento_pca.ipynb`
5. `05_modelado_kmeans_dbscan.ipynb`
6. `06_evaluacion_estabilidad.ipynb`
7. `07_interpretacion_casos_estudio.ipynb`

## Instalación
```bash
pip install -r requirements.txt
```

## Demo
Ver `demo/README.md`
