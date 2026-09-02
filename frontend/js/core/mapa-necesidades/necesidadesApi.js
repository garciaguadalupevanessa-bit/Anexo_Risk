// frontend/js/core/mapa-necesidades/necesidadesApi.js

let NECESIDADES_BASE_URL = "/api/necesidades";

/**
 * Sobrescribe la URL base de la API. Pensado para scripts de prueba
 * manual (Node) o para desarrollo local si el backend corre en otro
 * puerto sin proxy configurado.
 * @param {string} baseUrl - p. ej. "http://localhost:8000/api/necesidades"
 */
export function configurarBaseUrl(baseUrl) {
    NECESIDADES_BASE_URL = baseUrl;
}

// 8 categorías cerradas del rediseño (antes eran 6 en el Sprint 1)
export const TIPOS_NECESIDAD = Object.freeze({
    AGUA: "agua",
    ALIMENTOS: "alimentos",
    PARAFARMACIA: "parafarmacia",
    ROPA: "ropa",
    HIGIENE: "higiene",
    REFUGIO: "refugio",
    TRANSPORTE: "transporte",
    OTROS: "otros",
});

// Etiqueta con emoji por categoría. El backend la envía en "categoria_etiqueta",
// pero este mapeo sirve para pintar los propios controles del formulario y filtros.
export const ETIQUETAS_TIPO_NECESIDAD = Object.freeze({
    [TIPOS_NECESIDAD.AGUA]: "💧 Agua",
    [TIPOS_NECESIDAD.ALIMENTOS]: "🍞 Alimentos",
    [TIPOS_NECESIDAD.PARAFARMACIA]: "💊 Parafarmacia",
    [TIPOS_NECESIDAD.ROPA]: "👕 Ropa",
    [TIPOS_NECESIDAD.HIGIENE]: "🧴 Higiene",
    [TIPOS_NECESIDAD.REFUGIO]: "🏠 Refugio",
    [TIPOS_NECESIDAD.TRANSPORTE]: "🚗 Transporte",
    [TIPOS_NECESIDAD.OTROS]: "📦 Otros",
});

export const PRIORIDADES_NECESIDAD = Object.freeze({
    BAJA: "baja",
    MEDIA: "media",
    ALTA: "alta",
    CRITICA: "critica",
});

// Ciclo de vida simplificado a un solo paso (abierta -> cubierta)
export const ESTADOS_NECESIDAD = Object.freeze({
    ABIERTA: "abierta",
    CUBIERTA: "cubierta",
});

/**
 * Error personalizado para poder distinguir en el código que consume
 * esta API entre "no encontrado" (404), "transición inválida" (409)
 * y errores inesperados (red, 500, JSON mal formado).
 */
export class NecesidadApiError extends Error {
    constructor(mensaje, status, detalle = null) {
        super(mensaje);
        this.name = "NecesidadApiError";
        this.status = status;
        this.detalle = detalle;
    }
}

/**
 * Construye un mensaje legible a partir del formato de error estándar
 * de FastAPI para fallos de validación de Pydantic (422):
 * { "detail": [ { "loc": [...], "msg": "...", "type": "..." } ] }
 */
function formatearDetalleValidacion(cuerpo) {
    if (!cuerpo || !Array.isArray(cuerpo.detail)) return null;
    return cuerpo.detail
        .map((err) => {
            const campo = Array.isArray(err.loc) ? err.loc.at(-1) : "campo";
            return `${campo}: ${err.msg}`;
        })
        .join("; ");
}

/**
 * Parsea la respuesta de fetch, lanzando NecesidadApiError si no es OK.
 * Maneja tanto el formato propio {error, detalle} para 404/409, como el 422 de FastAPI.
 */
async function parseRespuesta(response) {
    let cuerpo = null;
    try {
        cuerpo = await response.json();
    } catch (_err) {
        cuerpo = null;
    }

    if (!response.ok) {
        const detalleValidacion = formatearDetalleValidacion(cuerpo);
        const mensaje = cuerpo?.error || "Error en la petición a la API";
        const detalle = detalleValidacion || cuerpo?.detalle || null;
        throw new NecesidadApiError(mensaje, response.status, detalle);
    }
    return cuerpo;
}

/**
 * Construye la query string a partir de un objeto de filtros,
 * omitiendo claves undefined/null para no mandar "tipo=undefined".
 */
function construirQueryString(filtros = {}) {
    const params = new URLSearchParams();
    if (filtros.tipo != null) params.set("tipo", filtros.tipo);
    if (filtros.estado != null) params.set("estado", filtros.estado);
    const query = params.toString();
    return query ? `?${query}` : "";
}

/**
 * Obtiene las necesidades del mapa, con filtros opcionales por tipo y estado.
 */
export async function obtenerNecesidades(filtros = {}) {
    const url = `${NECESIDADES_BASE_URL}${construirQueryString(filtros)}`;
    const response = await fetch(url, {
        method: "GET",
        headers: { Accept: "application/json" },
    });
    return parseRespuesta(response);
}

/**
 * Obtiene una única necesidad por su id.
 */
export async function obtenerNecesidad(idNecesidad) {
    const response = await fetch(`${NECESIDADES_BASE_URL}/${idNecesidad}`, {
        method: "GET",
        headers: { Accept: "application/json" },
    });
    return parseRespuesta(response);
}

/**
 * Crea una nueva necesidad en el mapa.
 */
export async function crearNecesidad(datosNecesidad) {
    const response = await fetch(NECESIDADES_BASE_URL, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
        },
        body: JSON.stringify(datosNecesidad),
    });
    return parseRespuesta(response);
}

/**
 * Cambia el estado de una necesidad existente (abierta -> cubierta).
 */
export async function actualizarEstadoNecesidad(idNecesidad, nuevoEstado) {
    const response = await fetch(`${NECESIDADES_BASE_URL}/${idNecesidad}`, {
        method: "PATCH",
        headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
        },
        body: JSON.stringify({ estado: nuevoEstado }),
    });
    return parseRespuesta(response);
}