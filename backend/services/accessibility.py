"""Accessibility / Routing service.

Determines if a resource can reach a need through the network graph.
Uses BFS through operational_nodes and network_links.
"""
from __future__ import annotations

import json
import logging
from collections import deque
from typing import Any

from db.database import get_cursor

logger = logging.getLogger(__name__)


def find_path(
    origin_id: str,
    destination_id: str,
    include_blocked: bool = False,
    max_hops: int = 10,
) -> dict[str, Any]:
    """Find shortest path between two nodes through the network graph.

    Uses BFS. Returns reachability, distance, time, and path.
    """
    if origin_id == destination_id:
        return {
            "origin": origin_id,
            "destination": destination_id,
            "is_reachable": True,
            "shortest_distance_km": 0.0,
            "shortest_time_min": 0.0,
            "path_link_ids": [],
            "hops": 0,
        }

    # Build adjacency list from network_links
    graph = _build_graph(exclude_blocked=not include_blocked)

    if origin_id not in graph:
        return _unreachable(origin_id, destination_id)

    # BFS
    visited = {origin_id}
    queue = deque([(origin_id, 0.0, 0.0, [])])

    while queue:
        current, dist, time, path = queue.popleft()
        if len(path) > max_hops:
            continue

        for neighbor, link_id, link_dist, link_time in graph.get(current, []):
            if neighbor == destination_id:
                return {
                    "origin": origin_id,
                    "destination": destination_id,
                    "is_reachable": True,
                    "shortest_distance_km": round(dist + link_dist, 2),
                    "shortest_time_min": round(time + link_time, 2),
                    "path_link_ids": path + [link_id],
                    "hops": len(path) + 1,
                }
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, dist + link_dist, time + link_time, path + [link_id]))

    return _unreachable(origin_id, destination_id)


def check_accessibility(
    origin_id: str,
    destination_id: str,
    include_blocked: bool = False,
) -> dict[str, Any]:
    """Check accessibility and cache result."""
    result = find_path(origin_id, destination_id, include_blocked)

    # Cache result
    try:
        with get_cursor() as cur:
            cur.execute(
                """INSERT OR REPLACE INTO accessibility_cache
                (origin_node_id, destination_node_id, is_reachable,
                 shortest_distance_km, shortest_time_min, path_link_ids_json,
                 blocking_count, computed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                (
                    origin_id, destination_id,
                    1 if result["is_reachable"] else 0,
                    result.get("shortest_distance_km"),
                    result.get("shortest_time_min"),
                    json.dumps(result.get("path_link_ids", [])),
                    _count_blocked_links(result.get("path_link_ids", [])),
                ),
            )
    except Exception as exc:
        logger.warning("Failed to cache accessibility: %s", exc)

    return result


def batch_accessibility(
    origin_ids: list[str],
    destination_ids: list[str],
    include_blocked: bool = False,
) -> list[dict[str, Any]]:
    """Check accessibility for multiple origin-destination pairs."""
    results = []
    for origin in origin_ids:
        for dest in destination_ids:
            if origin != dest:
                result = find_path(origin, dest, include_blocked)
                results.append(result)
    return results


def get_blocked_routes() -> list[dict[str, Any]]:
    """Get all currently blocked or restricted routes."""
    with get_cursor() as cur:
        rows = cur.execute(
            """SELECT id, name, link_type, status, start_node_id, end_node_id,
                      distance_km, estimated_time_min
            FROM network_links
            WHERE status IN ('blocked', 'restricted')
            ORDER BY name"""
        ).fetchall()
        return [dict(r) for r in rows]


def _build_graph(exclude_blocked: bool = True) -> dict[str, list]:
    """Build adjacency list from network_links.

    Returns {node_id: [(neighbor_id, link_id, distance_km, time_min), ...]}
    """
    graph: dict[str, list] = {}
    query = "SELECT * FROM network_links"
    if exclude_blocked:
        query += " WHERE status = 'open'"
    with get_cursor() as cur:
        rows = cur.execute(query).fetchall()
        for row in rows:
            d = dict(row)
            start = d.get("start_node_id")
            end = d.get("end_node_id")
            if not start or not end:
                continue
            link_id = d["id"]
            dist = d.get("distance_km") or 0.0
            time = d.get("estimated_time_min") or 0.0
            graph.setdefault(start, []).append((end, link_id, dist, time))
            graph.setdefault(end, []).append((start, link_id, dist, time))
    return graph


def _unreachable(origin_id: str, destination_id: str) -> dict[str, Any]:
    return {
        "origin": origin_id,
        "destination": destination_id,
        "is_reachable": False,
        "shortest_distance_km": None,
        "shortest_time_min": None,
        "path_link_ids": [],
        "hops": 0,
    }


def _count_blocked_links(path_link_ids: list[str]) -> int:
    """Count how many links in the path are blocked/restricted."""
    if not path_link_ids:
        return 0
    count = 0
    placeholders = ",".join("?" for _ in path_link_ids)
    with get_cursor() as cur:
        rows = cur.execute(
            f"SELECT status FROM network_links WHERE id IN ({placeholders})",
            path_link_ids,
        ).fetchall()
        for row in rows:
            if dict(row).get("status") in ("blocked", "restricted"):
                count += 1
    return count
