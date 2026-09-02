# Anexo Risk

> **Plataforma de respuesta a emergencias** — coordina alertas oficiales,
> necesidades reportadas por la comunidad y ofertas de ayuda (recursos,
> servicios, voluntariado) en un único panel de operaciones en tiempo real.

`anexo_risk` centraliza lo que hoy está disperso en una emergencia:
las alertas oficiales, lo que necesita la gente, y quién puede ayudar.
Toda la información aparece en un mapa interactivo con filtros por tipo,
severidad y ubicación.

## Funcionalidades actuales

- **Alertas oficiales** (GDACS) — Terremotos, ciclones, inundaciones, incendios, volcanes, sequías.
- **Mapa de necesidades** — Reporte de la comunidad con 8 categorías (agua, alimentos, parafarmacia, ropa, higiene, refugio, transporte, otros).
- **Publicación de ayudas** — Recursos, servicios, tiempo voluntario. Con validación por DNI para voluntariado.
- **Cambio de estado de necesidad** — `abierta → cubierta` con auditoría de transición.
- **PWA + offline banner** — Detección de conexión y cola de sincronización (backend preparado, frontend stub).

## Origen del proyecto

`anexo_risk` parte como un **fork refactorizado** de un proyecto académico
previo ("Nexo") desarrollado por otro equipo durante la Dana de Valencia
2024-2025. El objetivo fue tomar lo que ya funcionaba (modelos de datos,
contratos API validados, suite de tests) y adaptarlo a un nuevo contexto
operativo, con un equipo y stack propios.

### Qué se conserva

- Modelos de datos validados en emergencias reales (necesidades, alertas, donaciones, voluntariado, personas).
- Contratos JSON estables hacia el frontend.
- Suite de tests existente como red de seguridad del refactor.
- Decisiones arquitectónicas probadas (FastAPI + SQLite, migraciones idempotentes, modo offline con cola).

### Qué se descarta / no aplica a este equipo

El repositorio aún contiene artefactos del proyecto anterior que **no
forman parte del alcance de `anexo_risk`** y no se mantienen:

- Directorios `src/`, `notebooks/`, `streamlit_app/`, `app/`, `api/`,
  `scripts/`, `integration/` — prototipos ML / GeoRisk / Vercel del
  equipo anterior. No se ejecutan, no se testean, no se despliegan.
- `frontend/pages/*.html` (donaciones.html, mapa.html, etc.) — versión
  multi-página previa. Reemplazada por la SPA única (`index.html`).
- Documentos legacy en `docs/legacy/`, `estructura/`, `docs/modelo-entidad-relacion.md`,
  `docs/privacidad-datos.md`, `docs/integracion-nexo-georisk.md` — se
  conservan como **trazabilidad histórica**, no como guía de trabajo
  actual.

**Regla:** lo que está activo en `anexo_risk` es lo que está en
`backend/`, `frontend/` (excepto `pages/`), `tests/backend/`,
`tests/frontend/` y los docs listados en la sección *Documentación*.
El resto es referencia histórica.

## Arquitectura

```
anexo_risk/
├── backend/      # FastAPI + SQLite + Pydantic
├── frontend/     # SPA vanilla JS (Leaflet) — una sola index.html
├── docs/         # Arquitectura, sprints, decisiones
├── tests/        # Pytest (backend) + jest (frontend)
├── .github/      # CI/CD
└── vercel.json   # Despliegue serverless (opcional)
```

**Stack real:** Python 3.11+, FastAPI 0.115+, Pydantic 2.9+, SQLite con
migraciones idempotentes, Vanilla JS + ES modules, Leaflet 1.9.4, sin
frameworks, sin React, sin PostgreSQL en esta fase.

## Cómo ejecutar

### Requisitos

- Python 3.11 o superior
- pip

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate    # Linux/macOS
pip install -r requirements.txt
python -c "from db.database import init_db; init_db()"
python -m uvicorn main:app --reload --port 8000
```

### Frontend (otra terminal)

```bash
cd frontend
python -m http.server 5500
```

Abrir `http://localhost:5500` en el navegador.

### Verificación rápida

```bash
curl http://localhost:8000/api/health
# {"status":"ok","app":"Anexo Risk"}
```

## Cómo probar

```bash
cd backend
PYTHONPATH=backend DATABASE_URL=sqlite:///./backend/anexo_risk.db \
  python -m pytest ../tests/backend/ -v
```

## Variables de entorno

Copia `backend/.env.example` a `backend/.env` y ajusta según necesidad:

| Variable | Default | Descripción |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./anexo_risk.db` | Ruta de la base de datos |
| `BACKEND_PORT` | `8000` | Puerto del backend |
| `CORS_ORIGINS` | `http://localhost:5500,...` | Orígenes permitidos |
| `ANEXO_ADMIN_KEY` | `anexo-risk-dev-admin-key` | Clave de organizador (cabecera `X-Anexo-Key`) |
| `EMAIL_DUMMY_MODE` | `true` | Modo dummy (no envía correos reales) |

## Estructura

```
backend/
├── main.py                    # Arranque FastAPI
├── config.py                  # Variables de entorno
├── db/                        # SQLite + migraciones
├── modules/
│   ├── necesidades/           # Núcleo — reporte ciudadano
│   ├── alertas/               # Núcleo — GDACS
│   ├── donaciones/            # Núcleo — recursos y servicios
│   ├── voluntariado/          # Núcleo — red de apoyo
│   └── personas/              # Núcleo — registro y búsqueda
├── middleware/                # CORS, auth, logging, errores
├── sync/                      # Modo offline (backend listo)
└── integrations/              # GDACS, USGS

frontend/
├── index.html                 # SPA única
├── js/spa.js                  # Entry point
├── css/                       # Variables + estilos
├── assets/                    # Logo, iconos
└── mocks/                     # Fallback cuando la API cae
```

## Distribución de tareas (equipo Anexo Risk)

| Persona | Módulo | Alcance |
|---|---|---|
| **Vanessa** | Voluntariado y donaciones | Validación DNI, flujo aprobación, alta/baja |
| **Javi** | Alertas oficiales | GDACS, filtrado por severidad/tipo, cache |
| **Luis** | Necesidades | API, modelos, transiciones de estado |
| **Juan** | Mapa, frontend, integración | SPA, Leaflet, sync offline, CI/CD |

## Roadmap

- **Sprint 1** ✅ — Módulos núcleo, base de datos, contratos API
- **Sprint 2** 🔄 — SPA unificada, refinamiento UX, rebranding completo
- **Post-MVP** 📋 — Migración a PostgreSQL/PostGIS, autenticación,
  integración con Protección Civil en tiempo real, app móvil nativa

## Documentación

Documentos vigentes del proyecto `anexo_risk`:

- `docs/architecture.md` — Decisiones arquitectónicas (ADRs)
- `docs/manifiesto.md` — Misión y criterios de éxito
- `docs/backlog.md` — Estado actual del trabajo
- `docs/sprint.md` — Seguimiento de sprints
- `docs/convenciones.md` — Convenciones de código
- `docs/roadmap.md` — Roadmap por sprints

Documentos históricos del proyecto previo ("Nexo") que se conservan
solo como trazabilidad, **no como guía actual**:

- `docs/legacy/`
- `docs/modelo-entidad-relacion.md`
- `docs/privacidad-datos.md`
- `docs/integracion-nexo-georisk.md`
- `docs/faq.md` (referencias a estructura legacy)
- `estructura/`

---

**Producto:** `anexo_risk` · **Stack:** FastAPI + SQLite + Vanilla JS + Leaflet
**Equipo:** Vanessa, Javi, Luis, Juan · Heredado de: proyecto "Nexo" (Dana Valencia)
