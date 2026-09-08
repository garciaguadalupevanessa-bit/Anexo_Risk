# Spec: Event Correlation (FASE 6)

**ID:** CORR-001
**Status:** READY FOR IMPLEMENTATION
**Phase:** 6

---

## Purpose

Group related normalized events into coherent incidents, preserving provenance and supporting multi-jurisdictional events.

## Scope

### IN
- Correlation engine (distance, time, type, geometry)
- Incident creation from correlated events
- Multi-source incident composition
- Provenance preservation
- Confidence scoring
- Cross-border/municipal incident support

### OUT
- Automatic incident resolution
- ML-based correlation
- Real-time correlation (batch only for now)
- Alert generation from incidents

## Inputs

- Normalized events from `normalized_events` table
- H3 spatial index
- Configuration thresholds (distance, time window)

## Outputs

- Correlated incidents in `incidents` table
- Event → incident links
- Correlation metadata (confidence, method)

## Invariants

1. Original events never deleted by correlation
2. Provenance preserved for every event in an incident
3. An event can belong to at most one active incident
4. Correlation is deterministic (same inputs → same output)
5. Cross-border incidents are single coherent entities
6. Existing incident API unchanged

## Acceptance Criteria

| ID | Criterion | Verified by |
|---|---|---|
| CORR-001-AC1 | Two events within 50km and 2h of same type correlate | test |
| CORR-001-AC2 | Different event types do not correlate | test |
| CORR-001-AC3 | Provenance lists all contributing sources | test |
| CORR-001-AC4 | Cross-border incident is single entity | test |
| CORR-001-AC5 | Correlation confidence is calculated | test |
| CORR-001-AC6 | Existing incident CRUD unchanged | test suite |
| CORR-001-AC7 | Event not double-assigned to incidents | test |

## Failure Modes

| Mode | Behavior |
|---|---|
| No events match | No incident created |
| All events match | Single incident with all events |
| Ambiguous match | Highest confidence wins |
| DB error during correlation | Skip, log, retry next cycle |

## Security / Privacy

- Correlation operates on normalized events only
- No external API calls during correlation
- No PII in correlation metadata

## Observability

- Correlation run count
- Events correlated per run
- Incidents created per run
- Average confidence
- Processing time

## Compatibility

- Existing `/api/incidents` endpoints unchanged
- Existing incident model extended (not broken)
- New fields added to incident: `correlation_method`, `correlation_confidence`

## Test Strategy

- Unit: distance calculation, time window, type matching
- Integration: multi-event → incident pipeline
- Spatial: cross-border incident
- Edge cases: single event, no events, all same location
