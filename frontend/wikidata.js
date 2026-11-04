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
