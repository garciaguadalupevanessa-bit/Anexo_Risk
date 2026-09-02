## Summary

Full repository audit and hardening of the Anexo Risk emergency response platform.

## Changes

### P0 - Critical Runtime Errors
- **config.py**: `NEXO_ADMIN_KEY` default corrected from `nexo-dev-admin-key` to `anexo-risk-dev-admin-key` (was ignoring .env value at runtime)
- **error_handler.py**: global exception handler no longer leaks `str(exc)` to clients - logs full detail server-side, returns safe 500

### P1 - Broken Contracts and Code Quality
- **sync_controller.py**: removed duplicate router declaration, hardcoded `nexo.db` to `DATABASE_PATH`, removed unused imports
- **logging_config.py**: added missing `get_logger()` function (was imported but not defined)
- **config.py**: removed duplicate `GDACS_CACHE_TTL_SECONDS` line; fixed dummy defaults for SMTP/ADMIN

### P2 - Endpoint Failures
- **donaciones/models.py**: added `_normalize_donation()` to map legacy `tipo` values (`recursos`, `servicios`, `tiempo` to `ofrecida`) for backward compatibility with seed data
- **donaciones/schemas.py**: added optional `dni`, `latitud`, `longitud` fields to `DonationResponse` (matching existing DB schema; `extra='forbid'` was breaking `GET /api/donaciones`)

### NEXO - Anexo Identity Cleanup
- **backend/config.py**: default DATABASE_URL to `anexo_risk.db`
- **backend/main.py**: title to "Anexo Risk API"
- **backend/middleware/auth.py**: header to `X-Anexo-Key`
- **backend/modules/voluntariado/email_service.py**: `[Nexo]` to `[Anexo Risk]` in all email subjects
- **frontend/manifest.json**: name to "Anexo Finder", short_name to "Anexo Risk"
- **README.md**: complete rewrite as Anexo Risk product
- **docs**: titles updated in CONTRIBUTING.md, roadmap.md, architecture.md, privacidad-datos.md

### CI/CD Improvements
- **ci.yml**: DATABASE_URL set correctly, checks for `spa.js` existence, checks no NEXO in frontend/manifest

### Cleanup
- deleted: `requirements.txt` (root, ML legacy), server logs, `final_test.py`, `nexo.db`, audit doc
- moved: ML/GeoRisk requirements to `src/requirements.txt`
- gitignore: hardened against server logs, venv, audit docs

## Type of change

- [x] Bug fix
- [x] Refactor
- [x] Chore
- [x] Configuration

## Checklist

- [x] 79/79 backend tests passing
- [x] All P0 and P1 issues resolved
- [x] No new features introduced
- [x] NEXO references removed from active/visible code
