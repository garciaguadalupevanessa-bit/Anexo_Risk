"""Network Links API endpoints."""
from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from modules.network_links import models as link_models
from modules.network_links.schemas import LinkCreate, LinkUpdate

router = APIRouter(prefix="/api/links", tags=["network-links"])


@router.post("", status_code=201)
def create_link(data: LinkCreate):
    """Create a new network link."""
    link_dict = data.model_dump()
    # Auto-compute H3 for endpoints
    from geodata.services.h3_resolver import latlon_to_h3
    if link_dict.get("start_lat") and link_dict.get("start_lon"):
        h3_s = latlon_to_h3(link_dict["start_lat"], link_dict["start_lon"])
        if h3_s:
            link_dict["h3_start"] = h3_s
    if link_dict.get("end_lat") and link_dict.get("end_lon"):
        h3_e = latlon_to_h3(link_dict["end_lat"], link_dict["end_lon"])
        if h3_e:
            link_dict["h3_end"] = h3_e
    # Auto-compute distance if endpoints provided
    if (link_dict.get("start_lat") and link_dict.get("start_lon")
            and link_dict.get("end_lat") and link_dict.get("end_lon")
            and not link_dict.get("distance_km")):
        from geodata.services.spatial import haversine_distance
        link_dict["distance_km"] = round(haversine_distance(
            link_dict["start_lat"], link_dict["start_lon"],
            link_dict["end_lat"], link_dict["end_lon"],
        ), 2)
    return link_models.create_link(link_dict)


@router.get("")
def list_links(
    link_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    start_node_id: Optional[str] = Query(None),
    end_node_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List network links."""
    links = link_models.list_links(
        link_type=link_type, status=status,
        start_node_id=start_node_id, end_node_id=end_node_id,
        limit=limit, offset=offset,
    )
    return {"count": len(links), "links": links}


@router.get("/count")
def count_links(
    link_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    """Count network links."""
    return {"count": link_models.count_links(link_type=link_type, status=status)}


@router.get("/node/{node_id}")
def get_links_for_node(node_id: str):
    """Get all links connected to a node."""
    links = link_models.get_links_for_node(node_id)
    return {"node_id": node_id, "count": len(links), "links": links}


@router.get("/{link_id}")
def get_link(link_id: str):
    """Get a single network link."""
    link = link_models.get_link(link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return link


@router.put("/{link_id}")
def update_link(link_id: str, data: LinkUpdate):
    """Update a network link."""
    link = link_models.get_link(link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    updates = data.model_dump(exclude_unset=True)
    if not updates:
        return link
    return link_models.update_link(link_id, updates)


@router.delete("/{link_id}")
def delete_link(link_id: str):
    """Close a network link (soft delete)."""
    link = link_models.get_link(link_id)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return link_models.delete_link(link_id)
