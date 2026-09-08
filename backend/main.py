"""Punto de arranque del backend de Anexo Risk (FastAPI).

Parte de la base común: registra los routers de cada módulo, CORS y
manejo de errores. Los equipos NO deberían tener que tocar este
archivo salvo para registrar un router nuevo si crean un módulo.

uvicorn main:app --reload --port 8000
"""
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Obtener la ruta del directorio base del Backend
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"

# Inicializar la configuración de logs antes de importar otros módulos 
from middleware.logging_config import setup_logging

setup_logging()

from config import CORS_ORIGINS
from db.database import init_db
from middleware.error_handler import registrar_manejadores_de_error

from modules.necesidades.routes import router as necesidades_router
from modules.alertas.routes import router as alertas_router
from modules.voluntariado.routes import router as voluntariado_router
from modules.donaciones.routes import router as donaciones_router
from modules.personas.routes import router as personas_router
from modules.incendios.routes import router as incendios_router
from modules.clima.routes import router as clima_router
from sync.sync_controller import router as sync_router
from modules.organizaciones.routes import router as organizaciones_router
from modules.recursos.routes import router as recursos_router
from geodata.routes import router as geodata_router
from modules.decision_center.routes import router as decision_router
from modules.asignaciones.routes import router as asignaciones_router
from modules.external_risk.routes import router as external_risk_router
from modules.operational.routes import router as operational_router
from modules.incidentes.routes import router as incidentes_router
from modules.timeline.routes import router as timeline_router
from modules.outcome.routes import router as outcome_router
from modules.ai_tools import router as ai_tools_router
from middleware.rate_limit import RateLimitMiddleware

app = FastAPI(
    title="Anexo Risk API",
    description="Plataforma de respuesta a emergencias con mapa, alertas, necesidades y ayudas en tiempo real.",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware, requests_per_minute=120)

registrar_manejadores_de_error(app)

app.include_router(necesidades_router)     # Equipo 1 — núcleo
app.include_router(alertas_router)         # Equipo 2 — núcleo
app.include_router(voluntariado_router)    # Equipo 3 — núcleo
app.include_router(donaciones_router)      # Equipo 3 — núcleo
app.include_router(personas_router)        # Equipo 4 — siguiente prioridad
app.include_router(incendios_router)       # NASA FIRMS — incendios satélite
app.include_router(clima_router)           # AEMET + Open-Meteo — meteorología
app.include_router(sync_router)            # Equipo 4 — siguiente prioridad (modo offline)
app.include_router(organizaciones_router)  # Fase B — modelo de producto
app.include_router(recursos_router)        # Fase B — gestión de recursos
app.include_router(geodata_router)         # Fase C — GeoData Engine
app.include_router(decision_router)       # Fase D — Centro de Decisión
app.include_router(asignaciones_router)   # Fase C — Asignación de recursos a necesidades
app.include_router(external_risk_router)  # Fase D — GeoRisk Finder integration
app.include_router(operational_router)   # Fase D — Operational data for GeoRisk
app.include_router(incidentes_router)    # Fase 2 — Incidents (vertical slice entry point)
app.include_router(timeline_router)      # Fase 2 — Timeline events
app.include_router(outcome_router)       # Fase 2 — Outcome tracking
app.include_router(ai_tools_router)     # Fase 19-21 — AI tool-calling endpoints

# Inicializar la base de datos (ejecuta esquemas y migraciones automáticamente)
init_db()

# Servir archivos estáticos del frontend
app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
app.mount("/mocks", StaticFiles(directory=FRONTEND_DIR / "mocks"), name="mocks")

@app.get("/api/health")
def health():
    """Si esto responde, la base común está bien montada."""
    return {"status": "ok", "app": "Anexo Risk"}

@app.get("/manifest.json")
async def serve_manifest():
    return FileResponse(FRONTEND_DIR / "manifest.json", media_type="application/json")

@app.get("/sw.js")
async def serve_sw():
    return FileResponse(FRONTEND_DIR / "sw.js", media_type="application/javascript")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    file_path = (FRONTEND_DIR / full_path).resolve()
    if file_path.is_file() and file_path.is_relative_to(FRONTEND_DIR.resolve()):
        return FileResponse(file_path)
    return FileResponse(FRONTEND_DIR / "index.html")
