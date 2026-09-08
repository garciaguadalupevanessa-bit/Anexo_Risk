// Timeline — incident event history (real API + fallback, horizontal layout)
import { escapeHtml } from "../shared/config.js";

const EVENT_ICONS = {
  detected: "📍",
  evaluated: "📊",
  need_created: "📋",
  assigned: "🎯",
  delivered: "✅",
  resolved: "🏁",
  cancelled: "❌",
};

const EVENT_COLORS = {
  detected: "var(--sev-moderada)",
  evaluated: "var(--blue)",
  need_created: "var(--sev-alta)",
  assigned: "var(--success)",
  delivered: "var(--success)",
  resolved: "var(--success)",
  cancelled: "var(--text-muted)",
};

const EVENT_LABELS = {
  detected: "Detectado",
  evaluated: "Evaluado",
  need_created: "Necesidad",
  assigned: "Asignado",
  delivered: "Entregado",
  resolved: "Resuelto",
  cancelled: "Cancelado",
};

export function renderTimeline(container, params) {
  if (!container) return;

  if (params?.events && Array.isArray(params.events) && params.events.length > 0) {
    renderRealTimeline(container, params.events);
    return;
  }

  const events = [];
  if (params?.timestamp) {
    events.push({ time: params.timestamp, label: "Evento reportado", icon: "📍" });
  }
  events.push({ time: new Date().toISOString(), label: "Análisis generado", icon: "📊" });

  container.innerHTML = `
    <div class="timeline">
      <div class="timeline__title">Cronología</div>
      ${events.map((e, i) => `
        <div class="timeline__item">
          <div class="timeline__dot"></div>
          ${i < events.length - 1 ? '<div class="timeline__line"></div>' : ""}
          <div class="timeline__content">
            <span class="timeline__icon">${e.icon}</span>
            <span class="timeline__label">${escapeHtml(e.label)}</span>
            <span class="timeline__time">${formatTime(e.time)}</span>
          </div>
        </div>`).join("")}
    </div>`;
}

function renderRealTimeline(container, events) {
  // Horizontal timeline for 4+ events, vertical for fewer
  const useHorizontal = events.length >= 4;

  if (useHorizontal) {
    renderHorizontalTimeline(container, events);
  } else {
    renderVerticalTimeline(container, events);
  }
}

function renderHorizontalTimeline(container, events) {
  const statusOrder = ["detected", "evaluated", "need_created", "assigned", "delivered", "resolved"];
  const lastEvent = events[events.length - 1];
  const currentStage = statusOrder.indexOf(lastEvent?.event_type) ?? 0;

  container.innerHTML = `
    <div class="timeline-horizontal">
      <div class="timeline-horizontal__title">Ciclo de Vida del Incidente</div>
      <div class="timeline-horizontal__track">
        ${statusOrder.map((stage, i) => {
          const icon = EVENT_ICONS[stage] || "📌";
          const color = EVENT_COLORS[stage] || "var(--text-muted)";
          const label = EVENT_LABELS[stage] || stage;
          const isCompleted = i <= currentStage;
          const isCurrent = i === currentStage;
          const event = events.find(e => e.event_type === stage);
          const time = event?.created_at;

          return `
            <div class="timeline-horizontal__step ${isCompleted ? "timeline-horizontal__step--completed" : ""} ${isCurrent ? "timeline-horizontal__step--current" : ""}">
              <div class="timeline-horizontal__node" style="${isCompleted ? `background:${color};border-color:${color};` : ""}">
                <span style="font-size:10px;">${icon}</span>
              </div>
              ${i < statusOrder.length - 1 ? `<div class="timeline-horizontal__connector ${isCompleted ? "timeline-horizontal__connector--active" : ""}"></div>` : ""}
              <div class="timeline-horizontal__label">${escapeHtml(label)}</div>
              ${time ? `<div class="timeline-horizontal__time">${formatTime(time)}</div>` : ""}
            </div>`;
        }).join("")}
      </div>
    </div>`;

  // Also render event details below in a separate container
  const detailContainer = document.createElement("div");
  detailContainer.className = "timeline-detail";
  container.appendChild(detailContainer);
  renderVerticalTimeline(detailContainer, events, true);
}

function renderVerticalTimeline(container, events, compact = false) {
  container.innerHTML = `
    ${!compact ? '<div class="timeline"><div class="timeline__title">Cronología</div>' : '<div class="timeline" style="margin-top:var(--space-sm);">'}
      ${events.map((e, i) => {
        const icon = EVENT_ICONS[e.event_type] || "📌";
        const color = EVENT_COLORS[e.event_type] || "var(--text-muted)";
        const label = EVENT_LABELS[e.event_type] || e.event_type;
        return `
          <div class="timeline__item">
            <div class="timeline__dot" style="background:${color};"></div>
            ${i < events.length - 1 ? `<div class="timeline__line" style="background:${color};"></div>` : ""}
            <div class="timeline__content">
              <span class="timeline__icon">${icon}</span>
              <div style="flex:1;">
                <span class="timeline__label">${escapeHtml(e.description || label)}</span>
                ${e.priority_score != null ? `<span style="font-size:0.65rem;color:${color};font-weight:700;margin-left:4px;">${Number(e.priority_score).toFixed(0)}pts</span>` : ""}
                <div class="timeline__time">${formatTime(e.created_at)}</div>
              </div>
            </div>
          </div>`;
      }).join("")}
      ${events.length === 0 ? '<div class="state-empty" style="padding:var(--space-sm);"><p style="font-size:var(--text-xs);">Sin eventos registrados</p></div>' : ""}
    </div>`;
}

function formatTime(iso) {
  if (!iso) return "";
  try {
    const d = new Date(iso.replace(" ", "T"));
    if (isNaN(d.getTime())) return iso;
    return d.toLocaleString("es-ES", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
  } catch { return iso; }
}
