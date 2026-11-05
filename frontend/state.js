// The state of the start page lives in its URL (functional design 10.2: every
// state keeps its own URL): ?mid=…&pagina=…&object=…, or ?url=… / ?titel=….
export function readStart(search) {
  const params = new URLSearchParams(search);
  const read = (key) => params.get(key) || "";
  return { url: read("url"), titel: read("titel"), mid: read("mid"), pagina: read("pagina"), object: read("object") };
}

// History ("Laatst bezocht"): the files opened in this browser, newest first,
// with the page that was open. Per browser for now; with a login (phase 2)
// it can move to the server, per user. The first entry is the file the
// start page and the "back" link return to.
export const HISTORY_KEY = "cc-geschiedenis";
export const MAX_HISTORY = 50;
// A row of "Bekeken" being dragged carries its M-id under this type.
export const DRAG_TYPE = "application/x-commons-mineventory-mid";

function storage() {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

export function readHistory(store = storage()) {
  try {
    const list = JSON.parse(store?.getItem(HISTORY_KEY) || "[]");
    return Array.isArray(list) ? list.filter((entry) => entry && /^M\d+$/.test(entry.mid)) : [];
  } catch {
    return [];
  }
}

function writeHistory(list, store) {
  try {
    store?.setItem(HISTORY_KEY, JSON.stringify(list));
  } catch {
    // Private mode or blocked storage: there is simply no history.
  }
  return list;
}

/* Put a file on top of the history ({mid, naam, pagina, paginas}); returns the new list. */
export function addToHistory(entry, store = storage(), now = new Date()) {
  const list = readHistory(store).filter((e) => e.mid !== entry.mid);
  list.unshift({ ...entry, tijd: now.toISOString() });
  return writeHistory(list.slice(0, MAX_HISTORY), store);
}

/* Set an entry aside ("Opzij gezet") or bring it back to the active list. Opening
   the file again (addToHistory) also brings it back. */
export function setAside(mid, aside, store = storage()) {
  return writeHistory(readHistory(store).map((e) => (e.mid === mid ? { ...e, opzij: aside ? true : undefined } : e)), store);
}

export function removeFromHistory(mid, store = storage()) {
  return writeHistory(readHistory(store).filter((e) => e.mid !== mid), store);
}

export function clearHistory(store = storage()) {
  return writeHistory([], store);
}

/* The URL of the file that was open last, or null. */
export function lastFileUrl(store = storage()) {
  const [last] = readHistory(store);
  return last ? appUrl(last.mid, last.pagina || 1) : null;
}

export function appUrl(mid, n = 1, objectId) {
  const params = new URLSearchParams({ mid });
  if (n > 1) params.set("pagina", String(n));
  if (objectId) params.set("object", objectId);
  return `/?${params.toString()}`;
}

// What the tooltip and lists call an object, by language: the subject from the
// AI image description, else the caption (as the user or a file note wrote it),
// else the label of the detection. The labels the app gives itself (a click, a
// drawn rectangle, a region) are translated when `t` is given.
const OWN_LABELS = ["klik", "rechthoek", "regio"];

/* Names that occur more than once get a number ("man 1", "man 2"), in reading
   order of the list (alphabetical, then top to bottom, left to right), so the
   list and the names in the image say the same. {id: name}; the magnifier and
   Commons keep the plain name. */
export function numberedNames(objects, language = "nl", t = null) {
  const name = (obj) => objectName(obj, language, t);
  const sorted = [...objects].sort((a, b) => name(a).localeCompare(name(b), language, { sensitivity: "base" }) || a.box.y - b.box.y || a.box.x - b.box.x);
  const counts = {};
  const numbers = {};
  for (const obj of sorted) {
    const key = name(obj).toLocaleLowerCase(language);
    counts[key] = (counts[key] || 0) + 1;
    numbers[obj.id] = counts[key];
  }
  return Object.fromEntries(
    sorted.map((obj) => [obj.id, counts[name(obj).toLocaleLowerCase(language)] > 1 ? `${name(obj)} ${numbers[obj.id]}` : name(obj)])
  );
}

export function objectName(obj, language = "nl", t = null) {
  if (obj.beschrijving) {
    const subject = language === "en" ? obj.beschrijving.onderwerp_en : obj.beschrijving.onderwerp;
    if (subject) return subject;
  }
  if (obj.bijschrift?.tekst) return obj.bijschrift.tekst;
  if (t && OWN_LABELS.includes(obj.label) && !obj.label_en) return t(`object.label_${obj.label}`);
  if (language === "en") return obj.label_en || obj.label;
  return obj.label_nl || obj.label;
}

// CropTool (croptool2.toolforge.org) opened on the whole file. Its README
// mentions left/top/width/height for a preselected crop, but in practice it
// showed the whole image, so the app links to the file only (main screen).
// Only for single images: PDF, DjVu and multi-page TIFF are pages.
export const CROPTOOL = "https://croptool2.toolforge.org/";

export function cropToolLink(file) {
  if (!file || (file.paginas || 1) > 1 || !String(file.mime || "").startsWith("image/")) return null;
  const title = file.naam || String(file.titel || "").replace(/^File:/, "");
  return `${CROPTOOL}?${new URLSearchParams({ title })}`;
}

// "saved · 23 days left" for a saved cut-out (retention, functional design 12.1),
// with the date and an explanation for a tooltip. The server gives `verloopt`.
export function savedLabel(obj, t, language = "nl", now = Date.now()) {
  const saved = obj?.opgeslagen;
  if (!saved) return null;
  if (!saved.verloopt) return { text: t("objects.saved"), title: "" };
  const expires = new Date(saved.verloopt);
  const days = Math.max(0, Math.ceil((expires.getTime() - now) / 86400000));
  const date = expires.toLocaleDateString(language === "en" ? "en-GB" : "nl-NL", { day: "numeric", month: "long", year: "numeric" });
  return {
    text: t("objects.saved"),
    // The period left, shown apart (italic) so it stands out.
    left: days === 1 ? t("objects.saved_one_day") : t("objects.saved_days", { n: days }),
    title: t("objects.saved_expiry", { date }),
    soon: days <= 7,
  };
}

// The name of a Commons file without the namespace ("File:Foo.jpg" → "Foo.jpg").
export function fileName(title) {
  return String(title || "").replace(/^File:/, "");
}
