<!--
  The detection panel (functional design 7 and 10.4): suggestions for this
  page, regions from Commons, search, point or draw and bulk
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
    <busy-note v-if="busy && !busyElsewhere && where === 'top'" :message="t('busy.general')" />

    <!-- From Commons comes first (wish Olaf, 6-11-2026): what people already put on Commons
         goes before new AI suggestions, and it is free to read. Only when the file has
         captions, depicts, regions or notes (they always refer to page 1). Backlog 26. -->
    <cdx-accordion v-if="hasCommonsData" v-bind="sectionProps('commons')">
      <template #title>{{ t("panel.from_commons") }} <info-dialog v-bind="info('commons', 'panel.from_commons')" /> <section-lock v-bind="lockProps('commons')" /></template>
      <p class="cc-uitleg">{{ t("panel.from_commons_intro") }} <a :href="sdcLink" target="_blank" rel="noopener">{{ t("panel.commons_edit_link") }}</a></p>
      <!-- What the app read is kept a day: read again after adding something on Commons. -->
      <p class="cc-uitleg">
        <button type="button" class="cc-link" :disabled="busy" :title="t('panel.commons_read_again_help')" @click="act('commons-lezen', 'read-again')">{{ t("panel.commons_read_again") }}</button>
      </p>
      <busy-note v-if="busy && !busyElsewhere && where === 'commons-lezen'" :message="t('busy.general')" />
      <!-- The outcome right under the link (wish Olaf), not at the top of the page. -->
      <notice-list :notices="noticesAt('commons')" @dismiss="emit('dismiss-notice', $event)" />

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
        <result-message v-if="lastResult && resultAt === 'commons' && !busy" v-bind="resultProps(lastResult)" :busy="busy" @dismiss="emit('dismiss-result')" @restore-trash="emit('restore-trash', lastResult)" />
      </cdx-accordion>

      <!-- (3) Depicts without a position: a chip per item; a click lets SAM find it (paid),
           and what is found gets that item as its depicts. Read only: the search word is the English label. -->
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
            <li><strong>{{ t("panel.commons_depicts_bulk") }}</strong> {{ t("panel.commons_depicts_untick") }}</li>
            <li><strong>{{ t("panel.commons_depicts_results") }}</strong> {{ t("panel.terms_colours") }}</li>
            <!-- Something new for depicts: the three ways, as links to their sections (wish Olaf). -->
            <li>
              <strong>{{ t("panel.commons_depicts_add_new") }}</strong>
              <ul>
                <li>{{ t("panel.commons_depicts_try") }} <button type="button" class="cc-link" @click="showSuggestions">{{ t("panel.suggestions") }}</button></li>
                <li>{{ t("panel.commons_depicts_use") }} <button type="button" class="cc-link" @click="showSearch">{{ t("panel.search") }}</button> {{ t("panel.commons_depicts_below") }}</li>
                <li>{{ t("panel.commons_depicts_go") }} <button type="button" class="cc-link" @click="showPointOrDraw">{{ t("panel.point_or_draw") }}</button></li>
              </ul>
            </li>
          </ul>
        </div>
        <div class="cc-knoppen">
          <span v-for="item in commonsDepicts" :key="item.q" class="cc-term" :class="{ 'cc-term-uit': excludedItems.includes(item.q), ...resultClass(itemCount(item), itemWord(item)) }">
            <input
              type="checkbox"
              class="cc-term-mee"
              :checked="!excludedItems.includes(item.q)"
              :disabled="busy"
              :aria-label="t('panel.term_include', { term: item.label })"
              :title="t('panel.term_include', { term: item.label })"
              @change="toggleItem(item.q)"
            />
            <!-- Read only (wish Olaf, 11-11-2026): no pencil; another word goes under Search. -->
            <cdx-button
              action="progressive"
              size="small"
              :disabled="busy"
              :title="itemTitle(item)"
              @click="act('commons-depicts', 'detect', { modus: 'prompt', prompt: itemWord(item), items: { [itemWord(item)]: item.q }, ...(item.noEnglish ? { askWord: true } : {}) })"
            >
              <span v-if="item.noEnglish" class="cc-geen-engels" :title="t('panel.no_english_label')" aria-hidden="true">⚠</span>
              {{ item.label }}<span v-if="item.taal" class="cc-label-taal" :title="t('panel.label_language', { lang: item.taal })"> {{ item.taal }}</span>
              <span v-if="itemCount(item) || wasSearched(itemWord(item))" class="cc-term-aantal">{{ itemCount(item) }}</span>
            </cdx-button>
          </span>
          <!-- The tick-box links next to the button they steer, under the items (wish Olaf). -->
          <div class="cc-termen-bulk">
          <!-- After the first round (an item has a linked object) the label says "again" (wish Olaf). The amount
               is what it really costs: a word searched before comes from the cache, free. -->
          <cdx-button
            action="progressive"
            weight="primary"
            size="small"
            :disabled="busy || !includedItems.length"
            @click="locateItems(includedItems)"
          >
            {{ t(depictsLabel, { n: includedItems.length }) }}
            <span class="cc-kosten">{{ itemsCost(includedItems) }}</span>
          </cdx-button>
          <tick-links class="cc-termen-alles" :label="t('objects.select_label')" :keys="TERM_LINKS" :disabled="busy" @all="setExcludedItems([])" @none="setExcludedItems(commonsDepicts.map((item) => item.q))" @invert="invertItems(commonsDepicts.map((item) => item.q))" />
          </div>
        </div>
        <busy-note v-if="busy && where === 'commons-depicts'" :message="t('busy.sam')" />
        <result-message v-if="lastResult && resultAt === 'commons-depicts' && !busy" v-bind="resultProps(lastResult)" :busy="busy" @dismiss="emit('dismiss-result')" @restore-trash="emit('restore-trash', lastResult)" />
      </cdx-accordion>
    </cdx-accordion>

    <!-- Then the AI suggestions: they fit this image, unlike a fixed list. -->
    <cdx-accordion id="cc-ai-suggesties" v-bind="sectionProps('suggestions')">
      <template #title>{{ t("panel.suggestions") }} <info-dialog v-bind="info('suggestions', 'panel.suggestions')" /> <section-lock v-bind="lockProps('suggestions')" /></template>
      <!-- What this section is for, in one or two sentences (wish Olaf), as in From Commons. -->
      <!-- What the AI makes, one bullet each (wish Olaf 13-11-2026). -->
      <!-- Once the AI has looked, in the past tense and as it is: what it made, and what is not
           there (wish Olaf 13-11-2026). -->
      <div v-if="!inventory" class="cc-uitleg cc-sectie-intro">
        {{ t("panel.suggestions_intro") }}
        <ul class="cc-uitleg-lijst">
          <li>{{ t("panel.suggestions_intro_description") }}</li>
          <li>{{ t("panel.suggestions_intro_text") }}</li>
          <li>{{ t("panel.suggestions_intro_terms") }}</li>
        </ul>
      </div>
      <div v-else class="cc-uitleg cc-sectie-intro">
        {{ t("panel.suggestions_done") }}
        <ul class="cc-uitleg-lijst">
          <!-- The word in [brackets] jumps to its part below and opens it (wish Olaf 13-11-2026). -->
          <li v-for="line in madeLines" :key="line.text">
            <template v-for="(piece, k) in linkPieces(line.text)" :key="k">
              <a v-if="piece.link" href="#" class="cc-naar-deel" @click.prevent="showPart(line.part)">{{ piece.text }}</a>
              <template v-else>{{ piece.text }}</template>
            </template>
          </li>
        </ul>
      </div>
      <!-- In the order of the work: (1) ask the AI what is on the image (one call), (2) its
           description, (3) the search terms: find where those things are, and what was found.
           Each part can be asked again (a call for that part only) or removed on its own.
           Explanations (cc-uitleg) look different from what the AI said (cc-ai-resultaat). -->
      <!-- Removing everything, or a part whose place is gone with it: the outcome on top of this section. -->
      <notice-list :notices="inventory ? noticesAt('ai-alles') : notices.filter((n) => String(n.where || '').startsWith('ai-'))" @dismiss="emit('dismiss-notice', $event)" />
      <template v-if="!inventory">
        <p class="cc-uitleg">{{ t("panel.inventory_help") }} {{ museCost(pageUsd ?? config.muse.pagina_usd) }}</p>
        <div class="cc-knoppen">
          <cdx-button action="progressive" weight="primary" :disabled="busy" @click="act('inventory', 'inventory', { detailniveau: detail })">{{ t("panel.inventory") }}</cdx-button>
        </div>
        <busy-note v-if="busy && where === 'inventory'" :message="t('busy.muse_page')" />
      </template>
      <template v-else>
        <!-- (2) The AI's description of the image: editable, with its earlier versions (PageDescription.vue).
             Each of the two parts folds away on its own (wish Olaf). -->
        <cdx-accordion v-model="open.beschrijving" class="cc-deel-uitklap" data-deel="beschrijving">
          <template #title>{{ t("panel.part_title_beschrijving") }}</template>
        <page-description
          :mid="file.mid"
          :n="page.n"
          :inventory="inventory"
          :busy="busy"
          :cost="museCost(pageUsd ?? config.muse.pagina_usd)"
          @changed="emit('inventory-changed', $event)"
          @again="act('beschrijving', 'inventory', { deel: 'beschrijving', beschrijvingsniveau: $event })"
          @forget="act('beschrijving', 'forget-inventory', { deel: 'beschrijving' })"
        >
          <template #wachten><busy-note v-if="busy && where === 'beschrijving'" :message="t('busy.muse_page')" /></template>
        </page-description>
        <notice-list :notices="noticesAt('ai-beschrijving')" @dismiss="emit('dismiss-notice', $event)" />
        </cdx-accordion>

        <!-- (3) The search terms. -->
        <cdx-accordion v-model="open.zoektermen" class="cc-deel-uitklap" data-deel="zoektermen">
          <template #title>{{ t("panel.part_title_zoektermen") }}</template>
        <!-- First what makes the search terms (the level of detail, asking anew, removing), compact
             on one line; under it the terms themselves, the result of that (wish Olaf). -->
        <div class="cc-termen-bron">
          <!-- Always side by side, under the slider: ask anew, and remove all. -->
          <div class="cc-termen-knoppen">
          <cdx-button action="progressive" weight="quiet" size="small" :disabled="busy" :title="`${t('panel.part_again_help_zoektermen')} ${t('panel.parts_help')}`" @click="act('zoektermen', 'inventory', { deel: 'zoektermen', detailniveau: detail })">
            {{ t(inventory.zoektermen?.length ? "panel.part_again_zoektermen" : "panel.part_ask_zoektermen") }} <span class="cc-kosten">{{ museCost(pageUsd ?? config.muse.pagina_usd) }}</span>
          </cdx-button>
          <cdx-button v-if="inventory.zoektermen?.length" action="destructive" weight="quiet" size="small" :disabled="busy" @click="act('zoektermen', 'forget-inventory', { deel: 'zoektermen' })">
            <cdx-icon :icon="cdxIconTrash" size="small" /> {{ t("panel.part_forget_zoektermen_button") }}
          </cdx-button>
          </div>
        </div>
        <busy-note v-if="busy && where === 'zoektermen'" :message="t('busy.muse_page')" />
        <notice-list :notices="noticesAt('ai-zoektermen')" @dismiss="emit('dismiss-notice', $event)" />
        <template v-if="inventory.zoektermen?.length">
          <!-- Two blocks (wish Olaf): first what the AI saw that Commons already depicts, as
               buttons that do nothing (locate those under From Commons); then what the AI adds. -->
          <template v-if="commonsTerms.length">
            <p class="cc-termen-kop">{{ t("panel.terms_on_commons_title", { n: commonsTerms.length }) }}</p>
            <p class="cc-uitleg cc-termen-uitleg">{{ t("panel.terms_on_commons_help") }}</p>
            <div class="cc-knoppen">
              <!-- The name of the item on Commons ("stairs"), not the AI's word ("staircase"): one thing per chip (wish Olaf). -->
              <span v-for="term in commonsTerms" :key="term.en" class="cc-term cc-term-vast" :class="{ 'cc-term-gevonden': commonsTermCount(term) > 0 }">
                <cdx-button size="small" disabled :title="t('panel.term_on_commons_help_ai', { term: termLabel(term) })">
                  {{ commonsLabel(term) }}
                  <span v-if="commonsTermCount(term)" class="cc-term-aantal">{{ commonsTermCount(term) }}</span>
                </cdx-button>
              </span>
            </div>
            <p class="cc-termen-kop">{{ t("panel.terms_new_title", { n: newTerms.length }) }}</p>
          </template>
          <p v-if="!newTerms.length" class="cc-uitleg">{{ t("panel.terms_new_none") }}</p>
          <!-- What the terms are for: finding where on the image each thing is. -->
          <p v-if="newTerms.length" class="cc-uitleg cc-termen-uitleg">
            {{ t("panel.terms_help") }} {{ cost(1) }} {{ t("panel.terms_colours") }} {{ t("panel.terms_choose") }}
          </p>
          <div v-if="newTerms.length" class="cc-knoppen">
            <!-- Each term: a tick (does it go along with "Detect all"?) and the term itself (detect only this one). -->
            <span v-for="term in newTerms" :key="term.en" class="cc-term" :class="{ 'cc-term-uit': excluded.includes(term.en), ...resultClass(termHits(term), term.en) }">
              <input
                type="checkbox"
                class="cc-term-mee"
                :checked="!excluded.includes(term.en)"
                :disabled="busy"
                :aria-label="t('panel.term_include', { term: termLabel(term) })"
                :title="t('panel.term_include', { term: termLabel(term) })"
                @change="toggleTerm(term.en)"
              />
              <!-- The AI's term as it is: no pencil (wish Olaf, 12-11-2026). Wrong? Remove the object
                   on the right. Something else? Search or Point or draw (the line under the terms). -->
              <cdx-button
                action="progressive"
                size="small"
                :disabled="busy"
                :title="termTitle(term)"
                @click="act('suggestions', 'detect', { modus: 'prompt', prompt: term.en })"
              >
                {{ termLabel(term) }}
                <span v-if="termHits(term) || wasSearched(term.en)" class="cc-term-aantal">{{ termHits(term) }}</span>
              </cdx-button>
            </span>
            <!-- The ticked terms in one go, right behind the terms themselves: the main action here;
                 the tick-box links next to it (wish Olaf). -->
            <div class="cc-termen-bulk">
            <cdx-button
              action="progressive"
              weight="primary"
              size="small"
              :disabled="busy || !includedTerms.length"
              @click="act('suggestions', 'detect', { modus: 'prompt', prompt: includedTerms.map((term) => term.en).join(', ') })"
            >
              {{ t(termsLabel, { n: includedTerms.length }) }}
              <span class="cc-kosten">{{ cost(includedTerms.length) }}</span>
            </cdx-button>
            <tick-links class="cc-termen-alles" :label="t('objects.select_label')" :keys="TERM_LINKS" :disabled="busy" @all="setExcluded([])" @none="setExcluded(newTerms.map((term) => term.en))" @invert="invertTerms(newTerms.map((term) => term.en))" />
            </div>
          </div>
          <!-- Not right, or something else: the places for that (wish Olaf). -->
          <p v-if="newTerms.length" class="cc-uitleg">
            {{ t("panel.terms_other") }} <button type="button" class="cc-link" @click="showSearch">{{ t("panel.search") }}</button> {{ t("panel.terms_other_or") }}
            <button type="button" class="cc-link" @click="showPointOrDraw">{{ t("panel.point_or_draw") }}</button>.
          </p>
          <busy-note v-if="busy && where === 'suggestions'" :message="t('busy.sam')" />
          <result-message v-if="lastResult && resultAt === 'suggestions' && !busy" v-bind="resultProps(lastResult)" :busy="busy" :other-ways="isNone(lastResult)" @try-search="trySearch(lastResult)" @try-point="tryPoint" @dismiss="emit('dismiss-result')" @restore-trash="emit('restore-trash', lastResult)" />
          <!-- What of these suggestions is on the image now, and what went to the trash. -->
          <p class="cc-status">
            {{ t("panel.suggestions_found", { n: suggestionTotals.found, terms: suggestionTotals.terms, total: newTerms.length }) }}
            <template v-if="suggestionTotals.trashed">{{ suggestionTotals.trashed === 1 ? t("panel.suggestions_trashed_one") : t("panel.suggestions_trashed", { n: suggestionTotals.trashed }) }}</template>
          </p>
        </template>
        <p v-else class="cc-uitleg">{{ t("panel.part_none_zoektermen") }}</p>
        </cdx-accordion>
      </template>
    </cdx-accordion>

    <cdx-accordion v-bind="sectionProps('search')">
      <template #title>{{ t("panel.search") }} <info-dialog v-bind="info('search', 'panel.search')" /> <section-lock v-bind="lockProps('search')" /></template>
      <p class="cc-uitleg cc-sectie-intro">{{ t("panel.search_intro") }}</p>
      <form class="cc-zoek" @submit.prevent="search">
        <cdx-text-input clearable v-model="prompt" :placeholder="t('panel.search_placeholder')" :aria-label="t('panel.search')" />
        <cdx-button type="submit" action="progressive" :disabled="busy || !cleanText(prompt)">{{ t("panel.search_button") }}</cdx-button>
      </form>
      <busy-note v-if="busy && where === 'search'" :message="t('busy.sam')" />
      <result-message v-if="lastResult && resultAt === 'search' && !busy" v-bind="resultProps(lastResult)" :busy="busy" :other-ways="isNone(lastResult)" :search-link="false" @try-point="tryPoint" @dismiss="emit('dismiss-result')" @restore-trash="emit('restore-trash', lastResult)" />
      <p class="cc-uitleg">{{ t("panel.search_help") }} {{ cost(1) }}</p>
      <!-- Rename to link (wish Olaf): only when the file has depicts items without a region. -->
      <p v-if="commonsDepicts.length" class="cc-uitleg">{{ t("panel.search_rename_tip") }}</p>
    </cdx-accordion>

    <!-- Point or draw: two ways to choose one object yourself; one of the two switches at a time. -->
    <cdx-accordion v-bind="sectionProps('point')" class="cc-sectie-aanwijzen">
      <template #title>{{ t("panel.point_or_draw") }} <info-dialog v-bind="info('point', 'panel.point_or_draw')" /> <section-lock v-bind="lockProps('point')" /></template>
      <p class="cc-uitleg cc-sectie-intro">{{ t("panel.point_or_draw_intro") }}</p>
      <!-- Two ways, each folding away on its own, as in the AI suggestions (wish Olaf). -->
      <cdx-accordion v-model="open.aanwijzen" class="cc-deel-uitklap">
        <template #title>{{ t("panel.part_title_point") }}</template>
      <div class="cc-modus-keuze">
        <cdx-toggle-switch :model-value="pointMode" @update:model-value="emit('point-mode', $event)">
          {{ t("panel.point_switch") }}
        </cdx-toggle-switch>
        <!-- A hint for the AI (wish Olaf, 12-11-2026): SAM then looks for this word and keeps what lies under the click. -->
        <label class="cc-hint-veld">
          <span class="cc-hint-label">{{ t("panel.hint_label") }}</span>
          <cdx-text-input clearable :model-value="hints.point" :placeholder="t('panel.hint_placeholder')" :disabled="busy || !pointMode" @update:model-value="emit('hint', { kind: 'point', text: $event })" />
        </label>
        <p class="cc-uitleg">{{ t("panel.point_help") }} <template v-if="hints.point.trim()">{{ t("panel.point_hint_help", { hint: hints.point.trim() }) }} </template>{{ cost(1) }}</p>
        <busy-note v-if="busy && where === 'point'" :message="t('busy.sam')" />
        <result-message v-if="lastResult && resultAt === 'point' && !busy && lastResult.modus === 'punt'" v-bind="resultProps(lastResult)" :busy="busy" @dismiss="emit('dismiss-result')" @restore-trash="emit('restore-trash', lastResult)" />
      </div>
      </cdx-accordion>
      <cdx-accordion v-model="open.tekenen" class="cc-deel-uitklap">
        <template #title>{{ t("panel.part_title_draw") }}</template>
      <div class="cc-modus-keuze">
        <cdx-toggle-switch :model-value="drawMode" @update:model-value="emit('draw-mode', $event)">
          {{ t("panel.draw_switch") }}
        </cdx-toggle-switch>
        <!-- With a hint the rectangle is searched for that word (paid); without one it stays free. -->
        <label class="cc-hint-veld">
          <span class="cc-hint-label">{{ t("panel.hint_label") }}</span>
          <cdx-text-input clearable :model-value="hints.draw" :placeholder="t('panel.hint_placeholder')" :disabled="busy || !drawMode" @update:model-value="emit('hint', { kind: 'draw', text: $event })" />
        </label>
        <p class="cc-uitleg">{{ t("panel.draw_help") }} <template v-if="hints.draw.trim()">{{ t("panel.draw_hint_help", { hint: hints.draw.trim() }) }} {{ cost(1) }}</template><template v-else>{{ t("panel.free") }}</template></p>
        <busy-note v-if="busy && where === 'draw'" :message="t('busy.sam')" />
        <result-message v-if="lastResult && resultAt === 'point' && !busy && lastResult.modus === 'rechthoek'" v-bind="resultProps(lastResult)" :busy="busy" @dismiss="emit('dismiss-result')" @restore-trash="emit('restore-trash', lastResult)" @undo="emit('undo-result', lastResult)" />
      </div>
      </cdx-accordion>
    </cdx-accordion>

    <!-- To Commons: the last step, for all work on the image, not only the AI suggestions (wish
         Olaf): depicts from Commons items, found objects and search terms, and the caption. -->
    <cdx-accordion v-bind="sectionProps('tocommons')" class="cc-naar-commons">
      <template #title>{{ t("panel.to_commons") }} <info-dialog v-bind="info('tocommons', 'panel.to_commons')" /> <section-lock v-bind="lockProps('tocommons')" /></template>
      <p class="cc-uitleg cc-sectie-intro">{{ t("panel.to_commons_intro") }}</p>
      <!-- Depicts and captions for the whole image (FO 9.7), in a window of its own. Blue but
           not filled: detecting stays the main action. Disabled for files with more pages, where
           the data belongs to the whole file. -->
      <div class="cc-origineel-knop">
        <!-- Only once there is something to add (wish Olaf): objects or AI suggestions. -->
        <cdx-button action="progressive" :disabled="busy || file.paginas > 1 || !somethingToAdd" :title="file.paginas > 1 ? t('original.button_pages') : somethingToAdd ? t('original.button_help') : t('original.button_nothing')" @click="originalOpen = true">
          {{ t("original.button") }}
        </cdx-button>
        <p v-if="file.paginas > 1" class="cc-uitleg">{{ t("original.button_pages") }}</p>
        <p v-else-if="!somethingToAdd" class="cc-uitleg cc-niets-toe-te-voegen">{{ t("original.button_nothing") }}</p>
        <!-- The list of what can go back is in the window this button opens (wish Olaf 13-11-2026). -->
      </div>
      <original-data
        v-if="originalOpen"
        :open="originalOpen"
        :file="file"
        :page="page"
        :inventory="inventory"
        :busy="busy"
        :cost="museCost(pageUsd ?? config.muse.pagina_usd)"
        @ask-caption="emit('inventory', { deel: 'beschrijving', beschrijvingsniveau: 'caption' })"
        @close="originalOpen = false"
      />
    </cdx-accordion>
  </div>
</template>

<script setup>
import { computed, inject, nextTick, reactive, ref, watch } from "vue";
import { CdxAccordion, CdxButton, CdxIcon, CdxMessage, CdxTextInput, CdxToggleSwitch } from "@wikimedia/codex";
import { cdxIconTrash } from "@wikimedia/codex-icons";
import SectionLock from "./SectionLock.vue";
import TickLinks from "./TickLinks.vue";
import ResultMessage from "./ResultMessage.vue";
import { textParts } from "../confirm.js";
import { priceLabel, useT } from "../i18n.js";
import { START_SUGGESTIONS, commonsFileUrl } from "../state.js";
import { readStored, removeStored, useStoredList, writeStored } from "../storage.js";
import { get, pagePath } from "../api.js";
import { objectsWithTerm } from "../facets.js";
import { cleanText } from "../text.js";
import AiBadge from "./AiBadge.vue";
import BusyNote from "./BusyNote.vue";
import PageDescription from "./PageDescription.vue";
import InfoDialog from "./InfoDialog.vue";
import OriginalData from "./OriginalData.vue";
import NoticeList from "./NoticeList.vue";

// Read once when the app starts (module scope), so a panel built again still knows it.
const SUGGESTIONS_FOR = START_SUGGESTIONS;
const props = defineProps({
  // What asking Muse Spark about the whole image costs for this file (from the page's plan; the
  // cheaper Contributor model for public-domain files). null: not known yet, the general price.
  pageUsd: { type: Number, default: null },
  // Busy with something in the objects column (describe, group): its note shows there, not here.
  busyElsewhere: { type: Boolean, default: false },
  file: { type: Object, required: true },
  page: { type: Object, required: true },
  busy: { type: Boolean, default: false },
  inventory: { type: Object, default: null },
  // The objects on the page now, and per search term how many are in the trash.
  objects: { type: Array, default: () => [] },
  trashTerms: { type: Object, default: () => ({}) },
  pointMode: { type: Boolean, default: false },
  drawMode: { type: Boolean, default: false },
  // The hints for Point and Draw ({point, draw}): a word SAM looks for.
  hints: { type: Object, default: () => ({ point: "", draw: "" }) },
  // The outcome of the last detection: shown in the section whose button asked for it.
  lastResult: { type: Object, default: null },
  // Notices about actions in this panel, shown near their button (where: commons, ai-…).
  notices: { type: Array, default: () => [] },
});
const noticesAt = (place) => props.notices.filter((n) => n.where === place);
const emit = defineEmits(["detect", "inventory", "inventory-changed", "forget-inventory", "point-mode", "draw-mode", "dismiss-result", "read-again", "dismiss-notice", "restore-trash", "hint", "undo-result"]);
const t = useT();
const config = inject("config");
// The tick-box links of the depicts items and the AI terms ("Alle termen" …).
const TERM_LINKS = { all: "panel.terms_all", none: "panel.terms_none", invert: "panel.terms_invert" };
// The two models in the live-mode line link to Meta's own pages. Muse Spark
// has no homepage of its own; its section in the model overview is the closest.
const modelLinks = {
  sam: { href: "https://ai.meta.com/sam3/", label: config.sam_model },
  muse: { href: "https://dev.meta.ai/docs/models#muse-spark", label: "Muse Spark" },
};
const prompt = ref("");
// The level of detail of the search terms: that of the overview, else the last one chosen in this browser.
const DETAIL_KEY = "cc-detailniveau";
const detail = ref(props.inventory?.detailniveau || readStored(DETAIL_KEY, "normaal"));
watch(
  () => props.inventory?.detailniveau,
  (level) => {
    if (level) detail.value = level;
  }
);
watch(detail, (level) => writeStored(DETAIL_KEY, level));
// The (i) beside each section title: a popup that explains what the section does.
function info(section, titleKey) {
  return {
    title: t(titleKey),
    label: t("panel.info_label", { section: t(titleKey) }),
    paragraphs: [
      ...[1, 2, 3, 4, 5, 6, 7, 8].map((n) => t(`panel.info_${section}_${n}`)).filter((text) => !text.startsWith("panel.")),
      // The lock pin of this section, and how it stands now (wish Olaf, 12-11-2026).
      t("panel.info_lock"),
      t(isLocked(section) ? "panel.info_lock_on" : "panel.info_lock_off", { state: t(open[section] ? "panel.section_state_open" : "panel.section_state_closed") }),
    ],
  };
}
const open = reactive({ captions: true, regios: true, beeldtaf: true, commons: true, search: false, suggestions: true, beschrijving: true, zoektermen: true, aanwijzen: true, tekenen: true, point: false, tocommons: true });
// Lock pins (wish Olaf, 12-11-2026): a locked section keeps the state it had when it was locked
// (folded or unfolded), also after the app is loaded again. Nothing folds or unfolds it then: not
// its title, and not the app's own links (they only scroll to it).
const LOCK_KEY = "cc-uitklap-vast";
function loadLocks() {
  const stored = readStored(LOCK_KEY, {}, { json: true });
  return Object.fromEntries(Object.entries(stored || {}).filter(([key, state]) => key in open && typeof state === "boolean"));
}
const locks = reactive(loadLocks());
Object.assign(open, locks);
const isLocked = (key) => typeof locks[key] === "boolean";
function toggleLock(key) {
  if (isLocked(key)) delete locks[key];
  else locks[key] = open[key];
  writeStored(LOCK_KEY, locks, { json: true }); // private window: the lock holds for this visit only
}
const lockLabel = (key) => {
  const state = t(open[key] ? "panel.section_state_open" : "panel.section_state_closed");
  return t(isLocked(key) ? "panel.section_unlock" : "panel.section_lock", { state });
};
// Every change of a section goes through here. A locked one refuses it; should the browser have
// folded it anyway (it did, now and then, on the first click after loading), it is put back.
function setOpen(key, value) {
  if (!isLocked(key)) {
    open[key] = value;
    return;
  }
  if (value === locks[key]) return;
  nextTick(() => {
    const element = document.querySelector(`[data-sectie="${key}"]`);
    if (element && element.open !== locks[key]) element.open = locks[key];
  });
}
// A click on the title of a locked section (not on its buttons, nor in a section inside it) does nothing.
function guard(key, event) {
  if (!isLocked(key) || event.target.closest("button")) return;
  const summary = event.target.closest("summary");
  if (summary && summary.parentElement === event.currentTarget) event.preventDefault();
}
// What each of the five sections carries (v-bind): its state through setOpen, its name for the
// lookup in setOpen (data-sectie), the look of a locked section and the guard on its title.
const sectionProps = (key) => ({
  modelValue: open[key],
  "data-sectie": key,
  "onUpdate:modelValue": (value) => setOpen(key, value),
  class: { "cc-uitklap-vast": isLocked(key) },
  onClickCapture: (event) => guard(key, event),
});
// The lock pin in the title of such a section.
const lockProps = (key) => ({ locked: isLocked(key), label: lockLabel(key), onToggle: () => toggleLock(key) });
const regionCount = computed(() => props.page.regio_aantal + props.page.notitie_aantal);
// The window "Gegevens van deze afbeelding" (9.7).
const originalOpen = ref(false);
// Something that can go to Commons: objects on the image, AI suggestions (description, search
// terms), or a caption on Commons that you may want to rewrite by hand (wish Olaf). Computed
// lazily, so commonsCaptions (defined below) is ready when it is read.
const somethingToAdd = computed(() => props.objects.length > 0 || Boolean(props.inventory?.zoektermen?.length || props.inventory?.samenvatting || props.inventory?.paginasoort) || commonsCaptions.value.length > 0);
// The "- " and "  - " lines of the (i) of To Commons, as a list with sub-items.

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
    // A readable name (Dutch/English, the multilingual label, another language, the Q-id last); the
    // English word for SAM, or, without one, the name (the server's dictionary may translate it) and
    // a request to give an English word first (wish Olaf 13-11-2026).
    const english = statement.label_en || "";
    const name = config.taal === "en" ? english || statement.label || statement.waarde : statement.label || english || statement.waarde;
    seen.set(statement.waarde, { q: statement.waarde, label: name, taal: statement.label_taal || "", en: english || statement.label || statement.waarde, noEnglish: !english });
  }
  return [...seen.values()];
});
const hasCommonsData = computed(() => Boolean(regionCount.value || commonsCaptions.value.length || commonsDepicts.value.length));
const sdcLink = computed(() => commonsFileUrl(props.file.titel, "P180"));

// With data on Commons, From Commons is open and the other sections closed (wish Olaf);
// without, the AI suggestions are open. Set again for every file and page.
watch(
  () => [props.file.mid, props.page.n],
  () => {
    const known = hasCommonsData.value;
    Object.assign(open, { commons: known, suggestions: !known, search: false, point: false });
    // A locked section keeps its own state (lock pin, wish Olaf 12-11-2026).
    Object.assign(open, locks);
    // #ai-suggesties (the link in "Start this image over", wish Olaf): open the AI suggestions and
    // bring them into view, once.
    // #ai-suggesties (the link in "Start this image over", wish Olaf): for that image only, the AI
    // suggestions open and in view, all other sections closed; also when the sections are set again
    // while the image loads.
    if (SUGGESTIONS_FOR && props.file.mid === SUGGESTIONS_FOR) {
      Object.assign(open, { commons: false, suggestions: true, search: false, point: false });
      nextTick(() => setTimeout(() => document.getElementById("cc-ai-suggesties")?.scrollIntoView({ block: "start", behavior: "smooth" }), 300));
    }
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
// The search word of a depicts item is its English label (read only, wish Olaf 11-11-2026).
const itemWord = (item) => cleanWord(item.en);
// The objects on the image linked to an item: found by locating that item. Not every object found with
// the same word (Olaf: all these items are on Commons already, so that would make every button green).
const itemCount = (item) =>
  props.objects.reduce((n, o) => n + (o.wikidata === item.q) + (o.groep?.leden || []).filter((m) => m.wikidata === item.q).length, 0);
function itemTitle(item) {
  return [t("panel.commons_depicts_item", { label: item.label, q: item.q }), t("panel.term_found", { n: itemCount(item) })].join(" · ");
}
// Items left out of "Detect all", like the terms (per file, this browser only).
const { list: excludedItems, set: setExcludedItems, toggle: toggleItem, invert: invertItems } = useStoredList(computed(() => `cc-items-uit:${props.file.mid}`));
const includedItems = computed(() => commonsDepicts.value.filter((item) => !excludedItems.value.includes(item.q)));
// The first round or a later one: does an item have a linked object on the image already?
const locatedItems = computed(() => commonsDepicts.value.filter((item) => itemCount(item)));
const depictsLabel = computed(() => {
  const all = includedItems.value.length === commonsDepicts.value.length;
  if (locatedItems.value.length) return all ? "panel.commons_depicts_all_again" : "panel.commons_depicts_chosen_again";
  return all ? "panel.commons_depicts_all" : "panel.commons_depicts_chosen";
});
const itemsRequest = (items) => ({
  modus: "prompt",
  prompt: items.map(itemWord).join(", "),
  items: Object.fromEntries(items.map((item) => [itemWord(item), item.q])),
  ...(items.some((item) => item.noEnglish) ? { askWord: true } : {}),
});
const locateItems = (items) => act("commons-depicts", "detect", itemsRequest(items));
// What a set of items really costs: the server knows which words are in the cache (free GET,
// the same estimate as the confirmation). Until it answers, every word counts.
// Per file and page: the same words can be free on one page (saved answers) and paid on another.
const paidCalls = ref({});
const estimateKey = (mid, n, prompt) => `${mid}/${n}|${prompt}`;
const itemsCost = (items) => {
  const key = estimateKey(props.file.mid, props.page.n, itemsRequest(items).prompt);
  return cost(key in paidCalls.value ? paidCalls.value[key] : items.length);
};
let estimateTimer = null;
watch(
  () => [props.file.mid, props.page.n, props.objects.length, itemsRequest(includedItems.value).prompt],
  ([mid, n, , ...prompts]) => {
    clearTimeout(estimateTimer);
    if (!config.betaald) return;
    estimateTimer = setTimeout(async () => {
      for (const prompt of new Set(prompts.filter(Boolean))) {
        try {
          const estimate = await get(`${pagePath(mid, n)}/detecties/raming?modus=prompt&prompt=${encodeURIComponent(prompt)}`);
          paidCalls.value = { ...paidCalls.value, [estimateKey(mid, n, prompt)]: estimate.aanroepen.betaald };
        } catch {
          // No estimate: the button keeps the full amount; the confirmation asks again.
        }
      }
    }, 400);
  },
  { immediate: true }
);
// The names (both languages) of what the file already depicts on Commons, to its item.
const commonsNames = computed(() => {
  const names = new Map();
  for (const statement of props.file.sdc?.beeldt_af || []) {
    if (statement.soort !== "item") continue;
    for (const name of [statement.label, statement.label_en]) if (name) names.set(String(name).toLowerCase(), statement.waarde);
  }
  return names;
});
const commonsItemFor = (term) => commonsNames.value.get(String(term.en || "").toLowerCase()) || commonsNames.value.get(String(term.nl || "").toLowerCase()) || null;
// The AI terms in two blocks (wish Olaf): what Commons already depicts (read only; locate those
// under From Commons) and what the AI adds, which you can search for, change and add.
// One chip per item: two AI words for the same item ("stairs", "staircase") are one thing.
const commonsTerms = computed(() => {
  const seen = new Set();
  return (props.inventory?.zoektermen || []).filter((term) => {
    const q = commonsItemFor(term);
    if (!q || seen.has(q)) return false;
    seen.add(q);
    return true;
  });
});
// The name of that item on Commons, in the language of the interface.
const commonsLabel = (term) => {
  const q = commonsItemFor(term);
  const statement = (props.file.sdc?.beeldt_af || []).find((st) => st.soort === "item" && st.waarde === q) || {};
  return (config.taal === "en" ? statement.label_en || statement.label : statement.label || statement.label_en) || termLabel(term);
};
const newTerms = computed(() => (props.inventory?.zoektermen || []).filter((term) => !commonsItemFor(term)));
// How many objects on the image are linked to the depicts item of such a term.
const commonsTermCount = (term) => {
  const q = commonsItemFor(term);
  return props.objects.reduce((n, o) => n + (o.wikidata === q) + (o.groep?.leden || []).filter((m) => m.wikidata === q).length, 0);
};

const cost = (calls) => priceLabel(calls * config.sam_usd, config.betaald, config.taal, t);
const museCost = (usd) => priceLabel(usd, config.betaald, config.taal, t);

// Where the waiting feedback goes: the section whose button was clicked last;
// a click in the image (point mode) shows it under Aanwijzen.
const where = ref("top");
let clicked = { section: "top", at: 0 };
// How long a click waits for its work to start (time to read and confirm the cost window).
const CLICK_WAITS_MS = 5 * 60 * 1000;
// How many objects on the image came from a suggested term (not those in the trash).
// The objects found with a word: also under a merged word ("ook") and inside a group (wish Olaf).
const termIds = (term) => objectsWithTerm(props.objects, term);
function termCount(term) {
  return termIds(term).length;
}

const termLabel = (term) => (config.taal === "nl" ? term.nl : term.en);

// Which search words were looked for on this page (wish Olaf): a chip with results is
// green, one that was searched but found nothing is grey with a 0. Remembered in this
// browser per file and page; what is on the image decides "found".
const { list: searched, set: setSearched } = useStoredList(computed(() => `cc-gezocht:${props.file.mid}:${props.page.n}`));
watch(
  () => props.lastResult,
  (result) => {
    if (!result || result.modus !== "prompt" || !result.prompt) return;
    const words = result.prompt.split(",").map((word) => word.trim().toLowerCase()).filter(Boolean);
    setSearched([...searched.value, ...words]);
  }
);
const wasSearched = (word) => searched.value.includes(String(word || "").toLowerCase());
const resultClass = (count, word) => ({ "cc-term-gevonden": count > 0, "cc-term-niets": !count && wasSearched(word) });

// The objects found with the AI's term (no own words any more: the pencil is gone, wish Olaf
// 12-11-2026). The old own words in this browser are forgotten, also those of the depicts
// items (pencil gone in 0.38.1).
const termObjectIds = (term) => termIds(term.en);
const termHits = (term) => termObjectIds(term).length;
watch(
  () => [props.file.mid, props.page.n],
  ([mid, n]) => {
    removeStored(`cc-term-zoekwoord:${mid}:${n}`);
    removeStored(`cc-item-zoekwoord:${mid}`);
  },
  { immediate: true }
);

// Terms left out of "Detect all" (by their English term), per file and page,
// remembered in this browser only (a convenience; nothing is stored on the server).
const { list: excluded, set: setExcluded, toggle: toggleTerm, invert: invertTerms } = useStoredList(computed(() => `cc-termen-uit:${props.file.mid}:${props.page.n}`));
const includedTerms = computed(() => newTerms.value.filter((term) => !excluded.value.includes(term.en)));
// Once the ticked terms were looked for, the button says "again", like for the depicts items (wish Olaf).
const termsLabel = computed(() => {
  const all = includedTerms.value.length === newTerms.value.length;
  const again = includedTerms.value.some((term) => termHits(term) || wasSearched(term.en));
  if (again) return all ? "panel.detect_suggestions_again" : "panel.detect_chosen_again";
  return all ? "panel.detect_suggestions" : "panel.detect_chosen";
});

function termTitle(term) {
  const parts = [t("panel.term_expected", { n: term.aantal, where: term.waar }), t("panel.term_found", { n: termHits(term) })];
  if (props.trashTerms[term.en]) parts.push(t("panel.term_trashed", { n: props.trashTerms[term.en] }));
  return parts.join(" · ");
}

// What the AI made for this image, as it is now (a part can have been removed, or the AI found
// no text): one line each for the description, the text and the search terms.
const LENGTHS = ["kort", "normaal", "caption", "uitgebreid"];
const madeLines = computed(() => {
  const inv = props.inventory || {};
  const lengths = LENGTHS.filter((level) => inv.beschrijvingen?.[level]).length || (inv.samenvatting || inv.paginasoort ? 1 : 0);
  const description = lengths === 4 ? t("panel.suggestions_done_description") : lengths ? t("panel.suggestions_done_description_some", { n: lengths }) : t("panel.suggestions_done_no_description");
  const text = inv.tekst ? t("panel.suggestions_done_text") : t("panel.suggestions_done_no_text");
  const n = inv.zoektermen?.length || 0;
  const terms = !n
    ? t("panel.suggestions_done_no_terms")
    : `${n === 1 ? t("panel.suggestions_done_terms_one") : t("panel.suggestions_done_terms", { n })} ${t(suggestionTotals.value.found ? "panel.suggestions_done_terms_found" : "panel.suggestions_done_terms_none_found")}`;
  return [
    { text: description, part: "beschrijving" },
    { text: text, part: "beschrijving" }, // the text from the image is shown with the description
    { text: terms, part: "zoektermen" },
  ];
});
// "a [word] here" → pieces, the bracketed one a link.
const linkPieces = (text) => String(text).split(/(\[[^\]]+\])/).filter(Boolean).map((piece) => (piece.startsWith("[") && piece.endsWith("]") ? { text: piece.slice(1, -1), link: true } : { text: piece, link: false }));
// Open a part of the AI suggestions and bring it into view.
async function showPart(part) {
  open[part] = true;
  await nextTick();
  document.querySelector(`[data-deel="${part}"]`)?.scrollIntoView({ behavior: "smooth", block: "start" });
}
const suggestionTotals = computed(() => {
  const terms = newTerms.value;
  const found = terms.map((term) => termObjectIds(term));
  return {
    // Each object once, also when several terms found it (merged finds).
    found: new Set(found.flat()).size,
    terms: found.filter((ids) => ids.length).length,
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
    // The click counts until the work it asked for starts, also when a window to confirm the cost
    // came in between (the busy bar starts only after confirming; bug found by Olaf 13-11-2026):
    // the first busy after a click is that click's, within a few minutes. Used once.
    const recent = clicked.at && Date.now() - clicked.at < CLICK_WAITS_MS;
    where.value = recent ? clicked.section : props.pointMode ? "point" : props.drawMode ? "draw" : "top";
    clicked = { ...clicked, at: 0 };
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
  if (result.fout) return "error";
  if (result.undone) return "success"; // Undo worked: the drawn object went to the trash
  // Pointing and drawing: about one object; a warning when nothing came of the click or the hint.
  if (result.modus === "punt") return result.outcome === "niets" ? "warning" : "success";
  if (result.modus === "rechthoek") return result.hint && !result.gevonden ? "warning" : "success";
  if (result.found || result.excluded) return "success";
  if (result.restored) return "success";
  return "warning"; // nothing new, merged, in a group or in the trash: to note, not an error
}

function resultText(result) {
  if (result.fout) return result.fout; // the request failed: its reason, here under the button
  if (result.undone) return result.undone;
  // Pointing and drawing: about one object.
  if (result.modus === "punt") {
    if (result.outcome === "niets") return result.hint ? t("panel.result_point_none_hint", { hint: result.hint }) : t("panel.result_point_none");
    return t(result.outcome === "bekend" ? "panel.result_point_known" : "panel.result_point_new", { name: result.name });
  }
  if (result.modus === "rechthoek") {
    if (!result.hint) return t("panel.result_rectangle", { name: result.name });
    return t(result.gevonden ? "panel.result_rectangle_hint" : "panel.result_rectangle_hint_none", { name: result.name, hint: result.hint });
  }
  const terms = result.prompt.split(",").map((s) => s.trim()).filter(Boolean);
  const what = result.modus === "commons" ? t("panel.result_commons") : terms.length > 1 ? t("panel.result_terms", { n: terms.length }) : t("panel.result_term", { term: terms[0] || "" });
  const elsewhere = elsewhereParts(result);
  if (!result.found && !result.excluded && !elsewhere.length) return t("panel.result_none", { what });
  const parts = [];
  if (result.found) parts.push(result.found === 1 ? t("panel.result_one", { what }) : t("panel.result_found", { n: result.found, what }));
  else if (!result.excluded) parts.push(t("panel.result_nothing_new", { what }));
  if (result.excluded) parts.push(t("panel.result_excluded", { n: result.excluded }));
  return parts.join(" ");
}

// Hits that are not shown as an object of their own, each with the reason.
function elsewhereParts(result) {
  if (!result || result.fout || result.modus === "punt" || result.modus === "rechthoek") return [];
  return [
    result.merged && t(result.merged === 1 ? "panel.result_merged_one" : "panel.result_merged", { n: result.merged, names: (result.holders || []).join(", ") }),
    result.inGroup && t(result.inGroup === 1 ? "panel.result_in_group_one" : "panel.result_in_group", { n: result.inGroup }),
    result.inTrash && t(result.inTrash === 1 ? "panel.result_in_trash_one" : "panel.result_in_trash", { n: result.inTrash }),
    result.hidden && t(result.hidden === 1 ? "panel.result_hidden_one" : "panel.result_hidden", { n: result.hidden }),
    result.restored && t(result.restored === 1 ? "panel.result_restored_one" : "panel.result_restored", { n: result.restored }),
  ].filter(Boolean);
}
// "Also found: …" as a paragraph of its own under the message (wish Olaf), with the list below it.
function resultAlso(result) {
  const elsewhere = elsewhereParts(result);
  return elsewhere.length ? `${t("panel.result_also")} ${elsewhere.join("; ")}.` : "";
}

// The objects found hits were merged into, as a bulleted list under the message (wish Olaf).
const mergedInto = (result) => (result && result.merged && result.holders) || [];
// Everything the outcome message of a section shows (ResultMessage.vue), in one place.
const resultProps = (result) => ({ result, type: resultType(result), text: resultText(result), also: resultAlso(result), merged: mergedInto(result) });

// A search with terms that found nothing (not "from Commons", pointing or drawing).
function isNone(result) {
  return Boolean(result) && !result.fout && result.modus === "prompt" && !result.found && !result.excluded && !result.merged && !result.inGroup && !result.inTrash && !result.hidden && !result.restored;
}
// After nothing was found: open Search with the term filled in, ready to change it.
async function trySearch(result) {
  setOpen("search", true);
  prompt.value = result.prompt.split(",").length === 1 ? result.prompt.trim() : "";
  await nextTick();
  const input = document.querySelector(".cc-zoek input");
  input?.scrollIntoView({ block: "center", behavior: "smooth" });
  input?.focus();
  input?.select();
}
// Or open Point or draw with that way switched on at once: click the object, or draw around it.
// Only unfold Point or draw and scroll to it, no way switched on (link under 'Depicts, without a region').
// Open the AI suggestions and bring them into view.
async function showSuggestions() {
  setOpen("suggestions", true);
  await nextTick();
  document.getElementById("cc-ai-suggesties")?.scrollIntoView({ block: "start", behavior: "smooth" });
}
// Open Search and put the cursor in its field, keeping what is typed there.
async function showSearch() {
  setOpen("search", true);
  await nextTick();
  const input = document.querySelector(".cc-zoek input");
  input?.scrollIntoView({ block: "center", behavior: "smooth" });
  input?.focus();
}
async function showPointOrDraw() {
  setOpen("point", true);
  await nextTick();
  document.querySelector(".cc-sectie-aanwijzen")?.scrollIntoView({ block: "center", behavior: "smooth" });
}
async function tryPoint(mode = "point") {
  setOpen("point", true);
  open[mode === "draw" ? "tekenen" : "aanwijzen"] = true;
  emit(mode === "draw" ? "draw-mode" : "point-mode", true);
  await nextTick();
  document.querySelector(".cc-sectie-aanwijzen")?.scrollIntoView({ block: "center", behavior: "smooth" });
}

function search() {
  const words = cleanText(prompt.value); // only spaces or invisible characters: nothing to search
  if (words) act("search", "detect", { modus: "prompt", prompt: words });
}
</script>
