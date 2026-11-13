// One confirmation question at a time, shown by ConfirmDialog.vue as a Codex
// dialog instead of the browser's own window.confirm (functional design 10).
import { reactive } from "vue";

export const confirmState = reactive({
  open: false, text: "", title: "", go: "", destructive: false, links: {}, dontAsk: "", dontAskChecked: false, resolve: null,
  // Optional: objects the question is about ({image, name}), shown as a list with thumbnails;
  // and a text field ({label, placeholder, help}) whose value askConfirmValue() returns.
  objects: [], objectsFirst: false, input: null, inputValue: "",
  // Optional: the objects as tick boxes, all on, so one can still be left out (bulk actions, wish
  // Olaf 13-11-2026); at least `pick.min` stay ticked. The text and button follow the count
  // (`pick.text(n)`, `pick.go(n)`); askConfirmValue() returns the ticked indexes as `picked`.
  pick: null, picked: [],
  // Optional: what else to know (wish Olaf 13-11-2026), as a paragraph after the objects; the
  // text itself says first, and briefly, what the action does.
  note: "",
  // Optional: a text the question is about, shown as it is in a block of its own after the
  // question (e.g. the earlier prompt that would be deleted; wish Olaf 13-11-2026).
  quote: "",
  // Optional: what goes as labelled fields ([{label, help, value}] or with `items` a list, shown
  // as bullets): the label in bold, its value
  // in a block of its own, a little smaller (wish Olaf 13-11-2026), after the question.
  fields: [],
  fieldsTitle: "",
  // Optional: a choice ({value, label, help, go, destructive}); the chosen one sets the
  // button, and askConfirmValue() returns it as `choice`.
  choices: [], choice: "",
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
export function askConfirmValue(text, { title = "", go = "", destructive = false, links = {}, dontAsk = "", objects = [], objectsFirst = false, input = null, choices = [], note = "", quote = "", fields = [], fieldsTitle = "", pick = null, store = session() } = {}) {
  const all = objects.map((_, i) => i);
  if (skipped(dontAsk, store)) return Promise.resolve({ ok: true, value: "", choice: choices[0]?.value || "", picked: all });
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
      objectsFirst,
      note,
      quote,
      fields,
      fieldsTitle,
      pick: pick && objects.length ? { min: 1, ...pick } : null,
      picked: objects.map(() => true),
      input,
      inputValue: "",
      choices,
      choice: choices[0]?.value || "",
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
        const choice = confirmState.choices.length ? confirmState.choice : "";
        const picked = confirmState.pick ? confirmState.picked.flatMap((on, i) => (on ? [i] : [])) : all;
        confirmState.open = false;
        confirmState.resolve = null;
        resolve({ ok: answer, value, choice, picked });
      },
    });
  });
}

// Deleting an earlier version (of a description, a completion, a prompt): the same question
// everywhere, only the sentence differs. `t` is the translation function. What goes is shown
// between the question and the rest of the text (wish Olaf 13-11-2026): `shown` is a text
// (the prompt, the description) or {objects} (e.g. the image of a completed version).
export function confirmDeleteVersion(text, t, shown = "") {
  return askRemoval(text, { title: t("describe.history_delete"), go: t("describe.history_delete"), destructive: true }, shown);
}

// A question about removing something, with what goes shown after the first paragraph: a text
// (`shown` a string: in a block of its own) or {objects: [{image, name}]}. The rest of the text
// becomes the note below it.
export function askRemoval(text, options, shown = "") {
  const what = typeof shown === "string" ? { quote: shown.trim() } : { objects: shown?.objects || [] };
  if (!what.quote && !what.objects?.length) return askConfirm(text, options);
  const [question, ...rest] = text.split(/\n\s*\n/);
  return askConfirm(question, { ...options, ...what, note: [rest.join("\n\n"), options.note].filter(Boolean).join("\n\n") });
}

export function answerConfirm(answer) {
  confirmState.resolve?.(answer);
}
