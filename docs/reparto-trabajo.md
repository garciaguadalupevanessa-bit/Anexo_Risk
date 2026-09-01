# Reparto de trabajo — Anexo Risk (4p: Javi, Juan, Luis, Vanessa) — Producto Integral

> **Evolución de NEXO:** `Anexo Risk` mantiene la misma app (mapa como protagonista, ALTO RIESGO desbloquea necesidades/ayudas) pero ahora con 4 personas cubriendo los 4 módulos. Cada persona es dueña **equitativa, sin solapes** de su módulo E2E (ver `docs/equipos/reparto-main-4p-equitativo.md` y `reparto-main-4p-detallado.md`). **Producto integral:** ningún módulo brilla solo — la demo es `alerta → zona → necesidad → ayuda → mapa`.

Base común montada y ya en `dev` (91a7647) + Vercel (`api/index.py` + `vercel.json`) con 4 equipos verticales y `main` como rama única de integración (no `main`).

## Base común (ya montada)
- Punto de entrada de la app (`index.html`, menú, logo) y estilos generales (colores, tipografía, tarjetas, botones).
- Cliente que conecta frontend con backend (`apiClient.js`) — todos llaman a la API igual, sin `fetch()` propio.
- Arranque del servidor en Python (`main.py`, `config.py`) y conexión a BD con tablas ya creadas: `necesidades`, `voluntarios`, `donaciones`, `personas`.
- Datos de ejemplo (`seed.py`) para ver la app funcionando desde el día 1.

> Base común mergeada en `dev` vía #53 — `dev` ya arranca (ver `docs/backlog.md`).

## Equipo 1 — Necesidades — Luis (5 tareas, sin solape)
- **Rama:** `feat/luis-g1-necesidades` → `main`
- **Archivos:** `backend/modules/necesidades/*`, `frontend/js/core/mapa-necesidades/formulario*`, `necesidadCard.js`, `geocodificacion.js` — ver `docs/equipos/grupo1-tareas.md`
- **Producto integral:** provee `{id, tipo, latitud, longitud, estado, direccion}` que G4 pinta; depende de G2 `zone` para filtrar ALTO RIESGO

## Equipo 2 — Alertas + activación — Javi (5 tareas, sin solape)
- **Rama:** `feat/javi-g2-alertas` → `main`
- **Archivos:** `backend/modules/alertas/*`, `backend/integrations/gdacs*`, `backend/config.py` (CORS) — ver `docs/equipos/grupo2-tareas.md`
- **Producto integral:** provee `zone` Polygon + `risk_level` que desbloquea G1+G3 en mapa; es el interruptor de todo

## Equipo 3 — Ayudas — Vanessa (5 tareas, sin solape)
- **Rama:** `feat/vanessa-g3-ayudas` → `main`
- **Archivos:** `backend/modules/voluntariado/*`, `backend/modules/donaciones/*`, `frontend/pages/donaciones.html`, `frontend/js/core/voluntariado-donaciones/**`, `frontend/mocks/ayudas.mock.json` — ver `docs/equipos/grupo3-tareas.md`
- **Producto integral:** provee `{id, type, category, latitud, longitud}` que G4 pinta dentro de `zone`

## Equipo 4 — Mapa + Interfaz — Juan (5 tareas, sin solape, integrador)
- **Rama:** `feat/juan-g4-mapa` (`feat/juan-main` actual) → `main`
- **Archivos:** `frontend/pages/mapa.html`, `frontend/js/core/mapa-necesidades/mapaNecesidades.js`, `frontend/js/shared/apiClient.js`, `frontend/mocks/*.json` — ver `docs/equipos/grupo4-tareas.md`
- **Producto integral:** consume G1+G2+G3 y demuestra `alerta → zona → necesidad → ayuda → cubierta` sin recargar
