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

// A price as on a button: "($0.01)" when it is paid (live mode), else the word for free.
/* A moment shown in the app, always to the second (wish Olaf 13-11-2026): "13 nov 2026, 12:24:07".
   `dateStyle` "short" for the compact lines under earlier versions. Empty for no value. */
export function formatStamp(value, language = "nl", dateStyle = "medium") {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleString(language === "en" ? "en-GB" : "nl-NL", { dateStyle, timeStyle: "medium" });
}

export function priceLabel(amount, paid, language, t) {
  return paid ? `(${money(amount, language)})` : t("panel.free");
}
