// Text typed by a person (a name, caption, hint, search): spaces and invisible characters at the
// edges go (zero-width spaces, joiners, direction marks, a BOM, pasted along from elsewhere), so a
// text of only those counts as empty. Inside the text nothing changes: an emoji built with a joiner,
// or Arabic or Hebrew next to Latin, stays as it is.
const INVISIBLE = "\\s\\u00AD\\u180E\\u200B-\\u200F\\u2028-\\u202F\\u205F-\\u2064\\u2066-\\u206F\\uFEFF";
const EDGE = new RegExp(`^[${INVISIBLE}]+|[${INVISIBLE}]+$`, "g");

export function cleanText(value) {
  return value == null ? "" : String(value).replace(EDGE, "");
}

/* The words of a search, each cleaned, empty ones left out, in lower case. */
export function searchWords(value) {
  return cleanText(value).toLowerCase().split(/\s+/).map(cleanText).filter(Boolean);
}

/* A text with "- " bullets and "  - " sub-bullets as a list: [{text, sub: [..]}]; other lines are left out. */
export function bulletList(text) {
  const items = [];
  for (const line of String(text || "").split("\n")) {
    if (line.startsWith("- ")) items.push({ text: line.slice(2), sub: [] });
    else if (line.startsWith("  - ") && items.length) items[items.length - 1].sub.push(line.slice(4));
  }
  return items;
}
