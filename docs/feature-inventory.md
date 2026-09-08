# Feature Inventory — Anexo_Risk v2.1

**Date:** 2026-09-08
**Status:** FASE 0 Complete

---

## Classification Legend

- **CORE** — Transversal capability, must evolve with product
- **REGIONAL** — Useful in specific territory, preserve if valuable
- **LOCAL** — Specific to a locality/organization
- **LEGACY** — Existing capability with uncertain value, isolate
- **DEPRECATED** — Exists but should not grow

---

## Backend Modules

| Module | Prefix | Classification | Current Value | Action |
|---|---|---|---|---|
| incidentes | `/api/incidents` | CORE | High — vertical slice entry point | Evolve |
| alertas | `/api/alertas` | CORE | High — alert management | Evolve |
| necesidades | `/api/necesidades` | CORE | High — humanitarian needs | Evolve |
| timeline | `/api/timeline` | CORE | High — lifecycle tracking | Evolve |
| outcome | `/api/outcomes` | CORE | Medium — feedback loop | Evolve |
| asignaciones | `/api/assignments` | CORE | High — resource assignment | Evolve |
| organizaciones | `/api/organizations` | CORE | High — federation model | Evolve |
| recursos | `/api/resources` | CORE | High — resource management | Evolve |
| decision_center | `/api/decision` | CORE | High — contextual analysis | Evolve |
| operational | `/api/operational` | CORE | High — operational summary | Evolve |
| voluntariado | `/api/voluntarios` | REGIONAL | Medium — Spain-specific volunteer workflow | Preserve |
| donaciones | `/api/donaciones` | REGIONAL | Medium — donation management | Preserve |
| incendios | `/api/incendios` | REGIONAL | Medium — NASA FIRMS Spain focus | Preserve |
| clima | `/api/clima` | REGIONAL | Medium — AEMET Spain weather | Preserve |
| personas | `/api/personas` | LOCAL | Low — person registration | Evaluate |
| ai_tools | `/api/ai` | LOCAL | Low — schema descriptors only | Evaluate |
| sync | `/api/sync` | REGIONAL | Medium — offline sync | Preserve |
| external_risk | `/api/external-risk` | CORE | High — GeoRisk integration | Evolve |
| geodata | `/api/geodata` | CORE | High — spatial analysis engine | Evolve |
| health | `/api/health` | CORE | High — observability | Evolve |

---

## Frontend Modules

| Module | Path | Classification | Action |
|---|---|---|---|
| spa.js | js/spa.js | CORE | Evolve — add region selector |
| config.js | js/shared/config.js | CORE | Evolve — add region/AOI constants |
| mapa.js | js/sections/mapa.js | CORE | Evolve — add new layers, region filter |
| alertas.js | js/sections/alertas.js | CORE | Evolve — source health indicators |
| dashboard.js | js/sections/dashboard.js | CORE | Evolve — operational coverage metrics |
| decision-center.js | js/sections/decision-center.js | CORE | Evolve — action areas, network |
| risk-card.js | js/sections/risk-card.js | CORE | Evolve — multi-source risk |
| timeline.js | js/sections/timeline.js | CORE | Preserve |
| freshness.js | js/sections/freshness.js | CORE | Evolve — source registry integration |
| ayudas.js | js/sections/ayudas.js | CORE | Evolve — resource routing |
| domain.js | js/core/normalization/domain.js | CORE | Evolve — new entity types |
| sources.js | js/core/normalization/sources.js | CORE | Evolve — new source normalizers |
| analytics.js | js/shared/analytics.js | LOCAL | Preserve |
| geocodificacion.js | js/core/mapa-necesidades/ | LOCAL | Preserve |

---

## Database Tables

| Table | Rows | Classification | Action |
|---|---|---|---|
| incidents | 454 | CORE | Evolve — add region, AOI |
| alertas | 619 | CORE | Evolve — add source registry link |
| necesidades | 142 | CORE | Evolve — add H3, region |
| timeline_events | 763 | CORE | Preserve |
| feedback_loop | 194 | CORE | Preserve |
| need_assignments | 0 | CORE | Evolve |
| organizations | 1 | CORE | Evolve — federation |
| operational_users | 7 | CORE | Evolve — RBAC |
| resources | 7 | CORE | Evolve — add H3, region |
| donaciones | 20 | REGIONAL | Preserve |
| voluntarios | 0 | REGIONAL | Preserve |
| voluntario_documentos | 0 | REGIONAL | Preserve |
| personas | 0 | LOCAL | Evaluate |
| sync_operations | 0 | REGIONAL | Preserve |
| sync_log | 0 | LEGACY | Isolate |
| geodata_events | 0 | CORE | Evolve — event correlation |
| spatial_cells | 0 | CORE | Evolve — H3 mesh |
| risk_scores | 0 | CORE | Evolve |
| model_versions | 0 | CORE | Preserve |
| prediction_history | 0 | CORE | Preserve |

---

## External Integrations

| Integration | Status | Classification | Action |
|---|---|---|---|
| GDACS | Working | GLOBAL | Evolve — source registry |
| NASA FIRMS | Working | GLOBAL | Evolve — source registry |
| USGS | Working | GLOBAL | Evolve — source registry |
| EFFIS/Copernicus | Working | GLOBAL/EU | Evolve — source registry |
| Open-Meteo | Working | GLOBAL | Evolve — source registry |
| AEMET | Working | COUNTRY:ES | Evolve — source registry |
| GeoRisk Finder | Working | CORE | Evolve — deeper integration |
| Proteccion Civil | Stub | COUNTRY:ES | Evaluate — needs real source |
| IBTrACS | Working | GLOBAL | Preserve |
| Smithsonian GVP | Working | GLOBAL | Preserve |

---

## New Capabilities Required (v2.1)

| Capability | Classification | Priority | Phase |
|---|---|---|---|
| Region/AOI Engine | CORE | High | 1 |
| Source Registry | CORE | High | 2 |
| Source Health Dashboard | CORE | High | 2 |
| Normalized Adapter Contract | CORE | High | 3 |
| Near-Real-Time Polling | CORE | High | 5 |
| Event Correlation Engine | CORE | High | 6 |
| H3 Operational Mesh | CORE | Medium | 7 |
| Dynamic Action Area | CORE | Medium | 11 |
| Operational Nodes | CORE | Medium | 8 |
| Network Links | CORE | Medium | 9 |
| Accessibility/Routing | CORE | Medium | 10 |
| Alert Policy Engine | CORE | Medium | 12 |
| Alert Dry-Run | CORE | Medium | 12 |
| Federated Organizations | CORE | Medium | 13 |
| RBAC Expansion | CORE | Medium | 13 |
| Live UX | CORE | Medium | 14 |
| Privacy Policy | CORE | High | 15 |
| Spain Regional Sources | REGIONAL | Medium | 4 |
| Operational Coverage Metric | CORE | Low | 7 |
