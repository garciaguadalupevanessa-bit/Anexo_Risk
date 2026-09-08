"""Live Dashboard service.

Aggregates operational status for the live UX: region overview,
source health, active incidents, node status, and network status.
"""
from __future__ import annotations

import json
import logging
from typing import Any
from datetime import datetime, timezone

from db.database import get_cursor

logger = logging.getLogger(__name__)


def get_live_dashboard(region_id: str | None = None) -> dict[str, Any]:
    """Get aggregated live dashboard data."""
    now = datetime.now(timezone.utc).isoformat()

    # Active incidents
    active_incidents = 0
    try:
        with get_cursor() as cur:
            incidents_row = cur.execute(
                "SELECT COUNT(*) as cnt FROM incidentes WHERE estado != 'resuelto'"
            ).fetchone()
            active_incidents = incidents_row["cnt"] if incidents_row else 0
    except Exception:
        pass

    # Active events
    with get_cursor() as cur:
        events_row = cur.execute(
            "SELECT COUNT(*) as cnt FROM normalized_events WHERE is_active = 1"
        ).fetchone()
        active_events = events_row["cnt"] if events_row else 0

    # Source health summary
    source_health = _get_source_health_summary()

    # Node status
    node_status = _get_node_status_summary()

    # Network status
    network_status = _get_network_status_summary()

    # H3 coverage
    h3_coverage = _get_h3_coverage_summary()

    return {
        "timestamp": now,
        "region_id": region_id,
        "active_incidents": active_incidents,
        "active_events": active_events,
        "source_health": source_health,
        "node_status": node_status,
        "network_status": network_status,
        "h3_coverage": h3_coverage,
    }


def _get_source_health_summary() -> dict[str, Any]:
    """Get summary of source health status."""
    with get_cursor() as cur:
        rows = cur.execute(
            """SELECT source, COUNT(*) as event_count,
                      MAX(timestamp) as last_event
            FROM normalized_events
            WHERE is_active = 1
            GROUP BY source"""
        ).fetchall()
        sources = []
        for row in rows:
            d = dict(row)
            sources.append({
                "source": d["source"],
                "event_count": d["event_count"],
                "last_event": d["last_event"],
            })
    return {"sources": sources, "total_sources": len(sources)}


def _get_node_status_summary() -> dict[str, Any]:
    """Get summary of operational node status."""
    with get_cursor() as cur:
        rows = cur.execute(
            """SELECT node_type, COUNT(*) as cnt,
                      SUM(capacity) as total_capacity,
                      SUM(current_occupancy) as total_occupancy
            FROM operational_nodes
            WHERE is_active = 1
            GROUP BY node_type"""
        ).fetchall()
        nodes = []
        for row in rows:
            d = dict(row)
            nodes.append({
                "type": d["node_type"],
                "count": d["cnt"],
                "total_capacity": d["total_capacity"] or 0,
                "total_occupancy": d["total_occupancy"] or 0,
            })
    total = sum(n["count"] for n in nodes)
    return {"by_type": nodes, "total_nodes": total}


def _get_network_status_summary() -> dict[str, Any]:
    """Get summary of network link status."""
    with get_cursor() as cur:
        rows = cur.execute(
            """SELECT status, COUNT(*) as cnt
            FROM network_links
            GROUP BY status"""
        ).fetchall()
        statuses = {}
        for row in rows:
            d = dict(row)
            statuses[d["status"]] = d["cnt"]
    total = sum(statuses.values())
    blocked = statuses.get("blocked", 0) + statuses.get("restricted", 0)
    return {
        "by_status": statuses,
        "total_links": total,
        "blocked_count": blocked,
        "open_count": statuses.get("open", 0),
    }


def _get_h3_coverage_summary() -> dict[str, Any]:
    """Get H3 coverage summary."""
    with get_cursor() as cur:
        cells_row = cur.execute(
            "SELECT COUNT(DISTINCT h3_index) as cnt FROM normalized_events WHERE is_active = 1 AND h3_index IS NOT NULL"
        ).fetchone()
        cells_with_data = cells_row["cnt"] if cells_row else 0
    return {"cells_with_data": cells_with_data}
