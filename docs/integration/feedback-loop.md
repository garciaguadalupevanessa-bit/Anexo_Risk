# Feedback Loop — Anexo_Risk ↔ GeoRisk Finder

**Version:** 1.0  
**Date:** 2026-09-07  
**Status:** Designed — data collection phase

---

## 1. Overview

The feedback loop connects predictions from both systems to actual operational outcomes. This enables:

- Measuring prediction accuracy
- Identifying systematic biases
- Collecting training data for future ML models
- Improving both scientific and operational risk assessment

---

## 2. Flow

```
PREDICTION                    OUTCOME
    ↓                           ↓
GeoRisk scientific risk    Anexo_Risk operational result
Anexo_Risk operational risk    
    ↓                           ↓
    └──────→ feedback_loop ←────┘
                  ↓
         analysis & reporting
                  ↓
         future ML training (when data is sufficient)
```

---

## 3. Data Model

### 3.1 Prediction Record

| Field | Type | Description |
|-------|------|-------------|
| `prediction_source` | text | `anexo_risk` or `georisk` |
| `model_version` | text | e.g., `rules-v1`, `ml-v1`, `georisk-v3` |
| `predicted_level` | text | `critica`, `alta`, `moderada`, `informativa` |
| `predicted_score` | real | 0-100 score |
| `prediction_time` | text | ISO 8601 timestamp |
| `h3_index` | text | H3 cell (resolution 3) |
| `lat`, `lon` | real | Center coordinates |
| `needs_open_at_prediction` | int | Needs in cell at prediction time |
| `resources_available_at_prediction` | int | Resources in cell at prediction time |
| `incident_id` | text | Associated incident (if any) |

### 3.2 Outcome Record

| Field | Type | Description |
|-------|------|-------------|
| `outcome_time` | text | ISO 8601 timestamp |
| `incident_closed` | bool | Was the incident resolved? |
| `needs_created` | int | New needs created after prediction |
| `needs_resolved` | int | Needs resolved after prediction |
| `resource_gap_at_outcome` | int | Gap at outcome time |
| `response_duration_hours` | real | Time from prediction to outcome |
| `escalation_occurred` | bool | Did severity increase? |

---

## 4. Usage

### 4.1 Recording a Prediction

When Anexo_Risk generates a risk score:

```python
from models.feedback import record_prediction

record_prediction(
    prediction_source="anexo_risk",
    model_version="rules-v1",
    predicted_level="alta",
    predicted_score=72.5,
    prediction_time="2026-09-07T12:00:00Z",
    h3_index="832bffffffffff",
    lat=40.4168,
    lon=-3.7038,
    needs_open=5,
    resources_available=2,
    incident_id="INC-2026-001",
)
```

### 4.2 Recording an Outcome

When the incident is resolved or reviewed:

```python
from models.feedback import record_outcome

record_outcome(
    feedback_id=42,
    incident_closed=True,
    needs_created=3,
    needs_resolved=8,
    resource_gap=0,
    response_duration_hours=6.5,
    escalation_occurred=False,
)
```

### 4.3 Querying Feedback

```python
from models.feedback import get_feedback_entries, get_feedback_stats

# All predictions for a cell
entries = get_feedback_entries(h3_index="832bffffffffff")

# Only predictions with outcomes
entries = get_feedback_entries(has_outcome=True)

# Aggregate statistics
stats = get_feedback_stats()
```

---

## 5. Analysis Use Cases

### 5.1 Prediction Accuracy

Compare predicted level vs. actual outcome:
- Did "alta" predictions actually result in escalations?
- Did "baja" predictions stay low?

### 5.2 Resource Gap Analysis

- How often did resource_gap > 0 correlate with escalation?
- What's the average response duration for different gap levels?

### 5.3 Model Comparison

- Compare GeoRisk scientific predictions vs. Anexo_Risk operational predictions
- Which was closer to the actual outcome?

---

## 6. Constraints

1. **No automatic retraining** — only analysis and reporting
2. **No outcome fabrication** — only record real operational results
3. **Provenance required** — every record must have source and timestamp
4. **Privacy** — do not record personal data in the feedback loop
5. **Retention** — keep records for at least 2 years for longitudinal analysis

---

## 7. Integration with GeoRisk

GeoRisk can query the feedback loop via:

```
GET /api/operational/feedback?h3_index=...
GET /api/operational/feedback/stats
```

This allows GeoRisk to:
- Evaluate its own prediction accuracy
- Identify cells where its model underperforms
- Collect training data for future model improvements
