// The settings and texts Flask embeds in every page (<script id="cutter-config">),
// so nothing has to be loaded from elsewhere.
export function readConfig(doc = document) {
  const element = doc.getElementById("cutter-config");
  return element ? JSON.parse(element.textContent) : { taal: "en", teksten: {} };
}
