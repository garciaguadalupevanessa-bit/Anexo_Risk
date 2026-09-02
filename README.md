# Anexo Risk

<p align="center">
  <img src="frontend/assets/logo/anexo-icon.png" alt="Anexo Risk logo" width="180" />
</p>

<p align="center">
  <strong>Plataforma de respuesta a emergencias</strong> que unifica alertas
  oficiales, necesidades de la población y ofertas de ayuda en un único
  panel de operaciones visible para coordinadores, voluntarios y
  ciudadanía.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/status-MVP-success" alt="Status" />
  <img src="https://img.shields.io/badge/stack-FastAPI%20%2B%20SQLite%20%2B%20Vanilla%20JS-blue" alt="Stack" />
  <img src="https://img.shields.io/badge/tests-84%20passing-brightgreen" alt="Tests" />
  <img src="https://img.shields.io/badge/license-Academic-lightgrey" alt="License" />
</p>

---

## Tabla de contenidos

**Producto**
1. [El problema que resolvemos](#1-el-problema-que-resolvemos)
2. [Qué es Anexo Risk](#2-qué-es-anexo-risk)
3. [Para quién](#3-para-quién)
4. [Casos de uso reales](#4-casos-de-uso-reales)
5. [Diferenciadores](#5-diferenciadores)
6. [Cómo se ve](#6-cómo-se-ve)

**Equipo**
7. [Origen del proyecto](#7-origen-del-proyecto)
8. [Equipo actual](#8-equipo-actual)
9. [Mapa de ramas](#9-mapa-de-ramas)

**Técnico**
10. [Stack técnico](#10-stack-técnico)
11. [Arquitectura](#11-arquitectura)
12. [Cómo ejecutarlo](#12-cómo-ejecutarlo)
13. [Cómo probarlo](#13-cómo-probarlo)
14. [Variables de entorno](#14-variables-de-entorno)
15. [Estructura del repositorio](#15-estructura-del-repositorio)
16. [API endpoints](#16-api-endpoints)
17. [Convenciones y docs](#17-convenciones-y-docs)

**Visión**
18. [Próximas implementaciones](#18-próximas-implementaciones)
19. [Licencia y créditos](#19-licencia-y-créditos)

---

# Producto

## 1. El problema que resolvemos

Durante una emergencia (inundación, incendio, terremoto, nevada, ola de
calor) la información crítica vive en canales dispersos:

- Las **alertas oficiales** se publican en webs y redes de Protección
  Civil, difíciles de centralizar.
- Las **necesidades** ("necesito agua en la calle X", "faltan mantas en
  el polideportivo") circulan por WhatsApp, Twitter y boca a boca.
- Las **ofertas de ayuda** ("puedo donar comida", "tengo una furgoneta",
  "me apunto como voluntario") llegan en grupos descoordinados.

El resultado: coordinadores saturados, gente que necesita ayuda sin
saber a quién llamar, y personas dispuestas a ayudar que no encuentran
dónde.

## 2. Qué es Anexo Risk

`anexo_risk` centraliza las tres corrientes de información en un mismo
panel:

| Corriente | Fuente | Estado actual |
|---|---|---|
| **Alertas oficiales** | GDACS (Global Disaster Alert and Coordination System) | ✅ En producción |
| **Necesidades reportadas** | Reporte ciudadano geolocalizado | ✅ En producción |
| **Ofertas de ayuda** | Recursos, servicios, voluntariado | ✅ En producción |
| **Registro de personas** | Marcado como localizada / desaparecida | ✅ En producción |
| **Modo offline** | Cola con sincronización diferida | ✅ Backend listo, frontend en progreso |

Toda la información se muestra en un **mapa interactivo** (Leaflet) con
filtros por tipo, severidad, estado y ubicación. Funciona en modo
**offline** (PWA) para cuando la red está caída o saturada, algo
habitual en emergencias reales.

## 3. Para quién

- **Coordinadores de emergencia** — Triage, priorización, asignación de
  recursos, seguimiento del estado de cada necesidad.
- **Voluntarios** — Publicar disponibilidad y habilidades, ver dónde se
  necesita ayuda ahora mismo.
- **Ciudadanía** — Reportar necesidades, ofrecer recursos, consultar
  alertas oficiales.

## 4. Casos de uso reales

> **Inundación en comarca de Valencia, 2024.**
> Un grupo de vecinos abre `anexo_risk` en su móvil, reporta en 3
> minutos las calles que necesitan agua embotellada. La coordinadora
> del polideportivo ve en su panel todas las necesidades abiertas
> priorizadas por urgencia, marca como cubiertas conforme llegan
> donaciones, y contacta con un voluntario que se acaba de apuntar
> con disponibilidad de furgoneta 4x4. Todo sin una sola llamada
> cruzada.

> **Corte de carretera por nevada.**
> El sistema detecta la alerta de Protección Civil vía GDACS y la
> publica en la portada. Los vecinos usan el mapa para reportar
> tramos sin acceso, y los conductores con cadenas ven en qué punto
> pueden ser útiles.

> **Persona desaparecida.**
> Un familiar abre la app, marca a la persona como desaparecida con
> última ubicación conocida. Los voluntarios reciben la notificación
> en el directorio y pueden actualizar el estado a "localizada"
> cuando se confirma.

## 5. Diferenciadores

| Lo que otros hacen | Lo que Anexo Risk aporta |
|---|---|
| Apps pesadas con login obligatorio | Acceso sin fricción, sólo `X-Anexo-Key` para coordinadores |
| Canales aislados (alertas / necesidades / ofertas por separado) | Un único panel con las tres corrientes en el mismo mapa |
| Apps que dejan de funcionar sin red | PWA con cola offline, sincroniza cuando vuelve la señal |
| Soluciones propietarias caras | Stack abierto (FastAPI + SQLite + Vanilla JS), desplegable en cualquier hosting |
| Datos centralizados en una sola entidad | Datos sensibles quedan en local; sólo alertas se consultan a fuentes públicas |

## 6. Cómo se ve

El usuario abre `index.html` y ve:

- **Banner offline** si no hay conexión.
- **Mapa centrado** en la zona con marcadores por necesidad.
- **Panel lateral** con alertas oficiales filtrables por severidad.
- **Botón flotante** para reportar nueva necesidad o publicar ayuda.
- **Directorio** de voluntarios y recursos disponibles.

---

# Equipo

## 7. Origen del proyecto

`anexo_risk` parte como un **fork refactorizado** de un proyecto
académico previo ("Nexo") desarrollado por otro equipo durante la Dana
de Valencia 2024-2025. El objetivo fue tomar lo que ya funcionaba en
emergencias reales (modelos de datos validados, contratos API probados,
suite de tests como red de seguridad) y adaptarlo a un nuevo contexto
operativo con un equipo y stack propios.

### Qué se conserva

- Modelos de datos validados en emergencias reales (necesidades,
  alertas, donaciones, voluntariado, personas).
- Contratos JSON estables hacia el frontend.
- Suite de tests como red de seguridad del refactor.
- Decisiones arquitectónicas probadas: FastAPI + SQLite, migraciones
  idempotentes, modo offline con cola de sincronización.

### Qué se descarta (no aplica a este equipo)

El repositorio aún contiene artefactos del proyecto anterior que **no
forman parte del alcance de `anexo_risk`** y no se mantienen:

- `src/`, `notebooks/`, `streamlit_app/`, `app/`, `api/`, `scripts/`,
  `integration/` — prototipos ML / GeoRisk / Vercel del equipo
  anterior. No se ejecutan, no se testean, no se despliegan.
- `frontend/pages/*.html` (donaciones.html, mapa.html, etc.) — versión
  multi-página previa. Reemplazada por la SPA única (`index.html`).
- `docs/legacy/`, `estructura/`, `docs/modelo-entidad-relacion.md`,
  `docs/privacidad-datos.md`, `docs/integracion-nexo-georisk.md`,
  `docs/faq.md` — **trazabilidad histórica** únicamente, no son guía de
  trabajo actual.

**Regla:** lo que está activo en `anexo_risk` es lo que vive en
`backend/`, `frontend/` (excepto `pages/`), `tests/backend/`,
`tests/frontend/` y los docs listados en
[Convenciones y docs](#17-convenciones-y-docs). El resto es referencia
histórica.

## 8. Equipo actual

| Persona | Módulo | Alcance |
|---|---|---|
| **Vanessa** | Voluntariado y donaciones | Validación DNI, flujo aprobación, alta/baja |
| **Javi** | Alertas oficiales | GDACS, filtrado por severidad/tipo, cache |
| **Luis** | Necesidades | API, modelos, transiciones de estado |
| **Juan** | Mapa, frontend, integración | SPA, Leaflet, sync offline, CI/CD |

## 9. Mapa de ramas

Auditoría del repositorio remoto a fecha de hoy. Ningún trabajo se
borra: cada persona mantiene su rama propia y todas convergen en
`main`.

| Rama | Responsable | Estado | Trabajo único vs `main` |
|---|---|---|---|
| `main` | — | Protegida | Línea base. Solo recibe merges. |
| `feat/Luis-G1-Necesidades` | Luis | Merged en main | Necesidades (módulo G1) |
| `feat/alertas-g2` | Javi | Merged en main | Alertas oficiales (módulo G2) |
| `feat/vanessa-g3-ayudas` | Vanessa | Merged en main | Donaciones y voluntariado (módulo G3) |
| `feat/juan-g4-mapa` | Juan | Activa, con trabajo extra | Mapa, frontend, branding Anexo Finder (módulo G4) |
| `anexo-risk` | — | Histórico | Trabajo de rebranding previo a la convención del flujo |
| `chore/anexo-risk-hardening` | Juan | Activa, pendiente PR a develop | Hardening: P0/P1 fixes, limpieza NEXO, CI, .env.example, README |

> **Convención de trabajo:** cada feature parte de `main`, se desarrolla
> en `feat/<persona>-<módulo>`, y vuelve a `main` por PR. La rama
> `chore/anexo-risk-hardening` es la única transversal de mantenimiento
> y va a `develop` para que cada equipo la integre en su próxima iteración.

---

# Técnico

## 10. Stack técnico

| Capa | Tecnología | Versión |
|---|---|---|
| Backend | Python | 3.11+ |
| Framework | FastAPI | 0.115+ |
| Validación | Pydantic | 2.9+ |
| Base de datos | SQLite | con migraciones idempotentes |
| Frontend | Vanilla JS | ES modules, sin framework |
| Mapa | Leaflet | 1.9.4 |
| Tests backend | pytest | con TestClient de FastAPI |
| Tests frontend | jest | en `tests/frontend/` |
| CI/CD | GitHub Actions | `.github/workflows/ci.yml` |

**Decisiones explícitas del equipo:**

- **Sin frameworks JS** (sin React, Vue, Svelte) — vanilla JS con
  módulos ES para mantener bundle bajo y curva de entrada plana.
- **Sin PostgreSQL en esta fase** — SQLite con migraciones idempotentes
  cubre el volumen esperado en emergencias locales.
- **Sin JWT en el MVP** — la autenticación se reduce a una cabecera
  `X-Anexo-Key` para acciones sensibles de coordinador. Login de
  usuario queda para post-MVP.
- **Sin Haversine manual** — la geolocalización usa APIs públicas
  (Nominatim para geocoding inverso, GDACS para alertas).

## 11. Arquitectura

`anexo_risk` sigue una arquitectura en **tres capas desacopladas** con
fronteras explícitas, inspirada en hexagonal simplificado.

### Vista lógica de capas

```
┌──────────────────────────────────────────────────────────────────────┐
│                          CAPA DE PRESENTACIÓN                        │
│                                                                      │
│   Frontend (SPA)                                                     │
│   - Vanilla JS + ES modules (sin framework)                          │
│   - Leaflet 1.9.4 (mapa interactivo)                                 │
│   - Service Worker (cola offline, PWA)                               │
│   - Estado: en memoria + localStorage                                │
└──────────────────────────────────────────────────────────────────────┘
                                │
                                │  HTTP/JSON (REST)
                                │  CORS: localhost:5500
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                          CAPA DE APLICACIÓN                         │
│                                                                      │
│   Backend FastAPI                                                    │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
│   │  Middleware     │  │  Routers        │  │  Background     │     │
│   │  - CORS         │  │  /api/*         │  │  - GDACS cache  │     │
│   │  - Auth         │  │  - Validación   │  │  - Email queue  │     │
│   │  - ErrorHandler │  │    Pydantic 2   │  │                 │     │
│   │  - Logging      │  │  - Modelos SQL  │  │                 │     │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘     │
│                                                                      │
│   Patrón por módulo:                                                 │
│   modules/<dominio>/                                                 │
│     ├── routes.py      # FastAPI router + response_model             │
│     ├── schemas.py     # Pydantic contracts (entrada/salida)         │
│     ├── models.py      # Acceso a datos (queries parametrizadas)     │
│     └── services.py    # Lógica de negocio (transiciones, etc.)      │
└──────────────────────────────────────────────────────────────────────┘
                                │
                                │  sqlite3 (stdlib)
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                          CAPA DE DATOS                              │
│                                                                      │
│   SQLite + migraciones idempotentes (001-005)                        │
│   - Una tabla por agregado (necesidades, alertas, donaciones, ...)   │
│   - Migraciones aplicadas una vez (controladas por schema_migrations)│
│   - Sin ORM: queries SQL explícitas y parametrizadas                 │
│   - Path configurable vía DATABASE_URL                               │
└──────────────────────────────────────────────────────────────────────┘
                                │
                                │  HTTP (servicios externos)
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       SERVICIOS EXTERNOS                            │
│                                                                      │
│   - GDACS RSS         (alertas oficiales, cache 15 min)              │
│   - Nominatim OSM     (geocoding inverso, rate-limited)              │
│   - SMTP (dummy)      (notificaciones de voluntariado)               │
└──────────────────────────────────────────────────────────────────────┘
```

### Principios arquitectónicos

| Principio | Aplicación concreta |
|---|---|
| **Contratos estables** | Cada respuesta de la API está definida como Pydantic `response_model`. Cambios incompatibles rompen tests antes de llegar a producción. |
| **Queries parametrizadas** | Cero SQL injection. Toda query pasa por `cursor.execute(sql, params)`. |
| **Idempotencia** | Migraciones (por nombre en `schema_migrations`) y operaciones de sync (por `operation_id`). Reintentar no duplica. |
| **Manejo de errores uniforme** | Un único `error_handler` global convierte excepciones a `{status, error, message}` con código HTTP coherente. |
| **Config por entorno** | `python-dotenv` + `os.getenv` con defaults de desarrollo. Cero secretos en código. |
| **Sin framework JS** | El bundle de la SPA queda en <50 KB y carga offline sin pipeline de build. |

### Diagrama de secuencia: reportar una necesidad

```
Ciudadano           SPA                Backend           Nominatim          SQLite
   │                 │                     │                  │                │
   │  click "Reportar"│                    │                  │                │
   │ ───────────────▶│                     │                  │                │
   │                 │  POST /api/necesidades                  │                │
   │                 │  {tipo, lat, lng, ...}                  │                │
   │                 │ ───────────────────▶│                   │                │
   │                 │                     │  reverse geocode  │                │
   │                 │                     │ ────────────────▶│                │
   │                 │                     │  ◀──── address ──│                │
   │                 │                     │  INSERT row (parameterized)        │
   │                 │                     │ ──────────────────────────────────▶│
   │                 │                     │  ◀───── id ───────────────────────│
   │                 │  201 Created        │                  │                │
   │                 │  {id, estado, ...}  │                  │                │
   │                 │ ◀───────────────────│                  │                │
   │  toast "ok"     │                     │                  │                │
   │ ◀──────────────│                      │                  │                │
   │                 │                     │                  │                │
```

### Módulos del backend

| Módulo | Ruta base | Responsabilidad |
|---|---|---|
| Necesidades | `/api/necesidades` | Reporte ciudadano, geocoding, transiciones de estado |
| Alertas | `/api/alertas` | Feed GDACS, filtrado, cache TTL |
| Donaciones | `/api/donaciones` | Recursos, servicios, ciclo activa→entregada |
| Voluntariado | `/api/voluntarios` | Alta, validación DNI, aprobación, directorio |
| Personas | `/api/personas` | Registro, marcado como localizada |
| Sync | `/api/sync` | Cola offline con idempotencia y reintentos |
| Health | `/api/health` | Liveness check |

## 12. Cómo ejecutarlo

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

## 13. Cómo probarlo

```bash
cd backend
PYTHONPATH=backend DATABASE_URL=sqlite:///./backend/anexo_risk.db \
  python -m pytest ../tests/backend/ -v
```

Resultado esperado: **79 tests pasando**.

## 14. Variables de entorno

Copia `backend/.env.example` a `backend/.env` y ajusta:

| Variable | Default | Descripción |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./anexo_risk.db` | Ruta de la base de datos |
| `BACKEND_PORT` | `8000` | Puerto del backend |
| `CORS_ORIGINS` | `http://localhost:5500,...` | Orígenes CORS permitidos |
| `ANEXO_ADMIN_KEY` | `anexo-risk-dev-admin-key` | Clave de coordinador (cabecera `X-Anexo-Key`) |
| `GDACS_API_URL` | `https://www.gdacs.org/xml/rss.xml` | Feed de alertas oficiales |
| `GDACS_CACHE_TTL_SECONDS` | `900` | TTL del cache de alertas |
| `EMAIL_DUMMY_MODE` | `true` | Si `true`, no envía correos reales (solo log) |
| `ADMIN_EMAIL` | `admin@anexo-risk-dummy.local` | Destinatario de notificaciones |
| `SMTP_*` | localhost:587 | Configuración SMTP (modo dummy) |
| `UPLOAD_DIR` | `uploads/voluntarios` | Carpeta para documentos de voluntarios |
| `MAX_UPLOAD_SIZE_MB` | `5` | Tamaño máximo de subida |

## 15. Estructura del repositorio

```
anexo_risk/
├── backend/                 # FastAPI + SQLite + Pydantic
│   ├── main.py              # Arranque FastAPI
│   ├── config.py            # Variables de entorno
│   ├── db/
│   │   ├── database.py      # Conexión + get_cursor()
│   │   ├── migrations/      # 001-005 *.sql idempotentes
│   │   └── seed.py          # Datos de ejemplo (idempotente)
│   ├── modules/
│   │   ├── necesidades/     # Reporte ciudadano
│   │   ├── alertas/         # GDACS
│   │   ├── donaciones/      # Recursos y servicios
│   │   ├── voluntariado/    # Red de apoyo
│   │   └── personas/        # Registro y búsqueda
│   ├── middleware/          # CORS, auth, logging, errores
│   ├── sync/                # Modo offline (backend listo)
│   └── integrations/        # GDACS, USGS, Nominatim
│
├── frontend/                # SPA vanilla JS
│   ├── index.html           # SPA única
│   ├── manifest.json        # PWA manifest
│   ├── js/
│   │   ├── spa.js           # Entry point
│   │   ├── core/            # Módulos por pantalla
│   │   └── shared/          # Componentes y utilidades
│   ├── css/                 # Variables + estilos
│   ├── assets/              # Logo, iconos
│   └── mocks/               # Fallback cuando la API cae
│
├── tests/
│   ├── backend/             # pytest
│   └── frontend/            # jest
│
├── docs/                    # Documentación vigente
├── .github/workflows/       # CI/CD
└── vercel.json              # Despliegue serverless (opcional)
```

## 16. API endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/health` | Liveness check |
| GET | `/api/alertas` | Listar alertas oficiales (filtros: nivel, tipo, país) |
| GET | `/api/necesidades` | Listar necesidades (filtros: tipo, estado) |
| POST | `/api/necesidades` | Reportar nueva necesidad |
| GET | `/api/necesidades/{id}` | Detalle de una necesidad |
| PATCH | `/api/necesidades/{id}/estado` | Cambiar estado (transición válida) |
| GET | `/api/donaciones` | Listar donaciones (filtro: tipo) |
| POST | `/api/donaciones` | Publicar donación |
| PATCH | `/api/donaciones/{id}/estado` | Marcar entregada |
| GET | `/api/voluntarios` | Directorio de voluntarios |
| POST | `/api/voluntarios` | Alta de voluntario |
| POST | `/api/personas/{id}/localizada` | Marcar persona como localizada |
| POST | `/api/sync/batch` | Sincronizar cola offline |

Las cabeceras comunes son:

- `Content-Type: application/json`
- `X-Anexo-Key: <ANEXO_ADMIN_KEY>` para acciones sensibles de coordinador

## 17. Convenciones y docs

Documentos vigentes del proyecto `anexo_risk`:

- [`docs/architecture.md`](docs/architecture.md) — Decisiones arquitectónicas (ADRs)
- [`docs/manifiesto.md`](docs/manifiesto.md) — Misión y criterios de éxito
- [`docs/backlog.md`](docs/backlog.md) — Estado actual del trabajo
- [`docs/sprint.md`](docs/sprint.md) — Seguimiento de sprints
- [`docs/convenciones.md`](docs/convenciones.md) — Convenciones de código
- [`docs/roadmap.md`](docs/roadmap.md) — Roadmap por sprints

Convenciones de código obligatorias (resumen):

- **Python:** `snake_case` para funciones/variables, `PascalCase` para clases, `SNAKE_CASE` para constantes, queries SQL siempre parametrizadas.
- **JavaScript:** `camelCase` para funciones y variables, `PascalCase` para clases, ES modules, sin framework.
- **CSS:** variables `nexo-` + BEM-lite (convención heredada del proyecto previo, mantenida por estabilidad de estilos).
- **SQL:** tablas en `snake_case`, migraciones idempotentes, no romper la firma de una tabla ya desplegada sin `ALTER TABLE`.
- **Commits:** Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`, `test:`, `ci:`).

---

# Visión

## 18. Próximas implementaciones

Roadmap del producto en tres horizontes. Lo que se enumera aquí es lo
que se construirá, no lo que se ha construido.

### 18.1 Sprint actual (en curso)

- **SPA unificada y rebranding completo** — Sustituir las páginas
  individuales (`pages/`) por una única `index.html` que enruta
  internamente.
- **Refinamiento UX** — Mapa más limpio, marcadores accesibles, panel
  lateral plegable, soporte móvil real.
- **Hardening transversal** — Corrección de bugs P0/P1 heredados
  (config defaults, exception handler, sync controller, identidad
  NEXO→Anexo), CI con tests contra DB correcta, gitignore endurecido.

### 18.2 Siguiente sprint (post-MVP inmediato)

- **Migración de SQLite a PostgreSQL/PostGIS** — Cuando el volumen de
  necesidades geolocalizadas crezca, las queries espaciales nativas
  (radio, polígono, intersección con alertas) justifican el cambio.
- **Autenticación real de coordinadores** — Sustituir la cabecera
  `X-Anexo-Key` compartida por un sistema de cuentas (OAuth / magic
  link) con roles diferenciados: coordinador, voluntario, ciudadano.
- **Modo offline 100% funcional** — El backend ya soporta sync con
  idempotencia y reintentos. Falta la cola en frontend y el
  service worker completo para lectura de necesidades y alertas
  cacheadas.
- **Notificaciones push** — Avisar a coordinadores cuando se abre
  una necesidad de prioridad `critica` o cuando una alerta oficial
  cae en su zona.

### 18.3 Roadmap estratégico (3-6 meses)

- **Integración con Protección Civil en tiempo real** — Pasar del
  feed RSS de GDACS a un canal bidireccional con la fuente oficial
  nacional, incluyendo creación de alertas manuales.
- **App móvil nativa** — Wrapper ligero sobre la PWA con capacidades
  nativas: geolocalización en background, notificaciones push
  nativas, cámara para documentar necesidades.
- **Módulo de analytics para coordinadores** — Dashboard de métricas
  operativas: tiempo medio de cobertura, ratio necesidad/voluntario
  por zona, mapa de calor de actividad, exportación CSV/PDF para
  informes a autoridades.
- **Multi-idioma** — `i18n` desde el inicio en los textos visibles
  (interfaz), empezando por español, inglés y valenciano.
- **API pública documentada** — Exponer un subconjunto de la API
  (alertas, necesidades públicas) para que terceros puedan
  integrarse: ONGs, otros municipios, medios de comunicación.
- **Panel de auditoría** — Trazabilidad completa de cambios de
  estado, transiciones de necesidades, aprobaciones de voluntariado,
  para cumplir con requisitos de protección de datos.

### 18.4 Lo que **no** entra en el roadmap

Decisiones explícitas que el equipo ha tomado y que no se
revisarán en el horizonte próximo, salvo cambio de contexto:

- **No PostgreSQL antes de que el volumen lo justifique** — SQLite con
  migraciones cubre la fase actual.
- **No React/Vue/Svelte** — Vanilla JS sigue siendo la opción correcta
  para el bundle y la mantenibilidad.
- **No chatbot, no IA conversacional, no LangChain** — La
  interacción es formulario + mapa, no chat. La complejidad de un
  agente conversacional no aporta al problema de triage.
- **No Haversine manual en backend** — Se usan las APIs geoespaciales
  de la base de datos cuando se migre a PostGIS, no se reimplementa
  en Python.
- **No JWT en MVP** — La cabecera `X-Anexo-Key` cubre las acciones
  sensibles. JWT entra cuando haya login de usuario real.

---

## 19. Licencia y créditos

**Producto:** `anexo_risk`
**Stack:** FastAPI + SQLite + Vanilla JS + Leaflet
**Equipo actual:** Vanessa, Javi, Luis, Juan
**Herencia:** Proyecto "Nexo" (Dana de Valencia, 2024-2025)

`anexo_risk` se publica como proyecto académico y de impacto social.
Cualquier organización interesada en desplegarlo o contribuir puede
abrir un issue en el repositorio.
