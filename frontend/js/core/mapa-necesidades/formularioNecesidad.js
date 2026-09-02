// frontend/js/core/mapa-necesidades/formularioNecesidad.js

import { crearNecesidad } from "./necesidadesApi.js";
import { buscarDireccion, direccionInversa } from "./geocodificacion.js";

/**
 * Controlador para el formulario simplificado de "Reportar necesidad" (rediseño G1).
 * Rediseño del MVP: el ciudadano solo tiene que elegir una de las 8 categorías
 * cerradas (botones con emoji) y decir dónde. El título se autogenera en el backend.
 */
export class NeedFormController {
    constructor(container, onSubmit) {
        this.container = typeof container === "string" ? document.querySelector(container) : container;
        this.onSubmit = onSubmit;
        this.formElement = null;
        this.tipoSeleccionado = null;
        
        // Coordenadas ya confirmadas por GPS o clic en el mapa.
        this.coordenadasConfirmadas = null;
        
        this.init();
    }

    init() {
        if (!this.container) return;
        this.formElement = this.container.tagName === "FORM" ? this.container : this.container.querySelector("form");
        
        this.setupCategorias();
        this.setupDireccion();
        this.setupGeolocation();
        this.setupClicEnMapa();
        this.bindEvents();
    }

    /**
     * Convierte el grupo de botones de categoría cerrados (.anr-categoria-btn)
     * en un selector exclusivo. Sustituye al antiguo <select id="select-tipo">.
     */
    setupCategorias() {
        const botones = this.formElement.querySelectorAll(".anr-categoria-btn");
        botones.forEach((btn) => {
            btn.addEventListener("click", () => {
                // Deseleccionar los demás botones
                botones.forEach((b) => {
                    b.classList.remove("is-selected");
                    b.setAttribute("aria-pressed", "false");
                });
                
                // Seleccionar el actual
                btn.classList.add("is-selected");
                btn.setAttribute("aria-pressed", "true");
                this.tipoSeleccionado = btn.dataset.tipo;
            });
        });
    }

    /**
     * Si la persona edita la dirección a mano, invalidamos las coordenadas
     * obtenidas por GPS o clic en el mapa, forzando una geocodificación del
     * nuevo texto al enviar.
     */
    setupDireccion() {
        const direccionInput = this.formElement.querySelector("#input-direccion");
        if (!direccionInput) return;
        direccionInput.addEventListener("input", () => {
            this.coordenadasConfirmadas = null;
        });
    }

    /**
     * Obtiene la ubicación actual del dispositivo usando la API de Geolocalización nativa.
     */
    setupGeolocation() {
        const gpsBtn = this.formElement.querySelector("#btn-usar-gps");
        if (!gpsBtn) return;
        gpsBtn.addEventListener("click", async () => {
            gpsBtn.disabled = true;
            const textoOriginal = gpsBtn.textContent;
            gpsBtn.textContent = "⏳ Obteniendo ubicación...";
            
            navigator.geolocation.getCurrentPosition(
                async (pos) => {
                    const { latitude, longitude } = pos.coords;
                    await this.confirmarUbicacion(latitude, longitude);
                    gpsBtn.disabled = false;
                    gpsBtn.textContent = textoOriginal;
                },
                (err) => {
                    console.warn("Fallo en la geolocalización nativa del dispositivo:", err);
                    alert("No se pudo obtener el GPS automáticamente. Haz clic directo en el mapa o escribe la dirección.");
                    gpsBtn.disabled = false;
                    gpsBtn.textContent = textoOriginal;
                }
            );
        });
    }

    /**
     * Escucha eventos globales de clics en el mapa (disparados por mapaNecesidades.js)
     * para rellenar la ubicación de la necesidad.
     */
    setupClicEnMapa() {
        document.addEventListener("anr:ubicacion-seleccionada", async (evento) => {
            const { lat, lng } = evento.detail || {};
            if (typeof lat === "number" && typeof lng === "number") {
                await this.confirmarUbicacion(lat, lng);
            }
        });
    }

    /**
     * Almacena las coordenadas confirmadas del mapa/GPS y rellena
     * la dirección legible con geocodificación inversa.
     */
    async confirmarUbicacion(lat, lng) {
        this.coordenadasConfirmadas = { lat, lng };
        const direccionInput = this.formElement.querySelector("#input-direccion");
        if (direccionInput) {
            direccionInput.placeholder = "⏳ Obteniendo dirección legible...";
            const legible = await direccionInversa(lat, lng);
            direccionInput.value = legible || `${lat.toFixed(5)}, ${lng.toFixed(5)}`;
            direccionInput.placeholder = "Dirección de la necesidad";
        }
    }

    bindEvents() {
        this.formElement.addEventListener("submit", async (e) => {
            e.preventDefault();
            const submitBtn = this.formElement.querySelector("button[type='submit']");
            const hint = this.formElement.querySelector(".anr-hint");
            
            if (!this.tipoSeleccionado) {
                alert("Por favor, selecciona una categoría.");
                return;
            }

            const direccionInput = this.formElement.querySelector("#input-direccion");
            const direccionTexto = direccionInput?.value.trim() || "";
            let lat = null;
            let lng = null;

            submitBtn.disabled = true;
            if (hint) hint.textContent = "Procesando dirección geoespacial...";

            try {
                if (this.coordenadasConfirmadas) {
                    lat = this.coordenadasConfirmadas.lat;
                    lng = this.coordenadasConfirmadas.lng;
                } else {
                    if (!direccionTexto) {
                        throw new Error("Debes proporcionar una dirección de texto o ubicar un punto en el mapa.");
                    }
                    const coords = await buscarDireccion(direccionTexto);
                    if (!coords) {
                        throw new Error("No pudimos encontrar esa dirección. Intenta marcar el punto directamente en el mapa.");
                    }
                    lat = coords.lat;
                    lng = coords.lng;
                }

                // Validación robusta de límites geográficos requeridos en schemas.py (Pydantic)
                if (lat < -90 || lat > 90 || lng < -180 || lng > 180) {
                    throw new Error("Las coordenadas geográficas están fuera del rango planetario válido.");
                }

                const payload = {
                    tipo: this.tipoSeleccionado,
                    latitud: lat,
                    longitud: lng,
                    direccion: direccionTexto,
                    descripcion: this.formElement.querySelector("#input-descripcion")?.value || "",
                    prioridad: this.formElement.querySelector("#select-prioridad")?.value || "media"
                };

                const nuevaNecesidad = await crearNecesidad(payload);
                
                this.reset();
                if (this.onSubmit) this.onSubmit(nuevaNecesidad);
                alert("¡Necesidad reportada con éxito!");

            } catch (error) {
                alert(error.message);
            } finally {
                submitBtn.disabled = false;
                if (hint) hint.textContent = "Selecciona en el mapa o usa GPS para autocompletar.";
            }
        });
    }

    reset() {
        if (this.formElement) this.formElement.reset();
        this.coordenadasConfirmadas = null;
        this.tipoSeleccionado = null;
        const botones = this.formElement.querySelectorAll(".anr-categoria-btn");
        botones.forEach((b) => {
            b.classList.remove("is-selected");
            b.setAttribute("aria-pressed", "false");
        });
    }
}