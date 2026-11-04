<!--
  The detection panel (functional design 7 and 10.4): suggestions for this
  page, regions from Commons, search, point or draw, bulk and CropTool
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
      <template #title>{{ t("panel.suggestions") }} <info-dialog v-bind="info('suggestions', 'panel.suggestions')" /></template>
      <template v-if="inventory">
        <!-- Dutch, and English below it in italics, as in the magnifier (overviews from before 0.8 have only Dutch). -->
        <p class="cc-klein">
          {{ inventory.paginasoort }} — {{ inventory.samenvatting }}
          <template v-if="inventory.samenvatting_en"><br /><i>{{ inventory.paginasoort_en }} — {{ inventory.samenvatting_en }}</i></template>
          <ai-badge kind="pagina" :model="inventory.model" />
        </p>
        <!-- The text the model read in and under the image (overviews since 0.16 only). -->
        <div v-if="inventory.tekst" class="cc-klein cc-inventaris-tekst">
          <strong>{{ t("panel.inventory_text") }}</strong>
          <blockquote>{{ inventory.tekst }}</blockquote>
        </div>
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
      <template #title>{{ t("panel.from_commons") }} <info-dialog v-bind="info('commons', 'panel.from_commons')" /></template>
      <p class="cc-klein">{{ t("panel.from_commons_help") }}</p>
      <cdx-button action="progressive" :disabled="busy" @click="act('commons', 'detect', { modus: 'commons' })">
        {{ t("panel.regions_button", { n: regionCount }) }}
      </cdx-button>
      <busy-note v-if="busy && where === 'commons'" :message="t('busy.commons')" />
    </cdx-accordion>

    <cdx-accordion v-model="open.search">
      <template #title>{{ t("panel.search") }} <info-dialog v-bind="info('search', 'panel.search')" /></template>
      <form class="cc-zoek" @submit.prevent="search">
        <cdx-text-input v-model="prompt" :placeholder="t('panel.search_placeholder')" :aria-label="t('panel.search')" />
        <cdx-button type="submit" action="progressive" :disabled="busy || !prompt.trim()">{{ t("panel.search_button") }}</cdx-button>
      </form>
      <busy-note v-if="busy && where === 'search'" :message="t('busy.sam')" />
      <p class="cc-klein">{{ t("panel.search_help") }} {{ cost(1) }}</p>
    </cdx-accordion>

    <!-- Point or draw: two ways to choose one object yourself; one of the two switches at a time. -->
    <cdx-accordion v-model="open.point">
      <template #title>{{ t("panel.point_or_draw") }} <info-dialog v-bind="info('point', 'panel.point_or_draw')" /></template>
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
      <template #title>{{ t("panel.bulk") }} <info-dialog v-bind="info('bulk', 'panel.bulk')" /></template>
      <div class="cc-knoppen cc-knoppen-rij">
        <!-- Only usable when there is something to do: ticked objects without a description, or two objects or more. -->
        <cdx-button action="progressive" :disabled="busy || !toDescribe" @click="act('bulk', 'describe-all')">
          {{ t("panel.describe_all") }}<template v-if="toDescribe"> ({{ toDescribe }})</template>
        </cdx-button>
        <cdx-button action="progressive" :disabled="busy || objects.length < 2" @click="act('bulk', 'merge')">{{ t("panel.merge") }}</cdx-button>
      </div>
      <p v-if="!toDescribe || objects.length < 2" class="cc-klein">
        {{ objects.length < 2 ? t("panel.bulk_hint_objects") : t("panel.bulk_hint_select") }}
      </p>
      <busy-note v-if="busy && where === 'bulk'" :message="t('busy.general')" />
    </cdx-accordion>

    <!-- CropTool: the usual tool for cropping on Commons, for the whole file (single images only). -->
    <cdx-accordion v-if="cropTool" v-model="open.croptool">
      <!-- The CropTool2 logo is the Codex "cut" icon, so it is the same here. -->
      <template #title><cdx-icon :icon="cdxIconCut" size="small" class="cc-croptool-logo" /> {{ t("panel.croptool") }} <info-dialog v-bind="info('croptool', 'panel.croptool')" /></template>
      <p class="cc-klein">{{ t("panel.croptool_help") }}</p>
      <a
        class="cdx-button cdx-button--fake-button cdx-button--fake-button--enabled cdx-button--action-progressive"
        :href="cropTool"
        target="_blank"
        rel="noopener"
      ><cdx-icon :icon="cdxIconCut" /> {{ t("panel.croptool_button") }} <cdx-icon :icon="cdxIconLinkExternal" size="small" /></a>
    </cdx-accordion>
  </div>
</template>

<script setup>
import { computed, inject, reactive, ref, watch } from "vue";
import { CdxAccordion, CdxButton, CdxIcon, CdxTextInput, CdxToggleSwitch } from "@wikimedia/codex";
import { cdxIconCut, cdxIconLinkExternal } from "@wikimedia/codex-icons";
import { textParts } from "../confirm.js";
import { money, useT } from "../i18n.js";
import { cropToolLink } from "../state.js";
import AiBadge from "./AiBadge.vue";
import BusyNote from "./BusyNote.vue";
import InfoDialog from "./InfoDialog.vue";

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
const emit = defineEmits(["detect", "inventory", "merge", "describe-all", "point-mode", "draw-mode"]);
// Ticked objects that have no description yet: what "Describe selection" would describe.
const toDescribe = computed(() => props.objects.filter((o) => o.status === "geselecteerd" && !o.beschrijving).length);
const t = useT();
const config = inject("config");
// The two models in the live-mode line link to Meta's own pages. Muse Spark
// has no homepage of its own; its section in the model overview is the closest.
const modelLinks = {
  sam: { href: "https://ai.meta.com/sam3/", label: config.sam_model },
  muse: { href: "https://dev.meta.ai/docs/models#muse-spark", label: "Muse Spark" },
};
const prompt = ref("");
// The (i) beside each section title: a popup that explains what the section does.
function info(section, titleKey) {
  return {
    title: t(titleKey),
    label: t("panel.info_label", { section: t(titleKey) }),
    paragraphs: [1, 2, 3].map((n) => t(`panel.info_${section}_${n}`)).filter((text) => !text.startsWith("panel.")),
  };
}
const open = reactive({ commons: true, search: false, suggestions: true, point: false, bulk: false, croptool: false });
const cropTool = computed(() => cropToolLink(props.file));
const regionCount = computed(() => props.page.regio_aantal + props.page.notitie_aantal);

const cost = (calls) => (config.betaald ? `(${money(calls * config.sam_usd, config.taal)})` : t("panel.free"));
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
