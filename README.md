<p align="center">
  <img src="docs/logo_anexo_risk.png" alt="Anexo Risk" width="320" />
</p>

<h1 align="center">Anexo Risk</h1>

<p align="center">
  <strong>Plataforma de Inteligencia Geoespacial para Respuesta a Emergencias</strong><br/>
  <sub>Centro de Operaciones en Tiempo Real — Mapa · Alertas · Necesidades · Ayudas</sub>
</p>

<p align="center">
  <a href="#-visión-del-negocio">Negocio</a> ·
  <a href="#-arquitectura-técnica">Arquitectura</a> ·
  <a href="#-módulos">Módulos</a> ·
  <a href="#-inicio-rápido">Setup</a> ·
  <a href="#-equipo">Equipo</a> ·
  <a href="#-roadmap">Roadmap</a>
</p>

---

## 🎯 Visión del Negocio

**Anexo Risk** nace de la necesidad real de coordinator la respuesta ante emergencias a nivel comunitario. Ante un desastre natural — inundación, terremoto, incendio — existe un caos informativo: la gente no sabe qué necesita su comunidad, los voluntarios no saben dónde acudir, y los recursos se distribuyen de forma desordenada.

**Anexo Risk resuelve esto** ofreciendo un **centro de operaciones en tiempo real** donde convergen:

- **Alertas oficiales** de fuentes globales (GDACS) con nivel de riesgo y geolocalización
- **Necesidades reales** reportadas por la ciudadanía en 8 categorías (agua, alimentos, medicamentos, etc.)
- **Ayudas y voluntariado** publicados por quienes pueden ofrecer recursos, servicios o tiempo
- **Mapa interactivo** que visualiza todo en capas — alertas, zonas de alto riesgo, necesidades y ofertas de ayuda

> **Modelo de negocio:** Plataforma open-source orientada a ONGs, protecciones civiles y gobiernos locales. Monetización futura via hosting gestionado, módulos premium (analytics predictivos, integración con satélites) y consultoría de implementación.

### Propuesta de Valor

| Problema actual | Solución Anexo Risk |
|---|---|
| Información dispersa en WhatsApp, radio, tv | Dashboard centralizado en tiempo real |
| No se sabe qué necesita cada zona | Mapa con necesidades geolocalizadas por categoría |
| Voluntarios sin dirección clara | Ofertas de ayuda visibles y filtrables |
| Decisiones reactivas | Alertas globales con nivel de severidad |
| Sin trazabilidad de recursos | States tracking: reportada → cubierta |

---

## 🏗 Arquitectura Técnica

```
Anexo_Risk/
├── backend/                    # API REST — FastAPI + SQLite
│   ├── main.py                 # Entry point, CORS, routers
│   ├── config.py               # Environment config
│   ├── modules/
│   │   ├── alertas/            # G2 — Alertas oficiales (GDACS)
│   │   ├── necesidades/        # G1 — Necesidades ciudadanas
│   │   ├── donaciones/         # G3 — Ayudas y voluntariado
│   │   ├── personas/           # Registro de personas
│   │   └── voluntariado/       # Voluntariado
│   ├── db/
│   │   ├── database.py         # SQLite init + migrations
│   │   ├── seed.py             # Datos de prueba
│   │   └── migrations/         # SQL idempotentes
│   └── integrations/           # Clientes externos (GDACS)
├── frontend/                   # PWA — Vanilla JS, ES Modules
│   ├── index.html              # SPA unificada
│   ├── css/
│   │   ├── variables.css       # Design system (dark glassmorphism)
│   │   └── style.css           # Estilos globales
│   ├── js/
│   │   ├── spa.js              # Entry point — integra todos los módulos
│   │   ├── core/
│   │   │   ├── mapa-necesidades/   # G4 — Mapa + necesidades
│   │   │   ├── alertas-oficiales/  # G2 — Alertas GDACS
│   │   │   └── voluntariado-donaciones/  # G3 — Donaciones
│   │   └── shared/             # API client, utils, componentes
│   └── mocks/                  # Datos de prueba para frontend
├── src/                        # Pipeline GeoRisk (H3, clustering)
├── data/                       # Datasets procesados
├── docs/                       # Documentación del proyecto
│   ├── backlog.md              # Backlog del producto
│   ├── SPRINT.md               # Tracking de sprints
│   ├── ARCHITECTURE.md         # ADRs y decisiones técnicas
│   └── ...
└── api/                        # Serverless FastAPI (Vercel)
```

### Stack

| Capa | Tecnología | Por qué |
|---|---|---|
| Backend | FastAPI + SQLite | Rápido, minimal dependencies, sin infra pesada |
| Frontend | Vanilla JS + Leaflet | Sin framework = despliegue estático, PWA-ready |
| Mapa | Leaflet + CARTO Voyager | Tiles gratuitos, buen rendimiento |
| Alertas | GDACS API | Fuente oficial ONU, cobertura global |
| Geolocalización | Nominatim (OSM) | Gratis, sin API key |
| Deploy | Vercel (API) + CDN (frontend) | Edge global, CI integrado |

---

## 📦 Módulos

### G1 — Necesidades Ciudadanas
Los ciudadanos reportan necesidades en 8 categorías cerradas (agua, alimentos, parafarmacia, ropa, higiene, refugio, transporte, otros). El sistema genera un título automático y permite geolocalizar por GPS, mapa o dirección escrita.

**States:** `abierta` → `cubierta`

### G2 — Alertas Oficiales
Consume la API de GDACS (Global Disaster Alerting Coordination System). Muestra terremotos, inundaciones, ciclones, incendios y volcanes a nivel mundial con niveles de severidad (crítico / atención / bajo riesgo).

**States:** `normal` → `active` → `high_risk` → `deactivated`

### G3 — Ayudas y Voluntariado
Publicación de recursos, servicios y tiempo voluntario. Validación condicional de DNI para voluntariado. Fallback a localStorage si el backend no está disponible.

**Types:** `recursos` · `servicios` · `tiempo`

### G4 — Mapa Interactivo
Centro de mando visual con 6 capas toggleables: alertas, zonas de alto riesgo, necesidades, ayudas, clusters H3 de necesidades y clusters H3 de ayudas. Click-to-select para reportar ubicación.

---

## 🚀 Inicio Rápido

### Requisitos
- Python 3.10+
- pip

### Instalación

```bash
# 1. Clonar
git clone https://github.com/garciaguadalupevanessa-bit/Anexo_Risk.git
cd Anexo_Risk

# 2. Backend
cd backend
pip install -r requirements-dev.txt
python db/seed.py          # Carga datos de prueba
uvicorn main:app --reload --port 8000

# 3. Frontend (otra terminal)
cd frontend
python -m http.server 5500
```

### Uso

Abrir **http://localhost:5500** → Seleccionar sección (MAPA / ALERTAS / DONACIONES)

---

## 👥 Equipo

| Nombre | Rol | Módulo | GitHub |
|---|---|---|---|
| **Juan** | PM / Tech Lead | G4 — Mapa + Interfaz | `@juann` |
| **Javi** | Backend Lead | G2 — Alertas + Activación | `@javi` |
| **Luis** | Frontend Lead | G1 — Necesidades | `@luis` |
| **Vanessa** | Full Stack | G3 — Ayudas + Donaciones | `@vanessa` |

---

## 🗺 Roadmap

### Sprint 1 ✅ (Completado)
- [x] Base común: backend + CORS + apiClient
- [x] Módulo de necesidades (8 categorías, 2 estados)
- [x] Alertas GDACS con filtros y severidad
- [x] Voluntariado y donaciones backend
- [x] Mapa interactivo con Leaflet

### Sprint 2 🔄 (Actual)
- [x] Alertas G2 integradas al SPA
- [x] Donaciones G3 con validación DNI
- [x] Necesidades G1 refactorizadas (Luis)
- [x] SPA unificada (single-page application)
- [x] Design system dark glassmorphism
- [ ] CI/CD pipeline
- [ ] PWA instalable
- [ ] Modo offline

### Sprint 3 📋 (Próximo)
- [ ] Analytics predictivos con H3
- [ ] Integración con protección civil
- [ ] App móvil (React Native)
- [ ] Multi-idioma (i18n)

---

## 📄 Licencia

MIT — Open Source. Ver [LICENSE](LICENSE) para detalles.

---

## 📚 Documentación

| Documento | Descripción |
|---|---|
| [Backlog](docs/backlog.md) | Producto backlog con prioridades |
| [Sprint Tracking](docs/SPRINT.md) | Estado actual de sprints |
| [Architecture Decision Records](docs/ARCHITECTURE.md) | Decisiones técnicas (ADR) |
| [Entity Relationship](docs/modelo-entidad-relacion.md) | Modelo de datos |
| [Team Assignments](docs/equipos.md) | Reparto de trabajo |
| [Conventions](docs/convenciones.md) | Convenciones del proyecto |

---

<details>
<summary><h2>🇬🇧 English Documentation (click to expand)</h2></summary>

### Vision

**Anexo Risk** is a real-time emergency operations platform that consolidates official disaster alerts, community-reported needs, and volunteer/resource offers into a single interactive dashboard.

Born from the NEXO emergency response project and integrated with GeoRisk's geospatial intelligence (H3 hexagonal grid, clustering), it provides decision-makers with a unified operational picture during crises.

**Business Model:** Open-source platform targeting NGOs, civil protection agencies, and local governments. Future monetization through managed hosting, premium analytics modules, and implementation consulting.

### Value Proposition

| Current Problem | Anexo Risk Solution |
|---|---|
| Information scattered across WhatsApp, radio, TV | Centralized real-time dashboard |
| No visibility into zone-specific needs | Geolocalized needs map by category |
| Volunteers lack clear direction | Filterable help/resource offers |
| Reactive decision-making | Global alerts with severity levels |
| No resource tracking | Status tracking: reported → covered |

### Tech Stack

| Layer | Technology | Rationale |
|---|---|---|
| Backend | FastAPI + SQLite | Fast, minimal dependencies |
| Frontend | Vanilla JS + Leaflet | Zero-framework = static deploy, PWA-ready |
| Map | Leaflet + CARTO Voyager | Free tiles, good performance |
| Alerts | GDACS API | Official UN source, global coverage |
| Geocoding | Nominatim (OSM) | Free, no API key required |
| Deploy | Vercel (API) + CDN (frontend) | Global edge, integrated CI |

### Modules

| Module | Code | Description |
|---|---|---|
| **G1 — Needs** | `necesidades/` | Citizens report needs in 8 closed categories. Auto-generated titles, geolocation via GPS/map/address. States: `abierta` → `cubierta` |
| **G2 — Alerts** | `alertas/` | GDACS integration. Earthquakes, floods, cyclones, fires, volcanoes. Severity: critical / attention / low risk |
| **G3 — Donations** | `donaciones/` | Resources, services, and volunteer time. Conditional DNI validation. localStorage fallback |
| **G4 — Map** | `mapa/` | Interactive dashboard with 6 toggleable layers, H3 hexagonal clustering, click-to-report |

### Getting Started

```bash
# Clone
git clone https://github.com/garciaguadalupevanessa-bit/Anexo_Risk.git
cd Anexo_Risk

# Backend
cd backend && pip install -r requirements-dev.txt
python db/seed.py && uvicorn main:app --reload --port 8000

# Frontend
cd frontend && python -m http.server 5500
```

Open **http://localhost:5500**

### Sprint Status

| Sprint | Status | Key Deliverables |
|---|---|---|
| Sprint 1 | ✅ Done | Core backend, G1-G4 modules, GDACS integration |
| Sprint 2 | 🔄 In Progress | SPA unification, design system, CI/CD, PWA |
| Sprint 3 | 📋 Planned | H3 analytics, civil protection integration, mobile app |

### Team

| Name | Role | Module |
|---|---|---|
| Juan | PM / Tech Lead | G4 — Map + Interface |
| Javi | Backend Lead | G2 — Alerts + Activation |
| Luis | Frontend Lead | G1 — Needs |
| Vanessa | Full Stack | G3 — Donations + Aid |

### Further Documentation

- [Product Backlog](docs/backlog.md)
- [Sprint Tracking](docs/SPRINT.md)
- [Architecture Decision Records](docs/ARCHITECTURE.md)
- [Entity Relationship Model](docs/modelo-entidad-relacion.md)
- [Team Assignments](docs/equipos.md)

### License

MIT — Open Source. See [LICENSE](LICENSE) for details.

</details>
