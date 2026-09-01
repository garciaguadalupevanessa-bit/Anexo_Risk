# NexoGeoRisk — Integración NEXO + GeoRisk

> Repositorio integrado del módulo de **Alertas NEXO** dentro de **GeoRisk Finder**. Combina la plataforma de inteligencia geoespacial (H3, globo, clustering) con la app comunitaria de respuesta a emergencias (alertas oficiales GDACS, mapa de necesidades, voluntariado/donaciones).

Este repo es la versión particular del equipo 2 (Javi, Juan, Luis, Vanessa) — 4 personas cubriendo los 4 módulos de NEXO (G1 Necesidades, G2 Alertas, G3 Ayudas, G4 Mapa) + módulos GeoRisk (mapa, globo, H3).

## Estructura integrada

- `backend/` — API FastAPI (NEXO) + migraciones SQLite (ver `docs/modelo-entidad-relacion.md`)
- `frontend/` — PWA estática (NEXO) + `georisk_globe/` (globo 3D)
- `src/` — Pipeline GeoRisk (H3, clustering, data_loader) — fuente única GDACS
- `data/` — Datasets procesados GeoRisk (ciclones, volcanes, sismos, grid H3)
- `notebooks/` — EDA GeoRisk
- `api/` — Serverless FastAPI para Vercel (ver plan `docs/equipos/reparto-4p-mvp.md`)
- `public/` — Frontend estático para CDN Vercel

## Integración Alertas (G2) — GeoRisk como fuente única

Ver `docs/equipos/reparto-4p-mvp.md` y resumen de integración en la descripción del repo. Esquema unificado:

```python
{
    "external_id": "GDACS_1234",
    "title": str, "event_type": str, "source": "GDACS|PROTECCION_CIVIL|MANUAL",
    "severity": "RED|ORANGE|GREEN", "risk_level": "low|medium|high",
    "status": "normal|active|high_risk|deactivated",
    "zone": GeoJSON, "is_active": bool
}
```

Fallback `[]` si GDACS cae, deduplicación por `external_id`.

## Cómo arrancar (NEXO)

```bash
cd backend && pip install -r requirements-dev.txt && python db/seed.py && uvicorn main:app --reload --port 8000
cd frontend && python -m http.server 5500
```

Ver `docs/manifiesto.md`, `docs/equipos.md`, `docs/backlog.md` (trazabilidad Sprint 1-2).

---

# GeoRisk Finder 🌍 (original)

> Plataforma de Inteligencia Geoespacial para la Evaluación de Riesgos Compuestos y Decisiones de Inversión en Resiliencia Climática

Ver `informe_tecnico.md` y `GeoRisk_Finder/README.md` original para el pipeline H3/clustering.
