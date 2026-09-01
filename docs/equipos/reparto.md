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

### Javi — G2 Alertas (Backend crítico)
**Rama:** `feat/javi-g2-alertas`
- [ ] Merge `alerts` da97f22 → zona GeoJSON `TEXT`, `RiskLevelEnum`, `is_active`
- [ ] Esquema unificado inglés `external_id`/`source`/`severity` + alias español (`Field(alias="fuente")`)
- [ ] Endpoints `GET /api/alertas?external_id` + `POST /alto-riesgo` + validación Polygon + dedup `external_id` vs BD
- [ ] Fallback GDACS `[]` sin 500 + `proteccion_civil_client` stub
- [ ] Tests `test_alertas.py` 13 verdes + `test_alto_riesgo_desbloquea_zona`

### Juan (tú) — G4 Mapa (Integración + GeoRisk)
**Rama:** `feat/juan-g4-mapa` (ya tienes `feat/juan-main`, renombrar)
- [ ] Mapa base Leaflet `CartoDB` + `LayerControl` (capas toggles)
- [ ] Consumir `GET /api/alertas` → `L.geoJSON(zone)` + `GET /api/necesidades` → `L.marker` + `GET /api/ayudas`
- [ ] Resaltado `ALTO RIESGO`: `zone` rojo + `fitBounds` + filtro `booleanPointInPolygon` (o H3 res7 si quieres)
- [ ] Popups `titulo`+`direccion`+`categoria_etiqueta` + botón `PATCH cubierta`
- [ ] Header `Mapa|Alertas|Ayudas` + estados carga/vacío/error (sin mocks — esos los lleva Vanessa)

### Luis — G1 Necesidades (Fullstack ligero)
**Rama:** `feat/luis-g1-necesidades`
- [ ] `POST /api/necesidades` con `direccion` + 8 cats `parafarmacia` + 2 estados `abierta→cubierta` (backend ya en dev, solo verificar)
- [ ] `formularioNecesidad.js` 8 botones + `geocodificacion.js` → `direccion` legible
- [ ] `necesidadCard.js` lista lateral + `necesidadesApi.js` (`obtener/crear/cambiarEstado`)
- [ ] `services.py` título por defecto desde `tipo` + truncado `direccion` 300
- [ ] Tests `test_necesidades` + `probar_integracion_necesidades.mjs` verdes

### Vanessa — G3 Ayudas + QA Global (Fullstack + Estilos)
**Rama:** `feat/vanessa-g3-ayudas`
- [ ] Wrapper `POST /api/ayudas` + `GET /api/ayudas` 3 tipos (`recursos|servicios|tiempo` con DNI)
- [ ] UI `ayudas.html` selector + form mínimo + contrato `{id,type,category,lat,lon,status}` → mapa
- [ ] Reusa tablas `donaciones`/`voluntarios` (no nueva tabla) + `seed.py` 1 ayuda demo
- [ ] `frontend/mocks/*.json` + `frontend/css/*` (variables `nexo-`) + fallback si API cae
- [ ] QA: `pytest --ignore=test_mlflow` 120 verdes + lint `test -f frontend/index.html`

## Agilidad profesional (sin burocracia)
- **WIP 1:** cada uno 1 PR abierto a `main`, review del compañero <2h, merge squash, `git pull --rebase` diario.
- **Daily 15:00 (15 min):** qué hice, qué haré, bloqueo. Bloqueos se resuelven en pair 30 min (Javi+Juan para `zone`, Luis+Vanessa para `form`).
- **Integración:** todos PR → `main` (no `main`). Jueves 12:00 PR `main` → `main` para entrega.
- **Vercel:** `main` auto-deploy Preview; `main` es producción.

## Por qué es mejor así (sin directrices viejas)
- **Equitativo:** 5 tareas/8h cada uno (antes Juan 8 vs Luis 4). **Sin solapes:** matriz CODEOWNERS arriba.
- **Más ágil:** G1 y G3 son formularios iguales → Luis y Vanessa comparten patrón pero sin pisarse (archivos distintos). G2 y G4 acoplados → Javi y Juan hacen pair puntual, no bloquean a otros.
- **Más profesional:** cada PR es vertical E2E demostrable en demo, CI verde obligatorio, trazabilidad `Closes #` por epic.

> Este reemplaza a `reparto-4p-mvp.md` y `reparto-main-4p-detallado.md` para el equipo de 4.
