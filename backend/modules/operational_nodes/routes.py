"""Operational Nodes API endpoints."""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from modules.operational_nodes import models as node_models
from modules.operational_nodes.schemas import NodeCreate, NodeUpdate
from services.h3_mesh import index_event, cells_in_radius

router = APIRouter(prefix="/api/nodes", tags=["operational-nodes"])


@router.post("", status_code=201)
def create_node(data: NodeCreate):
    """Create a new operational node."""
    node_dict = data.model_dump()
    # Auto-index H3 if lat/lon provided
    if node_dict.get("lat") and node_dict.get("lon") and not node_dict.get("h3_index"):
        from geodata.services.h3_resolver import latlon_to_h3
        h3_idx = latlon_to_h3(node_dict["lat"], node_dict["lon"])
        if h3_idx:
            node_dict["h3_index"] = h3_idx
    return node_models.create_node(node_dict)


@router.get("")
def list_nodes(
    node_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    country_code: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List operational nodes."""
    nodes = node_models.list_nodes(
        node_type=node_type, status=status, country_code=country_code,
        limit=limit, offset=offset,
    )
    return {"count": len(nodes), "nodes": nodes}


@router.get("/count")
def count_nodes(
    node_type: Optional[str] = Query(None),
):
    """Count operational nodes."""
    return {"count": node_models.count_nodes(node_type=node_type)}


@router.get("/nearby")
def get_nearby_nodes(
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(50, ge=0.1, le=500),
    node_type: Optional[str] = Query(None),
):
    """Get operational nodes within a radius using H3 grid_disk."""
    from geodata.services.h3_resolver import latlon_to_h3, H3_RESOLUTION, get_h3_neighbors
    from services.h3_mesh import _approx_km_per_ring
    from db.database import get_cursor

    center_h3 = latlon_to_h3(lat, lon, H3_RESOLUTION)
    if not center_h3:
        return {"center": {"lat": lat, "lon": lon}, "radius_km": radius_km, "count": 0, "nodes": []}

    km_per_ring = _approx_km_per_ring(H3_RESOLUTION)
    k = max(1, int(radius_km / km_per_ring))
    ring_cells = get_h3_neighbors(center_h3, k) or [center_h3]

    nodes = []
    if ring_cells:
        with get_cursor() as cur:
            placeholders = ",".join("?" for _ in ring_cells)
            query = f"SELECT * FROM operational_nodes WHERE h3_index IN ({placeholders}) AND is_active = 1"
            params = list(ring_cells)
            if node_type:
                query += " AND node_type = ?"
                params.append(node_type)
            rows = cur.execute(query, params).fetchall()
            nodes = [node_models._row_to_response(r) for r in rows]

    return {
        "center": {"lat": lat, "lon": lon},
        "radius_km": radius_km,
        "count": len(nodes),
        "nodes": nodes,
    }


@router.get("/{node_id}")
def get_node(node_id: str):
    """Get a single operational node."""
    node = node_models.get_node(node_id)
    if not node or not node.get("is_active"):
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.put("/{node_id}")
def update_node(node_id: str, data: NodeUpdate):
    """Update an operational node."""
    node = node_models.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        return node
    return node_models.update_node(node_id, updates)


@router.delete("/{node_id}")
def delete_node(node_id: str):
    """Soft-delete an operational node."""
    node = node_models.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node_models.delete_node(node_id)
