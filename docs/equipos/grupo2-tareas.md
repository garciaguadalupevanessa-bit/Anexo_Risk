# Grupo 2 (Alertas + Activación) — Javi — MVP Jueves

> **Dueño único: Javi** — Rama `feat/javi-g2-alertas` → PR → `anexo-risk`. Ver `docs/equipos/reparto-anexo-risk-4p-equitativo.md`.

## Archivos (solo Javi los toca)

| Archivo | Qué hace |
|---|---|
| `backend/modules/alertas/schemas.py` | `SeverityEnum` (red/orange/green), `EventTypeEnum` (terremoto/ciclon/inundacion/incendio/volcan/sequia/otro), `AlertResponse` con `external_id`, `source`, `risk_level` |
| `backend/modules/alertas/services.py` | `fetch_base_alerts()` con fallback `[]` + `list_filtered_alerts(tipo,severidad,pais)` + `COUNTRY_ALIASES` + dedup `external_id` |
| `backend/modules/alertas/routes.py` | `GET /api/alertas`, `POST /api/alertas` (con `zone` Polygon), `POST /{id}/activar|alto-riesgo|desactivar` + validación `severity`/`tipo` (422) |
| `backend/integrations/gdacs_client.py`, `gdacs_mock.py`, `proteccion_civil_client.py` | Ingesta GDACS RSS + mock + PC stub |
| `backend/config.py` | `GDACS_CACHE_TTL_SECONDS` (15 min) + CORS |
| `backend/main.py` | Registro `alertas_router` (solo si crea nuevo router) |
| `tests/backend/test_alertas.py` | Tests GDACS (filtros, cache, resiliencia 500/malformed) |

## Tareas detalladas (5 tareas)

- [ ] **T1 — Merge `alerts` da97f22:** `RiskLevelEnum` low/medium/high + `zone: TEXT GeoJSON` + `is_active` a `schemas.py`. Resolver `main.py`.
- [ ] **T2 — Esquema unificado inglés:** añadir `external_id="GDACS_1234"`, `source`, `severity`, `risk_level`, `status`, `zone`, `h3_cells` (usa `Field(alias="fuente")` para no romper front).
- [ ] **T3 — Endpoints:** `GET /api/alertas?tipo=&severidad=&pais=&external_id` (valida Enum 422), `POST /api/alertas` (valida `zone` Polygon), `POST /{id}/alto-riesgo` → `risk_level=high`+`is_active` (desbloquea mapa), `POST /{id}/desactivar`.
- [ ] **T4 — Resiliencia + dedup:** `fetch_base_alerts()` ya hace `[]` sin 500 → añadir `if external_id in db: skip` para no duplicar GDACS live vs BD.
- [ ] **T5 — Tests + demo:** `PYTHONPATH=backend pytest tests/backend/test_alertas.py -q` 13 verdes + `curl POST /api/alertas -d '{"titulo":"Valencia","zone":{"type":"Polygon","coordinates":[[...]]},"risk_level":"high"}'` visible en mapa.

**Bloquea a:** Juan G4 (necesita `zone`). **Depende de:** nadie.
