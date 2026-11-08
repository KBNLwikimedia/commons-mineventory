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

/* The image of a file (its page), through the app's own server. */
export const fileImage = (f, width) => `${API}/bestand/${encodeURIComponent(f.mid)}/pagina/${f.pagina || 1}/afbeelding?w=${width}`;
