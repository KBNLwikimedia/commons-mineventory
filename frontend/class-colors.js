/* A colour per class of object (wish Olaf, 8-11-2026): when a page has objects of more than
   one kind (plates, wine glasses, ...), the masks in the viewer and a dot in the object list
   share a colour per kind. The kind is the search term the image detection found it with;
   a group has that of its members, a region from Commons its name; drawn boxes and clicks have
   none and keep their own colours.
   Plain JS, used by the viewer (no Vue) and by the components. */

// Distinct from the status colours of the frames (blue, red, green, orange, grey).
export const CLASS_PALETTE = ["#7a3db8", "#0f8f8f", "#c2185b", "#7c8a00", "#8d5a2b", "#1f4e8c", "#d4a017", "#5c6b73"];

const PLACEHOLDER_TERMS = new Set(["klik", "rechthoek", "regio"]);

/* The kind of an object in lower case, or null: its search term; for a group that of its members
   ("group: cloud (13)" is a cloud; mixed: none); for a region from Commons its English name, as the search terms are English (wish Olaf). */
export function classKey(obj) {
  if (!obj) return null;
  const source = { sam: obj.zoekterm, dummy: obj.zoekterm, groep: obj.groep?.soort, commons: obj.label_en || obj.label_item || obj.label };
  if (!(obj.bron in source)) return null;
  const term = String(source[obj.bron] || "").trim().toLowerCase();
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

/* What the frame of an object shows (its colour in the legend): excluded, a region from
   Commons, a drawn rectangle, else selected or found. Used to show only some (wish Olaf). */
export const FRAME_KEYS = ["geselecteerd", "kandidaat", "commons", "handmatig", "uitgesloten"];
export function frameKey(obj) {
  if (obj?.status === "uitgesloten") return "uitgesloten";
  if (obj?.bron === "commons") return "commons";
  if (obj?.bron === "handmatig") return "handmatig";
  return obj?.status === "geselecteerd" ? "geselecteerd" : "kandidaat";
}

/* The colour of one object, or null. */
export const classColor = (colors, obj) => (colors && colors[classKey(obj)]) || null;
