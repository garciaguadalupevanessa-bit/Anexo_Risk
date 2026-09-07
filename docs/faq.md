# Preguntas frecuentes y decisiones (NEXO)

> Documento vivo y curado. Solo se registra lo confirmado (decisión o duda cerrada).
> Las dudas abiertas se marcan como "Abierto".

## Grupo 2 — Alertas (dudas generales)

**Decisiones / alcance**
1. **Alcance MVP:** mapa de necesidades, alertas oficiales, voluntariado y donaciones.
2. **Catástrofes:** las de GDACS (terremoto, ciclón, inundación, incendio, volcán, sequía).
   **No:** fuga radiactiva ni apagones.
3. **Localización:** alertas a nivel mundial; mapa con coordenadas libres, sin limitar a España.
   Sin zonas/celdas definidas.
4. **Protección Civil:** capa local opcional de España a futuro; no es AEMET/IGN ni protocolos;
   sin API clara → queda en TODO.
5. **GDACS bloquea:** caché en backend 15 min; si falla → lista vacía (nunca 500). Para demo se
   usan datos simulados.
6. **CSS:** base común ya da estilos compartidos; cada equipo añade los propios de su pantalla.
7. **Vanilla:** HTML/CSS/JS puro, sin framework, PWA.
8. **Filtros:** sí, por tipo de evento, severidad y país (por defecto todas).
9. **Visión:** convertir información dispersa y respuesta desorganizada en capacidad coordinada;
   infraestructura de coordinación, no red social. Simulación/IA: futuro.
10. **Mapa/celdas:** mapa de necesidades con lat/long; zonas/celdas aún no definidas.

**Abierto**
- **Trello vs GitHub Projects:** decidido → **Trello** (un tablero por grupo + uno general).

## Personas / Offline (dudas generales)

**Decisiones / estado**
1. **Guía `personas.html`:** no hay guía específica; seguir el patrón de `index.html` y la lógica
   en `js/siguiente/registro-personas/*.js`. Ver `estructura/estructuranexo.md` y
   `estructuranexoexplicada.md`.
2. **Guía de estilos:** CSS compartido (`variables.css`, `style.css`, `components.css`);
   reutilizar, no inventar. Confirmado en reunión.
3. **Backend:** **FastAPI** (no Flask), API REST bajo `/api/*`. El módulo `personas` ya tiene tabla
   en BD (`001_init.sql`), datos de ejemplo (`seed.py`) y router `/api/personas` en `main.py`;
   faltan endpoints (listar/crear/estoy-bien) y el frontend.
4. **Offline transversal:** diseño en `docs/architecture.md` (apiClient → syncQueue → IndexedDB →
   `procesarColaPendiente()` → `POST /api/sync` → `sync_controller`). La base común lo dejó en TODO
   (`syncQueue.js` solo avisa, `localDb.js`/`serviceWorker.js` TODO) → lo implementa el equipo de frontend (en Sprint 1 correspondía al Grupo 4 — Personas/Offline).
5. **Despliegue:** ninguno definido. Hoy local (frontend `python -m http.server` :5500, backend
   `uvicorn` :8000). CI sí, despliegue no. Opciones demo: frontend Vercel/Netlify, backend
   Render/Railway/Fly.

**Abierto**
- **Alcance exacto del offline:** decisión abierta.
- **Estrategia de despliegue:** pendiente.

## Arquitectura Modular (Sprint 2)

### ¿Por qué se separó spa.js en módulos?
spa.js tenía 1,186 líneas con toda la lógica del mapa (512 líneas), alertas, donaciones, dashboard, navegación, sidebar y drawer en un solo archivo monolítico. Se extrajo en módulos ES:
- `shared/config.js` — API config, constants, escapeHtml utility
- `sections/mapa.js` — Map init, 6 layers, markers, popups
- `sections/alertas.js` — Alert rendering, filters, notifications
- `sections/ayudas.js` — Donation/aid section
- `sections/dashboard.js` — KPI dashboard, CSV export
- `spa.js` — Slim orchestrator (~160 lines)
Resultado: spa.js reducido de 1,186 → 163 líneas (86% reducción).
Ver ADR-007 en `docs/architecture.md`.

### ¿Cómo funciona la normalización de entidades?
El módulo `core/normalization/` (domain.js + sources.js) unifica los datos de 5 fuentes diferentes (GDACS, FIRMS, Open-Meteo, necesidades, donaciones) en una entidad común con campos: id, type, severity, coords, title, description, source, timestamp, country, status, extras. Esto permite que el frontend renderice cualquier fuente con la misma lógica.

## Seguridad (Sprint 2)

### ¿Cómo se protege contra XSS?
Se implementó `escapeHtml()` en `shared/config.js` que escapa &, <, >, ", ' en todo texto insertado en `innerHTML`. Se aplica en TODOS los módulos: alertas.js, mapa.js, ayudas.js, dashboard.js. También se fixeó la inyección de atributos en `data-entity` (JSON → escapeHtml completo).
Ver ADR-008 en `docs/architecture.md`.

### ¿Cómo se valida la entrada de usuario?
Todos los schemas Pydantic tienen: `max_length` en strings, `ge`/`le` en coordenadas, `allow_inf_nan=False` en floats. El `operation_id` en sync se valida con regex `^[a-zA-Z0-9_-]+$` para prevenir SQL injection en SAVEPOINT names.

### ¿Cómo se protegen las rutas sensibles?
- Admin key comparada con `hmac.compare_digest()` (timing-safe)
- SPA catch-all valida `file_path.is_relative_to(FRONTEND_DIR)` (path traversal)
- Error messages genéricos al cliente, detalles en server-side logging
