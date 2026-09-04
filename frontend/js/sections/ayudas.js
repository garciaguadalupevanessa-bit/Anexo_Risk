// Ayudas section — initDonaciones, loadNecesidadesParaAyuda, loadDonaciones, selectNeed
import { API_BASE, apiGet, escapeHtml } from "../shared/config.js";

export function initDonaciones() {
  const form = document.getElementById("form-donacion");
  const tipoEl = document.getElementById("don-tipo");
  const campoDni = document.getElementById("campo-dni");
  const dniInput = document.getElementById("dni");
  const descEl = document.getElementById("don-descripcion");
  const counterEl = document.getElementById("contador-desc");
  const listEl = document.getElementById("lista-donaciones");
  const needsListEl = document.getElementById("lista-necesidades-ayuda");
  const submitBtn = document.getElementById("btn-publicar-ayuda");
  const necesidadInfo = document.getElementById("don-necesidad-info");

  let selectedNeed = null;

  if (tipoEl) {
    tipoEl.addEventListener("change", () => {
      if (tipoEl.value === "tiempo") {
        campoDni.style.display = "block";
        dniInput.setAttribute("required", "true");
      } else {
        campoDni.style.display = "none";
        dniInput.removeAttribute("required");
        dniInput.value = "";
      }
    });
  }

  if (descEl && counterEl) {
    descEl.addEventListener("input", () => {
      counterEl.textContent = `${descEl.value.length} / 1000`;
    });
  }

  function selectNeed(need) {
    selectedNeed = need;
    document.getElementById("don-necesidad-id").value = need.id;
    if (necesidadInfo) {
      necesidadInfo.style.display = "block";
      necesidadInfo.textContent = `✓ Ayudando con: ${need.titulo || need.tipo} — ${need.direccion || (need.latitud && need.longitud ? `${need.latitud}, ${need.longitud}` : "sin ubicación")}`;
    }
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = `Ofrecer ayuda para esta necesidad`;
    }
    document.querySelectorAll(".need-card").forEach(c => c.classList.remove("is-selected"));
  }

  async function loadNecesidadesParaAyuda() {
    if (!needsListEl) return;
    needsListEl.innerHTML = '<div class="state-loading"><p>Cargando necesidades...</p></div>';
    try {
      const data = await apiGet("/api/necesidades?estado=abierta");
      window._lastNeeds = data || [];
      if (!data || !data.length) {
        needsListEl.innerHTML = '<div class="state-empty"><p>No hay necesidades activas. ¡Buenas noticias!</p></div>';
        return;
      }
      const ICONS = {
        agua: "💧", alimentos: "🍞", parafarmacia: "💊", ropa: "👕",
        higiene: "🧴", refugio: "🏠", transporte: "🚗", otros: "📦",
      };
      needsListEl.innerHTML = data.map(n => {
        const tipo = n.tipo || n.categoria || "otros";
        const isSelected = selectedNeed && selectedNeed.id === n.id;
        return `
          <div class="need-card ${isSelected ? "is-selected" : ""}" data-need-id="${escapeHtml(String(n.id))}" style="cursor:pointer; padding: 12px; border: 1px solid ${isSelected ? "var(--cyan)" : "var(--border)"}; border-radius: 8px; margin-bottom: 8px; background: ${isSelected ? "var(--cyan-subtle)" : "transparent"};">
            <div style="display: flex; align-items: center; gap: 8px;">
              <span style="font-size: 1.4rem;">${ICONS[tipo] || "📦"}</span>
              <div style="flex: 1;">
                <div style="font-weight: 600;">${escapeHtml(n.titulo || tipo)}</div>
                <div style="font-size: 0.8rem; color: var(--text-muted);">${escapeHtml(n.direccion || (n.latitud && n.longitud ? `${n.latitud}, ${n.longitud}` : "Sin ubicación"))}</div>
                ${n.descripcion ? `<div style="font-size: 0.85rem; margin-top: 4px;">${escapeHtml(n.descripcion)}</div>` : ""}
              </div>
              <button type="button" class="btn btn--primary btn--sm" data-need-select="${escapeHtml(String(n.id))}">Elegir</button>
            </div>
          </div>`;
      }).join("");

      needsListEl.querySelectorAll("[data-need-select]").forEach(btn => {
        btn.addEventListener("click", (e) => {
          e.stopPropagation();
          const need = data.find(n => n.id === parseInt(btn.dataset.needSelect));
          if (need) selectNeed(need);
        });
      });
    } catch {
      needsListEl.innerHTML = '<div class="state-error"><p>No se pudieron cargar las necesidades.</p></div>';
    }
  }

  async function loadDonaciones() {
    if (!listEl) return;
    listEl.innerHTML = '<div class="state-loading"><p>Cargando ayudas...</p></div>';
    try {
      const data = await apiGet("/api/donaciones");
      if (!data || !data.length) {
        listEl.innerHTML = '<div class="state-empty"><p>No hay ayudas publicadas todavía.</p></div>';
        return;
      }
      const ICONS = {
        "Comida": "🍞", "Medicamentos": "💊", "Transporte": "🚗",
        "Alojamiento temporal": "🏠", "Apoyo logistico": "👥", "Otros": "📦",
      };
      listEl.innerHTML = data.map(d => {
        const status = d.status || d.estado || "abierta";
        const isActive = status === "abierta" || status === "activa";
        return `
          <div class="donation-card">
            <div class="donation-card__icon"><span style="font-size:1.2rem;">${ICONS[d.recurso || d.category] || "📦"}</span></div>
            <div class="donation-card__body">
              <div class="donation-card__title">${escapeHtml(d.recurso || d.category || "General")} — ${escapeHtml(d.tipo || d.type || "Ayuda")}</div>
              ${d.descripcion ? `<div class="donation-card__desc">${escapeHtml(d.descripcion)}</div>` : ""}
              <div class="donation-card__meta">Contacto: ${escapeHtml(d.contacto || "No especificado")}${d.dni ? ` · DNI: ${escapeHtml(d.dni)}` : ""}</div>
            </div>
            <span class="donation-card__status donation-card__status--${isActive ? "active" : "done"}">${isActive ? "Activa" : "Completada"}</span>
          </div>`;
      }).join("");
    } catch {
      listEl.innerHTML = '<div class="state-error"><p>No se pudieron cargar las ayudas.</p></div>';
    }
  }

  if (form) {
    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!selectedNeed) { alert("Selecciona una necesidad para ayudar."); return; }
      const recurso = document.getElementById("don-recurso").value;
      if (!recurso) { alert("Selecciona una categoría."); return; }
      const payload = {
        tipo: tipoEl.value,
        recurso,
        descripcion: descEl.value.trim(),
        contacto: document.getElementById("don-contacto").value.trim(),
        dni: tipoEl.value === "tiempo" ? dniInput.value.trim() : null,
        necesidad_id: selectedNeed.id,
      };
      submitBtn.disabled = true;
      submitBtn.textContent = "Enviando...";
      try {
        const resp = await fetch(`${API_BASE}/api/donaciones`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (!resp.ok) {
          const err = await resp.json().catch(() => ({}));
          throw new Error(err.detail || `Error ${resp.status}`);
        }
        form.reset();
        counterEl.textContent = "0 / 1000";
        campoDni.style.display = "none";
        selectedNeed = null;
        document.getElementById("don-necesidad-id").value = "";
        if (necesidadInfo) necesidadInfo.style.display = "none";
        submitBtn.textContent = "Selecciona una necesidad para ayudar";
        await Promise.all([loadNecesidadesParaAyuda(), loadDonaciones()]);
        if (typeof window.loadNecesidades === "function") await window.loadNecesidades();
      } catch (err) {
        console.error(err);
        alert("No se pudo publicar la ayuda: " + err.message);
      } finally {
        submitBtn.disabled = false;
      }
    });
  }

  loadDonaciones();
  loadNecesidadesParaAyuda();
  window.loadNecesidades = loadNecesidadesParaAyuda;
  window.loadAyudasSection = () => { loadNecesidadesParaAyuda(); loadDonaciones(); };
  window.selectNeedForAid = (id) => { loadNecesidadesParaAyuda().then(() => { const need = (window._lastNeeds || []).find(n => n.id === id); if (need) selectNeed(need); }); };
}
