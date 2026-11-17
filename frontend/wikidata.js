// Searching Wikidata items (through the server, a read), shared by every search
// field: a short pause after typing, at least two letters, and an answer that
// arrives after a newer question is ignored. stop() ends a pending search when
// the component closes.

import { API, get, query } from "./api.js";

export const DELAY_MS = 300;
export const MIN_LETTERS = 2;

/* A hit as an item for a Codex menu: label, "Q… · description", and the hit itself. */
export function menuItem(hit) {
  return { value: hit.q, label: hit.label, description: [hit.q, hit.beschrijving].filter(Boolean).join(" · "), hit };
}

/* The image (P18) of a Wikidata item, through our own server. */
export const itemImage = (q, width = 120) => `${API}/wikidata/${q}/afbeelding?w=${width}`;

// A Wikidata label or description ({nl, en, mul?, andere?: {taal, waarde}}) in the language of the
// interface; without one the other of nl/en, then the multilingual label, then another language
// (wish Olaf 17-11-2026: never empty when Wikidata has something). "" when there is nothing.
export function inLanguage(texts, language) {
  if (!texts) return "";
  const other = language === "en" ? "nl" : "en";
  return texts[language] || texts[other] || texts.mul || texts.andere?.waarde || "";
}

// The best Wikidata hit for a search term: the label exactly as the term first ("lemon" the
// fruit, not "LemON" the band), then the same letters in another case, then a label containing
// it, else the first hit. Shared by the window for the whole image and that of a cut-out.
export function bestHit(hits, term) {
  const exact = String(term || "").trim();
  const lower = exact.toLowerCase();
  return (
    hits.find((h) => h.label === exact) ||
    hits.find((h) => (h.label || "").toLowerCase() === lower) ||
    hits.find((h) => (h.label || "").toLowerCase().includes(lower)) ||
    hits[0] ||
    null
  );
}

// Label and description per Q-id ({Q: {label: {nl, en}, beschrijving: {nl, en}}}), free and cached.
export async function itemInfo(ids) {
  const list = [...new Set(ids.filter(Boolean))];
  const result = {};
  for (let i = 0; i < list.length; i += 50) {
    const data = await get(`${API}/wikidata/items${query({ ids: list.slice(i, i + 50).join("|") })}`);
    Object.assign(result, data.items || {});
  }
  return result;
}

export async function searchItems(term, language) {
  return (await get(`${API}/wikidata/zoek${query({ q: term, taal: language })}`)).resultaten;
}

/* A searcher for one field. search(text, apply) calls apply(items, done): items
   are menu items; done is false while waiting and true once an answer is in. */
export function wikidataSearcher(language) {
  let timer = null;
  let asked = 0;
  return {
    search(text, apply) {
      clearTimeout(timer);
      const mine = ++asked;
      const term = (text || "").trim();
      if (term.length < MIN_LETTERS) {
        apply([], false);
        return;
      }
      apply(null, false);
      timer = setTimeout(async () => {
        let items = [];
        try {
          items = (await searchItems(term, language)).map(menuItem);
        } catch {
          items = [];
        }
        if (mine === asked) apply(items, true); // an older answer after a newer question: ignored
      }, DELAY_MS);
    },
    stop() {
      clearTimeout(timer);
      asked += 1;
    },
  };
}
