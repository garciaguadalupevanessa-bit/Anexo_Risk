# Grupo 3 (Ayudas) — Vanessa — MVP Jueves

> **Dueña única: Vanessa** — Rama `feat/vanessa-g3-ayudas` → PR → `main`.

## Archivos (solo Vanessa los toca)

| Archivo | Qué hace |
|---|---|
| `backend/modules/voluntariado/models.py`, `schemas.py`, `routes.py`, `services.py` | Voluntariado `tiempo` (nombre, dni, contacto, habilidades, disponibilidad) |
| `backend/modules/donaciones/models.py`, `schemas.py`, `routes.py` | Donaciones `recursos`/`servicios` (tipo, recurso, cantidad, contacto) |
| `backend/integrations/proteccion_civil_client.py` | Stub PC (soporte, no bloqueante) |
| `frontend/pages/donaciones.html`, `voluntariado.html` → `ayudas.html` | Unifica UI (selector tipo) |
| `frontend/js/core/voluntariado-donaciones/donaciones.js`, `donacionesApi.js`, `voluntariado.js`, `voluntariadoApi.js` | Lógica UI + API cliente |
| `frontend/css/donaciones.css`, `voluntariado.css` | Estilos `nexo-` |
| `frontend/mocks/ayudas.mock.json` | Mock fallback 1 ayuda demo |
| `backend/db/seed.py` | Seed demo (opcional 1 ayuda) |

## Tareas detalladas (5 tareas)

- [ ] **T1 — Wrapper API:** Crear `POST /api/ayudas` + `GET /api/ayudas` (o en `voluntariado/routes.py`). Reutiliza tablas `donaciones`/`voluntarios` (no nueva tabla). Espejo contrato: `recursos`→`donaciones`, `tiempo`→`voluntarios` con `dni`.
- [ ] **T2 — Tipos:** `recursos` `{recurso:"alimentos", cantidad}`, `servicios` `{recurso:"transporte"}`, `tiempo` `{nombre, dni, contacto, habilidades}` (dni validado).
- [ ] **T3 — UI unificada:** `ayudas.html` con selector `tipo` → muestra form correspondiente; para `tiempo` exige `nombre`+`DNI`; submit → `POST /api/ayudas`.
- [ ] **T4 — Contrato mapa:** `GET /api/ayudas` → `{id, type, category, latitude, longitude, status}` para `mapaNecesidades.js` (Juan consume).
- [ ] **T5 — Persistencia + fallback:** Reusa tablas existentes; si falta tiempo, `seed.py` hardcodea 1 ayuda `recursos: alimentos` en zona ALTO RIESGO. Tests `pytest` voluntariado ya verdes.

**Depende de:** nadie. **Bloquea a:** Juan G4 (consume contrato).
