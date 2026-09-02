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

## Arquitectura

```
anexo_risk/
├── backend/      # FastAPI + SQLite + Pydantic
├── frontend/     # SPA vanilla JS (Leaflet) — una sola index.html
├── docs/         # Arquitectura, sprints, decisiones
├── tests/        # Pytest (backend + ML)
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
pip install -r requirements-dev.txt
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
| `ANEXO_ADMIN_KEY` | `anexo-risk-dev-admin-key` | Clave de organizador |
| `EMAIL_DUMMY_MODE` | `true` | Modo dummy (no envía correos reales) |

## Estructura

```
backend/
├── main.py                    # Arranque FastAPI
├── config.py                  # Variables de entorno
├── db/                        # SQLite + migraciones
├── modules/
│   ├── necesidades/           # G1 — núcleo
│   ├── alertas/               # G2 — núcleo
│   ├── donaciones/            # G3 — núcleo
│   ├── voluntariado/          # G3 — núcleo
│   └── personas/              # G4 — siguiente prioridad
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

## Equipo

- **Javi** (G2) — Alertas oficiales
- **Juan** (G4) — Mapa, interfaz, integración
- **Luis** (G1) — Necesidades
- **Vanessa** (G3) — Voluntariado y donaciones

## Roadmap

- **Sprint 1** ✅ — Módulos núcleo, base de datos, contratos API
- **Sprint 2** 🔄 — SPA unificada, rebranding a Anexo Risk, refinamiento UX
- **Post-MVP** 📋 — Migración a PostgreSQL/PostGIS, autenticación, integración
  con Protección Civil en tiempo real, aplicación móvil nativa

## Documentación

- `docs/architecture.md` — Decisiones arquitectónicas (ADRs)
- `docs/manifiesto.md` — Misión y criterios de éxito
- `docs/backlog.md` — Estado actual del trabajo
- `docs/sprint.md` — Seguimiento de sprints
- `docs/convenciones.md` — Convenciones de código

---

**Producto:** `anexo_risk` · **Stack:** FastAPI + SQLite + Vanilla JS + Leaflet
