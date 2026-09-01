# Legacy — Evolución NEXO → Anexo Risk

> **Anexo Risk** no borra historia: es evolución de **NEXO** (Sprint 1-2, 16+ personas) + **GeoRisk Finder** (ML/H3). Este directorio preserva el legado como trazabilidad, separado del trabajo activo en `anexo-risk` (4p: Javi, Juan, Luis, Vanessa).

## Qué se conserva y por qué no es basura

| Legado | Dónde estaba | Por qué se guarda |
|---|---|---|
| **Sprint 1 — 6 categorías / 3 estados** (`agua/alimento/medicina...` + `abierta→en_proceso→cubierta`) | `001_init.sql` original, `schemas.py` v1 | Justifica migración `005_necesidades_redisenio.sql` (mapeo `alimento→alimentos`, `medicina→parafarmacia`, `en_proceso→abierta`) |
| **Sprint 1 — G1=Mapa, G3=Voluntariado/Donaciones, G4=Personas/Offline** | `backlog.md` #40-#45, `equipos.md` Sprint 1 | Justifica remapeo Sprint 2 G1=Necesidades, G3=Ayudas, G4=Mapa (reunión 27/08) |
| **ER original** | `modelo-entidad-relacion.md` v1 (sin `direccion`) | Fuente única antes de rediseño — ver `docs/legacy/modelo-sprint1.md` |
| **GeoRisk Streamlit** | `streamlit_app/` | Reemplazado por Jamstack Vercel (`api/index.py`), pero conserva lógica H3/globo |

## Estructura legacy

- `backlog-sprint1.md` — Snapshot `docs/backlog.md` a 2026-08-25 (PRs #18-#32, Kanban #40-#45)
- `modelo-sprint1.md` — `necesidades` sin `direccion`, 6 cats, 3 estados
- `equipos-sprint1.md` — 16+ personas (Josema, Gema, Helen, etc.) vs 4p actual

Activos actuales siempre en `docs/backlog.md` → `## Trazabilidad Sprint 2`, `docs/modelo-entidad-relacion.md`, `docs/equipos/reparto-anexo-risk-4p-*.md`.
