/* A colour per class of object (wish Olaf, 8-11-2026): when a page has objects of more than
   one kind (plates, wine glasses, ...), the masks in the viewer and a dot in the object list
   share a colour per kind. The kind is the name you gave it yourself, else the search term the
   image detection found it with; a group has that of its members, a region from Commons its name;
   drawn boxes and clicks without a name of your own have none and keep their own colours.
   Plain JS, used by the viewer (no Vue) and by the components. */

// Distinct from the status colours of the frames (blue, red, green, orange, grey).
export const CLASS_PALETTE = ["#7a3db8", "#0f8f8f", "#c2185b", "#7c8a00", "#8d5a2b", "#1f4e8c", "#d4a017", "#5c6b73"];

const PLACEHOLDER_TERMS = new Set(["klik", "rechthoek", "regio"]);
// A click, a drawn rectangle or a region has no search word of its own.
export const isPlaceholderTerm = (term) => PLACEHOLDER_TERMS.has(String(term || "").trim().toLowerCase());

const kindOf = (value) => {
  const term = String(value || "").trim().toLowerCase();
  return term && !PLACEHOLDER_TERMS.has(term) ? term : null;
};

/* The kind of an object in lower case, or null: the name you gave it (wish Olaf: a doll the
   detection found as "person" and you named "doll" is a doll); else its search term; for a group
   that of its members ("group: cloud (13)" is a cloud; mixed: none); for a region from Commons
   its English name, as the search terms are English (wish Olaf). */
export function classKey(obj) {
  if (!obj) return null;
  return ownKind(obj) || foundKind(obj);
}
const ownKind = (obj) => kindOf(obj.naam || obj.groep?.naam);
function foundKind(obj) {
  const source = { sam: obj.zoekterm, dummy: obj.zoekterm, groep: obj.groep?.soort, commons: obj.label_en || obj.label_item || obj.label };
  return obj.bron in source ? kindOf(source[obj.bron]) : null;
}

/* Every kind an object belongs to, for the tick boxes and their counts: one per object (wish Olaf
   12-11-2026), the name you gave it, else the search term that found it ("cardboard box" renamed
   to "suitcase" is only a suitcase); the words it was also found with before finds were merged
   ("Also found as") no longer count here. A group counts under the kinds of its members too.
   The mask has one colour: that of classKey (a group of mixed kinds without a name has none). */
export function classKeys(obj) {
  if (!obj) return [];
  const members = obj.bron === "groep" ? obj.groep?.leden || [] : [];
  return [...new Set([classKey(obj), ...members.flatMap(classKeys)].filter(Boolean))];
}

/* {kind: colour} for the objects of a page; empty when there are fewer than two kinds, so a
   page with one kind keeps the colours of the status. Alphabetical, so a colour stays with
   its kind while objects come and go. */
export function classColors(objects) {
  const kinds = [...new Set((objects || []).flatMap(classKeys))].sort();
  if (kinds.length < 2) return {};
  return Object.fromEntries(kinds.map((kind, i) => [kind, CLASS_PALETTE[i % CLASS_PALETTE.length]]));
}

/* The tick boxes of the masks as [kind, colour]; while you search the object list, what you typed
   comes first (wish Olaf): "doll" as a tick box for all objects that match it. A kind of that
   name merges with it and keeps its colour. */
export const QUERY_COLOUR = "#54595d";
export function kindsWithQuery(colors, query) {
  const kinds = Object.entries(colors || {});
  return query ? [[query, colors?.[query] || QUERY_COLOUR], ...kinds.filter(([kind]) => kind !== query)] : kinds;
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
