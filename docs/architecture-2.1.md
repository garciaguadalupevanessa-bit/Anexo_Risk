# Architecture 2.1 — Region/AOI + Source Registry

**Date:** 2026-09-08
**Status:** FASE 1-2 Complete

---

## Overview

Anexo_Risk 2.1 evolves from a single-territory emergency platform to a **multi-territory, multi-source, live situational awareness system**.

---

## New Components

### 1. Region/AOI Engine (`/api/regions`)

**Purpose:** Define and manage geographic areas of interest.

**Hierarchy:**
```
WORLD
  ↓
COUNTRY
  ↓
REGION
  ↓
PROVINCE
  ↓
MUNICIPALITY
  ↓
LOCALITY
  ↓
POINT / RADIUS / CUSTOM
```

**Database:** `regions` table with geometry, bbox, center, H3 resolution, parent hierarchy, source linking.

**Key features:**
- Create regions at any level (world → municipality → custom polygon)
- Link sources to regions (which sources are relevant for which area)
- Parent-child hierarchy (Comunidad de Madrid → Madrid City → Alcobendas)
- Active region concept (current operational context)
- Geometry support (Point, Polygon, BBox, Radius)

### 2. Source Registry (`/api/sources`)

**Purpose:** Central catalog of all data sources with health monitoring.

**Database:** `source_registry` table with scope, capabilities, authentication, health status.

**Key features:**
- Register sources with metadata (scope, data types, capabilities)
- Track health: last successful fetch, latency, errors
- Source health dashboard (`/api/sources/health`)
- Link sources to regions via `region_sources` junction table

**Existing sources seeded:**
| ID | Name | Scope | Types |
|---|---|---|---|
| gdacs | GDACS | global | alerts, earthquake, flood, fire, cyclone, volcano |
| firms | NASA FIRMS | global | fire, hotspot |
| usgs | USGS | global | earthquake |
| effis | Copernicus EFFIS | regional | fire_danger, hotspot, burnt_area |
| open-meteo | Open-Meteo | global | weather, forecast |
| aemet | AEMET | country:ES | weather, alerts |
| georisk | GeoRisk Finder | regional | risk, hazard, exposure |
| ibtracs | IBTrACS | global | cyclone |
| smithsonian | Smithsonian GVP | global | volcano |

---

## Data Flow

```
Region Selected
    ↓
Source Registry → Active Sources for Region
    ↓
Poll Sources → Normalize → Store
    ↓
Event Correlation
    ↓
Incidents
    ↓
Risk + Exposure
    ↓
Action Areas
    ↓
Needs + Resources
    ↓
Coordination
```

---

## API Endpoints

### Regions
| Method | Path | Description |
|---|---|---|
| GET | `/api/regions` | List all regions |
| GET | `/api/regions/active` | Get active region |
| GET | `/api/regions/{id}` | Get region by ID |
| POST | `/api/regions` | Create region |
| PATCH | `/api/regions/{id}` | Update region |
| DELETE | `/api/regions/{id}` | Soft-delete region |
| GET | `/api/regions/{id}/children` | Get child regions |
| GET | `/api/regions/{id}/sources` | Get sources for region |
| POST | `/api/regions/{id}/sources` | Link source to region |
| DELETE | `/api/regions/{id}/sources/{sid}` | Unlink source |

### Sources
| Method | Path | Description |
|---|---|---|
| GET | `/api/sources` | List all sources |
| GET | `/api/sources/health` | Get health summary |
| GET | `/api/sources/{id}` | Get source by ID |
| POST | `/api/sources` | Register source |
| PATCH | `/api/sources/{id}` | Update source |
| DELETE | `/api/sources/{id}` | Remove source |
| POST | `/api/sources/{id}/status` | Update health status |

---

## Migration History

| Migration | Purpose |
|---|---|
| 001-020 | v2.0.0 schema |
| 021 | Region/AOI engine |
| 022 | Source registry |

---

## Test Coverage

| Module | Tests |
|---|---|
| Region/AOI | 19 tests (schemas, API, models) |
| Source Registry | 12 tests (API, models) |
| **Total** | 489 tests passing |
