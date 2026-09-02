// Donations list and form — Team 3 frontend (G3 Ayudas).
import { getDonations, markDonationAsDelivered, postDonation } from "./donacionesApi.js";

const list           = document.getElementById("lista-donaciones");
const statusEl       = document.getElementById("estado-lista");
const form           = document.getElementById("form-donacion");
const filterType     = document.getElementById("filtro-tipo");
const filterOrder    = document.getElementById("filtro-orden");
const filterCategory = document.getElementById("filtro-categoria");
const campoDni       = document.getElementById("campo-dni");
const dniInput       = document.getElementById("dni");

function updateDniVisibility(tipoValue) {
  if (campoDni) {
    if (tipoValue === "tiempo") {
      campoDni.style.display = "block";
      dniInput.setAttribute("required", "true");
    } else {
      campoDni.style.display = "none";
      dniInput.removeAttribute("required");
      dniInput.value = "";
    }
  }
}

function initDropdowns() {
  document.querySelectorAll(".nexo-select").forEach(sel => {
    const trigger = sel.querySelector(".nexo-select__trigger");
    const menu    = sel.querySelector(".nexo-select__menu");
    const label   = sel.querySelector(".nexo-select__label");

    trigger.addEventListener("click", (e) => {
      e.stopPropagation();
      const isOpen = sel.classList.contains("nexo-select--abierto");
      document.querySelectorAll(".nexo-select.nexo-select--abierto").forEach(s => s.classList.remove("nexo-select--abierto"));
      if (!isOpen) sel.classList.add("nexo-select--abierto");
    });

    const isFormDropdown = form.contains(sel);

    menu.querySelectorAll("li").forEach(li => {
      li.addEventListener("click", () => {
        sel.dataset.value = li.dataset.value;
        label.textContent = li.textContent;
        label.classList.remove("nexo-select__label--placeholder");
        menu.querySelectorAll("li").forEach(l => l.classList.remove("nexo-select__opcion--activa"));
        li.classList.add("nexo-select__opcion--activa");
        sel.classList.remove("nexo-select--abierto");

        // Si cambia el tipo en el formulario, actualizamos la visibilidad del DNI
        if (sel.id === "tipo") {
          updateDniVisibility(li.dataset.value);
        }

        if (!isFormDropdown) loadDonations();
      });
    });
  });

  document.addEventListener("click", () => {
    document.querySelectorAll(".nexo-select.nexo-select--abierto").forEach(s => s.classList.remove("nexo-select--abierto"));
  });
}

// Iconos SVG indexados por nombre exacto de categoría
const ICONS = {
  "Agua": `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 2C12 2 5 9.5 5 14a7 7 0 0 0 14 0C19 9.5 12 2 12 2z"/></svg>`,
  "Comida": `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="7" width="18" height="13" rx="2"/><path d="M3 11h18"/><path d="M8 7V4"/><path d="M16 7V4"/></svg>`,
  "Medicamentos": `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="4" y="3" width="16" height="18" rx="2"/><path d="M9 9h6"/><path d="M9 13h6"/><path d="M8 3v3h8V3"/></svg>`,
  "Transporte": `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="1" y="8" width="22" height="10" rx="2"/><circle cx="7" cy="18" r="2"/><circle cx="17" cy="18" r="2"/></svg>`,
  "Apoyo logistico": `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>`
};

function getIcon(category) {
  return ICONS[category] || `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 8H3l1.5 11h15z"/><path d="M3 8l2-4h14l2 4"/></svg>`;
}

function renderCard(d) {
  const status   = d.status || d.estado || "abierta";
  const isActive = status === "abierta" || status === "activa";
  const cat = d.category || d.recurso || "General";
  return `
    <div class="donacion-card" id="donacion-${d.id}">
      <div class="donacion-led donacion-led--${status}">
        <span class="donacion-led__punto"></span>
        ${isActive ? "Activa" : "Completada"}
      </div>
      <div class="donacion-card__icono">${getIcon(cat)}</div>
      <div class="donacion-card__contenido">
        <h3>${cat} (${d.type || d.tipo || 'Ayuda'})</h3>
        ${d.descripcion ? `<p class="donacion-card__desc">${d.descripcion}</p>` : ""}
        ${d.dni ? `<p><strong>DNI:</strong> ${d.dni}</p>` : ""}
        <p>Contacto: ${d.contacto || 'No especificado'}</p>
        ${isActive ? `<button class="donacion-card__btn" data-id="${d.id}">Marcar como entregada</button>` : ""}
      </div>
    </div>
  `;
}

list.addEventListener("click", async (e) => {
  const btn = e.target.closest(".donacion-card__btn");
  if (btn) await markAsDelivered(Number(btn.dataset.id));
});

async function markAsDelivered(id) {
  try {
    await markDonationAsDelivered(id);
    await loadDonations();
  } catch {
    showStatus("No se pudo actualizar el estado de la ayuda.");
  }
}

function showStatus(text) {
  statusEl.textContent = text;
  statusEl.hidden = false;
}

function hideStatus() {
  statusEl.hidden = true;
}

async function loadDonations() {
  const type     = filterType.dataset.value     || null;
  const order    = filterOrder.dataset.value    || "recientes";
  const category = filterCategory.dataset.value || null;

  list.innerHTML = "";
  showStatus("Cargando...");

  let data;
  try {
    data = await getDonations(type);
  } catch {
    showStatus("No se pudieron cargar las ayudas. Inténtalo de nuevo más tarde.");
    return;
  }

  if (category) data = data.filter(d => (d.category || d.recurso) === category);

  data.sort((a, b) => {
    const ta = new Date(a.creado_en || 0).getTime();
    const tb = new Date(b.creado_en || 0).getTime();
    return order === "antiguos" ? ta - tb : tb - ta;
  });

  hideStatus();

  if (data.length === 0) {
    showStatus("No hay ayudas disponibles para los filtros seleccionados.");
    return;
  }

  list.innerHTML = data.map(renderCard).join("");
}

function resetFormDropdowns() {
  const typeEl = document.getElementById("tipo");
  typeEl.dataset.value = "recursos";
  typeEl.querySelector(".nexo-select__label").textContent = "Recursos";
  typeEl.querySelectorAll("li").forEach((li, i) => li.classList.toggle("nexo-select__opcion--activa", i === 0));

  updateDniVisibility("recursos");

  const resourceEl = document.getElementById("recurso");
  resourceEl.dataset.value = "";
  const resourceLabel = resourceEl.querySelector(".nexo-select__label");
  resourceLabel.textContent = "Selecciona una categoría";
  resourceLabel.classList.add("nexo-select__label--placeholder");
  resourceEl.querySelectorAll("li").forEach(li => li.classList.remove("nexo-select__opcion--activa"));
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const resourceEl = document.getElementById("recurso");
  if (!resourceEl.dataset.value) {
    const trigger = resourceEl.querySelector(".nexo-select__trigger");
    trigger.classList.add("nexo-select__trigger--error");
    setTimeout(() => trigger.classList.remove("nexo-select__trigger--error"), 1500);
    return;
  }

  const tipoVal = document.getElementById("tipo").dataset.value;

  const btn = form.querySelector("button[type=submit]");
  btn.disabled = true;
  btn.textContent = "Publicando...";

  // Payload ajustado a las claves que espera FastAPI/Pydantic
  const payload = {
    tipo: tipoVal,
    recurso: resourceEl.dataset.value,
    descripcion: form.querySelector("#descripcion").value.trim(),
    contacto: form.querySelector("#contacto").value.trim(),
    dni: (tipoVal === "tiempo") ? dniInput.value.trim() : null
  };

  try {
    await postDonation(payload);
    form.reset();
    resetFormDropdowns();
    document.getElementById("contador-desc").textContent = "0 / 1000";
    await loadDonations();
  } catch (error) {
    console.error("Error al publicar:", error);
    alert("No se pudo publicar la ayuda. Verifica la conexión.");
  } finally {
    btn.disabled = false;
    btn.textContent = "Publicar Ayuda";
  }
});

const descriptionEl = form.querySelector("#descripcion");
const counterEl     = document.getElementById("contador-desc");
descriptionEl.addEventListener("input", () => {
  counterEl.textContent = `${descriptionEl.value.length} / 1000`;
});

// Inicialización
updateDniVisibility("recursos");
initDropdowns();
loadDonations();
