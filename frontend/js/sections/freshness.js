// Freshness — data source freshness indicators
import { escapeHtml } from "../shared/config.js";

const SOURCES = {
  alerts: { label: "Alertas GDACS", maxAge: 300000 },
  firms: { label: "NASA FIRMS", maxAge: 600000 },
  clima: { label: "Meteorología", maxAge: 900000 },
  needs: { label: "Necesidades", maxAge: 120000 },
  incidents: { label: "Incidentes", maxAge: 60000 },
};

let freshnessState = {};

export function updateFreshness(source, ageMs) {
  freshnessState[source] = { age: ageMs, updated: Date.now() };
  renderFreshnessPanel();
  renderFreshnessInline();
}

function getStatus(key) {
  const meta = SOURCES[key];
  const state = freshnessState[key];
  const age = state?.age ?? null;

  if (age === null) return { label: "Sin datos", class: "freshness--offline" };
  if (age < meta.maxAge) return { label: "En tiempo real", class: "freshness--live" };
  if (age < meta.maxAge * 3) return { label: `Desactualizado (${Math.floor(age / 60000)} min)`, class: "freshness--stale" };
  return { label: "Sin conexión", class: "freshness--offline" };
}

export function renderFreshnessPanel() {
  const container = document.getElementById("freshness-panel");
  if (!container) return;

  container.innerHTML = Object.entries(SOURCES).map(([key, meta]) => {
    const status = getStatus(key);
    return `
      <div class="freshness ${status.class}">
        <span class="freshness__dot"></span>
        <span class="freshness__label">${escapeHtml(meta.label)}</span>
        <span class="freshness__status">${escapeHtml(status.label)}</span>
      </div>`;
  }).join("");
}

function renderFreshnessInline() {
  const el = document.getElementById("sb-freshness-text");
  const dotEl = document.querySelector("#sb-freshness .freshness__dot");
  if (!el) return;

  const sources = Object.keys(SOURCES);
  const liveCount = sources.filter(k => freshnessState[k]?.age != null && freshnessState[k].age < SOURCES[k].maxAge).length;
  const staleCount = sources.filter(k => freshnessState[k]?.age != null && freshnessState[k].age >= SOURCES[k].maxAge).length;

  if (liveCount === sources.length) {
    el.textContent = "Todo actualizado";
    if (dotEl) dotEl.style.background = "var(--success)";
  } else if (staleCount > 0) {
    el.textContent = `${staleCount} fuentes desactualizadas`;
    if (dotEl) dotEl.style.background = "var(--stale)";
  } else {
    el.textContent = "Actualizado";
    if (dotEl) dotEl.style.background = "var(--success)";
  }
}

window._updateFreshness = updateFreshness;
