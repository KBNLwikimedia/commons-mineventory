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
      <!-- In the order of the work: (1) ask the AI what is on the image (one call), (2) its
           description, (3) the search terms: find where those things are, and what was found.
           Each part can be asked again (a call for that part only) or removed on its own.
           Explanations (cc-uitleg) look different from what the AI said (cc-ai-resultaat). -->
      <template v-if="!inventory">
        <p class="cc-uitleg">{{ t("panel.inventory_help") }} {{ museCost(config.muse.pagina_usd) }}</p>
        <detail-slider v-model="detail" :disabled="busy" />
        <div class="cc-knoppen">
          <cdx-button action="progressive" weight="primary" :disabled="busy" @click="act('inventory', 'inventory', { detailniveau: detail })">{{ t("panel.inventory") }}</cdx-button>
        </div>
        <busy-note v-if="busy && where === 'inventory'" :message="t('busy.muse_page')" />
      </template>
      <template v-else>
        <!-- (2) The AI's description of the image: editable, with its earlier versions (PageDescription.vue). -->
        <page-description
          :mid="file.mid"
          :n="page.n"
          :inventory="inventory"
          :busy="busy"
          :cost="museCost(config.muse.pagina_usd)"
          @changed="emit('inventory-changed', $event)"
          @again="act('beschrijving', 'inventory', { deel: 'beschrijving' })"
          @forget="act('beschrijving', 'forget-inventory', { deel: 'beschrijving' })"
        />
        <busy-note v-if="busy && where === 'beschrijving'" :message="t('busy.muse_page')" />

        <!-- (3) The search terms. -->
        <h4 class="cc-deel-kop">{{ t("panel.part_title_zoektermen") }}</h4>
        <template v-if="inventory.zoektermen?.length">
          <!-- What the terms are for: finding where on the image each thing is. -->
          <p class="cc-uitleg cc-termen-uitleg">
            {{ t("panel.terms_help") }} {{ cost(1) }} {{ t("panel.terms_choose") }}
            <button type="button" class="cc-link" :disabled="busy" @click="setExcluded([])">{{ t("panel.terms_all") }}</button>
            ·
            <button type="button" class="cc-link" :disabled="busy" @click="setExcluded(inventory.zoektermen.map((term) => term.en))">{{ t("panel.terms_none") }}</button>
            ·
            <button type="button" class="cc-link" :disabled="busy" @click="setExcluded(inventory.zoektermen.map((term) => term.en).filter((term) => !excluded.includes(term)))">{{ t("panel.terms_invert") }}</button>
          </p>
          <div class="cc-knoppen">
            <!-- Each term: a tick (does it go along with "Detect all"?) and the term itself (detect only this one). -->
            <span v-for="term in inventory.zoektermen" :key="term.en" class="cc-term" :class="{ 'cc-term-uit': excluded.includes(term.en) }">
              <input
                type="checkbox"
                class="cc-term-mee"
                :checked="!excluded.includes(term.en)"
                :disabled="busy"
                :aria-label="t('panel.term_include', { term: termLabel(term) })"
                :title="t('panel.term_include', { term: termLabel(term) })"
                @change="toggleTerm(term.en)"
              />
              <cdx-button
                action="progressive"
                size="small"
                :disabled="busy"
                :title="termTitle(term)"
                @click="act('suggestions', 'detect', { modus: 'prompt', prompt: term.en })"
              >
                {{ termLabel(term) }}
                <span v-if="termCount(term.en)" class="cc-term-aantal">{{ termCount(term.en) }}</span>
              </cdx-button>
            </span>
            <!-- The ticked terms in one go, right behind the terms themselves: the main action here. -->
            <cdx-button
              action="progressive"
              weight="primary"
              size="small"
              :disabled="busy || !includedTerms.length"
              @click="act('suggestions', 'detect', { modus: 'prompt', prompt: includedTerms.map((term) => term.en).join(', ') })"
            >
              {{ t(includedTerms.length === inventory.zoektermen.length ? "panel.detect_suggestions" : "panel.detect_chosen", { n: includedTerms.length }) }}
              <span class="cc-kosten">{{ cost(includedTerms.length) }}</span>
            </cdx-button>
          </div>
          <busy-note v-if="busy && where === 'suggestions'" :message="t('busy.sam')" />
          <cdx-message v-if="lastResult && resultAt === 'suggestions' && !busy" :type="lastResult.found || lastResult.excluded ? 'success' : 'warning'" :inline="true" class="cc-zoekresultaat">
            {{ resultText(lastResult) }}
            <!-- Nothing found: the other ways to get the object, as links to the sections below. -->
            <template v-if="isNone(lastResult)"> {{ t("panel.result_none_next") }}
            <button type="button" class="cc-link" @click="trySearch(lastResult)">{{ t("panel.result_try_search") }}</button>
            {{ t("panel.result_or") }}
            <button type="button" class="cc-link" @click="tryPoint">{{ t("panel.result_try_point") }}</button>.</template>
          </cdx-message>
          <!-- What of these suggestions is on the image now, and what went to the trash. -->
          <p class="cc-status">
            {{ t("panel.suggestions_found", { n: suggestionTotals.found, terms: suggestionTotals.terms, total: inventory.zoektermen.length }) }}
            <template v-if="suggestionTotals.trashed">{{ suggestionTotals.trashed === 1 ? t("panel.suggestions_trashed_one") : t("panel.suggestions_trashed", { n: suggestionTotals.trashed }) }}</template>
          </p>
        </template>
        <p v-else class="cc-uitleg">{{ t("panel.part_none_zoektermen") }}</p>
        <!-- Asking the search terms anew, at the level of detail chosen here. -->
        <detail-slider v-model="detail" :disabled="busy" />
        <div class="cc-deel-acties">
          <cdx-button action="progressive" weight="quiet" size="small" :disabled="busy" :title="t('panel.part_again_help_zoektermen')" @click="act('zoektermen', 'inventory', { deel: 'zoektermen', detailniveau: detail })">
            {{ t(inventory.zoektermen?.length ? "panel.part_again_zoektermen" : "panel.part_ask_zoektermen") }} <span class="cc-kosten">{{ museCost(config.muse.pagina_usd) }}</span>
          </cdx-button>
          <cdx-button v-if="inventory.zoektermen?.length" action="destructive" weight="quiet" size="small" :disabled="busy" @click="act('zoektermen', 'forget-inventory', { deel: 'zoektermen' })">
            <cdx-icon :icon="cdxIconTrash" size="small" /> {{ t("panel.part_forget") }}
          </cdx-button>
        </div>
        <busy-note v-if="busy && where === 'zoektermen'" :message="t('busy.muse_page')" />
        <p class="cc-uitleg">{{ t("panel.parts_help") }}</p>
      </template>
    </cdx-accordion>

    <cdx-accordion v-if="regionCount" v-model="open.commons">
      <template #title>{{ t("panel.from_commons") }} <info-dialog v-bind="info('commons', 'panel.from_commons')" /></template>
      <p class="cc-uitleg">{{ t("panel.from_commons_help") }}</p>
      <cdx-button action="progressive" :disabled="busy" @click="act('commons', 'detect', { modus: 'commons' })">
        {{ t("panel.regions_button", { n: regionCount }) }}
      </cdx-button>
      <busy-note v-if="busy && where === 'commons'" :message="t('busy.commons')" />
      <cdx-message v-if="lastResult && resultAt === 'commons' && !busy" :type="lastResult.found || lastResult.excluded ? 'success' : 'warning'" :inline="true" class="cc-zoekresultaat">{{ resultText(lastResult) }}</cdx-message>
    </cdx-accordion>

    <cdx-accordion v-model="open.search">
      <template #title>{{ t("panel.search") }} <info-dialog v-bind="info('search', 'panel.search')" /></template>
      <form class="cc-zoek" @submit.prevent="search">
        <cdx-text-input v-model="prompt" :placeholder="t('panel.search_placeholder')" :aria-label="t('panel.search')" />
        <cdx-button type="submit" action="progressive" :disabled="busy || !prompt.trim()">{{ t("panel.search_button") }}</cdx-button>
      </form>
      <busy-note v-if="busy && where === 'search'" :message="t('busy.sam')" />
      <cdx-message v-if="lastResult && resultAt === 'search' && !busy" :type="lastResult.found || lastResult.excluded ? 'success' : 'warning'" :inline="true" class="cc-zoekresultaat">
            {{ resultText(lastResult) }}
            <!-- Nothing found: the other ways to get the object, as links to the sections below. -->
            <template v-if="isNone(lastResult)"> {{ t("panel.result_none_next") }}
            <button type="button" class="cc-link" @click="trySearch(lastResult)">{{ t("panel.result_try_search") }}</button>
            {{ t("panel.result_or") }}
            <button type="button" class="cc-link" @click="tryPoint">{{ t("panel.result_try_point") }}</button>.</template>
          </cdx-message>
      <p class="cc-uitleg">{{ t("panel.search_help") }} {{ cost(1) }}</p>
    </cdx-accordion>

    <!-- Point or draw: two ways to choose one object yourself; one of the two switches at a time. -->
    <cdx-accordion v-model="open.point" class="cc-sectie-aanwijzen">
      <template #title>{{ t("panel.point_or_draw") }} <info-dialog v-bind="info('point', 'panel.point_or_draw')" /></template>
      <div class="cc-modus-keuze">
        <cdx-toggle-switch :model-value="pointMode" @update:model-value="emit('point-mode', $event)">
          {{ t("panel.point_switch") }}
        </cdx-toggle-switch>
        <p class="cc-uitleg">{{ t("panel.point_help") }} {{ cost(1) }}</p>
        <busy-note v-if="busy && where === 'point'" :message="t('busy.sam')" />
        <cdx-message v-if="lastResult && resultAt === 'point' && !busy && lastResult.modus === 'punt'" :type="lastResult.outcome === 'niets' ? 'warning' : 'success'" :inline="true" class="cc-zoekresultaat">{{ resultText(lastResult) }}</cdx-message>
      </div>
      <div class="cc-modus-keuze">
        <cdx-toggle-switch :model-value="drawMode" @update:model-value="emit('draw-mode', $event)">
          {{ t("panel.draw_switch") }}
        </cdx-toggle-switch>
        <p class="cc-uitleg">{{ t("panel.draw_help") }} {{ t("panel.free") }}</p>
        <cdx-message v-if="lastResult && resultAt === 'point' && lastResult.modus === 'rechthoek'" type="success" :inline="true" class="cc-zoekresultaat">{{ resultText(lastResult) }}</cdx-message>
      </div>
    </cdx-accordion>

    <!-- CropTool: the usual tool for cropping on Commons, for the whole file (single images only). -->
    <cdx-accordion v-if="cropTool" v-model="open.croptool">
      <!-- The CropTool2 logo is the Codex "cut" icon, so it is the same here. -->
      <template #title><cdx-icon :icon="cdxIconCut" size="small" class="cc-croptool-logo" /> {{ t("panel.croptool") }} <info-dialog v-bind="info('croptool', 'panel.croptool')" /></template>
      <p class="cc-uitleg">{{ t("panel.croptool_help") }}</p>
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
import { computed, inject, nextTick, reactive, ref, watch } from "vue";
import { CdxAccordion, CdxButton, CdxIcon, CdxMessage, CdxTextInput, CdxToggleSwitch } from "@wikimedia/codex";
import { cdxIconCut, cdxIconLinkExternal, cdxIconTrash } from "@wikimedia/codex-icons";
import { textParts } from "../confirm.js";
import { money, useT } from "../i18n.js";
import { cropToolLink } from "../state.js";
import AiBadge from "./AiBadge.vue";
import BusyNote from "./BusyNote.vue";
import DetailSlider from "./DetailSlider.vue";
import PageDescription from "./PageDescription.vue";
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
  // The outcome of the last detection: shown in the section whose button asked for it.
  lastResult: { type: Object, default: null },
});
const emit = defineEmits(["detect", "inventory", "inventory-changed", "forget-inventory", "point-mode", "draw-mode"]);
const t = useT();
const config = inject("config");
// The two models in the live-mode line link to Meta's own pages. Muse Spark
// has no homepage of its own; its section in the model overview is the closest.
const modelLinks = {
  sam: { href: "https://ai.meta.com/sam3/", label: config.sam_model },
  muse: { href: "https://dev.meta.ai/docs/models#muse-spark", label: "Muse Spark" },
};
const prompt = ref("");
// The level of detail of the search terms: that of the overview, else the last one chosen in this browser.
const DETAIL_KEY = "cc-detailniveau";
function storedDetail() {
  try {
    return window.localStorage.getItem(DETAIL_KEY) || "normaal";
  } catch {
    return "normaal";
  }
}
const detail = ref(props.inventory?.detailniveau || storedDetail());
watch(
  () => props.inventory?.detailniveau,
  (level) => {
    if (level) detail.value = level;
  }
);
watch(detail, (level) => {
  try {
    window.localStorage.setItem(DETAIL_KEY, level);
  } catch {
    // Blocked storage: the level holds until the page is reloaded.
  }
});
// The (i) beside each section title: a popup that explains what the section does.
function info(section, titleKey) {
  return {
    title: t(titleKey),
    label: t("panel.info_label", { section: t(titleKey) }),
    paragraphs: [1, 2, 3].map((n) => t(`panel.info_${section}_${n}`)).filter((text) => !text.startsWith("panel.")),
  };
}
const open = reactive({ commons: true, search: false, suggestions: true, point: false, croptool: false });
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

const termLabel = (term) => (config.taal === "nl" ? term.nl : term.en);

// Terms left out of "Detect all" (by their English term), per file and page,
// remembered in this browser only (a convenience; nothing is stored on the server).
const excluded = ref([]);
const storageKey = computed(() => `cc-termen-uit:${props.file.mid}:${props.page.n}`);
watch(
  storageKey,
  (key) => {
    try {
      excluded.value = JSON.parse(window.localStorage.getItem(key) || "[]");
    } catch {
      excluded.value = [];
    }
  },
  { immediate: true }
);
function setExcluded(terms) {
  excluded.value = [...new Set(terms)];
  try {
    window.localStorage.setItem(storageKey.value, JSON.stringify(excluded.value));
  } catch {
    // Blocked storage: the choice holds until the page is reloaded.
  }
}
function toggleTerm(term) {
  setExcluded(excluded.value.includes(term) ? excluded.value.filter((t2) => t2 !== term) : [...excluded.value, term]);
}
const includedTerms = computed(() => (props.inventory?.zoektermen || []).filter((term) => !excluded.value.includes(term.en)));

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

// Which section shows the last outcome: the one clicked last before it came.
const resultAt = ref(null);
watch(
  () => props.lastResult,
  (result) => {
    resultAt.value = result ? result.section || clicked.section : null;
  }
);
watch(() => [props.file.mid, props.page.n], () => (resultAt.value = null));
function resultText(result) {
  // Pointing and drawing: about one object.
  if (result.modus === "punt") {
    if (result.outcome === "niets") return t("panel.result_point_none");
    return t(result.outcome === "bekend" ? "panel.result_point_known" : "panel.result_point_new", { name: result.name });
  }
  if (result.modus === "rechthoek") return t("panel.result_rectangle", { name: result.name });
  const terms = result.prompt.split(",").map((s) => s.trim()).filter(Boolean);
  const what = result.modus === "commons" ? t("panel.result_commons") : terms.length > 1 ? t("panel.result_terms", { n: terms.length }) : t("panel.result_term", { term: terms[0] || "" });
  if (!result.found && !result.excluded) return t("panel.result_none", { what });
  const found = result.found === 1 ? t("panel.result_one", { what }) : t("panel.result_found", { n: result.found, what });
  return result.excluded ? `${found} ${t("panel.result_excluded", { n: result.excluded })}` : found;
}

// A search with terms that found nothing (not "from Commons", pointing or drawing).
function isNone(result) {
  return Boolean(result) && result.modus === "prompt" && !result.found && !result.excluded;
}
// After nothing was found: open Search with the term filled in, ready to change it.
async function trySearch(result) {
  open.search = true;
  prompt.value = result.prompt.split(",").length === 1 ? result.prompt.trim() : "";
  await nextTick();
  const input = document.querySelector(".cc-zoek input");
  input?.scrollIntoView({ block: "center", behavior: "smooth" });
  input?.focus();
  input?.select();
}
// Or open Point or draw, to point at the object or draw a rectangle around it.
async function tryPoint() {
  open.point = true;
  await nextTick();
  document.querySelector(".cc-sectie-aanwijzen")?.scrollIntoView({ block: "center", behavior: "smooth" });
}

function search() {
  if (prompt.value.trim()) act("search", "detect", { modus: "prompt", prompt: prompt.value.trim() });
}
</script>
