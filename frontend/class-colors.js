/* A colour per class of object (wish Olaf, 8-11-2026): when a page has objects of more than
   one kind (plates, wine glasses, ...), the masks in the viewer and a dot in the object list
   share a colour per kind. The kind is the search term the image detection found it with;
   drawn boxes, clicks, groups and regions from Commons have none and keep their own colours.
   Plain JS, used by the viewer (no Vue) and by the components. */

// Distinct from the status colours of the frames (blue, red, green, orange, grey).
export const CLASS_PALETTE = ["#7a3db8", "#0f8f8f", "#c2185b", "#7c8a00", "#8d5a2b", "#1f4e8c", "#d4a017", "#5c6b73"];

const PLACEHOLDER_TERMS = new Set(["klik", "rechthoek", "regio"]);

/* The kind of an object: its search term in lower case, or null. */
export function classKey(obj) {
  if (!obj || (obj.bron !== "sam" && obj.bron !== "dummy")) return null;
  const term = String(obj.zoekterm || "").trim().toLowerCase();
  return term && !PLACEHOLDER_TERMS.has(term) ? term : null;
}

/* {kind: colour} for the objects of a page; empty when there are fewer than two kinds, so a
   page with one kind keeps the colours of the status. Alphabetical, so a colour stays with
   its kind while objects come and go. */
export function classColors(objects) {
  const kinds = [...new Set((objects || []).map(classKey).filter(Boolean))].sort();
  if (kinds.length < 2) return {};
  return Object.fromEntries(kinds.map((kind, i) => [kind, CLASS_PALETTE[i % CLASS_PALETTE.length]]));
}

/* The colour of one object, or null. */
export const classColor = (colors, obj) => (colors && colors[classKey(obj)]) || null;
