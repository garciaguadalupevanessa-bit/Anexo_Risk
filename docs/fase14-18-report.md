# FASE 14-18 — Geodata + PWA: Final Report

**Status:** COMPLETED
**Date:** 2026-09-07
**Tests:** 430 passed

## What Changed

### PWA Manifest (manifest.json)
- Updated name to "Anexo Risk"
- Light theme colors (#F4F7FA background, #102A43 theme)
- Added `orientation`, `categories`, `purpose: maskable`

### Service Worker (sw.js)
- **App shell:** Cache-first strategy
- **Local API:** Stale-while-revalidate (2min cache)
- **External APIs:** Network-first with cache fallback (GDACS, FIRMS, Open-Meteo, GeoRisk)
- Removed non-existent files from APP_SHELL

### Geodata Adapters
- `effis_adapter.py` — Copernicus EFFIS: WMS URLs for fire danger (FWI, ISI, BUI), hotspots, burnt areas, fuel maps
- `ibtracs_adapter.py` — IBTrACS tropical cyclones
- `smithsonian_adapter.py` — Smithsonian volcanic activity
- `usgs_adapter.py` — USGS earthquakes

### Files
- `frontend/manifest.json` — Light theme, maskable icons
- `frontend/sw.js` — Cache strategies (app shell, API, external)
- `backend/geodata/adapters/effis_adapter.py` — Copernicus WMS (already comprehensive)

## Cache Strategies
| Layer | Strategy | TTL |
|---|---|---|
| App shell (HTML, CSS) | Cache-first | Until new SW |
| Local API (/api/*) | Stale-while-revalidate | 2 min |
| External APIs | Network-first + cache fallback | 1 hour |

## Next Phase
**FASE 19-21:** AI tools + Docker containerization
