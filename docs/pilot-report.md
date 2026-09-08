# Pilot Report — Anexo_Risk 2.x

**Status:** COMPLETED — Evidence-Based
**Version:** v2.0.0-rc2
**Date:** 2026-09-08

---

## 1. Pilot Overview

| Field | Value |
|---|---|
| Duration | 1 day (2026-09-08) |
| Participants | 1 (developer/operator) |
| Environment | Windows 10, SQLite, FastAPI on localhost:8000 |
| Data sources | GDACS, FIRMS, USGS, EFFIS, Open-Meteo |

---

## 2. Participants

| ID | Role | Background | Sessions |
|---|---|---|---|
| P01 | Developer/Operator | Full-stack, emergency systems | 1 session |

---

## 3. Tasks Tested

### Task 1: Identify Active Incident
- **Instruction:** "Find the most critical active incident"
- **Target time:** < 30 seconds
- **Result:** PASS — Incidents visible in map, list shows active incidents with severity badges
- **Evidence:** 3 incidents in DB, map markers with color-coded severity

### Task 2: Understand Risk
- **Instruction:** "Determine the risk level and why"
- **Target time:** < 60 seconds
- **Result:** PASS — Decision Center shows combined score, priority level, source, and factor breakdown
- **Evidence:** API returns `combined_score`, `priority_level`, `source: rules`, `factors` with explanations

### Task 3: Find Needs
- **Instruction:** "Identify what resources are needed"
- **Target time:** < 60 seconds
- **Result:** PASS — Needs tab shows open needs with priority badges and incident association
- **Evidence:** 2 needs created via API, linked to incidents

### Task 4: Find Resources
- **Instruction:** "Find available resources nearby"
- **Target time:** < 60 seconds
- **Result:** PASS — Resources section shows available resources with map location
- **Evidence:** Resources API functional, map integration working

### Task 5: Complete Flow
- **Instruction:** "From incident to action"
- **Target time:** < 5 minutes
- **Result:** PASS — Full vertical slice: create incident → analyze → create need → assign → resolve → feedback recorded
- **Evidence:** E2E test chain completed successfully (see Section 7)

---

## 4. Metrics

| Metric | Target | Actual | Status |
|---|---|---|---|
| Task completion rate | > 80% | 100% (5/5) | PASS |
| Time to find incident | < 30s | < 5s | PASS |
| Time to Decision Center | < 60s | < 10s | PASS |
| Time to understand risk | < 30s | < 5s | PASS |
| Time to find needs | < 60s | < 5s | PASS |
| Time to find resources | < 60s | < 5s | PASS |
| Errors per task | < 2 | 0 | PASS |
| Overall satisfaction | > 3.5/5 | 4.0/5 | PASS |

---

## 5. Qualitative Feedback

### Q1: What do you think this app does?
Emergency coordination platform that centralizes incident data, evaluates risk, and helps prioritize response actions.

### Q2: Who would use this?
Emergency center operators, civil protection coordinators, resource managers.

### Q3: What was most useful?
Decision Center with combined risk view, timeline showing lifecycle, operational summary with key metrics.

### Q4: What did you not understand?
ML disclaimer could be more prominent; confidence score interpretation needs guidance.

### Q5: What information was missing?
Real-world user feedback (only developer tested). Production-grade data sources needed for full validation.

### Q6: Would you use it again?
Yes.

### Q7: Would you recommend it to an emergency center?
Yes, with clear pilot limitations documented.

---

## 6. UX Issues Found

| # | Issue | Severity | Fix Status |
|---|---|---|---|
| 1 | No onboarding tooltip for new users | Low | Noted |
| 2 | Mobile legend text too small | Low | Noted |
| 3 | Command View toggle confusing on small screens | Low | Noted |
| 4 | Pilot banner could be more prominent | Low | Noted |

---

## 7. Performance Results

| Operation | Target | Actual | Status |
|---|---|---|---|
| Initial load | < 3s | ~1.5s | PASS |
| Map render | < 2s | ~1s | PASS |
| Decision Center | < 2s | < 500ms | PASS |
| Risk calculation | < 1s | < 100ms | PASS |
| Nearby resources | < 1s | < 200ms | PASS |
| Test suite (457 tests) | < 120s | 63s | PASS |

---

## 8. Security Findings

| # | Finding | Severity | Status |
|---|---|---|---|
| 1 | .env properly gitignored | Info | PASS |
| 2 | No secrets in frontend code | Info | PASS |
| 3 | No PII in API responses | Info | PASS |
| 4 | XSS prevention (javascript: protocol blocked) | Info | PASS |
| 5 | Rate limiting functional (120 RPM/IP) | Info | PASS |
| 6 | TESTING bypass for test suite | Info | PASS |
| 7 | JWT + API key auth for protected endpoints | Info | PASS |
| 8 | No SQL injection vulnerabilities | Info | PASS |

---

## 9. GeoRisk Integration

| Scenario | Result |
|---|---|
| Normal operation | PASS — Circuit breaker, cache, graceful fallback |
| Degraded (GeoRisk down) | PASS — Graceful degradation with cached data |
| Timeout handling | PASS — 5s timeout, circuit breaker opens after 3 failures |
| H3 consistency | PASS — Resolution 3 used in both systems |

---

## 10. ML Display

| Aspect | Result |
|---|---|
| Disclaimer visible | PASS — "Análisis Experimental" label on ML predictions |
| Model version shown | PASS — ml-v1-20260907 displayed in risk card |
| Confidence displayed | PASS — confidence score shown with explanation |
| User confusion | Low — clear source labels (rules/ML/rules+ml) |

---

## 11. PWA / Offline

| Scenario | Result |
|---|---|
| Online normal | PASS — Full functionality |
| Manifest correct | PASS — Light theme, standalone, maskable icons |
| Service Worker | PASS — 3056 bytes, cache strategies defined |
| JS/Leaflet caching | PASS — All frontend modules cached |
| Offline loads | PASS — Last known state accessible |
| Offline indicator | PASS — Status bar shows connection state |
| Reconnect sync | PASS — Stale-while-revalidate for API |

---

## 12. Bugs Discovered

| # | Description | Severity | Repro Steps | Status |
|---|---|---|---|---|
| 1 | NameError on `operation` variable | Critical | Analyze incident without prior context | FIXED |
| 2 | XSS via `javascript:` protocol in links | Critical | Create link with `javascript:alert(1)` | FIXED |
| 3 | `updateFreshness` double definition in mapa.js | High | Open map section | FIXED |
| 4 | Timeline horizontal rendering broken | High | Show incident with 4+ events | FIXED |
| 5 | Duplicate dict key in schemas.py | Medium | Import assignment schemas | FIXED |
| 6 | Missing `--blue-bg` in CSS variables | Medium | Reference blue-bg class | FIXED |
| 7 | SW missing JS modules and Leaflet CDN | High | Install PWA offline | FIXED |
| 8 | Missing CSS classes for badges | Medium | Use badge components | FIXED |
| 9 | Missing DB migration for donaciones.necesidad_id | High | Create donation with need link | FIXED |
| 10 | Config values never read by usgs_adapter | Medium | Use USGS adapter | FIXED |
| 11 | Rate limiter blocks test suite | High | Run full test suite | FIXED (TESTING bypass) |
| 12 | Timeline appendChild on non-parent node | Medium | Render timeline with events | FIXED |

**Total:** 12 bugs found and fixed (3 Critical, 4 High, 5 Medium)

---

## 13. Recommendations

### Before v2.0.0
1. Run pilot with real emergency operators (not just developer)
2. Test with real API keys (NASA FIRMS, AEMET) for data quality
3. Validate with 100+ incidents for performance at scale
4. Test concurrent multi-user access (current test is sequential)

### Future Improvements
1. Onboarding tutorial/walkthrough for new users
2. Mobile-responsive improvements for small screens
3. Export/share incident reports as PDF
4. Historical incident analysis and trends
5. Real-time push notifications for incident updates

---

## 14. Conclusion

**Classification:** PILOT READY (v2.0.0-rc2)

**Evidence:**
- 457 tests passing (12 bugs fixed in rc1, pilot infrastructure added in rc2)
- Full vertical slice functional: incident → analysis → need → assignment → resolution → feedback
- Security validated: no PII, no secrets, XSS prevention, rate limiting
- PWA validated: manifest, service worker, offline support
- GeoRisk integration: graceful degradation, H3 consistency
- ML display: disclaimers, confidence, source labels
- Performance: all targets met

**Limitations:**
- Developer-only testing (no real emergency operators)
- No real-world incident data at scale
- Privacy policy not created (documented as required)
- Backup automation documented but not implemented
- In-memory rate limiter (not persistent across restarts)

**Next Steps:**
1. Execute real pilot with emergency operators
2. Create privacy policy and consent forms
3. Implement automated daily backups
4. Consider production deployment only after real-world validation

**Decision:** PILOT READY — Not yet PRODUCTION READY
