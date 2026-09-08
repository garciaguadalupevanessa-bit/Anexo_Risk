"""Region-Source resolution service.

Determines which data sources are applicable for a given region
based on scope, capabilities, and region-source links.
"""
from modules.regiones import models as region_models
from modules.source_registry import models as source_models


def get_sources_for_region(region_id):
    """Get all applicable sources for a region.

    Resolution order:
    1. Explicit region→source links (from region_sources table)
    2. Scope matching (global sources always apply, country/Regional if matching)

    Returns list of sources with their configuration for this region.
    """
    region = region_models.get_region(region_id)
    if not region:
        return []

    # Get explicit links
    linked = region_models.get_region_sources(region_id)
    linked_ids = {ls["source_id"]: ls for ls in linked}

    # Get all active sources
    all_sources = source_models.list_sources(status="active")

    result = []
    for src in all_sources:
        config = linked_ids.get(src["id"], {})

        # Determine if source applies to this region
        if _source_applies_to_region(src, region, config):
            result.append({
                **src,
                "region_priority": config.get("priority", 0),
                "region_enabled": config.get("is_enabled", True),
                "region_config": config.get("config"),
            })

    # Sort by priority (explicit links first, then by scope hierarchy)
    result.sort(key=lambda s: (-s["region_priority"], _scope_order(s["scope"])))
    return result


def _source_applies_to_region(source, region, config):
    """Determine if a source applies to a region.

    Rules:
    - If explicitly linked, it applies (unless disabled)
    - Global sources always apply
    - Country sources apply if country_code matches
    - Regional sources apply if region matches
    - Local sources apply if parent hierarchy matches
    """
    # Explicit link takes precedence
    if config:
        return config.get("is_enabled", True)

    source_scope = source.get("scope", "global")

    # Global sources always apply
    if source_scope == "global":
        return True

    # Country sources match by country code (scope format: "country" or "country:XX")
    if source_scope.startswith("country") and region.get("country_code"):
        source_country = source_scope.split(":", 1)[1] if ":" in source_scope else source.get("country_code")
        return source_country == region.get("country_code")

    # Regional/local sources need explicit linking
    return False


def _scope_order(scope):
    """Sort scope for priority (lower = higher priority)."""
    order = {"global": 0, "country": 1, "regional": 2, "local": 3}
    return order.get(scope, 4)


def get_source_health_for_region(region_id):
    """Get health status of all sources applicable to a region."""
    sources = get_sources_for_region(region_id)
    return [
        {
            "id": s["id"],
            "name": s["name"],
            "scope": s["scope"],
            "status": s["status"],
            "last_successful_fetch": s.get("last_successful_fetch"),
            "last_failure": s.get("last_failure"),
            "latency_ms": s.get("latency_ms"),
            "region_priority": s.get("region_priority", 0),
        }
        for s in sources
    ]
