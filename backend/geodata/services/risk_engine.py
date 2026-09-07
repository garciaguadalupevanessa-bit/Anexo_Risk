"""Risk Engine determinista y explicable.

Calcula scores de riesgo basados en reglas ponderadas.
Presentado como "Índice de Prioridad Operacional" — no como probabilidad real.

Incluye RiskAssessment con methodology_version para trazabilidad.
"""
from __future__ import annotations

from datetime import datetime, timezone

METHODOLOGY_VERSION = "rules-v1"


def calculate_risk_score(
    severity: float = 0.0,
    exposure: float = 0.0,
    weather: float = 0.0,
    event_density: float = 0.0,
    needs_open: int = 0,
    trend: float = 0.0,
    ml_score: float | None = None,
    ml_confidence: float | None = None,
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
        Tendencia de actividad -1 a 1 (negativo = decreciente).
    ml_score : float or None
        Score ML 0-1 si disponible.
    ml_confidence : float or None
        Confianza del modelo 0-1.

    Returns
    -------
    dict
        RiskAssessment con combined_score, priority_level, factors, explanation,
        methodology_version, generated_at.
    """
    needs_factor = min(needs_open / 10, 1.0)

    rule_score = (
        severity * 0.30
        + exposure * 0.25
        + weather * 0.15
        + event_density * 0.15
        + needs_factor * 0.10
        + max(trend, 0) * 0.05
    )

    rule_score_100 = round(rule_score * 100, 1)

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

    if ml_score is not None and ml_confidence is not None and ml_confidence >= 0.6:
        combined = (rule_score_100 * 0.6 + ml_score * 100 * 0.4)
        combined = round(combined, 1)
        factors.append(f"ML contribuye (confianza: {ml_confidence:.0%})")
        explanation = _build_explanation(rule_score_100, ml_score * 100, ml_confidence, factors)
        source = "rules+ml"
    else:
        combined = rule_score_100
        if ml_confidence is not None and ml_confidence < 0.6:
            factors.append("Predicción ML no disponible (confianza insuficiente)")
        explanation = _build_explanation(rule_score_100, None, None, factors)
        source = "rules"

    priority_level = _score_to_level(combined)
    now = datetime.now(timezone.utc).isoformat()

    return {
        "combined_score": combined,
        "priority_level": priority_level,
        "rule_score": rule_score_100,
        "ml_risk_score": round(ml_score * 100, 1) if ml_score is not None else None,
        "ml_confidence": round(ml_confidence, 3) if ml_confidence is not None else None,
        "factors": factors,
        "explanation": explanation,
        "source": source,
        "methodology_version": METHODOLOGY_VERSION,
        "generated_at": now,
    }


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
) -> str:
    lines = [f"Reglas: {rule_score}"]
    if ml_score is not None:
        lines.append(f"ML: {ml_score:.1f}")
        lines.append(f"Confianza del modelo: {ml_confidence:.0%}")
    lines.append("")
    if factors:
        lines.append("Factores:")
        for f in factors:
            lines.append(f"  - {f}")
    else:
        lines.append("Sin factores significativos.")
    return "\n".join(lines)
