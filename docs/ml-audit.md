# Auditoría ML — Anexo Risk 2.x

**Fecha:** 2026-09-07
**Estado:** FASE A completada
**Pipeline:** `backend/ml/pipeline.py`

---

## 1. Estado actual del pipeline

### Componentes
- **Modelo:** GradientBoostingClassifier (100 estimadores)
- **Features:** 10 columnas
- **Target:** `priority_level` (critico/alto/medio/bajo)
- **Split:** 80/20 stratificado
- **Scaler:** StandardScaler

### Features utilizadas
| # | Feature | Tipo | Origen |
|---|---------|------|--------|
| 1 | severity | float 0-1 | Evento |
| 2 | magnitude | float | Evento |
| 3 | depth | float | Evento |
| 4 | latitude | float | Evento |
| 5 | longitude | float | Evento |
| 6 | event_density | float 0-1 | Calculado |
| 7 | needs_open | int | Necesidades |
| 8 | resources_nearby | int | Recursos |
| 9 | weather_score | float 0-1 | Meteorología |
| 10 | distance_to_coast | float km | Calculado |

---

## 2. Problemas identificados

### PROBLEMA CRÍTICO: Data Leakage

**Ubicación:** `pipeline.py:84-105` y `pipeline.py:68-81`

El target se genera con la fórmula:
```python
score = severity * 0.5 + min(needs / 5, 1.0) * 0.3 + density * 0.2
```

Pero las features incluyen:
- `severity` (feature #1)
- `needs_open` (feature #7)
- `event_density` (feature #6)

**Impacto:** El modelo está memorizando las reglas que generan el target. No está aprendiendo un patrón generalizable. Es equivalente a preguntarle a alguien "¿cuál es la respuesta?" y luego evaluar si la respuesta es correcta.

** severidad:** ALTA — invalida cualquier métrica de evaluación reporting actual.

### PROBLEMA ALTO: Target derivado de reglas

**Ubicación:** `pipeline.py:84-105`

El target no proviene de observaciones reales (escalada, resolución, impacto medido). Proviene de una fórmula determinista.

**Impacto:** El modelo aprende las reglas del Risk Engine, no la realidad operacional. No se puede presentar como "predicción" de prioridad real.

### PROBLEMA MEDIO: geographical bias

**Ubicación:** `pipeline.py:309-328`

`_estimate_distance_to_coast()` solo cubre 9 puntos de la costa española:
```python
coast_points = [
    (36.0, -5.0), (37.0, -7.0), (38.0, -9.0),
    (39.0, -9.5), (40.0, -9.0), (41.0, -9.0),
    (42.0, -9.0), (43.0, -2.0), (44.0, -1.0),
]
```

**Impacto:** Para eventos fuera de España, el valor `distance_to_coast` es inútil o engañoso.

### PROBLEMA MEDIO: Features sin variación

Las features `latitude` y `longitude` son coordenadas crudas. No son útiles como features para un modelo de clasificación (el modelo no puede generalizar "lat 40.4 = crítico").

### PROBLEMA BAJO: Sin baseline comparison

No se compara el modelo contra:
- Majority class
- Reglas simples (el propio target formula)
- Dummy classifier

### PROBLEMA BAJO: Métricas incompletas

Solo se reportan accuracy y F1 weighted. Faltan:
- Confusion matrix
- Per-class precision/recall
- ROC-AUC (si aplica)
- Feature importance documentada

---

## 3. Dataset

### Fuentes declaradas
- USGS Earthquake Catalog (CSV feed)
- Smithsonian Global Volcanism Program (WFS)

### Tamaño
~300 muestras declaradas

### Distribución de clases
Generada por las reglas del target (no observada):

| Clase | Generada por reglas |
|-------|-------------------|
| critico | score >= 0.7 |
| alto | score >= 0.5 |
| medio | score >= 0.3 |
| bajo | score < 0.3 |

---

## 4. Recomendaciones

### INMEDIATO (antes de FASE B)

1. **Eliminar leakage:** Quitar `needs_open`, `event_density`, y `severity` del target generation O crear un target que no dependa de las features.

2. **Opción A (recomendada):** Generar target usando SOLO `severity` (que es la feature más directa):
   ```python
   score = severity  # Solo severidad del evento
   ```
   Esto elimina el leakage pero reduce la utilidad del modelo.

3. **Opción B:** Usar un target observado cuando haya datos históricos reales (necesidades escaladas, impacto medido).

4. **Eliminar features no útiles:** `latitude`, `longitude` no deben ser features del modelo.

### CORTO PLAZO

5. **Añadir baseline:** Comparar contra majority class y reglas simples.

6. **Confusion matrix:** Generar y documentar.

7. **Feature importance:** Documentar con caveats (no implica causalidad).

8. **geographical bias:** Eliminar `distance_to_coast` o hacerla global (no solo España).

### MEDIANO PLAZO

9. **Target observado:** Cuando exista histórico de incidentes reales, usar:
   - Tiempo de respuesta
   - Número de necesidades generadas
   - Escalada a emergencia mayor
   - Impacto económico medido

10. **Documentación:** Dejar claro en toda presentación que el target es rule-based.

---

## 5. Veredicto

### El ML actual NO es un modelo predictivo válido

**Razón:** Data leakage + target derivado de reglas.

### Lo que SÍ es útil

- La infraestructura del pipeline (features, train, predict, save) está bien construida
- El Risk Engine determinista como baseline es válido
- La integración con el risk engine está preparada
- El pathway hacia ML real está abierto

### Lo que se debe documentar

En toda presentación, API response, y documentación:

> "El modelo actual aprende las reglas del Risk Engine determinista. Las métricas de accuracy reflejan la capacidad de memorizar esas reglas, no de predecir resultados reales. Se requieren datos observados para una validación genuina."

---

## 6. Acción inmediata recomendada

1. Corregir el pipeline para eliminar leakage
2. Entrenar modelo corregido
3. Generar baseline comparison
4. Documentar en `docs/ml-evaluation.md`
5. Continuar con FASE B (ML explicable) sobre la base corregida

---

## 7. Aprobación para continuar

Esta auditoría está lista para ser revisada y aprobada antes de proceder a las correcciones del pipeline.
