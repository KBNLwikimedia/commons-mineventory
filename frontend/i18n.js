// A small translation function for the Vue components (functional design 3):
// the same frontend/i18n/<taal>.json files the Jinja templates use, embedded
// by Flask in the page. A missing key shows the key itself.
import { inject } from "vue";

export function translate(messages, key, params = {}) {
  const text = messages[key] ?? key;
  return text.replace(/\{(\w+)\}/g, (match, name) => (name in params ? String(params[name]) : match));
}

export function createI18n(messages, language = "en") {
  const t = (key, params) => translate(messages, key, params);
  return {
    t,
    language,
    install(app) {
      app.config.globalProperties.$t = t;
      app.provide("t", t);
      app.provide("language", language);
    },
  };
}

export function useT() {
  return inject("t", (key) => key);
}

// Amounts in dollars, in the interface language.
export function money(amount, language = "en") {
  return new Intl.NumberFormat(language === "nl" ? "nl-NL" : "en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 2,
    maximumFractionDigits: 4,
  }).format(amount || 0);
}
