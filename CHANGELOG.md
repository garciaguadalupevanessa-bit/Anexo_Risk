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
- Assignments module (FASE C): CRUD completo con reglas de negocio
  - POST /api/assignments: crear asignación (valida cantidad, estado, disponibilidad)
  - GET /api/assignments: listar con filtros need_id/resource_id/status
  - GET /api/assignments/{id}: detalle con joins de necesidad y recurso
  - PATCH /api/assignments/{id}: transiciones asignado->en_curso->completado|cancelado
  - GET /api/assignments/need/{need_id}: resumen de asignaciones por necesidad
- Business rules: deducción de available_quantity, actualización de covered_quantity
- Auto-cierre de necesidades al cubrir toda la cantidad solicitada
- Restauración de disponibilidad al cancelar/completar asignaciones
- Decision Center integrado con asignaciones activas por incidente
- Migración 014: updated_at en need_assignments
- 32 tests de asignaciones (creación, errores, transiciones, restauración, listado, schemas, SQL injection)
- Migraciones 009-014 (organizations, resources, needs_extended, geodata, risk_engine, assignment_updated_at)
- AGENTS.md: documento de reglas arquitectónicas
- AUTHORS.md: atribución de autores MVP + evolución
- Integration audit document

### Changed
- alertas/services.py: eliminada dependencia de gdacs_mock
- config.py: JWT_SECRET_KEY y ANEXO_ADMIN_KEY ahora son requeridos
- main.py: registrados 13 routers (53 endpoints totales)
- decision_center/service.py: operación incluye asignaciones activas + explicación mejorada
- requirements.txt: añadidas dependencias h3, numpy, pandas, scikit-learn

## [v1.0.0] - 2025

### MVP Original
- Plataforma de gestión de emergencias
- Módulos: necesidades, alertas, voluntariado, donaciones, personas
- Frontend SPA con Leaflet
- Backend FastAPI + SQLite
- 84 tests pasando
