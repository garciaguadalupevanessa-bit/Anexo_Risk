# Evaluación ML — Anexo Risk 2.x

**Fecha:** 2026-09-07 10:15 UTC
**Muestras:** 12,161
**Features:** 6
**Modelo:** GradientBoostingClassifier (100 estimadores)
**Versión:** ml-v1-20260907

---

## Advertencia importante

> El target actual está generado por reglas deterministas (solo severidad).
> Las métricas reflejan la capacidad del modelo de aprender esas reglas,
> NO de predecir resultados reales de emergencias.
> Se requieren datos observados para una validación genuina.

---

## Métricas

| Métrica | Valor |
|---------|-------|
| Accuracy | 0.919 |
| F1 Weighted | 0.9023 |

## Baseline (Majority Class)

| Métrica | Valor |
|---------|-------|
| Accuracy | 0.8759 |
| F1 Weighted | 0.818 |

**Mejora sobre baseline:** +4.3% accuracy, +8.4% F1

## Confusion Matrix

| | alto | bajo | critico | medio |
|---|---|---|---|---|
| alto | 0 | 33 | 1 | 23 |
| bajo | 2 | 2109 | 8 | 13 |
| critico | 0 | 19 | 2 | 3 |
| medio | 1 | 85 | 1 | 134 |

## Feature Importance

> La importancia NO implica causalidad.

| Feature | Importancia | Nota |
|---------|-------------|------|
| depth | 0.6355 | Disponible en USGS/Smithsonian |
| distance_to_coast | 0.3645 | Calculado (aproximación global) |
| event_density | 0.0000 | Sin datos en dataset actual |
| needs_open | 0.0000 | Sin datos en dataset actual |
| resources_nearby | 0.0000 | Sin datos en dataset actual |
| weather_score | 0.0000 | Sin datos en dataset actual |

### Análisis de features con importancia 0

Cuatro features tienen importancia 0 porque valen 0 para todos los eventos del dataset. Los adapters USGS y Smithsonian solo proporcionan magnitud, profundidad y coordenadas. Las variables contextuales (densidad, necesidades, recursos, clima) no están disponibles en el dataset de entrenamiento.

Ver `docs/ml-audit.md` §7 para análisis detallado y plan de implementación.

---

## Limitaciones

- Target rule-based, no observado
- 4 de 6 features con valores 0 (sin datos contextuales)
- _estimate_distance_to_coast() es aproximación global
- Sin separación temporal/espacial en train/test
- Sin evaluación con datos reales de emergencias

---

## Metadata del modelo

```json
{
  "version": "ml-v1-20260907",
  "model_type": "gradient_boosting",
  "accuracy": 0.919,
  "f1_weighted": 0.9023,
  "n_samples": 12161,
  "feature_columns": ["depth", "event_density", "needs_open", "resources_nearby", "weather_score", "distance_to_coast"],
  "target_type": "rule-based (severity only)",
  "trained_at": "2026-09-07T10:15:00Z"
}
```

---

## Próximos pasos

1. Enriquecer dataset con features contextuales (event_density, needs_open, resources_nearby, weather_score)
2. Recopilar datos observados de incidentes reales
3. Crear target basado en tiempo de respuesta, escalada, impacto
4. Re-entrenar con target observado
5. Comparar ambos modelos
