// Donations API calls.
// Llamadas a la API de donaciones.
// En local usa FastAPI en el puerto 8000. En producción, el HTML puede definir
// window.ANEXO_API_BASE = "" para usar rutas relativas detrás de un proxy.
const API_BASE = window.ANEXO_API_BASE ?? "http://127.0.0.1:8000";

/**
 * Obtiene el listado de donaciones/ayudas.
 * @param {string|null} type - Filtro opcional por tipo
 */
export async function getDonations(type = null) {
  const params = type ? `?tipo=${encodeURIComponent(type)}` : "";
  try {
    const resp = await fetch(`${API_BASE}/api/donaciones${params}`);
    if (!resp.ok) throw new Error(`GET /api/donaciones -> ${resp.status}`);
    return await resp.json();
  } catch (error) {
    console.warn("Error al conectar con la API, recurriendo a localStorage:", error);
    const localData = JSON.parse(localStorage.getItem("anr_donaciones") || "[]");
    if (type) {
      return localData.filter(d => d.tipo === type || d.type === type);
    }
    return localData;
  }
}

/**
 * Publica una nueva donación o ayuda.
 * @param {Object} data - Payload con los datos del formulario
 */
export async function postDonation(data) {
  try {
    const resp = await fetch(`${API_BASE}/api/donaciones`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!resp.ok) throw new Error(`POST /api/donaciones -> ${resp.status}`);
    return await resp.json();
  } catch (error) {
    console.warn("Guardando publicación en localStorage por fallo de conexión:", error);
    const localData = JSON.parse(localStorage.getItem("anr_donaciones") || "[]");
    const newEntry = {
      id: Date.now(),
      ...data,
      creado_en: new Date().toISOString(),
      estado: "activa"
    };
    localData.unshift(newEntry);
    localStorage.setItem("anr_donaciones", JSON.stringify(localData));
    return newEntry;
  }
}

/**
 * Actualiza el estado de una donación a "entregada".
 * @param {number|string} id - Identificador de la donación
 */
export async function markDonationAsDelivered(id) {
  try {
    const resp = await fetch(`${API_BASE}/api/donaciones/${id}/estado`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ estado: "entregada" }),
    });
    if (!resp.ok) throw new Error(`PATCH /api/donaciones/${id}/estado -> ${resp.status}`);
    return await resp.json();
  } catch (error) {
    console.warn("Actualizando estado en localStorage por fallo de conexión:", error);
    const localData = JSON.parse(localStorage.getItem("anr_donaciones") || "[]");
    const updated = localData.map(item => {
      if (item.id === id) {
        return { ...item, estado: "entregada", status: "completada" };
      }
      return item;
    });
    localStorage.setItem("anr_donaciones", JSON.stringify(updated));
    return { success: true };
  }
}
