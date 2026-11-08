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

    <!-- From Commons comes first (wish Olaf, 6-11-2026): what people already put on Commons
         goes before new AI suggestions, and it is free to read. Only when the file has
         captions, depicts, regions or notes (they always refer to page 1). Backlog 26. -->
    <cdx-accordion v-if="hasCommonsData" v-model="open.commons">
      <template #title>{{ t("panel.from_commons") }} <info-dialog v-bind="info('commons', 'panel.from_commons')" /></template>
      <p class="cc-uitleg">{{ t("panel.from_commons_intro") }} <a :href="sdcLink" target="_blank" rel="noopener">{{ t("panel.commons_edit_link") }}</a></p>
      <!-- What the app read is kept a day: read again after adding something on Commons. -->
      <p class="cc-uitleg">
        <button type="button" class="cc-link" :disabled="busy" :title="t('panel.commons_read_again_help')" @click="act('commons-lezen', 'read-again')">{{ t("panel.commons_read_again") }}</button>
      </p>
      <busy-note v-if="busy && where === 'commons-lezen'" :message="t('busy.general')" />

      <!-- (1) The captions on Commons: read only. -->
      <cdx-accordion v-if="commonsCaptions.length" v-model="open.captions" class="cc-deel-uitklap">
        <template #title>{{ t("panel.commons_captions") }}</template>
        <ul class="cc-commons-captions">
          <li v-for="caption in commonsCaptions" :key="caption.lang"><span class="cc-taal-code">{{ caption.lang }}</span> {{ caption.text }}</li>
        </ul>
      </cdx-accordion>

      <!-- (2) Regions (depicts with a position) and file notes: free objects. -->
      <cdx-accordion v-if="regionCount" v-model="open.regios" class="cc-deel-uitklap">
        <template #title>{{ t("panel.commons_regions") }}</template>
        <p class="cc-uitleg">{{ t("panel.from_commons_help") }}</p>
        <cdx-button action="progressive" :disabled="busy" @click="act('commons', 'detect', { modus: 'commons' })">
          {{ t("panel.regions_button", { n: regionCount }) }}
        </cdx-button>
        <busy-note v-if="busy && where === 'commons'" :message="t('busy.commons')" />
        <cdx-message v-if="lastResult && resultAt === 'commons' && !busy" :type="resultType(lastResult)" :allow-user-dismiss="true" :dismiss-button-label="t('actions.close')" class="cc-zoekresultaat" @user-dismissed="emit('dismiss-result')">{{ resultText(lastResult) }}</cdx-message>
      </cdx-accordion>

      <!-- (3) Depicts without a position: a chip per item; a click lets SAM find it (paid),
           and what is found gets that item as its depicts. The search word can be changed. -->
      <cdx-accordion v-if="commonsDepicts.length" v-model="open.beeldtaf" class="cc-deel-uitklap">
        <template #title>{{ t("panel.commons_depicts", { n: commonsDepicts.length }) }}</template>
        <!-- The explanation as a short list (wish Olaf). -->
        <div class="cc-uitleg cc-termen-uitleg">
          <p>
            {{ t("panel.commons_depicts_intro_before") }}
            (<a href="https://www.wikidata.org/wiki/Property:P180" target="_blank" rel="noopener">P180</a>)
            {{ t("panel.commons_depicts_intro_after") }}
          </p>
          <ul class="cc-uitleg-lijst">
            <li><strong>{{ t("panel.commons_depicts_single") }}</strong> {{ t("panel.commons_depicts_click") }}</li>
            <li>
              <strong>{{ t("panel.commons_depicts_bulk") }}</strong> {{ t("panel.commons_depicts_untick") }}
              <button type="button" class="cc-link" :disabled="busy" @click="setExcludedItems([])">{{ t("panel.terms_all") }}</button>
              ·
              <button type="button" class="cc-link" :disabled="busy" @click="setExcludedItems(commonsDepicts.map((item) => item.q))">{{ t("panel.terms_none") }}</button>
              ·
              <button type="button" class="cc-link" :disabled="busy" @click="setExcludedItems(commonsDepicts.map((item) => item.q).filter((q) => !excludedItems.includes(q)))">{{ t("panel.terms_invert") }}</button>
            </li>
            <li><strong>{{ t("panel.commons_depicts_search_word") }}</strong> {{ t("panel.commons_depicts_pencil") }}</li>
            <li><strong>{{ t("panel.commons_depicts_results") }}</strong> {{ t("panel.terms_colours") }}</li>
            <li>
              <strong>{{ t("panel.commons_depicts_new_region") }}</strong> {{ t("panel.commons_depicts_new_region_go") }}
              <button type="button" class="cc-link" @click="showPointOrDraw">{{ t("panel.point_or_draw") }}</button>.
            </li>
          </ul>
        </div>
        <div class="cc-knoppen">
          <span v-for="item in commonsDepicts" :key="item.q" class="cc-term" :class="{ 'cc-term-uit': excludedItems.includes(item.q), ...resultClass(itemCount(item.q), itemWord(item)) }">
            <input
              type="checkbox"
              class="cc-term-mee"
              :checked="!excludedItems.includes(item.q)"
              :disabled="busy"
              :aria-label="t('panel.term_include', { term: item.label })"
              :title="t('panel.term_include', { term: item.label })"
              @change="toggleItem(item.q)"
            />
            <input
              v-if="editingItem === item.q"
              ref="itemInput"
              v-model="itemDraft"
              class="cc-term-veld"
              :aria-label="t('panel.commons_depicts_word', { item: item.label })"
              @keydown.enter.prevent="saveItemWord(item)"
              @keydown.esc.prevent="editingItem = null"
              @blur="saveItemWord(item)"
            />
            <cdx-button
              v-else
              action="progressive"
              size="small"
              :disabled="busy"
              :title="itemTitle(item)"
              @click="act('commons-depicts', 'detect', { modus: 'prompt', prompt: itemWord(item), items: { [itemWord(item)]: item.q } })"
            >
              <!-- Your own search word when you changed it (wish Olaf); the item stays in the tooltip. -->
              {{ itemWords[item.q] ? itemWord(item) : item.label }}
              <span v-if="itemCount(item.q) || wasSearched(itemWord(item))" class="cc-term-aantal">{{ itemCount(item.q) }}</span>
            </cdx-button>
            <cdx-button
              v-if="editingItem !== item.q"
              action="progressive"
              weight="quiet"
              size="small"
              class="cc-term-potlood"
              :disabled="busy"
              :aria-label="t('panel.commons_depicts_word', { item: item.label })"
              :title="t('panel.commons_depicts_word', { item: item.label })"
              @click="startItemWord(item)"
            >
              <cdx-icon :icon="cdxIconEdit" size="small" />
            </cdx-button>
          </span>
          <cdx-button
            action="progressive"
            weight="primary"
            size="small"
            :disabled="busy || !includedItems.length"
            @click="act('commons-depicts', 'detect', { modus: 'prompt', prompt: includedItems.map(itemWord).join(', '), items: Object.fromEntries(includedItems.map((item) => [itemWord(item), item.q])) })"
          >
            {{ t(includedItems.length === commonsDepicts.length ? "panel.commons_depicts_all" : "panel.detect_chosen", { n: includedItems.length }) }}
            <span class="cc-kosten">{{ cost(includedItems.length) }}</span>
          </cdx-button>
        </div>
        <busy-note v-if="busy && where === 'commons-depicts'" :message="t('busy.sam')" />
        <cdx-message v-if="lastResult && resultAt === 'commons-depicts' && !busy" :type="resultType(lastResult)" :allow-user-dismiss="true" :dismiss-button-label="t('actions.close')" class="cc-zoekresultaat" @user-dismissed="emit('dismiss-result')">{{ resultText(lastResult) }}</cdx-message>
      </cdx-accordion>
    </cdx-accordion>

    <!-- Then the AI suggestions: they fit this image, unlike a fixed list. -->
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
        <!-- (2) The AI's description of the image: editable, with its earlier versions (PageDescription.vue).
             Each of the two parts folds away on its own (wish Olaf). -->
        <cdx-accordion v-model="open.beschrijving" class="cc-deel-uitklap">
          <template #title>{{ t("panel.part_title_beschrijving") }}</template>
        <page-description
          :mid="file.mid"
          :n="page.n"
          :inventory="inventory"
          :busy="busy"
          :cost="museCost(config.muse.pagina_usd)"
          @changed="emit('inventory-changed', $event)"
          @again="act('beschrijving', 'inventory', { deel: 'beschrijving', beschrijvingsniveau: $event })"
          @forget="act('beschrijving', 'forget-inventory', { deel: 'beschrijving' })"
        />
        <busy-note v-if="busy && where === 'beschrijving'" :message="t('busy.muse_page')" />
        </cdx-accordion>

        <!-- (3) The search terms. -->
        <cdx-accordion v-model="open.zoektermen" class="cc-deel-uitklap">
          <template #title>{{ t("panel.part_title_zoektermen") }}</template>
        <!-- First what makes the search terms (the level of detail, asking anew, removing), compact
             on one line; under it the terms themselves, the result of that (wish Olaf). -->
        <div class="cc-termen-bron">
          <detail-slider v-model="detail" :disabled="busy" compact />
          <!-- Always side by side, under the slider: ask anew, and remove all. -->
          <div class="cc-termen-knoppen">
          <cdx-button action="progressive" weight="quiet" size="small" :disabled="busy" :title="`${t('panel.part_again_help_zoektermen')} ${t('panel.parts_help')}`" @click="act('zoektermen', 'inventory', { deel: 'zoektermen', detailniveau: detail })">
            {{ t(inventory.zoektermen?.length ? "panel.part_again_zoektermen" : "panel.part_ask_zoektermen") }} <span class="cc-kosten">{{ museCost(config.muse.pagina_usd) }}</span>
          </cdx-button>
          <cdx-button v-if="inventory.zoektermen?.length" action="destructive" weight="quiet" size="small" :disabled="busy" @click="act('zoektermen', 'forget-inventory', { deel: 'zoektermen' })">
            <cdx-icon :icon="cdxIconTrash" size="small" /> {{ t("panel.part_forget_zoektermen_button") }}
          </cdx-button>
          </div>
        </div>
        <busy-note v-if="busy && where === 'zoektermen'" :message="t('busy.muse_page')" />
        <template v-if="inventory.zoektermen?.length">
          <!-- What the terms are for: finding where on the image each thing is. -->
          <p class="cc-uitleg cc-termen-uitleg">
            {{ t("panel.terms_help") }} {{ cost(1) }} {{ t("panel.terms_pencil") }} {{ t("panel.terms_colours") }} {{ t("panel.terms_choose") }}
            <button type="button" class="cc-link" :disabled="busy" @click="setExcluded([])">{{ t("panel.terms_all") }}</button>
            ·
            <button type="button" class="cc-link" :disabled="busy" @click="setExcluded(inventory.zoektermen.map((term) => term.en))">{{ t("panel.terms_none") }}</button>
            ·
            <button type="button" class="cc-link" :disabled="busy" @click="setExcluded(inventory.zoektermen.map((term) => term.en).filter((term) => !excluded.includes(term)))">{{ t("panel.terms_invert") }}</button>
          </p>
          <div class="cc-knoppen">
            <!-- Each term: a tick (does it go along with "Detect all"?) and the term itself (detect only this one). -->
            <span v-for="term in inventory.zoektermen" :key="term.en" class="cc-term" :class="{ 'cc-term-uit': excluded.includes(term.en), ...resultClass(termHits(term), termWord(term)) }">
              <input
                type="checkbox"
                class="cc-term-mee"
                :checked="!excluded.includes(term.en)"
                :disabled="busy"
                :aria-label="t('panel.term_include', { term: termLabel(term) })"
                :title="t('panel.term_include', { term: termLabel(term) })"
                @change="toggleTerm(term.en)"
              />
              <!-- The search word can be changed with the pencil, as for the depicts items (wish Olaf). -->
              <input
                v-if="editingTerm === term.en"
                ref="termInput"
                v-model="termDraft"
                class="cc-term-veld"
                :aria-label="t('panel.term_word', { term: termLabel(term) })"
                @keydown.enter.prevent="saveTermWord(term)"
                @keydown.esc.prevent="editingTerm = null"
                @blur="saveTermWord(term)"
              />
              <cdx-button
                v-else
                action="progressive"
                size="small"
                :disabled="busy"
                :title="termTitle(term)"
                @click="act('suggestions', 'detect', { modus: 'prompt', prompt: termWord(term) })"
              >
                {{ termWords[term.en] || termLabel(term) }}
                <span v-if="termHits(term) || wasSearched(termWord(term))" class="cc-term-aantal">{{ termHits(term) }}</span>
                <span v-if="onCommons(term)" class="cc-term-op-commons" :title="t('panel.term_on_commons_help')">{{ t("panel.term_on_commons") }}</span>
              </cdx-button>
              <cdx-button
                v-if="editingTerm !== term.en"
                action="progressive"
                weight="quiet"
                size="small"
                class="cc-term-potlood"
                :disabled="busy"
                :aria-label="t('panel.term_word', { term: termLabel(term) })"
                :title="t('panel.term_word', { term: termLabel(term) })"
                @click="startTermWord(term)"
              >
                <cdx-icon :icon="cdxIconEdit" size="small" />
              </cdx-button>
            </span>
            <!-- The ticked terms in one go, right behind the terms themselves: the main action here. -->
            <cdx-button
              action="progressive"
              weight="primary"
              size="small"
              :disabled="busy || !includedTerms.length"
              @click="act('suggestions', 'detect', { modus: 'prompt', prompt: includedTerms.map(termWord).join(', ') })"
            >
              {{ t(includedTerms.length === inventory.zoektermen.length ? "panel.detect_suggestions" : "panel.detect_chosen", { n: includedTerms.length }) }}
              <span class="cc-kosten">{{ cost(includedTerms.length) }}</span>
            </cdx-button>
          </div>
          <busy-note v-if="busy && where === 'suggestions'" :message="t('busy.sam')" />
          <cdx-message v-if="lastResult && resultAt === 'suggestions' && !busy" :type="resultType(lastResult)" :allow-user-dismiss="true" :dismiss-button-label="t('actions.close')" class="cc-zoekresultaat" @user-dismissed="emit('dismiss-result')">
            {{ resultText(lastResult) }}
            <!-- Nothing found: the other ways to get the object, as links to the sections below. -->
            <template v-if="isNone(lastResult)"> {{ t("panel.result_none_next") }}
              <ul class="cc-andere-weg">
                <li><button type="button" class="cc-link" @click="trySearch(lastResult)">{{ t("panel.result_try_search") }}</button></li>
                <li><button type="button" class="cc-link" @click="tryPoint('point')">{{ t("panel.result_try_point") }}</button></li>
                <li><button type="button" class="cc-link" @click="tryPoint('draw')">{{ t("panel.result_try_draw") }}</button></li>
              </ul>
            </template>
          </cdx-message>
          <!-- What of these suggestions is on the image now, and what went to the trash. -->
          <p class="cc-status">
            {{ t("panel.suggestions_found", { n: suggestionTotals.found, terms: suggestionTotals.terms, total: inventory.zoektermen.length }) }}
            <template v-if="suggestionTotals.trashed">{{ suggestionTotals.trashed === 1 ? t("panel.suggestions_trashed_one") : t("panel.suggestions_trashed", { n: suggestionTotals.trashed }) }}</template>
          </p>
        </template>
        <p v-else class="cc-uitleg">{{ t("panel.part_none_zoektermen") }}</p>
        </cdx-accordion>
      </template>
      <!-- Depicts and captions for the whole image (FO 9.7): a window of its own, so this
           block does not get too full. Blue but not filled: detecting stays the main action.
           Disabled for files with more pages, where the data belongs to the whole file. -->
      <div class="cc-origineel-knop">
        <cdx-button action="progressive" :disabled="busy || file.paginas > 1" :title="file.paginas > 1 ? t('original.button_pages') : t('original.button_help')" @click="originalOpen = true">
          {{ t("original.button") }}
        </cdx-button>
        <p class="cc-uitleg">{{ file.paginas > 1 ? t("original.button_pages") : t("original.button_help") }}</p>
      </div>
      <original-data
        v-if="originalOpen"
        :open="originalOpen"
        :file="file"
        :page="page"
        :inventory="inventory"
        :busy="busy"
        :cost="museCost(config.muse.pagina_usd)"
        @ask-caption="emit('inventory', { deel: 'beschrijving', beschrijvingsniveau: 'caption' })"
        @close="originalOpen = false"
      />
    </cdx-accordion>

    <cdx-accordion v-model="open.search">
      <template #title>{{ t("panel.search") }} <info-dialog v-bind="info('search', 'panel.search')" /></template>
      <form class="cc-zoek" @submit.prevent="search">
        <cdx-text-input v-model="prompt" :placeholder="t('panel.search_placeholder')" :aria-label="t('panel.search')" />
        <cdx-button type="submit" action="progressive" :disabled="busy || !prompt.trim()">{{ t("panel.search_button") }}</cdx-button>
      </form>
      <busy-note v-if="busy && where === 'search'" :message="t('busy.sam')" />
      <cdx-message v-if="lastResult && resultAt === 'search' && !busy" :type="resultType(lastResult)" :allow-user-dismiss="true" :dismiss-button-label="t('actions.close')" class="cc-zoekresultaat" @user-dismissed="emit('dismiss-result')">
            {{ resultText(lastResult) }}
            <!-- Nothing found: the other ways to get the object, as links to the sections below. -->
            <template v-if="isNone(lastResult)"> {{ t("panel.result_none_next") }}
              <ul class="cc-andere-weg">
                <li><button type="button" class="cc-link" @click="trySearch(lastResult)">{{ t("panel.result_try_search") }}</button></li>
                <li><button type="button" class="cc-link" @click="tryPoint('point')">{{ t("panel.result_try_point") }}</button></li>
                <li><button type="button" class="cc-link" @click="tryPoint('draw')">{{ t("panel.result_try_draw") }}</button></li>
              </ul>
            </template>
          </cdx-message>
      <p class="cc-uitleg">{{ t("panel.search_help") }} {{ cost(1) }}</p>
    </cdx-accordion>

    <!-- Point or draw: two ways to choose one object yourself; one of the two switches at a time. -->
    <cdx-accordion v-model="open.point" class="cc-sectie-aanwijzen">
      <template #title>{{ t("panel.point_or_draw") }} <info-dialog v-bind="info('point', 'panel.point_or_draw')" /></template>
      <!-- Two ways, each folding away on its own, as in the AI suggestions (wish Olaf). -->
      <cdx-accordion v-model="open.aanwijzen" class="cc-deel-uitklap">
        <template #title>{{ t("panel.part_title_point") }}</template>
      <div class="cc-modus-keuze">
        <cdx-toggle-switch :model-value="pointMode" @update:model-value="emit('point-mode', $event)">
          {{ t("panel.point_switch") }}
        </cdx-toggle-switch>
        <p class="cc-uitleg">{{ t("panel.point_help") }} {{ cost(1) }}</p>
        <busy-note v-if="busy && where === 'point'" :message="t('busy.sam')" />
        <cdx-message v-if="lastResult && resultAt === 'point' && !busy && lastResult.modus === 'punt'" :type="lastResult.outcome === 'niets' ? 'warning' : 'success'" :allow-user-dismiss="true" :dismiss-button-label="t('actions.close')" class="cc-zoekresultaat" @user-dismissed="emit('dismiss-result')">{{ resultText(lastResult) }}</cdx-message>
      </div>
      </cdx-accordion>
      <cdx-accordion v-model="open.tekenen" class="cc-deel-uitklap">
        <template #title>{{ t("panel.part_title_draw") }}</template>
      <div class="cc-modus-keuze">
        <cdx-toggle-switch :model-value="drawMode" @update:model-value="emit('draw-mode', $event)">
          {{ t("panel.draw_switch") }}
        </cdx-toggle-switch>
        <p class="cc-uitleg">{{ t("panel.draw_help") }} {{ t("panel.free") }}</p>
        <cdx-message v-if="lastResult && resultAt === 'point' && lastResult.modus === 'rechthoek'" type="success" :allow-user-dismiss="true" :dismiss-button-label="t('actions.close')" class="cc-zoekresultaat" @user-dismissed="emit('dismiss-result')">{{ resultText(lastResult) }}</cdx-message>
      </div>
      </cdx-accordion>
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
import { cdxIconCut, cdxIconEdit, cdxIconLinkExternal, cdxIconTrash } from "@wikimedia/codex-icons";
import { textParts } from "../confirm.js";
import { money, useT } from "../i18n.js";
import { cropToolLink } from "../state.js";
import AiBadge from "./AiBadge.vue";
import BusyNote from "./BusyNote.vue";
import DetailSlider from "./DetailSlider.vue";
import PageDescription from "./PageDescription.vue";
import InfoDialog from "./InfoDialog.vue";
import OriginalData from "./OriginalData.vue";

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
const emit = defineEmits(["detect", "inventory", "inventory-changed", "forget-inventory", "point-mode", "draw-mode", "dismiss-result", "read-again"]);
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
    paragraphs: [1, 2, 3, 4, 5, 6, 7, 8].map((n) => t(`panel.info_${section}_${n}`)).filter((text) => !text.startsWith("panel.")),
  };
}
const open = reactive({ captions: true, regios: true, beeldtaf: true, commons: true, search: false, suggestions: true, beschrijving: true, zoektermen: true, aanwijzen: true, tekenen: true, point: false, croptool: false });
const cropTool = computed(() => cropToolLink(props.file));
const regionCount = computed(() => props.page.regio_aantal + props.page.notitie_aantal);
// The window "Gegevens van deze afbeelding" (9.7).
const originalOpen = ref(false);

// What the file already has on Commons (backlog 26): captions and depicts without a
// position. Read with the file, free. Like the regions, only on page 1.
const firstPage = computed(() => (props.page.n || 1) === 1);
const commonsCaptions = computed(() =>
  firstPage.value
    ? Object.entries(props.file.sdc?.captions || {})
        .filter(([, text]) => text)
        .map(([lang, text]) => ({ lang, text }))
        .sort((a, b) => (a.lang === config.taal ? -1 : b.lang === config.taal ? 1 : a.lang.localeCompare(b.lang)))
    : []
);
const commonsDepicts = computed(() => {
  if (!firstPage.value) return [];
  const statements = props.file.sdc?.beeldt_af || [];
  // An item that also has a region is found that way already.
  const withRegion = new Set(statements.filter((s2) => s2.positie).map((s2) => s2.waarde));
  const seen = new Map();
  for (const statement of statements) {
    if (statement.soort !== "item" || withRegion.has(statement.waarde) || seen.has(statement.waarde)) continue;
    const en = statement.label_en || statement.label || statement.waarde;
    seen.set(statement.waarde, { q: statement.waarde, label: config.taal === "en" ? en : statement.label || en, en });
  }
  return [...seen.values()];
});
const hasCommonsData = computed(() => Boolean(regionCount.value || commonsCaptions.value.length || commonsDepicts.value.length));
const sdcLink = computed(() => `https://commons.wikimedia.org/wiki/${encodeURIComponent((props.file.titel || "").replace(/ /g, "_"))}#P180`);

// With data on Commons, From Commons is open and the other sections closed (wish Olaf);
// without, the AI suggestions are open. Set again for every file and page.
watch(
  () => [props.file.mid, props.page.n],
  () => {
    const known = hasCommonsData.value;
    Object.assign(open, { commons: known, suggestions: !known, search: false, point: false, croptool: false });
  },
  { immediate: true }
);

// The search word for an item: the English label (SAM searches in English), without the
// words and signs that split a prompt; changeable per item, remembered in this browser.
const cleanWord = (text) =>
  String(text || "")
    .replace(/[,+]/g, " ")
    .replace(/\s+(en|and|min|not)\s+/gi, " & ")
    .replace(/(^|\s)-\s*/g, " ")
    .replace(/\s+/g, " ")
    .trim();
const itemWords = ref({});
const itemWordsKey = computed(() => `cc-item-zoekwoord:${props.file.mid}`);
watch(
  itemWordsKey,
  (key) => {
    try {
      itemWords.value = JSON.parse(window.localStorage.getItem(key) || "{}");
    } catch {
      itemWords.value = {};
    }
  },
  { immediate: true }
);
const itemWord = (item) => cleanWord(itemWords.value[item.q] || item.en);
const editingItem = ref(null);
const itemDraft = ref("");
const itemInput = ref(null);
async function startItemWord(item) {
  editingItem.value = item.q;
  itemDraft.value = itemWord(item);
  await nextTick();
  const input = Array.isArray(itemInput.value) ? itemInput.value[0] : itemInput.value;
  input?.focus();
  input?.select();
}
function saveItemWord(item) {
  if (editingItem.value !== item.q) return;
  const word = cleanWord(itemDraft.value);
  const words = { ...itemWords.value };
  if (word && word !== cleanWord(item.en)) words[item.q] = word;
  else delete words[item.q]; // empty or the label again: back to the label
  itemWords.value = words;
  editingItem.value = null;
  try {
    window.localStorage.setItem(itemWordsKey.value, JSON.stringify(words));
  } catch {
    // Blocked storage: the word holds until the page is reloaded.
  }
}
const itemCount = (q) => props.objects.filter((o) => o.wikidata === q).length;
function itemTitle(item) {
  return [t("panel.commons_depicts_item", { label: item.label, q: item.q, word: itemWord(item) }), t("panel.term_found", { n: itemCount(item.q) })].join(" · ");
}
// Items left out of "Detect all", like the terms (per file, this browser only).
const excludedItems = ref([]);
const excludedItemsKey = computed(() => `cc-items-uit:${props.file.mid}`);
watch(
  excludedItemsKey,
  (key) => {
    try {
      excludedItems.value = JSON.parse(window.localStorage.getItem(key) || "[]");
    } catch {
      excludedItems.value = [];
    }
  },
  { immediate: true }
);
function setExcludedItems(list) {
  excludedItems.value = [...new Set(list)];
  try {
    window.localStorage.setItem(excludedItemsKey.value, JSON.stringify(excludedItems.value));
  } catch {
    // Blocked storage: the choice holds until the page is reloaded.
  }
}
const toggleItem = (q) => setExcludedItems(excludedItems.value.includes(q) ? excludedItems.value.filter((x) => x !== q) : [...excludedItems.value, q]);
const includedItems = computed(() => commonsDepicts.value.filter((item) => !excludedItems.value.includes(item.q)));
// An AI search term for something the file already depicts on Commons gets a mark.
const commonsNames = computed(() => {
  const names = new Set();
  for (const statement of props.file.sdc?.beeldt_af || []) {
    for (const name of [statement.label, statement.label_en]) if (name) names.add(String(name).toLowerCase());
  }
  return names;
});
const onCommons = (term) => commonsNames.value.has(String(term.en || "").toLowerCase()) || commonsNames.value.has(String(term.nl || "").toLowerCase());

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

// Which search words were looked for on this page (wish Olaf): a chip with results is
// green, one that was searched but found nothing is grey with a 0. Remembered in this
// browser per file and page; what is on the image decides "found".
const searched = ref([]);
const searchedKey = computed(() => `cc-gezocht:${props.file.mid}:${props.page.n}`);
watch(
  searchedKey,
  (key) => {
    try {
      searched.value = JSON.parse(window.localStorage.getItem(key) || "[]");
    } catch {
      searched.value = [];
    }
  },
  { immediate: true }
);
watch(
  () => props.lastResult,
  (result) => {
    if (!result || result.modus !== "prompt" || !result.prompt) return;
    const words = result.prompt.split(",").map((word) => word.trim().toLowerCase()).filter(Boolean);
    searched.value = [...new Set([...searched.value, ...words])];
    try {
      window.localStorage.setItem(searchedKey.value, JSON.stringify(searched.value));
    } catch {
      // Blocked storage: the colours hold until the page is reloaded.
    }
  }
);
const wasSearched = (word) => searched.value.includes(String(word || "").toLowerCase());
const resultClass = (count, word) => ({ "cc-term-gevonden": count > 0, "cc-term-niets": !count && wasSearched(word) });

// Your own search word for an AI search term (the pencil, wish Olaf), per file and page,
// remembered in this browser; empty or the term again goes back to the term.
const termWords = ref({});
const termWordsKey = computed(() => `cc-term-zoekwoord:${props.file.mid}:${props.page.n}`);
watch(
  termWordsKey,
  (key) => {
    try {
      termWords.value = JSON.parse(window.localStorage.getItem(key) || "{}");
    } catch {
      termWords.value = {};
    }
  },
  { immediate: true }
);
const termWord = (term) => cleanWord(termWords.value[term.en] || term.en);
// Objects found with the term, or with your own word for it.
const termHits = (term) => {
  const word = termWords.value[term.en];
  return termCount(term.en) + (word && word.toLowerCase() !== term.en.toLowerCase() ? termCount(word) : 0);
};
const editingTerm = ref(null);
const termDraft = ref("");
const termInput = ref(null);
async function startTermWord(term) {
  editingTerm.value = term.en;
  termDraft.value = termWord(term);
  await nextTick();
  const input = Array.isArray(termInput.value) ? termInput.value[0] : termInput.value;
  input?.focus();
  input?.select();
}
function saveTermWord(term) {
  if (editingTerm.value !== term.en) return;
  const word = cleanWord(termDraft.value);
  const words = { ...termWords.value };
  if (word && word.toLowerCase() !== term.en.toLowerCase()) words[term.en] = word;
  else delete words[term.en];
  termWords.value = words;
  editingTerm.value = null;
  try {
    window.localStorage.setItem(termWordsKey.value, JSON.stringify(words));
  } catch {
    // Blocked storage: the word holds until the page is reloaded.
  }
}

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
  const parts = [t("panel.term_expected", { n: term.aantal, where: term.waar }), t("panel.term_found", { n: termHits(term) })];
  if (termWords.value[term.en]) parts.push(t("panel.term_searched_as", { word: termWord(term) }));
  if (props.trashTerms[term.en]) parts.push(t("panel.term_trashed", { n: props.trashTerms[term.en] }));
  return parts.join(" · ");
}

const suggestionTotals = computed(() => {
  const terms = props.inventory?.zoektermen || [];
  const counts = terms.map((term) => termHits(term));
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
// Green when something was found, blue when the hits went elsewhere (merged, a group,
// the trash, hidden), yellow when nothing was found at all.
function resultType(result) {
  if (result.found || result.excluded) return "success";
  return result.merged || result.inGroup || result.inTrash || result.hidden ? "notice" : "warning";
}

function resultText(result) {
  // Pointing and drawing: about one object.
  if (result.modus === "punt") {
    if (result.outcome === "niets") return t("panel.result_point_none");
    return t(result.outcome === "bekend" ? "panel.result_point_known" : "panel.result_point_new", { name: result.name });
  }
  if (result.modus === "rechthoek") return t("panel.result_rectangle", { name: result.name });
  const terms = result.prompt.split(",").map((s) => s.trim()).filter(Boolean);
  const what = result.modus === "commons" ? t("panel.result_commons") : terms.length > 1 ? t("panel.result_terms", { n: terms.length }) : t("panel.result_term", { term: terms[0] || "" });
  // Hits that are not shown as an object of their own, each with the reason.
  const elsewhere = [
    result.merged && t(result.merged === 1 ? "panel.result_merged_one" : "panel.result_merged", { n: result.merged, names: (result.holders || []).join(", ") }),
    result.inGroup && t(result.inGroup === 1 ? "panel.result_in_group_one" : "panel.result_in_group", { n: result.inGroup }),
    result.inTrash && t(result.inTrash === 1 ? "panel.result_in_trash_one" : "panel.result_in_trash", { n: result.inTrash }),
    result.hidden && t(result.hidden === 1 ? "panel.result_hidden_one" : "panel.result_hidden", { n: result.hidden }),
  ].filter(Boolean);
  if (!result.found && !result.excluded && !elsewhere.length) return t("panel.result_none", { what });
  const parts = [];
  if (result.found) parts.push(result.found === 1 ? t("panel.result_one", { what }) : t("panel.result_found", { n: result.found, what }));
  else if (!result.excluded) parts.push(t("panel.result_nothing_new", { what }));
  if (result.excluded) parts.push(t("panel.result_excluded", { n: result.excluded }));
  if (elsewhere.length) parts.push(`${t("panel.result_also")} ${elsewhere.join("; ")}.`);
  return parts.join(" ");
}

// A search with terms that found nothing (not "from Commons", pointing or drawing).
function isNone(result) {
  return Boolean(result) && result.modus === "prompt" && !result.found && !result.excluded && !result.merged && !result.inGroup && !result.inTrash && !result.hidden;
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
// Or open Point or draw with that way switched on at once: click the object, or draw around it.
// Only unfold Point or draw and scroll to it, no way switched on (link under 'Depicts, without a region').
async function showPointOrDraw() {
  open.point = true;
  await nextTick();
  document.querySelector(".cc-sectie-aanwijzen")?.scrollIntoView({ block: "center", behavior: "smooth" });
}
async function tryPoint(mode = "point") {
  open.point = true;
  open[mode === "draw" ? "tekenen" : "aanwijzen"] = true;
  emit(mode === "draw" ? "draw-mode" : "point-mode", true);
  await nextTick();
  document.querySelector(".cc-sectie-aanwijzen")?.scrollIntoView({ block: "center", behavior: "smooth" });
}

function search() {
  if (prompt.value.trim()) act("search", "detect", { modus: "prompt", prompt: prompt.value.trim() });
}
</script>
