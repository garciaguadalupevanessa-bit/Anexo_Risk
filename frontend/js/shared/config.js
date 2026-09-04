// Centralized API config and shared utilities
import { SeverityLevel } from "../core/normalization/index.js";

export const API_BASE = "";

export async function apiGet(path) {
  const resp = await fetch(`${API_BASE}${path}`);
  if (!resp.ok) throw new Error(`GET ${path} -> ${resp.status}`);
  return resp.json();
}

export function formatDate(isoString) {
  if (!isoString) return "";
  const d = new Date(isoString.replace(" ", "T"));
  if (isNaN(d.getTime())) return isoString;
  return d.toLocaleString("es-ES", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
}

// --- Shared constants used by alertas, dashboard, mapa ---

export const TYPE_LABELS = {
  terremoto: "Terremoto", ciclon: "Ciclón", inundacion: "Inundación",
  incendio: "Incendio", volcan: "Volcán", sequia: "Sequía", otro: "Otro",
  earthquake: "Terremoto", cyclone: "Ciclón", flood: "Inundación",
  fire: "Incendio", volcano: "Volcán", drought: "Sequía", other: "Otro",
  calor: "Ola de calor", viento: "Viento fuerte", lluvia: "Lluvia intensa",
  nieve: "Nieve", tormenta: "Tormenta", general: "Aviso general",
};

export const SEVERITY_LABELS = {
  critica: "Crítico", alta: "Atención", moderada: "Moderada",
  informativa: "Informativa", sin_severidad: "Sin severidad",
  red: "Crítico", orange: "Atención", green: "Bajo riesgo",
};

export const SEV_CLASS_MAP = {
  [SeverityLevel.CRITICAL]: "critica",
  [SeverityLevel.HIGH]: "alta",
  [SeverityLevel.MODERATE]: "moderada",
  [SeverityLevel.LOW]: "informativa",
  [SeverityLevel.UNKNOWN]: "sin-dato",
};

export const REGION_COUNTRIES = {
  espana: ["Spain", "España", "Espana"],
  europa: [
    "Spain", "France", "Germany", "Italy", "Portugal", "United Kingdom",
    "Poland", "Romania", "Netherlands", "Belgium", "Sweden", "Austria",
    "Switzerland", "Czech Republic", "Denmark", "Finland", "Greece",
    "Hungary", "Ireland", "Norway", "Slovakia", "Slovenia", "Croatia",
    "Luxembourg", "Lithuania", "Latvia", "Estonia", "Cyprus", "Malta",
    "Bulgaria", "Serbia", "Bosnia", "Ukraine", "Russia",
    "Austria, Switzerland", "Bosnia and Herzegovina, Croatia",
    "China, Kyrgyzstan, Kazakhstan, Mongolia, Russia",
    "Austria, Bosnia & Herzegovina, Belgium, Belarus, Switzerland, Czech Republic, Germany, Denmark, Spain, France, Croatia, Hungary, Ireland, Italy, Liechtenstein, Luxembourg, Netherlands, Poland, Romania, Serbia, Sweden, Slovenia, Slovakia, San Marino, Ukraine",
  ],
};

export function matchesRegion(pais, region) {
  if (!region || region === "world") return true;
  if (!pais) return false;
  const paisLower = pais.toLowerCase();
  const keywords = REGION_COUNTRIES[region] || [];
  return keywords.some(k => paisLower.includes(k.toLowerCase()));
}

// --- XSS Protection ---
const _escMap = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#x27;" };
const _escRe = /[&<>"']/g;
export function escapeHtml(str) {
  if (str == null) return "";
  return String(str).replace(_escRe, c => _escMap[c]);
}
