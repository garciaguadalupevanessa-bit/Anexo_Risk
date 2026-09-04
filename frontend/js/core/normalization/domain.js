/**
 * Anexo_Risk — Domain Entity Model & Normalization Layer
 *
 * Defines the unified frontend entity model and normalization functions.
 * All backend responses are mapped through this layer before reaching the UI.
 *
 * Rules:
 * - No invented data. If a field is absent, it stays null.
 * - The original raw value is always preserved alongside the normalized one.
 * - UI must handle null/missing fields gracefully.
 */

// ---------------------------------------------------------------------------
// 1. ENTITY TYPES
// ---------------------------------------------------------------------------

export const EntityType = Object.freeze({
  ALERT: "alerta",
  INCIDENT: "incidente",
  NEED: "necesidad",
  RESOURCE: "recurso",
  WEATHER: "meteorologia",
  DETECCION: "deteccion",
});

// ---------------------------------------------------------------------------
// 2. NORMALIZED TYPE MAPPING (raw code → human label)
//    Only includes types that actually exist in the backend responses.
// ---------------------------------------------------------------------------

export const TYPE_MAP = Object.freeze({
  // GDACS event types (gdacs_client.py _EVENT_TYPES)
  terremoto: { label: "Terremoto", icon: "🌋", category: EntityType.ALERT },
  ciclon:    { label: "Ciclón tropical", icon: "🌀", category: EntityType.ALERT },
  inundacion: { label: "Inundación", icon: "🌊", category: EntityType.ALERT },
  incendio:  { label: "Incendio forestal", icon: "🔥", category: EntityType.ALERT },
  volcan:    { label: "Volcán", icon: "🌋", category: EntityType.ALERT },
  sequia:    { label: "Sequía", icon: "☀️", category: EntityType.ALERT },
  otro:      { label: "Otro", icon: "⚠️", category: EntityType.ALERT },

  // Clima weather types (clima/models.py Open-Meteo)
  calor:    { label: "Ola de calor", icon: "🌡️", category: EntityType.WEATHER },
  viento:   { label: "Viento fuerte", icon: "💨", category: EntityType.WEATHER },
  lluvia:   { label: "Lluvia intensa", icon: "🌧️", category: EntityType.WEATHER },
  nieve:    { label: "Nieve", icon: "❄️", category: EntityType.WEATHER },
  tormenta: { label: "Tormenta", icon: "⛈️", category: EntityType.WEATHER },
  general:  { label: "Aviso general", icon: "📋", category: EntityType.WEATHER },
});

/**
 * Returns the human-readable label for a raw type code.
 * Falls back to the raw value itself if unknown.
 */
export function normalizeType(raw) {
  if (!raw) return { label: "Desconocido", icon: "❓", category: EntityType.ALERT };
  const key = String(raw).toLowerCase().trim();
  return TYPE_MAP[key] || { label: raw, icon: "❓", category: EntityType.ALERT };
}

// ---------------------------------------------------------------------------
// 3. SEVERITY NORMALIZATION
//    Backend sources use different scales. This maps them to a unified set.
// ---------------------------------------------------------------------------

export const SeverityLevel = Object.freeze({
  CRITICAL: "critica",
  HIGH: "alta",
  MODERATE: "moderada",
  LOW: "informativa",
  UNKNOWN: "sin_severidad",
});

// GDACS: RED/ORANGE/GREEN → severity enum
const GDACS_SEVERITY_MAP = Object.freeze({
  RED:    SeverityLevel.CRITICAL,
  ORANGE: SeverityLevel.HIGH,
  GREEN:  SeverityLevel.MODERATE,
});

// Clima: rojo/naranja/amarillo/verde → severity
const CLIMA_SEVERITY_MAP = Object.freeze({
  rojo:     SeverityLevel.CRITICAL,
  naranja:  SeverityLevel.HIGH,
  amarillo: SeverityLevel.MODERATE,
  verde:    SeverityLevel.LOW,
});

/**
 * Normalizes a severity value from any source to a unified level.
 * Preserves the original value in `raw`.
 *
 * @param {string|null} value - The raw severity value
 * @param {string} source - The data source ("GDACS", "AEMET", "Open-Meteo", "NASA_FIRMS")
 * @returns {{ level: string, raw: string|null }}
 */
export function normalizeSeverity(value, source = "") {
  if (value == null || value === "") {
    return { level: SeverityLevel.UNKNOWN, raw: null };
  }

  const src = String(source).toUpperCase();
  const raw = String(value);

  if (src.includes("GDACS")) {
    const mapped = GDACS_SEVERITY_MAP[raw.toUpperCase()];
    return { level: mapped || SeverityLevel.UNKNOWN, raw };
  }

  if (src.includes("AEMET") || src.includes("OPEN-METEO")) {
    const mapped = CLIMA_SEVERITY_MAP[raw.toLowerCase()];
    return { level: mapped || SeverityLevel.UNKNOWN, raw };
  }

  // NASA FIRMS / unknown sources: no severity provided
  return { level: SeverityLevel.UNKNOWN, raw };
}

// ---------------------------------------------------------------------------
// 4. COORDINATE VALIDATION
// ---------------------------------------------------------------------------

/**
 * Validates and sanitizes geographic coordinates.
 * Returns null if invalid, or { lat, lon } if valid.
 */
export function normalizeCoords(lat, lon) {
  const la = parseFloat(lat);
  const lo = parseFloat(lon);
  if (Number.isNaN(la) || Number.isNaN(lo)) return null;
  if (la < -90 || la > 90 || lo < -180 || lo > 180) return null;
  return { lat: la, lon: lo };
}

// ---------------------------------------------------------------------------
// 5. TIMESTAMP NORMALIZATION
// ---------------------------------------------------------------------------

/**
 * Parses a timestamp from various formats to ISO string or null.
 * Handles: ISO strings, Date objects, Unix timestamps, empty strings.
 */
export function normalizeTimestamp(value) {
  if (value == null || value === "") return null;
  if (value instanceof Date) {
    return Number.isNaN(value.getTime()) ? null : value.toISOString();
  }
  if (typeof value === "number") {
    const d = new Date(value > 1e12 ? value : value * 1000);
    return Number.isNaN(d.getTime()) ? null : d.toISOString();
  }
  if (typeof value === "string") {
    const d = new Date(value);
    return Number.isNaN(d.getTime()) ? null : d.toISOString();
  }
  return null;
}

// ---------------------------------------------------------------------------
// 6. TEXT SANITIZATION
// ---------------------------------------------------------------------------

/**
 * Returns a clean string, or fallback if empty/null.
 * Strips HTML tags to prevent XSS in popups.
 */
export function safeText(value, fallback = "") {
  if (value == null) return fallback;
  const s = String(value).trim();
  if (!s) return fallback;
  // Strip simple HTML tags
  return s.replace(/<[^>]*>/g, "");
}

// ---------------------------------------------------------------------------
// 7. DATA STATE ENUM (for loading indicators)
// ---------------------------------------------------------------------------

export const DataState = Object.freeze({
  IDLE: "idle",
  LOADING: "loading",
  SUCCESS: "success",
  EMPTY: "empty",
  ERROR: "error",
  OFFLINE: "offline",
  STALE: "stale",
});

// ---------------------------------------------------------------------------
// 8. UNIFIED FRONTEND ENTITY
// ---------------------------------------------------------------------------

/**
 * Creates a normalized frontend entity from any backend source.
 * All fields are optional — UI must handle nulls.
 *
 * @param {object} raw - The raw backend response item
 * @param {string} entityType - One of EntityType values
 * @param {string} source - The data source identifier
 * @returns {object} Normalized entity
 */
export function createEntity(raw, entityType, source = "") {
  if (!raw || typeof raw !== "object") return null;

  const typeInfo = normalizeType(raw.tipo || raw.type);
  const severity = normalizeSeverity(
    raw.severidad || raw.severity || raw.nivel || raw.level,
    source
  );
  const coords = normalizeCoords(
    raw.latitud ?? raw.lat ?? raw.latitude,
    raw.longitud ?? raw.lon ?? raw.longitude
  );

  return {
    // Identity
    id: raw.id != null ? String(raw.id) : null,
    externalId: raw.external_id != null ? String(raw.external_id) : null,

    // Classification
    entityType,
    type: typeInfo,
    severity,
    source: source || raw.source || raw.fuente || "",

    // Content
    title: safeText(raw.titulo || raw.title),
    description: safeText(raw.descripcion || raw.description),

    // Location
    coords,
    country: safeText(raw.pais || raw.country),
    address: safeText(raw.direccion || raw.address),
    region: safeText(raw.region || raw.zona),

    // Timestamps
    timestamp: normalizeTimestamp(raw.fecha || raw.date || raw.created_at || raw.creado_en),
    updatedAt: normalizeTimestamp(raw.updated_at),

    // Status
    status: raw.status || raw.estado || null,
    isActive: raw.is_active != null ? Boolean(raw.is_active) : null,

    // Source-specific extras (preserved for source-specific rendering)
    extras: extractExtras(raw, entityType),

    // Raw reference (for debugging / source-specific fields)
    _raw: raw,
  };
}

/**
 * Extracts source-specific fields that don't fit the unified model.
 * These are preserved for source-specific rendering (e.g., NASA FIRMS brightness).
 */
function extractExtras(raw, entityType) {
  const extras = {};

  if (entityType === EntityType.DETECCION) {
    // NASA FIRMS specific fields
    extras.satellite = raw.satellite || null;
    extras.brightness = raw.brightness ?? raw.brillo ?? null;
    extras.confidence = raw.confidence ?? raw.confianza ?? null;
    extras.frp = raw.frp ?? null;
    extras.acqDate = raw.acq_date || null;
    extras.acqTime = raw.acq_time || null;
  }

  if (entityType === EntityType.ALERT) {
    // GDACS/alert specific fields
    extras.riskLevel = raw.risk_level || null;
    extras.zone = raw.zone || null;
    extras.enlace = raw.enlace || raw.link || null;
  }

  if (entityType === EntityType.NEED) {
    // Necesidad specific fields
    extras.prioridad = raw.prioridad || raw.priority || null;
    extras.categoriaEtiqueta = raw.categoria_etiqueta || raw.category_label || null;
    extras.direccion = raw.direccion || raw.address || null;
  }

  if (entityType === EntityType.RESOURCE) {
    // Donación specific fields
    extras.recurso = raw.recurso || raw.resource || null;
    extras.cantidad = raw.cantidad || raw.quantity || null;
    extras.contacto = raw.contacto || raw.contact || null;
    extras.necesidadId = raw.necesidad_id || null;
  }

  return extras;
}
