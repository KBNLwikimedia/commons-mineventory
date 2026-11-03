// Mounts a Vue app on a place in a Jinja page (functional design 10.2), with
// the texts and settings Flask embedded in the page.
import { createApp } from "vue";
import { readConfig } from "./config.js";
import { createI18n } from "./i18n.js";

export function mount(component, selector, props = {}) {
  const element = document.querySelector(selector);
  if (!element) return null;
  const config = readConfig();
  const declared = component.props || {};
  const wanted = { ...element.dataset, ...props, config };
  // Only the props the component declares; the rest would end up as HTML attributes.
  const given = Object.fromEntries(Object.entries(wanted).filter(([key]) => key in declared));
  const app = createApp(component, given);
  app.use(createI18n(config.teksten || {}, config.taal));
  app.provide("config", config);
  app.mount(element);
  return app;
}
