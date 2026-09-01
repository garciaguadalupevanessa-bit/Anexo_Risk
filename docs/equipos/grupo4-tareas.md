# Grupo 4 (Mapa + Interfaz) — Juan — MVP Jueves — Producto Integral

> **Dueño único: Juan (tú, GeoRisk)** — Rama `feat/juan-g4-mapa` (actual `feat/juan-anexo-risk`) → PR → `anexo-risk`. **Producto integral:** el mapa es el pegamento de todo — sin G4 no hay demo (ALTO RIESGO desbloquea G1+G3). Ver `docs/equipos/reparto-anexo-risk-4p-equitativo.md`.

## Archivos (solo Juan los toca)

| Archivo | Qué hace (producto integral) |
|---|---|
| `frontend/pages/mapa.html` | Página principal — header `Mapa | Alertas | Ayudas`, contenedor `#map`, filtros `typeFilter` |
| `frontend/js/core/mapa-necesidades/mapaNecesidades.js` | **Núcleo integral:** Leaflet base + capas + consumo de 3 contratos + resaltado `zone` + intensidad + popups |
| `frontend/js/shared/apiClient.js` | Cliente único `apiGet/apiPost` para `alertas`, `necesidades`, `ayudas` (evita `fetch` disperso) |
| `frontend/mocks/*.json` | `alertas.mock.json`, `necesidades.mock.json`, `ayudas.mock.json` — fallback si API cae en demo |
| `frontend/css/*` (`variables.css`, `style.css`, `components.css`, `mapa.css`) | Estilos `nexo-` para marcadores y popups |
| `georisk_globe/frontend/` | Referencia globo 3D — **post-MVP** (`?globe=1` toggle) |
| `src/h3_aggregator.py` | Referencia H3 res 6-7 para intensidad hex — **post-MVP** (MVP usa `filter` simple) |

## Tareas detalladas (5 tareas, producto integral)

- [ ] **T1 — Mapa base + toggles:** `L.map("map").setView([40.41,-3.70],13)` + `L.tileLayer CartoDB` + `L.control.layers` con `L.layerGroup` para Alertas / Zonas / Necesidades / Ayudas (ver `mapaNecesidades.js:1-11`).
- [ ] **T2 — Consumo 3 contratos (integral):**
  - `GET /api/alertas` (Javi) → `L.geoJSON(zone, {style:{color: risk_level}})`
  - `GET /api/necesidades?estado=abierta` (Luis) → `L.marker([lat,lon], {icon: getIconByPriority})` con `direccion` + `categoria_etiqueta`
  - `GET /api/ayudas` (Vanessa) → `L.marker` icono Ayuda
  - Todo vía `apiClient.js` (no `fetch` directo)
- [ ] **T3 — ALTO RIESGO (pegamento integral):** si `alertas[0].risk_level===high && is_active`, pinta `zone` rojo + `map.fitBounds(zone)` + filtra `necesidades`/`ayudas` dentro de `zone` (`turf.booleanPointInPolygon` o `h3` res7 para MVP `filter`, H3 post-MVP).
- [ ] **T4 — Intensidad + popups:** conteo necesidades en `zone` → 🟢 <3 🟠 3-5 🔴 >5 (`aggregate_by_h3` opcional), `marker.bindPopup` con `titulo`+`direccion`+`prioridad` badge + botón `PATCH /api/necesidades/{id}`→`cubierta` (cambia icono y oculta del mapa).
- [ ] **T5 — Interfaz + fallback:** header `Mapa|Alertas|Ayudas` + estados `carga/vacío/error` + si API falla cargar `frontend/mocks/*.json` (ya en `dev`). Demo: sin recargar página, `loadNeedsFromAPI()` refresca al crear necesidad.

**Depende de:** Javi (zone), Luis (necesidades), Vanessa (ayudas) — **último en mergear.** Es el **integrador del producto integral**: sin G4 no se ve el flujo `alerta→zona→necesidad→ayuda`.

**Post-MVP:** `h3_aggregator.py` hex grid + `georisk_globe` toggle.
