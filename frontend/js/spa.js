// =============================================
// ANEXO FINDER — SPA Entry Point
// Unifica: Mapa (G4) + Alertas (G2) + Donaciones (G3)
// =============================================

// --- SHARED ---
const API_BASE = "http://127.0.0.1:8000";

async function apiGet(path) {
  const resp = await fetch(`${API_BASE}${path}`);
  if (!resp.ok) throw new Error(`GET ${path} -> ${resp.status}`);
  return resp.json();
}

function formatDate(isoString) {
  if (!isoString) return "";
  const d = new Date(isoString.replace(" ", "T"));
  if (isNaN(d.getTime())) return isoString;
  return d.toLocaleString("es-ES", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}

// --- NAVIGATION ---
function showSection(name) {
  document.querySelectorAll(".section").forEach(s => s.classList.remove("active"));
  document.querySelectorAll(".nav__link").forEach(b => b.classList.remove("active"));
  const sec = document.getElementById(`section-${name}`);
  const btn = document.querySelector(`[data-section="${name}"]`);
  if (sec) sec.classList.add("active");
  if (btn) btn.classList.add("active");
  if (name === "mapa") setTimeout(() => window._map?.invalidateSize(), 100);
}
window.showSection = showSection;

document.querySelectorAll(".nav__link").forEach(btn => {
  btn.addEventListener("click", () => showSection(btn.dataset.section));
});

// --- ONLINE STATUS ---
function updateStatus() {
  const el = document.getElementById("status-text");
  if (el) el.textContent = navigator.onLine ? "ONLINE" : "OFFLINE";
}
window.addEventListener("online", updateStatus);
window.addEventListener("offline", updateStatus);
updateStatus();

// ============================================================
//  MAPA (G4 — Juan)
// ============================================================
function initMap() {
  const map = L.map("map").setView([40.4168, -3.7038], 6);
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
    zonasNecesidades: L.layerGroup().addTo(map),
    zonasAyudas: L.layerGroup().addTo(map),
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

  function getAyudaIcon(tipo) {
    const cls = tipo === "tiempo" ? "ayuda-tiempo" : tipo === "servicios" ? "ayuda-servicio" : "ayuda-recurso";
    return L.divIcon({ className: "", html: `<div class="marcador-ayuda ${cls}"></div>`, iconSize: [14, 14], iconAnchor: [7, 7] });
  }

  // --- Needs ---
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
    needsList.forEach(n => {
      if (n.latitud == null || n.longitud == null) return;
      const marker = L.marker([n.latitud, n.longitud], { icon: getIconByPriority(n.prioridad) });
      marker.bindPopup(`
        <div class="anr-popup" style="font-family:var(--font);min-width:200px;">
          <div style="display:flex;gap:6px;margin-bottom:8px;">
            <span style="background:rgba(0,240,255,0.15);color:var(--cyan);padding:2px 8px;border-radius:12px;font-size:0.7rem;font-weight:700;">${n.prioridad || 'media'}</span>
            <span style="background:rgba(255,255,255,0.1);padding:2px 8px;border-radius:12px;font-size:0.7rem;">${n.tipo || 'otros'}</span>
          </div>
          <h3 style="margin:0 0 6px;font-size:1rem;font-weight:700;">${n.titulo || n.categoria_etiqueta || n.tipo}</h3>
          ${n.direccion ? `<p style="color:var(--text-muted);font-size:0.8rem;margin:0 0 4px;">📍 ${n.direccion}</p>` : ""}
          <p style="color:var(--text-secondary);font-size:0.85rem;margin:0;">${n.descripcion || ""}</p>
          <button onclick="window.cambiarEstadoNecesidad(${n.id},'cubierta')" style="margin-top:10px;width:100%;padding:8px;background:linear-gradient(135deg,var(--cyan),var(--blue));color:var(--text-inverse);border:none;border-radius:var(--radius-sm);cursor:pointer;font-weight:700;font-size:0.8rem;">✓ Marcar cubierta</button>
        </div>`);
      marker.addTo(capas.necesidades);
    });

  }

  function renderAyudas(list) {
    capas.ayudas.clearLayers();
    list.forEach(a => {
      const lat = a.latitud ?? a.latitude;
      const lon = a.longitud ?? a.longitude;
      if (lat == null || lon == null) return;
      const m = L.marker([lat, lon], { icon: getAyudaIcon(a.tipo || a.type) });
      m.bindPopup(`<b>${a.tipo || a.type || "Ayuda"}</b><br>${a.categoria || a.category || ""}<br><small>${a.estado || a.status || ""}</small>`);
      m.addTo(capas.ayudas);
    });

  }

  function renderAlertasOnMap(alerts) {
    capas.alertas.clearLayers();
    capas.zonas.clearLayers();
    zonaActiva = null;
    alerts.forEach(a => {
      const lat = a.latitud ?? a.lat ?? a.latitude;
      const lon = a.longitud ?? a.lon ?? a.longitude;
      const zone = a.zone || a.zona;
      const isHigh = a.risk_level === "high" || a.status === "high_risk";
      if (isHigh && zone) {
        try {
          const geo = typeof zone === "string" ? JSON.parse(zone) : zone;
          const layer = L.geoJSON(geo, { style: { color: "var(--red)", weight: 3, fillOpacity: 0.15 } }).addTo(capas.zonas);
          zonaActiva = geo;
          try { map.fitBounds(layer.getBounds(), { padding: [20, 20] }); } catch {}
        } catch {}
      }
      if (lat != null && lon != null) {
        const m = L.marker([lat, lon]).addTo(capas.alertas);
        m.bindPopup(`<b>${a.titulo || a.title || "Alerta"}</b><br>${a.descripcion || a.description || ""}<br><small>${a.risk_level || ""} — ${a.status || ""}</small>`);
        m.on("click", () => {
          map.flyTo([lat, lon], 8, { duration: 1.5 });
          showSection("mapa");
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
          <span class="need-card__type">${n.categoria_etiqueta || n.tipo}</span>
          <span class="need-card__priority need-card__priority--${n.prioridad}">${n.prioridad}</span>
        </div>
        ${n.direccion ? `<div class="need-card__address">📍 ${n.direccion}</div>` : ""}
        <div class="need-card__desc">${(n.descripcion || "").substring(0, 100)}${(n.descripcion || "").length > 100 ? "..." : ""}</div>
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

  async function loadAlertasMap() {
    try {
      const data = await apiGet("/api/alertas");
      loadedAlerts = Array.isArray(data) ? data : [];
    } catch { loadedAlerts = []; }
    renderAlertasOnMap(loadedAlerts);
    updateBadge();
  }

  async function loadAyudasMap() {
    try {
      const data = await apiGet("/api/ayudas");
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

  // Map click -> set coordinates
  let tempMarker = null;
  map.on("click", e => {
    const { lat, lng } = e.latlng;
    document.getElementById("input-lat").value = lat.toFixed(6);
    document.getElementById("input-lng").value = lng.toFixed(6);
    const msg = document.getElementById("ubicacion-mensaje");
    if (msg) {
      msg.textContent = `✓ Ubicación: ${lat.toFixed(4)}, ${lng.toFixed(4)}`;
      msg.style.color = "var(--cyan)";
    }
    if (tempMarker) map.removeLayer(tempMarker);
    tempMarker = L.circleMarker([lat, lng], { radius: 10, color: "var(--orange)", fillColor: "var(--orange)", fillOpacity: 0.4, weight: 2 }).addTo(map);
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

  // Load all
  Promise.all([loadAlertasMap(), loadNeeds(), loadAyudasMap()]);
}

// ============================================================
//  ALERTAS (G2 — Javi)
// ============================================================
const TYPE_LABELS = {
  terremoto: "Terremoto", ciclon: "Ciclón", inundacion: "Inundación",
  incendio: "Incendio", volcan: "Volcán", sequia: "Sequía", otro: "Otro",
  earthquake: "Terremoto", cyclone: "Ciclón", flood: "Inundación",
  fire: "Incendio", volcano: "Volcán", drought: "Sequía", other: "Otro",
};
const SEVERITY_LABELS = { red: "Crítico", orange: "Atención", green: "Bajo riesgo" };

async function fetchAlerts() {
  const container = document.getElementById("alerts-container");
  if (!container) return;
  container.innerHTML = '<div class="state-loading"><p>Cargando alertas...</p></div>';

  const params = new URLSearchParams();
  const tipo = document.getElementById("type-filter")?.value;
  const sev = document.getElementById("severity-filter")?.value;
  const pais = document.getElementById("country-filter")?.value?.trim();
  if (tipo) params.set("tipo", tipo);
  if (sev) params.set("severidad", sev);
  if (pais) params.set("pais", pais);

  try {
    const data = await apiGet(`/api/alertas?${params.toString()}`);
    if (!data || !data.length) {
      container.innerHTML = '<div class="state-empty"><h3>No hay alertas activas</h3><p>Consulta más tarde o ajusta los filtros.</p></div>';
      return;
    }
    container.innerHTML = data.map(a => {
      const sev = a.severidad ?? a.severity ?? "green";
      const tipo = a.tipo ?? a.type ?? "otro";
      const badgeCls = sev === "red" ? "red" : sev === "orange" ? "orange" : "green";
      return `
        <div class="alert-card alert-card--${badgeCls}">
          <div class="alert-card__header">
            <div class="alert-card__title">${a.titulo || a.title || "Alerta"}</div>
            <span class="alert-card__badge alert-card__badge--${badgeCls}">${SEVERITY_LABELS[sev] || sev}</span>
          </div>
          <div class="alert-card__meta">
            <span>${TYPE_LABELS[tipo] ?? tipo}</span>
            <span>${a.pais || a.country || "País desconocido"}</span>
            <span>${formatDate(a.fecha || a.date)}</span>
          </div>
          <div class="alert-card__desc">${a.descripcion || a.description || ""}</div>
          ${a.enlace || a.link ? `<a href="${a.enlace || a.link}" target="_blank" class="btn btn--ghost btn--sm" style="margin-top:8px;">Ver detalle →</a>` : ""}
        </div>`;
    }).join("");
  } catch (err) {
    console.error("Alerts error:", err);
    container.innerHTML = '<div class="state-error"><h3>Error al cargar alertas</h3><p>Comprueba la conexión con el servidor.</p><button class="btn btn--ghost" onclick="fetchAlerts()">Reintentar</button></div>';
  }
}
window.fetchAlerts = fetchAlerts;

function initAlerts() {
  document.getElementById("type-filter")?.addEventListener("change", fetchAlerts);
  document.getElementById("severity-filter")?.addEventListener("change", fetchAlerts);
  document.getElementById("country-filter")?.addEventListener("keydown", e => { if (e.key === "Enter") fetchAlerts(); });
}

// ============================================================
//  DONACIONES (G3 — Vanessa)
// ============================================================
function initDonaciones() {
  const form = document.getElementById("form-donacion");
  const tipoEl = document.getElementById("don-tipo");
  const campoDni = document.getElementById("campo-dni");
  const dniInput = document.getElementById("dni");
  const descEl = document.getElementById("don-descripcion");
  const counterEl = document.getElementById("contador-desc");
  const listEl = document.getElementById("lista-donaciones");
  const needsListEl = document.getElementById("lista-necesidades-ayuda");
  const submitBtn = document.getElementById("btn-publicar-ayuda");
  const necesidadInfo = document.getElementById("don-necesidad-info");

  let selectedNeed = null;

  if (tipoEl) {
    tipoEl.addEventListener("change", () => {
      if (tipoEl.value === "tiempo") {
        campoDni.style.display = "block";
        dniInput.setAttribute("required", "true");
      } else {
        campoDni.style.display = "none";
        dniInput.removeAttribute("required");
        dniInput.value = "";
      }
    });
  }

  if (descEl && counterEl) {
    descEl.addEventListener("input", () => {
      counterEl.textContent = `${descEl.value.length} / 1000`;
    });
  }

  function selectNeed(need) {
    selectedNeed = need;
    document.getElementById("don-necesidad-id").value = need.id;
    if (necesidadInfo) {
      necesidadInfo.style.display = "block";
          necesidadInfo.textContent = `✓ Ayudando con: ${need.titulo || need.tipo} — ${need.direccion || (need.latitud && need.longitud ? `${need.latitud}, ${need.longitud}` : "sin ubicación")}`;
    }
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = `Ofrecer ayuda para esta necesidad`;
    }
    document.querySelectorAll(".need-card").forEach(c => c.classList.remove("is-selected"));
  }

  async function loadNecesidadesParaAyuda() {
    if (!needsListEl) return;
    needsListEl.innerHTML = '<div class="state-loading"><p>Cargando necesidades...</p></div>';
    try {
      const data = await apiGet("/api/necesidades?estado=abierta");
      if (!data || !data.length) {
        needsListEl.innerHTML = '<div class="state-empty"><p>No hay necesidades activas. ¡Buenas noticias!</p></div>';
        return;
      }
      const ICONS = {
        agua: "💧", alimentos: "🍞", parafarmacia: "💊", ropa: "👕",
        higiene: "🧴", refugio: "🏠", transporte: "🚗", otros: "📦",
      };
      needsListEl.innerHTML = data.map(n => {
        const tipo = n.tipo || n.categoria || "otros";
        const isSelected = selectedNeed && selectedNeed.id === n.id;
        return `
          <div class="need-card ${isSelected ? "is-selected" : ""}" data-need-id="${n.id}" style="cursor:pointer; padding: 12px; border: 1px solid ${isSelected ? "var(--cyan)" : "var(--border)"}; border-radius: 8px; margin-bottom: 8px; background: ${isSelected ? "var(--cyan-subtle)" : "transparent"};">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="font-size: 1.4rem;">${ICONS[tipo] || "📦"}</span>
              <div style="flex: 1;">
                <div style="font-weight: 600;">${n.titulo || tipo}</div>
                <div style="font-size: 0.8rem; color: var(--text-muted);">${n.direccion || (n.latitud && n.longitud ? `${n.latitud}, ${n.longitud}` : "Sin ubicación")}</div>
                ${n.descripcion ? `<div style="font-size: 0.85rem; margin-top: 4px;">${n.descripcion}</div>` : ""}
              </div>
              <button type="button" class="btn btn--primary btn--sm" data-need-select="${n.id}">Elegir</button>
            </div>
          </div>`;
      }).join("");

      needsListEl.querySelectorAll("[data-need-select]").forEach(btn => {
        btn.addEventListener("click", (e) => {
          e.stopPropagation();
          const need = data.find(n => n.id === parseInt(btn.dataset.needSelect));
          if (need) selectNeed(need);
        });
      });
    } catch {
      needsListEl.innerHTML = '<div class="state-error"><p>No se pudieron cargar las necesidades.</p></div>';
    }
  }

  async function loadDonaciones() {
    if (!listEl) return;
    listEl.innerHTML = '<div class="state-loading"><p>Cargando ayudas...</p></div>';
    try {
      const data = await apiGet("/api/donaciones");
      if (!data || !data.length) {
        listEl.innerHTML = '<div class="state-empty"><p>No hay ayudas publicadas todavía.</p></div>';
        return;
      }
      const ICONS = {
        "Comida": "🍞", "Medicamentos": "💊", "Transporte": "🚗",
        "Alojamiento temporal": "🏠", "Apoyo logistico": "👥", "Otros": "📦",
      };
      listEl.innerHTML = data.map(d => {
        const status = d.status || d.estado || "abierta";
        const isActive = status === "abierta" || status === "activa";
        return `
          <div class="donation-card">
            <div class="donation-card__icon"><span style="font-size:1.2rem;">${ICONS[d.recurso || d.category] || "📦"}</span></div>
            <div class="donation-card__body">
              <div class="donation-card__title">${d.recurso || d.category || "General"} — ${d.tipo || d.type || "Ayuda"}</div>
              ${d.descripcion ? `<div class="donation-card__desc">${d.descripcion}</div>` : ""}
              <div class="donation-card__meta">Contacto: ${d.contacto || "No especificado"}${d.dni ? ` · DNI: ${d.dni}` : ""}</div>
            </div>
            <span class="donation-card__status donation-card__status--${isActive ? "active" : "done"}">${isActive ? "Activa" : "Completada"}</span>
          </div>`;
      }).join("");
    } catch {
      listEl.innerHTML = '<div class="state-error"><p>No se pudieron cargar las ayudas.</p></div>';
    }
  }

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!selectedNeed) { alert("Selecciona una necesidad para ayudar."); return; }
      const recurso = document.getElementById("don-recurso").value;
      if (!recurso) { alert("Selecciona una categoría."); return; }
      const payload = {
        tipo: tipoEl.value,
        recurso,
        descripcion: descEl.value.trim(),
        contacto: document.getElementById("don-contacto").value.trim(),
        dni: tipoEl.value === "tiempo" ? dniInput.value.trim() : null,
        necesidad_id: selectedNeed.id,
      };
      submitBtn.disabled = true;
      submitBtn.textContent = "Enviando...";
      try {
        const resp = await fetch(`${API_BASE}/api/donaciones`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (!resp.ok) {
          const err = await resp.json().catch(() => ({}));
          throw new Error(err.detail || `Error ${resp.status}`);
        }
        form.reset();
        counterEl.textContent = "0 / 1000";
        campoDni.style.display = "none";
        selectedNeed = null;
        document.getElementById("don-necesidad-id").value = "";
        if (necesidadInfo) necesidadInfo.style.display = "none";
        submitBtn.textContent = "Selecciona una necesidad para ayudar";
        await Promise.all([loadNecesidadesParaAyuda(), loadDonaciones()]);
        if (typeof window.loadNecesidades === "function") await window.loadNecesidades();
      } catch (err) {
        console.error(err);
        alert("No se pudo publicar la ayuda: " + err.message);
      } finally {
        submitBtn.disabled = false;
      }
    });
  }

  loadDonaciones();
  loadNecesidadesParaAyuda();
  window.loadNecesidades = loadNecesidadesParaAyuda;
}

// ============================================================
//  BOOT
// ============================================================
document.addEventListener("DOMContentLoaded", () => {
  initMap();
  initAlerts();
  initDonaciones();
});
