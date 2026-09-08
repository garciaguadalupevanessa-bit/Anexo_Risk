# Spec: Operational Nodes (FASE 8)

**ID:** NODE-001
**Status:** READY FOR IMPLEMENTATION
**Phase:** 8

---

## Purpose

Register and query operational infrastructure: hospitals, fire stations, shelters, logistics bases, warehouses, and command posts. These nodes are the physical backbone of emergency response.

## Scope

### IN
- Node CRUD (type, name, location, capacity, capabilities, status)
- Node types: hospital, fire_station, shelter, logistics_base, warehouse, command_post
- Spatial queries (nearby nodes, nodes by type)
- H3 indexing for nodes
- Capacity and capability tracking

### OUT
- Real-time occupancy tracking
- Supply chain management
- Staff scheduling
- Vehicle tracking

## Acceptance Criteria

| ID | Criterion | Verified by |
|---|---|---|
| NODE-001-AC1 | CRUD operations for nodes | test |
| NODE-001-AC2 | Spatial query returns nearby nodes | test |
| NODE-001-AC3 | Nodes indexed in H3 | test |
| NODE-001-AC4 | Filter by type and capability | test |
| NODE-001-AC5 | Capacity tracking works | test |

## Failure Modes

| Mode | Behavior |
|---|---|
| Invalid coordinates | Reject with 422 |
| Unknown node type | Reject with 400 |
| Duplicate node | Upsert by external_id |

## Security / Privacy

- Node locations are operational data, not PII
- No individual tracking
- Read access for all authenticated users
- Write access for coordinators+

## Test Strategy

- Unit: CRUD operations
- Integration: spatial queries with H3
- API: full endpoint coverage
- Edge: empty results, invalid inputs
