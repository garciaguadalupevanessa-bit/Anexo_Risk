# PostGIS Assessment — Anexo_Risk

**Date:** 2026-09-07  
**Status:** Analysis Complete  
**Recommendation:** NOT NEEDED (current phase)

---

## 1. Current Geospatial Implementation

### 1.1 What We Have

| Feature | Implementation | Limitation |
|---------|----------------|------------|
| Lat/Lon storage | `latitud`, `longitud` columns | No geometry type |
| H3 cells | Computed on-the-fly | Not stored in operational tables |
| Bounding box queries | `lat BETWEEN AND lon BETWEEN` | Approximation only |
| Radius queries | Bounding box + haversine post-filter | Inefficient |
| Nearest-neighbor | Sort by distance | No spatial index |
| Intersection | Not implemented | — |
| Containment | Not implemented | — |
| Area calculation | Not implemented | — |

### 1.2 H3 as Spatial Index

H3 is used as a **logical** spatial identifier, not a **physical** spatial index:

```python
# Current: compute H3 at query time
h3_index = latlon_to_h3(lat, lon, resolution=3)
# Then: query by H3 cell
WHERE h3_index = ?
```

This works for H3-based queries but doesn't support arbitrary spatial operations.

---

## 2. PostGIS Capabilities

### 2.1 Spatial Operations

| Operation | SQL Function | Use Case |
|-----------|--------------|----------|
| Intersection | `ST_Intersects(geom1, geom2)` | Find alerts in a zone |
| Containment | `ST_Contains(geom1, geom2)` | Find resources in a polygon |
| Nearest | `ST_Distance(geom1, geom2)` | Find nearest resource |
| Area | `ST_Area(geom)` | Calculate polygon area |
| Buffer | `ST_Buffer(geom, distance)` | Create radius polygon |
| Union | `ST_Union(geom1, geom2)` | Merge polygons |
| Difference | `ST_Difference(geom1, geom2)` | Subtract polygons |

### 2.2 Spatial Indexing

```sql
-- GiST index for spatial queries
CREATE INDEX idx_resources_geom ON resources USING GIST (geom);

-- Query: find resources within 10km
SELECT * FROM resources
WHERE ST_DWithin(geom, ST_MakePoint(-75.0, 6.0)::geography, 10000);
```

### 2.3 H3 + PostGIS

```sql
-- H3 cells as geometries
CREATE INDEX idx_h3_geom ON spatial_cells USING GIST (h3_to_geometry(h3_index));

-- Find all H3 cells that intersect a polygon
SELECT * FROM spatial_cells
WHERE ST_Intersects(h3_to_geometry(h3_index), ST_GeomFromText('POLYGON(...)'));
```

---

## 3. Current Queries That Could Use PostGIS

### 3.1 Operational Queries

| Query | Current Implementation | PostGIS Improvement |
|-------|----------------------|---------------------|
| Operational events | `lat BETWEEN AND lon BETWEEN` | `ST_DWithin(geom, center, radius)` |
| Operational needs | `lat BETWEEN AND lon BETWEEN` | `ST_DWithin(geom, center, radius)` |
| Operational resources | `lat BETWEEN AND lon BETWEEN` | `ST_DWithin(geom, center, radius)` |
| Operational summary | `lat BETWEEN AND lon BETWEEN` | `ST_DWithin(geom, center, radius)` |
| Operational h3 | `lat BETWEEN AND lon BETWEEN` | `ST_DWithin(geom, center, radius)` |

### 3.2 Benefit Analysis

| Benefit | Impact | Justification |
|---------|--------|---------------|
| More accurate radius queries | Low | Current bounding box + haversine is sufficient |
| Spatial joins (alerts ∩ needs) | Medium | Not currently needed |
| Containment (zone ∩ resources) | Medium | Not currently needed |
| Nearest-neighbor (closest resource) | Low | Current sort-by-distance is sufficient |
| Polygon queries (incident zones) | Low | `alertas.zone` is GeoJSON text, not geometry |

---

## 4. When PostGIS Would Be Needed

### 4.1 Trigger Conditions

| Trigger | Current Status | Threshold |
|---------|---------------|-----------|
| Need for spatial joins | Not implemented | When 2+ tables need spatial intersection |
| Need for containment queries | Not implemented | When "find resources in zone" is needed |
| Need for precise radius queries | Approximated | When bounding box approximation is insufficient |
| Need for polygon storage | Text only (`alertas.zone`) | When zone is used in queries |
| Need for spatial aggregation | Not implemented | When grouping by area is needed |
| Need for routing/distance matrix | Not implemented | When multi-stop routing is needed |

### 4.2 Use Cases

| Use Case | PostGIS Required | Current Solution |
|----------|-----------------|------------------|
| "Find alerts near me" | No | Bounding box + haversine |
| "Find resources in my zone" | Yes | Not implemented |
| "Which zone has most alerts?" | Yes | Not implemented |
| "Find nearest resource to need" | Optional | Sort by distance |
| "Show me alerts in this polygon" | Yes | Text search in `alertas.zone` |

---

## 5. Migration Cost

### 5.1 Schema Changes

```sql
-- Add geometry columns
ALTER TABLE resources ADD COLUMN geom GEOMETRY(Point, 4326);
ALTER TABLE necesidades ADD COLUMN geom GEOMETRY(Point, 4326);
ALTER TABLE alertas ADD COLUMN geom GEOMETRY(Point, 4326);

-- Migrate lat/lon → geometry
UPDATE resources SET geom = ST_SetSRID(ST_MakePoint(longitud, latitud), 4326);
UPDATE necesidades SET geom = ST_SetSRID(ST_MakePoint(longitud, latitud), 4326);
UPDATE alertas SET geom = ST_SetSRID(ST_MakePoint(longitud, latitud), 4326);

-- Create GiST indexes
CREATE INDEX idx_resources_geom ON resources USING GIST (geom);
CREATE INDEX idx_necesidades_geom ON necesidades USING GIST (geom);
CREATE INDEX idx_alertas_geom ON alertas USING GIST (geom);
```

### 5.2 Code Changes

| File | Change | Effort |
|------|--------|--------|
| `backend/db/database.py` | Add PostGIS extension | Low |
| `backend/modules/operational/routes.py` | Update spatial queries | High |
| `backend/geodata/services/h3_resolver.py` | Add H3↔geometry conversion | Medium |
| `backend/modules/geodata/routes.py` | Update spatial queries | Medium |
| Tests | Update all spatial tests | High |

**Total effort:** 3-5 days  
**Risk:** Medium (SQL dialect differences, geometry handling)

---

## 6. Recommendation

### 6.1 NOT NEEDED (Current Phase)

**Reasons:**
1. No current query requires true spatial operations
2. Bounding box + haversine is sufficient for current radius queries
3. H3 cells provide adequate spatial indexing for current use cases
4. No spatial joins or containment queries in production
5. Migration cost > operational benefit

### 6.2 WHEN to Consider

| Trigger | Action | Priority |
|---------|--------|----------|
| Need for spatial joins | Add PostGIS | High |
| Need for containment queries | Add PostGIS | High |
| Need for precise radius queries | Evaluate PostGIS | Medium |
| Need for polygon storage | Add PostGIS | Medium |
| Need for spatial aggregation | Add PostGIS | Medium |
| SQLite becomes insufficient | Migrate to PostgreSQL + PostGIS | High |

### 6.3 Alternative: Keep H3 + SQLite

H3 provides similar spatial indexing benefits to PostGIS for our use cases:

| Feature | H3 + SQLite | PostGIS |
|---------|-------------|---------|
| Spatial indexing | H3 cells (resolution 3) | GiST R-tree |
| Radius queries | H3 neighbors + haversine | ST_DWithin |
| Nearest-neighbor | H3 neighbors + sort | ST_Distance |
| Containment | Not supported | ST_Contains |
| Intersection | Not supported | ST_Intersects |

**H3 + SQLite is sufficient for current use cases.**

---

## 7. Conclusion

**PostGIS is NOT needed at this stage.**

- Current queries: bounding box + haversine is sufficient
- H3 cells: provide adequate spatial indexing
- No spatial joins or containment queries in production
- Migration cost: 3-5 days + ongoing maintenance
- Operational benefit: minimal (no current use case)

**Consider PostGIS when:**
1. Need for spatial joins (alerts ∩ needs)
2. Need for containment queries (resources in zone)
3. Need for precise radius queries (beyond bounding box approximation)
4. SQLite becomes insufficient (concurrent writes, scale)

Until then, **H3 + SQLite is the right choice.**
