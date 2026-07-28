# GeoRisk Finder 🌍
> **Plataforma de Inteligencia Geoespacial para la Evaluación de Riesgos Compuestos y Decisiones de Inversión en Resiliencia Climática**

![GeoRisk Finder Banner](streamlit_app/assets/banner_georisk.png)

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=flat&logo=python)
![Scikit-Learn](https://img.shields.io/badge/Machine_Learning-Scikit--Learn-F7931E?style=flat&logo=scikit-learn)
![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-FF4B4B?style=flat&logo=streamlit)
![Uber H3](https://img.shields.io/badge/Spatial_Grid-Uber_H3-black.svg?style=flat)
![Licencia](https://img.shields.io/badge/License-Academic_/_Open-green.svg)

---

## 📌 Resumen Ejecutivo

Las catástrofes naturales generan pérdidas globales superiores a los **$300.000 millones anuales**. Los modelos tradicionales suelen evaluar los riesgos (terremotos, huracanes, erupciones) de forma aislada, ignorando las **zonas de riesgo compuesto** donde múltiples amenazas coinciden en el tiempo y espacio.

**GeoRisk Finder** utiliza aprendizaje no supervisado (*Clustering*) sobre una cuadrícula hexagonal espacial (**Uber H3**) para procesar más de **130 millones de eventos históricos**. El sistema categoriza automáticamente cualquier celda del planeta en perfiles de riesgo y evalúa el **Retorno de Inversión (ROI)** de implementar Sistemas de Alerta Temprana (EWS) frente al coste de reconstrucción.

---

## 💼 Casos de Uso e Impacto de Negocio

* 🏢 **Sector Asegurador y Reaseguro:** Optimización de primas y modelado de riesgo multinivel en carteras de activos expuestos.
* 🏛️ **Organismos Internacionales (UNDRR, Banco Mundial):** Priorización de fondos de adaptación climática en regiones de alta vulnerabilidad financiera.
* 🌐 **Gobiernos y Planificación Urbana:** Identificación de áreas críticas para el despliegue de infraestructura de respuesta rápida y alertas tempranas.

---

## 🌟 Características Clave del Producto

* 🗺️ **Grid Hexagonal Global (Uber H3 Res 3):** Discretización homogénea del planeta en ~12.500 celdas de ~12.300 km² cada una.
* 🌪️ **Integración Multi-Peligro:** Ingesta y normalización en tiempo real de registros USGS (sismos), IBTrACS/NOAA (ciclones) e IGN (catálogo histórico).
* 🤖 **Reducción de Dimensionalidad y Clustering:** Pipeline PCA (85% varianza retenida) + K-Means (4 perfiles macro de riesgo) + DBSCAN (detección de celdas atípicas extremas).
* 📊 **Dashboard de Impacto Financiero (Streamlit):** Módulo interactivo de simulación de escenarios (Conservador, Base, Optimista) con cálculo del Ratio Beneficio-Coste (BCR).
* 🌐 **Demo 3D Interactiva:** Visualizador en globo terraqueo con capas dinámicas de amenaza y buscador de ciudades.

---

## 🏗️ Arquitectura del Sistema

### Flujo de Datos & Ejecución
```text
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                           GEORISK FINDER - END-TO-END PIPELINE                                   │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘

  [ FUENTES EXTERNAS ]          [ INGESTA & LIMPIEZA ]          [ GRID H3 & FEATURES ]         [ ML & CLUSTERING ]         [ PRODUCTO ]
  ───────────────────          ─────────────────────────        ───────────────────────        ─────────────────────        ──────────
  ┌──────────────┐             ┌────────────────────┐           ┌────────────────────┐          ┌─────────────────┐         ┌────────────┐
  │ USGS API     │────────────▶│ src/usgs_          │──────────▶│ src/features/      │─────────▶│ src/prepro-     │────────▶│ streamlit_ │
  │ (Sismos M≥4.5│             │ earthquakes.py     │  raw CSV  │ grid.py            │  grid_   │ cessing.py      │  model  │ app/       │
  │  1900-2026)  │             │ 01_eda_sismos.ipynb│           │ engineering.py     │ features │ 04_preprocesa-  │         │ (Dashboard │
  └──────────────┘             └────────────────────┘           │ 03_grid_y_featu-   │ .csv     │ miento_pca.ipynb│         │ Financiero)│
        │                                                      │ res.ipynb          │          │ src/clustering. │         └────────────┘
        │                                                      └────────────────────┘          │ py              │               │
        │                                                                     │               └─────────────────┘               │
  ┌──────────────┐             ┌────────────────────┐                │                     │               │
  │ IBTrACS      │────────────▶│ 02_eda_ciclones_   │────────────────┘                     │               ▼
  │ (Ciclones    │             │ volcanes.ipynb     │                                  ┌─────────────────┐         ┌────────────┐
  │  1970-2025)  │             │ src/features/      │                                  │ MLflow Tracking │         │ georisk_   │
  └──────────────┘             │ ingestion.py       │                                  │ (Experimentos,  │         │ globe/     │
        │                      └────────────────────┘                                  │  Métricas,      │         │ (Demo 3D   │
        │                                                                               │  Artefactos,    │         │  Interact.)│
  ┌──────────────┐             ┌────────────────────┐           ┌────────────────────┐  │  Model Registry)│         └────────────┘
  │ NOAA/NCEI    │────────────▶│ (Volcanes, IGN)    │──────────▶│ src/h3_aggregator. │◀─┘                 │
  │ (Volcanes    │             │                    │           │ py (merge multi-   │                    │
  │  Históricos) │             └────────────────────┘           │ hazard por H3)   │                    │
  └──────────────┘                                              └────────────────────┘                    │
                                                                                                      ▼
                                                                                             ┌────────────┐
                                                                                             │ outputs/   │
                                                                                             │ figures/   │
                                                                                             │ (PNG, HTML)│
                                                                                             └────────────┘
```

### Estructura de Carpetas
```text
GeoRisk_Finder/
├── data/
│   ├── raw/                      # Datos originales (NO versionar >50MB)
│   │   └── ibtracs_sample.csv
│   └── processed/                # Datasets listos para modelado
│       ├── usgs_earthquakes_clean.csv   # 79M filas
│       ├── ciclones_clean.csv           # 46M filas
│       ├── volcanes_clean.csv           # 7.5K filas
│       ├── espana_clean.csv             # 11M filas (IGN)
│       ├── grid_features.csv            # 4.5M celdas × 15 features
│       ├── cluster_labels.csv           # Etiquetas K-Means + DBSCAN
│       ├── interpretacion_clusters.csv  # Perfil riesgo por cluster
│       └── casos_estudio.csv            # 10 casos validados geo
├── notebooks/                    # 7 notebooks en orden de ejecución
│   ├── 01_eda_sismos.ipynb           → Ingesta/EDA USGS (David)
│   ├── 02_eda_ciclones_volcanes.ipynb → Ingesta/EDA IBTrACS/NOAA/IGN (Vanessa)
│   ├── 03_grid_y_features.ipynb      → Grid H3 + Feature Engineering (Joel/Juan)
│   ├── 04_preprocesamiento_pca.ipynb → Pipeline Preproc + PCA + joblib (Juan/Anas)
│   ├── 05_modelado_clustering.ipynb  → K-Means + DBSCAN (María Isabel/Anas)
│   ├── 06_evaluacion_estabilidad.ipynb → Bootstrap stability (Anas/Joel)
│   └── 07_interpretacion_casos_estudio.ipynb → Labels semánticos + casos (María Isabel)
├── src/                          # Código reutilizable (importado desde notebooks)
│   ├── config.py                 # Config central (schema, PCA, H3)
│   ├── data_loader.py            # Carga unificada + fallback sintético
│   ├── usgs_earthquakes.py       # Ingesta completa USGS (API, yearly, dedup)
│   ├── h3_aggregator.py          # Merge multi-hazard por H3 genérico
│   ├── features/
│   │   ├── grid.py               # Grid global H3 res=3 + asignación eventos→celdas
│   │   ├── engineering.py        # Features sísmicas/ciclónicas/volcánicas por celda
│   │   └── ingestion.py          # Carga fuentes externas normalizadas
│   ├── preprocessing.py          # Pipeline sklearn: Log1p → OneHot → Scaler → PCA
│   ├── clustering.py             # K-Means (elbow/silhouette) + DBSCAN (k-dist)
│   └── visualization.py          # Gráficos pro: Matplotlib/Plotly/Folium
├── streamlit_app/                # Dashboard financiero (7 páginas)
│   ├── app.py
│   ├── requirements.txt
│   └── assets/
│       ├── Modelo_Catastrofes_Alerta_Temprana.xlsx  # 6 hojas modelo financiero
│       ├── Resumen_Ejecutivo_Catastrofes_EWS.pdf
│       ├── Analisis_Sesgos_Modelo_Catastrofes.pdf
│       └── banner_georisk.png
├── georisk_globe/                # Demo 3D interactiva (Duo A - 2ª mitad)
│   ├── message_sender/
│   └── layer_panel/
├── outputs/figures/              # Gráficos exportados para presentación
├── tests/                        # Pytest suite (data, preproc, clustering, viz)
└── requirements.txt
```

### MLflow Tracking
```bash
# Iniciar servidor MLflow (opcional, para tracking de experimentos)
mlflow ui --backend-store-uri sqlite:///mlflow.db --default-artifact-root ./mlruns

# Los notebooks 04, 05, 06 logean automáticamente:
#   - Parámetros (K, eps, n_components, threshold varianza)
#   - Métricas (inertia, silhouette, Jaccard bootstrap, ARI)
#   - Artefactos (pipeline_riesgo.joblib, figuras PCA, cluster maps)
#   - Modelos registrados (KMeans, DBSCAN, Pipeline completo)
```

* El **12% de las celdas globales** analizadas concentran el **70% del impacto financiero acumulado** por catástrofes.
* **Clusters de Riesgo Compuesto:** Se identificaron 4 perfiles claros de riesgo, destacando zonas críticas donde la recurrencia ciclónica amplifica el daño sísmico latente.
* **Detección de Anomalías (DBSCAN):** El algoritmo identificó como "ruido estructural" a regiones costeras insulares de baja frecuencia pero intensidad volcánica/ciclónica extrema (alto valor para reaseguradoras).
* **Eficiencia en Alerta Temprana:** Los modelos simulados demuestran que por cada **$1 invertido** en sistemas de prevención en zonas de *Cluster Alto Riesgo*, se evitan hasta **$6 en pérdidas** post-desastre (BCR 6:1).

---

## ⚙️ Estructura del Repositorio

```
GeoRisk_Finder/
├── data/                         # Datasets procesados y muestras de trabajo
├── notebooks/                    # Pipeline analítico ordenado (01 EDA → 07 Casos Estudio)
├── src/                          # Código modular reutilizable (Ingesta, H3, PCA, Clustering)
├── streamlit_app/                # App de análisis financiero y simulación de escenarios
├── georisk_globe/                # Visualizador interactivo 3D del globo
├── outputs/figures/              # Gráficos y mapas exportados
├── tests/                        # Suite de pruebas unitarias (Pytest)
└── requirements.txt              # Dependencias del proyecto
```

---

## 🚀 Guía Rápida de Inicio

### 1. Clonar el repositorio e instalar dependencias
```bash
git clone https://github.com/jowel2701/GeoRisk_Finder.git
cd GeoRisk_Finder

python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Ejecutar el Dashboard de Negocio (Streamlit)
```bash
cd streamlit_app
streamlit run app.py
```

### 3. Ejecutar los Tests
```bash
pytest tests/ -v
```

---

## 👥 Créditos del Proyecto

Proyecto desarrollado por un equipo multidisciplinar de Data Science & BI:

| Miembro | Rol |
|---------|-----|
| **María Isabel** | Product Owner & Business Impact |
| **Joel** | Scrum Master & Spatial Engineering (H3) |
| **David** | Seismic Hazard Lead & ML Engineering |
| **Vanessa** | Atmospheric Hazards Lead & 3D Globe Demo |
| **Juan** | Data Pipeline Architect & Preprocessing Lead |
| **Anas** | Clustering & Model Stability Lead |

---

## 📄 Licencia y Fuentes de Datos

**Licencia:** Uso académico y de demostración.

**Fuentes de datos:**
- **USGS** (United States Geological Survey) — Catálogo sísmico global
- **IBTrACS / NOAA** — Trayectorias ciclónicas históricas
- **IGN** (Instituto Geográfico Nacional de España) — Catálogo sísmico regional
- **NOAA/NCEI** — Base de datos de erupciones volcánicas significativas
- **Aon, Swiss Re, EM-DAT, WMO/UNDRR, World Bank** — Datos financieros y macroeconómicos para el modelo de impacto