# Grupo 1 (Necesidades) — Luis — MVP Jueves

> **Dueño único (equitativo, sin solapes): Luis** — Rama `feat/luis-g1-necesidades` → PR → `anexo-risk` (no `main`). Ver `docs/equipos/reparto-anexo-risk-4p-equitativo.md`.

## Archivos (solo Luis los toca)

| Archivo | Qué hace |
|---|---|
| `backend/modules/necesidades/models.py` | Modelo `necesidades` (id, titulo, tipo 8 cats, descripcion, direccion, lat/lon, prioridad, estado 2, creado_en) — ya en `dev`, solo verificar |
| `backend/modules/necesidades/schemas.py` | `NeedType` (agua/alimentos/parafarmacia/ropa/higiene/refugio/transporte/otros), `NeedStatus` (abierta/cubierta), `NeedBase` con `direccion` + `strip_text_fields` |
| `backend/modules/necesidades/services.py` | `create_need` genera `titulo` desde `tipo` si vacío, `list_needs`, `update_need_status` (solo abierta→cubierta) |
| `backend/modules/necesidades/routes.py` | `GET /api/necesidades?tipo=&estado=`, `GET /{id}`, `POST`, `PATCH /{id}` (409 si transición inválida) |
| `frontend/js/core/mapa-necesidades/formularioNecesidad.js` | Form 8 botones, llama `geocodificacion.js` → `direccion` legible, valida lat/lon, `prioridad` default `media` |
| `frontend/js/core/mapa-necesidades/necesidadCard.js` | Lista lateral con `categoria_etiqueta` + `direccion` + botón `PATCH cubierta` |
| `frontend/js/core/mapa-necesidades/necesidadesApi.js` | `obtenerNecesidades`, `crearNecesidad`, `cambiarEstado` vía `apiClient.js` |
| `frontend/js/core/mapa-necesidades/geocodificacion.js` | Nominatim forward/reverse, recorte `direccion` 300, fallback GPS/clic mapa |
| `tests/backend/test_necesidades*.py`, `tests/frontend/mapa-necesidades.test.js`, `probar_integracion_necesidades.mjs` | Tests |

## Tareas detalladas (5 tareas, ~8h)

- [ ] **T1 — Verificar backend ya en `dev`:** `curl POST /api/necesidades -d '{"tipo":"agua","latitud":40.4,"longitud":-3.7}'` → `direccion` default '' + `estado=abierta` + `titulo=💧 Agua` generado
- [ ] **T2 — Formulario:** 8 botones categoría, `geocodificacion.js` rellena `direccion` tras escribir dirección o GPS/clic, valida `lat∈[-90,90]`, `lon∈[-180,180]`
- [ ] **T3 — Tarjeta:** `necesidadCard.js` muestra `categoria_etiqueta` + `direccion` + `prioridad` badge + `PATCH` cubierta (filtro `estado!==cubierta` en mapa)
- [ ] **T4 — API cliente:** `necesidadesApi.js` con `alias titulo/tipo/direccion/latitud/longitud` → contrato `{id, tipo, latitud, longitud, estado, direccion, categoria_etiqueta}`
- [ ] **T5 — Tests:** `PYTHONPATH=backend pytest tests/backend/test_necesidades* -q` y `probar_integracion_necesidades.mjs` verdes. Demo: crear necesidad y verla en `mapaNecesidades.js`

**Depende de:** nadie. **Bloquea a:** Juan G4 (consume contrato).
