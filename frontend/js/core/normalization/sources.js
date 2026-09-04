/**
 * Anexo_Risk — Source-Specific Normalizers
 *
 * Each normalizer transforms a raw backend response into an array of
 * normalized frontend entities. They handle:
 * - Field mapping from source-specific names to unified model
 * - Missing field defaults (never invented, just null)
 * - Coordinate validation
 * - Entity type assignment
 */

import {
  EntityType,
  createEntity,
  normalizeCoords,
  normalizeTimestamp,
  safeText,
} from "./domain.js";

// ---------------------------------------------------------------------------
// GDACS ALERT NORMALIZER
// ---------------------------------------------------------------------------
// Backend: /api/alertas → AlertResponse[]
// Fields: id, external_id, source, tipo, titulo, descripcion, severidad,
//         risk_level, status, is_active, zone, pais, lat, lon, fecha, enlace

export function normalizeGDACSAlerts(rawList) {
  if (!Array.isArray(rawList)) return [];
  return rawList
    .filter(item => item != null && typeof item === "object")
    .map((item) => createEntity(item, EntityType.ALERT, item.source || item.fuente || "GDACS"))
    .filter(Boolean);
}

// ---------------------------------------------------------------------------
// NASA FIRMS DETECTION NORMALIZER
// ---------------------------------------------------------------------------
// Backend: /api/incendios → { total, detecciones: FireDetection[] }
// FireDetection fields: id, satellite, latitud, longitud, brillo, confianza,
//                       fecha, pais
// Note: The Pydantic schema aliases brightness→brillo, confidence→confianza.
//       After the FASE 1.5 fix, the API now returns both alias and original.

export function normalizeFIRMSDetections(rawResponse) {
  if (!rawResponse || !Array.isArray(rawResponse.detecciones)) return [];
  return rawResponse.detecciones
    .filter(item => item != null && typeof item === "object")
    .map((item) => createEntity(item, EntityType.DETECCION, "NASA_FIRMS"))
    .filter(Boolean);
}

// ---------------------------------------------------------------------------
// CLIMA WEATHER ALERT NORMALIZER
// ---------------------------------------------------------------------------
// Backend: /api/clima → { total, alertas: WeatherAlert[], fuente, fallback_activado }
// WeatherAlert fields: id, tipo, nivel, titulo, descripcion, region, fecha, fuente
// Note: WeatherAlert has NO lat/lon. Coordinates are not provided by either
//       AEMET or Open-Meteo in the current implementation.

export function normalizeClimaAlerts(rawResponse) {
  if (!rawResponse || !Array.isArray(rawResponse.alertas)) return [];
  return rawResponse.alertas
    .filter(item => item != null && typeof item === "object")
    .map((item) => {
      const entity = createEntity(item, EntityType.WEATHER, item.fuente || "Clima");
      // Clima alerts use 'nivel' for severity, map it
      if (entity && item.nivel) {
        entity.severity = {
          level: mapClimaLevel(item.nivel),
          raw: item.nivel,
        };
      }
      return entity;
    })
    .filter(Boolean);
}

function mapClimaLevel(nivel) {
  const map = {
    rojo: "critica",
    naranja: "alta",
    amarillo: "moderada",
    verde: "informativa",
  };
  return map[String(nivel).toLowerCase()] || "sin_severidad";
}

// ---------------------------------------------------------------------------
// NECESIDAD NORMALIZER
// ---------------------------------------------------------------------------
// Backend: /api/necesidades → NeedResponse[]
// Fields: id, titulo, tipo, descripcion, direccion, latitud, longitud,
//         prioridad, estado, creado_en, categoria_etiqueta

export function normalizeNecesidades(rawList) {
  if (!Array.isArray(rawList)) return [];
  return rawList
    .filter(item => item != null && typeof item === "object")
    .map((item) => createEntity(item, EntityType.NEED, "necesidades"))
    .filter(Boolean);
}

// ---------------------------------------------------------------------------
// DONACIÓN / RECURSO NORMALIZER
// ---------------------------------------------------------------------------
// Backend: /api/donaciones → DonationResponse[]
// Fields: id, tipo, recurso, cantidad, descripcion, contacto, dni,
//         estado, creado_en, latitud, longitud

export function normalizeDonaciones(rawList) {
  if (!Array.isArray(rawList)) return [];
  return rawList
    .filter(item => item != null && typeof item === "object")
    .map((item) => createEntity(item, EntityType.RESOURCE, "donaciones"))
    .filter(Boolean);
}

// ---------------------------------------------------------------------------
// GENERIC NORMALIZER (for unknown/future sources)
// ---------------------------------------------------------------------------

export function normalizeGeneric(rawList, entityType = EntityType.ALERT, source = "unknown") {
  if (!Array.isArray(rawList)) return [];
  return rawList
    .map((item) => createEntity(item, entityType, source))
    .filter(Boolean);
}
