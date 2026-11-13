// The small conveniences this browser remembers (localStorage). Storage can be
// off or full (private window, blocked site data): every call then quietly does
// nothing, and a read gives the fallback, so the app works the same without it.

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
