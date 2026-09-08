// Risk Card — visual risk score with factor breakdown + GeoRisk scientific risk
import { escapeHtml } from "../shared/config.js";

const SEV_MAP = {
  critica: { label: "CRÍTICO", color: "var(--sev-critica)", bg: "var(--sev-critica-bg)", border: "var(--sev-critica-border)" },
  alta: { label: "ALTA", color: "var(--sev-alta)", bg: "var(--sev-alta-bg)", border: "var(--sev-alta-border)" },
  moderada: { label: "MEDIA", color: "var(--sev-moderada)", bg: "var(--sev-moderada-bg)", border: "var(--sev-moderada-border)" },
  informativa: { label: "BAJA", color: "var(--sev-informativa)", bg: "var(--sev-informativa-bg)", border: "var(--sev-informativa-border)" },
};

function getScoreColor(score) {
  if (score >= 80) return SEV_MAP.critica;
  if (score >= 60) return SEV_MAP.alta;
  if (score >= 40) return SEV_MAP.moderada;
  return SEV_MAP.informativa;
}

export function renderRiskCard(container, risk, explanation, georisk) {
  if (!container) return;
  const score = risk?.combined_score ?? 0;
  const sev = getScoreColor(score);
  const source = risk?.source || "rules";
  const methodology = risk?.methodology_version || "rules-v1";

  const factors = explanation?.factors || [];
  const breakdown = explanation?.score_breakdown || {};

  const factorBars = Object.entries(breakdown).map(([key, val]) => {
    const label = { severity: "Severidad", exposure: "Exposición", event_density: "Densidad", trend: "Tendencia" }[key] || key;
    const pct = Math.min(Math.max(val * 100, 0), 100);
    return `
      <div class="risk-factor">
        <div class="risk-factor__header">
          <span class="risk-factor__label">${escapeHtml(label)}</span>
          <span class="risk-factor__value">${pct.toFixed(0)}%</span>
        </div>
        <div class="risk-factor__track">
          <div class="risk-factor__fill" style="width:${pct}%;background:${sev.color};"></div>
        </div>
      </div>`;
  }).join("");

  // GeoRisk scientific risk (if available)
  const georiskScore = georisk?.risk_score ?? null;
  const georiskLevel = georisk?.risk_level || null;
  const georiskStatus = georisk?.status || "unavailable";
  const georiskSev = georiskScore !== null ? getScoreColor(georiskScore) : null;

  container.innerHTML = `
    <div class="risk-card" style="border:1px solid ${sev.border};background:${sev.bg};">
      <div class="risk-card__header">
        <span class="risk-card__icon">⚠️</span>
        <span class="risk-card__label">PRIORIDAD OPERACIONAL</span>
      </div>
      <div class="risk-card__score" style="color:${sev.color};">${score.toFixed(0)}</div>
      <div class="risk-card__level badge badge--${source === 'ml' ? 'info' : 'default'}" style="color:${sev.color};">
        ${sev.label}
      </div>
      <div class="risk-card__meta">
        Fuente: <strong>${escapeHtml(source)}</strong> · ${escapeHtml(methodology)}
      </div>
      ${factorBars ? `<div class="risk-card__factors">${factorBars}</div>` : ""}
      ${factors.length ? `
      <div class="risk-card__factors-list">
        ${factors.map(f => `<div class="risk-card__factor-item">• ${escapeHtml(f)}</div>`).join("")}
      </div>` : ""}
    </div>

    ${georiskScore !== null ? `
    <div class="risk-card risk-card--scientific" style="border:1px solid var(--blue-border);background:var(--blue-bg);margin-top:var(--space-sm);">
      <div class="risk-card__header">
        <span class="risk-card__icon">🔬</span>
        <span class="risk-card__label">RIESGO CIENTÍFICO</span>
      </div>
      <div class="risk-card__score" style="color:${georiskSev.color};">${georiskScore.toFixed(0)}</div>
      <div class="risk-card__level" style="color:${georiskSev.color};">
        ${georiskSev.label}
      </div>
      <div class="risk-card__meta">
        Fuente: <strong>GeoRisk Finder</strong> · Análisis territorial
      </div>
    </div>` : georiskStatus === "unavailable" ? `
    <div class="risk-card risk-card--unavailable" style="border:1px dashed var(--border);margin-top:var(--space-sm);opacity:0.7;">
      <div class="risk-card__header">
        <span class="risk-card__icon">🔬</span>
        <span class="risk-card__label">RIESGO CIENTÍFICO</span>
      </div>
      <div style="padding:var(--space-sm);text-align:center;">
        <span style="font-size:var(--text-xs);color:var(--text-muted);">GeoRisk no disponible</span>
      </div>
    </div>` : ""}
  `;
}
