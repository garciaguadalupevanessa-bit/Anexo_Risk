# Evaluación ML — Anexo Risk 2.x

**Fecha:** 2026-09-07 10:07 UTC
**Muestras:** 12166
**Features:** 6

## Advertencia importante

> El target actual está generado por reglas deterministas (solo severidad).
> Las métricas reflejan la capacidad del modelo de aprender esas reglas,
> NO de predecir resultados reales de emergencias.
> Se requieren datos observados para una validación genuina.

## Métricas

| Métrica | Valor |
|---------|-------|
| Accuracy | 0.9224 |
| F1 Weighted | 0.9068 |

## Baseline (Majority Class)

| Métrica | Valor |
|---------|-------|
| Accuracy | 0.8759 |
| F1 Weighted | 0.818 |

## Confusion Matrix

| | alto | bajo | critico | medio |
|---|---|---|---|---|
| alto | 0 | 33 | 1 | 23 |
| bajo | 2 | 2109 | 8 | 13 |
| critico | 0 | 19 | 2 | 3 |
| medio | 1 | 85 | 1 | 134 |

## Feature Importance

> La importancia NO implica causalidad.

| Feature | Importancia |
|---------|-------------|
| depth | 0.6355 |
| distance_to_coast | 0.3645 |
| event_density | 0.0000 |
| needs_open | 0.0000 |
| resources_nearby | 0.0000 |
| weather_score | 0.0000 |

## Limitaciones

- Target rule-based, no observado
- _estimate_distance_to_coast() es una aproximación global simplificada
- Sin separación temporal/espacial en train/test
- Sin evaluación con datos reales de emergencias

## Próximos pasos

1. Recopilar datos observados de incidentes reales
2. Crear target basado en tiempo de respuesta, escalada, impacto
3. Re-entrenar con target observado
4. Comparar ambos modelos
