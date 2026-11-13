// Feedback after an action that changed something, with Undo where it can be undone (wish Olaf
// 13-11-2026): one message per place, in the colours of 10.4, that stays until it is closed.
// useUndoMessage() keeps that message for a component (UndoMessage.vue shows it); the helpers below
// make the usual "put the previous version back" undo functions, so no component writes its own.
import { reactive } from "vue";
import { del, errorText, put } from "./api.js";

let lastId = 0;

/* The message of one place: show(type, text, undo, {label, done}) replaces the previous one.
   `undo` (optional) is an async function; undo() runs it, then shows `done` (or "Ongedaan gemaakt.")
   in green, or the error in red. `label` replaces "↶ Ongedaan maken" on the button. */
export function useUndoMessage(t) {
  const note = reactive({
    message: null,
    busy: false,
    show(type, text, undo = null, { label = "", done = "" } = {}) {
      note.message = { id: ++lastId, type, text, undo, label, done };
    },
    async undo() {
      const shown = note.message;
      if (!shown?.undo || note.busy) return;
      note.busy = true;
      try {
        await shown.undo();
        note.show("success", shown.done || t("feedback.undone"));
      } catch (error) {
        note.show("error", errorText(t, error));
      } finally {
        note.busy = false;
      }
    },
    clear() {
      note.message = null;
    },
  });
  return note;
}

// The id of a description version, as the server gives it (beschrijving.py, version()):
// when it was edited by hand, else when the AI made it. "" without a description.
export const descriptionVersion = (description) => (description && (description.bewerkt_op || description.tijdstempel)) || "";

// The same for the description of the whole image (page_description_version()); "" when the
// overview has no description.
export function pageDescriptionVersion(overview) {
  if (!overview || !["paginasoort", "paginasoort_en", "samenvatting", "samenvatting_en", "tekst"].some((field) => overview[field])) return "";
  return overview.bewerkt_op || (overview.delen?.beschrijving || overview).tijdstempel || "";
}

/* Undo of a change of version: PUT {key: value} back to `path` (a description by its "versie", an
   AI-completed version by its "sleutel"); without an earlier one, DELETE `path` instead. */
export function versionBack(path, key, value) {
  return () => (value ? put(path, { [key]: value }) : del(path));
}

/* Undo of a change of your own prompt: the text that was yours before, or back to the app's
   prompt when there was none (`info`: the prompt answer before the change). */
export function promptBack(path, info) {
  return versionBack(path, "prompt", info?.eigen ? info.eigen_prompt?.tekst || "" : "");
}
