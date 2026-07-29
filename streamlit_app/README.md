# GeoRisk Finder — App Unificada

Dashboard multi-página en Streamlit que integra el modelo financiero de catástrofes vs alerta temprana, el mapa de riesgo global 3D, el simulador asegurador y el índice de priorización humanitaria.

## Estructura

```
streamlit_app/
├── main.py                  # Entry point (st.navigation)
├── pages/
│   ├── modelo_financiero.py # Dashboard financiero EWS
│   ├── mapa_global.py       # Mapa de riesgo global 3D
│   ├── panel_aseguradora.py # Simulador de prima relativa
│   └── ayuda_humanitaria.py # Priorización ayuda humanitaria
├── theme.py                 # Sistema de diseño compartido (paleta Nexus teal)
├── data_utils.py            # Utilidades de carga de datos con fallback sintético
├── requirements.txt         # Dependencias Python
└── assets/
    ├── Modelo_Catastrofes_Alerta_Temprana.xlsx   # Modelo financiero (6 hojas)
    ├── Resumen_Ejecutivo_Catastrofes_EWS.pdf      # PDF resumen ejecutivo
    ├── Analisis_Sesgos_Modelo_Catastrofes.pdf      # PDF análisis de sesgos
    ├── infografia_completa.png                     # Infografía principal
    ├── infografia_sesgos.png                       # Infografía de sesgos
    ├── chart_escenarios.png                        # Gráfico comparativo
    ├── logo_georisk.png                            # Logo del proyecto
    └── favicon.png                                 # Favicon
```

## Instalación

```bash
# 1. Ir a la raíz del proyecto
cd GeoRisk_Finder/

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar la app unificada
streamlit run streamlit_app/main.py
```

## Páginas del Dashboard

| Página | Descripción |
|--------|-------------|
| **Mapa global de riesgo** | Visualización 3D de clusters K-Means/DBSCAN sobre grid H3, incidentes GDACS en vivo, modo satélite |
| **Modelo financiero EWS** | KPIs globales, BCR por región, escenarios (Conservador/Base/Optimista), proyecciones 10 años, análisis de sesgos |
| **Panel aseguradora** | Simulador de prima relativa por zona geográfica basado en perfiles de riesgo del grid |
| **Ayuda humanitaria** | Índice compuesto de prioridad por país (severidad + vulnerabilidad + población) |

## Datos Base

- **Aon** — Climate and Catastrophe Insight 2026
- **Swiss Re Institute** — Pérdidas aseguradas por región
- **EM-DAT / CRED** — Base de datos internacional de desastres
- **WMO / UNDRR** — ROI de EWS, initiative EW4All
- **McKinsey / HBS** — BCR de adaptación climática
- **World Bank** — PIB por país/región

## Personalización

- Los colores siguen la paleta Nexus (teal `#01696F`) definida en `theme.py`.
- Los datos financieros se cargan desde `Modelo_Catastrofes_Alerta_Temprana.xlsx`; edita las hojas **Supuestos** o **Escenarios** para cambiar las proyecciones.
- Los datos del grid (clusters, features) se cargan desde `data/processed/` con fallback a datos sintéticos si los CSVs no existen.
