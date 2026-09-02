# Sprint Tracking — Anexo Risk

> Last updated: 2026-09-02  
> Repository: `garciaguadalupevanessa-bit/Anexo_Risk`  
> Branching: GitHub Flow (`feat/*` → `main`)

---

## Sprint 1 — COMPLETE ✅

**Duration:** 2026-08-25 → 2026-08-31  
**Goal:** MVP with 4 core modules operational

### Deliverables

| Module | Owner | Status | PR |
|--------|-------|--------|----|
| Backend foundation (CORS, apiClient, seed) | Juan | ✅ Merged | #53 |
| G1 — Needs (8 categories, 2 states) | Luis | ✅ Merged | #56, #61 |
| G2 — Alerts (GDACS, filters, severity) | Javi | ✅ Merged | PR #4 → main |
| G3 — Donations + Volunteering | Vanessa | ✅ Merged | PR #2 → main |
| G4 — Interactive Map (Leaflet) | Juan | ✅ Merged | PR #4 → main |
| Documentation & governance | Juan | ✅ Merged | #53 |

### Velocity

- Total story points: 34
- Completed: 34
- Carry-over: 0

---

## Sprint 2 — IN PROGRESS 🔄

**Duration:** 2026-09-01 → 2026-09-07  
**Goal:** Production-ready SPA with integrated modules, design system, and CI/CD

### Sprint Backlog

| ID | Task | Priority | Owner | Status |
|----|------|----------|-------|--------|
| S2-01 | Unify all modules into single SPA (`index.html` + `spa.js`) | High | Juan | ✅ Done |
| S2-02 | Dark glassmorphism design system (`variables.css` + `style.css`) | High | Juan | ✅ Done |
| S2-03 | Fix Anexo Risk logo references | High | Juan | ✅ Done |
| S2-04 | Merge Luis's PR #5 (G1 needs refactor) | High | Juan | ✅ Done |
| S2-05 | Fix seed.py enum error ("Agua embotellada") | High | Juan | ✅ Done |
| S2-06 | Professional bilingual README | High | Juan | ✅ Done |
| S2-07 | English Scrum documentation | Medium | Juan | 🔄 In Progress |
| S2-08 | CI/CD pipeline (GitHub Actions) | High | Javi | ⬜ Todo |
| S2-09 | PWA manifest + service worker | Medium | Vanessa | ⬜ Todo |
| S2-10 | Offline mode (localStorage fallback) | Medium | Vanessa | ⬜ Todo |
| S2-11 | Responsive mobile layout | Medium | Luis | ⬜ Todo |
| S2-12 | End-to-end integration testing | High | Javi | ⬜ Todo |

### Burndown

```
Day 1 (Mon): ████████████████████████ 12 tasks
Day 2 (Tue): ████████████████░░░░░░░░  8 tasks (4 done)
Day 3 (Wed): ████████████░░░░░░░░░░░░  5 tasks (7 done)
Day 4 (Thu): ░░░░░░░░░░░░░░░░░░░░░░░░  remaining
```

### Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| CI pipeline not active | High | Javi to configure GitHub Actions this sprint |
| Mobile responsiveness incomplete | Medium | Luis to add responsive breakpoints |
| GDACS API downtime | Low | Fallback to empty array, cached data |

---

## Sprint 3 — PLANNED 📋

**Duration:** 2026-09-08 → 2026-09-14  
**Goal:** Analytics, external integrations, and mobile

### Epic Backlog

| Epic | Description | Owner |
|------|-------------|-------|
| H3 Analytics | Predictive analytics using hexagonal grid clustering | Juan |
| Civil Protection Integration | API sync with government alert systems | Javi |
| Mobile App | React Native wrapper for iOS/Android | Luis |
| Multi-language (i18n) | Spanish/English toggle | Vanessa |

---

## Definition of Done

A task is considered **done** when:

- [ ] Code implemented following project conventions
- [ ] Unit tests passing (`pytest` for backend)
- [ ] No linting errors
- [ ] Tested in browser (Chrome, Firefox)
- [ ] Mobile responsive (≥360px)
- [ ] States handled: loading, empty, error
- [ ] PR reviewed and merged
- [ ] Documentation updated if needed

## Definition of Ready

A task is **ready** for sprint planning when:

- [ ] Clear objective
- [ ] Assigned owner
- [ ] Acceptance criteria defined
- [ ] Dependencies identified
- [ ] Estimated (story points)
