// The small conveniences this browser remembers (localStorage). Storage can be
// off or full (private window, blocked site data): every call then quietly does
// nothing, and a read gives the fallback, so the app works the same without it.

import { ref, watch } from "vue";

/* The stored text for `key`, or `fallback` when there is none (or it is empty).
   With {json: true} the text is parsed; text that does not parse gives `fallback`. */
export function readStored(key, fallback = null, { json = false } = {}) {
  try {
    const raw = window.localStorage.getItem(key);
    if (raw === null || raw === "") return fallback;
    return json ? JSON.parse(raw) : raw;
  } catch {
    return fallback;
  }
}

/* Store `value` under `key`: as is (as text), or with {json: true} as JSON. */
export function writeStored(key, value, { json = false } = {}) {
  try {
    window.localStorage.setItem(key, json ? JSON.stringify(value) : String(value));
  } catch {
    // Blocked storage: the value holds until the page is reloaded.
  }
}

export function removeStored(key) {
  try {
    window.localStorage.removeItem(key);
  } catch {
    // Blocked storage: nothing to forget.
  }
}

/* `value` taken out of `list` when it is in it, else added (a tick box). */
export const toggledIn = (list, value) => (list.includes(value) ? list.filter((x) => x !== value) : [...list, value]);
/* The other ones: what is in `all` but not in `list` (Invert). */
export const invertedIn = (all, list) => all.filter((x) => !list.includes(x));

/* A list remembered in this browser under a key that changes (per file or page; `key` is a
   computed): read again when the key changes, stored on every change, without doubles. */
export function useStoredList(key) {
  const list = ref([]);
  watch(key, (k) => (list.value = readStored(k, [], { json: true })), { immediate: true });
  function set(values) {
    list.value = [...new Set(values)];
    writeStored(key.value, list.value, { json: true });
  }
  return { list, set, toggle: (value) => set(toggledIn(list.value, value)), invert: (all) => set(invertedIn(all, list.value)) };
}
