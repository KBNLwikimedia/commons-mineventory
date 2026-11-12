/* The facets of the Objects page (functional design 10.4), for both tabs: Objects and Trash. */
import { API } from "./api.js";
import { fileName } from "./state.js";

export const emptyFilters = () => ({ sources: [], files: [], saved: false, augmented: false, query: "" });

const searchWords = (query) => (query || "").toLowerCase().split(/\s+/).filter(Boolean);

/* What the search box on the Objects page looks in; the same fields as the export (OBJECT_SEARCHED in api.py).
   A name of your own replaces the AI's search term (wish Olaf, 12-11-2026). */
export const objectText = (o) =>
  [o.mid, o.bestand_titel, o.naam || o.groep?.naam, ...(o.naam || o.groep?.naam ? (o.bron === "commons" ? [o.label_en] : []) : [o.label_nl, o.zoekterm, o.label_en]), o.licentie, o.bijschrift?.tekst, o.beschrijving?.onderwerp, o.beschrijving?.onderwerp_en, o.beschrijving?.beschrijving, o.beschrijving?.beschrijving_en]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

/* The objects the facets let through. */
export function applyFacets(objects, filters) {
  const words = searchWords(filters.query);
  return objects.filter(
    (o) =>
      (!filters.sources.length || filters.sources.includes(o.bron)) &&
      (!filters.files.length || filters.files.includes(o.mid)) &&
      (!filters.saved || o.opgeslagen) &&
      (!filters.augmented || o.aangevuld) &&
      (!words.length || words.every((word) => objectText(o).includes(word)))
  );
}

/* The files the objects come from, for the file facet: {mid, titel, n, pagina, url}, by title. */
export function filesOf(objects) {
  const byMid = new Map();
  for (const o of objects) {
    const entry = byMid.get(o.mid) || { mid: o.mid, titel: "", n: 0, pagina: o.pagina || 1, url: "" };
    // Not every object carries the file title; take the first one that does.
    entry.titel ||= fileName(o.bestand_titel);
    entry.url ||= o.bestand_url || "";
    entry.n += 1;
    byMid.set(o.mid, entry);
  }
  return [...byMid.values()].map((f) => ({ ...f, titel: f.titel || f.mid })).sort((a, b) => a.titel.localeCompare(b.titel));
}

/* For the pages that are a list (Changelog, Usage). A row is {values: {facet: value}, text}, with
   the text in lower case. Within a facet any chosen value will do, between facets all must hold;
   every word of the search must occur. */
export function applyListFilters(rows, filters, query = "") {
  const words = searchWords(query);
  return rows.filter(
    (row) => Object.entries(filters).every(([key, chosen]) => !chosen.length || chosen.includes(row.values[key])) && words.every((word) => row.text.includes(word))
  );
}

// A choice as text in an address: a list comma-separated, on as "1", empty or off as "".
const paramText = (value) => (Array.isArray(value) ? value.join(",") : value === true ? "1" : typeof value === "string" ? value.trim() : "");

/* The download address of an export: lists comma-separated, what is empty or off left out. */
export function exportUrl(base, params, format) {
  const query = new URLSearchParams({ formaat: format });
  for (const [name, value] of Object.entries(params || {})) {
    const text = paramText(value);
    if (text) query.set(name, text);
  }
  return `${base}?${query}`;
}

/* The choice on a list page in its address (wish Olaf: RESTful, so a view can be bookmarked and
   shared), with the same names as its export. readAddress gives {name: [values]} and the search q;
   writeAddress sets or removes them, leaving other parameters (uselang) alone, without a new step
   in the browser history. */
export function readAddress(names, search = window.location.search) {
  const query = new URLSearchParams(search);
  const lists = Object.fromEntries(names.map((name) => [name, (query.get(name) || "").split(",").map((v) => v.trim()).filter(Boolean)]));
  return { ...lists, q: query.get("q") || "" };
}
export function writeAddress(params, location = window.location, history = window.history) {
  const query = new URLSearchParams(location.search);
  for (const [name, value] of Object.entries(params)) {
    const text = paramText(value);
    if (text) query.set(name, text);
    else query.delete(name);
  }
  const text = query.toString();
  const url = location.pathname + (text ? `?${text}` : "") + location.hash;
  if (url !== location.pathname + location.search + location.hash) history.replaceState(history.state, "", url);
}

/* The ids of the objects found with a search word (wish Olaf): as their own search term, as a
   word they were also found with before two finds were merged ("ook"), also inside a group. */
export function objectsWithTerm(objects, term) {
  const word = String(term || "").toLowerCase();
  const has = (o) => String(o.zoekterm || "").toLowerCase() === word || (o.ook || []).some((e) => String(e.zoekterm || "").toLowerCase() === word);
  const ids = [];
  for (const o of objects || []) {
    if (has(o)) ids.push(o.id);
    for (const member of o.groep?.leden || []) if (has(member)) ids.push(member.id);
  }
  return ids;
}

/* The rows ordered by a value (direction 1 or -1): numbers as numbers, text with 0.9 before 0.33;
   rows without a value always last. */
export function sortRows(rows, value, direction) {
  const empty = (v) => v === null || v === undefined || v === "";
  const compare = (a, b) => (typeof a === "number" && typeof b === "number" ? a - b : typeof a === "boolean" ? Number(a) - Number(b) : String(a).localeCompare(String(b), undefined, { numeric: true, sensitivity: "base" }));
  return rows
    .map((row) => [row, value(row)])
    .sort(([, a], [, b]) => (empty(a) ? (empty(b) ? 0 : 1) : empty(b) ? -1 : direction * compare(a, b)))
    .map(([row]) => row);
}

/* Latest date or highest version first. */
export const newestFirst = (a, b) => b.localeCompare(a, undefined, { numeric: true });

/* The values of one facet with their number of rows: [{value, n}], most rows first (wish Olaf) unless
   a comparison of the values is given; rows without a value are left out. */
export function facetOptions(rows, key, compare = null) {
  const counts = new Map();
  for (const row of rows) {
    const value = row.values[key];
    if (value) counts.set(value, (counts.get(value) || 0) + 1);
  }
  const byCount = (a, b) => b.n - a.n || a.value.localeCompare(b.value, undefined, { numeric: true });
  return [...counts].map(([value, n]) => ({ value, n })).sort(compare ? (a, b) => compare(a.value, b.value) : byCount);
}

/* The image of a file (its page), through the app's own server. */
export const fileImage = (f, width) => `${API}/bestand/${encodeURIComponent(f.mid)}/pagina/${f.pagina || 1}/afbeelding?w=${width}`;
