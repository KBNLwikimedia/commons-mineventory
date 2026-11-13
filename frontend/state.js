// The state of the start page lives in its URL (functional design 10.2: every
// state keeps its own URL): ?mid=…&pagina=…&object=…, or ?url=… / ?titel=….
export function readStart(search) {
  const params = new URLSearchParams(search);
  const read = (key) => params.get(key) || "";
  return { url: read("url"), titel: read("titel"), mid: read("mid"), pagina: read("pagina"), object: read("object"), vergroten: read("vergroten") };
}

/* A page number from an address or the history: a whole number from 1 to `total` (when known);
   anything else ("abc", 0, -2, 2.5, a page the file no longer has) gives the nearest valid page. */
export function pageNumber(value, total = Infinity) {
  const n = Math.floor(Number(value));
  if (!Number.isFinite(n) || n < 1) return 1;
  return Math.min(n, Math.max(1, Number(total) || 1));
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

/* Write a list back (Undo after removing or clearing): only valid entries, at most MAX_HISTORY. */
export function restoreHistory(list, store = storage()) {
  const valid = (Array.isArray(list) ? list : []).filter((entry) => entry && /^M\d+$/.test(entry.mid));
  const seen = new Set();
  return writeHistory(valid.filter((entry) => !seen.has(entry.mid) && seen.add(entry.mid)).slice(0, MAX_HISTORY), store);
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

/* The image whose AI suggestions should open on arrival: the link "the AI suggestions" in "Start this image
   over" ends in #ai-suggesties (wish Olaf). Read once when the app loads; the mark then leaves the address. */
export const START_SUGGESTIONS = (() => {
  if (typeof window === "undefined" || window.location.hash !== "#ai-suggesties") return null;
  const mid = new URLSearchParams(window.location.search).get("mid");
  window.history.replaceState(null, "", window.location.pathname + window.location.search);
  return mid;
})();

/* Forget what this browser keeps for one file (wish Olaf, starting an image over): searched words,
   your own search words, unticked terms and items. Keys look like "cc-…:<mid>" or "cc-…:<mid>:<page>". */
export function forgetFileInBrowser(mid, storage = window.localStorage) {
  const keys = [];
  try {
    for (let i = 0; i < storage.length; i++) keys.push(storage.key(i));
    for (const key of keys) if (key?.startsWith("cc-") && key.split(":")[1] === mid) storage.removeItem(key);
  } catch {
    // Storage can be off in a private window: nothing to forget then.
  }
}

export function objectName(obj, language = "nl", t = null) {
  // A name you gave it yourself (in the list, like a layer in Photoshop) comes first.
  if (obj.naam) return obj.naam;
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

// The page of a file on Commons, e.g. with anchor "P180" at its depicts statements.
export function commonsFileUrl(title, anchor = "") {
  return `https://commons.wikimedia.org/wiki/${encodeURIComponent(String(title || "").replace(/ /g, "_"))}${anchor ? `#${anchor}` : ""}`;
}

/* The objects per search term ({term, name, n}), groups left out, named as in the list (the Dutch
   label when there is one); `skip(object)` leaves more out. For the "per kind" links in bulk. */
export function kindsOf(objects, language = "nl", skip = () => false) {
  const terms = new Map();
  for (const o of objects) {
    if (o.bron === "groep" || !o.zoekterm || skip(o)) continue;
    const item = terms.get(o.zoekterm) || { term: o.zoekterm, name: language === "en" ? o.zoekterm : o.label_nl || o.zoekterm, n: 0 };
    item.n += 1;
    terms.set(o.zoekterm, item);
  }
  return [...terms.values()];
}

// The name of a Commons file without the namespace ("File:Foo.jpg" → "Foo.jpg").
export function fileName(title) {
  return String(title || "").replace(/^File:/, "");
}
