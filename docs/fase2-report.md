# FASE 2 — Vertical Slice Backend: Final Report

**Status:** COMPLETED
**Date:** 2026-09-07
**Tests:** 430 passed, 0 failures

---

## What Changed

### 1. Bug Fixes (prerequisite)
- **IncidentSeverity enum:** Default value `moderada` didn't exist in enum → changed to `amarilla` in `schemas.py`
- **OutcomeCreate forward ref:** `from __future__ import annotations` caused Pydantic resolution failure → explicit imports + `model_config = ConfigDict(protected_namespaces=())`
- **Incident models severity default:** `"moderada"` → `"amarilla"` for consistency

### 2. Vertical Slice Wiring (incident → decision → need → timeline)

**New endpoints in `/api/incidents`:**
| Endpoint | Method | Description |
|---|---|---|
| `/{id}/timeline` | GET | Timeline of events for an incident |
| `/{id}/analyze` | POST | Build decision context, update scores, record in timeline |
| `/{id}/needs` | POST | Create need linked to incident, record in timeline, update status |

**Incident creation now auto-records:**
- `detected` timeline event with severity and status snapshot

**Severity conversion:**
- Incidents store severity as string (`"verde"`, `"amarilla"`, `"naranja"`, `"roja"`)
- Decision engine expects float (0.25, 0.5, 0.75, 1.0)
- `SEVERITY_TO_FLOAT` mapping bridges the two formats
- `magnitude` defaults to 0.0 when None

### 3. Full Lifecycle Chain
```
POST /api/incidents (create)
  → auto: timeline event "detected"

POST /api/incidents/{id}/analyze
  → builds decision context (exposure, risk, ML, GeoRisk)
  → updates incident scores (priority_score, exposure_score)
  → auto: timeline event "evaluated"

POST /api/incidents/{id}/needs
  → creates necesidad linked to incident
  → auto: timeline event "need_created"
  → auto: updates incident status to "en_respuesta"
```

### 4. Outcome API (wraps feedback_loop)
- `POST /api/outcomes/prediction` — record prediction
- `PATCH /api/outcomes/{id}/record` — record outcome
- `GET /api/outcomes` — list entries
- `GET /api/outcomes/stats` — aggregate statistics

### 5. New Integration Tests (17 tests)
- `TestIncidentCreation` (4): create, H3, timeline, 404
- `TestIncidentAnalysis` (5): context, risk, timeline, scores, 404
- `TestNeedCreationFromIncident` (4): create, timeline, status, 404
- `TestFullVerticalSlice` (1): complete lifecycle E2E
- `TestOutcomesAPI` (3): prediction, list, stats

---

## Files Modified
- `backend/modules/incidentes/schemas.py` — severity default fix
- `backend/modules/incidentes/models.py` — severity default fix
- `backend/modules/incidentes/routes.py` — 3 new endpoints + severity mapping + timeline wiring
- `backend/modules/outcome/schemas.py` — protected_namespaces fix
- `backend/modules/outcome/routes.py` — explicit imports (no future annotations)
- `tests/backend/test_vertical_slice.py` — 17 new E2E tests

## Test Count
- **Before FASE 2:** 413 passing
- **After FASE 2:** 430 passing (+17 new)

## Known Limitations
- `severity` string→float conversion is simple mapping; could be more granular
- `magnitude` defaults to 0.0 — incidents without magnitude get lower impact scores
- Outcome API wraps feedback_loop directly; no independent outcome table yet
- `test_alertas.py` still has 19 pre-existing `_DB_LOCK` errors (excluded)

## Next Phase
**FASE 3:** Frontend vertical slice — map → incident selection → Decision Center → need → resource → assign → timeline
