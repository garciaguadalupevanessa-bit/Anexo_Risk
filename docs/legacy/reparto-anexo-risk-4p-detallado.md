# Anexo Risk — Reparto detallado 4p (Javi, Juan, Luis, Vanessa) — MVP Jueves

> **Repo único:** `garciaguadalupevanessa-bit/Anexo_Risk` (antes `NexoGeoRisk_Finder`). Rama base `dev` (a687fda, integración NEXO+GeoRisk). **No se toca `main`**: cada persona trabaja en `feat/*` → PR → `dev`. Este documento es fuente única de tareas (reemplaza a `grupo1-4-tareas.md` dispersos). Sprint 2: G1=Necesidades, G2=Alertas, G3=Ayudas, G4=Mapa. Vercel Jamstack (`api/index.py` + `vercel.json`) ya en `dev`.

## Reglas comunes
- **Vertical por módulo:** cada persona dueña E2E (backend + frontend + tests) de su módulo. No tocar archivos ajenos sin avisar en daily 15:00.
- **Contratos mapa (fuente única `docs/modelo-entidad-relacion.md`):**
  - Alerta→Mapa `{id, risk_level, status, zone: Polygon GeoJSON, h3_cells?}`
  - Necesidad→Mapa `{id, tipo, latitud, longitud, estado, direccion, prioridad, categoria_etiqueta}`
  - Ayuda→Mapa `{id, tipo, categoria, latitud, longitud, estado}`
- **Commits/PRs:** `feat(modulo): mensaje en inglés`, PR con `Closes #<epic>` para Kanban. CI `backend-tests` + `frontend-lint` debe pasar.
- **Orden integración:** 1) Javi (Alertas) → 2) Luis+Vanessa en paralelo → 3) Juan (Mapa consume). `git pull --rebase origin dev` cada mañana.

---

### P1 — Javi — G2 Alertas + Activación de crisis + GDACS (Backend)

**Rama:** `feat/alertas-g2-javi` (desde `dev`)
**Archivos dueños (solo él los toca):**
- `backend/modules/alertas/routes.py`
- `backend/modules/alertas/services.py`
- `backend/modules/alertas/schemas.py`
- `backend/integrations/gdacs_client.py`, `gdacs_mock.py`, `proteccion_civil_client.py`
- `backend/config.py` (solo `GDACS_CACHE_TTL_SECONDS` si hace falta)
- `tests/backend/test_alertas.py`, `tests/backend/test_alertas_routes.py` (si existen)
- `frontend/js/core/alertas-oficiales/alerts.js` (solo lectura, coordina con Juan)

**Tareas MVP (debe estar en `dev` Miércoles 18:00):**
- [ ] **Mergear `alerts` (da97f22) a su rama:** `RiskLevelEnum` (`low|medium|high`), `zone: TEXT GeoJSON`, `is_active` ya vienen. Resolver conflictos en `main.py` (router) si hace falta.
- [ ] **Adaptar a esquema unificado GeoRisk (inglés en código, español en docs):** añadir `external_id` (ej. `GDACS_1234`), `source` (`GDACS|PROTECCION_CIVIL|MANUAL`), `severity` (`RED|ORANGE|GREEN`), `risk_level`, `status` (`normal|active|high_risk|deactivated`). Usar `Field(alias="fuente")` para no romper front actual.
- [ ] **Endpoints:** `GET /api/alertas?tipo=&severidad=&pais=` (ya existe, añadir `external_id` filter), `POST /api/alertas` (crear manual con `zone`), `POST /api/alertas/{id}/activar`, `POST /api/alertas/{id}/alto-riesgo` (pone `risk_level=high` + `is_active=true`), `POST /api/alertas/{id}/desactivar`. Validar `zone` es Polygon GeoJSON.
- [ ] **Resiliencia:** `fetch_base_alerts()` ya hace fallback `[]` sin 500 — verificar deduplicación `external_id` vs BD local ( `if external_id in db: skip GDACS live` ).
- [ ] **Tests:** `PYTHONPATH=backend pytest tests/backend/test_alertas.py -q` 13 verdes. Añadir test `test_alto_riesgo_desbloquea_zona`.
- [ ] **Entregable demo:** `curl POST /api/alertas -d '{"titulo":"Simulacro Valencia","zone":{"type":"Polygon","coordinates":[...]}, "risk_level":"high"}'` queda visible en mapa.

**Depende de:** nadie. **Bloquea a:** G4 Mapa (Juan necesita `zone`).

---

### P2 — Juan (tú) — G4 Mapa + Interfaz + GeoRisk H3/Globo

**Rama:** `feat/juan-main` (ya creada, desde `dev` a687fda)
**Archivos dueños:**
- `frontend/pages/mapa.html`
- `frontend/js/core/mapa-necesidades/mapaNecesidades.js`
- `frontend/js/shared/apiClient.js`
- `frontend/js/core/mapa-necesidades/geocodificacion.js` (solo consumo, no lógica)
- `frontend/css/*` (variables, mapa)
- `frontend/mocks/*.json` (`alertas.mock.json`, `necesidades.mock.json`, `ayudas.mock.json`)
- `georisk_globe/frontend/` (referencia, no tocar para MVP)
- `src/h3_aggregator.py` (referencia, opcional intensidad)

**Tareas MVP:**
- [ ] **Mapa base:** Leaflet `L.map("map").setView([40.41,-3.70],13)` ya existe — añadir capa `CartoDB positron` + `OpenStreetMap` + `LayerControl`.
- [ ] **Capas toggles:** `L.layerGroup` para Alertas / Zonas / Necesidades / Ayudas con `L.control.layers`.
- [ ] **Consumo contratos:**
  - `GET /api/alertas` → pintar `zone` Polygon con `L.geoJSON(zone, {style: {color: risk_level}})`
  - `GET /api/necesidades?estado=abierta` → `L.marker([lat,lon])` con `getIconByPriority`
  - `GET /api/ayudas` → `L.marker` con icono Ayuda
- [ ] **Resaltado ALTO RIESGO:** si `risk_level=high` y `is_active`, `zone` en rojo + `map.fitBounds(zone)` y filtrar `necesidades`/`ayudas` que caen dentro (`turf.booleanPointInPolygon` o `h3` res 7: `h3.latlng_to_cell(lat,lon,7)` ∈ `h3_cells` del alerta).
- [ ] **Intensidad:** conteo necesidades en zona → 🟢 <3, 🟠 3-5, 🔴 >5 (usa `aggregate_by_h3` de `src/h3_aggregator.py` si quieres, o simple `filter` para MVP).
- [ ] **Popups:** `need.titulo` + `need.direccion` + `need.categoria_etiqueta` + botón `POST /api/necesidades/{id}` → `cubierta`.
- [ ] **Mocks fallback:** si API no responde, cargar `frontend/mocks/*.json` (ya existen en `dev`).
- [ ] **Interfaz:** header `Mapa | Alertas | Ayudas` (3 links a `pages/*.html`), estados carga/vacío/error.

**Depende de:** Javi (zone), Luis (necesidades), Vanessa (ayudas). **Último en mergear.**

**Post-MVP (no Jueves):** `h3_aggregator.py` res 6 para hex grid + toggle `?globe=1` con `georisk_globe`.

---

### P3 — Luis — G1 Necesidades (8 cats/2 estados + direccion)

**Rama:** `feat/necesidades-g1-luis` (desde `dev`)
**Archivos dueños:**
- `backend/modules/necesidades/models.py`, `schemas.py`, `services.py`, `routes.py`
- `backend/db/migrations/001_init.sql` (no tocar salvo nueva migración), `004_necesidades_direccion.sql`, `005_necesidades_redisenio.sql` (ya en `dev`, solo leer)
- `frontend/js/core/mapa-necesidades/formularioNecesidad.js`
- `frontend/js/core/mapa-necesidades/necesidadCard.js`
- `frontend/js/core/mapa-necesidades/necesidadesApi.js`
- `frontend/js/core/mapa-necesidades/geocodificacion.js`
- `tests/backend/test_necesidades.py`, `test_necesidades_routes.py`, `tests/frontend/mapa-necesidades.test.js`

**Tareas MVP (backend ya en `dev` 91a7647, solo pulir frontend):**
- [ ] Verificar `POST /api/necesidades` acepta `direccion` (geocodificación Nominatim) + `tipo` 8 valores (`parafarmacia` no `medicina`) + estados `abierta→cubierta` (sin `en_proceso`). Ya mergeado, solo testear `curl`.
- [ ] `formularioNecesidad.js`: 8 botones categoría, `geocodificacion.js` → `direccion` legible, validación `lat/lon`, `prioridad` default `media`.
- [ ] `necesidadCard.js`: lista lateral con `categoria_etiqueta` (emoji) + `direccion` + botón `PATCH /api/necesidades/{id}` → `cubierta`.
- [ ] `necesidadesApi.js`: `configurarBaseUrl("http://localhost:8000/api/necesidades")` + `obtenerNecesidades`, `crearNecesidad`, `cambiarEstado`.
- [ ] Tests: `probar_integracion_necesidades.mjs` y `pytest` 120 pasan (ya verificado en `integrados`).

**Entregable:** crear necesidad con categoría + ubicación + `direccion` y verla en mapa.

---

### P4 — Vanessa — G3 Ayudas (Unifica donación + voluntariado)

**Rama:** `feat/ayudas-g3-vanessa` (desde `dev`)
**Archivos dueños:**
- `backend/modules/voluntariado/*` (`models.py`, `schemas.py`, `routes.py`, `services.py`)
- `backend/modules/donaciones/*` (`models.py`, `schemas.py`, `routes.py`)
- `frontend/pages/donaciones.html`, `frontend/pages/voluntariado.html` (unificar en `ayudas.html` si prefieres)
- `frontend/js/core/voluntariado-donaciones/**` (`donaciones.js`, `donacionesApi.js`, `voluntariado.js`, `voluntariadoApi.js`)
- `backend/integrations/proteccion_civil_client.py` (soporte)
- `frontend/css/donaciones.css`, `voluntariado.css`

**Tareas MVP (reduce a 1 tipo para demo):**
- [ ] Crear wrapper `POST /api/ayudas` + `GET /api/ayudas` en `backend/modules/voluntariado/routes.py` o nuevo `backend/modules/ayudas/` (reutiliza modelos). Body 3 tipos:
  - `recursos`: `{tipo:"recursos", recurso:"alimentos", cantidad, contacto}`
  - `servicios`: `{tipo:"servicios", recurso:"transporte"}`
  - `tiempo`: `{tipo:"tiempo", nombre, dni, contacto, habilidades}`
- [ ] UI `ayudas.html` con selector `tipo` + formulario mínimo (para `tiempo`: `nombre`+`DNI` obligatorios).
- [ ] Contrato hacia mapa G4: `GET /api/ayudas` → `{id, type, category, latitude, longitude, status}`.
- [ ] Persistencia: reutiliza tablas `donaciones`/`voluntarios` (no nueva tabla). Si falta tiempo, hardcodear 1 ayuda `recurso: alimentos` en `backend/db/seed.py`.
- [ ] Tests: `pytest` voluntariado verdes ya en `dev`.

**Depende de:** nadie para crear, pero G4 consume su contrato.

---

## Tareas transversales (todos, antes de Jueves)

- [ ] **Seed demo** (Juan coordina, todos aportan 1 dato): `backend/db/seed.py` → 1 alerta `high_risk` zona Valencia, 3 necesidades (`agua`, `alimentos`, `refugio`) dentro de `zone`, 1 ayuda `recursos` dentro.
- [ ] **CI verde:** `PYTHONPATH=backend pytest --ignore=tests/test_mlflow_tracking.py` (120 tests) + `test -f frontend/index.html` en cada PR.
- [ ] **Vercel:** `api/index.py` + `vercel.json` ya en `dev` (4f9f29f) — cada `feat/*` no necesita tocar. Deploy final desde `dev` en `garciaguadalupevanessa-bit/Anexo_Risk`.
- [ ] **Limpieza legacy (no tocar sin verificar):** `sync_log` vs `sync_operations`, `streamlit_app/` (se mantiene solo como referencia, no se despliega).

## Orden y ramas (no se toca `main`)

```bash
git checkout dev && git pull origin dev
git checkout -b feat/tu-modulo   # ej. feat/juan-main ya existe
# ... trabaja solo tus archivos ...
git push -u origin feat/tu-modulo
gh pr create --base dev --title "feat(modulo): ..."  # 1 review de otro del equipo → merge
# Jueves 12:00: gh pr create --base main --head dev --title "release: MVP Anexo Risk"
```

**PRs esperados Jueves:** 4× `feat/*` → `dev` + 1× `dev` → `main`.

