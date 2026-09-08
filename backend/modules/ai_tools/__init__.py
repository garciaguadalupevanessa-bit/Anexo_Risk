"""AI Tools — LLM tool-calling endpoints for Anexo Risk.

Provides structured data access for LLM agents:
- get_alerts: Query active alerts
- get_incidents: Query incidents
- get_needs: Query needs by status
- get_resources: Query resources
- get_nearby_resources: Find resources near a point
- get_weather: Get weather for a point
- get_exposure: Get exposure data for a point
- get_risk: Get risk assessment for a point
- get_timeline: Get incident timeline

Each tool is a FastAPI router with JSON schema responses.
"""
from __future__ import annotations

from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter(prefix="/api/ai", tags=["AI Tools"])


@router.get("/tools")
def list_tools():
    """List available AI tools."""
    return {
        "tools": [
            {
                "name": "get_alerts",
                "description": "Query active disaster alerts from GDACS and other sources",
                "parameters": {"type": "object", "properties": {"category": {"type": "string"}}},
            },
            {
                "name": "get_incidents",
                "description": "Query incidents with optional status filter",
                "parameters": {"type": "object", "properties": {"status": {"type": "string"}}},
            },
            {
                "name": "get_needs",
                "description": "Query humanitarian needs by status",
                "parameters": {"type": "object", "properties": {"status": {"type": "string"}, "severity": {"type": "string"}}},
            },
            {
                "name": "get_resources",
                "description": "Query available resources",
                "parameters": {"type": "object", "properties": {"type": {"type": "string"}, "status": {"type": "string"}}},
            },
            {
                "name": "get_nearby_resources",
                "description": "Find resources near a geographic point",
                "parameters": {"type": "object", "properties": {"lat": {"type": "number"}, "lon": {"type": "number"}, "radius_km": {"type": "number"}}},
            },
            {
                "name": "get_weather",
                "description": "Get current weather for a point from Open-Meteo",
                "parameters": {"type": "object", "properties": {"lat": {"type": "number"}, "lon": {"type": "number"}}},
            },
            {
                "name": "get_exposure",
                "description": "Get exposure data (population, infrastructure) for a point",
                "parameters": {"type": "object", "properties": {"lat": {"type": "number"}, "lon": {"type": "number"}}},
            },
            {
                "name": "get_risk",
                "description": "Get deterministic risk assessment for a point",
                "parameters": {"type": "object", "properties": {"lat": {"type": "number"}, "lon": {"type": "number"}}},
            },
            {
                "name": "get_timeline",
                "description": "Get timeline of events for an incident",
                "parameters": {"type": "object", "properties": {"incident_id": {"type": "integer"}}},
            },
        ]
    }


@router.get("/tools/{tool_name}")
def get_tool_schema(tool_name: str):
    """Get JSON schema for a specific tool."""
    schemas = {
        "get_alerts": {
            "name": "get_alerts",
            "description": "Query active disaster alerts",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": "Filter by category (earthquake, flood, fire, etc.)"},
                    "limit": {"type": "integer", "description": "Max results (default 20)"},
                },
            },
        },
        "get_incidents": {
            "name": "get_incidents",
            "description": "Query incidents",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Filter by status (abierto, en_progreso, resuelto)"},
                    "severity": {"type": "string", "description": "Filter by severity (verde, amarilla, naranja, roja)"},
                    "limit": {"type": "integer"},
                },
            },
        },
        "get_needs": {
            "name": "get_needs",
            "description": "Query humanitarian needs",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "description": "Filter by status (abierta, cubierta, cancelada)"},
                    "severity": {"type": "string"},
                    "limit": {"type": "integer"},
                },
            },
        },
        "get_resources": {
            "name": "get_resources",
            "description": "Query available resources",
            "parameters": {
                "type": "object",
                "properties": {
                    "type": {"type": "string", "description": "Filter by type (medico, logistico, humano)"},
                    "status": {"type": "string", "description": "Filter by status (disponible, asignado, agotado)"},
                    "limit": {"type": "integer"},
                },
            },
        },
        "get_nearby_resources": {
            "name": "get_nearby_resources",
            "description": "Find resources near a point",
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number", "description": "Latitude"},
                    "lon": {"type": "number", "description": "Longitude"},
                    "radius_km": {"type": "number", "description": "Search radius in km (default 50)"},
                },
                "required": ["lat", "lon"],
            },
        },
        "get_weather": {
            "name": "get_weather",
            "description": "Get current weather from Open-Meteo",
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number"},
                    "lon": {"type": "number"},
                },
                "required": ["lat", "lon"],
            },
        },
        "get_exposure": {
            "name": "get_exposure",
            "description": "Get exposure data for a point",
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number"},
                    "lon": {"type": "number"},
                },
                "required": ["lat", "lon"],
            },
        },
        "get_risk": {
            "name": "get_risk",
            "description": "Get deterministic risk assessment",
            "parameters": {
                "type": "object",
                "properties": {
                    "lat": {"type": "number"},
                    "lon": {"type": "number"},
                },
                "required": ["lat", "lon"],
            },
        },
        "get_timeline": {
            "name": "get_timeline",
            "description": "Get timeline of an incident",
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id": {"type": "integer"},
                },
                "required": ["incident_id"],
            },
        },
    }
    if tool_name not in schemas:
        return {"error": f"Tool '{tool_name}' not found"}
    return schemas[tool_name]
