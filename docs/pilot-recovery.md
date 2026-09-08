# Pilot Recovery Test Results

**Date:** 2026-09-07
**Environment:** Local development + Docker

## Test Scenarios

### 1. Backend Restart

**Procedure:** Kill uvicorn, wait 5s, restart.

**Result:** ✅ PASS
- App recovers immediately
- DB persists (SQLite file-based)
- No data loss
- Frontend shows offline indicator during downtime, reconnects automatically

### 2. GeoRisk Unavailable

**Procedure:** Stop GeoRisk Finder on port 8000.

**Result:** ✅ PASS
- Anexo_Risk continues fully operational
- Decision Center shows "GeoRisk no disponible" fallback
- Risk calculation uses rules-only mode
- No crashes or errors in logs
- Circuit breaker activates after 3 failed requests

### 3. External API Unavailable (GDACS)

**Procedure:** Block GDACS endpoint.

**Result:** ✅ PASS
- Alertas section shows last cached data
- Freshness indicator shows "Desactualizado"
- No crashes
- Other sections unaffected

### 4. External API Unavailable (NASA FIRMS)

**Procedure:** Block FIRMS endpoint.

**Result:** ✅ PASS
- Incendios layer shows cached data or empty
- Other layers unaffected
- Freshness indicator updated

### 5. Offline Client

**Procedure:** Disconnect network in browser.

**Result:** ✅ PASS (with limitations)
- App loads from service worker cache
- Map tiles cached for previously viewed areas
- API calls fail gracefully
- Status bar shows offline indicator
- Last visible state preserved
- Limitation: New map areas won't load offline

### 6. DB Issue (Corrupted SQLite)

**Procedure:** corrupt DB file, restart backend.

**Result:** ⚠️ DEGRADED
- Backend starts but queries fail
- Health endpoint reports `degraded` status
- Frontend shows error states
- Recovery: replace DB file and restart

### 7. Concurrent Writes

**Procedure:** 10 simultaneous incident creations.

**Result:** ✅ PASS
- All 10 succeed (SQLite serializes writes)
- No data corruption
- Response times acceptable (< 100ms each)

## Recovery Summary

| Scenario | Status | Data Loss | User Impact |
|---|---|---|---|
| Backend restart | ✅ PASS | None | Brief offline indicator |
| GeoRisk down | ✅ PASS | None | Reduced analysis |
| GDACS down | ✅ PASS | None | Stale alerts |
| FIRMS down | ✅ PASS | None | No fire data |
| Offline client | ✅ PASS | None | Read-only last state |
| DB corrupted | ⚠️ DEGRADED | Potential | Errors until fix |
| Concurrent writes | ✅ PASS | None | None |

## Recommendations

1. **DB backups:** Automated daily backup of `anexo_risk.db`
2. **Health monitoring:** Poll `/api/health` every 60s
3. **GeoRisk:** Circuit breaker already handles gracefully
4. **Offline:** Document that offline mode is read-only
5. **DB corruption:** Rare but requires manual intervention; document restore procedure
