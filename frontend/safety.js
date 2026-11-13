// The safety net of a page: an error nobody caught (in a component, a watcher, or a promise that
// was never awaited) shows one red message at the top of the screen, instead of a blank or frozen
// page. The error itself still goes to the console, so a real bug is not hidden.
import { createApp, reactive } from "vue";
import { errorText, isAbort } from "./api.js";
import NoticeList from "./components/NoticeList.vue";

// The one message of the safety net (at most one: a newer error replaces it).
export const safetyNotices = reactive([]);
let lastId = 0;

/* Show `error` as the one red message; `t` translates. Aborted requests are not errors. */
export function reportUnexpected(t, error) {
  if (isAbort(error)) return false;
  const detail = errorText(t, error);
  safetyNotices.splice(0, safetyNotices.length, { id: ++lastId, type: "error", text: t("error.unexpected", { detail }) });
  return true;
}

let listening = false;
/* Install the net on a Vue app: its errorHandler, and once per page the window's unhandled
   promise rejections. `target`: where the message is shown (a new element on top of the body). */
export function installSafetyNet(app, t, { target = null, win = window, log = console } = {}) {
  app.config.errorHandler = (error, instance, info) => {
    log.error(error, info); // Vue logs nothing itself once a handler is set
    reportUnexpected(t, error);
  };
  if (!listening && win?.addEventListener) {
    listening = true;
    // The browser logs the rejection itself; it is not prevented, so the console keeps it.
    win.addEventListener("unhandledrejection", (event) => reportUnexpected(t, event.reason));
  }
  const host = target || mountPoint(win);
  if (!host) return null;
  const net = createApp(NoticeList, { notices: safetyNotices, onDismiss: (id) => safetyNotices.splice(0, safetyNotices.length, ...safetyNotices.filter((n) => n.id !== id)) });
  net.provide("t", t);
  net.mount(host);
  return net;
}

function mountPoint(win) {
  const doc = win?.document;
  if (!doc?.body) return null;
  let host = doc.querySelector(".cc-vangnet");
  if (host) return null; // already there (a second app on the same page)
  host = doc.createElement("div");
  host.className = "cc-vangnet";
  doc.body.prepend(host);
  return host;
}

/* For the tests: forget that the window listener was added. */
export function resetSafetyNet() {
  listening = false;
  safetyNotices.splice(0, safetyNotices.length);
}
