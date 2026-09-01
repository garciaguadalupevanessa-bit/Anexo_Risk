"""Serverless entry para Vercel — NexoGeoRisk.

Reexporta la app FastAPI de backend/main.py como handler serverless.
Vercel ejecuta este archivo como función en /api/*.

Despliegue: vercel.json rewrites /api/(.*) -> api/index.py
Local: uvicorn api.index:app --reload sigue funcionando.
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from main import app  # noqa: E402
