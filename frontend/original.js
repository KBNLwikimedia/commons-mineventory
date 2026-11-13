// Helpers for "Gegevens van deze afbeelding" (OriginalData.vue, functional design 9.7):
// caption languages and the edit summary that saving on Commons will use (phase 2).

// A language code as Wikibase uses it for captions: "de", "zh-hans", "nds-nl".
export const isLanguageCode = (code) => /^[a-z]{2,3}(-[a-z0-9]{2,8})*$/.test(String(code || ""));

// The name of a language in the language of the interface ("Duits"), else the code.
export function languageName(code, uiLanguage) {
  try {
    const name = new Intl.DisplayNames([uiLanguage], { type: "language" }).of(code);
    return name && name !== code ? name : code;
  } catch {
    return code;
  }
}

// Languages to offer under "Add a language" (more can be typed as a code).
export const COMMON_LANGUAGES = [
  "de", "fr", "es", "it", "pt", "la", "fy", "li", "nds", "pap", "af", "da", "sv", "nb", "fi", "pl",
  "cs", "hu", "el", "ru", "uk", "tr", "ar", "he", "fa", "hi", "id", "ja", "ko", "zh-hans", "zh-hant",
];

// What was typed or chosen under "Add a language" → a code, or "" when it is none:
// a code itself, or the name of a language in the list ("Duits", "german").
export function languageFromInput(text, uiLanguage) {
  const typed = String(text || "").trim();
  const lower = typed.toLowerCase();
  if (isLanguageCode(lower)) return lower;
  const named = COMMON_LANGUAGES.find(
    (code) => languageName(code, uiLanguage).toLowerCase() === lower || languageName(code, "en").toLowerCase() === lower
  );
  return named || "";
}

// The edit summary on Commons, in English (decision 8 of 9.7: the AI origin is said here,
// not in the data): "Added depicts (3) and position to existing depicts (1), changed
// caption (nl) with Commons Mineventory; AI suggestions checked by the user".
export function editSummary({ depicts = 0, positions = 0, added = [], changed = [] }) {
  const parts = [];
  const addedParts = [];
  if (depicts) addedParts.push(`depicts (${depicts})`);
  if (positions) addedParts.push(`position to existing depicts (${positions})`);
  if (added.length) addedParts.push(`caption (${added.join(", ")})`);
  if (addedParts.length) parts.push(`added ${joinAnd(addedParts)}`);
  if (changed.length) parts.push(`changed caption (${changed.join(", ")})`);
  if (!parts.length) return "";
  const text = parts.join(", ");
  return `${text[0].toUpperCase()}${text.slice(1)} with Commons Mineventory; AI suggestions checked by the user`;
}
const joinAnd = (list) => (list.length > 1 ? `${list.slice(0, -1).join(", ")} and ${list.at(-1)}` : list[0]);
