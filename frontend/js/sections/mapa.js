// Mapa section — initMap, all render functions, layer toggles, map click handlers
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
  };

  function toggleLayer(nombre, visible) {
    const capa = capas[nombre];
    if (!capa) return;
    visible ? map.addLayer(capa) : map.removeLayer(capa);
  }

  function getIconByPriority(p) {
    const cls = (p === "alta" || p === "critica") ? "priority-high" : p === "media" ? "priority-medium" : "priority-low";
    return L.divIcon({ className: "", html: `<div class="marcador-custom ${cls}"></div>`, iconSize: [16, 16], iconAnchor: [8, 8] });
  }

  function makeEmojiIcon(emoji, color) {
    return L.divIcon({
      className: "nexo-marker",
      html: `<div style="
        background: ${color};
        width: 30px; height: 30px;
        border-radius: 50%;
        border: 2px solid #ffffff;
        box-shadow: 0 2px 6px rgba(0,0,0,0.4);
        display: flex; align-items: center; justify-content: center;
        font-size: 16px; line-height: 1;
      ">${emoji}</div>`,
      iconSize: [30, 30],
      iconAnchor: [15, 15],
    });
  }

  const ALERT_ICONS = {
    terremoto: { emoji: "🌋", color: "#8b4513" },
    ciclon: { emoji: "🌀", color: "#00bcd4" },
    inundacion: { emoji: "🌊", color: "#1976d2" },
    incendio: { emoji: "🔥", color: "#ff5722" },
    volcan: { emoji: "🌋", color: "#d32f2f" },
    sequia: { emoji: "☀️", color: "#fbc02d" },
    otro: { emoji: "⚠️", color: "#9e9e9e" },
  };

  const CLIMA_ICONS = {
    rojo: { emoji: "🟥", color: "#d32f2f" },
    naranja: { emoji: "🟧", color: "#f57c00" },
    amarillo: { emoji: "🟨", color: "#fbc02d" },
    verde: { emoji: "🟩", color: "#43a047" },
  };

  let loadedNeeds = [];
  let loadedAlerts = [];
  let loadedAyudas = [];
  let zonaActiva = null;

  function renderZonasH3(list, capa, color, popupLabel) {
    capa.clearLayers();
    if (!list.length) return;
    const grid = new Map();
    const res = 0.02;
    list.forEach(item => {
      const lat = item.latitud ?? item.latitude;
      const lon = item.longitud ?? item.longitude;
      if (lat == null || lon == null) return;
      const key = `${Math.floor(lat / res)}_${Math.floor(lon / res)}`;
      if (!grid.has(key)) grid.set(key, { count: 0, lat: Math.floor(lat / res) * res + res / 2, lon: Math.floor(lon / res) * res + res / 2 });
      grid.get(key).count++;
    });
    grid.forEach(cell => {
      const c = cell.count > 5 ? "var(--red)" : cell.count > 2 ? "var(--orange)" : color;
      const bounds = [[cell.lat - res / 2, cell.lon - res / 2], [cell.lat + res / 2, cell.lon + res / 2]];
      L.rectangle(bounds, { color: c, weight: 1, fillColor: c, fillOpacity: 0.18 }).addTo(capa)
        .bindPopup(`<b>${popupLabel}</b><br>${cell.count} elementos`);
    });
  }

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
          <div style="display:flex;gap:6px;margin-bottom:8px;">
            <span style="background:rgba(0,240,255,0.15);color:var(--cyan);padding:2px 8px;border-radius:12px;font-size:0.7rem;font-weight:700;">${escapeHtml(prioridad)}</span>
            <span style="background:rgba(255,255,255,0.1);padding:2px 8px;border-radius:12px;font-size:0.7rem;">${escapeHtml(tipo)}</span>
          </div>
          <h3 style="margin:0 0 6px;font-size:1rem;font-weight:700;">${escapeHtml(e.title || catLabel)}</h3>
          ${e.address ? `<p style="color:var(--text-muted);font-size:0.8rem;margin:0 0 4px;">📍 ${escapeHtml(e.address)}</p>` : ""}
          <p style="color:var(--text-secondary);font-size:0.85rem;margin:0;">${escapeHtml(e.description)}</p>
          <button onclick="window.cambiarEstadoNecesidad(${Number(e.id)},'cubierta')" style="margin-top:10px;width:100%;padding:8px;background:linear-gradient(135deg,var(--cyan),var(--blue));color:var(--text-inverse);border:none;border-radius:var(--radius-sm);cursor:pointer;font-weight:700;font-size:0.8rem;">✓ Marcar cubierta</button>
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
      const ayudaMeta = tipo === "tiempo" ? { emoji: "⏰", color: "#9c27b0" } : tipo === "servicios" ? { emoji: "🛠️", color: "#009688" } : { emoji: "📦", color: "#ff9800" };
      const icon = makeEmojiIcon(ayudaMeta.emoji, ayudaMeta.color);
      const m = L.marker([lat, lon], { icon });
      m.bindPopup(`<b>${escapeHtml(tipo.charAt(0).toUpperCase() + tipo.slice(1))}</b><br>${escapeHtml(e.extras.recurso || "")}<br>${escapeHtml(e.description)}<br><small>${escapeHtml(e.status || "")}</small>`);
      m.on("click", () => {
        openDrawer(e.title || "Ayuda", renderDrawerFields(e));
      });
      m.addTo(capas.ayudas);
    });
  }

  function renderAlertasOnMap(alerts) {
    capas.alertas.clearLayers();
    capas.zonas.clearLayers();
    zonaActiva = null;
    const entities = normalizeGDACSAlerts(alerts);
    entities.forEach(e => {
      const zone = e.extras.zone;
      const isHigh = e.extras.riskLevel === "high" || e.status === "high_risk";
      if (isHigh && zone) {
        try {
          const geo = typeof zone === "string" ? JSON.parse(zone) : zone;
          const layer = L.geoJSON(geo, { style: { color: "#d32f2f", weight: 3, fillOpacity: 0.15 } }).addTo(capas.zonas);
          zonaActiva = geo;
          try { map.fitBounds(layer.getBounds(), { padding: [20, 20] }); } catch {}
        } catch {}
      }
      if (e.coords) {
        const { lat, lon } = e.coords;
        const meta = ALERT_ICONS[e.type.label] || ALERT_ICONS.otro;
        const SEV_COLORS = {
          [SeverityLevel.CRITICAL]: "#FF334B",
          [SeverityLevel.HIGH]: "#FF6B00",
          [SeverityLevel.MODERATE]: "#FBC02D",
          [SeverityLevel.LOW]: "#38BDF8",
        };
        const sevColor = SEV_COLORS[e.severity.level] || meta.color;
        const icon = makeEmojiIcon(meta.emoji, sevColor);
        const m = L.marker([lat, lon], { icon }).addTo(capas.alertas);
        m.bindPopup(`<b>${escapeHtml(e.title || "Alerta")}</b><br>${escapeHtml(e.description)}<br><small>${escapeHtml(e.severity.raw || e.extras.riskLevel || "")} — ${escapeHtml(e.country)}</small>`);
        m.on("click", () => {
          openDrawer(e.title || "Alerta", renderDrawerFields(e));
        });
      }
    });
  }

  function renderNeedsList(needs) {
    const el = document.getElementById("needs-list");
    if (!el) return;
    if (!needs.length) {
      el.innerHTML = '<div class="state-empty"><p>No hay necesidades activas</p></div>';
      return;
    }
    el.innerHTML = needs.slice(0, 20).map(n => `
      <div class="need-card">
        <div class="need-card__header">
          <span class="need-card__type">${escapeHtml(n.categoria_etiqueta || n.tipo)}</span>
          <span class="need-card__priority need-card__priority--${escapeHtml(n.prioridad)}">${escapeHtml(n.prioridad)}</span>
        </div>
        ${n.direccion ? `<div class="need-card__address">📍 ${escapeHtml(n.direccion)}</div>` : ""}
        <div class="need-card__desc">${escapeHtml((n.descripcion || "").substring(0, 100))}${(n.descripcion || "").length > 100 ? "..." : ""}</div>
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
  }

  function renderIncendios(data) {
    capas.incendios.clearLayers();
    const entities = normalizeFIRMSDetections(data);
    entities.forEach(e => {
      if (!e.coords) return;
      const { lat, lon } = e.coords;
      const brillo = e.extras.brightness ?? 0;
      const confianza = e.extras.confidence ?? "nominal";
      const color = confianza === "high" ? "#ff2200" : confianza === "nominal" ? "#ff8800" : "#ffaa00";

      const halo = L.circleMarker([lat, lon], {
        radius: 14,
        color: color,
        weight: 1,
        fillColor: color,
        fillOpacity: 0.25,
        interactive: false,
      }).addTo(capas.incendios);

      const icon = L.divIcon({
        className: "incendio-marker",
        html: `<div style="
          background: ${color};
          width: 26px; height: 26px;
          border-radius: 50%;
          border: 2px solid #ffffff;
          box-shadow: 0 0 8px ${color}, 0 0 14px rgba(255,80,0,0.5);
          display: flex; align-items: center; justify-content: center;
          font-size: 16px; line-height: 1;
        ">🔥</div>`,
        iconSize: [26, 26],
        iconAnchor: [13, 13],
      });
      const marker = L.marker([lat, lon], { icon }).addTo(capas.incendios);
      marker.bindPopup(`
        <b>🔥 Detección NASA FIRMS</b><br>
        <b>Satélite:</b> ${escapeHtml(e.extras.satellite || "VIIRS SNPP")}<br>
        <b>Fecha:</b> ${escapeHtml(e.extras.acqDate || e.timestamp || "")}<br>
        <b>Brillo:</b> ${escapeHtml(Number(brillo).toFixed(1))} K<br>
        <b>Confianza:</b> ${escapeHtml(confianza)}<br>
        <small>${escapeHtml(e.country || "España")}</small>
      `);
      marker.on("click", () => {
        openDrawer(e.title || "Detección FIRMS", renderDrawerFields(e));
      });
    });
  }

  async function loadIncendiosMap() {
    try {
      const data = await apiGet("/api/incendios");
      renderIncendios(data);
    } catch (err) {
      console.error("Incendios error:", err);
    }
  }

  function renderClima(data) {
    capas.clima.clearLayers();
    const entities = normalizeClimaAlerts(data);
    if (!entities.length) {
      const center = [40.4168, -3.7038];
      const noAlert = L.marker(center, {
        icon: L.divIcon({
          className: "nexo-marker",
          html: `<div style="background:rgba(76,175,80,0.15);color:#43a047;padding:6px 10px;border-radius:8px;font-size:0.75rem;border:1px solid #43a047;">☀️ Sin alertas meteorológicas activas</div>`,
          iconSize: [200, 28],
          iconAnchor: [100, 14],
        }),
        interactive: false,
      }).addTo(capas.clima);
      return;
    }
    entities.forEach(e => {
      const nivel = e.severity.raw || "amarillo";
      const meta = CLIMA_ICONS[nivel] || CLIMA_ICONS.amarillo;
      const lat = e.coords?.lat ?? (40.4168 + (Math.random() - 0.5) * 2);
      const lon = e.coords?.lon ?? (-3.7038 + (Math.random() - 0.5) * 2);
      const icon = makeEmojiIcon(meta.emoji, meta.color);
      const marker = L.marker([lat, lon], { icon }).addTo(capas.clima);
      marker.bindPopup(`<b>⚠️ Alerta meteorológica</b><br><b>${escapeHtml(e.title || "Alerta")}</b><br>${escapeHtml(e.description)}<br><small>${escapeHtml(e.source)} — ${escapeHtml(e.region || "España")}</small>`);
      marker.on("click", () => {
        openDrawer(e.title || "Alerta meteorológica", renderDrawerFields(e));
      });
    });
  }

  async function loadClimaMap() {
    try {
      const data = await apiGet("/api/clima");
      renderClima(data);
    } catch (err) {
      console.error("Clima error:", err);
    }
  }

  async function loadAlertasMap() {
    const mapEl = document.getElementById("map");
    if (mapEl) mapEl.classList.add("map--loading");
    try {
      const data = await apiGet("/api/alertas");
      const region = document.getElementById("region-filter")?.value;
      const raw = Array.isArray(data) ? data : [];
      loadedAlerts = normalizeGDACSAlerts(raw);
      if (region && region !== "world") {
        loadedAlerts = loadedAlerts.filter(e => matchesRegion(e.country, region));
      }
      notifyCritical(loadedAlerts);
    } catch { loadedAlerts = []; }
    if (mapEl) mapEl.classList.remove("map--loading");
    renderAlertasOnMap(loadedAlerts);
    updateBadge();
  }

  async function loadAyudasMap() {
    try {
      const data = await apiGet("/api/donaciones");
      loadedAyudas = Array.isArray(data) ? data : [];
    } catch {
      try {
        loadedAyudas = await fetch("/mocks/ayudas.mock.json").then(r => r.json());
      } catch { loadedAyudas = []; }
    }
    renderAyudas(loadedAyudas);
    updateBadge();
  }

  function updateBadge() {
    const badge = document.getElementById("intensityBadge");
    if (!badge) return;
    badge.textContent = `${loadedNeeds.length} total`;
  }

  // Category filter
  document.getElementById("typeFilter")?.addEventListener("change", (e) => {
    const val = e.target.value;
    let filtered = loadedNeeds;
    if (val && val !== "all") filtered = filtered.filter(n => n.tipo === val);
    renderMap(filtered);
    renderNeedsList(filtered);
  });

  // Layer toggles
  document.getElementById("toggle-alertas")?.addEventListener("change", e => toggleLayer("alertas", e.target.checked));
  document.getElementById("toggle-zonas")?.addEventListener("change", e => toggleLayer("zonas", e.target.checked));
  document.getElementById("toggle-necesidades")?.addEventListener("change", e => toggleLayer("necesidades", e.target.checked));
  document.getElementById("toggle-ayudas")?.addEventListener("change", e => toggleLayer("ayudas", e.target.checked));
  document.getElementById("toggle-incendios")?.addEventListener("change", e => toggleLayer("incendios", e.target.checked));
  document.getElementById("toggle-clima")?.addEventListener("change", e => toggleLayer("clima", e.target.checked));

  // Map click -> set coordinates + reverse geocode
  let tempMarker = null;
  map.on("click", async e => {
    const { lat, lng } = e.latlng;
    document.getElementById("input-lat").value = lat.toFixed(6);
    document.getElementById("input-lng").value = lng.toFixed(6);
    const dirInput = document.getElementById("input-direccion");
    const msg = document.getElementById("ubicacion-mensaje");
    if (msg) {
      msg.textContent = `Buscando dirección... (${lat.toFixed(4)}, ${lng.toFixed(4)})`;
      msg.style.color = "var(--text-muted)";
    }
    if (tempMarker) map.removeLayer(tempMarker);
    tempMarker = L.circleMarker([lat, lng], { radius: 10, color: "var(--orange)", fillColor: "var(--orange)", fillOpacity: 0.4, weight: 2 }).addTo(map);

    try {
      const { direccionInversa } = await import("../core/mapa-necesidades/geocodificacion.js");
      const direccion = await direccionInversa(lat, lng);
      if (direccion && dirInput) {
        dirInput.value = direccion;
        if (msg) {
          msg.textContent = `✓ ${direccion}`;
          msg.style.color = "var(--cyan)";
        }
      } else if (msg) {
        msg.textContent = `✓ Ubicación fijada: ${lat.toFixed(4)}, ${lng.toFixed(4)}`;
        msg.style.color = "var(--cyan)";
      }
    } catch {
      if (msg) {
        msg.textContent = `✓ Ubicación fijada: ${lat.toFixed(4)}, ${lng.toFixed(4)}`;
        msg.style.color = "var(--cyan)";
      }
    }
  });

  // Need form
  let selectedTipo = null;
  document.querySelectorAll(".anr-categoria-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      if (selectedTipo === btn.dataset.tipo) {
        btn.classList.remove("is-selected");
        btn.style.background = "";
        btn.style.borderColor = "";
        selectedTipo = null;
      } else {
        document.querySelectorAll(".anr-categoria-btn").forEach(b => {
          b.classList.remove("is-selected");
          b.style.background = "";
          b.style.borderColor = "";
        });
        btn.classList.add("is-selected");
        btn.style.background = "var(--cyan-subtle)";
        btn.style.borderColor = "var(--cyan)";
        selectedTipo = btn.dataset.tipo;
      }
    });
  });

  document.getElementById("need-form")?.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!selectedTipo) { alert("Selecciona una categoría."); return; }
    const dir = document.getElementById("input-direccion").value.trim();
    const lat = document.getElementById("input-lat").value;
    const lng = document.getElementById("input-lng").value;
    if (!lat || !lng) { alert("Selecciona una ubicación en el mapa o escribe una dirección."); return; }
    const payload = {
      tipo: selectedTipo,
      titulo: "",
      descripcion: document.getElementById("textarea-desc").value.trim(),
      direccion: dir,
      latitud: parseFloat(lat),
      longitud: parseFloat(lng),
    };
    try {
      await fetch(`${API_BASE}/api/necesidades`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      alert("¡Necesidad reportada!");
      document.getElementById("need-form").reset();
      document.querySelectorAll(".anr-categoria-btn").forEach(b => {
        b.classList.remove("is-selected");
        b.style.background = "";
        b.style.borderColor = "";
      });
      selectedTipo = null;
      await loadNeeds();
    } catch (err) { alert("Error al reportar: " + err.message); }
  });

  // Load all layers
  Promise.all([loadAlertasMap(), loadNeeds(), loadAyudasMap(), loadIncendiosMap(), loadClimaMap()]);

  window.loadIncendiosMap = loadIncendiosMap;
  window.loadClimaMap = loadClimaMap;
}
