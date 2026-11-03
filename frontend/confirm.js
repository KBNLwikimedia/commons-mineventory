// One confirmation question at a time, shown by ConfirmDialog.vue as a Codex
// dialog instead of the browser's own window.confirm (functional design 10).
import { reactive } from "vue";

export const confirmState = reactive({ open: false, text: "", title: "", go: "", destructive: false, resolve: null });

// Resolves to true (go ahead) or false (cancelled or closed).
export function askConfirm(text, { title = "", go = "", destructive = false } = {}) {
  if (confirmState.resolve) confirmState.resolve(false); // a newer question replaces an open one
  return new Promise((resolve) => {
    Object.assign(confirmState, {
      open: true,
      text,
      title,
      go,
      destructive,
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
