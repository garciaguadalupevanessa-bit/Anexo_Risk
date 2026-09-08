# Pilot Guide — Anexo_Risk v2.1

**Version:** 2.1.0
**Date:** 2026-09-08
**Target users:** Emergency operators and coordinators

---

## Quick Start

### 1. Start the Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 2. Start the Frontend

The frontend is served automatically by the backend at `http://localhost:8000`.

### 3. Seed Demo Data (Optional)

```bash
cd backend
python seed_sources.py  # Seed source registry
```

## Key Features for Pilot

### Map View
- **Layers:** Incidents, events, nodes, action areas, risk zones
- **Click** on any marker for details
- **Draw** on map to create incidents

### Incident Management
- Create incidents with coordinates and severity
- Auto-computed risk scores
- Timeline tracking
- Status workflow: detected → evaluated → assigned → delivered → resolved

### Source Health Dashboard
- Real-time source status (LIVE/FRESH/STALE/DEGRADED/UNAVAILABLE)
- Event counts per source
- Last event timestamp

### Live Dashboard
- Active incidents count
- Active events count
- Node status by type
- Network status (open/blocked)
- H3 coverage metric

### Action Areas
- Compute affected zones around incidents
- H3 cell coverage for spatial analysis
- Severity-adjusted radii

### Alert Policies (Dry Run)
- Create notification policies
- Evaluate against conditions
- See eligible nodes without sending notifications

## API Endpoints

### Core
- `GET /api/health` — System health check
- `GET /api/incidents` — List incidents
- `POST /api/incidents` — Create incident

### Regions
- `GET /api/regions` — List regions
- `POST /api/regions` — Create region

### Sources
- `GET /api/sources` — List sources
- `GET /api/sources/health` — Source health summary

### Live Data
- `POST /api/live/ingest` — Ingest from sources
- `GET /api/live/freshness` — Source freshness

### H3 Mesh
- `GET /api/h3/cells` — Cells in bbox
- `GET /api/h3/coverage` — Coverage metric

### Nodes
- `GET /api/nodes` — List operational nodes
- `POST /api/nodes` — Create node
- `GET /api/nodes/nearby` — Nearby nodes

### Links
- `GET /api/links` — List network links
- `POST /api/links` — Create link

### Accessibility
- `GET /api/accessibility/path` — Find path between nodes
- `POST /api/accessibility/batch` — Batch accessibility check

### Action Areas
- `POST /api/action-areas` — Compute action area
- `GET /api/action-areas/incident/{id}` — Areas for incident

### Alert Policies
- `POST /api/alert-policies` — Create policy
- `POST /api/alert-policies/{id}/evaluate` — Evaluate policy

### Dashboard
- `GET /api/live-dashboard` — Aggregated live status

## Pilot Scenarios

### Scenario 1: Wildfire Response
1. Source ingests FIRMS fire data
2. Auto-correlate nearby fire detections
3. Create incident from cluster
4. Compute action area (fire radius)
5. Check accessibility to nearest fire station
6. Create alert policy for nearby hospitals

### Scenario 2: Earthquake Response
1. Source ingests USGS earthquake data
2. Compute action area (100km radius)
3. Check accessibility to shelters
4. Evaluate alert policy for red severity
5. Track incident through resolution

### Scenario 3: Multi-Hazard
1. Multiple sources detect events in same region
2. Correlate events into single incident
3. Compute overlapping action areas
4. Check network status (blocked roads)
5. Find accessible resources

## Known Limitations

1. No real-time push notifications (polling only)
2. No user authentication in pilot mode
3. SQLite single-writer (not suitable for high concurrency)
4. No automated backup during pilot
5. External source APIs may be rate-limited

## Feedback

During pilot, collect feedback on:
1. Data accuracy
2. Response time
3. UI usability
4. Missing features
5. Error handling

Report issues to the development team.
