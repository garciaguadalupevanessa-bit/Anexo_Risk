// Dashboard section — loadDashboard, dashboardExportCSV
import { normalizeGDACSAlerts } from "../core/normalization/index.js";
import { apiGet } from "../shared/config.js";

export async function loadDashboard() {
  const container = document.getElementById("dashboard-categorias");
  const zonasContainer = document.getElementById("dashboard-zonas");
  const sevContainer = document.getElementById("dashboard-severidad");
  const tiposContainer = document.getElementById("dashboard-tipos");
  const deteccionesEl = document.getElementById("metric-detecciones");

  try {
    const [necesidades, donaciones, alertas, incendios] = await Promise.all([
      apiGet("/api/necesidades"),
      apiGet("/api/donaciones"),
      apiGet("/api/alertas"),
      apiGet("/api/incendios").catch(() => ({ detecciones: [] })),
    ]);

    const total = necesidades.length;
    const abiertas = necesidades.filter(n => n.estado === "abierta").length;
    const cubiertas = total - abiertas;
    const cobertura = total > 0 ? Math.round((cubiertas / total) * 100) : 0;

    const totalAyudas = donaciones.length;
    const activasAyudas = donaciones.filter(d => d.estado === "activa" || d.estado === "abierta").length;

    const totalAlertas = alertas.length;
    const normalizedAlerts = normalizeGDACSAlerts(alertas);
    const criticasAlertas = normalizedAlerts.filter(a => a.severity.level === "critica" || a.severity.level === "alta").length;

    const totalDetecciones = (incendios.detecciones || []).length;

    if (document.getElementById("metric-alertas-activas"))
      document.getElementById("metric-alertas-activas").textContent = totalAlertas;
    if (document.getElementById("metric-alertas-criticas"))
      document.getElementById("metric-alertas-criticas").textContent = criticasAlertas + " críticas";
    if (document.getElementById("metric-necesidades-abiertas"))
      document.getElementById("metric-necesidades-abiertas").textContent = abiertas;
    if (document.getElementById("metric-necesidades-total"))
      document.getElementById("metric-necesidades-total").textContent = total;
    if (document.getElementById("metric-necesidades-cubiertas"))
      document.getElementById("metric-necesidades-cubiertas").textContent = cubiertas;
    if (document.getElementById("metric-cobertura"))
      document.getElementById("metric-cobertura").textContent = cobertura;
    if (deteccionesEl) deteccionesEl.textContent = totalDetecciones;

    if (sevContainer) {
      const sevCounts = {};
      normalizedAlerts.forEach(a => {
        const s = a.severity.level;
        sevCounts[s] = (sevCounts[s] || 0) + 1;
      });
      const sevLabels = { critica: "Crítica", alta: "Alta", moderada: "Moderada", informativa: "Informativa", sin_severidad: "Sin dato" };
      const sevColors = { critica: "var(--sev-critica)", alta: "var(--sev-alta)", moderada: "var(--sev-moderada)", informativa: "var(--sev-informativa)", sin_severidad: "var(--text-muted)" };
      sevContainer.innerHTML = Object.entries(sevCounts).map(([s, c]) => `
        <div class="data-row" role="listitem">
          <span class="data-row__dot" style="background:${sevColors[s] || 'var(--text-muted)'}"></span>
          <span class="data-row__label">${sevLabels[s] || s}</span>
          <span class="data-row__value">${c}</span>
        </div>`).join("") || '<p style="color:var(--text-muted);font-size:var(--text-sm);">Sin datos</p>';
    }

    if (tiposContainer) {
      const typeCounts = {};
      normalizedAlerts.forEach(a => {
        const t = a.type.label;
        typeCounts[t] = (typeCounts[t] || 0) + 1;
      });
      tiposContainer.innerHTML = Object.entries(typeCounts).sort((a, b) => b[1] - a[1]).map(([t, c]) => `
        <div class="data-row" role="listitem">
          <span class="data-row__label">${t}</span>
          <span class="data-row__value">${c}</span>
        </div>`).join("") || '<p style="color:var(--text-muted);font-size:var(--text-sm);">Sin datos</p>';
    }

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
        <div class="dashboard-bar">
          <span class="dashboard-bar__label">${catLabels[tipo] || tipo}</span>
          <div class="dashboard-bar__track">
            <div class="dashboard-bar__fill" style="width:${(count / maxCat) * 100}%"></div>
          </div>
          <span class="dashboard-bar__count">${count}</span>
        </div>`).join("");
    }

    // Necesidades críticas
    const criticalNecesidades = necesidades.filter(n => n.prioridad === "critica" && n.estado === "abierta");
    const criticasContainer = document.getElementById("dashboard-criticas");
    if (criticasContainer) {
      criticasContainer.innerHTML = criticalNecesidades.length
        ? criticalNecesidades.slice(0, 5).map(n => `
          <div style="padding:10px 0;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:8px;">
            <span style="font-size:1.2rem;">${catLabels[n.tipo] || "📦"}</span>
            <div style="flex:1;">
              <div style="font-weight:600;">${n.titulo || n.tipo}</div>
              <div style="font-size:0.8rem;color:var(--text-muted);">${n.direccion || "Sin ubicación"}</div>
            </div>
            <button class="btn btn--primary btn--sm" onclick="window.showSection('ayudas'); window.selectNeedForAid(${n.id})">Ayudar</button>
          </div>`).join("")
        : '<p style="color:var(--green);font-size:var(--text-sm);">🎉 ¡No hay necesidades críticas! ¡Buen trabajo!</p>';
    }

    // Motivación
    const motivacionEl = document.getElementById("dashboard-motivacion");
    if (motivacionEl) {
      let motivacion = "";
      if (abiertas === 0) {
        motivacion = "🎉 ¡Todas las necesidades han sido cubiertas! La comunidad es increíble.";
      } else if (cobertura >= 75) {
        motivacion = `🔥 ¡${cobertura}% de cobertura! Ya casi lo conseguimos. Faltan ${abiertas} necesidades.`;
      } else if (cobertura >= 50) {
        motivacion = `💪 ¡Buen avance! ${cobertura}% de necesidades cubiertas. ¡Sigue así!`;
      } else if (total > 0) {
        motivacion = `🤝 Hay ${total} necesidades reportadas. Cada ayuda cuenta. ¿Empezamos?`;
      } else {
        motivacion = "🚀 Aún no hay necesidades activas. Sé el primero en ayudar cuando llegue una.";
      }
      motivacionEl.textContent = motivacion;
    }

    // Top zonas
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
        ? zonasSorted.map(([zona, count]) => `<div class="dashboard-zone-item">${zona} — <strong>${count}</strong> necesidad${count > 1 ? "es" : ""}</div>`).join("")
        : '<p style="color:var(--text-muted);font-size:var(--text-sm);">Sin datos suficientes</p>';
    }

    window._dashboardData = { necesidades, donaciones, alertas };
    window._dashboardData.alertas = alertas;
  } catch (err) {
    console.error("Dashboard error:", err);
  }
}

window.dashboardExportCSV = function() {
  const data = window._dashboardData;
  if (!data) return;
  let csv = "=== ANEXO FINDER — EXPORT DE DATOS ===\n";
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
