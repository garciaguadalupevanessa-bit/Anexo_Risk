# Database Scaling & Architecture Assessment — Anexo_Risk

**Date:** 2026-09-07  
**Status:** Analysis Complete  
**Recommendation:** Keep SQLite

---

## 1. SQLite vs PostgreSQL vs PostGIS Comparison

### 1.1 SQLite

| Criteria | Score | Notes |
|----------|-------|-------|
| Setup complexity | ✅ None | Single file, zero config |
| Local development | ✅ Perfect | No server needed |
| Current load | ✅ Excellent | 675 rows, single-user |
| Schema evolution | ✅ Good | Migrations via Python |
| Backup/restore | ✅ Simple | File copy |
| Geospatial | ⚠️ Approximated | Lat/lon BETWEEN, no ST_* |
| Full-text search | ⚠️ FTS5 possible | Not currently used |
| Concurrent writes | ❌ Poor | Serial writes, WAL helps |
| Replication | ❌ None | Single server only |
| PostGIS compatibility | ❌ None | Different SQL dialect |

**Verdict:** SQLite handles current and 24-month projected scale comfortably.

---

### 1.2 PostgreSQL

| Criteria | Score | Notes |
|----------|-------|-------|
| Setup complexity | ❌ High | Server, user, DB, extensions |
| Local development | ⚠️ Docker needed | Or local install |
| Current load | ⚠️ Overkill | 675 rows don't need a server |
| Schema evolution | ✅ Excellent | Rich migration tools |
| Backup/restore | ⚠️ Moderate | pg_dump, WAL archiving |
| Geospatial | ✅ PostGIS | Native spatial queries |
| Full-text search | ✅ tsvector | Native FTS |
| Concurrent writes | ✅ Excellent | MVCC, row-level locking |
| Replication | ✅ Built-in | Streaming, logical |
| PostGIS compatibility | ✅ Native | Same SQL dialect |

**Verdict:** PostgreSQL is superior in almost every way, but the operational cost is not justified at current scale.

---

### 1.3 PostGIS (PostgreSQL Extension)

| Criteria | Score | Notes |
|----------|-------|-------|
| Spatial queries | ✅ Native | ST_Intersects, ST_DWithin, ST_Contains |
| Spatial indexing | ✅ R-tree | GiST indexes |
| H3 support | ✅ h3-postgres | Direct H3 in SQL |
| Coordinate systems | ✅ Full | EPSG:4326, EPSG:3857, etc. |
| Geometry operations | ✅ Full | Area, distance, intersection |
| Complexity | ❌ High | Extension, functions, types |
| Current need | ❌ None | No spatial queries in production |

**Verdict:** PostGIS is unnecessary. No current query requires true spatial operations.

---

## 2. Scaling Analysis

### 2.1 Current Scale

| Metric | Value | SQLite Limit |
|--------|-------|--------------|
| Total rows | 675 | 2^64 (effectively unlimited) |
| Largest table | 619 (alertas) | 1 billion rows |
| Database file size | ~5 MB | 140 TB |
| Concurrent users | 1-5 | 1 writer at a time |
| Write rate | ~10-50 ops/hour | 100,000+ ops/sec |
| Read rate | ~100-500 ops/hour | Unlimited (concurrent reads) |

**SQLite is not a bottleneck.**

---

### 2.2 Growth Projections

| Table | Current | 6 months | 12 months | 24 months | SQLite Limit |
|-------|---------|----------|-----------|-----------|--------------|
| alertas | 619 | 5,000 | 20,000 | 100,000 | 2^64 |
| necesidades | 22 | 500 | 2,000 | 10,000 | 2^64 |
| resources | 7 | 50 | 200 | 1,000 | 2^64 |
| geodata_events | 0 | 10,000 | 50,000 | 200,000 | 2^64 |
| prediction_history | 0 | 1,000 | 5,000 | 20,000 | 2^64 |

**Even at 24-month projections, SQLite handles this scale.**

---

### 2.3 When SQLite Would Be Insufficient

| Condition | Current | Threshold | Action |
|-----------|---------|-----------|--------|
| Concurrent writers | 1 | >10 | Migrate to PostgreSQL |
| Total rows/table | 619 | >1M | Migrate to PostgreSQL |
| Database file size | 5 MB | >1 GB | Migrate to PostgreSQL |
| Spatial queries | None | Need ST_* | Migrate to PostGIS |
| Full-text search | None | Need tsvector | Migrate to PostgreSQL |
| Replication needed | No | Yes | Migrate to PostgreSQL |
| Multi-server | No | Yes | Migrate to PostgreSQL |

---

## 3. Migration Path

### 3.1 SQLite → PostgreSQL

| Step | Effort | Risk |
|------|--------|------|
| 1. Install PostgreSQL | Low | Low |
| 2. Create schema | Medium | Low |
| 3. Export SQLite data | Low | Low |
| 4. Import to PostgreSQL | Low | Low |
| 5. Update Python code (sqlite3 → psycopg2) | High | Medium |
| 6. Update connection strings | Low | Low |
| 7. Test | High | Medium |

**Estimated effort:** 2-3 days  
**Risk:** Medium (SQL dialect differences, transaction handling)

---

### 3.2 PostgreSQL → PostGIS

| Step | Effort | Risk |
|------|--------|------|
| 1. Enable PostGIS extension | Low | Low |
| 2. Add geometry columns | Medium | Low |
| 3. Migrate lat/lon → geometry | Medium | Low |
| 4. Create GiST indexes | Low | Low |
| 5. Update Python code (add geoalchemy2) | Medium | Low |
| 6. Update queries (ST_* functions) | High | Medium |
| 7. Test | High | Medium |

**Estimated effort:** 1-2 days  
**Risk:** Medium (SQL dialect differences, geometry handling)

---

## 4. Recommendation

### 4.1 KEEP SQLite (Current Phase)

**Reasons:**
1. Current scale is well within SQLite's capabilities
2. No operational need for concurrent writers
3. No need for true spatial queries
4. Zero operational cost (no server to manage)
5. Perfect for local development
6. Migration cost > operational benefit

### 4.2 WHEN to Consider Migration

| Trigger | Action | Priority |
|---------|--------|----------|
| >10 concurrent writers | PostgreSQL | High |
| >1M rows in any table | PostgreSQL | Medium |
| Need for spatial queries | PostGIS | Medium |
| Need for replication | PostgreSQL | High |
| Multi-server deployment | PostgreSQL | High |
| Full-text search (beyond FTS5) | PostgreSQL | Low |

### 4.3 Migration Effort

| From → To | Effort | Risk | Benefit |
|-----------|--------|------|---------|
| SQLite → PostgreSQL | 2-3 days | Medium | Concurrent writes, replication |
| PostgreSQL → PostGIS | 1-2 days | Low | True spatial queries |
| SQLite → PostGIS | 3-5 days | Medium | Both benefits |

---

## 5. SQLite Optimization (Current)

### 5.1 WAL Mode

```sql
PRAGMA journal_mode=WAL;
```

Already recommended in `db-backups.md`. Improves concurrent read performance.

### 5.2 Connection Pooling

```python
import sqlite3

# Single connection, serial writes
conn = sqlite3.connect('anexo_risk.db', timeout=30)

# WAL mode for concurrent reads
conn.execute('PRAGMA journal_mode=WAL')
```

### 5.3 Timeout Handling

```python
# Handle busy database
try:
    conn.execute('BEGIN IMMEDIATE')
except sqlite3.OperationalError:
    # Database is locked, retry
    time.sleep(0.1)
```

---

## 6. Conclusion

**SQLite is the right choice for Anexo_Risk at this stage.**

- Current scale: 675 rows (trivial)
- 24-month projection: <300,000 rows (trivial)
- Operational need: Single-server, single-writer
- Cost: Zero (SQLite) vs Moderate (PostgreSQL)

**Migration should only happen when a specific trigger is met** (see §4.2).
Until then, SQLite is simpler, cheaper, and faster to develop with.
