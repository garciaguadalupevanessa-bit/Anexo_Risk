/* Anexo Risk — Anonymous Analytics (Pilot)

Tracks product events only. NO PII, NO coordinates, NO medical data.
Events are stored in localStorage for later export.
*/
const STORAGE_KEY = "anexo_analytics";
const MAX_EVENTS = 500;

function _trackEvent(eventName, data = {}) {
  try {
    const events = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    events.push({
      event: eventName,
      ts: new Date().toISOString(),
      ...data,
    });
    // Keep only last MAX_EVENTS
    if (events.length > MAX_EVENTS) events.splice(0, events.length - MAX_EVENTS);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(events));
  } catch (e) { /* silent */ }
}

window._trackEvent = _trackEvent;

window._exportAnalytics = function() {
  try {
    const events = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
    const blob = new Blob([JSON.stringify(events, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `anexo_analytics_${new Date().toISOString().split("T")[0]}.json`;
    a.click();
  } catch (e) { /* silent */ }
};
