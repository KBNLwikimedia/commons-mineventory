// One confirmation question at a time, shown by ConfirmDialog.vue as a Codex
// dialog instead of the browser's own window.confirm (functional design 10).
import { reactive } from "vue";

export const confirmState = reactive({
  open: false, text: "", title: "", go: "", destructive: false, links: {}, dontAsk: "", dontAskChecked: false, resolve: null,
  // Optional: objects the question is about ({image, name}), shown as a list with thumbnails;
  // and a text field ({label, placeholder, help}) whose value askConfirmValue() returns.
  objects: [], input: null, inputValue: "",
});

/* "Niet meer vragen": a question with a dontAsk key can be switched off for
   this session of the browser tab (sessionStorage); it then answers yes at once. */
const DONT_ASK_PREFIX = "cc-niet-vragen:";
function skipped(key, store) {
  try {
    return Boolean(key) && store?.getItem(DONT_ASK_PREFIX + key) === "1";
  } catch {
    return false;
  }
}
function session() {
  try {
    return window.sessionStorage;
  } catch {
    return null;
  }
}

/* The text in parts: plain text, and links for {name} placeholders that
   `links` names ({name: {href, label}}). No HTML is inserted. */
export function textParts(text, links = {}) {
  return text.split(/(\{\w+\})/).filter(Boolean).map((part) => {
    const name = part.match(/^\{(\w+)\}$/)?.[1];
    return name && links[name] ? { link: links[name] } : { text: part };
  });
}

// Resolves to true (go ahead) or false (cancelled or closed).
export function askConfirm(text, options = {}) {
  return askConfirmValue(text, options).then((result) => result.ok);
}

// Resolves to {ok, value}: with `input`, value is what was typed in the field ("" if nothing).
export function askConfirmValue(text, { title = "", go = "", destructive = false, links = {}, dontAsk = "", objects = [], input = null, store = session() } = {}) {
  if (skipped(dontAsk, store)) return Promise.resolve({ ok: true, value: "" });
  if (confirmState.resolve) confirmState.resolve(false); // a newer question replaces an open one
  return new Promise((resolve) => {
    Object.assign(confirmState, {
      open: true,
      text,
      title,
      go,
      destructive,
      links,
      dontAsk,
      dontAskChecked: false,
      objects,
      input,
      inputValue: "",
      resolve: (answer) => {
        // Only a "yes" with the box ticked switches the question off.
        if (answer && confirmState.dontAsk && confirmState.dontAskChecked) {
          try {
            store?.setItem(DONT_ASK_PREFIX + confirmState.dontAsk, "1");
          } catch {
            // Blocked storage: the question simply comes again.
          }
        }
        const value = confirmState.input ? confirmState.inputValue.trim() : "";
        confirmState.open = false;
        confirmState.resolve = null;
        resolve({ ok: answer, value });
      },
    });
  });
}

export function answerConfirm(answer) {
  confirmState.resolve?.(answer);
}
