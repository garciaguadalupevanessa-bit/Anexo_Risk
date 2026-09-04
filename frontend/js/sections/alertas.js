// Alertas section — fetchAlerts, initAlerts, notifyCritical
import { SeverityLevel, normalizeGDACSAlerts } from "../core/normalization/index.js";
import { apiGet, formatDate, SEV_CLASS_MAP, SEVERITY_LABELS, matchesRegion, escapeHtml } from "../shared/config.js";

const NOTIFIED_KEY = "anexo_notified_alerts";
const notifiedIds = new Set(JSON.parse(sessionStorage.getItem(NOTIFIED_KEY) || "[]"));

export function notifyCritical(alerts) {
  const container = document.getElementById("notification-container");
  if (!container) return;
  const criticas = alerts.filter(e => {
    return (e.severity.level === SeverityLevel.CRITICAL || e.severity.level === SeverityLevel.HIGH) && !notifiedIds.has(e.id);
  });
  criticas.forEach(e => {
    notifiedIds.add(e.id);
    sessionStorage.setItem(NOTIFIED_KEY, JSON.stringify([...notifiedIds]));
    const isCritica = e.severity.level === SeverityLevel.CRITICAL;
    const icon = isCritica ? "🚨" : "⚠️";
    const div = document.createElement("div");
    div.className = isCritica ? "notification notification--critica" : "notification";
    div.setAttribute("role", "alert");
    div.innerHTML = `
      <div class="notification__header">
        <span class="notification__icon" aria-hidden="true">${icon}</span>
        <span class="notification__title">Alerta ${isCritica ? "Crítica" : "de Atención"}</span>
      </div>
      <div class="notification__body">${escapeHtml(e.title || "Alerta sin título")}<br><small style="color:var(--text-muted)">${escapeHtml(e.country)}</small></div>
      <div class="notification__footer">
        <span class="notification__country">${escapeHtml(e.country)}</span>
        <button class="notification__close" aria-label="Cerrar notificación" onclick="this.closest('.notification').classList.add('notification--exit'); setTimeout(()=>this.closest('.notification').remove(), 300)">✕</button>
      </div>`;
    container.appendChild(div);
    setTimeout(() => {
      if (div.parentNode) {
        div.classList.add("notification--exit");
        setTimeout(() => div.remove(), 300);
      }
    }, 10000);
  });
}

export async function fetchAlerts() {
  const container = document.getElementById("alerts-container");
  if (!container) return;
  container.innerHTML = '<div class="state-loading"><p>Cargando alertas...</p></div>';

  const region = document.getElementById("region-filter")?.value;
  const tipo = document.getElementById("type-filter")?.value;
  const sev = document.getElementById("severity-filter")?.value;
  const pais = document.getElementById("country-filter")?.value?.trim();

  try {
    let raw = await apiGet("/api/alertas");
    if (!raw || !raw.length) {
      container.innerHTML = '<div class="state-empty"><h3>No hay alertas activas</h3><p>Consulta más tarde o ajusta los filtros.</p></div>';
      return;
    }

    let data = normalizeGDACSAlerts(raw);

    if (region && region !== "world") {
      data = data.filter(e => matchesRegion(e.country, region));
    }
    if (tipo) data = data.filter(e => e.type.category.toLowerCase() === tipo.toLowerCase());
    if (sev) data = data.filter(e => e.severity.level === sev.toLowerCase());
    if (pais) data = data.filter(e => (e.country || "").toLowerCase().includes(pais.toLowerCase()));

    notifyCritical(data);
    if (!data.length) {
      container.innerHTML = '<div class="state-empty"><h3>No hay alertas para estos filtros</h3><p>Prueba con otra zona o tipo.</p></div>';
      return;
    }
    container.innerHTML = data.map(e => {
      const sev = e.severity.level;
      const tipo = e.type.label;
      const badgeCls = SEV_CLASS_MAP[sev] || "sin-dato";
      const entityJson = escapeHtml(JSON.stringify(e));
      return `
        <div class="alert-card alert-card--${badgeCls}" role="listitem" tabindex="0"
             onclick="const e=JSON.parse(this.dataset.entity);openDrawer(e.title||'Alerta',renderDrawerFields(e))"
             data-entity='${entityJson}'
             onkeydown="if(event.key==='Enter'){this.click()}">
          <div class="alert-card__header">
            <div class="alert-card__title">${escapeHtml(e.title || "Alerta")}</div>
            <span class="sev-badge sev-badge--${badgeCls}" aria-label="Severidad: ${SEVERITY_LABELS[sev] || sev}">${SEVERITY_LABELS[sev] || sev}</span>
          </div>
          <div class="alert-card__meta">
            <span>${escapeHtml(tipo)}</span>
            <span>${escapeHtml(e.country || "País desconocido")}</span>
            <span>${formatDate(e.timestamp)}</span>
          </div>
          <div class="alert-card__desc">${escapeHtml(e.description)}</div>
          ${e.extras.enlace ? `<a href="${escapeHtml(e.extras.enlace)}" target="_blank" rel="noopener noreferrer" class="btn btn--ghost btn--sm" style="margin-top:8px;" onclick="event.stopPropagation()">Ver detalle →</a>` : ""}
        </div>`;
    }).join("");
  } catch (err) {
    console.error("Alerts error:", err);
    container.innerHTML = '<div class="state-error"><h3>Error al cargar alertas</h3><p>Comprueba la conexión con el servidor.</p><button class="btn btn--ghost" onclick="fetchAlerts()">Reintentar</button></div>';
  }
}
window.fetchAlerts = fetchAlerts;

export function initAlerts() {
  document.getElementById("region-filter")?.addEventListener("change", fetchAlerts);
  document.getElementById("type-filter")?.addEventListener("change", fetchAlerts);
  document.getElementById("severity-filter")?.addEventListener("change", fetchAlerts);
  document.getElementById("country-filter")?.addEventListener("keydown", e => { if (e.key === "Enter") fetchAlerts(); });
}
