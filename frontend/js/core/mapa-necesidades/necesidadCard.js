// frontend/js/core/mapa-necesidades/necesidadCard.js

import { actualizarEstadoNecesidad } from "./necesidadesApi.js";

/**
 * Componente para representar las tarjetas de necesidad individuales
 * en la lista lateral de la aplicación (rediseño G1).
 * 
 * Cumple con el ciclo de vida simplificado de un paso: abierta -> cubierta.
 */
export class NeedCardComponent {
    /**
     * @param {Object} needData - Datos de la necesidad provenientes del backend.
     * @param {Function} [onStatusChange] - Callback opcional que se ejecuta cuando
     * la necesidad se marca como cubierta (útil para que G4 actualice el mapa).
     */
    constructor(needData, onStatusChange) {
        this.data = needData;
        this.onStatusChange = onStatusChange;
        this.element = this.createDOMElement();
    }

    /**
     * Construye y retorna la estructura HTML estructurada del componente.
     */
    createDOMElement() {
        const card = document.createElement("article");
        const prioridad = (this.data.prioridad || "baja").toLowerCase();
        const tipo = (this.data.tipo || "otros").toLowerCase();
        const etiquetaCategoria = this.data.categoria_etiqueta || tipo;

        // Acuerdo 3: Clases semánticas basadas en variables.css de Vanessa
        card.className = `anr-card anr-card--${prioridad}`;
        
        const header = document.createElement("div");
        header.className = "anr-card__header";

        const title = document.createElement("h4");
        title.className = "anr-card__title";
        // Si no hay título manual, cae en la etiqueta de la categoría autogenerada
        title.textContent = this.data.titulo || etiquetaCategoria;

        const badge = document.createElement("span");
        badge.className = `anr-card__badge anr-card__badge--${prioridad}`;
        badge.textContent = prioridad;

        header.append(title, badge);

        const desc = document.createElement("p");
        desc.className = "anr-card__desc";
        desc.textContent = this.data.descripcion || "Sin descripción proporcionada.";

        const address = document.createElement("p");
        address.className = "anr-card__address";
        address.innerHTML = `📍 <span>${this.data.direccion || "Ubicación en coordenadas"}</span>`;

        const footer = document.createElement("div");
        footer.className = "anr-card__footer";

        const typeSlot = document.createElement("span");
        typeSlot.className = "anr-card__type";
        typeSlot.textContent = etiquetaCategoria;

        const statusSlot = document.createElement("div");
        statusSlot.className = "anr-card__estado-slot";

        footer.append(typeSlot, statusSlot);
        card.append(header, desc, address, footer);

        this.renderEstado(card);
        return card;
    }

    /**
     * Pinta de forma reactiva la sección del botón/estado.
     * Se separa en su propio método para actualizar la UI en el clic sin repintar toda la tarjeta.
     */
    renderEstado(card) {
        const slot = card.querySelector(".anr-card__estado-slot");
        if (!slot) return;
        slot.innerHTML = "";

        if (this.data.estado === "cubierta") {
            const check = document.createElement("span");
            check.className = "check-done";
            check.textContent = "✅ Cubierta";
            slot.appendChild(check);
        } else {
            const btn = document.createElement("button");
            btn.className = "btn-cover";
            btn.textContent = "Marcar cubierta";
            
            btn.addEventListener("click", async () => {
                btn.disabled = true;
                btn.textContent = "⏳...";
                try {
                    // Llamada PATCH a la API
                    const actualizada = await actualizarEstadoNecesidad(this.data.id, "cubierta");
                    this.data.estado = "cubierta";
                    
                    // Repintamos el slot de estado localmente de forma inmediata
                    this.renderEstado(card); 
                    
                    // Si el mapa (Juan) nos pasó un callback, le notificamos para que actualice su marcador
                    if (this.onStatusChange) {
                        this.onStatusChange(actualizada);
                    }
                } catch (err) {
                    alert("No se pudo actualizar el estado de la necesidad.");
                    btn.disabled = false;
                    btn.textContent = "Marcar cubierta";
                }
            });
            slot.appendChild(btn);
        }
    }

    /**
     * Retorna el nodo DOM para ser inyectado en el panel.
     */
    getNode() {
        return this.element;
    }

    // ==========================================================================
    // CUMPLIMIENTO DEL PUNTO 22 (Mobile-first, estados del sistema sin pantallas en blanco)
    // ==========================================================================

    static renderLoading() {
        const el = document.createElement("div");
        el.className = "anr-state anr-state--loading";
        el.innerHTML = "<p>⏳ Cargando necesidades en tiempo real...</p>";
        return el;
    }

    static renderEmpty() {
        const el = document.createElement("div");
        el.className = "anr-state anr-state--empty";
        el.innerHTML = "<p>🍃 No hay necesidades registradas en esta zona.</p>";
        return el;
    }

    static renderError(msg = "Fallo al conectar con el servidor.") {
        const el = document.createElement("div");
        el.className = "anr-state anr-state--error";
        el.innerHTML = `<p>⚠️ ${msg}</p>`;
        return el;
    }
}