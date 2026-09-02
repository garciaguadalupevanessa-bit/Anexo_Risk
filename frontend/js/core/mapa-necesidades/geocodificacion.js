// frontend/js/core/mapa-necesidades/geocodificacion.js

const NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org";

/**
 * Busca una dirección escrita a mano y devuelve su mejor coincidencia.
 * @param {string} texto - p. ej. "Calle Mayor 3, Valencia"
 * @returns {Promise<{lat: number, lng: number, direccion: string}|null>}
 * Retorna null si no hay coincidencia (no es un error, solo "no encontrado").
 * @throws {Error} si no se puede conectar con el servicio (red caída, etc.)
 */
export async function buscarDireccion(texto) {
    const consulta = (texto || "").trim();
    if (!consulta) return null;

    const url = `${NOMINATIM_BASE_URL}/search?format=json&limit=1&q=${encodeURIComponent(consulta)}`;
    let response;
    try {
        response = await fetch(url, { headers: { Accept: "application/json" } });
    } catch (_err) {
        throw new Error("No se pudo contactar con el buscador de direcciones.");
    }

    if (!response.ok) {
        throw new Error("El buscador de direcciones no respondió correctamente.");
    }

    const resultados = await response.json();
    if (!Array.isArray(resultados) || resultados.length === 0) {
        return null;
    }

    // Tomamos la primera coincidencia (la más relevante)
    const { lat, lon, display_name: direccion } = resultados;
    return { 
        lat: parseFloat(lat), 
        lng: parseFloat(lon), 
        direccion 
    };
}

/**
 * Traduce unas coordenadas a una dirección legible (geocodificación inversa).
 * @param {number} lat
 * @param {number} lng
 * @returns {Promise<string|null>} la dirección legible, o null si falla.
 */
export async function direccionInversa(lat, lng) {
    const url = `${NOMINATIM_BASE_URL}/reverse?format=json&lat=${lat}&lon=${lng}`;
    try {
        const response = await fetch(url, { headers: { Accept: "application/json" } });
        if (!response.ok) return null;
        const resultado = await response.json();
        return resultado?.display_name || null;
    } catch (_err) {
        // Fallo silencioso a propósito: si la red falla o Nominatim no responde,
        // no bloqueamos al usuario. Es mejor tener lat/lng puras que romper la app.
        return null; 
    }
}
