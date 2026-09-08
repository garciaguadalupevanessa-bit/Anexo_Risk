// Dashboard section — loadDashboard, dashboardExportCSV (light theme)
import { normalizeGDACSAlerts } from "../core/normalization/index.js";
import { apiGet, escapeHtml } from "../shared/config.js";

export async function loadDashboard() {
  const container = document.getElementById("dashboard-categorias");
  const zonasContainer = document.getElementById("dashboard-zonas");
  const sevContainer = document.getElementById("dashboard-severidad");
  const deteccionesEl = document.getElementById("metric-detecciones");

  try {
    const [necesidades, donaciones, alertas, incendios, incidentsData] = await Promise.all([
      apiGet("/api/necesidades"),
      apiGet("/api/donaciones"),
      apiGet("/api/alertas"),
      apiGet("/api/incendios").catch(() => ({ detecciones: [] })),
      apiGet("/api/incidents?is_active=true").catch(() => []),
    ]);

    const incidents = Array.isArray(incidentsData) ? incidentsData : [];
    const total = necesidades.length;
    const abiertas = necesidades.filter(n => n.estado === "abierta").length;
    const cubiertas = total - abiertas;
    const cobertura = total > 0 ? Math.round((cubiertas / total) * 100) : 0;

    const totalDetecciones = (incendios.detecciones || []).length;

    const normalizedAlerts = normalizeGDACSAlerts(alertas);
    const criticasAlertas = normalizedAlerts.filter(a => a.severity.level === "critica" || a.severity.level === "alta").length;

    const set = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };
    set("metric-alertas-activas", alertas.length);
    set("metric-alertas-criticas", `${criticasAlertas} críticas`);
    set("metric-necesidades-abiertas", abiertas);
    set("metric-necesidades-total", total);
    set("metric-necesidades-cubiertas", cubiertas);
    set("metric-cobertura", cobertura);
    if (deteccionesEl) deteccionesEl.textContent = totalDetecciones;

    // Incident metrics
    const incActive = incidents.length;
    const incCritical = incidents.filter(i => i.severity === "roja").length;
    const incHigh = incidents.filter(i => i.severity === "naranja").length;
    const incInResponse = incidents.filter(i => i.status === "en_respuesta").length;
    const metricIncEl = document.getElementById("metric-incidentes-activas");
    const metricIncCritEl = document.getElementById("metric-incidentes-criticas");
    if (metricIncEl) metricIncEl.textContent = incActive;
    if (metricIncCritEl) metricIncCritEl.textContent = `${incCritical} críticos · ${incHigh} altos`;

    // Feedback stats
    const feedbackContainer = document.getElementById("dashboard-feedback");
    if (feedbackContainer) {
      try {
        const feedbackStats = await apiGet("/api/outcomes/stats");
        feedbackContainer.innerHTML = `
          <div class="data-row"><span class="data-row__label">Predicciones registradas</span><span class="data-row__value">${feedbackStats.total_predictions}</span></div>
          <div class="data-row"><span class="data-row__label">Con resultado</span><span class="data-row__value">${feedbackStats.with_outcome}</span></div>
          <div class="data-row"><span class="data-row__label">Incidentes cerrados</span><span class="data-row__value">${feedbackStats.incidents_closed}</span></div>
          <div class="data-row"><span class="data-row__label">Escalaciones</span><span class="data-row__value">${feedbackStats.escalations}</span></div>
          ${feedbackStats.avg_response_hours ? `<div class="data-row"><span class="data-row__label">Tiempo medio respuesta</span><span class="data-row__value">${Number(feedbackStats.avg_response_hours).toFixed(1)}h</span></div>` : ""}
        `;
      } catch {
        feedbackContainer.innerHTML = '<p class="state-empty" style="font-size:var(--text-sm);padding:var(--space-sm);">Sin datos de feedback</p>';
      }
    }

    // Severity bars
    if (sevContainer) {
      const sevCounts = {};
      normalizedAlerts.forEach(a => {
        const s = a.severity.level;
        sevCounts[s] = (sevCounts[s] || 0) + 1;
      });
      const sevLabels = { critica: "Crítica", alta: "Alta", moderada: "Moderada", informativa: "Informativa", sin_severidad: "Sin dato" };
      const sevColors = { critica: "var(--sev-critica)", alta: "var(--sev-alta)", moderada: "var(--sev-moderada)", informativa: "var(--sev-informativa)", sin_severidad: "var(--text-muted)" };
      const maxSev = Math.max(...Object.values(sevCounts), 1);
      sevContainer.innerHTML = Object.entries(sevCounts).map(([s, c]) => `
        <div class="dashboard-bar" role="listitem">
          <span class="dashboard-bar__dot" style="background:${sevColors[s] || 'var(--text-muted)'}"></span>
          <span class="dashboard-bar__label">${sevLabels[s] || s}</span>
          <div class="dashboard-bar__track">
            <div class="dashboard-bar__fill" style="width:${(c / maxSev) * 100}%;background:${sevColors[s] || 'var(--text-muted)'}"></div>
          </div>
          <span class="dashboard-bar__count">${c}</span>
        </div>`).join("") || '<p class="state-empty" style="font-size:var(--text-sm);padding:var(--space-sm);">Sin datos</p>';
    }

    // Category bars
    const catLabels = { agua: "💧 Agua", alimentos: "🍞 Alimentos", parafarmacia: "💊 Parafarmacia", ropa: "👕 Ropa", higiene: "🧴 Higiene", refugio: "🏠 Refugio", transporte: "🚗 Transporte", otros: "📦 Otros" };
    if (container) {
      const cats = {};
      necesidades.forEach(n => {
        const t = n.tipo || n.categoria || "otros";
        cats[t] = (cats[t] || 0) + 1;
      });
      const maxCat = Math.max(...Object.values(cats), 1);
      const catSorted = Object.entries(cats).sort((a, b) => b[1] - a[1]);
      container.innerHTML = catSorted.map(([tipo, count]) => `
        <div class="dashboard-bar" role="listitem">
          <span class="dashboard-bar__label">${catLabels[tipo] || tipo}</span>
          <div class="dashboard-bar__track">
            <div class="dashboard-bar__fill" style="width:${(count / maxCat) * 100}%"></div>
          </div>
          <span class="dashboard-bar__count">${count}</span>
        </div>`).join("") || '<p class="state-empty" style="font-size:var(--text-sm);padding:var(--space-sm);">Sin datos</p>';
    }

    // Critical needs
    const criticalNecesidades = necesidades.filter(n => n.prioridad === "critica" && n.estado === "abierta");
    const criticasContainer = document.getElementById("dashboard-criticas");
    if (criticasContainer) {
      criticasContainer.innerHTML = criticalNecesidades.length
        ? criticalNecesidades.slice(0, 5).map(n => `
          <div class="data-row" style="align-items:center;">
            <span style="font-size:var(--text-base);">${catLabels[n.tipo] || "📦"}</span>
            <span class="data-row__label" style="flex:1;">
              <strong>${escapeHtml(n.titulo || n.tipo)}</strong>
              <span style="display:block;font-size:var(--text-xs);color:var(--text-muted);">${escapeHtml(n.direccion || "Sin ubicación")}</span>
            </span>
            <button class="btn btn--primary btn--sm" onclick="window.showSection('ayudas'); window.selectNeedForAid(${n.id})">Ayudar</button>
          </div>`).join("")
        : '<p class="state-empty" style="font-size:var(--text-sm);color:var(--success);padding:var(--space-sm);">✓ No hay necesidades críticas</p>';
    }

    // Top zones
    if (zonasContainer) {
      const zonas = {};
      necesidades.forEach(n => {
        if (!n.direccion || n.estado === "cubierta") return;
        const parts = n.direccion.split(",");
        const zona = parts.length > 1 ? parts[parts.length - 1].trim() : n.direccion.substring(0, 30);
        zonas[zona] = (zonas[zona] || 0) + 1;
      });
      const zonasSorted = Object.entries(zonas).sort((a, b) => b[1] - a[1]).slice(0, 5);
      zonasContainer.innerHTML = zonasSorted.length
        ? zonasSorted.map(([zona, count]) => `
          <div class="data-row">
            <span class="data-row__label">${escapeHtml(zona)}</span>
            <span class="data-row__value">${count}</span>
          </div>`).join("")
        : '<p class="state-empty" style="font-size:var(--text-sm);padding:var(--space-sm);">Sin datos suficientes</p>';
    }

    window._dashboardData = { necesidades, donaciones, alertas };
  } catch (err) {
    console.error("Dashboard error:", err);
  }
}

window.dashboardExportCSV = function() {
  const data = window._dashboardData;
  if (!data) return;
  let csv = "=== ANEXO RISK — EXPORT DE DATOS ===\n";
  csv += `Generado: ${new Date().toLocaleString("es-ES")}\n\n`;

  csv += "=== NECESIDADES ===\n";
  csv += ["ID", "Tipo", "Título", "Descripción", "Dirección", "Prioridad", "Estado", "Fecha"].map(c => `"${c}"`).join(",") + "\n";
  data.necesidades.forEach(n => {
    csv += [n.id, n.tipo, n.titulo || "", n.descripcion || "", n.direccion || "", n.prioridad, n.estado, n.creado_en].map(c => `"${(c || "").toString().replace(/"/g, '""')}"`).join(",") + "\n";
  });

  csv += "\n=== AYUDAS ===\n";
  csv += ["ID", "Tipo", "Recurso", "Cantidad", "Descripción", "Contacto", "Estado", "Fecha"].map(c => `"${c}"`).join(",") + "\n";
  data.donaciones.forEach(d => {
    csv += [d.id, d.tipo, d.recurso, d.cantidad || "", d.descripcion || "", d.contacto, d.estado, d.creado_en].map(c => `"${(c || "").toString().replace(/"/g, '""')}"`).join(",") + "\n";
  });

  csv += "\n=== ALERTAS ===\n";
  csv += ["ID", "Título", "Tipo", "Severidad", "País", "Fecha", "Enlace"].map(c => `"${c}"`).join(",") + "\n";
  data.alertas.forEach(a => {
    csv += [a.id, a.titulo || "", a.tipo || "", a.severidad || "", a.pais || "", a.fecha || "", a.enlace || ""].map(c => `"${(c || "").toString().replace(/"/g, '""')}"`).join(",") + "\n";
  });

  const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `anexo_risk_export_${new Date().toISOString().split("T")[0]}.csv`;
  a.click();
};
