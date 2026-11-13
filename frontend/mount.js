// Mounts a Vue app on a place in a Jinja page (functional design 10.2), with
// the texts and settings Flask embedded in the page.
import { createApp } from "vue";
import { smoothAccordions } from "./accordion-motion.js";
import { readConfig } from "./config.js";
import { createI18n } from "./i18n.js";
import { movableDialogs } from "./movable.js";

export function mount(component, selector, props = {}) {
  const element = document.querySelector(selector);
  if (!element) return null;
  const config = readConfig();
  const declared = component.props || {};
  const wanted = { ...element.dataset, ...props, config };
  // Only the props the component declares; the rest would end up as HTML attributes.
  const given = Object.fromEntries(Object.entries(wanted).filter(([key]) => key in declared));
  const app = createApp(component, given);
  const i18n = createI18n(config.teksten || {}, config.taal);
  app.use(i18n);
  app.provide("config", config);
  app.mount(element);
  smoothAccordions(); // all fold-outs open and close smoothly (once per page)
  // Every dialog can be moved and resized (wish Olaf 13-11-2026); once per page.
  movableDialogs({ move: i18n.t("magnifier.move"), resize: i18n.t("magnifier.resize") });
  return app;
}
