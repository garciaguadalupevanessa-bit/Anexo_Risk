"""Risk Engine determinista y explicable.

Calcula scores de riesgo basados en reglas ponderadas.
Presentado como "Índice de Prioridad Operacional" — no como probabilidad real.

Fuentes:
- rules-v1: scoring determinista basado en reglas
- ml-v1: predicción ML (experimental, target rule-based)
- rules+ml: combinación ponderada cuando ML tiene confianza suficiente

Incluye RiskAssessment con methodology_version, source, generated_at para trazabilidad.
"""
from __future__ import annotations

from datetime import datetime, timezone

from config import (
    RISK_ENGINE_SEVERITY_WEIGHT,
    RISK_ENGINE_EXPOSURE_WEIGHT,
    RISK_ENGINE_WEATHER_WEIGHT,
    RISK_ENGINE_DENSITY_WEIGHT,
    RISK_ENGINE_NEEDS_WEIGHT,
    RISK_ENGINE_TREND_WEIGHT,
)

METHODOLOGY_RULES = "rules-v1"
METHODOLOGY_ML = "ml-v1"
METHODOLOGY_COMBINED = "rules+ml-v1"


def calculate_risk_score(
    severity: float = 0.0,
    exposure: float = 0.0,
    weather: float = 0.0,
    event_density: float = 0.0,
    needs_open: int = 0,
    trend: float = 0.0,
    ml_prediction: dict | None = None,
) -> dict:
    """Calcula score de riesgo combinando reglas + ML opcional.

    Parameters
    ----------
    severity : float
        Score de severidad 0-1.
    exposure : float
        Score de exposición 0-1.
    weather : float
        Score meteorológico 0-1.
    event_density : float
        Score de densidad de eventos 0-1.
    needs_open : int
        Número de necesidades abiertas.
    trend : float
        Tendencia de actividad -1 a 1.
    ml_prediction : dict or None
        Predicción ML completa de predict_with_explanation().

    Returns
    -------
    dict
        RiskAssessment con combined_score, priority_level, factors, explanation,
        source, methodology_version, generated_at, ml_info.
    """
    needs_factor = min(needs_open / 10, 1.0)

    rule_score = (
        severity * RISK_ENGINE_SEVERITY_WEIGHT
        + exposure * RISK_ENGINE_EXPOSURE_WEIGHT
        + weather * RISK_ENGINE_WEATHER_WEIGHT
        + event_density * RISK_ENGINE_DENSITY_WEIGHT
        + needs_factor * RISK_ENGINE_NEEDS_WEIGHT
        + max(trend, 0) * RISK_ENGINE_TREND_WEIGHT
    )

    rule_score_100 = round(rule_score * 100, 1)

    factors = _build_rule_factors(severity, exposure, weather, event_density, needs_open, trend)

    ml_score = None
    ml_confidence = None
    ml_info = None
    source = "rules"
    methodology = METHODOLOGY_RULES

    if ml_prediction and ml_prediction.get("available"):
        ml_pred = ml_prediction.get("prediction")
        ml_conf = ml_prediction.get("confidence", 0)

        ml_level_map = {"critico": 0.9, "alto": 0.7, "medio": 0.5, "bajo": 0.2, "informativo": 0.1}
        ml_score = ml_level_map.get(ml_pred, 0.5) if ml_pred else 0.5
        ml_confidence = ml_conf

        if ml_confidence >= 0.6:
            combined = rule_score_100 * 0.6 + ml_score * 100 * 0.4
            combined = round(combined, 1)
            source = "rules+ml"
            methodology = METHODOLOGY_COMBINED
            factors.append(
                f"ML contribuye: prioridad {ml_pred} "
                f"(confianza: {ml_confidence:.0%})"
            )
            top_feats = ml_prediction.get("top_features", [])
            if top_feats:
                feat_names = [f["name"] for f in top_feats[:2]]
                factors.append(
                    f"Factores ML: {', '.join(feat_names)}"
                )
        else:
            combined = rule_score_100
            factors.append("ML no disponible (confianza insuficiente)")
    else:
        combined = rule_score_100
        if ml_prediction and not ml_prediction.get("available"):
            reason = ml_prediction.get("disclaimer", "Modelo no cargado")
            factors.append(f"ML no disponible: {reason}")

    priority_level = _score_to_level(combined)
    now = datetime.now(timezone.utc).isoformat()

    explanation = _build_explanation(
        rule_score=rule_score_100,
        ml_score=round(ml_score * 100, 1) if ml_score is not None else None,
        ml_confidence=ml_confidence,
        factors=factors,
        source=source,
    )

    return {
        "combined_score": combined,
        "priority_level": priority_level,
        "rule_score": rule_score_100,
        "ml_risk_score": round(ml_score * 100, 1) if ml_score is not None else None,
        "ml_confidence": round(ml_confidence, 3) if ml_confidence is not None else None,
        "factors": factors,
        "explanation": explanation,
        "source": source,
        "methodology_version": methodology,
        "generated_at": now,
        "ml_info": ml_prediction if ml_prediction else None,
    }


def _build_rule_factors(
    severity: float,
    exposure: float,
    weather: float,
    event_density: float,
    needs_open: int,
    trend: float,
) -> list[str]:
    """Construye factores del scoring determinista."""
    factors = []
    if severity >= 0.8:
        factors.append("Severidad alta")
    elif severity >= 0.5:
        factors.append("Severidad moderada")

    if exposure >= 0.7:
        factors.append("Elevada exposición")
    elif exposure >= 0.4:
        factors.append("Exposición moderada")

    if weather >= 0.6:
        factors.append("Condiciones meteorológicas adversas")

    if event_density >= 0.6:
        factors.append("Alta densidad de eventos")

    if needs_open >= 5:
        factors.append(f"{needs_open} necesidades abiertas")
    elif needs_open >= 1:
        factors.append(f"{needs_open} necesidades pendientes")

    if trend > 0.3:
        factors.append("Tendencia creciente")
    elif trend < -0.3:
        factors.append("Tendencia decreciente")

    return factors


def _score_to_level(score: float) -> str:
    if score >= 80:
        return "critico"
    if score >= 60:
        return "alto"
    if score >= 40:
        return "medio"
    if score >= 20:
        return "bajo"
    return "informativo"


def _build_explanation(
    rule_score: float,
    ml_score: float | None,
    ml_confidence: float | None,
    factors: list[str],
    source: str,
) -> str:
    """Construye explicación textual del riesgo."""
    lines = [f"Fuente: {source}"]

    if source == "rules+ml":
        lines.append(f"Reglas: {rule_score}")
        lines.append(f"ML: {ml_score:.1f}")
        lines.append(f"Confianza ML: {ml_confidence:.0%}")
        lines.append("Combinación: 60% reglas + 40% ML")
    elif source == "ml":
        lines.append(f"ML: {ml_score:.1f}")
        lines.append(f"Confianza: {ml_confidence:.0%}")
    else:
        lines.append(f"Score: {rule_score}")

    lines.append("")
    if factors:
        lines.append("Factores:")
        for f in factors:
            lines.append(f"  - {f}")
    else:
        lines.append("Sin factores significativos.")

    return "\n".join(lines)
