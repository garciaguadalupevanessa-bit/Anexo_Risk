/**
 * Anexo_Risk — Normalization Layer (barrel export)
 *
 * Import from here:
 *   import { normalizeGDACSAlerts, EntityType, ... } from "./core/normalization/index.js";
 */

export {
  EntityType,
  TYPE_MAP,
  normalizeType,
  SeverityLevel,
  normalizeSeverity,
  normalizeCoords,
  normalizeTimestamp,
  safeText,
  DataState,
  createEntity,
} from "./domain.js";

export {
  normalizeGDACSAlerts,
  normalizeFIRMSDetections,
  normalizeClimaAlerts,
  normalizeNecesidades,
  normalizeDonaciones,
  normalizeGeneric,
} from "./sources.js";
