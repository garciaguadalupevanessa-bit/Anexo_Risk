# Changelog

## [Unreleased]

### Seguridad
- Eliminados fallbacks inseguros para `JWT_SECRET_KEY` y `ANEXO_ADMIN_KEY`
- Eliminado mock GDACS fallback (no más datos sintéticos presentados como reales)
- `.env.example` actualizado con placeholders y instrucciones de generación

### Added
- GeoData Engine con adapters: USGS, IBTrACS, Smithsonian, Copernicus/EFFIS
- Spatial services: H3 indexing, haversine distance, nearby search
- Exposure calculation con factores explicativos
- Risk Engine determinista con methodology_version y generated_at
- ML Pipeline: GradientBoostingClassifier, feature engineering, model artifacts
- Decision Center: /api/decision/context y /api/decision/explain
- Organizations module: CRUD con autenticación
- Resources module: CRUD con nearby search y autenticación
- Extended needs: 7 campos adicionales + tabla need_assignments
- Migraciones 009-013 (organizations, resources, needs_extended, geodata, risk_engine)
- AGENTS.md: documento de reglas arquitectónicas
- AUTHORS.md: atribución de autores MVP + evolución
- Integration audit document

### Changed
- alertas/services.py: eliminada dependencia de gdacs_mock
- config.py: JWT_SECRET_KEY y ANEXO_ADMIN_KEY ahora son requeridos
- main.py: registrados 12 routers (48 endpoints totales)
- requirements.txt: añadidas dependencias h3, numpy, pandas, scikit-learn

## [v1.0.0] - 2025

### MVP Original
- Plataforma de gestión de emergencias
- Módulos: necesidades, alertas, voluntariado, donaciones, personas
- Frontend SPA con Leaflet
- Backend FastAPI + SQLite
- 84 tests pasando
