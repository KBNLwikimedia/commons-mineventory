<!--
  A small "AI" mark beside a text that a language model wrote: the subject
  and description from "Wat staat hierop?" (kind "beschrijving") or the page
  overview with its search terms (kind "pagina"), or an object found by the
  AI image detection (kind "detectie"). A click opens a short
  explanation of what that means and what to check. It may sit in an
  accordion title, so the click does not toggle the accordion.
-->
<template>
  <cdx-button
    weight="quiet"
    size="small"
    action="progressive"
    class="cc-ai-merk"
    :aria-label="t('ai.badge_label')"
    :title="t('ai.badge_label')"
    @click.stop.prevent="open = true"
  >
    <cdx-icon :icon="cdxIconRobot" size="small" /> AI
  </cdx-button>
  <cdx-dialog
    v-model:open="open"
    class="cc-ai-uitleg"
    :title="t('ai.title')"
    :use-close-button="true"
    :close-button-label="t('actions.close')"
    :default-action="{ label: t('actions.close') }"
    @default="open = false"
  >
    <p>
      <template v-for="(part, i) in textParts(t(texts.what), { model: modelLink })" :key="i">
        <a v-if="part.link" :href="part.link.href" target="_blank" rel="noopener">{{ part.link.label }}</a>
        <template v-else>{{ part.text }}</template>
      </template>
      <template v-if="score != null"> {{ t("ai.score_detection", { score: Math.round(score * 100) }) }}</template>
    </p>
    <p>{{ t(texts.risk) }}</p>
    <p>{{ t(texts.check) }}</p>
    <p v-if="edited">{{ t("ai.edited") }}</p>
  </cdx-dialog>
</template>

<script setup>
import { computed, ref } from "vue";
import { CdxButton, CdxDialog, CdxIcon } from "@wikimedia/codex";
import { cdxIconRobot } from "@wikimedia/codex-icons";
import { textParts } from "../confirm.js";
import { useT } from "../i18n.js";

const props = defineProps({
  model: { type: String, default: "" },
  kind: { type: String, default: "beschrijving" },
  // The detection's score (0-1), for kind "detectie".
  score: { type: Number, default: null },
  // The text was changed by hand after the model wrote it.
  edited: { type: Boolean, default: false },
});
const t = useT();
const open = ref(false);
const TEXTS = {
  beschrijving: { what: "ai.what", risk: "ai.risk", check: "ai.check" },
  pagina: { what: "ai.what_page", risk: "ai.risk", check: "ai.check_page" },
  detectie: { what: "ai.what_detection", risk: "ai.risk_detection", check: "ai.check_detection" },
};
const texts = computed(() => TEXTS[props.kind] || TEXTS.beschrijving);
// The model name links to Meta's page about it (as in the live-mode line).
const modelLink = computed(() => ({
  label: props.model || (props.kind === "detectie" ? "SAM" : "Muse Spark"),
  href: props.kind === "detectie" ? "https://ai.meta.com/sam3/" : "https://dev.meta.ai/docs/models#muse-spark",
}));
</script>
