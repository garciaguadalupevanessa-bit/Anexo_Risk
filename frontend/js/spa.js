// =============================================
// ANEXO FINDER — SPA Orchestrator
// Navigation, shell (sidebar/drawer), boot
// =============================================

import { initMap } from "./sections/mapa.js";
import { fetchAlerts, initAlerts } from "./sections/alertas.js";
import { initDonaciones } from "./sections/ayudas.js";
import { loadDashboard } from "./sections/dashboard.js";

// --- NAVIGATION ---
function showSection(name) {
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
  if (name === "dashboard") loadDashboard();
  if (name === "alertas") fetchAlerts();
  if (name === "ayudas") window.loadAyudasSection?.();
  closeSidebar();
}
window.showSection = showSection;

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
    fields.push({ label: "Severidad", value: sevLabels[entity.severity.level] || entity.severity.level, cls: `sev-badge sev-badge--${entity.severity.level === "critica" ? "critica" : entity.severity.level === "alta" ? "alta" : entity.severity.level === "moderada" ? "moderada" : "informativa"}` });
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
  if (entity.extras?.enlace) fields.push({ label: "Enlace externo", value: `<a href="${entity.extras.enlace}" target="_blank" rel="noopener noreferrer">Ver detalle →</a>` });
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
const statusDot = document.querySelector(".status-dot");
function updateStatus() {
  const el = document.getElementById("status-text");
  const online = navigator.onLine;
  if (el) el.textContent = online ? "ONLINE" : "OFFLINE";
  if (statusDot) {
    statusDot.style.background = online ? "var(--green)" : "var(--offline)";
    statusDot.style.boxShadow = online ? "0 0 8px var(--green-glow)" : "none";
  }
}
window.addEventListener("online", updateStatus);
window.addEventListener("offline", updateStatus);
updateStatus();

// --- BOOT ---
document.addEventListener("DOMContentLoaded", () => {
  initMap();
  initAlerts();
  initDonaciones();
  loadDashboard();
});
