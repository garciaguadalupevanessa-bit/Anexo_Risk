"""Seed the source registry with existing data sources."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
os.environ.setdefault("TESTING", "true")
os.environ.setdefault("JWT_SECRET_KEY", "seed-only")
os.environ.setdefault("ANEXO_ADMIN_KEY", "seed-only")

from modules.source_registry import models

SOURCES = [
    {
        "id": "gdacs",
        "name": "GDACS — Global Disaster Alerting Coordination System",
        "scope": "global",
        "source_type": "rss",
        "data_types": ["alerts", "earthquake", "flood", "fire", "cyclone", "volcano", "drought"],
        "supports_point": False,
        "supports_bbox": False,
        "supports_region": False,
        "update_interval_seconds": 900,
        "authentication": "none",
        "license": "Open — gdacs.org",
        "status": "active",
        "cache_ttl_seconds": 900,
        "endpoint_url": "https://www.gdacs.org/xml/rss.xml",
    },
    {
        "id": "firms",
        "name": "NASA FIRMS — Fire Information for Resource Management System",
        "scope": "global",
        "source_type": "api",
        "data_types": ["fire", "hotspot"],
        "supports_point": False,
        "supports_bbox": True,
        "supports_region": True,
        "update_interval_seconds": 300,
        "authentication": "api_key",
        "license": "Open — NASA",
        "status": "active",
        "cache_ttl_seconds": 3600,
        "endpoint_url": "https://firms.modaps.eosdis.nasa.gov/api/area/csv",
    },
    {
        "id": "usgs",
        "name": "USGS Earthquake Hazards Program",
        "scope": "global",
        "source_type": "csv",
        "data_types": ["earthquake"],
        "supports_point": False,
        "supports_bbox": False,
        "supports_region": False,
        "update_interval_seconds": 300,
        "authentication": "none",
        "license": "Open — USGS",
        "status": "active",
        "cache_ttl_seconds": 900,
        "endpoint_url": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/",
    },
    {
        "id": "effis",
        "name": "Copernicus EFFIS — European Forest Fire Information System",
        "scope": "regional",
        "source_type": "wms",
        "data_types": ["fire_danger", "hotspot", "burnt_area"],
        "supports_point": True,
        "supports_bbox": True,
        "supports_region": True,
        "update_interval_seconds": 3600,
        "authentication": "none",
        "license": "Open — Copernicus",
        "status": "active",
        "cache_ttl_seconds": 3600,
        "endpoint_url": "https://maps.effis.emergency.copernicus.eu/effis",
    },
    {
        "id": "open-meteo",
        "name": "Open-Meteo Weather API",
        "scope": "global",
        "source_type": "api",
        "data_types": ["weather", "forecast"],
        "supports_point": True,
        "supports_bbox": False,
        "supports_region": False,
        "update_interval_seconds": 900,
        "authentication": "none",
        "license": "Open — open-meteo.com",
        "status": "active",
        "cache_ttl_seconds": 900,
        "endpoint_url": "https://api.open-meteo.com/v1/forecast",
    },
    {
        "id": "aemet",
        "name": "AEMET OpenData — Agencia Estatal de Meteorología",
        "scope": "country",
        "source_type": "api",
        "data_types": ["weather", "alerts"],
        "supports_point": True,
        "supports_bbox": False,
        "supports_region": True,
        "update_interval_seconds": 300,
        "authentication": "api_key",
        "license": "Open — AEMET",
        "status": "active",
        "cache_ttl_seconds": 300,
        "endpoint_url": "https://opendata.aemet.es/opendata/api",
    },
    {
        "id": "georisk",
        "name": "GeoRisk Finder — Scientific Risk Analysis",
        "scope": "regional",
        "source_type": "api",
        "data_types": ["risk", "hazard", "exposure"],
        "supports_point": True,
        "supports_bbox": False,
        "supports_region": True,
        "update_interval_seconds": 300,
        "authentication": "none",
        "license": "Internal — Anexo ecosystem",
        "status": "active",
        "cache_ttl_seconds": 900,
        "endpoint_url": "http://localhost:8000",
    },
    {
        "id": "ibtracs",
        "name": "IBTrACS — International Best Track Archive",
        "scope": "global",
        "source_type": "csv",
        "data_types": ["cyclone"],
        "supports_point": False,
        "supports_bbox": False,
        "supports_region": False,
        "update_interval_seconds": 86400,
        "authentication": "none",
        "license": "Open — NOAA",
        "status": "active",
        "cache_ttl_seconds": 3600,
        "endpoint_url": "https://www.ncei.noaa.gov/data/international-best-track-archive-for-climate-stewardship-ibtracs/",
    },
    {
        "id": "smithsonian",
        "name": "Smithsonian Global Volcanism Program",
        "scope": "global",
        "source_type": "wfs",
        "data_types": ["volcano"],
        "supports_point": True,
        "supports_bbox": True,
        "supports_region": True,
        "update_interval_seconds": 86400,
        "authentication": "none",
        "license": "Open — Smithsonian",
        "status": "active",
        "cache_ttl_seconds": 86400,
        "endpoint_url": "https://volcano.si.edu/gvp_EWS.xml",
    },
]


def seed():
    for src in SOURCES:
        existing = models.get_source(src["id"])
        if existing:
            print(f"  [skip] {src['id']} already exists")
        else:
            models.register_source(src)
            print(f"  [ok]  {src['id']} registered")


if __name__ == "__main__":
    print("Seeding source registry...")
    seed()
    print("Done.")
