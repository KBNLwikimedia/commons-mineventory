// One confirmation question at a time, shown by ConfirmDialog.vue as a Codex
// dialog instead of the browser's own window.confirm (functional design 10).
import { reactive } from "vue";

export const confirmState = reactive({ open: false, text: "", title: "", go: "", destructive: false, links: {}, resolve: null });

/* The text in parts: plain text, and links for {name} placeholders that
   `links` names ({name: {href, label}}). No HTML is inserted. */
export function textParts(text, links = {}) {
  return text.split(/(\{\w+\})/).filter(Boolean).map((part) => {
    const name = part.match(/^\{(\w+)\}$/)?.[1];
    return name && links[name] ? { link: links[name] } : { text: part };
  });
}

// Resolves to true (go ahead) or false (cancelled or closed).
export function askConfirm(text, { title = "", go = "", destructive = false, links = {} } = {}) {
  if (confirmState.resolve) confirmState.resolve(false); // a newer question replaces an open one
  return new Promise((resolve) => {
    Object.assign(confirmState, {
      open: true,
      text,
      title,
      go,
      destructive,
      links,
      resolve: (answer) => {
        confirmState.open = false;
        confirmState.resolve = null;
        resolve(answer);
      },
    });
  });
}

export function answerConfirm(answer) {
  confirmState.resolve?.(answer);
}
