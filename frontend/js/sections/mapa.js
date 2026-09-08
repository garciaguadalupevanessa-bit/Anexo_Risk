// Mapa section — initMap, layers, popups, light theme
import {
  SeverityLevel,
  normalizeGDACSAlerts,
  normalizeFIRMSDetections,
  normalizeClimaAlerts,
  normalizeNecesidades,
  normalizeDonaciones,
} from "../core/normalization/index.js";
import { API_BASE, apiGet, matchesRegion, escapeHtml } from "../shared/config.js";
import { notifyCritical } from "./alertas.js";

export function initMap() {
  const map = L.map("map").setView([38.5, -3.5], 6);
  window._map = map;

  L.tileLayer("https://a.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}.png?key=cb1_2qa8_1_a275e8c9b45d6b70d3b144df", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.carto.com/">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright">OSM</a>'
  }).addTo(map);

  const capas = {
    alertas: L.layerGroup().addTo(map),
    zonas: L.layerGroup().addTo(map),
    necesidades: L.layerGroup().addTo(map),
    ayudas: L.layerGroup().addTo(map),
    incendios: L.layerGroup().addTo(map),
    clima: L.layerGroup().addTo(map),
    incidentes: L.layerGroup().addTo(map),
  };

  function toggleLayer(nombre, visible) {
    const capa = capas[nombre];
    if (!capa) return;
    visible ? map.addLayer(capa) : map.removeLayer(capa);
  }

  const SEV_COLORS = {
    [SeverityLevel.CRITICAL]: "#C62828",
    [SeverityLevel.HIGH]: "#E65100",
    [SeverityLevel.MODERATE]: "#D97706",
    [SeverityLevel.LOW]: "#2563EB",
  };

  function getIconByPriority(p) {
    const color = (p === "alta" || p === "critica") ? SEV_COLORS[SeverityLevel.CRITICAL] : p === "media" ? SEV_COLORS[SeverityLevel.HIGH] : SEV_COLORS[SeverityLevel.LOW];
    return L.divIcon({
      className: "",
      html: `<div style="width:14px;height:14px;border-radius:50%;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,0.25);background:${color};"></div>`,
      iconSize: [14, 14], iconAnchor: [7, 7],
    });
  }

  function makeEmojiIcon(emoji, color) {
    return L.divIcon({
      className: "",
      html: `<div style="
        background: ${color};
        width: 28px; height: 28px;
        border-radius: 50%;
        border: 2px solid #fff;
        box-shadow: 0 1px 4px rgba(0,0,0,0.25);
        display: flex; align-items: center; justify-content: center;
        font-size: 14px; line-height: 1;
      ">${emoji}</div>`,
      iconSize: [28, 28], iconAnchor: [14, 14],
    });
  }

  const ALERT_ICONS = {
    terremoto: { emoji: "🌋", color: "#8B4513" },
    ciclon: { emoji: "🌀", color: "#00ACC1" },
    inundacion: { emoji: "🌊", color: "#1565C0" },
    incendio: { emoji: "🔥", color: "#E65100" },
    volcan: { emoji: "🌋", color: "#C62828" },
    sequia: { emoji: "☀️", color: "#F9A825" },
    otro: { emoji: "⚠️", color: "#78909C" },
  };

  const CLIMA_ICONS = {
    rojo: { emoji: "🟥", color: "#C62828" },
    naranja: { emoji: "🟧", color: "#E65100" },
    amarillo: { emoji: "🟨", color: "#F9A825" },
    verde: { emoji: "🟩", color: "#2E7D32" },
  };

  let loadedNeeds = [];
  let loadedAlerts = [];
  let loadedAyudas = [];
  let loadedIncidents = [];
  let selectedIncidentId = null;
  let lastDataUpdate = Date.now();

  function renderMap(needsList) {
    capas.necesidades.clearLayers();
    const entities = normalizeNecesidades(needsList);
    entities.forEach(e => {
      if (!e.coords) return;
      const { lat, lon } = e.coords;
      const prioridad = e.extras.prioridad || "media";
      const tipo = e.type.label || "otros";
      const catLabel = e.extras.categoriaEtiqueta || tipo;
      const marker = L.marker([lat, lon], { icon: getIconByPriority(prioridad) });
      marker.bindPopup(`
        <div class="anr-popup" style="font-family:var(--font);min-width:200px;">
          <div style="display:flex;gap:4px;margin-bottom:6px;">
            <span style="background:var(--sev-${prioridad === 'alta' || prioridad === 'critica' ? 'critica' : prioridad === 'media' ? 'alta' : 'informativa'}-bg);color:var(--sev-${prioridad === 'alta' || prioridad === 'critica' ? 'critica' : prioridad === 'media' ? 'alta' : 'informativa'});padding:1px 6px;border-radius:10px;font-size:0.65rem;font-weight:700;">${escapeHtml(prioridad)}</span>
            <span style="background:var(--bg-surface-alt);padding:1px 6px;border-radius:10px;font-size:0.65rem;">${escapeHtml(tipo)}</span>
          </div>
          <h3 style="margin:0 0 4px;font-size:0.9rem;font-weight:700;color:var(--navy);">${escapeHtml(e.title || catLabel)}</h3>
          ${e.address ? `<p style="color:var(--text-muted);font-size:0.75rem;margin:0 0 3px;">📍 ${escapeHtml(e.address)}</p>` : ""}
          <p style="color:var(--text-secondary);font-size:0.8rem;margin:0;">${escapeHtml(e.description)}</p>
          <button onclick="window.cambiarEstadoNecesidad(${Number(e.id)},'cubierta')" style="margin-top:8px;width:100%;padding:6px;background:var(--navy);color:#fff;border:none;border-radius:var(--radius-sm);cursor:pointer;font-weight:600;font-size:0.75rem;">✓ Marcar cubierta</button>
        </div>`);
      marker.on("click", () => {
        openDrawer(e.title || "Necesidad", renderDrawerFields(e));
      });
      marker.addTo(capas.necesidades);
    });
  }

  function renderAyudas(list) {
    capas.ayudas.clearLayers();
    const entities = normalizeDonaciones(list);
    entities.forEach(e => {
      if (!e.coords) return;
      const { lat, lon } = e.coords;
      const tipo = (e.type.label || "recurso").toLowerCase();
      const ayudaMeta = tipo === "tiempo" ? { emoji: "⏰", color: "#7C3AED" } : tipo === "servicios" ? { emoji: "🛠️", color: "#0891B2" } : { emoji: "📦", color: "#EA580C" };
      const icon = makeEmojiIcon(ayudaMeta.emoji, ayudaMeta.color);
      const m = L.marker([lat, lon], { icon });
      m.bindPopup(`<b>${escapeHtml(tipo.charAt(0).toUpperCase() + tipo.slice(1))}</b><br>${escapeHtml(e.extras.recurso || "")}<br>${escapeHtml(e.description)}<br><small>${escapeHtml(e.status || "")}</small>`);
      m.on("click", () => openDrawer(e.title || "Ayuda", renderDrawerFields(e)));
      m.addTo(capas.ayudas);
    });
  }

  function renderAlertasOnMap(alerts) {
    capas.alertas.clearLayers();
    capas.zonas.clearLayers();
    const entities = normalizeGDACSAlerts(alerts);
    let criticalCount = 0;
    let highCount = 0;
    entities.forEach(e => {
      if (e.severity?.level === SeverityLevel.CRITICAL) criticalCount++;
      if (e.severity?.level === SeverityLevel.HIGH) highCount++;

      const zone = e.extras.zone;
      const isHigh = e.extras.riskLevel === "high" || e.status === "high_risk";
      if (isHigh && zone) {
        try {
          const geo = typeof zone === "string" ? JSON.parse(zone) : zone;
          L.geoJSON(geo, { style: { color: "#C62828", weight: 2, fillColor: "#C62828", fillOpacity: 0.12 } }).addTo(capas.zonas);
        } catch {}
      }
      if (e.coords) {
        const { lat, lon } = e.coords;
        const meta = ALERT_ICONS[e.type.label] || ALERT_ICONS.otro;
        const sevColor = SEV_COLORS[e.severity.level] || meta.color;
        const icon = makeEmojiIcon(meta.emoji, sevColor);
        const m = L.marker([lat, lon], { icon }).addTo(capas.alertas);
        m.bindPopup(`<b>${escapeHtml(e.title || "Alerta")}</b><br>${escapeHtml(e.description)}<br><small>${escapeHtml(e.severity.raw || e.extras.riskLevel || "")} — ${escapeHtml(e.country)}</small>`);
        m.on("click", () => openDrawer(e.title || "Alerta", renderDrawerFields(e)));
      }
    });
    window._updateStatusBar?.({ critical: criticalCount, high: highCount });
  }

  function renderNeedsList(needs) {
    const el = document.getElementById("needs-list");
    if (!el) return;
    if (!needs.length) {
      el.innerHTML = '<div class="state-empty" style="padding:var(--space-md);"><p style="font-size:var(--text-xs);">No hay necesidades activas</p></div>';
      return;
    }
    el.innerHTML = needs.slice(0, 15).map(n => `
      <div class="need-card" style="margin-bottom:4px;">
        <div class="need-card__header">
          <span class="need-card__type">${escapeHtml(n.categoria_etiqueta || n.tipo)}</span>
          <span class="need-card__priority need-card__priority--${escapeHtml(n.prioridad)}">${escapeHtml(n.prioridad)}</span>
        </div>
        ${n.direccion ? `<div class="need-card__address">📍 ${escapeHtml(n.direccion)}</div>` : ""}
      </div>`).join("");
  }

  window.cambiarEstadoNecesidad = async (id, estado) => {
    try {
      await fetch(`${API_BASE}/api/necesidades/${id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ estado }),
      });
      await loadNeeds();
    } catch (e) { console.error(e); }
  };

  async function loadNeeds() {
    const needsStartTime = Date.now();
    try {
      const data = await apiGet("/api/necesidades");
      loadedNeeds = data.filter(n => n.estado !== "cubierta");
    } catch {
      try {
        loadedNeeds = await fetch("/mocks/necesidades.mock.json").then(r => r.json());
      } catch { loadedNeeds = []; }
    }
    renderMap(loadedNeeds);
    renderNeedsList(loadedNeeds);
    updateBadge();
    const uncovered = loadedNeeds.filter(n => !n.covered_quantity || n.covered_quantity < (n.quantity || 0)).length;
    window._updateStatusBar?.({ needs: loadedNeeds.length, uncovered });
    window._updateFreshness?.("needs", Date.now() - needsStartTime);
  }

  function renderIncendios(data) {
    capas.incendios.clearLayers();
    const entities = normalizeFIRMSDetections(data);
    entities.forEach(e => {
      if (!e.coords) return;
      const { lat, lon } = e.coords;
      const confianza = e.extras.confidence ?? "nominal";
      const color = confianza === "high" ? "#C62828" : confianza === "nominal" ? "#E65100" : "#F9A825";

      L.circleMarker([lat, lon], {
        radius: 12, color, weight: 1, fillColor: color, fillOpacity: 0.2, interactive: false,
      }).addTo(capas.incendios);

      const icon = L.divIcon({
        className: "",
        html: `<div style="background:${color};width:22px;height:22px;border-radius:50%;border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,0.3);display:flex;align-items:center;justify-content:center;font-size:12px;">🔥</div>`,
        iconSize: [22, 22], iconAnchor: [11, 11],
      });
      const marker = L.marker([lat, lon], { icon }).addTo(capas.incendios);
      marker.bindPopup(`<b>🔥 FIRMS</b><br><b>Satélite:</b> ${escapeHtml(e.extras.satellite || "VIIRS")}<br><b>Brillo:</b> ${escapeHtml(Number(e.extras.brightness ?? 0).toFixed(1))} K<br><b>Confianza:</b> ${escapeHtml(confianza)}`);
      marker.on("click", () => openDrawer(e.title || "FIRMS", renderDrawerFields(e)));
    });
  }

  async function loadIncendiosMap() {
    try {
      const data = await apiGet("/api/incendios");
      renderIncendios(data);
    } catch (err) { console.error("Incendios:", err); }
  }

  function renderClima(data) {
    capas.clima.clearLayers();
    const entities = normalizeClimaAlerts(data);
    if (!entities.length) {
      L.marker([40.4168, -3.7038], {
        icon: L.divIcon({ className: "", html: `<div style="background:var(--success-bg);color:var(--success);padding:4px 8px;border-radius:6px;font-size:0.7rem;border:1px solid var(--success-border);">☀️ Sin alertas</div>`, iconSize: [140, 24], iconAnchor: [70, 12] }),
        interactive: false,
      }).addTo(capas.clima);
      return;
    }
    entities.forEach(e => {
      const nivel = e.severity.raw || "amarillo";
      const meta = CLIMA_ICONS[nivel] || CLIMA_ICONS.amarillo;
      const lat = e.coords?.lat ?? (40.4168 + (Math.random() - 0.5) * 2);
      const lon = e.coords?.lon ?? (-3.7038 + (Math.random() - 0.5) * 2);
      const marker = L.marker([lat, lon], { icon: makeEmojiIcon(meta.emoji, meta.color) }).addTo(capas.clima);
      marker.bindPopup(`<b>⚠️ Meteorología</b><br><b>${escapeHtml(e.title || "Alerta")}</b><br>${escapeHtml(e.description)}`);
      marker.on("click", () => openDrawer(e.title || "Meteorología", renderDrawerFields(e)));
    });
  }

  async function loadClimaMap() {
    try {
      const data = await apiGet("/api/clima");
      renderClima(data);
    } catch (err) { console.error("Clima:", err); }
  }

  const INCIDENT_ICONS = {
    terremoto: { emoji: "🌋", color: "#8B4513" },
    incendio: { emoji: "🔥", color: "#E65100" },
    ciclon: { emoji: "🌀", color: "#00ACC1" },
    inundacion: { emoji: "🌊", color: "#1565C0" },
    volcan: { emoji: "🌋", color: "#C62828" },
    alerta: { emoji: "⚠️", color: "#D97706" },
    otro: { emoji: "📍", color: "#78909C" },
  };

  const INCIDENT_SEV_COLORS = {
    roja: "#C62828",
    naranja: "#E65100",
    amarilla: "#D97706",
    verde: "#2E7D32",
  };

  const INCIDENT_STATUS_LABELS = {
    detectado: "Detectado",
    evaluado: "Evaluado",
    en_respuesta: "En respuesta",
    resuelto: "Resuelto",
    cancelado: "Cancelado",
  };

  function renderIncidentsList(incidents) {
    const el = document.getElementById("incidents-list");
    const badge = document.getElementById("incidents-count-badge");
    if (!el) return;
    if (badge) badge.textContent = incidents.length;
    if (!incidents.length) {
      el.innerHTML = '<div class="state-empty" style="padding:var(--space-xs);"><p style="font-size:var(--text-xs);">Sin incidentes activos</p></div>';
      return;
    }
    el.innerHTML = incidents.slice(0, 10).map(inc => {
      const sevColor = INCIDENT_SEV_COLORS[inc.severity] || "#78909C";
      const statusLabel = INCIDENT_STATUS_LABELS[inc.status] || inc.status;
      return `
        <div class="need-card" style="margin-bottom:4px;cursor:pointer;border-left:3px solid ${sevColor};" onclick="window.selectIncident(${inc.id})" role="listitem">
          <div class="need-card__header">
            <span class="need-card__type" style="font-size:var(--text-xs);font-weight:700;color:${sevColor};">${escapeHtml(inc.severity)}</span>
            <span class="need-card__priority" style="font-size:0.6rem;color:var(--text-muted);">${escapeHtml(statusLabel)}</span>
          </div>
          <div style="font-size:var(--text-xs);font-weight:600;color:var(--navy);margin:2px 0;">${escapeHtml(inc.title)}</div>
          ${inc.priority_score != null ? `<div style="font-size:0.6rem;color:var(--text-muted);">Riesgo: ${Number(inc.priority_score).toFixed(0)}/100</div>` : ""}
        </div>`;
    }).join("");
  }

  function renderIncidentesOnMap(incidents) {
    capas.incidentes.clearLayers();
    renderIncidentsList(incidents);
    incidents.forEach(inc => {
      if (!inc.lat || !inc.lon) return;
      const meta = INCIDENT_ICONS[inc.event_type] || INCIDENT_ICONS.otro;
      const sevColor = INCIDENT_SEV_COLORS[inc.severity] || "#78909C";
      const isSelected = inc.id === selectedIncidentId;

      let icon;
      if (isSelected) {
        icon = L.divIcon({
          className: "",
          html: `<div style="
            background: ${sevColor};
            width: 36px; height: 36px;
            border-radius: 50%;
            border: 3px solid #fff;
            box-shadow: 0 0 0 3px ${sevColor}44, 0 2px 8px rgba(0,0,0,0.3);
            display: flex; align-items: center; justify-content: center;
            font-size: 16px; line-height: 1;
            animation: pulse-ring 1.5s ease-out infinite;
          ">${meta.emoji}</div>`,
          iconSize: [36, 36], iconAnchor: [18, 18],
        });
      } else {
        icon = makeEmojiIcon(meta.emoji, sevColor);
      }

      const m = L.marker([inc.lat, inc.lon], { icon });
      m.bindPopup(`
        <div class="anr-popup" style="font-family:var(--font);min-width:220px;">
          <div style="display:flex;gap:4px;margin-bottom:6px;">
            <span style="background:${sevColor}22;color:${sevColor};padding:1px 6px;border-radius:10px;font-size:0.65rem;font-weight:700;">${escapeHtml(inc.severity)}</span>
            <span style="background:var(--bg-surface-alt);padding:1px 6px;border-radius:10px;font-size:0.65rem;">${escapeHtml(inc.event_type)}</span>
            ${inc.status ? `<span style="background:var(--bg-surface-alt);padding:1px 6px;border-radius:10px;font-size:0.65rem;">${escapeHtml(inc.status)}</span>` : ""}
          </div>
          <h3 style="margin:0 0 4px;font-size:0.9rem;font-weight:700;color:var(--navy);">${escapeHtml(inc.title)}</h3>
          ${inc.description ? `<p style="color:var(--text-secondary);font-size:0.8rem;margin:0 0 4px;">${escapeHtml(inc.description)}</p>` : ""}
          <p style="color:var(--text-muted);font-size:0.75rem;margin:0 0 6px;">${escapeHtml(inc.source)} · ${inc.created_at ? new Date(inc.created_at).toLocaleString("es-ES") : ""}</p>
          ${inc.priority_score != null ? `<p style="color:var(--navy);font-size:0.8rem;margin:0 0 6px;font-weight:700;">Riesgo: ${Number(inc.priority_score).toFixed(0)}/100</p>` : ""}
          <div style="display:flex;gap:4px;">
            <button onclick="window.selectIncident(${inc.id})" style="flex:1;padding:6px;background:var(--navy);color:#fff;border:none;border-radius:var(--radius-sm);cursor:pointer;font-weight:600;font-size:0.75rem;">📊 Decisión</button>
            <button onclick="window.openIncidentDetail(${inc.id})" style="flex:1;padding:6px;background:var(--blue);color:#fff;border:none;border-radius:var(--radius-sm);cursor:pointer;font-weight:600;font-size:0.75rem;">📋 Detalle</button>
          </div>
        </div>
      `);
      m.on("click", () => {
        window._selectedIncident = inc;
      });
      m.addTo(capas.incidentes);
    });

    // Draw selection radius if an incident is selected
    if (selectedIncidentId) {
      const sel = incidents.find(i => i.id === selectedIncidentId);
      if (sel?.lat && sel?.lon) {
        L.circle([sel.lat, sel.lon], {
          radius: 50000, color: "#1769AA", fillColor: "#1769AA", fillOpacity: 0.05, weight: 1, dashArray: "6 4",
        }).addTo(capas.incidentes);
      }
    }
  }

  async function loadIncidentesMap() {
    try {
      const data = await apiGet("/api/incidents?is_active=true");
      loadedIncidents = Array.isArray(data) ? data : [];
    } catch { loadedIncidents = []; }
    renderIncidentesOnMap(loadedIncidents);
    window._updateStatusBar?.({
      incidents: loadedIncidents.length,
    });
    window._updateFreshness?.("incidents", 0);
  }

  window.selectIncident = async (incidentId) => {
    selectedIncidentId = incidentId;
    const inc = loadedIncidents.find(i => i.id === incidentId);
    if (!inc) return;
    window._selectedIncident = inc;

    // Center map on incident with animation
    if (inc.lat && inc.lon) {
      map.flyTo([inc.lat, inc.lon], 10, { duration: 0.8 });
    }

    renderIncidentesOnMap(loadedIncidents);
    window.showSection("decision");
    if (window.loadIncidentDecisionContext) {
      window.loadIncidentDecisionContext(incidentId);
    }
  };

  window.openIncidentDetail = async (incidentId) => {
    const inc = loadedIncidents.find(i => i.id === incidentId);
    if (!inc) return;

    const sevColor = INCIDENT_SEV_COLORS[inc.severity] || "#78909C";
    const statusLabel = INCIDENT_STATUS_LABELS[inc.status] || inc.status;

    // Fetch timeline
    let timelineHtml = '<p style="font-size:var(--text-xs);color:var(--text-muted);">Cargando cronología...</p>';
    try {
      const timelineData = await apiGet(`/api/incidents/${incidentId}/timeline`);
      const events = timelineData.events || [];
      const eventIcons = { detected: "📍", evaluated: "📊", need_created: "📋", assigned: "🎯", delivered: "✅", resolved: "🏁" };
      timelineHtml = events.length ? events.map((e, i) => `
        <div style="display:flex;gap:8px;align-items:flex-start;margin-bottom:8px;">
          <div style="width:8px;height:8px;border-radius:50%;background:${sevColor};margin-top:4px;flex-shrink:0;"></div>
          <div>
            <div style="font-size:var(--text-xs);font-weight:600;color:var(--navy);">${eventIcons[e.event_type] || "📌"} ${escapeHtml(e.description || e.event_type)}</div>
            <div style="font-size:0.65rem;color:var(--text-muted);">${e.created_at ? new Date(e.created_at.replace(" ", "T")).toLocaleString("es-ES") : ""}</div>
          </div>
        </div>`).join("") : '<p style="font-size:var(--text-xs);color:var(--text-muted);">Sin eventos</p>';
    } catch { timelineHtml = '<p style="font-size:var(--text-xs);color:var(--text-muted);">Error cargando cronología</p>'; }

    const html = `
      <div style="display:flex;flex-direction:column;gap:var(--space-md);">
        <div style="display:flex;gap:var(--space-sm);flex-wrap:wrap;">
          <span style="background:${sevColor}22;color:${sevColor};padding:2px 8px;border-radius:10px;font-size:var(--text-xs);font-weight:700;">${escapeHtml(inc.severity)}</span>
          <span style="background:var(--bg-surface-alt);padding:2px 8px;border-radius:10px;font-size:var(--text-xs);">${escapeHtml(inc.event_type)}</span>
          <span style="background:var(--bg-surface-alt);padding:2px 8px;border-radius:10px;font-size:var(--text-xs);">${escapeHtml(statusLabel)}</span>
        </div>
        <div style="font-size:var(--text-xs);color:var(--text-muted);">
          Fuente: ${escapeHtml(inc.source)} · ${inc.created_at ? new Date(inc.created_at.replace(" ", "T")).toLocaleString("es-ES") : ""}
        </div>
        ${inc.description ? `<div style="font-size:var(--text-sm);color:var(--text-secondary);">${escapeHtml(inc.description)}</div>` : ""}
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:var(--space-sm);">
          <div style="background:var(--bg-surface-alt);padding:var(--space-sm);border-radius:var(--radius-sm);">
            <div style="font-size:0.65rem;color:var(--text-muted);">Latitud</div>
            <div style="font-size:var(--text-sm);font-weight:600;font-family:var(--font-mono);">${inc.lat?.toFixed(4) || "N/A"}</div>
          </div>
          <div style="background:var(--bg-surface-alt);padding:var(--space-sm);border-radius:var(--radius-sm);">
            <div style="font-size:0.65rem;color:var(--text-muted);">Longitud</div>
            <div style="font-size:var(--text-sm);font-weight:600;font-family:var(--font-mono);">${inc.lon?.toFixed(4) || "N/A"}</div>
          </div>
          ${inc.priority_score != null ? `
          <div style="background:var(--sev-alta-bg);padding:var(--space-sm);border-radius:var(--radius-sm);">
            <div style="font-size:0.65rem;color:var(--sev-alta-text);">Riesgo</div>
            <div style="font-size:var(--text-lg);font-weight:800;color:var(--sev-alta);">${Number(inc.priority_score).toFixed(0)}/100</div>
          </div>` : ""}
          ${inc.h3_index ? `
          <div style="background:var(--bg-surface-alt);padding:var(--space-sm);border-radius:var(--radius-sm);">
            <div style="font-size:0.65rem;color:var(--text-muted);">Celda H3</div>
            <div style="font-size:var(--text-xs);font-weight:600;font-family:var(--font-mono);">${escapeHtml(inc.h3_index)}</div>
          </div>` : ""}
        </div>
        <div>
          <h4 style="font-size:var(--text-sm);font-weight:700;color:var(--navy);margin-bottom:var(--space-xs);">Cronología</h4>
          <div style="max-height:200px;overflow-y:auto;">${timelineHtml}</div>
        </div>
        <div style="display:flex;gap:var(--space-sm);">
          <button class="btn btn--primary btn--sm" style="flex:1;" onclick="window.selectIncident(${inc.id}); window.closeDrawer();">📊 Centro de Decisión</button>
          <button class="btn btn--ghost btn--sm" style="flex:1;" onclick="window._map?.flyTo([${inc.lat}, ${inc.lon}], 10); window.closeDrawer();">🗺️ Ver en Mapa</button>
        </div>
      </div>`;

    window.openDrawer(`Incidente #${inc.id}`, html);
  };

  window._refreshIncidents = loadIncidentesMap;

  async function loadAlertasMap() {
    const mapEl = document.getElementById("map");
    if (mapEl) mapEl.style.opacity = "0.6";
    try {
      const data = await apiGet("/api/alertas");
      const raw = Array.isArray(data) ? data : [];
      loadedAlerts = normalizeGDACSAlerts(raw);
      notifyCritical(loadedAlerts);
      lastDataUpdate = Date.now();
    } catch { loadedAlerts = []; }
    if (mapEl) mapEl.style.opacity = "1";
    renderAlertasOnMap(loadedAlerts);
    updateBadge();
    window._updateFreshness?.("alerts", Date.now() - lastDataUpdate);
  }

  async function loadAyudasMap() {
    try {
      const data = await apiGet("/api/donaciones");
      loadedAyudas = Array.isArray(data) ? data : [];
    } catch {
      try { loadedAyudas = await fetch("/mocks/ayudas.mock.json").then(r => r.json()); } catch { loadedAyudas = []; }
    }
    renderAyudas(loadedAyudas);
    updateBadge();
  }

  function updateBadge() {
    const badge = document.getElementById("intensityBadge");
    if (badge) badge.textContent = loadedNeeds.length;
  }

  // Category filter
  document.getElementById("typeFilter")?.addEventListener("change", (e) => {
    const val = e.target.value;
    let filtered = loadedNeeds;
    if (val && val !== "all") filtered = filtered.filter(n => n.tipo === val);
    renderMap(filtered);
    renderNeedsList(filtered);
  });

  // Incident filters
  function applyIncidentFilters() {
    const sev = document.getElementById("incident-filter-severity")?.value || "";
    const status = document.getElementById("incident-filter-status")?.value || "";
    let filtered = loadedIncidents;
    if (sev) filtered = filtered.filter(i => i.severity === sev);
    if (status) filtered = filtered.filter(i => i.status === status);
    renderIncidentesOnMap(filtered);
  }
  document.getElementById("incident-filter-severity")?.addEventListener("change", applyIncidentFilters);
  document.getElementById("incident-filter-status")?.addEventListener("change", applyIncidentFilters);

  // Layer toggles
  ["alertas", "zonas", "necesidades", "ayudas", "incendios", "clima", "incidentes"].forEach(name => {
    document.getElementById(`toggle-${name}`)?.addEventListener("change", e => toggleLayer(name, e.target.checked));
  });

  // Map click -> coordinates + reverse geocode
  let tempMarker = null;
  map.on("click", async e => {
    const { lat, lng } = e.latlng;
    document.getElementById("input-lat").value = lat.toFixed(6);
    document.getElementById("input-lng").value = lng.toFixed(6);
    const dirInput = document.getElementById("input-direccion");
    const msg = document.getElementById("ubicacion-mensaje");
    if (msg) { msg.textContent = `Buscando... (${lat.toFixed(4)}, ${lng.toFixed(4)})`; msg.style.color = "var(--text-muted)"; }
    if (tempMarker) map.removeLayer(tempMarker);
    tempMarker = L.circleMarker([lat, lng], { radius: 8, color: "#1769AA", fillColor: "#1769AA", fillOpacity: 0.3, weight: 2 }).addTo(map);

    try {
      const { direccionInversa } = await import("../core/mapa-necesidades/geocodificacion.js");
      const direccion = await direccionInversa(lat, lng);
      if (direccion && dirInput) {
        dirInput.value = direccion;
        if (msg) { msg.textContent = `✓ ${direccion}`; msg.style.color = "var(--success)"; }
      } else if (msg) {
        msg.textContent = `✓ ${lat.toFixed(4)}, ${lng.toFixed(4)}`;
        msg.style.color = "var(--success)";
      }
    } catch {
      if (msg) { msg.textContent = `✓ ${lat.toFixed(4)}, ${lng.toFixed(4)}`; msg.style.color = "var(--success)"; }
    }
  });

  // Need form
  let selectedTipo = null;
  document.querySelectorAll(".anr-categoria-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".anr-categoria-btn").forEach(b => {
        b.classList.remove("active");
        b.setAttribute("aria-pressed", "false");
      });
      if (selectedTipo !== btn.dataset.tipo) {
        btn.classList.add("active");
        btn.setAttribute("aria-pressed", "true");
        selectedTipo = btn.dataset.tipo;
      } else {
        selectedTipo = null;
      }
    });
  });

  document.getElementById("need-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!selectedTipo) { alert("Selecciona una categoría."); return; }
    const lat = document.getElementById("input-lat").value;
    const lng = document.getElementById("input-lng").value;
    if (!lat || !lng) { alert("Selecciona una ubicación."); return; }
    const payload = {
      tipo: selectedTipo, titulo: "",
      descripcion: document.getElementById("textarea-desc").value.trim(),
      direccion: document.getElementById("input-direccion").value.trim(),
      latitud: parseFloat(lat), longitud: parseFloat(lng),
    };
    try {
      await fetch(`${API_BASE}/api/necesidades`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      document.getElementById("need-form").reset();
      document.querySelectorAll(".anr-categoria-btn").forEach(b => { b.classList.remove("active"); b.setAttribute("aria-pressed", "false"); });
      selectedTipo = null;
      await loadNeeds();
    } catch (err) { alert("Error: " + err.message); }
  });

  // Load all layers
  Promise.all([loadAlertasMap(), loadNeeds(), loadAyudasMap(), loadIncendiosMap(), loadClimaMap(), loadIncidentesMap()]);

  window.loadIncendiosMap = loadIncendiosMap;
  window.loadClimaMap = loadClimaMap;
  window.loadIncidentesMap = loadIncidentesMap;
}
