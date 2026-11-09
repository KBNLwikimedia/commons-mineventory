/* The facets of the Objects page (functional design 10.4), for both tabs: Objects and Trash. */
import { API } from "./api.js";
import { fileName } from "./state.js";

export const emptyFilters = () => ({ sources: [], files: [], saved: false, augmented: false });

/* The objects the facets let through. */
export function applyFacets(objects, filters) {
  return objects.filter(
    (o) =>
      (!filters.sources.length || filters.sources.includes(o.bron)) &&
      (!filters.files.length || filters.files.includes(o.mid)) &&
      (!filters.saved || o.opgeslagen) &&
      (!filters.augmented || o.aangevuld)
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
  const words = query.toLowerCase().split(/\s+/).filter(Boolean);
  return rows.filter(
    (row) => Object.entries(filters).every(([key, chosen]) => !chosen.length || chosen.includes(row.values[key])) && words.every((word) => row.text.includes(word))
  );
}

/* The download address of an export: lists comma-separated, what is empty or off left out. */
export function exportUrl(base, params, format) {
  const query = new URLSearchParams({ formaat: format });
  for (const [name, value] of Object.entries(params || {})) {
    const text = Array.isArray(value) ? value.join(",") : value === true ? "1" : typeof value === "string" ? value.trim() : "";
    if (text) query.set(name, text);
  }
  return `${base}?${query}`;
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
