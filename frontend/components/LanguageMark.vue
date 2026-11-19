<!--
  A small language icon after a text that is not in the language of the interface: Wikidata had
  no label or description in it, so the app shows another language (wish Olaf 19-11-2026). The
  mouse-over (and the screen reader) says which language. Nothing when the text is in the
  interface language or has no language.
-->
<template>
  <span v-if="lang && lang !== config.taal" class="cc-taal-vervanger" role="img" :aria-label="help" :title="help">
    <cdx-icon :icon="cdxIconLanguage" size="x-small" />
  </span>
</template>

<script setup>
import { computed, inject } from "vue";
import { CdxIcon } from "@wikimedia/codex";
import { cdxIconLanguage } from "@wikimedia/codex-icons";
import { useT } from "../i18n.js";
import { languageName } from "../original.js";

const props = defineProps({
  // The language the text is in: "en", "mul", "de"…
  lang: { type: String, default: "" },
});
const config = inject("config");
const t = useT();
const help = computed(() =>
  props.lang === "mul"
    ? t("language.fallback_mul", { wanted: languageName(config.taal, config.taal) })
    : t("language.fallback", { wanted: languageName(config.taal, config.taal), lang: languageName(props.lang, config.taal), code: props.lang })
);
</script>
