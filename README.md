# Anexo Risk

Plataforma geoespacial de apoyo a la decisión para centros y organismos de coordinación de emergencias.

## Origen

Este repositorio es una evolución de un MVP académico desarrollado colaborativamente por el equipo Nexo (Dana de Valencia — Universitat Politècnica de València, 2024-2025).

El historial Git completo conserva la atribución de todos los contribuidores originales. Ver [AUTHORS.md](AUTHORS.md) para más detalles.

## Evolución 2.x

Esta versión representa una evolución técnica y funcional centrada en apoyo a la decisión mediante:

- **GeoData Engine**: integración de fuentes geoespaciales reales (USGS, IBTrACS, Smithsonian, Copernicus/EFFIS)
- **Análisis geoespacial**: indexación H3, distancia haversine, búsqueda de cercanía
- **Exposición**: cálculo de población e infraestructura expuesta
- **Risk Engine**: scoring determinista con metodología versionada y trazable
- **ML Pipeline**: GradientBoostingClassifier con feature engineering y explicabilidad
- **Decision Center**: contexto unificado que integra situación, exposición, riesgo y operación
- **Organizaciones y Recursos**: gestión con autenticación
- **Necesidades extendidas**: campos adicionales y asignación de recursos

## Arquitectura

```
Frontend          Vanilla JS + ES Modules + Leaflet + PWA
Backend           Python + FastAPI + Pydantic
Persistencia      SQLite (idempotent migrations)
Análisis          NumPy, pandas, GeoPandas, H3, scikit-learn
Fuentes externas  GDACS, NASA FIRMS, AEMET, Open-Meteo,
                  USGS, IBTrACS, Smithsonian, Copernicus/EFFIS
```

## Fuentes de datos

| Fuente | Tipo | Estado |
|--------|------|--------|
| GDACS | Alertas globales | Integrado |
| NASA FIRMS | Detección satelital de incendios | Integrado |
| AEMET | Meteorología oficial España | Integrado (fallback a Open-Meteo) |
| Open-Meteo | Meteorología global | Integrado |
| USGS | Terremotos | Integrado |
| IBTrACS | Ciclones tropicales | Integrado |
| Smithsonian/GVP | Volcanes | Integrado |
| Copernicus/EFFIS | Peligro de incendio forestal | Integrado (WMS) |

## Instalación

```bash
# Clonar
git clone <url>
cd Anexo_Risk

# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate     # Windows
pip install -r requirements.txt

# Configurar entorno
copy .env.example .env
# Editar .env con tus API keys y generar JWT_SECRET_KEY

# Iniciar
python -m uvicorn main:app --reload
```

## API Principal

| Endpoint | Descripción |
|----------|-------------|
| `GET /api/alertas` | Alertas de GDACS + manuales |
| `GET /api/necesidades` | Necesidades abiertas |
| `GET /api/donaciones` | Donaciones/ayudas |
| `GET /api/incendios` | Incendios NASA FIRMS |
| `GET /api/clima` | Meteorología |
| `GET /api/geodata/earthquakes` | Terremotos USGS |
| `GET /api/geodata/cyclones` | Ciclones IBTrACS |
| `GET /api/geodata/volcanoes` | Volcanes Smithsonian |
| `GET /api/geodata/effis` | Peligro incendio EFFIS |
| `GET /api/geodata/exposure` | Cálculo de exposición |
| `GET /api/geodata/risk` | Risk score |
| `GET /api/decision/context` | Contexto de decisión |
| `GET /api/decision/explain` | Explicación de prioridad |
| `GET/POST /api/organizations` | Organizaciones |
| `GET/POST /api/resources` | Recursos |

## Modelos de riesgo

El Risk Engine utiliza scoring determinista con 6 factores ponderados:

- Severidad del evento (30%)
- Exposición calculada (25%)
- Condiciones meteorológicas (15%)
- Densidad de eventos cercanos (15%)
- Necesidades abiertas en la zona (10%)
- Tendencia temporal (5%)

Cada evaluación incluye `methodology_version`, `generated_at` y desglose de factores para trazabilidad.

## Limitaciones conocidas

- **ML**: el target actual está generado por reglas deterministas, no por observaciones reales. El modelo aprende el scoring etiquetado, no predicciones validadas.
- **SQLite**: adecuado para desarrollo y demos, no para producción con alto concurrencia.
- **Copernicus/EFFIS**: genera URLs WMS pero no valida disponibilidad del servicio.
- **Protección Civil**: stub vacío, no integrado con API real.

## Proyectos relacionados

- **GeoRisk Finder**: laboratorio científico de análisis geoespacial y ML
- **Anexo_Risk**: producto operacional de apoyo a la decisión en emergencias

## Licencia

MIT — Ver [LICENSE](LICENSE)

Nota: licencia provisional para la fase académica. Antes de abrir el proyecto a código abierto, revisar si MIT sigue siendo la opción adecuada.

## Seguridad

Ver [docs/security-repository.md](docs/security-repository.md) para políticas de seguridad del repositorio.
