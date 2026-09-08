# Integration Contract — Anexo_Risk ↔ GeoRisk Finder

**Version:** 1.0  
**Date:** 2026-09-07  
**Status:** Active

---

## 1. Overview

Anexo_Risk and GeoRisk Finder are two independent, complementary products:

- **GeoRisk Finder** → Scientific risk intelligence (H3, clustering, scenarios, ML)
- **Anexo_Risk** → Emergency operations (incidents, needs, resources, assignments, decisions)

When both services are available, they exchange data through a controlled JSON REST contract.  
When one is unavailable, the other continues operating normally with degraded capabilities.

---

## 2. Architecture Principles

```
GeoRisk Finder                    Anexo_Risk
= scientific analysis             = operational response

        ┌─────────────────┐
        │  H3 Cell Index  │  ← common spatial identifier
        └─────────────────┘
              ↕
    JSON REST API (optional)
```

- No shared databases
- No shared code imports
- No circular dependencies
- Request → Response pattern only
- Each service owns its data

---

## 3. Spatial Identity: H3

Both systems use H3 resolution 3 as the common spatial identifier.

**Conversion flow:**
```
Event (lat, lon)
  → h3.latlng_to_cell(lat, lon, res=3)
  → H3 cell ID (e.g., "832bffffffffff")
  → GeoRisk analysis
  → risk profile
  → Anexo_Risk Decision Center
```

**Resolution:** 3 (~12,500 km² per cell, ~12,500 global cells)

---

## 4. Endpoints

### 4.1 GeoRisk → Anexo_Risk

Anexo_Risk exposes operational data for GeoRisk consumption:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/operational/events` | Active alerts/incidents with coordinates |
| GET | `/api/operational/needs` | Open needs with spatial filters |
| GET | `/api/operational/resources` | Available resources with spatial filters |
| GET | `/api/operational/summary` | Aggregated operational metrics |
| GET | `/api/operational/h3/{h3_index}` | Per-cell operational metrics |
| GET | `/api/operational/feedback` | Prediction-outcome feedback records |
| GET | `/api/operational/feedback/stats` | Feedback aggregate statistics |

**Spatial filters (all endpoints):**
- `h3_index` — exact H3 cell match
- `bbox` — bounding box (lat_min,lon_min,lat_max,lon_max)
- `radius_km` + `center_lat` + `center_lon` — radius search
- `since` — ISO 8601 timestamp filter

### 4.2 Anexo_Risk → GeoRisk

GeoRisk exposes scientific analysis for operational consumption:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/external-risk/cell/{h3_index}` | Risk profile for H3 cell |
| GET | `/api/external-risk/cell/{h3_index}/events` | Nearby hazard events |
| GET | `/api/external-risk/ranking?limit=N` | Top risk cells |
| GET | `/api/external-risk/status` | Integration status |

---

## 5. Response Models

### 5.1 Cell Risk Profile

```json
{
  "h3_index": "832bffffffffff",
  "risk_score": 82.5,
  "risk_level": "high",
  "model_version": "georisk-v3",
  "cluster_id": 2,
  "cluster_label": "Zona sísmica activa",
  "features": {
    "eq_count": 45,
    "cyclone_count": 12,
    "volcano_count": 3,
    "exposure_index": 0.72
  },
  "explanation": "Alta actividad sísmica histórica...",
  "confidence": 0.85,
  "generated_at": "2026-09-07T12:00:00Z",
  "source": "georisk"
}
```

### 5.2 Scenario Data

```json
{
  "h3_index": "832bffffffffff",
  "scenarios": {
    "ssp126": { "risk_delta": -5.2, "description": "Mitigación moderada" },
    "ssp245": { "risk_delta": 2.1, "description": "Business as usual" },
    "ssp585": { "risk_delta": 12.8, "description": "Emisiones altas" }
  },
  "model_version": "georisk-v3",
  "generated_at": "2026-09-07T12:00:00Z"
}
```

### 5.3 Error Response

```json
{
  "error": "cell_not_found",
  "message": "H3 cell 832bffffffffff not found in grid",
  "source": "georisk",
  "timestamp": "2026-09-07T12:00:00Z"
}
```

---

## 6. Fallback Behavior

### When GeoRisk is unavailable:

Anexo_Risk operates normally using:
- Its own operational Risk Engine (rules-v1)
- Its own ML model (ml-v1)
- Local data only

Display:
```
GeoRisk: No disponible
Usando riesgo operacional local
```

### When Anexo_Risk is unavailable:

GeoRisk operates normally using:
- Its own scientific analysis
- H3 grid data
- Clustering and scenarios

Display:
```
Operational data: No disponible
Scientific datasets: Available
```

---

## 7. Caching

GeoRisk responses should be cached for 15 minutes in Anexo_Risk:

```python
cache_key = f"georisk:cell:{h3_index}"
cache_ttl = 900  # 15 minutes
```

---

## 8. Circuit Breaker

Anexo_Risk uses a circuit breaker pattern:

- **Closed** (normal): requests pass through
- **Open** (after 3 consecutive failures): skip GeoRisk for 60 seconds
- **Half-Open** (after 60s): allow 1 test request

---

## 9. Observability

Log every integration call:

```python
{
  "integration": "georisk",
  "endpoint": "/api/external-risk/cell/{h3}",
  "status": "success|error|timeout|circuit_open",
  "latency_ms": 120,
  "cache_hit": false,
  "source_timestamp": "2026-09-07T12:00:00Z"
}
```

---

## 10. Ownership

| Data | Owner |
|------|-------|
| Operational incidents | Anexo_Risk |
| Operational needs | Anexo_Risk |
| Operational resources | Anexo_Risk |
| Operational assignments | Anexo_Risk |
| Scientific risk scores | GeoRisk Finder |
| H3 grid features | GeoRisk Finder |
| Clustering labels | GeoRisk Finder |
| Climate scenarios | GeoRisk Finder |
| ML models | GeoRisk Finder |
