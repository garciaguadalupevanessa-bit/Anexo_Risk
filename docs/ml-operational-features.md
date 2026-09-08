# ML Operational Features — Analysis

**Date:** 2026-09-07  
**Status:** Analysis only — NO retraining yet  
**Author:** Anexo_Risk

---

## 1. Overview

This document analyzes operational features from Anexo_Risk that could enrich GeoRisk Finder's ML pipeline. The goal is to identify which features are viable, which have data quality issues, and which targets are realistic.

**Key principle:** Do not use features that leak future information into the prediction target.

---

## 2. Available Operational Features

### 2.1 Features per H3 Cell

| Feature | Source | Coverage | Timestamp | Missing Rate | Leakage Risk |
|---------|--------|----------|-----------|--------------|--------------|
| `needs_open` | necesidades table | ~80% cells | Created per need | Low | **LOW** — needs exist at prediction time |
| `needs_uncovered` | needs_open - covered_quantity | ~80% | Created per need | Low | **LOW** — same as needs_open |
| `resources_available` | resources table | ~60% cells | Created per resource | Medium | **LOW** — resources exist at prediction time |
| `resource_gap` | needs_open - resources_available | ~70% | Derived | Low | **LOW** — derived from current state |
| `operational_load` | active_assignments / resources | ~60% | Derived | Medium | **LOW** — current ratio |
| `event_count` | alertas table | ~90% | Alert creation time | Low | **LOW** — alerts exist at prediction time |
| `critical_alerts` | alertas.severidad = 'RED' | ~90% | Alert creation time | Low | **LOW** — same as event_count |

### 2.2 Temporal Features

| Feature | Description | Leakage Risk |
|---------|-------------|--------------|
| `needs_trend_24h` | Change in needs count over 24h | **MEDIUM** — requires careful windowing |
| `response_time_avg` | Average time from need creation to assignment | **HIGH** — outcome data, not available at prediction time |
| `escalation_rate` | % of needs that escalate in priority | **HIGH** — outcome data |

---

## 3. Leakage Analysis

### 3.1什么是 Leakage?

Leakage occurs when the model has access to information at training time that would NOT be available at prediction time.

### 3.2 Current GeoRisk Target

The current GeoRisk target is rule-based (severity score from the Risk Engine). This means:
- The model learns the scoring rules, not real outcomes
- No temporal leakage in the target itself
- But the model may learn patterns that don't generalize

### 3.3 Operational Features — Leakage Assessment

**SAFE to use (available at prediction time):**
- `needs_open` — count of open needs in the cell
- `needs_uncovered` — count of needs not yet covered
- `resources_available` — count of available resources
- `resource_gap` — difference between needs and resources
- `operational_load` — ratio of assignments to resources
- `event_count` — count of active alerts
- `critical_alerts` — count of critical alerts

**NOT SAFE to use (outcome data):**
- `response_time_avg` — this is an outcome, not a predictor
- `escalation_rate` — this is an outcome
- `incident_closed` — this is an outcome
- `needs_resolved` — this is an outcome

### 3.4 Temporal Window Rules

When using time-series features:
1. The feature timestamp must be BEFORE the prediction target timestamp
2. Use `needs_created_at` not `needs_updated_at` for temporal alignment
3. Avoid using features that aggregate over a window that includes the target time

---

## 4. Viable Targets for Future ML

### 4.1 Target A: Needs Escalation Probability

**Definition:** Probability that a need will escalate from "media" to "alta" or "critica" within 24 hours.

**Feasibility:** LOW — requires historical priority changes, which are not consistently recorded.

**Data needed:**
- Historical priority changes with timestamps
- At least 100+ escalation events

### 4.2 Target B: Resource Gap Persistence

**Definition:** Probability that a resource gap (needs > resources) will persist for more than 6 hours.

**Feasibility:** MEDIUM — we have needs and resources with timestamps.

**Data needed:**
- Historical resource availability over time
- Assignment timestamps
- At least 200+ gap events

### 4.3 Target C: Operational Load Category

**Definition:** Classification of operational load into categories (low/medium/high/critical) based on needs-to-resource ratio.

**Feasibility:** HIGH — directly calculable from current data.

**Data needed:**
- Current needs and resources (already available)
- Definition of threshold boundaries

### 4.4 Target D: Response Duration

**Definition:** Time from need creation to first assignment.

**Feasibility:** MEDIUM — we have creation timestamps and assignment timestamps.

**Data needed:**
- Need `created_at` timestamps
- Assignment `created_at` timestamps
- At least 100+ completed assignments

---

## 5. Minimum Dataset Requirements

### 5.1 For Operational Features

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Cells with data | 50 | 200+ |
| Needs with coordinates | 100 | 500+ |
| Resources with coordinates | 50 | 200+ |
| Time span | 7 days | 30+ days |
| Assignments | 50 | 200+ |

### 5.2 For Target Training

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| Labeled outcomes | 100 | 500+ |
| Positive examples | 20 | 100+ |
| Negative examples | 80 | 400+ |
| Time span | 14 days | 60+ days |

---

## 6. Recommendations

### 6.1 Immediate (No retraining)

1. Add operational features to the H3 grid as **read-only metadata**
2. Log feature availability and missing rates
3. Create monitoring dashboards for feature quality

### 6.2 Short-term (After data collection)

1. Implement `record_prediction()` and `record_outcome()` in the feedback loop
2. Collect 30+ days of operational data
3. Analyze feature correlations with outcomes

### 6.3 Medium-term (When data is sufficient)

1. Train a classifier for Target C (Operational Load Category)
2. Evaluate if operational features improve GeoRisk's scientific risk model
3. Compare: model with operational features vs. without

### 6.4 NOT recommended

- Do NOT use `response_time_avg` or `escalation_rate` as features (leakage)
- Do NOT retrain automatically without measuring improvement
- Do NOT combine operational and scientific scores without evidence

---

## 7. Data Provenance Requirements

Every operational feature must include:

```json
{
  "feature_name": "needs_open",
  "value": 12,
  "source": "anexo_risk",
  "timestamp": "2026-09-07T12:00:00Z",
  "h3_index": "832bffffffffff",
  "methodology": "count_of_open_needs_in_cell"
}
```

---

## 8. Conclusion

The operational features from Anexo_Risk are **viable** for enriching GeoRisk's ML pipeline, but:

1. Only use features available at prediction time (no leakage)
2. Collect data for 30+ days before training
3. Start with Target C (Operational Load) as it's the simplest
4. Always compare against baseline (without operational features)
5. Document everything
