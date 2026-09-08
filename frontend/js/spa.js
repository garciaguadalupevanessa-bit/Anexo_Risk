// =============================================
// ANEXO RISK — SPA Orchestrator 2.x
// Navigation, shell (sidebar/drawer), status bar, boot
// =============================================

import { initMap } from "./sections/mapa.js";
import { fetchAlerts, initAlerts } from "./sections/alertas.js";
import { initDonaciones } from "./sections/ayudas.js";
import { loadDashboard } from "./sections/dashboard.js";
import { initDecisionCenter, loadDecisionContext, loadIncidentDecisionContext } from "./sections/decision-center.js";
import { renderRiskCard } from "./sections/risk-card.js";
import { renderTimeline } from "./sections/timeline.js";
import { updateFreshness } from "./sections/freshness.js";

window._updateFreshness = updateFreshness;

// --- NAVIGATION ---
function showSection(name) {
  window._trackEvent?.("section_open", { section: name });
  document.querySelectorAll(".section").forEach(s => s.classList.remove("active"));
  document.querySelectorAll(".nav__link").forEach(b => {
    b.classList.remove("active");
    b.removeAttribute("aria-current");
  });
  const sec = document.getElementById(`section-${name}`);
  const btn = document.querySelector(`[data-section="${name}"]`);
  if (sec) sec.classList.add("active");
  if (btn) {
    btn.classList.add("active");
    btn.setAttribute("aria-current", "page");
  }
  if (name === "mapa") setTimeout(() => window._map?.invalidateSize(), 100);
  if (name === "decision") initDecisionCenter();
  if (name === "dashboard") loadDashboard();
  if (name === "alertas") fetchAlerts();
  if (name === "ayudas") window.loadAyudasSection?.();
  closeSidebar();
}
window.showSection = showSection;
window.loadIncidentDecisionContext = loadIncidentDecisionContext;

// --- COMMAND VIEW ---
let _commandViewActive = false;

function toggleCommandView() {
  _commandViewActive = !_commandViewActive;
  document.body.classList.toggle("command-view", _commandViewActive);
  const btn = document.getElementById("cmd-view-toggle");
  if (btn) {
    btn.classList.toggle("active", _commandViewActive);
    btn.setAttribute("aria-pressed", _commandViewActive);
  }
  setTimeout(() => window._map?.invalidateSize(), 200);
}
window.toggleCommandView = toggleCommandView;

// Auto-activate command view on large screens
if (window.matchMedia("(min-width: 1920px)").matches) {
  toggleCommandView();
}

document.querySelectorAll(".nav__link").forEach(btn => {
  btn.addEventListener("click", () => showSection(btn.dataset.section));
});

// --- SIDEBAR TOGGLE ---
const sidebarEl = document.getElementById("app-sidebar");
const sidebarOverlay = document.getElementById("sidebar-overlay");
const sidebarToggle = document.getElementById("sidebar-toggle");
const sidebarClose = document.getElementById("sidebar-close");

function openSidebar() {
  sidebarEl?.classList.add("open");
  sidebarEl?.setAttribute("aria-hidden", "false");
  sidebarOverlay?.classList.add("active");
  sidebarOverlay?.setAttribute("aria-hidden", "false");
  sidebarToggle?.setAttribute("aria-expanded", "true");
  document.body.style.overflow = "hidden";
}

function closeSidebar() {
  sidebarEl?.classList.remove("open");
  sidebarEl?.setAttribute("aria-hidden", "true");
  sidebarOverlay?.classList.remove("active");
  sidebarOverlay?.setAttribute("aria-hidden", "true");
  sidebarToggle?.setAttribute("aria-expanded", "false");
  document.body.style.overflow = "";
}

sidebarToggle?.addEventListener("click", () => {
  const isOpen = sidebarEl?.classList.contains("open");
  isOpen ? closeSidebar() : openSidebar();
});
sidebarClose?.addEventListener("click", closeSidebar);
sidebarOverlay?.addEventListener("click", closeSidebar);

document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    if (sidebarEl?.classList.contains("open")) closeSidebar();
    if (drawerEl?.classList.contains("active")) closeDrawer();
  }
});

// --- DRAWER ---
const drawerEl = document.getElementById("entity-drawer");
const drawerBackdrop = document.getElementById("drawer-backdrop");
const drawerTitle = document.getElementById("drawer-title");
const drawerBody = document.getElementById("drawer-body");
const drawerCloseBtn = document.getElementById("drawer-close");

function openDrawer(title, html) {
  if (drawerTitle) drawerTitle.textContent = title;
  if (drawerBody) drawerBody.innerHTML = html;
  drawerEl?.classList.add("active");
  drawerEl?.setAttribute("aria-hidden", "false");
  drawerBackdrop?.classList.add("active");
  drawerBackdrop?.setAttribute("aria-hidden", "false");
  document.body.style.overflow = "hidden";
  drawerEl?.focus();
}

function closeDrawer() {
  drawerEl?.classList.remove("active");
  drawerEl?.setAttribute("aria-hidden", "true");
  drawerBackdrop?.classList.remove("active");
  drawerBackdrop?.setAttribute("aria-hidden", "true");
  document.body.style.overflow = "";
}

drawerCloseBtn?.addEventListener("click", closeDrawer);
drawerBackdrop?.addEventListener("click", closeDrawer);

function renderDrawerFields(entity) {
  const fields = [];
  if (entity.type?.label) fields.push({ label: "Tipo", value: `${entity.type.icon || ""} ${entity.type.label}` });
  if (entity.severity?.level && entity.severity.level !== "sin_severidad") {
    const sevLabels = { critica: "Crítica", alta: "Alta", moderada: "Moderada", informativa: "Informativa" };
    fields.push({ label: "Severidad", value: sevLabels[entity.severity.level] || entity.severity.level, cls: `sev-badge sev-badge--${entity.severity.level}` });
  }
  if (entity.source) fields.push({ label: "Fuente", value: entity.source });
  if (entity.title) fields.push({ label: "Título", value: entity.title });
  if (entity.description) fields.push({ label: "Descripción", value: entity.description });
  if (entity.coords) fields.push({ label: "Coordenadas", value: `${entity.coords.lat.toFixed(4)}, ${entity.coords.lon.toFixed(4)}` });
  if (entity.country) fields.push({ label: "País/Región", value: entity.country });
  if (entity.address) fields.push({ label: "Dirección", value: entity.address });
  if (entity.timestamp) fields.push({ label: "Fecha", value: entity.timestamp });
  if (entity.status) fields.push({ label: "Estado", value: entity.status });
  if (entity.extras?.riskLevel) fields.push({ label: "Nivel de riesgo", value: entity.extras.riskLevel });
  if (entity.extras?.enlace) {
    const safeUrl = /^(https?:\/\/)/i.test(entity.extras.enlace) ? entity.extras.enlace : "#";
    fields.push({ label: "Enlace", value: `<a href="${safeUrl}" target="_blank" rel="noopener noreferrer">Ver detalle →</a>` });
  }
  if (entity.extras?.satellite) fields.push({ label: "Satélite", value: entity.extras.satellite });
  if (entity.extras?.brightness != null) fields.push({ label: "Brillo", value: `${Number(entity.extras.brightness).toFixed(1)} K` });
  if (entity.extras?.confidence) fields.push({ label: "Confianza", value: entity.extras.confidence });
  if (entity.extras?.frp != null) fields.push({ label: "FRP", value: `${Number(entity.extras.frp).toFixed(1)} MW` });
  if (entity.extras?.prioridad) fields.push({ label: "Prioridad", value: entity.extras.prioridad });
  if (entity.extras?.categoriaEtiqueta) fields.push({ label: "Categoría", value: entity.extras.categoriaEtiqueta });
  if (entity.extras?.recurso) fields.push({ label: "Recurso", value: entity.extras.recurso });
  if (entity.extras?.cantidad) fields.push({ label: "Cantidad", value: entity.extras.cantidad });
  if (entity.extras?.contacto) fields.push({ label: "Contacto", value: entity.extras.contacto });

  return fields.map(f => `
    <div class="drawer__field">
      <div class="drawer__field-label">${f.label}</div>
      <div class="drawer__field-value${f.cls ? ` ${f.cls}` : ""}">${f.value}</div>
    </div>
  `).join("");
}
window.openDrawer = openDrawer;
window.closeDrawer = closeDrawer;
window.renderDrawerFields = renderDrawerFields;

// --- ONLINE STATUS ---
const statusDot = document.getElementById("status-dot");
function updateStatus() {
  const el = document.getElementById("status-text");
  const online = navigator.onLine;
  if (el) el.textContent = online ? "ONLINE" : "OFFLINE";
  if (statusDot) {
    statusDot.classList.toggle("status-dot--offline", !online);
  }
}
window.addEventListener("online", updateStatus);
window.addEventListener("offline", updateStatus);
updateStatus();

// --- STATUS BAR ---
let _statusBarData = { critical: 0, high: 0, needs: 0, uncovered: 0, resources: 0, incidents: 0 };

function updateStatusBar(data) {
  Object.assign(_statusBarData, data);
  const set = (id, val) => {
    const el = document.getElementById(id);
    if (el) el.textContent = val;
  };
  set("sb-critical", _statusBarData.critical);
  set("sb-high", _statusBarData.high);
  set("sb-incidents", _statusBarData.incidents);
  set("sb-needs", _statusBarData.needs);
  set("sb-uncovered", _statusBarData.uncovered);
  set("sb-resources", _statusBarData.resources);
}
window._updateStatusBar = updateStatusBar;

// --- BOOT ---
document.addEventListener("DOMContentLoaded", () => {
  window._trackEvent?.("app_open");
  initMap();
  initAlerts();
  initDonaciones();
  loadDashboard();
});
