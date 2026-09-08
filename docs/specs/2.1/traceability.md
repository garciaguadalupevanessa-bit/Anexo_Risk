# Traceability Matrix — FASES 4-7

**Date:** 2026-09-08

---

## FASE 4 — Region Sources

| Requirement | Spec | Code | Test | Documentation |
|---|---|---|---|---|
| REG-001: Region→source mapping | region-sources.md | `modules/regiones/models.py` | `test_regiones.py` | feature-inventory.md |
| REG-002: Source capabilities | region-sources.md | `modules/source_registry/models.py` | `test_source_registry.py` | architecture-2.1.md |
| REG-003: Region determines sources | region-sources.md | `modules/regiones/routes.py` | `test_regiones.py::test_sources` | region-sources.md |
| REG-004: Source health tracking | region-sources.md | `modules/source_registry/routes.py` | `test_source_registry.py::test_health_summary` | architecture-2.1.md |

---

## FASE 5 — Live Events

| Requirement | Spec | Code | Test | Documentation |
|---|---|---|---|---|
| LIVE-001: Scheduler polls sources | live-events.md | `services/live_ingestion.py` | `test_live_ingestion.py` | live-events.md |
| LIVE-002: Timeout handling | live-events.md | `services/live_ingestion.py` | `test_live_ingestion.py` | live-events.md |
| LIVE-003: Retry with backoff | live-events.md | `services/live_ingestion.py` | `test_live_ingestion.py` | live-events.md |
| LIVE-004: Circuit breaker | live-events.md | `services/live_ingestion.py` | `test_live_ingestion.py` | live-events.md |
| LIVE-005: Deduplication | live-events.md | `modules/normalized_events/models.py` | `test_normalized_events.py` | architecture-2.1.md |
| LIVE-006: Freshness tracking | live-events.md | `services/source_health.py` | `test_source_health.py` | live-events.md |

---

## FASE 6 — Event Correlation

| Requirement | Spec | Code | Test | Documentation |
|---|---|---|---|---|
| CORR-001: Distance correlation | event-correlation.md | `services/correlation.py` | `test_correlation.py` | event-correlation.md |
| CORR-002: Time window correlation | event-correlation.md | `services/correlation.py` | `test_correlation.py` | event-correlation.md |
| CORR-003: Type matching | event-correlation.md | `services/correlation.py` | `test_correlation.py` | event-correlation.md |
| CORR-004: Provenance preservation | event-correlation.md | `services/correlation.py` | `test_correlation.py` | event-correlation.md |
| CORR-005: Cross-border support | event-correlation.md | `services/correlation.py` | `test_correlation.py` | event-correlation.md |

---

## FASE 7 — H3 Operational Mesh

| Requirement | Spec | Code | Test | Documentation |
|---|---|---|---|---|
| H3-001: Event H3 indexing | h3-operational-mesh.md | `services/h3_mesh.py` | `test_h3_mesh.py` | h3-operational-mesh.md |
| H3-002: Region→H3 conversion | h3-operational-mesh.md | `services/h3_mesh.py` | `test_h3_mesh.py` | h3-operational-mesh.md |
| H3-003: Per-cell aggregation | h3-operational-mesh.md | `services/h3_mesh.py` | `test_h3_mesh.py` | h3-operational-mesh.md |
| H3-004: Spatial queries | h3-operational-mesh.md | `services/h3_mesh.py` | `test_h3_mesh.py` | h3-operational-mesh.md |
| H3-005: Coverage metric | h3-operational-mesh.md | `services/h3_mesh.py` | `test_h3_mesh.py` | h3-operational-mesh.md |
