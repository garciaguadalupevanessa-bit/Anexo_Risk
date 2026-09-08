# Spec: H3 Operational Mesh (FASE 7)

**ID:** H3-001
**Status:** READY FOR IMPLEMENTATION
**Phase:** 7

---

## Purpose

Use H3 as the common spatial index to aggregate events, incidents, risk, exposure, needs, resources, and organizations per cell, enabling spatial queries and operational coverage metrics.

## Scope

### IN
- H3 indexing for all geolocated events
- Per-cell aggregation (events, incidents, risk, exposure)
- Region → H3 cell conversion
- Multi-municipal H3 representation
- Operational coverage metric
- Spatial queries (bbox, polygon, radius → H3 cells)

### OUT
- Real-time H3 streaming
- 3D visualization
- H3 resolution auto-adjustment
- Custom H3 hierarchies

## Inputs

- Normalized events with lat/lon
- Incidents with coordinates
- Regions with geometry/bbox
- H3 resolution from config (default: 3)

## Outputs

- H3 index on all geolocated events
- Per-cell aggregation endpoint
- Region → H3 cells mapping
- Operational coverage score

## Invariants

1. H3 resolution configurable per region
2. Existing H3 usage (risk engine, spatial) unchanged
3. H3 is spatial identifier, not replacement for geometry
4. Administrative borders are separate from H3 cells
5. Existing `/api/geodata/h3/*` endpoints unchanged

## Acceptance Criteria

| ID | Criterion | Verified by |
|---|---|---|
| H3-001-AC1 | Events have h3_index when geolocalized | test |
| H3-001-AC2 | Region converts to H3 cells | test |
| H3-001-AC3 | Per-cell aggregation returns counts | test |
| H3-001-AC4 | Cross-municipal incident maps to multiple cells | test |
| H3-001-AC5 | Spatial query (bbox) returns relevant cells | test |
| H3-001-AC6 | Existing H3 endpoints unchanged | test suite |
| H3-001-AC7 | Operational coverage metric calculable | test |

## Failure Modes

| Mode | Behavior |
|---|---|
| Invalid coordinates | Skip H3 indexing, log |
| H3 library error | Skip, store null h3_index |
| Too many cells | Limit aggregation results |

## Security / Privacy

- H3 cells are public geographic identifiers
- No PII in H3 aggregation
- No individual tracking via H3

## Observability

- H3 indexing success rate
- Cells with data count
- Aggregation query time
- Coverage metric calculation time

## Compatibility

- Existing H3 usage in risk engine preserved
- Existing spatial services preserved
- New H3 features are additive

## Test Strategy

- Unit: lat/lon → H3 conversion, aggregation
- Integration: event → H3 pipeline
- Spatial: bbox → cells, polygon → cells
- Edge cases: equator, poles, antimeridian
