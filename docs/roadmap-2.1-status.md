# Roadmap 2.1 Status

**Last updated:** 2026-09-08
**Current phase:** FASE 2 Complete

---

## FASE 0 — Inventory & Classification
**Status:** COMPLETE
**Tests:** N/A (documentation)
**Notes:** 20 backend modules, 16 frontend modules, 22 DB tables classified as CORE/REGIONAL/LOCAL/LEGACY

## FASE 1 — Region/AOI Engine
**Status:** COMPLETE
**Tests:** 19 new tests
**Files:**
- `backend/db/migrations/021_regions.sql`
- `backend/modules/regiones/models.py`
- `backend/modules/regiones/schemas.py`
- `backend/modules/regiones/routes.py`
- `tests/backend/test_regiones.py`

## FASE 2 — Source Registry
**Status:** COMPLETE
**Tests:** 12 new tests
**Files:**
- `backend/db/migrations/022_source_registry.sql`
- `backend/modules/source_registry/models.py`
- `backend/modules/source_registry/schemas.py`
- `backend/modules/source_registry/routes.py`
- `backend/seed_sources.py`
- `tests/backend/test_source_registry.py`

## FASE 3 — Normalized Adapter Contract
**Status:** NOT STARTED
**Scope:** Common SourceAdapter interface (fetch, normalize, health, freshness, capabilities)

## FASE 4 — Spain Regional Sources
**Status:** NOT STARTED
**Scope:** AEMET deeper integration, Protección Civil real data, autonomic sources

## FASE 5 — Near-Real-Time Engine
**Status:** NOT STARTED
**Scope:** Polling, cache, retry, backoff, circuit breaker, freshness tracking

## FASE 6 — Event Correlation
**Status:** NOT STARTED
**Scope:** Multiple signals → single incident, distance/time/type correlation

## FASE 7 — H3 Operational Mesh
**Status:** NOT STARTED
**Scope:** Per-cell data aggregation, operational coverage metric

## FASE 8 — Operational Nodes
**Status:** NOT STARTED
**Scope:** Hospitals, fire stations, shelters, logistics bases

## FASE 9 — Network Links
**Status:** NOT STARTED
**Scope:** Roads, corridors, routes with status (open/blocked/restricted)

## FASE 10 — Accessibility/Routing
**Status:** NOT STARTED
**Scope:** Can a resource reach a need? Distance, time, blocking

## FASE 11 — Dynamic Action Area
**Status:** NOT STARTED
**Scope:** Per-incident action area based on hazard type, intensity, risk

## FASE 12 — Alert Policy / Dry Run
**Status:** NOT STARTED
**Scope:** Risk → policy → eligible entities → notification (dry-run first)

## FASE 13 — Federated Organizations
**Status:** NOT STARTED
**Scope:** Multi-org, RBAC expansion, region-scoped permissions

## FASE 14 — Live UX
**Status:** NOT STARTED
**Scope:** Region selector, source health dashboard, live indicators

## FASE 15 — Resilience / Security / Privacy
**Status:** NOT STARTED
**Scope:** Privacy policy, backup automation, security hardening

## FASE 16 — Pilot
**Status:** NOT STARTED
**Scope:** Real-world validation with emergency operators

---

## Total Test Count: 489 passing
