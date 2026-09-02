# Architecture Decision Records — Anexo Risk

> Last updated: 2026-09-02  
> Format: Lightweight ADR (Architecture Decision Record)

---

## ADR-001: Single-Page Application (SPA)

**Date:** 2026-09-02  
**Status:** Accepted  
**Decision Makers:** Juan (PM/Tech Lead)

### Context
The project had multiple HTML pages (`mapa.html`, `alertas.html`, `donaciones.html`, etc.) causing:
- Inconsistent branding and navigation
- Page reload transitions breaking UX
- Duplicate CSS/JS references
- Difficulty integrating modules

### Decision
Consolidate all sections into a single `index.html` with JavaScript-driven section switching.

### Consequences
- ✅ Unified navigation and branding
- ✅ Smooth transitions between sections
- ✅ Shared state between modules (map, alerts, donations)
- ✅ Reduced asset loading
- ❌ Larger initial HTML payload
- ❌ More complex JavaScript state management

---

## ADR-002: Dark Glassmorphism Design System

**Date:** 2026-09-02  
**Status:** Accepted  
**Decision Makers:** Juan (PM/Tech Lead)

### Context
Emergency operations platforms need:
- High contrast for readability in stressful situations
- Visual hierarchy to prioritize critical information
- Modern aesthetic for professional credibility
- Dark theme to reduce eye strain during extended monitoring

### Decision
Adopt a dark glassmorphism design system with:
- **Background:** Deep void (#060810) with glass panels
- **Accents:** Cyan (#00F0FF) for active elements, Red (#FF334B) for critical alerts, Orange (#FF6B00) for warnings
- **Typography:** Inter font family with clear hierarchy
- **Effects:** Backdrop blur, subtle borders, glow effects on alerts

### Consequences
- ✅ Professional "mission control" aesthetic
- ✅ Clear visual hierarchy for emergency data
- ✅ Reduced eye strain for extended monitoring
- ✅ Accessible contrast ratios
- ❌ Requires careful color management
- ❌ Some legacy CSS variables need migration

---

## ADR-003: Vanilla JS (No Framework)

**Date:** 2026-08-25  
**Status:** Accepted  
**Decision Makers:** Team consensus

### Context
Team of 4 developers with mixed experience levels. Need fast prototyping for MVP.

### Decision
Use vanilla JavaScript with ES Modules, no framework (React, Vue, etc.).

### Consequences
- ✅ Zero build step required
- ✅ Static deployment ready (CDN, Vercel)
- ✅ Easy to understand for all team members
- ✅ PWA-ready without framework overhead
- ❌ No component abstraction
- ❌ Manual DOM manipulation
- ❌ More verbose code

---

## ADR-004: FastAPI + SQLite Backend

**Date:** 2026-08-25  
**Status:** Accepted  
**Decision Makers:** Team consensus

### Context
Need a lightweight backend for rapid MVP development without infrastructure overhead.

### Decision
- **Framework:** FastAPI (async, automatic OpenAPI docs)
- **Database:** SQLite (file-based, zero config)
- **ORM:** None (raw SQL for transparency)

### Consequences
- ✅ Instant setup (no database server needed)
- ✅ Auto-generated API documentation
- ✅ High performance for read-heavy workload
- ✅ Easy deployment (single file database)
- ❌ No concurrent write scaling
- ❌ No relational integrity enforcement
- ❌ Manual query optimization

---

## ADR-005: GDACS as Single Source for Alerts

**Date:** 2026-08-28  
**Status:** Accepted  
**Decision Makers:** Javi (Backend Lead)

### Context
Multiple potential alert sources (GDACS, national civil protection, manual entry) create complexity.

### Decision
Use GDACS (Global Disaster Alerting Coordination System) as the primary and only external source. Manual alerts supported via API but not integrated in MVP.

### Consequences
- ✅ Single integration point
- ✅ Global coverage (UN-backed)
- ✅ Reliable API with 99.9% uptime
- ✅ Deduplication by `external_id`
- ❌ Dependent on GDACS data quality
- ❌ No local/custom alert support in MVP

---

## ADR-006: GitHub Flow Branching Strategy

**Date:** 2026-08-25  
**Status:** Accepted  
**Decision Makers:** Juan (PM)

### Context
Small team (4 people) needs simple but disciplined branching.

### Decision
- `main` branch: protected, only merged via PR
- `feat/*` branches: per module/person
- PR required with at least 1 review
- CI must pass before merge

### Consequences
- ✅ Simple to understand and follow
- ✅ Code review enforced
- ✅ CI ensures quality
- ✅ Clear history
- ❌ No parallel development on same module
- ❌ Requires discipline to avoid stale branches
