# Auditoría de Integración: Anexo_Risk × GeoRisk Finder

**Fecha:** 2026-09-07  
**Rama:** `feat/v2-mejoras`  
**Commit base:** `7479f97`

---

## 1. Resumen Ejecutivo

| Aspecto | Anexo_Risk | GeoRisk Finder |
|---|---|---|
| **Stack** | FastAPI + SQLite + Vanilla JS + Leaflet | Python + pandas + scikit-learn |
| **Enfoque** | API en tiempo real + SPA | Análisis batch (offline) |
| **Fuentes** | GDACS, FIRMS, AEMET, Open-Meteo | USGS, IBTrACS, Smithsonian, IGN |
| **Tests** | 460 passing | 12 passing |
| **Estado** | Producción funcional | Prototipo académico |

---

## 2. Matriz de Integración

| Componente GeoRisk | Reutilizar | Adaptar | No reutilizar | Motivo |
|---|---|---|---|---|
| `src/config.py` (PREPROCESSING_CONFIG) | | ✅ | | Patrón reutilizable, pero las columnas son placeholders None |
| `src/preprocessing.py` (pipeline completo) | ✅ | | | Funciones genéricas: skew detection, log1p, dummies, PCA |
| `src/visualization.py` (plot_varianza, plot_pca_2d) | ✅ | | | Funciones genéricas de matplotlib |
| `tests/conftest.py` (fixtures sintéticos) | | ✅ | | Patrón reutilizable, distribuciones a adaptar |
| `tests/test_preprocessing.py` (12 tests) | ✅ | | | Tests unitarios del pipeline |
| `notebooks/03_*` (ingesta USGS) | | ✅ | | API real, pero solo en notebook |
| `notebooks/03_*` (ingesta IBTrACS) | | ✅ | | API real, chunked read |
| `notebooks/03_*` (ingesta Smithsonian) | | ✅ | | WFS request pattern |
| `notebooks/03_*` (filtro IGN bbox) | | | ✅ | Naive: solo bounding box, no API real |
| H3 grid | | ✅ | | No implementado en GeoRisk, solo planeado |
| Clustering (KMeans, DBSCAN) | | ✅ | | No implementado, solo planeado |
| React 19 / Zustand / deck.gl | | | ✅ | No existe en GeoRisk actual |
| Auth demo / secretos hardcodeados | | | ✅ | No copiar deuda técnica |
| Datos financieros sintéticos | | | ✅ | No aplica |
| WebSocket stub | | | ✅ | No existe implementado |

---

## 3. Fuentes de Datos Disponibles

### Actuales en Anexo_Risk:
| Fuente | Estado | Endpoint |
|---|---|---|
| GDACS | ✅ Integrado | `integrations/gdacs_client.py` |
| NASA FIRMS | ✅ Integrado | `modules/incendios/models.py` |
| AEMET | ✅ Integrado (fallback Open-Meteo) | `modules/clima/models.py` |
| Open-Meteo | ✅ Integrado (fallback) | `modules/clima/models.py` |
| Protección Civil | ⚠️ Mock | `integrations/proteccion_civil_client.py` |

### Nuevas desde GeoRisk Finder:
| Fuente | Estado | Implementación necesaria |
|---|---|---|
| USGS Earthquakes | 🆕 Nuevo | Adapter CSV feed |
| IBTrACS Cyclones | 🆕 Nuevo | Adapter chunked CSV |
| Smithsonian Volcanoes | 🆕 Nuevo | Adapter WFS |
| Copernicus EFFIS | 🆕 Nuevo | API investigation needed |
| Copernicus Exposure | 🆕 Nuevo | API investigation needed |

---

## 4. Decisiones de Arquitectura

### 4.1 No fusionar repositorios
GeoRisk Finder se mantiene como proyecto separado. Solo se extraen:
- Patrones de preprocessing
- Fuentes de datos (adaptadas a adapters)
- Conceptos de visualización

### 4.2 Nuevo módulo `geodata/`
```
backend/
  geodata/
    __init__.py
    models.py          # Tablas spatial_features, risk_scores, model_versions
    adapters/
      __init__.py
      usgs_adapter.py
      ibtracs_adapter.py
      smithsonian_adapter.py
      copernicus_adapter.py
    services/
      __init__.py
      spatial.py        # GeoPandas spatial joins
      exposure.py       # Cálculo de exposición
      risk_engine.py    # Risk scoring determinista
    routes.py           # Endpoints /api/geodata/*
```

### 4.3 Dependencias nuevas (requirements.txt)
```
geopandas>=0.14.0
shapely>=2.0.0
h3>=4.0.0
scikit-learn>=1.3.0
```

### 4.4 Migraciones nuevas
- `009_organizations.sql` — Organizaciones y usuarios operacionales
- `010_resources.sql` — Recursos
- `011_needs_extended.sql` — Necesidades extendidas
- `012_geodata.sql` — Tablas geoespaciales
- `013_risk_engine.sql` — Risk scores y modelos

---

## 5. Plan de Implementación

| Fase | Descripción | Estado |
|---|---|---|
| **A** | Auditoría de integración | ✅ Completada |
| **B** | Modelo de producto (organizations, roles, resources, needs) | 🔄 En progreso |
| **C** | GeoData Engine + GeoPandas + H3 | ⏳ Pendiente |
| **D** | USGS + volcanes + ciclones adapters | ⏳ Pendiente |
| **E** | Copernicus (EFFIS vertical slice) | ⏳ Pendiente |
| **F** | Exposure + Impact Assessment | ⏳ Pendiente |
| **G** | Risk Engine determinista y explicable | ⏳ Pendiente |
| **H** | Dataset histórico + ML real | ⏳ Pendiente |
| **I** | Decision Center | ⏳ Pendiente |
| **J** | Offline/PWA + sync | ⏳ Pendiente |
| **K** | Asistente IA con tools | ⏳ Pendiente |
| **L** | Hardening, tests, documentación y demo | ⏳ Pendiente |

---

## 6. Criterios de No Regresión

- [ ] Todos los 460 tests actuales siguen pasando
- [ ] Ningún endpoint existente roto
- [ ] Seguridad mantenida (escapeHtml, path traversal, auth)
- [ ] Frontend Vanilla JS sin React
- [ ] Sin dependencias innecesarias
- [ ] Sin datos sintéticos presentados como reales
