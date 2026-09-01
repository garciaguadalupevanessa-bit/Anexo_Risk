# Backlog de Anexo Risk

> **Evolución de NEXO → Anexo Risk.** Mantenido por PM Juan. Repo actual: `garciaguadalupevanessa-bit/Anexo_Risk` — **solo `main` (bloqueada) + `anexo-risk` (rama única de integración)**. GitHub Flow `feat/*` → `main`. Última actualización: 2026-09-01 (audit `anexo-risk` 557f8f7). Legacy NEXO Sprint 1-2 preservado en `docs/legacy/`.
> Referencia de prioridades: `docs/manifiesto.md` y `docs/roadmap.md`.

## Estado por módulo

| Módulo | Prioridad | Rama(s) | PR | Dueño | Estado |
|--------|-----------|---------|----|-------|--------|
| Alertas + activación (G2) | Núcleo (MVP) | `anexo-risk` | `feat/javi-g2-alertas` → `main` | Javi | `backend/modules/alertas/*` + `zone` + `external_id` dedup — en `anexo-risk` (4f9f29f) |
| Necesidades (G1) | Núcleo (MVP) | `anexo-risk` | `feat/luis-g1-necesidades` → `main` | Luis | 8 cats/2 estados + `direccion` + `services.py` + `geocodificacion.js` — en `anexo-risk` (91a7647+). Ver `docs/equipos/reparto.md` |
| Ayudas (G3) | Núcleo (MVP) | `anexo-risk` | `feat/vanessa-g3-ayudas` → `main` | Vanessa | `voluntariado`+`donaciones` unificado `POST /api/ayudas` — `anexo-risk` |
| Mapa + Interfaz (G4) | Núcleo (MVP) | `anexo-risk` | `feat/juan-g4-mapa` → `main` | Juan | `mapa.html` + `mapaNecesidades.js` + `apiClient.js` + `mocks` + H3/globo post-MVP — `anexo-risk` |
| Personas / Offline | Siguiente | `main` | #20, #21 **MERGED** (legacy) | Vanessa/Juan | Backend en `main` (legacy NEXO); falta UI offline — Siguiente |
| Documentación y gobernanza | Transversal | `anexo-risk` → `main` | `anexo-risk` (557f8f7→`main`) | Juan (PM) | README Anexo Risk + logo + `equipos/reparto.md` (único, 4p con nombres) + ER — en `anexo-risk`, legacy en `docs/legacy/` |

> **Mapeo de grupos actualizado en Sprint 2 (reunión 27/08):** G1=Necesidades, G2=Alertas, G3=Ayudas, G4=Mapa + Interfaz principal. En Sprint 1 eran G1=Mapa de necesidades, G2=Alertas, G3=Voluntariado/Donaciones, G4=Personas/Offline. La sección "Trazabilidad Sprint 1" más abajo mantiene el detalle anterior para trazabilidad.

## PRs — Legacy NEXO (a `dev`, repo `adrianaarang/Nexo`) + Anexo Risk (actual)

| PR | Título | Estado |
|----|--------|--------|
| #18 | Feature/form cards (mapa E2E) | **MERGED** a `dev` |
| #19 / #26 / #28 | Alertas backend / fixes CORS+apiClient / refactor resiliente + stub PC | **MERGED** a `feature/alerts` |
| #20 | feat(personas): add estoy bien backend | **MERGED** a `dev` |
| #21 | feat(sync): offline synchronization backend (G4) | **MERGED** a `dev` |
| #22 | Integración necesidadesApi.js | **MERGED** a `dev` |
| #23 | fix(api): validation error format | **MERGED** a `dev` |
| #24 | feat(voluntariado): volunteer module | **MERGED** a `dev` |
| #25 | Añadir kanban del Equipo 1 | **MERGED** a `dev` |
| #27 | chore(voluntariado): config and support | **MERGED** a `dev` |
| #29 | feat(voluntariado): volunteer registration | **MERGED** a `dev` |
| #30 | feat(alertas): integrate alerts module into dev (Sprint 1) | **REVERTIDO** con #32 (dev vuelve a pre-alertas) |
| #32 | Revert "feat(alertas): integrate alerts module into dev" | **MERGED** a `dev` |
| #53 | docs(sprint2): align team/module mapping and regenerate Kanban (Sprint 2) | **MERGED** a `dev` (91a7647) — cierra #41/#43/#44 con trazabilidad |
| #55 | feature/forms-needs-elenadiaz1 | **MERGED** a `dev` (88019a1) |
| #56 | feat(necesidades): nueva_version/elena — 8 cats + direccion | **MERGED** a `dev` (4c3d244) |
| #61 | feat(necesidades): gema — rediseño 2 estados + services | **MERGED** a `dev` (91a7647) |
| `fix/base-comun`→dev | fix(base-comun): init_db, CORS and apiClient to boot dev | **MERGED** (vía #53 / ya en dev) |

## Tablero / Kanban (Sprint 2)

En Anexo Risk el Kanban se regenera con `scripts/setup-kanban.sh` (idempotente) al mergear a `main` (workflow `.github/workflows/setup-kanban.yml`, `main` bloqueada). Crea los epics por equipo y **cierra con trazabilidad** los issues de Sprint 1 obsoletos (#41, #43, #44) hacia su equivalente de Sprint 2. Cada epic se cierra al mergear `feat/*` → `main` si incluye `Closes #<num>`. Tablero Project V2 personal (agrupado por Label, columnas por Status). Composición en `docs/equipos/reparto.md` (4p, un archivo).

Mapeo Anexo Risk (4p, `anexo-risk` → `main`, GitHub Flow):

| Persona | Módulo | Rama | Estado |
|--------|--------|------|--------|
| Luis (P3) | Necesidades (G1) | `feat/luis-g1-necesidades` → `main` | Por hacer |
| Javi (P1) | Alertas + activación (G2) | `feat/javi-g2-alertas` → `main` | Por hacer |
| Vanessa (P4) | Ayudas (G3) | `feat/vanessa-g3-ayudas` → `main` | Por hacer |
| Juan (P2) | Mapa + Interfaz (G4) | `feat/juan-g4-mapa` → `main` | Por hacer |

> Los issues de Sprint 1 (#41 Equipo 1, #43 Equipo 3, #44 Equipo 4) se cierran al crear los de
> Sprint 2, con un comentario de trazabilidad hacia el nuevo issue.

### Sprint 1 (histórico) — issues originales del Kanban

> Snapshot 2026-08-25. El script de Sprint 2 cierra estos issues con trazabilidad:
> #41 → Equipo 1 - Necesidades, #43 → Equipo 3 - Ayudas, #44 → Equipo 4 - Mapa + Interfaz.

| # | Título (Sprint 1) | Label | Estado a 2026-08-25 |
|---|-------------------|-------|---------------------|
| #40 | Base comun - revision previa al reparto | base-comun, kanban | **CERRADO** |
| #41 | Equipo 1 - Mapa de necesidades | equipo-1, kanban | Abierto |
| #42 | Equipo 2 - Alertas oficiales | equipo-2, kanban | **CERRADO** |
| #43 | Equipo 3 - Voluntariado y donaciones | equipo-3, kanban | Abierto |
| #44 | Equipo 4 - Personas y modo offline | equipo-4, kanban | Abierto |
| #45 | Futuro - Resilience OS | futuro, kanban | Abierto |

## Objetivos MVP (de `docs/manifiesto.md`)
- [ ] O1 Alertas GDACS con filtros y estados (núcleo del Grupo 2) — feature/alerts (G2) listo, falta PR #56 a dev; base común en fix/base-comun
- [ ] O2 Mapa de necesidades end-to-end — en dev
- [ ] O3 Voluntariado/donaciones end-to-end — backend en dev; falta UI donaciones
- [ ] O4 E2E completo (frontend→API→BD) con CI verde — depende de #56 + fix/base-comun + CI en dev
- [ ] O5 PWA instalable con detección de conexión — offline backend en dev

## Trazabilidad Sprint 1 (entrega) — snapshot 2026-08-25

Resumen general del estado de los 4 equipos y la base común a fecha 2026-08-25, tras revertir #30 con #32. Se mantiene por trazabilidad; el estado actual está en "Estado por módulo" arriba.

| Equipo / Base | Módulo | Rama | PR a `dev` | Estado a 2026-08-25 |
|---------------|--------|------|-----------|---------------------|
| Base común | Arranque backend + CORS + apiClient | `fix/base-comun` | **ABIERTO** | `dev` roto tras #30; parche de 4 archivos pendiente de merge |
| Grupo 1 | Mapa de necesidades | `dev` | #18, #22, #25 **MERGED** | En `dev`, datos reales |
| Grupo 2 | Alertas oficiales (GDACS) | `feature/alerts` | #56 **ABIERTO** | G2-only, filtro país ES→EN corregido, tests verdes |
| Grupo 3 | Voluntariado y donaciones | `dev` | #24, #27, #29 **MERGED** | En `dev`; falta UI donaciones |
| Grupo 4 | Personas / "estoy bien" + offline | `dev` | #20, #21 **MERGED** | En `dev`; falta UI offline |
| PM / Docs | Estado y gobernanza | `feature/docs` | **ABIERTO** | Crea tablero Kanban al mergear |

> Nota histórica: sin respuesta de la integradora y entrega al día siguiente; `fix/base-comun` se mergeó después como parte de #53.

## Trazabilidad Sprint 2 (actual — `dev` en 91a7647)

| Equipo / Base | Módulo | Rama | PR a `dev` | Estado actual |
|---------------|--------|------|-----------|---------------|
| Base común | Arranque backend + CORS + apiClient | `dev` | #53 **MERGED** | En `dev`; `dev` arranca (init_db idempotente + CORS + apiClient) |
| Grupo 1 | Necesidades (8 cats, 2 estados) | `dev` | #61, #56 **MERGED** | En `dev`: rediseño 8 cats + `direccion` + `services.py` + geocodificación + 2 estados — merge 91a7647 |
| Grupo 2 | Alertas oficiales (GDACS) | `feature/alerts` | #56 (S1) — pendiente | Aún fuera de `dev` (G2-only tras revertir #30); PR #56 pendiente de integrar |
| Grupo 3 | Ayudas (voluntariado/donaciones) | `dev` | #24, #27, #29 **MERGED** | En `dev`; falta UI donaciones |
| Grupo 4 | Mapa + Interfaz principal | `dev` | #53 **MERGED** (docs) | En `dev`: `grupo4-tareas.md` creado; mapa consume contratos alertas/necesidades |
| PM / Docs | Estado y gobernanza | `dev` | #53 **MERGED** | ER + Kanban + docs S2 en `dev` |

## Pendientes de gobernanza (PM)
- [ ] Integrar `feature/alerts` (G2) a `dev` (PR #56 pendiente) — alertas aún fuera de `dev` tras revertir #30.
- [ ] Cerrar la UI offline en el frontend (backend ya en `dev` vía #21).
- [ ] Limpiar ramas duplicadas `feature/alerts-vanessa` / `fix/base-comun` (ya sin upstream, solo locales).
- [ ] Preparar Demo Day (narrativa alerta→mapa→necesidad→recurso→resolución).
- [x] Activar CI también en `dev` — hecho (workflow en `dev`, pendiente verificar checks).
- [x] Mergear `feature/docs → dev` — mergeado #53 en 91a7647 (crea tablero Kanban y deja README bilingüe oficial).
- [x] Decidir herramienta de backlog: Trello — decidido.
- [x] Reparto de tareas del Grupo 4 — creado `docs/equipos/grupo4-tareas.md` en Sprint 2.
- [x] Votar la convención bilingüe (README bilingüe oficial en `dev`).

## Abierto (por decidir)
- Zonas/celdas del mapa aún no definidas.
- Alcance exacto del modo offline (decisión abierta).
- Estrategia de despliegue (solo local hoy; CI sin despliegue).

## Riesgos
- **Alertas (G2, #56):** módulo aún fuera de `dev` (G2-only tras revertir #30). `fix/base-comun` ya mergeado vía #53, pero `feature/alerts` sigue pendiente de integrar a `dev`.
- **CI:** activado en `dev` (#53), pero `dev` sigue sin protección de branch con checks requeridos.
- **Rama duplicada:** `feature/alerts-vanessa` / `fix/base-comun` ya sin upstream; limpiar locales.
