# Spec: Region Sources (FASE 4)

**ID:** REG-001
**Status:** READY FOR IMPLEMENTATION
**Phase:** 4

---

## Purpose

Enable Anexo_Risk to determine which data sources are relevant for a given active region, and to fetch/normalize data from those sources on demand.

## Scope

### IN
- Region → source mapping via `region_sources` table
- Source capabilities filtering (point, bbox, region)
- Spain as first reference region
- AEMET, NASA FIRMS, USGS, GDACS as primary sources
- Adapter contract compliance

### OUT
- Real Protección Civil API (stub only until verified)
- Autonomous community sources (future extension)
- Municipal sources (future extension)
- Source authentication management (keys stay in .env)

## Inputs

- Active region (from `/api/regions/active`)
- Source registry (`/api/sources`)
- Region-source links (`/api/regions/{id}/sources`)

## Outputs

- Filtered list of applicable sources for a region
- Normalized events from each source
- Source health status per region

## Invariants

1. Existing `/api/sources` endpoints remain unchanged
2. Existing `/api/regions` endpoints remain unchanged
3. Source registry seeded data preserved
4. No source is called without adapter implementation
5. All external data treated as untrusted

## Acceptance Criteria

| ID | Criterion | Verified by |
|---|---|---|
| REG-001-AC1 | `GET /api/regions/{id}/sources` returns applicable sources | test |
| REG-001-AC2 | Each source has capabilities (point, bbox, region) | test |
| REG-001-AC3 | Region determines which sources to poll | test |
| REG-001-AC4 | AEMET adapter fetches real data or documents limitation | manual |
| REG-001-AC5 | Source health is trackable | test |
| REG-001-AC6 | No existing tests broken | test suite |

## Failure Modes

| Mode | Behavior |
|---|---|
| Source unavailable | Return cached data or empty, mark DEGRADED |
| No sources for region | Return empty list, log warning |
| Adapter not implemented | Return source metadata only, no data fetch |
| API key missing | Log warning, skip source, mark DEGRADED |

## Security / Privacy

- API keys stored in `.env`, never in code or DB
- External data treated as untrusted
- No PII stored in source registry
- No secrets in logs

## Observability

- Source health updated after each fetch attempt
- Latency tracked per source
- Error messages logged
- Freshness calculated from last successful fetch

## Compatibility

- All existing `/api/sources` endpoints unchanged
- All existing `/api/regions` endpoints unchanged
- Seed data preserved

## Test Strategy

- Unit: source capabilities filtering
- Integration: region → source resolution
- API: endpoint contracts
- Resilience: source unavailable behavior
