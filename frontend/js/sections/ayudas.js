// Ayudas section — initDonaciones, loadNecesidadesParaAyuda, loadDonaciones, selectNeed, assignments
import { API_BASE, apiGet, escapeHtml } from "../shared/config.js";

export function initDonaciones() {
  const form = document.getElementById("form-donacion");
  const tipoEl = document.getElementById("don-tipo");
  const campoDni = document.getElementById("campo-dni");
  const dniInput = document.getElementById("dni");
  const descEl = document.getElementById("don-descripcion");
  const counterEl = document.getElementById("contador-desc");
  const listEl = document.getElementById("lista-assignaciones");
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
        needsListEl.innerHTML = '<div class="state-empty"><p>No hay necesidades activas.</p></div>';
        return;
      }
      const ICONS = {
        agua: "💧", alimentos: "🍞", parafarmacia: "💊", ropa: "👕",
        higiene: "🧴", refugio: "🏠", transporte: "🚗", otros: "📦",
      };
      needsListEl.innerHTML = data.map(n => {
        const tipo = n.tipo || n.categoria || "otros";
        const isSelected = selectedNeed && selectedNeed.id === n.id;
        const covered = n.covered_quantity || 0;
        const needed = n.quantity || 0;
        const pct = needed > 0 ? Math.min(Math.round((covered / needed) * 100), 100) : 0;
        return `
          <div class="need-card ${isSelected ? "is-selected" : ""}" data-need-id="${escapeHtml(String(n.id))}">
            <div class="need-card__header">
              <span class="need-card__type">${ICONS[tipo] || "📦"} ${escapeHtml(n.titulo || tipo)}</span>
              <span class="need-card__priority need-card__priority--${escapeHtml(n.prioridad || 'media')}">${escapeHtml(n.prioridad || "media")}</span>
            </div>
            <div class="need-card__address">📍 ${escapeHtml(n.direccion || (n.latitud && n.longitud ? `${n.latitud}, ${n.longitud}` : "Sin ubicación"))}</div>
            ${n.descripcion ? `<div class="need-card__desc">${escapeHtml(n.descripcion)}</div>` : ""}
            ${needed > 0 ? `
            <div class="need-card__progress" style="margin-top:var(--space-xs);">
              <div class="need-card__progress-bar">
                <div class="need-card__progress-fill" style="width:${pct}%;${pct >= 100 ? 'background:var(--success);' : ''}"></div>
              </div>
              <span class="need-card__progress-text">${covered}/${needed} cubiertos (${pct}%)</span>
            </div>` : ""}
            <div class="need-card__actions">
              <button type="button" class="btn btn--primary btn--sm" data-need-select="${escapeHtml(String(n.id))}">Elegir</button>
              <button type="button" class="btn btn--ghost btn--sm" data-assign-need="${escapeHtml(String(n.id))}" data-need-tipo="${escapeHtml(tipo)}" data-need-direccion="${escapeHtml(n.direccion || '')}">Asignar recurso</button>
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

      needsListEl.querySelectorAll("[data-assign-need]").forEach(btn => {
        btn.addEventListener("click", (e) => {
          e.stopPropagation();
          openAssignModal(parseInt(btn.dataset.assignNeed), btn.dataset.needTipo);
        });
      });
    } catch {
      needsListEl.innerHTML = '<div class="state-error"><p>No se pudieron cargar las necesidades.</p></div>';
    }
  }

  async function loadAssignments() {
    if (!listEl) return;
    listEl.innerHTML = '<div class="state-loading"><p>Cargando asignaciones...</p></div>';
    try {
      const data = await apiGet("/api/assignments");
      if (!data || !data.length) {
        listEl.innerHTML = '<div class="state-empty"><p>No hay asignaciones activas.</p></div>';
        return;
      }
      const STATUS_LABELS = { asignado: "Asignado", en_curso: "En curso", completado: "Completado", cancelado: "Cancelado" };
      listEl.innerHTML = data.map(a => `
        <div class="assignment-card assignment-card--${escapeHtml(a.status || 'asignado')}">
          <div class="assignment-card__header">
            <span class="assignment-card__status badge badge--${escapeHtml(a.status || 'asignado')}">${STATUS_LABELS[a.status] || a.status}</span>
            <span class="assignment-card__qty">${a.quantity_assigned} uds</span>
          </div>
          <div class="assignment-card__body">
            <div class="assignment-card__resource">${escapeHtml(a.resource_name || "Recurso")}</div>
            <div class="assignment-card__need">→ ${escapeHtml(a.need_tipo || "Necesidad")} ${a.need_id ? `#${a.need_id}` : ""}</div>
          </div>
          <div class="assignment-card__footer">
            <span class="assignment-card__org">${escapeHtml(a.organization_name || "")}</span>
            <span class="assignment-card__time">${formatTime(a.created_at)}</span>
          </div>
        </div>`).join("");
    } catch {
      listEl.innerHTML = '<div class="state-error"><p>No se pudieron cargar las asignaciones.</p></div>';
    }
  }

  async function loadDonaciones() {
    await loadAssignments();
  }

  // Assignment modal
  function openAssignModal(needId, needTipo) {
    const existing = document.getElementById("assign-modal");
    if (existing) existing.remove();

    const modal = document.createElement("div");
    modal.id = "assign-modal";
    modal.className = "modal-overlay";
    modal.setAttribute("role", "dialog");
    modal.setAttribute("aria-label", "Asignar recurso");
    modal.innerHTML = `
      <div class="modal">
        <div class="modal__header">
          <h3 class="modal__title">Asignar recurso a: ${escapeHtml(needTipo)}</h3>
          <button class="modal__close" aria-label="Cerrar">&times;</button>
        </div>
        <div class="modal__body">
          <div class="form-group">
            <label for="assign-resource">Recurso</label>
            <select id="assign-resource" class="form-select">
              <option value="">Cargando recursos...</option>
            </select>
          </div>
          <div class="form-group">
            <label for="assign-qty">Cantidad</label>
            <input id="assign-qty" class="form-input" type="number" min="1" value="1" />
          </div>
          <div id="assign-error" class="form-hint" style="color:var(--sev-critica);display:none;"></div>
        </div>
        <div class="modal__footer">
          <button class="btn btn--ghost" id="assign-cancel">Cancelar</button>
          <button class="btn btn--primary" id="assign-confirm">Asignar</button>
        </div>
      </div>`;

    document.body.appendChild(modal);
    modal.querySelector(".modal__close").addEventListener("click", () => modal.remove());
    modal.querySelector("#assign-cancel").addEventListener("click", () => modal.remove());
    modal.addEventListener("click", (e) => { if (e.target === modal) modal.remove(); });

    // Load resources
    apiGet("/api/recursos").then(resources => {
      const sel = modal.querySelector("#assign-resource");
      sel.innerHTML = resources.filter(r => (r.available_quantity || 0) > 0).map(r => `
        <option value="${r.id}" data-avail="${r.available_quantity}">${escapeHtml(r.nombre || r.recurso)} (${r.available_quantity} disp.)</option>
      `).join("") || '<option value="">Sin recursos disponibles</option>';
    }).catch(() => {});

    modal.querySelector("#assign-confirm").addEventListener("click", async () => {
      const resourceId = modal.querySelector("#assign-resource").value;
      const qty = parseInt(modal.querySelector("#assign-qty").value) || 1;
      const errorEl = modal.querySelector("#assign-error");

      if (!resourceId) {
        errorEl.textContent = "Selecciona un recurso";
        errorEl.style.display = "block";
        return;
      }

      try {
        const resp = await fetch(`${API_BASE}/api/assignments`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ need_id: needId, resource_id: parseInt(resourceId), quantity_assigned: qty }),
        });
        if (!resp.ok) {
          const err = await resp.json().catch(() => ({}));
          throw new Error(err.detail || `Error ${resp.status}`);
        }
        modal.remove();
        await Promise.all([loadNecesidadesParaAyuda(), loadAssignments()]);
      } catch (err) {
        errorEl.textContent = err.message;
        errorEl.style.display = "block";
      }
    });
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
        await Promise.all([loadNecesidadesParaAyuda(), loadAssignments()]);
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
  window.loadAyudasSection = () => { loadNecesidadesParaAyuda(); loadAssignments(); };
  window.selectNeedForAid = (id) => { loadNecesidadesParaAyuda().then(() => { const need = (window._lastNeeds || []).find(n => n.id === id); if (need) selectNeed(need); }); };
}

function formatTime(iso) {
  if (!iso) return "";
  try {
    const d = new Date(iso);
    if (isNaN(d.getTime())) return iso;
    return d.toLocaleString("es-ES", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit" });
  } catch { return iso; }
}
