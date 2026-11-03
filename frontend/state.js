// The state of the start page lives in its URL (functional design 10.2: every
// state keeps its own URL): ?mid=…&pagina=…&object=…, or ?url=… / ?titel=….
export function readStart(search) {
  const params = new URLSearchParams(search);
  const read = (key) => params.get(key) || "";
  return { url: read("url"), titel: read("titel"), mid: read("mid"), pagina: read("pagina"), object: read("object") };
}

export function appUrl(mid, n = 1, objectId) {
  const params = new URLSearchParams({ mid });
  if (n > 1) params.set("pagina", String(n));
  if (objectId) params.set("object", objectId);
  return `/?${params.toString()}`;
}

// What the tooltip and lists call an object: the Dutch or English name, by language.
export function objectName(obj, language = "nl") {
  if (obj.beschrijving) {
    const subject = language === "en" ? obj.beschrijving.onderwerp_en : obj.beschrijving.onderwerp;
    if (subject) return subject;
  }
  if (language === "en") return obj.label_en || obj.label;
  return obj.label_nl || obj.label;
}
