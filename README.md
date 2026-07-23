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



# 🗺️ GeoRisk Finder — Data Pipelines & Notebooks

## 1. `01_eda_terremotos.ipynb` — Global Seismic Data & USGS Ingestion
**Author:** David Rojas (Persona 1)



## 2. `02_eda_ciclones_volcanes.ipynb` — Global Cyclones, Volcanic Activity & Regional IGN Monitoring

**Author:** [Vanessa / Persona 2]  
**Focus:** Ingestion, cleaning, EDA, and schema standardization for global atmospheric hazards, volcanic activity, and regional seismic monitoring in Spain and the Canary Islands.

---

### 📥 Data Sources & Ingestion

* **Global Cyclones:** **IBTrACS** (International Best Track Archive for Climate Stewardship - NOAA).
  * A local copy (`ibtracs_all_list_v04r01.csv`) is used instead of direct URL ingestion to improve reproducibility, avoid repeated external downloads, and guarantee consistent preprocessing.

* **Global Volcanoes:** **NOAA / NCEI Significant Volcanic Eruptions Database**.
  * Historical significant volcanic events were ingested and reduced to the spatial attributes required for risk modelling.

* **Regional Seismic Activity (Spain & Canary Islands):** **IGN (Instituto Geográfico Nacional de España)**.
  * The original USGS regional query was replaced by the official IGN historical earthquake catalogue (`ign_earthquakes_1900_present.csv`) to provide higher-resolution local coverage and avoid dependency on external API queries.

---

### ⚙️ Pipeline & Key Processing Steps

#### 1. Source Integration

Three hazard-related datasets were integrated:

* Historical global cyclone tracks from IBTrACS.
* Significant historical volcanic events from NOAA/NCEI.
* Regional seismic events from the IGN catalogue.

The regional seismic source was migrated from generic global earthquake queries to the official IGN catalogue to improve spatial resolution and avoid duplicated requests.

---

#### 2. Schema Standardization

All datasets were standardized around common spatial and temporal attributes required for future spatial aggregation:

* `lat` — latitude
* `lon` — longitude
* `timestamp` — event datetime

Additional hazard-specific variables were preserved:

* Cyclones:
  * `wind`
  * `pressure`

* Volcanoes:
  * `elevation`
  * `country`

* IGN seismic catalogue:
  * `depth_km`
  * `magnitude`
  * `mag_type`

---

#### 3. Data Cleaning & Quality Assessment

The notebook includes:

* Data type normalization.
* Missing value assessment.
* Temporal validation.
* Distribution analysis of hazard intensity variables.

##### IGN Coordinate Normalization

Historical IGN records required additional preprocessing before spatial indexing.

Some historical records contained scaled latitude and longitude values (especially Canary Islands events). Coordinates were normalized before applying spatial analysis to ensure valid geographic positioning.

After cleaning:

* **96,076 seismic events retained**
* Temporal coverage:
  * **1900-02-16 → 2026-07-22**

Missing magnitude values (~1.16%) were preserved because the events still contain valid spatial and temporal information required for H3-based hazard density calculations.

---

### 📊 Exploratory Data Analysis (EDA)

Generated distributions for:

* Cyclone wind intensity.
* Earthquake magnitude distribution for Spain and Canary Islands.
   
 ### 💾 Processed Outputs

Clean datasets generated and saved in:

data/processed/

Files:

ciclones_clean.csv
volcanes_clean.csv
espana_clean.csv
   
   Static visualizations exported:

   * `outputs/figures/distribucion_eventos.png`

   