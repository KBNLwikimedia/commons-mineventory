<!--
  The detection panel (functional design 7 and 10.4): regions from Commons,
  search, Snel zoeken, suggestions for this page, point mode and bulk
  operations. Costs are shown per button; in dummy mode everything is free.
-->
<template>
  <div class="cc-paneel">
    <p class="cc-modus" :class="{ betaald: config.betaald }">
      <template v-if="config.betaald">
        <template v-for="(part, i) in textParts(t('panel.mode_live'), modelLinks)" :key="i">
          <a v-if="part.link" :href="part.link.href" target="_blank" rel="noopener">{{ part.link.label }}</a>
          <template v-else>{{ part.text }}</template>
        </template>
      </template>
      <template v-else>{{ t("panel.mode_dummy") }}</template>
    </p>
    <busy-note v-if="busy && where === 'top'" :message="t('busy.general')" />

    <!-- Only when Commons has regions or notes for this page (they always refer to page 1). -->
    <!-- The AI suggestions come first: they fit this image, unlike a fixed list. -->
    <cdx-accordion v-model="open.suggestions">
      <template #title>{{ t("panel.suggestions") }}</template>
      <template v-if="inventory">
        <!-- Dutch, and English below it in italics, as in the magnifier (overviews from before 0.8 have only Dutch). -->
        <p class="cc-klein">
          {{ inventory.paginasoort }} — {{ inventory.samenvatting }}
          <template v-if="inventory.samenvatting_en"><br /><i>{{ inventory.paginasoort_en }} — {{ inventory.samenvatting_en }}</i></template>
          <ai-badge kind="pagina" :model="inventory.model" />
        </p>
        <div class="cc-knoppen">
          <cdx-button
            action="progressive"
            v-for="term in inventory.zoektermen"
            :key="term.en"
            size="small"
            :disabled="busy"
            :title="termTitle(term)"
            @click="act('suggestions', 'detect', { modus: 'prompt', prompt: term.en })"
          >
            {{ config.taal === "nl" ? term.nl : term.en }}
            <span v-if="termCount(term.en)" class="cc-term-aantal">{{ termCount(term.en) }}</span>
          </cdx-button>
        </div>
        <!-- What of these suggestions is on the image now, and what went to the trash. -->
        <p class="cc-klein">
          {{ t("panel.suggestions_found", { n: suggestionTotals.found, terms: suggestionTotals.terms, total: inventory.zoektermen.length }) }}
          <template v-if="suggestionTotals.trashed">{{ suggestionTotals.trashed === 1 ? t("panel.suggestions_trashed_one") : t("panel.suggestions_trashed", { n: suggestionTotals.trashed }) }}</template>
        </p>
      </template>
      <!-- The actions, full size, apart from the suggested labels above. With an
           overview, detecting all its terms in one go is the main action. -->
      <div class="cc-knoppen cc-inventaris-knop">
        <cdx-button
          v-if="inventory?.zoektermen?.length"
          action="progressive"
          weight="primary"
          :disabled="busy"
          @click="act('suggestions', 'detect', { modus: 'prompt', prompt: inventory.zoektermen.map((term) => term.en).join(', ') })"
        >
          {{ t("panel.detect_suggestions", { n: inventory.zoektermen.length }) }} <span class="cc-kosten">{{ cost(inventory.zoektermen.length) }}</span>
        </cdx-button>
        <cdx-button action="progressive" :weight="inventory?.zoektermen?.length ? 'normal' : 'primary'" :disabled="busy" @click="act('inventory', 'inventory')">
          {{ inventory ? t("panel.inventory_again") : t("panel.inventory") }}
        </cdx-button>
      </div>
      <busy-note v-if="busy && where === 'suggestions'" :message="t('busy.sam')" />
      <busy-note v-if="busy && where === 'inventory'" :message="t('busy.muse_page')" />
      <p class="cc-klein">
        {{ t("panel.inventory_help") }} {{ museCost(config.muse.pagina_usd) }}
        <template v-if="inventory">{{ t("panel.inventory_again_help") }}</template>
      </p>
    </cdx-accordion>

    <cdx-accordion v-if="regionCount" v-model="open.commons">
      <template #title>{{ t("panel.from_commons") }}</template>
      <p class="cc-klein">{{ t("panel.from_commons_help") }}</p>
      <cdx-button action="progressive" :disabled="busy" @click="act('commons', 'detect', { modus: 'commons' })">
        {{ t("panel.regions_button", { n: regionCount }) }}
      </cdx-button>
      <busy-note v-if="busy && where === 'commons'" :message="t('busy.commons')" />
    </cdx-accordion>

    <cdx-accordion v-model="open.search">
      <template #title>{{ t("panel.search") }}</template>
      <form class="cc-zoek" @submit.prevent="search">
        <cdx-text-input v-model="prompt" :placeholder="t('panel.search_placeholder')" :aria-label="t('panel.search')" />
        <cdx-button type="submit" action="progressive" :disabled="busy || !prompt.trim()">{{ t("panel.search_button") }}</cdx-button>
      </form>
      <busy-note v-if="busy && where === 'search'" :message="t('busy.sam')" />
      <p class="cc-klein">{{ t("panel.search_help") }} {{ cost(1) }}</p>
    </cdx-accordion>

    <!-- Point or draw: two ways to choose one object yourself; one of the two switches at a time. -->
    <cdx-accordion v-model="open.point">
      <template #title>{{ t("panel.point_or_draw") }}</template>
      <div class="cc-modus-keuze">
        <cdx-toggle-switch :model-value="pointMode" @update:model-value="emit('point-mode', $event)">
          {{ t("panel.point_switch") }}
        </cdx-toggle-switch>
        <p class="cc-klein">{{ t("panel.point_help") }} {{ cost(1) }}</p>
        <busy-note v-if="busy && where === 'point'" :message="t('busy.sam')" />
      </div>
      <div class="cc-modus-keuze">
        <cdx-toggle-switch :model-value="drawMode" @update:model-value="emit('draw-mode', $event)">
          {{ t("panel.draw_switch") }}
        </cdx-toggle-switch>
        <p class="cc-klein">{{ t("panel.draw_help") }} {{ t("panel.free") }}</p>
      </div>
    </cdx-accordion>

    <cdx-accordion v-model="open.bulk">
      <template #title>{{ t("panel.bulk") }}</template>
      <div class="cc-knoppen cc-knoppen-rij">
        <cdx-button action="progressive" :disabled="busy" :title="config.alles.map((a) => a.en).join(', ')" @click="act('bulk', 'detect', { modus: 'alles' })">
          {{ t("panel.all") }} <small>{{ cost(config.alles.length) }}</small>
        </cdx-button>
        <cdx-button action="progressive" :disabled="busy" @click="act('bulk', 'smart')">{{ t("panel.smart") }}</cdx-button>
        <cdx-button action="progressive" :disabled="busy" @click="act('bulk', 'describe-all')">{{ t("panel.describe_all") }}</cdx-button>
        <cdx-button action="progressive" :disabled="busy" @click="act('bulk', 'merge')">{{ t("panel.merge") }}</cdx-button>
      </div>
      <busy-note v-if="busy && where === 'bulk'" :message="t('busy.general')" />
    </cdx-accordion>
  </div>
</template>

<script setup>
import { computed, inject, reactive, ref, watch } from "vue";
import { CdxAccordion, CdxButton, CdxTextInput, CdxToggleSwitch } from "@wikimedia/codex";
import { textParts } from "../confirm.js";
import { money, useT } from "../i18n.js";
import AiBadge from "./AiBadge.vue";
import BusyNote from "./BusyNote.vue";

const props = defineProps({
  file: { type: Object, required: true },
  page: { type: Object, required: true },
  busy: { type: Boolean, default: false },
  inventory: { type: Object, default: null },
  // The objects on the page now, and per search term how many are in the trash.
  objects: { type: Array, default: () => [] },
  trashTerms: { type: Object, default: () => ({}) },
  pointMode: { type: Boolean, default: false },
  drawMode: { type: Boolean, default: false },
});
const emit = defineEmits(["detect", "smart", "inventory", "merge", "describe-all", "point-mode", "draw-mode"]);
const t = useT();
const config = inject("config");
// The two models in the live-mode line link to Meta's own pages. Muse Spark
// has no homepage of its own; its section in the model overview is the closest.
const modelLinks = {
  sam: { href: "https://ai.meta.com/sam3/", label: config.sam_model },
  muse: { href: "https://dev.meta.ai/docs/models#muse-spark", label: "Muse Spark" },
};
const prompt = ref("");
const open = reactive({ commons: true, search: false, suggestions: true, point: false, bulk: false });
const regionCount = computed(() => props.page.regio_aantal + props.page.notitie_aantal);

const SAM_PER_CALL = 0.0025;
const cost = (calls) => (config.betaald ? `(${money(calls * SAM_PER_CALL, config.taal)})` : t("panel.free"));
const museCost = (usd) => (config.betaald ? `(${money(usd, config.taal)})` : t("panel.free"));

// Where the waiting feedback goes: the section whose button was clicked last;
// a click in the image (point mode) shows it under Aanwijzen.
const where = ref("top");
let clicked = { section: "top", at: 0 };
// How many objects on the image came from a suggested term (not those in the trash).
function termCount(term) {
  return props.objects.filter((o) => o.zoekterm === term).length;
}

function termTitle(term) {
  const parts = [t("panel.term_expected", { n: term.aantal, where: term.waar }), t("panel.term_found", { n: termCount(term.en) })];
  if (props.trashTerms[term.en]) parts.push(t("panel.term_trashed", { n: props.trashTerms[term.en] }));
  return parts.join(" · ");
}

const suggestionTotals = computed(() => {
  const terms = props.inventory?.zoektermen || [];
  const counts = terms.map((term) => termCount(term.en));
  return {
    found: counts.reduce((a, b) => a + b, 0),
    terms: counts.filter(Boolean).length,
    trashed: terms.reduce((sum, term) => sum + (props.trashTerms[term.en] || 0), 0),
  };
});

function act(section, event, payload) {
  clicked = { section, at: Date.now() };
  emit(event, payload);
}
watch(
  () => props.busy,
  (busy) => {
    if (!busy) return;
    const recent = Date.now() - clicked.at < 1500;
    where.value = recent ? clicked.section : props.pointMode ? "point" : "top";
  }
);

function search() {
  if (prompt.value.trim()) act("search", "detect", { modus: "prompt", prompt: prompt.value.trim() });
}
</script>
