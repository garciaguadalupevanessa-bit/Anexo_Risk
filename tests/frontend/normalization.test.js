/**
 * Anexo_Risk — Normalization Layer Tests
 *
 * Run: node --input-type=module < tests/frontend/normalization.test.js
 * Or:  node --experimental-vm-modules tests/frontend/normalization.test.js
 *
 * Tests cover:
 * - Type normalization
 * - Severity normalization
 * - Coordinate validation
 * - Timestamp normalization
 * - GDACS alert normalization
 * - NASA FIRMS detection normalization
 * - Clima alert normalization
 * - Necesidad normalization
 * - Donación normalization
 * - Incomplete/missing data handling
 * - Null/undefined field safety
 */

import {
  EntityType,
  normalizeType,
  SeverityLevel,
  normalizeSeverity,
  normalizeCoords,
  normalizeTimestamp,
  safeText,
  DataState,
  createEntity,
} from "../../frontend/js/core/normalization/domain.js";
import {
  normalizeGDACSAlerts,
  normalizeFIRMSDetections,
  normalizeClimaAlerts,
  normalizeNecesidades,
  normalizeDonaciones,
} from "../../frontend/js/core/normalization/sources.js";

let passed = 0;
let failed = 0;

function assert(condition, msg) {
  if (condition) {
    passed++;
  } else {
    failed++;
    console.error(`  FAIL: ${msg}`);
  }
}

function assertEq(actual, expected, msg) {
  if (actual === expected) {
    passed++;
  } else {
    failed++;
    console.error(`  FAIL: ${msg} — expected "${expected}", got "${actual}"`);
  }
}

function section(name) {
  console.log(`\n--- ${name} ---`);
}

// =========================================================================
// 1. TYPE NORMALIZATION
// =========================================================================
section("normalizeType");

assertEq(normalizeType("terremoto").label, "Terremoto", "terremoto → Terremoto");
assertEq(normalizeType("ciclon").label, "Ciclón tropical", "ciclon → Ciclón tropical");
assertEq(normalizeType("inundacion").label, "Inundación", "inundacion → Inundación");
assertEq(normalizeType("incendio").label, "Incendio forestal", "incendio → Incendio forestal");
assertEq(normalizeType("volcan").label, "Volcán", "volcan → Volcán");
assertEq(normalizeType("sequia").label, "Sequía", "sequia → Sequía");
assertEq(normalizeType("otro").label, "Otro", "otro → Otro");
assertEq(normalizeType("calor").label, "Ola de calor", "calor → Ola de calor");
assertEq(normalizeType("viento").label, "Viento fuerte", "viento → Viento fuerte");
assertEq(normalizeType("lluvia").label, "Lluvia intensa", "lluvia → Lluvia intensa");
assertEq(normalizeType(null).label, "Desconocido", "null → Desconocido");
assertEq(normalizeType("").label, "Desconocido", "empty → Desconocido");
assertEq(normalizeType("tipo_inexistente").label, "tipo_inexistente", "unknown → raw value");

assertEq(normalizeType("terremoto").category, EntityType.ALERT, "terremoto category = ALERT");
assertEq(normalizeType("calor").category, EntityType.WEATHER, "calor category = WEATHER");

// =========================================================================
// 2. SEVERITY NORMALIZATION
// =========================================================================
section("normalizeSeverity");

const gdacsRed = normalizeSeverity("RED", "GDACS");
assertEq(gdacsRed.level, SeverityLevel.CRITICAL, "GDACS RED → critica");
assertEq(gdacsRed.raw, "RED", "GDACS RED raw preserved");

const gdacsOrange = normalizeSeverity("ORANGE", "GDACS");
assertEq(gdacsOrange.level, SeverityLevel.HIGH, "GDACS ORANGE → alta");

const gdacsGreen = normalizeSeverity("GREEN", "GDACS");
assertEq(gdacsGreen.level, SeverityLevel.MODERATE, "GDACS GREEN → moderada");

const climaRojo = normalizeSeverity("rojo", "Open-Meteo");
assertEq(climaRojo.level, SeverityLevel.CRITICAL, "clima rojo → critica");

const climaAmarillo = normalizeSeverity("amarillo", "AEMET");
assertEq(climaAmarillo.level, SeverityLevel.MODERATE, "clima amarillo → moderada");

const climaVerde = normalizeSeverity("verde", "AEMET");
assertEq(climaVerde.level, SeverityLevel.LOW, "clima verde → informativa");

const nullSev = normalizeSeverity(null, "GDACS");
assertEq(nullSev.level, SeverityLevel.UNKNOWN, "null → sin_severidad");
assertEq(nullSev.raw, null, "null raw = null");

const emptySev = normalizeSeverity("", "NASA_FIRMS");
assertEq(emptySev.level, SeverityLevel.UNKNOWN, "empty → sin_severidad (NASA FIRMS)");

// =========================================================================
// 3. COORDINATE VALIDATION
// =========================================================================
section("normalizeCoords");

const valid = normalizeCoords(40.4168, -3.7038);
assert(valid !== null, "valid coords not null");
assertEq(valid.lat, 40.4168, "valid lat");
assertEq(valid.lon, -3.7038, "valid lon");

const validStr = normalizeCoords("37.17", "-3.60");
assert(validStr !== null, "string coords not null");
assertEq(validStr.lat, 37.17, "string lat parsed");

assertEq(normalizeCoords(null, null), null, "null coords → null");
assertEq(normalizeCoords("", ""), null, "empty coords → null");
assertEq(normalizeCoords(91, 0), null, "lat > 90 → null");
assertEq(normalizeCoords(-91, 0), null, "lat < -90 → null");
assertEq(normalizeCoords(0, 181), null, "lon > 180 → null");
assertEq(normalizeCoords(0, -181), null, "lon < -180 → null");
assertEq(normalizeCoords(NaN, NaN), null, "NaN → null");

// =========================================================================
// 4. TIMESTAMP NORMALIZATION
// =========================================================================
section("normalizeTimestamp");

const isoTs = normalizeTimestamp("2026-04-30T13:07:47Z");
assert(isoTs !== null, "ISO string parsed");
assert(isoTs.includes("2026"), "ISO string contains year");

const dateObj = normalizeTimestamp(new Date("2026-01-15"));
assert(dateObj !== null, "Date object parsed");

const unixTs = normalizeTimestamp(1714500000);
assert(unixTs !== null, "Unix timestamp parsed");

assertEq(normalizeTimestamp(null), null, "null → null");
assertEq(normalizeTimestamp(""), null, "empty → null");
assertEq(normalizeTimestamp("not-a-date"), null, "invalid string → null");

// =========================================================================
// 5. SAFE TEXT
// =========================================================================
section("safeText");

assertEq(safeText(null, "fallback"), "fallback", "null → fallback");
assertEq(safeText("", "fallback"), "fallback", "empty → fallback");
assertEq(safeText("  hello  ", ""), "hello", "trimmed");
assertEq(safeText("<script>alert(1)</script>", ""), "alert(1)", "HTML stripped");
assertEq(safeText(undefined, "default"), "default", "undefined → default");

// =========================================================================
// 6. GDACS ALERT NORMALIZATION
// =========================================================================
section("normalizeGDACSAlerts");

const gdacsRaw = [
  {
    id: "gdacs-FL20260002",
    external_id: "gdacs-FL20260002",
    source: "GDACS",
    tipo: "inundacion",
    titulo: "Flood - Spain",
    descripcion: "Severe flooding in the Ebro river basin",
    severidad: "RED",
    risk_level: "high",
    status: "active",
    is_active: true,
    pais: "Spain",
    lat: 41.65,
    lon: -0.88,
    fecha: "2026-04-30T13:07:47Z",
    enlace: "https://www.gdacs.org/report.aspx?eventid=1002",
  },
  {
    id: "gdacs-EQ20260001",
    tipo: "terremoto",
    titulo: "Earthquake - Spain",
    severidad: "GREEN",
    pais: "Spain",
    lat: 37.17,
    lon: -3.60,
    fecha: "2026-04-29T08:30:00Z",
  },
];

const gdacsEntities = normalizeGDACSAlerts(gdacsRaw);
assertEq(gdacsEntities.length, 2, "GDACS: 2 entities created");

const e1 = gdacsEntities[0];
assertEq(e1.entityType, EntityType.ALERT, "entity type = ALERT");
assertEq(e1.type.label, "Inundación", "type label");
assertEq(e1.severity.level, SeverityLevel.CRITICAL, "severity = critica");
assertEq(e1.severity.raw, "RED", "raw severity preserved");
assertEq(e1.title, "Flood - Spain", "title");
assertEq(e1.country, "Spain", "country");
assertEq(e1.coords.lat, 41.65, "latitude");
assertEq(e1.coords.lon, -0.88, "longitude");
assertEq(e1.source, "GDACS", "source");
assertEq(e1.extras.riskLevel, "high", "risk_level in extras");
assertEq(e1.extras.enlace, "https://www.gdacs.org/report.aspx?eventid=1002", "enlace in extras");

const e2 = gdacsEntities[1];
assertEq(e2.severity.level, SeverityLevel.MODERATE, "GREEN → moderada");

// Test with empty array
assertEq(normalizeGDACSAlerts([]).length, 0, "empty array → 0 entities");
assertEq(normalizeGDACSAlerts(null).length, 0, "null → 0 entities");
assertEq(normalizeGDACSAlerts("not-array").length, 0, "string → 0 entities");

// Test with missing fields
const incomplete = normalizeGDACSAlerts([{ id: "test" }]);
assertEq(incomplete.length, 1, "incomplete alert: 1 entity created");
assertEq(incomplete[0].title, "", "missing titulo → empty string");
assertEq(incomplete[0].coords, null, "missing lat/lon → null coords");
assertEq(incomplete[0].country, "", "missing pais → empty string");
assertEq(incomplete[0].severity.level, SeverityLevel.UNKNOWN, "missing severidad → unknown");

// =========================================================================
// 7. NASA FIRMS DETECTION NORMALIZATION
// =========================================================================
section("normalizeFIRMSDetections");

const firmsRaw = {
  total: 2,
  detecciones: [
    {
      id: "VIIRS-2026-04-30-40.4168-3.7038",
      satellite: "VIIRS SNPP",
      latitud: 40.4168,
      longitud: -3.7038,
      brillo: 320.5,
      confianza: "high",
      acq_date: "2026-04-30",
      acq_time: "1307",
      frp: 45.2,
      pais: "España",
    },
    {
      id: "VIIRS-2026-04-30-37.1700-3.6000",
      satellite: "VIIRS SNPP",
      lat: 37.17,
      lon: -3.60,
      brightness: 280.0,
      confidence: "nominal",
      acq_date: "2026-04-30",
      country: "España",
    },
  ],
};

const firmsEntities = normalizeFIRMSDetections(firmsRaw);
assertEq(firmsEntities.length, 2, "FIRMS: 2 entities created");

const f1 = firmsEntities[0];
assertEq(f1.entityType, EntityType.DETECCION, "entity type = DETECCION");
assertEq(f1.extras.satellite, "VIIRS SNPP", "satellite");
assertEq(f1.extras.brightness, 320.5, "brillo → brightness");
assertEq(f1.extras.confidence, "high", "confianza → confidence");
assertEq(f1.extras.frp, 45.2, "frp");
assertEq(f1.extras.acqDate, "2026-04-30", "acq_date");
assertEq(f1.country, "España", "pais → country");

const f2 = firmsEntities[1];
assertEq(f2.extras.brightness, 280.0, "brightness field (English) → brightness");
assertEq(f2.coords.lat, 37.17, "lat field (English) → coords");

// Test empty/invalid
assertEq(normalizeFIRMSDetections(null).length, 0, "null → 0");
assertEq(normalizeFIRMSDetections({}).length, 0, "no detecciones → 0");
assertEq(normalizeFIRMSDetections({ detecciones: "not-array" }).length, 0, "string detecciones → 0");

// =========================================================================
// 8. CLIMA ALERT NORMALIZATION
// =========================================================================
section("normalizeClimaAlerts");

const climaRaw = {
  total: 2,
  alertas: [
    {
      id: "om-heat-2026-04-30T13:00",
      tipo: "calor",
      nivel: "naranja",
      titulo: "Temperatura extrema: 40°C",
      descripcion: "Riesgo alto para la salud.",
      region: "España",
      fecha: "2026-04-30T13:00",
      fuente: "Open-Meteo",
    },
    {
      id: "aemet-123",
      tipo: "viento",
      nivel: "rojo",
      titulo: "Aviso de viento",
      fuente: "AEMET",
    },
  ],
  fuente: "Open-Meteo (fallback)",
  fallback_activado: true,
};

const climaEntities = normalizeClimaAlerts(climaRaw);
assertEq(climaEntities.length, 2, "Clima: 2 entities created");

const c1 = climaEntities[0];
assertEq(c1.entityType, EntityType.WEATHER, "entity type = WEATHER");
assertEq(c1.type.label, "Ola de calor", "type label");
assertEq(c1.severity.level, SeverityLevel.HIGH, "naranja → alta");
assertEq(c1.severity.raw, "naranja", "raw nivel preserved");
assertEq(c1.title, "Temperatura extrema: 40°C", "title");
assertEq(c1.source, "Open-Meteo", "source");

const c2 = climaEntities[1];
assertEq(c2.severity.level, SeverityLevel.CRITICAL, "rojo → critica");

// Clima alerts have no coordinates
assertEq(c1.coords, null, "clima: no coords");

// Test empty
assertEq(normalizeClimaAlerts(null).length, 0, "null → 0");
assertEq(normalizeClimaAlerts({}).length, 0, "no alertas → 0");

// =========================================================================
// 9. NECESIDAD NORMALIZATION
// =========================================================================
section("normalizeNecesidades");

const necesidadesRaw = [
  {
    id: 1,
    titulo: "Agua para barrio",
    tipo: "agua",
    descripcion: "Falta de agua potable",
    direccion: "Calle Mayor 3, Valencia",
    latitud: 39.47,
    longitud: -0.38,
    prioridad: "alta",
    estado: "abierta",
    creado_en: "2026-04-30T10:00:00",
    categoria_etiqueta: "💧 Agua",
  },
  {
    id: 2,
    tipo: "otros",
    latitud: 40.42,
    longitud: -3.70,
    prioridad: "baja",
    estado: "cubierta",
    creado_en: "2026-04-29T08:00:00",
  },
];

const necesidadesEntities = normalizeNecesidades(necesidadesRaw);
assertEq(necesidadesEntities.length, 2, "Necesidades: 2 entities");

const n1 = necesidadesEntities[0];
assertEq(n1.entityType, EntityType.NEED, "entity type = NEED");
assertEq(n1.title, "Agua para barrio", "title");
assertEq(n1.extras.prioridad, "alta", "prioridad in extras");
assertEq(n1.extras.categoriaEtiqueta, "💧 Agua", "categoria_etiqueta in extras");
assertEq(n1.extras.direccion, "Calle Mayor 3, Valencia", "direccion in extras");
assertEq(n1.status, "abierta", "estado → status");

const n2 = necesidadesEntities[1];
assertEq(n2.title, "", "missing titulo → empty");
assertEq(n2.extras.categoriaEtiqueta, null, "missing categoria_etiqueta → null");

// =========================================================================
// 10. DONACIÓN NORMALIZATION
// =========================================================================
section("normalizeDonaciones");

const donacionesRaw = [
  {
    id: 1,
    tipo: "recursos",
    recurso: "Agua",
    cantidad: "50 botellas",
    descripcion: "Agua potable",
    contacto: "Juan - 600123456",
    estado: "activa",
    creado_en: "2026-04-30T10:00:00",
    latitud: 39.47,
    longitud: -0.38,
  },
];

const donacionesEntities = normalizeDonaciones(donacionesRaw);
assertEq(donacionesEntities.length, 1, "Donaciones: 1 entity");

const d1 = donacionesEntities[0];
assertEq(d1.entityType, EntityType.RESOURCE, "entity type = RESOURCE");
assertEq(d1.extras.recurso, "Agua", "recurso in extras");
assertEq(d1.extras.cantidad, "50 botellas", "cantidad in extras");
assertEq(d1.extras.contacto, "Juan - 600123456", "contacto in extras");
assertEq(d1.status, "activa", "estado → status");

// =========================================================================
// 11. INCOMPLETE DATA SAFETY
// =========================================================================
section("incomplete data safety");

// Alert with absolutely minimal data
const minimal = normalizeGDACSAlerts([{ id: "x" }]);
assertEq(minimal.length, 1, "minimal alert: entity created");
assertEq(minimal[0].title, "", "no title → empty");
assertEq(minimal[0].description, "", "no description → empty");
assertEq(minimal[0].coords, null, "no coords → null");
assertEq(minimal[0].country, "", "no country → empty");
assertEq(minimal[0].timestamp, null, "no timestamp → null");
assertEq(minimal[0].severity.level, SeverityLevel.UNKNOWN, "no severity → unknown");

// Detection with null fields
const nullDetection = normalizeFIRMSDetections({
  detecciones: [{ id: "x", satellite: null, lat: null, lon: null }],
});
assertEq(nullDetection.length, 1, "null detection: entity created");
assertEq(nullDetection[0].coords, null, "null lat/lon → null coords");

// Necesidad with invalid coords
const badCoords = normalizeNecesidades([{ id: 1, tipo: "agua", latitud: 999, longitud: 999 }]);
assertEq(badCoords[0].coords, null, "invalid coords → null");

// Empty strings everywhere
const emptyStrings = normalizeGDACSAlerts([{
  id: "", tipo: "", titulo: "", descripcion: "", severidad: "", pais: "",
}]);
assertEq(emptyStrings.length, 1, "empty strings: entity created");
assertEq(emptyStrings[0].type.label, "Desconocido", "empty tipo → Desconocido");

// =========================================================================
// 12. EDGE CASES
// =========================================================================
section("edge cases");

// Array with null elements
const withNulls = normalizeGDACSAlerts([null, undefined, { id: "ok" }]);
assertEq(withNulls.length, 1, "null elements filtered out");

// Duplicate IDs
const duplicates = normalizeGDACSAlerts([
  { id: "dup", tipo: "terremoto" },
  { id: "dup", tipo: "incendio" },
]);
assertEq(duplicates.length, 2, "duplicates preserved (dedup is backend concern)");

// Very long strings
const longTitle = normalizeGDACSAlerts([{ id: "x", titulo: "A".repeat(500) }]);
assertEq(longTitle[0].title.length, 500, "long title preserved");

// HTML in title (should be stripped)
const htmlTitle = normalizeGDACSAlerts([{ id: "x", titulo: "<b>Bold</b> alert" }]);
assertEq(htmlTitle[0].title, "Bold alert", "HTML stripped from title");

// =========================================================================
// SUMMARY
// =========================================================================
console.log(`\n${"=".repeat(50)}`);
console.log(`Results: ${passed} passed, ${failed} failed`);
console.log(`${"=".repeat(50)}`);

process.exit(failed > 0 ? 1 : 0);
