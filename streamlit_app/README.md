# Dashboard Catástrofes vs Alerta Temprana

Dashboard interactivo en Streamlit que presenta el modelo financiero comparativo entre el coste histórico de catástrofes naturales y la inversión en sistemas de alerta temprana (EWS).

## Estructura

```
streamlit_app/
├── app.py                  # App principal (7 páginas)
├── requirements.txt        # Dependencias Python
├── README.md               # Este archivo
└── assets/                 # Documentos generados
    ├── Modelo_Catastrofes_Alerta_Temprana.xlsx   # Modelo financiero (6 hojas)
    ├── Resumen_Ejecutivo_Catastrofes_EWS.pdf      # PDF resumen ejecutivo (4 págs)
    ├── Analisis_Sesgos_Modelo_Catastrofes.pdf      # PDF análisis de sesgos (7 págs)
    ├── infografia_completa.png                     # Infografía principal
    ├── infografia_sesgos.png                       # Infografía de sesgos
    └── chart_escenarios.png                        # Gráfico comparativo de escenarios
```

## Instalación

### Opción A: Entorno local con VS Code

```bash
# 1. Abrir la carpeta en VS Code
code streamlit_app/

# 2. Crear entorno virtual (recomendado)
python -m venv venv
source venv/bin/activate        # Mac/Linux
# venv\Scripts\activate         # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Ejecutar la app
streamlit run app.py
```

### Opción B: Conda

```bash
conda create -n catrostrofes python=3.11
conda activate catrostrofes
pip install -r requirements.txt
streamlit run app.py
```

## Páginas del Dashboard

| Página | Contenido |
|--------|-----------|
| **Resumen Ejecutivo** | KPIs globales, BCR por región, infografía |
| **Modelo Financiero** | Tabla de KPIs por región, gráficos de inversión vs beneficio |
| **Pérdidas Históricas** | Evolución 2021-2025 por región |
| **Proyecciones 10 años** | Flujo neto anual por región, mapa de calor |
| **Comparativa de Escenarios** | Conservador vs Base vs Optimista |
| **Documentación** | PDF resumen ejecutivo embebido + descargas |
| **Análisis de Sesgos** | 6 sesgos críticos, infografía y PDF completo |

## Datos Base

- **Aon** — Climate and Catastrophe Insight 2026
- **Swiss Re Institute** — Pérdidas aseguradas por región
- **EM-DAT / CRED** — Base de datos internacional de desastres
- **WMO / UNDRR** — ROI de EWS, initiative EW4All
- **McKinsey / HBS** — BCR de adaptación climática
- **World Bank** — PIB por país/región

## Personalización

- Para cambiar escenarios, edita la hoja **Supuestos** del Excel.
- Los gráficos usan Plotly (interactivos: zoom, hover, descarga PNG).
- Los colores siguen la paleta Nexus (teal #01696F como acento principal).
