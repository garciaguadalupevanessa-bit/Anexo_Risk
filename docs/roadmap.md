# Roadmap — Anexo Risk

> Last updated: 2026-09-07

## Completado en Sprint 2 (2026-09-01 → 2026-09-07)

- [x] SPA unificada (index.html + spa.js)
- [x] Design system dark glassmorphism (variables.css + style.css)
- [x] Frontend modular (spa.js → 6 ES modules, 1186→163 líneas)
- [x] Security hardening (XSS, SQL injection, path traversal, timing attack)
- [x] Input validation completa (max_length, ge/le en todos los schemas)
- [x] Tests: 246 backend + 214 frontend = 460 total
- [x] Alertas persistidas en SQLite (migration 008)
- [x] FIRMS zone selector (spain/europa/mediterraneo/global)
- [x] Open-Meteo 7 ciudades con retry logic
- [x] Dead code cleanup (20 archivos JS eliminados)

## Siguiente prioridad

- [ ] UI de Voluntariado (backend listo, falta frontend)
- [ ] UI de Personas / "Estoy bien" (backend listo, falta frontend)
- [ ] Modo offline (frontend queue + service worker)
- [ ] Dashboard analytics con gráficas
- [ ] PWA instalable completa

## Horizonte estratégico (3-6 meses)

- [ ] Autenticación JWT (login de usuario)
- [ ] PostgreSQL/PostGIS para escalabilidad
- [ ] Push notifications para alertas críticas
- [ ] Mobile app (React Native o PWA avanzada)
- [ ] Multi-idioma (i18n)

## Excluido del MVP

- ❌ Machine learning / clustering de sismos
- ❌ Red mesh + nodos satelitales
- ❌ Monetización / premium features
