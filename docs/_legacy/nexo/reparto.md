# Anexo Risk — Reparto Equitativo 4p (sin directrices previas) — MVP Jueves

> 4 personas (Javi, Juan, Luis, Vanessa), 4 módulos, **1 rama única `anexo-risk` → `main`**. Cada persona **dueña exclusiva** de archivos (0 solapes) + **5 tareas / ~8h** equitativas. Enfoque ágil profesional: WIP=1, daily 15:00 15min, PR review <2h, integración continua a `main`.

## Matriz de propiedad (0 solapes — CODEOWNERS)

| Persona | Módulo | Archivos exclusivos | Puntos |
|---|---|---|---|
| **Javi** | G2 Alertas | `backend/modules/alertas/*`, `backend/integrations/gdacs*`, `backend/config.py` (CORS) | 5 |
| **Juan** | G4 Mapa | `frontend/pages/mapa.html`, `frontend/js/core/mapa-necesidades/mapaNecesidades.js`, `frontend/js/shared/apiClient.js` | 5 |
| **Luis** | G1 Necesidades | `backend/modules/necesidades/*`, `frontend/js/core/mapa-necesidades/formulario*`, `necesidadCard.js`, `geocodificacion.js` | 5 |
| **Vanessa** | G3 Ayudas + QA | `backend/modules/voluntariado/*`, `backend/modules/donaciones/*`, `frontend/pages/donaciones.html`, `frontend/js/core/voluntariado-donaciones/**`, `frontend/css/*`, `frontend/mocks/*.json` | 5 |

*Nadie toca `api/index.py`/`vercel.json`/`docs/*` sin avisar. `seed.py` y `main.py` solo por coordinador.*

## Reparto equitativo (5 tareas c/u, sin solapes)

### Javi — G2 Alertas (Backend crítico) — Coordina con Juan (punto 1)
**Rama:** `feat/javi-g2-alertas`
- [ ] Merge `alerts` da97f22 → zona GeoJSON `TEXT`, `RiskLevelEnum`, `is_active`
- [ ] **Acuerdo 1 — GeoJSON `zone` objeto:** `services.py` hace `json.loads(zone)` + `schemas.py` expone `zone: dict` (no string) con `Field(alias="zona")` para que `L.geoJSON(data.zone)` funcione sin `JSON.parse` (pair Javi+Juan)
- [ ] Esquema unificado inglés `external_id`/`source`/`severity` + alias español (`Field(alias="fuente")`)
- [ ] Endpoints `GET /api/alertas?external_id` + `POST /alto-riesgo` + validación Polygon + dedup `external_id` vs BD
- [ ] Fallback GDACS `[]` sin 500 + `proteccion_civil_client` stub
- [ ] Tests `test_alertas.py` 13 verdes + `test_alto_riesgo_desbloquea_zona`

### Juan (tú) — G4 Mapa (Integración + GeoRisk) — Coordina punto 1 y 3
**Rama:** `feat/juan-g4-mapa` (ya tienes `feat/juan-anexo-risk`, renombrar)
- [ ] Mapa base Leaflet `CartoDB` + `LayerControl` (capas toggles)
- [ ] **Acuerdo 1 — GeoJSON:** consumir `GET /api/alertas` → `L.geoJSON(data.zone)` directo (objeto, no string) — pair con Javi
- [ ] **Acuerdo 3 — CSS `nexo-`:** usar solo `var(--nexo-primary)`, `var(--nexo-alert-red)`, `var(--nexo-bg-dark)` de `variables.css` (Vanessa crea `:root` primero)
- [ ] Resaltado `ALTO RIESGO`: `zone` rojo + `fitBounds` + filtro `booleanPointInPolygon` (o H3 res7)
- [ ] Popups `titulo`+`direccion`+`categoria_etiqueta` + botón `PATCH cubierta` + Header `Mapa|Alertas|Ayudas` + estados carga/vacío/error

### Luis — G1 Necesidades (Fullstack ligero) — Acuerdo 3
**Rama:** `feat/luis-g1-necesidades`
- [ ] `POST /api/necesidades` con `direccion` + 8 cats `parafarmacia` + 2 estados `abierta→cubierta` (backend ya en `anexo-risk`, solo verificar)
- [ ] `formularioNecesidad.js` 8 botones + `geocodificacion.js` → `direccion` legible (usa `var(--nexo-*)` de Vanessa)
- [ ] `necesidadCard.js` lista lateral + `necesidadesApi.js` (`obtener/crear/cambiarEstado`) con `var(--nexo-*)`
- [ ] `services.py` título por defecto desde `tipo` + truncado `direccion` 300
- [ ] Tests `test_necesidades` + `probar_integracion_necesidades.mjs` verdes

### Vanessa — G3 Ayudas + QA Global (Fullstack + Estilos) — Acuerdos 2 y 3
**Rama:** `feat/vanessa-g3-ayudas`
- [ ] Wrapper `POST /api/ayudas` + `GET /api/ayudas` 3 tipos (`recursos|servicios|tiempo` con DNI)
- [ ] UI `ayudas.html` selector + form mínimo + contrato `{id,type,category,lat,lon,status}` → mapa
- [ ] Reusa tablas `donaciones`/`voluntarios` (no nueva tabla)
- [ ] **Acuerdo 2 — Seed:** NO tocar `backend/db/seed.py`/`main.py` (solo coordinador) — deja 1 ayuda demo en `frontend/mocks/ayudas.mock.json` y pasa JSON a Juan para `seed.py` en merge final a `main`
- [ ] **Acuerdo 3 — CSS `nexo-`:** crea **primero** `frontend/css/variables.css` con `:root{--nexo-primary:#10b981;--nexo-alert-red:#ef4444;--nexo-bg-dark:#0a192f;}` para que Juan/Luis usen `var(--nexo-*)` sin hardcode + `frontend/mocks/*.json` fallback si API cae + QA `pytest` 120 verdes

## Agilidad profesional (sin burocracia) + Acuerdos 2/4
- **WIP 1:** cada uno 1 PR abierto a `main`, review <2h, merge squash, `git pull --rebase origin main` diario.
- **Daily 15:00 (15 min):** qué hice, qué haré, bloqueo. Pairs 30 min: Javi+Juan para `zone` objeto, Luis+Vanessa para `form`/`variables.css`.
- **Acuerdo 2 — `seed.py`/`main.py`:** solo coordinador (Juan) los toca; el resto deja mocks/`frontend/mocks/*.json` + JSON al coordinador.
- **Acuerdo 4 — Vercel:** cada PR `feat/*` → `main` genera **Preview URL** aislada automática; `main` es **Producción** (URL definitiva Jueves). No configurar ramas Preview extra.

## Por qué es mejor así (sin directrices viejas)
- **Equitativo:** 5 tareas/8h cada uno (antes Juan 8 vs Luis 4). **Sin solapes:** matriz CODEOWNERS arriba.
- **Más ágil:** G1 y G3 son formularios iguales → Luis y Vanessa comparten patrón pero sin pisarse (archivos distintos). G2 y G4 acoplados → Javi y Juan hacen pair puntual, no bloquean a otros.
- **Más profesional:** cada PR es vertical E2E demostrable en demo, CI verde obligatorio, trazabilidad `Closes #` por epic.

> Este reemplaza a `reparto-4p-mvp.md` y `reparto-main-4p-detallado.md` para el equipo de 4.
