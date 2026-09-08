// Decision Center — loads context from backend, renders progressive disclosure sections
import { API_BASE, apiGet, escapeHtml } from "../shared/config.js";
import { renderRiskCard } from "./risk-card.js";
import { renderTimeline } from "./timeline.js";

const SECTION_TITLES = {
  "01-situacion": { num: "01", label: "Situación", icon: "📡" },
  "02-contexto": { num: "02", label: "Contexto", icon: "🔍" },
  "03-impacto": { num: "03", label: "Impacto", icon: "📊" },
  "04-georisk": { num: "04", label: "Riesgo Científico", icon: "🔬" },
  "05-riesgo": { num: "05", label: "Prioridad Operacional", icon: "⚠️" },
  "06-operacion": { num: "06", label: "Operación", icon: "🎯" },
  "07-accion": { num: "07", label: "Acción", icon: "🚀" },
};

const SEV_MAP = {
  critica: { label: "Crítico", color: "var(--sev-critica)", bg: "var(--sev-critica-bg)" },
  alta: { label: "Alta", color: "var(--sev-alta)", bg: "var(--sev-alta-bg)" },
  moderada: { label: "Moderada", color: "var(--sev-moderada)", bg: "var(--sev-moderada-bg)" },
  informativa: { label: "Informativa", color: "var(--sev-informativa)", bg: "var(--sev-informativa-bg)" },
};

let _currentIncidentId = null;

export function initDecisionCenter() {
  const ctx = document.getElementById("decision-context");
  if (!ctx) return;
  _currentIncidentId = null;
  ctx.innerHTML = `
    <div class="state-empty">
      <h3>Sin incidente seleccionado</h3>
      <p>Selecciona un incidente en el mapa para ver el análisis de decisión.</p>
      <button class="btn btn--ghost btn--sm" onclick="window.loadDecisionContextDefault()" style="margin-top:var(--space-md);">📍 Análisis genérico por coordenadas</button>
    </div>`;
}

window.loadDecisionContextDefault = () => {
  const lat = 40.42;
  const lon = -3.70;
  loadDecisionContext({ lat, lon, severity: 0.5, magnitude: 0, event_type: "desconocido", source: "manual" });
};

export async function loadDecisionContext(params) {
  const ctx = document.getElementById("decision-context");
  const riskContainer = document.getElementById("risk-card-container");
  const timelineContainer = document.getElementById("timeline-container");
  if (!ctx) return;

  ctx.innerHTML = '<div class="state-loading"><p>Cargando análisis...</p></div>';

  try {
    const qs = new URLSearchParams({
      lat: params.lat, lon: params.lon,
      severity: params.severity ?? 0.5,
      magnitude: params.magnitude ?? 0,
      event_type: params.event_type ?? "desconocido",
      source: params.source ?? "manual",
    });
    const data = await apiGet(`/api/decision/context?${qs}`);
    renderDecisionSections(ctx, data);

    if (riskContainer) {
      renderRiskCard(riskContainer, data.risk, data.explanation, data.georisk);
    }
    if (timelineContainer) {
      renderTimeline(timelineContainer, params);
    }
  } catch (err) {
    ctx.innerHTML = `<div class="state-error"><p>Error cargando contexto: ${escapeHtml(err.message)}</p></div>`;
  }
}

export async function loadIncidentDecisionContext(incidentId) {
  const ctx = document.getElementById("decision-context");
  const riskContainer = document.getElementById("risk-card-container");
  const timelineContainer = document.getElementById("timeline-container");
  if (!ctx) return;

  _currentIncidentId = incidentId;
  ctx.innerHTML = '<div class="state-loading"><p>Analizando incidente...</p></div>';

  try {
    const data = await apiGet(`/api/incidents/${incidentId}`);
    const analyzeData = await apiGet(`/api/incidents/${incidentId}/analyze`);
    const context = analyzeData.decision_context;

    renderDecisionSections(ctx, context, data);

    if (riskContainer) {
      renderRiskCard(riskContainer, context.risk, context.explanation, context.georisk);
    }
    if (timelineContainer) {
      renderTimelineFromAPI(timelineContainer, incidentId);
    }
  } catch (err) {
    ctx.innerHTML = `<div class="state-error"><p>Error analizando incidente: ${escapeHtml(err.message)}</p></div>`;
  }
}

async function renderTimelineFromAPI(container, incidentId) {
  try {
    const data = await apiGet(`/api/incidents/${incidentId}/timeline`);
    const events = data.events || [];
    renderTimeline(container, { events, incidentId });
  } catch {
    renderTimeline(container, { incidentId });
  }
}

function renderDecisionSections(container, data, incidentMeta = null) {
  const { situation, context, impact, georisk, risk, operation, explanation } = data;

  const incidentBadge = incidentMeta ? `
    <div style="display:flex;align-items:center;gap:var(--space-sm);margin-bottom:var(--space-md);padding:var(--space-sm) var(--space-md);background:var(--blue-bg);border:1px solid var(--blue-border);border-radius:var(--radius-sm);">
      <span style="font-size:var(--text-sm);font-weight:700;color:var(--navy);">📍 Incidente #${incidentMeta.id}</span>
      <span style="font-size:var(--text-xs);color:var(--text-muted);">${escapeHtml(incidentMeta.title)}</span>
    </div>` : "";

  container.innerHTML = `
    ${incidentBadge}
    <div class="decision-section" data-section="01-situacion">
      ${renderSectionHeader("01-situacion")}
      <div class="decision-section__body">
        ${renderSituation(situation)}
      </div>
    </div>
    <div class="decision-section" data-section="02-contexto">
      ${renderSectionHeader("02-contexto")}
      <div class="decision-section__body decision-section__body--collapsed">
        ${renderContext(context)}
      </div>
    </div>
    <div class="decision-section" data-section="03-impacto">
      ${renderSectionHeader("03-impacto")}
      <div class="decision-section__body decision-section__body--collapsed">
        ${renderImpact(impact)}
      </div>
    </div>
    <div class="decision-section" data-section="04-georisk">
      ${renderSectionHeader("04-georisk")}
      <div class="decision-section__body decision-section__body--collapsed">
        ${renderGeoRisk(georisk)}
      </div>
    </div>
    <div class="decision-section" data-section="05-riesgo">
      ${renderSectionHeader("05-riesgo")}
      <div class="decision-section__body decision-section__body--collapsed">
        ${renderRiskSection(risk, explanation)}
      </div>
    </div>
    <div class="decision-section" data-section="06-operacion">
      ${renderSectionHeader("06-operacion")}
      <div class="decision-section__body decision-section__body--collapsed">
        ${renderOperation(operation)}
      </div>
    </div>
    <div class="decision-section" data-section="07-accion">
      ${renderSectionHeader("07-accion")}
      <div class="decision-section__body decision-section__body--collapsed">
        ${renderAction(risk, operation, incidentMeta)}
      </div>
    </div>`;

  container.querySelectorAll(".decision-section__header").forEach(header => {
    header.addEventListener("click", () => {
      const section = header.closest(".decision-section");
      const body = section?.querySelector(".decision-section__body");
      if (!body) return;
      body.classList.toggle("decision-section__body--collapsed");
      header.setAttribute("aria-expanded", !body.classList.contains("decision-section__body--collapsed"));
    });
  });

  // Auto-expand critical sections based on risk score
  const score = data?.risk?.combined_score ?? 0;
  if (score >= 60) {
    const criticalSections = ["01-situacion", "05-riesgo", "07-accion"];
    criticalSections.forEach(id => {
      const section = container.querySelector(`[data-section="${id}"]`);
      const body = section?.querySelector(".decision-section__body");
      const hdr = section?.querySelector(".decision-section__header");
      if (body) body.classList.remove("decision-section__body--collapsed");
      if (hdr) hdr.setAttribute("aria-expanded", "true");
    });
  }
}

function renderSectionHeader(sectionId) {
  const meta = SECTION_TITLES[sectionId];
  return `
    <div class="decision-section__header" role="button" tabindex="0" aria-expanded="false" aria-controls="section-body-${sectionId}">
      <span class="decision-section__num">${meta.num}</span>
      <span class="decision-section__icon">${meta.icon}</span>
      <span class="decision-section__title">${meta.label}</span>
      <svg class="decision-section__chevron" width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
        <path d="M4 6l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </div>`;
}

function renderSituation(s) {
  const sevKey = s.severity >= 0.8 ? "critica" : s.severity >= 0.5 ? "alta" : s.severity >= 0.3 ? "moderada" : "informativa";
  const sev = SEV_MAP[sevKey] || SEV_MAP.informativa;
  const loc = s.location ? `${s.location.lat.toFixed(4)}, ${s.location.lon.toFixed(4)}` : "Sin ubicación";

  return `
    <div class="decision-kpi-row">
      <div class="decision-kpi">
        <span class="decision-kpi__label">Tipo</span>
        <span class="decision-kpi__value">${escapeHtml(s.event_type)}</span>
      </div>
      <div class="decision-kpi">
        <span class="decision-kpi__label">Severidad</span>
        <span class="badge badge--${sevKey}" style="background:${sev.bg};color:${sev.color};">${sev.label}</span>
      </div>
      <div class="decision-kpi">
        <span class="decision-kpi__label">Fuente</span>
        <span class="decision-kpi__value">${escapeHtml(s.source)}</span>
      </div>
      <div class="decision-kpi">
        <span class="decision-kpi__label">Ubicación</span>
        <span class="decision-kpi__value decision-kpi__value--mono">${escapeHtml(loc)}</span>
      </div>
      ${s.magnitude ? `
      <div class="decision-kpi">
        <span class="decision-kpi__label">Magnitud</span>
        <span class="decision-kpi__value">${s.magnitude}</span>
      </div>` : ""}
      ${s.timestamp ? `
      <div class="decision-kpi">
        <span class="decision-kpi__label">Fecha</span>
        <span class="decision-kpi__value">${escapeHtml(s.timestamp)}</span>
      </div>` : ""}
    </div>`;
}

function renderContext(c) {
  const trendIcon = c.trend > 0.3 ? "📈" : c.trend < -0.3 ? "📉" : "➡️";
  const trendLabel = c.trend > 0.3 ? "Creciente" : c.trend < -0.3 ? "Decreciente" : "Estable";

  return `
    <div class="decision-kpi-row">
      <div class="decision-kpi">
        <span class="decision-kpi__label">Eventos cercanos</span>
        <span class="decision-kpi__value">${c.nearby_events_count}</span>
      </div>
      <div class="decision-kpi">
        <span class="decision-kpi__label">Densidad</span>
        <span class="decision-kpi__value">${(c.event_density * 100).toFixed(0)}%</span>
      </div>
      <div class="decision-kpi">
        <span class="decision-kpi__label">Tendencia</span>
        <span class="decision-kpi__value">${trendIcon} ${trendLabel}</span>
      </div>
    </div>
    ${c.effis ? `
    <div class="decision-kpi-row" style="margin-top:var(--space-sm);">
      <div class="decision-kpi">
        <span class="decision-kpi__label">EFFIS Peligro</span>
        <span class="decision-kpi__value">${escapeHtml(c.effis.danger_level || "N/D")}</span>
      </div>
      ${c.effis.fire_weather_index != null ? `
      <div class="decision-kpi">
        <span class="decision-kpi__label">FWI</span>
        <span class="decision-kpi__value">${c.effis.fire_weather_index}</span>
      </div>` : ""}
    </div>` : ""}
    ${c.weather ? `
    <div class="decision-kpi-row" style="margin-top:var(--space-sm);">
      <div class="decision-kpi">
        <span class="decision-kpi__label">Meteorología</span>
        <span class="decision-kpi__value">${escapeHtml(c.weather.summary || "Sin datos")}</span>
      </div>
    </div>` : ""}`;
}

function renderImpact(imp) {
  return `
    <div class="decision-kpi-row">
      <div class="decision-kpi">
        <span class="decision-kpi__label">Exposición</span>
        <span class="decision-kpi__value">${(imp.exposure_score * 100).toFixed(0)}%</span>
      </div>
      <div class="decision-kpi">
        <span class="decision-kpi__label">Necesidades afectadas</span>
        <span class="decision-kpi__value">${imp.needs_affected}</span>
      </div>
      <div class="decision-kpi">
        <span class="decision-kpi__label">Recursos cercanos</span>
        <span class="decision-kpi__value">${imp.resources_nearby}</span>
      </div>
    </div>
    ${imp.factors?.length ? `
    <div class="data-rows" style="margin-top:var(--space-sm);">
      ${imp.factors.map(f => `
        <div class="data-row">
          <span class="data-row__label">${escapeHtml(f)}</span>
        </div>`).join("")}
    </div>` : ""}`;
}

function renderGeoRisk(georisk) {
  if (!georisk) {
    return `
      <div class="decision-empty">
        <span class="decision-empty__icon">🔬</span>
        <span class="decision-empty__text">Sin datos de riesgo científico</span>
        <span class="decision-empty__hint">GeoRisk Finder no configurado</span>
      </div>`;
  }

  if (georisk.status === "unavailable") {
    return `
      <div class="decision-empty decision-empty--warning">
        <span class="decision-empty__icon">⚠️</span>
        <span class="decision-empty__text">GeoRisk no disponible</span>
        <span class="decision-empty__hint">Usando riesgo operacional local</span>
        ${georisk.h3_index ? `<span class="decision-empty__hint">Celda H3: ${escapeHtml(georisk.h3_index)}</span>` : ""}
      </div>`;
  }

  if (georisk.status === "error") {
    return `
      <div class="decision-empty decision-empty--error">
        <span class="decision-empty__icon">❌</span>
        <span class="decision-empty__text">Error consultando GeoRisk</span>
        <span class="decision-empty__hint">${escapeHtml(georisk.message || "Error desconocido")}</span>
      </div>`;
  }

  const score = georisk.risk_score ?? 0;
  const level = georisk.risk_level || "unknown";
  const sevKey = score >= 80 ? "critica" : score >= 60 ? "alta" : score >= 40 ? "moderada" : "informativa";
  const sev = SEV_MAP[sevKey] || SEV_MAP.informativa;

  return `
    <div class="decision-source-badge">
      <span class="decision-source-badge__dot" style="background:var(--blue);"></span>
      <span>GEORISK FINDER — Análisis Científico</span>
    </div>
    <div class="decision-kpi-row">
      <div class="decision-kpi">
        <span class="decision-kpi__label">Riesgo Territorial</span>
        <span class="decision-kpi__value" style="color:${sev.color};font-size:var(--text-2xl);font-weight:800;">${score.toFixed(0)}</span>
      </div>
      <div class="decision-kpi">
        <span class="decision-kpi__label">Nivel</span>
        <span class="badge badge--${sevKey}" style="background:${sev.bg};color:${sev.color};">${escapeHtml(level)}</span>
      </div>
      <div class="decision-kpi">
        <span class="decision-kpi__label">Celda H3</span>
        <span class="decision-kpi__value decision-kpi__value--mono">${escapeHtml(georisk.h3_index || "N/A")}</span>
      </div>
    </div>
    ${georisk.cluster_label ? `
    <div class="decision-kpi-row" style="margin-top:var(--space-sm);">
      <div class="decision-kpi">
        <span class="decision-kpi__label">Cluster</span>
        <span class="decision-kpi__value">${escapeHtml(georisk.cluster_label)}</span>
      </div>
      ${georisk.confidence ? `
      <div class="decision-kpi">
        <span class="decision-kpi__label">Confianza</span>
        <span class="decision-kpi__value">${(georisk.confidence * 100).toFixed(0)}%</span>
      </div>` : ""}
    </div>` : ""}
    ${georisk.explanation ? `
    <div class="decision-explanation" style="margin-top:var(--space-sm);">
      <p style="font-size:var(--text-xs);color:var(--text-secondary);">${escapeHtml(georisk.explanation)}</p>
    </div>` : ""}
    <div class="decision-source-note">
      Fuente: <strong>GeoRisk Finder</strong> · Modelo: ${escapeHtml(georisk.model_version || "N/A")} · Estos indicadores son análisis científico, no prioridad operacional.
    </div>`;
}

function renderRiskSection(risk, explanation) {
  const score = risk.combined_score ?? 0;
  const level = risk.priority_level || "informativo";
  const sevKey = score >= 80 ? "critica" : score >= 60 ? "alta" : score >= 40 ? "moderada" : "informativa";
  const sev = SEV_MAP[sevKey] || SEV_MAP.informativa;

  return `
    <div class="decision-score-block">
      <div class="decision-score" style="color:${sev.color};">${score.toFixed(0)}</div>
      <div>
        <span class="badge badge--${sevKey}" style="background:${sev.bg};color:${sev.color};font-size:var(--text-sm);">${sev.label}</span>
        <div style="font-size:var(--text-xs);color:var(--text-muted);margin-top:2px;">
          Fuente: <strong>${escapeHtml(risk.source || "rules")}</strong> · ${escapeHtml(risk.methodology_version || "rules-v1")}
        </div>
      </div>
    </div>
    ${explanation?.factors?.length ? `
    <div class="data-rows" style="margin-top:var(--space-sm);">
      ${explanation.factors.map(f => `
        <div class="data-row">
          <span class="data-row__label">${escapeHtml(f)}</span>
        </div>`).join("")}
    </div>` : ""}
    ${explanation?.summary ? `
    <div class="decision-explanation" style="margin-top:var(--space-sm);">
      <p style="font-size:var(--text-xs);color:var(--text-secondary);white-space:pre-line;">${escapeHtml(explanation.summary)}</p>
    </div>` : ""}`;
}

function renderOperation(op) {
  return `
    <div class="decision-kpi-row">
      <div class="decision-kpi">
        <span class="decision-kpi__label">Necesidades abiertas</span>
        <span class="decision-kpi__value">${op.needs_open} / ${op.needs_total}</span>
      </div>
      <div class="decision-kpi">
        <span class="decision-kpi__label">Recursos disponibles</span>
        <span class="decision-kpi__value">${op.resources_available} / ${op.resources_total}</span>
      </div>
      <div class="decision-kpi">
        <span class="decision-kpi__label">Asignaciones activas</span>
        <span class="decision-kpi__value">${op.active_assignments}</span>
      </div>
      ${op.min_distance_resource != null ? `
      <div class="decision-kpi">
        <span class="decision-kpi__label">Recurso más cercano</span>
        <span class="decision-kpi__value">${op.min_distance_resource.toFixed(1)} km</span>
      </div>` : ""}
    </div>
    ${op.assignments?.length ? `
    <div class="data-rows" style="margin-top:var(--space-sm);">
      ${op.assignments.map(a => `
        <div class="data-row">
          <span class="data-row__label">${escapeHtml(a.resource_name || "Recurso")}</span>
          <span class="data-row__value badge badge--sm badge--${escapeHtml(a.status || 'asignado')}">${escapeHtml(a.status || "asignado")}</span>
        </div>`).join("")}
    </div>` : ""}`;
}

function renderAction(risk, op, incidentMeta) {
  const score = risk.combined_score ?? 0;
  const actions = [];

  if (score >= 80) {
    actions.push({ icon: "🚨", text: "Activar protocolo de emergencia máxima" });
    actions.push({ icon: "📞", text: "Notificar a todas las unidades de respuesta" });
  } else if (score >= 60) {
    actions.push({ icon: "⚠️", text: "Activar nivel de alerta alto" });
    actions.push({ icon: "📋", text: "Revisar necesidades abiertas en la zona" });
  } else if (score >= 40) {
    actions.push({ icon: "📊", text: "Monitorear evolución del incidente" });
  } else {
    actions.push({ icon: "ℹ️", text: "Registrar y monitorear" });
  }

  if (op.needs_open > 0 && op.resources_available > 0) {
    actions.push({ icon: "🎯", text: `${op.needs_open} necesidades con ${op.resources_available} recursos disponibles — considerar asignación` });
  } else if (op.needs_open > 0 && op.resources_available === 0) {
    actions.push({ icon: "❌", text: "Necesidades abiertas sin recursos disponibles — solicitar apoyo externo" });
  }

  const actionButtons = incidentMeta ? `
    <div style="margin-top:var(--space-md);display:flex;gap:var(--space-sm);flex-wrap:wrap;">
      <button class="btn btn--primary btn--sm" onclick="window.showCreateNeedForm(${incidentMeta.id})">
        📋 Crear Necesidad
      </button>
      <button class="btn btn--ghost btn--sm" onclick="window.showSection('mapa')">
        🗺️ Ver en Mapa
      </button>
    </div>
    <div id="create-need-inline" style="margin-top:var(--space-md);display:none;"></div>
  ` : "";

  return `
    <div class="data-rows">
      ${actions.map(a => `
        <div class="data-row" style="align-items:flex-start;">
          <span style="font-size:var(--text-base);">${a.icon}</span>
          <span class="data-row__label">${escapeHtml(a.text)}</span>
        </div>`).join("")}
    </div>
    ${actionButtons}`;
}

window.showCreateNeedForm = (incidentId) => {
  const container = document.getElementById("create-need-inline");
  if (!container) return;
  const isVisible = container.style.display !== "none";
  if (isVisible) { container.style.display = "none"; return; }
  container.style.display = "block";
  container.innerHTML = `
    <div class="card" style="padding:var(--space-md);border:1px solid var(--border);">
      <h4 style="font-size:var(--text-sm);font-weight:700;margin-bottom:var(--space-sm);color:var(--navy);">Crear Necesidad para Incidente #${incidentId}</h4>
      <form id="inline-need-form" style="display:flex;flex-direction:column;gap:var(--space-sm);">
        <div style="display:flex;gap:var(--space-sm);">
          <select id="inline-need-tipo" class="form-select" style="flex:1;" required>
            <option value="">Tipo...</option>
            <option value="agua">💧 Agua</option>
            <option value="alimentos">🍞 Alimentos</option>
            <option value="parafarmacia">💊 Parafarmacia</option>
            <option value="ropa">👕 Ropa</option>
            <option value="higiene">🧴 Higiene</option>
            <option value="refugio">🏠 Refugio</option>
            <option value="transporte">🚗 Transporte</option>
            <option value="otros">📦 Otros</option>
          </select>
          <select id="inline-need-prioridad" class="form-select" style="flex:1;">
            <option value="media">Prioridad Media</option>
            <option value="baja">Baja</option>
            <option value="alta">Alta</option>
            <option value="critica">Crítica</option>
          </select>
        </div>
        <input type="text" id="inline-need-titulo" class="form-input" placeholder="Título (opcional)" maxlength="120" />
        <textarea id="inline-need-desc" class="form-textarea" rows="2" maxlength="1000" placeholder="Descripción..."></textarea>
        <button type="submit" class="btn btn--primary btn--sm" style="width:100%;">📍 Crear Necesidad</button>
      </form>
    </div>`;

  document.getElementById("inline-need-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const tipo = document.getElementById("inline-need-tipo").value;
    if (!tipo) { alert("Selecciona una categoría."); return; }
    const inc = window._selectedIncident;
    const payload = {
      tipo,
      titulo: document.getElementById("inline-need-titulo").value.trim(),
      descripcion: document.getElementById("inline-need-desc").value.trim(),
      prioridad: document.getElementById("inline-need-prioridad").value,
      latitud: inc?.lat || 0,
      longitud: inc?.lon || 0,
    };
    try {
      const resp = await fetch(`${API_BASE}/api/incidents/${incidentId}/needs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (resp.ok) {
        container.innerHTML = '<div style="padding:var(--space-sm);color:var(--success);font-size:var(--text-sm);font-weight:600;">✓ Necesidad creada</div>';
        setTimeout(() => { container.style.display = "none"; }, 2000);
        window._refreshIncidents?.();
      } else {
        alert("Error creando necesidad");
      }
    } catch (err) { alert("Error: " + err.message); }
  });
};

window.loadDecisionContext = loadDecisionContext;
