// G4 Mapa — Juan — Anexo Risk — Producto integral
// Leaflet base + capas Alertas/Zonas/Necesidades/Ayudas + consumo contratos G1/G2/G3 + ALTO RIESGO
import { apiGet } from "../../shared/apiClient.js";
import { obtenerNecesidades, configurarBaseUrl } from "./necesidadesApi.js";

configurarBaseUrl("http://127.0.0.1:8000/api/necesidades");

const map = L.map("map").setView([40.416775, -3.70379], 13);
const baseOSM = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, attribution: "© OpenStreetMap contributors — sin API key" });
baseOSM.addTo(map);

const capas = {
  alertas: L.layerGroup().addTo(map),
  zonas: L.layerGroup().addTo(map),
  necesidades: L.layerGroup().addTo(map),
  ayudas: L.layerGroup().addTo(map),
  zonasNecesidades: L.layerGroup().addTo(map),
  zonasAyudas: L.layerGroup().addTo(map),
};
L.control.layers({ "OpenStreetMap (gratis, sin API key)": baseOSM }, { "Alertas": capas.alertas, "Zonas ALTO RIESGO": capas.zonas, "Necesidades": capas.necesidades, "Zonas Necesidades (H3)": capas.zonasNecesidades, "Ayudas": capas.ayudas, "Zonas Ayudas (H3)": capas.zonasAyudas }, { collapsed: false }).addTo(map);

let markers = [];
let loadedNeeds = [];
let loadedAlerts = [];
let loadedAyudas = [];
let zonaActiva = null;

function getIconByPriority(prioridad) {
  let priorityClass = "priority-low";
  if (prioridad === "alta" || prioridad === "critica") priorityClass = "priority-high";
  else if (prioridad === "media") priorityClass = "priority-medium";
  return L.divIcon({ className: "", html: `<div class="marcador-custom ${priorityClass}"></div>`, iconSize: [18, 18], iconAnchor: [9, 9] });
}

function getAyudaIcon(tipo) {
  const cls = tipo === "tiempo" ? "ayuda-tiempo" : tipo === "servicios" ? "ayuda-servicio" : "ayuda-recurso";
  return L.divIcon({ className: "", html: `<div class="marcador-ayuda ${cls}"></div>`, iconSize: [16, 16], iconAnchor: [8, 8] });
}

function clearMarkers() {
  capas.necesidades.clearLayers();
  markers = [];
}

function renderMap(needsList) {
  clearMarkers();
  needsList.forEach((need) => {
    const icon = getIconByPriority(need.prioridad);
    const marker = L.marker([need.latitud, need.longitud], { icon });
    const popupContent = `
      <div class="nexo-popup" style="font-family:var(--font-base); min-width:220px;">
        <div style="background: linear-gradient(135deg, var(--nexo-teal,#17A2A0), var(--nexo-navy,#0F2038)); color: white; margin: -12px -12px 10px -12px; padding:10px 12px; border-radius:8px 8px 0 0; display:flex; gap:6px; align-items:center;">
          <span style="background:rgba(255,255,255,0.2); padding:2px 8px; border-radius:12px; font-size:0.7rem; font-weight:600;">${need.prioridad}</span>
          <span style="background:rgba(255,255,255,0.15); padding:2px 8px; border-radius:12px; font-size:0.7rem;">${need.tipo}</span>
        </div>
        <h3 style="color: var(--nexo-dark,#16181D); margin:0 0 6px 0; font-size:1.05rem; font-weight:700;">${need.titulo || need.categoria_etiqueta || need.tipo}</h3>
        ${need.direccion ? `<p style="color:var(--nexo-text-muted,#9CA0A8);margin:0 0 6px 0;font-size:0.8rem; display:flex; align-items:center; gap:4px;">📍 ${need.direccion}</p>` : ""}
        <p style="color:#4b5563;margin:0;font-size:0.85rem; line-height:1.4;">${need.descripcion || ""}</p>
        ${need.categoria_etiqueta ? `<div style="margin-top:8px; font-size:1.1rem;">${need.categoria_etiqueta}</div>` : ""}
        <button onclick="window.cambiarEstadoNecesidad(${need.id}, 'cubierta')" style="margin-top:10px; width:100%; padding:8px; background: linear-gradient(135deg, var(--nexo-teal,#17A2A0), var(--nexo-orange,#F2542D)); color:white; border:none; border-radius:20px; cursor:pointer; font-weight:600; box-shadow:0 2px 8px rgba(242,84,45,0.3);">✓ Marcar cubierta</button>
      </div>`;
    marker.bindPopup(popupContent);
    marker.addTo(capas.necesidades);
    markers.push(marker);
  });
  renderZonasNecesidades(needsList);
}

function renderAyudas(ayudasList) {
  capas.ayudas.clearLayers();
  ayudasList.forEach((ayuda) => {
    const lat = ayuda.latitud ?? ayuda.latitude;
    const lon = ayuda.longitud ?? ayuda.longitude;
    if (lat == null || lon == null) return;
    const marker = L.marker([lat, lon], { icon: getAyudaIcon(ayuda.tipo || ayuda.type) });
    marker.bindPopup(`<div class="nexo-popup"><b>${ayuda.tipo || ayuda.type}</b><br>${ayuda.categoria || ayuda.category || ""}<br><small>${ayuda.estado || ayuda.status || ""}</small></div>`);
    marker.addTo(capas.ayudas);
  });
  renderZonasAyudas(ayudasList);
}

function renderZonasNecesidades(needsList) {
  capas.zonasNecesidades.clearLayers();
  if (!needsList.length) return;
  const grid = new Map();
  const res = 0.02;
  needsList.forEach((n) => {
    const key = `${Math.floor(n.latitud / res)}_${Math.floor(n.longitud / res)}`;
    if (!grid.has(key)) grid.set(key, { count: 0, lat: Math.floor(n.latitud / res) * res + res / 2, lon: Math.floor(n.longitud / res) * res + res / 2 });
    grid.get(key).count++;
  });
  grid.forEach((cell) => {
    const color = cell.count > 5 ? "var(--nexo-alert-red, #ef4444)" : cell.count > 2 ? "var(--nexo-orange, #F2542D)" : "var(--nexo-teal, #17A2A0)";
    const bounds = [[cell.lat - res / 2, cell.lon - res / 2], [cell.lat + res / 2, cell.lon + res / 2]];
    L.rectangle(bounds, { color, weight: 1, fillColor: color, fillOpacity: 0.18 }).addTo(capas.zonasNecesidades).bindPopup(`<b>Zona Necesidades</b><br>${cell.count} necesidades<br><small>H3-like res 0.02°</small>`);
  });
}

function renderZonasAyudas(ayudasList) {
  capas.zonasAyudas.clearLayers();
  if (!ayudasList.length) return;
  const grid = new Map();
  const res = 0.02;
  ayudasList.forEach((a) => {
    const lat = a.latitud ?? a.latitude;
    const lon = a.longitud ?? a.longitude;
    if (lat == null || lon == null) return;
    const key = `${Math.floor(lat / res)}_${Math.floor(lon / res)}`;
    if (!grid.has(key)) grid.set(key, { count: 0, lat: Math.floor(lat / res) * res + res / 2, lon: Math.floor(lon / res) * res + res / 2 });
    grid.get(key).count++;
  });
  grid.forEach((cell) => {
    const color = "var(--nexo-teal, #17A2A0)";
    const bounds = [[cell.lat - res / 2, cell.lon - res / 2], [cell.lat + res / 2, cell.lon + res / 2]];
    L.rectangle(bounds, { color, weight: 1, dashArray: "4,4", fillColor: color, fillOpacity: 0.12 }).addTo(capas.zonasAyudas).bindPopup(`<b>Zona Ayudas</b><br>${cell.count} ayudas`);
  });
}

function renderAlertas(alerts) {
  capas.alertas.clearLayers();
  capas.zonas.clearLayers();
  zonaActiva = null;
  alerts.forEach((alerta) => {
    const lat = alerta.latitud ?? alerta.lat ?? alerta.latitude;
    const lon = alerta.longitud ?? alerta.lon ?? alerta.longitude;
    const zone = alerta.zone || alerta.zona;
    const isHigh = (alerta.risk_level === "high" || alerta.nivel_riesgo === "alto" || alerta.status === "high_risk" || alerta.estado === "alto_riesgo");
    if (isHigh && zone) {
      try {
        const geo = typeof zone === "string" ? JSON.parse(zone) : zone;
        const layer = L.geoJSON(geo, { style: { color: "var(--nexo-alert-red, #ef4444)", weight: 3, fillOpacity: 0.15 } }).addTo(capas.zonas);
        zonaActiva = geo;
        try { map.fitBounds(layer.getBounds(), { padding: [20, 20] }); } catch {}
      } catch {}
    }
    if (lat != null && lon != null) {
      const m = L.marker([lat, lon]).addTo(capas.alertas);
      m.bindPopup(`<b>${alerta.titulo || alerta.title || "Alerta"}</b><br>${alerta.descripcion || alerta.description || ""}<br><small>${alerta.risk_level || alerta.nivel_riesgo || ""} — ${alerta.status || alerta.estado || ""}</small>`);
    }
  });
}

function isInsideZona(lat, lon) {
  if (!zonaActiva) return true;
  try {
    const geo = zonaActiva;
    const poly = geo.type === "Feature" ? geo.geometry : geo.type === "FeatureCollection" ? geo.features[0].geometry : geo;
    if (poly.type !== "Polygon") return true;
    const vs = poly.coordinates[0];
    let inside = false;
    for (let i = 0, j = vs.length - 1; i < vs.length; j = i++) {
      const xi = vs[i][0], yi = vs[i][1], xj = vs[j][0], yj = vs[j][1];
      const intersect = yi > lat !== yj > lat && lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi;
      if (intersect) inside = !inside;
    }
    return inside;
  } catch { return true; }
}

function applyIntensityFilter(list) {
  if (!zonaActiva) return list;
  return list.filter((n) => isInsideZona(n.latitud, n.longitud));
}

function applyFilter() {
  const selectedType = document.getElementById("typeFilter")?.value;
  let filtered = loadedNeeds;
  if (selectedType && selectedType !== "all") filtered = filtered.filter((n) => n.tipo === selectedType);
  filtered = applyIntensityFilter(filtered);
  renderMap(filtered);
  const count = filtered.length;
  const badge = document.getElementById("intensityBadge");
  if (badge) {
    badge.textContent = zonaActiva ? `${count} en zona` : `${count} total`;
    badge.className = count > 5 ? "nexo-badge nexo-badge--critica" : count > 2 ? "nexo-badge nexo-badge--alta" : "nexo-badge nexo-badge--media";
    badge.style.background = count > 5 ? "var(--nexo-alert-red, #ef4444)" : count > 2 ? "var(--nexo-orange, #F2542D)" : "var(--nexo-primary, #10b981)";
  }
}

document.getElementById("typeFilter")?.addEventListener("change", applyFilter);

export async function loadNeedsFromAPI() {
  try {
    const response = await obtenerNecesidades();
    loadedNeeds = response.filter((need) => need.estado !== "cubierta");
    applyFilter();
  } catch (error) {
    console.error("Error loading needs:", error);
    try {
      const mock = await apiGet("/mocks/necesidades.mock.json");
      loadedNeeds = Array.isArray(mock) ? mock : [];
      applyFilter();
    } catch {}
  }
}

export async function loadAlertasFromAPI() {
  try {
    const data = await apiGet("/api/alertas");
    loadedAlerts = Array.isArray(data) ? data : [];
    renderAlertas(loadedAlerts);
    applyFilter();
  } catch {
    try {
      const mock = await apiGet("/mocks/alertas.mock.json");
      loadedAlerts = Array.isArray(mock) ? mock : [];
      renderAlertas(loadedAlerts);
    } catch {}
  }
}

export async function loadAyudasFromAPI() {
  try {
    let data = [];
    try { data = await apiGet("/api/ayudas"); } catch { data = await apiGet("/api/ayudas?estado=disponible"); }
    loadedAyudas = Array.isArray(data) ? data : [];
    renderAyudas(loadedAyudas);
  } catch {
    try {
      const mock = await apiGet("/mocks/ayudas.mock.json");
      loadedAyudas = Array.isArray(mock) ? mock : [];
      renderAyudas(loadedAyudas);
    } catch {}
  }
}

window.cambiarEstadoNecesidad = async (id, estado) => {
  try {
    await apiGet(`/api/necesidades/${id}`); // warmup
    const { apiPost } = await import("../../shared/apiClient.js");
    // usa PATCH vía apiPost con modulo para offline queue
    await fetch(`${"http://127.0.0.1:8000"}/api/necesidades/${id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ estado }) });
    await loadNeedsFromAPI();
  } catch (e) { console.error(e); }
};

export async function loadAllForMap() {
  await Promise.all([loadAlertasFromAPI(), loadNeedsFromAPI(), loadAyudasFromAPI()]);
}

loadAllForMap();
