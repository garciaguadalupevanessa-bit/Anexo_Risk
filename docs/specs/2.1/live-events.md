# Spec: Live Events (FASE 5)

**ID:** LIVE-001
**Status:** READY FOR IMPLEMENTATION
**Phase:** 5

---

## Purpose

Enable Anexo_Risk to automatically poll data sources, normalize incoming events, deduplicate, store, and expose freshness status to the UI.

## Scope

### IN
- Background polling scheduler (in-process, no external queue)
- Per-source configurable intervals
- Cache with TTL
- Timeout and retry with backoff
- Circuit breaker per source
- Freshness tracking per source
- Normalized event storage
- Deduplication by external_id + source

### OUT
- WebSocket/SSE push to frontend (future)
- Distributed workers
- Message queues
- Real-time streaming

## Inputs

- Source registry (intervals, endpoints, capabilities)
- Region active sources
- External API responses

## Outputs

- Normalized events in `normalized_events` table
- Source health status in `source_registry`
- Freshness indicators for UI

## Invariants

1. Existing API endpoints unchanged
2. No source polled more frequently than configured
3. No duplicate events stored (dedup by external_id + source)
4. All events have provenance
5. Backend continues if one source fails
6. No PII in analytics or events

## Acceptance Criteria

| ID | Criterion | Verified by |
|---|---|---|
| LIVE-001-AC1 | Scheduler polls sources at configured intervals | test |
| LIVE-001-AC2 | Timeout prevents hanging on slow sources | test |
| LIVE-001-AC3 | Retry with backoff on transient errors | test |
| LIVE-001-AC4 | Circuit breaker opens after 3 failures | test |
| LIVE-001-AC5 | Dedup prevents duplicate events | test |
| LIVE-001-AC6 | Freshness is calculable per source | test |
| LIVE-001-AC7 | Backend starts clean if a source is down | test |
| LIVE-001-AC8 | No existing tests broken | test suite |

## Failure Modes

| Mode | Behavior |
|---|---|
| Source timeout | Retry 3x, then mark DEGRADED |
| Source returns invalid data | Skip, log, count error |
| Network unavailable | Use cache, mark STALE |
| Circuit breaker open | Skip source for 60s, then half-open |
| DB write fails | Log, skip event, continue |

## Security / Privacy

- API keys never logged
- External data sanitized before storage
- No PII extracted from external sources
- Rate limiting respected per source

## Observability

- Ingestion count per source per cycle
- Error count per source
- Latency per fetch
- Circuit breaker state changes
- Freshness age per source

## Compatibility

- All existing endpoints unchanged
- `normalized_events` table is new, no conflicts
- Source registry unchanged

## Test Strategy

- Unit: scheduler logic, dedup, freshness calculation
- Integration: poll → normalize → store pipeline
- Resilience: timeout, circuit breaker, retry
- API: freshness endpoint
