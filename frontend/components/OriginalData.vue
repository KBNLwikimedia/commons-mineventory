<!--
  "Gegevens van deze afbeelding" (functional design 9.7, backlog 15b): depicts (P180) and
  captions for the whole image. Brings together what the file has on Commons and what
  this app proposes (items chosen for cut-outs, the AI search terms, the Wikidata
  suggestions of "Wat staat hierop?"), and keeps the user's choices as a draft.
  Step by step (wish Olaf 13-11-2026): 1. what is on Commons already (only a place can be
  added), 2. new depicts, 3. captions (any language), 4. review everything that would change.
  Nothing is ever removed from Commons. Free: nothing goes to a model, nothing changes on
  Commons; saving to Commons is phase 2.
-->
<template>
  <cdx-dialog
    :open="open"
    class="cc-origineel"
    :title="t('original.title')"
    :subtitle="file.titel"
    :use-close-button="true"
    :close-button-label="t('actions.close')"
    @update:open="(value) => !value && emit('close')"
  >
    <step-bar v-if="data" v-model="step" :steps="steps" :label="t('original.steps_label')" />
    <!-- Going on with a draft, or starting afresh (wish Olaf 13-11-2026): say so at the top. -->
    <cdx-message v-if="draftState" type="warning" :allow-user-dismiss="true" :dismiss-button-label="t('actions.close')" class="cc-origineel-concept" @user-dismissed="draftState = ''">
      <template v-if="draftState === 'loaded'">
        {{ t("original.draft_loaded", { when: formatStamp(keptDraft?.bewaard_op, config.taal) }) }}
        <button type="button" class="cc-link" @click="startFresh">{{ t("original.draft_fresh") }}</button>
      </template>
      <template v-else>
        {{ t("original.draft_fresh_done", { when: formatStamp(keptDraft?.bewaard_op, config.taal) }) }}
        <button type="button" class="cc-link" @click="backToDraft">{{ t("original.draft_back") }}</button>
      </template>
    </cdx-message>
    <busy-note v-if="loading" :message="t('original.loading')" />
    <cdx-message v-if="error" type="error">{{ error }}</cdx-message>

    <template v-if="data">
      <!-- 1. Depicts already on Commons: read only, except adding a place (decision 3). -->
      <section v-show="step === 'bestaand'" class="cc-origineel-stap">
        <h3 class="cc-origineel-stapkop">{{ t("original.step_n", { n: stepNumber("bestaand"), total: steps.length }) }} · {{ t("original.step_existing") }}</h3>
        <p class="cc-uitleg">
          {{ t("original.existing_intro") }}
          <a :href="commonsUrl" target="_blank" rel="noopener">{{ t("panel.commons_edit_link") }}</a>
        </p>
        <p v-if="!commonsItems.length" class="cc-uitleg">{{ t("original.on_commons_none") }}</p>
        <!-- As the "Structured data" tab on Commons (wish Olaf 13-11-2026): a framed block
             "Items portrayed in this file / depicts", one light bar per item, in the order of
             Commons. Found here: a tick box to add the place; the others stay as they are. -->
        <div v-if="commonsItems.length" class="cc-sdc-blok">
          <div class="cc-sdc-blok-kop">
            <div>
              <div class="cc-sdc-blok-titel">{{ t("original.sdc_depicts_title") }}</div>
              <a class="cc-sdc-eigenschap" href="https://www.wikidata.org/wiki/Property:P180" target="_blank" rel="noopener">{{ t("original.sdc_depicts_property") }}</a>
            </div>
          </div>
          <p class="cc-uitleg">{{ t("original.existing_counts", { found: foundItems.length, total: commonsItems.length }) }} {{ foundItems.length ? t("original.add_position_help") : "" }}</p>
          <!-- All · None · Invert on the left, right above the tick boxes they set (wish Olaf 13-11-2026). -->
          <tick-links
            v-if="foundItems.length"
            class="cc-klein cc-sdc-selectie"
            @all="foundItems.forEach((item) => setBoxes(item, item.objects.map((o) => o.id)))"
            @none="foundItems.forEach((item) => setBoxes(item, []))"
            @invert="foundItems.forEach((item) => setBoxes(item, item.objects.map((o) => o.id).filter((id) => !boxesFor(item).includes(id))))"
          />
          <!-- A table with fixed columns (wish Olaf 13-11-2026): every row lines up. -->
          <div class="cc-sdc-rij cc-sdc-tabelkop cc-klein" aria-hidden="true">
            <span></span><span></span>
            <span>{{ t("original.col_item") }}</span>
            <span>{{ t("original.col_q") }}</span>
            <span>{{ t("original.col_description") }}</span>
            <span>{{ t("original.col_status") }}</span>
            <span></span>
          </div>
          <ul class="cc-sdc-items">
            <li v-for="item in existingRows" :key="item.q" class="cc-sdc-item" :class="{ 'cc-sdc-item-blijft': !item.canAddPosition }">
              <div class="cc-sdc-rij">
                <!-- Ticked: all its objects; half ticked: some of them (choose in the list below). -->
                <input
                  v-if="item.canAddPosition"
                  type="checkbox"
                  :checked="boxesFor(item).length === item.objects.length"
                  :indeterminate="boxesFor(item).length > 0 && boxesFor(item).length < item.objects.length"
                  :aria-label="t('original.add_position_for', { item: item.label })"
                  @change="setBoxes(item, $event.target.checked ? item.objects.map((o) => o.id) : [])"
                />
                <span v-else class="cc-sdc-geen-vinkje" aria-hidden="true"></span>
                <img class="cc-item-beeld cc-item-beeld-klein" :src="itemImage(item.q, 60)" alt="" loading="lazy" @mouseenter="showZoom($event, item.q)" @mouseleave="hideZoom" @error="hideImage" />
                <a class="cc-sdc-label" :href="`https://www.wikidata.org/wiki/${item.q}`" target="_blank" rel="noopener">{{ item.label }}</a>
                <span class="cc-klein cc-sdc-q">{{ item.q }}</span>
                <!-- The item's description on Wikidata, in the language of the interface only (wish Olaf). -->
                <span class="cc-klein cc-sdc-beschrijving">{{ item.description }}</span>
                <span class="cc-klein cc-sdc-status">
                  <span v-if="item.positions" class="cc-merkje">{{ t("original.with_position", { n: item.positions }) }}</span>
                  <template v-else-if="item.canAddPosition">{{ boxesFor(item).length ? boxesText(item) : t("original.found_here", { n: item.found }) }}</template>
                  <span v-else :title="t('original.not_found_title')">{{ t("original.not_found_stays") }}</span>
                </span>
                <!-- Which of the objects (wish Olaf 13-11-2026): an expander per item, in a column of its own. -->
                <span class="cc-klein cc-sdc-actie">
                  <button v-if="item.canAddPosition && item.objects.length > 1" type="button" class="cc-link cc-sdc-kies" :aria-expanded="Boolean(openItems[item.q])" @click="openItems[item.q] = !openItems[item.q]">
                    {{ openItems[item.q] ? t("original.boxes_hide") : t("original.boxes_choose", { n: item.objects.length }) }}
                  </button>
                </span>
              </div>
              <div v-if="item.canAddPosition && item.objects.length > 1 && openItems[item.q]" class="cc-sdc-objecten">
                <p class="cc-uitleg">{{ t("original.boxes_help", { item: item.label }) }}</p>
                <tick-links
                  class="cc-klein cc-sdc-selectie"
                  @all="setBoxes(item, item.objects.map((o) => o.id))"
                  @none="setBoxes(item, [])"
                  @invert="setBoxes(item, item.objects.map((o) => o.id).filter((id) => !boxesFor(item).includes(id)))"
                />
                <ul>
                  <li v-for="(obj, k) in item.objects" :key="obj.id">
                    <label>
                      <input type="checkbox" :checked="boxesFor(item).includes(obj.id)" @change="toggleBox(item, obj.id, $event.target.checked)" />
                      <!-- Hover: a larger view of the cut-out, as for the items' images (wish Olaf 13-11-2026). -->
                      <img
                        class="cc-sdc-duim"
                        :src="`${objectPath(file.mid, page.n, obj.id)}/uitsnede.jpg?w=64&v=${obj.positie || ''}`"
                        alt=""
                        loading="lazy"
                        @mouseenter="showZoom($event, item.q, `${objectPath(file.mid, page.n, obj.id)}/uitsnede.jpg?w=480&v=${obj.positie || ''}`, 420)"
                        @mouseleave="hideZoom"
                      />
                      <!-- Its own name when it has one, else the item's label with a number. -->
                      {{ obj.naam && obj.naam.toLowerCase() !== (item.label_en || "").toLowerCase() ? obj.naam : `${item.label} ${k + 1}` }}
                    </label>
                  </li>
                </ul>
              </div>
            </li>
          </ul>
        </div>
      </section>

      <!-- 2. New depicts: the proposals, search terms without objects, an item of your own. -->
      <section v-show="step === 'nieuw'" class="cc-origineel-stap">
        <h3 class="cc-origineel-stapkop">{{ t("original.step_n", { n: stepNumber("nieuw"), total: steps.length }) }} · {{ t("original.step_new") }}</h3>
        <p class="cc-uitleg">{{ t("original.new_intro") }}</p>
        <!-- The proposals, with an (i) that explains a row, and All · None · Invert (wish Olaf). -->
        <h4 class="cc-commons-kop">{{ t("original.proposals") }} <info-dialog :title="t('original.proposals')" :label="t('panel.info_label', { section: t('original.proposals') })" :paragraphs="proposalsInfo" /></h4>
        <!-- On the left, right above the tick boxes (wish Olaf 13-11-2026). -->
        <tick-links
          v-if="proposalRows.length"
          class="cc-klein cc-sdc-selectie cc-sdc-selectie-rijen"
          @all="proposalRows.forEach((row) => (row.checked = true))"
          @none="proposalRows.forEach((row) => (row.checked = false))"
          @invert="proposalRows.forEach((row) => (row.checked = !row.checked))"
        />
        <busy-note v-if="resolving" :message="t('original.resolving')" />
        <p v-if="!proposalRows.length && !resolving" class="cc-uitleg">{{ t("original.proposals_none") }}</p>
        <ul class="cc-origineel-rijen">
          <original-row
            v-for="row in proposalRows"
            :key="row.key"
            v-bind="rowProps(row)"
            :ai="row.ai"
            :changeable="Boolean(row.terms.length || row.bronnen.includes('eigen'))"
            v-on="rowEvents(row)"
          >
            <template #source>
              <div class="cc-klein cc-origineel-bron">
                {{ row.bronnen.map((b) => t(`original.source_${b}`)).join(" · ") }}<template v-if="row.terms.length"> ({{ row.terms.join(", ") }})</template>
                <template v-if="row.objecten.length"> · {{ t("original.objects", { n: row.objecten.length }) }}</template>
              </div>
              <!-- Rule 4 of 9.7: an object whose cut-out is saved gets its region on the original
                   with its upload; one statement per object, not two. -->
              <div v-if="row.objecten.some((o) => o.upload)" class="cc-klein cc-origineel-upload">
                {{ t("original.with_upload", { n: row.objecten.filter((o) => o.upload).length, names: row.objecten.filter((o) => o.upload).map((o) => o.naam).join(", ") }) }}
              </div>
            </template>
            <!-- "With place", with an (i) that explains it for this very row (wish Olaf). -->
            <span v-if="row.objecten.length && !data.meerdere_paginas" class="cc-origineel-met-positie">
              <!-- The property links to Wikidata (a link inside a label does not tick the box). -->
              <label>
                <input v-model="row.met_positie" type="checkbox" />
                {{ t("original.with_position_before") }}
                (<a href="https://www.wikidata.org/wiki/Property:P2677" target="_blank" rel="noopener">P2677</a>)
                {{ t("original.with_position_after") }}
              </label>
              <info-dialog
                :title="t('original.with_position_title')"
                :label="t('panel.info_label', { section: t('original.with_position_title') })"
                :paragraphs="[
                  t('original.with_position_on', { item: row.label, n: row.objecten.length }),
                  t('original.with_position_off', { item: row.label }),
                  t('original.with_position_default'),
                ]"
              />
            </span>
          </original-row>
        </ul>
        <!-- Search terms without a found object: under their own heading, only along when ticked. -->
        <div v-if="emptyRows.length" class="cc-origineel-leeg">
          <h4 class="cc-commons-kop">{{ t("original.terms_without_objects", { n: emptyRows.length }) }}</h4>
          <ul class="cc-origineel-rijen">
            <original-row v-for="row in emptyRows" :key="row.key" v-bind="rowProps(row)" ai changeable v-on="rowEvents(row)">
              <template #source>
                <div class="cc-klein cc-origineel-bron">{{ t("original.source_zoekterm") }} ({{ row.terms.join(", ") }}) · {{ t("original.no_objects") }}</div>
              </template>
            </original-row>
          </ul>
        </div>
        <!-- A row removed with the bin: yellow, with Undo (wish Olaf 13-11-2026). -->
        <undo-message :note="rowNote" />
        <p v-if="hidden.length" class="cc-klein">
          {{ t("original.hidden_rows", { n: hidden.length }) }}
          <button type="button" class="cc-link" @click="hidden = []">{{ t("original.hidden_show") }}</button>
        </p>
        <!-- Another item, for what the AI did not find. -->
        <div class="cc-origineel-zoek">
          <h4 class="cc-commons-kop"><label for="cc-origineel-eigen">{{ t("original.add_item") }}</label></h4>
          <cdx-text-input clearable id="cc-origineel-eigen" v-model="ownText" :placeholder="t('original.search_placeholder')" @update:model-value="searchOwn" />
          <ul class="cc-origineel-treffers">
            <li v-for="hit in ownHits" :key="hit.q">
              <button type="button" class="cc-link" @click="addOwn(hit)">{{ hit.label }}</button>
              <span class="cc-klein"> ({{ hit.q }}) {{ hit.beschrijving }}</span>
            </li>
          </ul>
        </div>
      </section>

      <!-- 3. Captions: per language; add, replace by the AI proposal, or write your own; any language. -->
      <section v-show="step === 'bijschriften'" class="cc-origineel-stap">
        <h3 class="cc-origineel-stapkop">{{ t("original.step_n", { n: stepNumber("bijschriften"), total: steps.length }) }} · {{ t("original.step_captions") }}</h3>
        <p class="cc-uitleg">{{ t("original.captions_intro") }}</p>
        <div v-if="data.ai_caption.beschrijvingsniveau && data.ai_caption.beschrijvingsniveau !== 'caption'" class="cc-origineel-caption-vraag">
          <p class="cc-uitleg">{{ t("original.caption_level_note") }}</p>
          <!-- Ask the AI for a Commons caption (paid, with the confirmation of the app); the
               current description goes to Earlier descriptions. Or shorten it here, free. -->
          <cdx-button action="progressive" :disabled="busy" @click="emit('ask-caption')">
            {{ t("original.caption_ask") }} <span class="cc-kosten">{{ cost }}</span>
          </cdx-button>
          <busy-note v-if="busy" :message="t('busy.muse_page')" />
        </div>
        <p v-if="!data.ai_caption.nl && !data.ai_caption.en" class="cc-uitleg">{{ t("original.caption_no_ai") }}</p>
        <div v-for="lang in captionLangs" :key="lang" class="cc-origineel-caption" :data-taal="lang">
          <h4 class="cc-commons-kop">
            <span class="cc-taal-code">{{ lang }}</span> {{ langName(lang) }}
            <button v-if="captions[lang].added" type="button" class="cc-link cc-klein" @click="removeLanguage(lang)">{{ t("original.caption_lang_remove") }}</button>
          </h4>
          <p class="cc-klein"><strong>{{ t("original.caption_now") }}</strong> {{ captions[lang].existing || t("original.caption_none") }}</p>
          <p v-if="captions[lang].ai" class="cc-klein">
            <strong>{{ t("original.caption_ai") }}</strong> {{ captions[lang].ai }} <ai-badge kind="beschrijving" :model="''" />
          </p>
          <p v-if="captions[lang].ai && clean(captions[lang].ai).length > CAPTION_MAX" class="cc-klein cc-te-lang">
            {{ t("original.caption_ai_too_long", { n: clean(captions[lang].ai).length, max: CAPTION_MAX }) }}
            <button type="button" class="cc-link" @click="shorten(lang)">{{ t("original.caption_shorten") }}</button>
          </p>
          <!-- Without a caption on Commons: add (ticked), with an editable text. -->
          <label v-if="!captions[lang].existing"><input v-model="captions[lang].include" type="checkbox" /> {{ t("original.caption_add") }}</label>
          <!-- With one: write it yourself (default for nl/en, from both texts), keep it, or replace it. -->
          <div v-else class="cc-origineel-keuze" role="radiogroup">
            <cdx-radio v-for="choice in ['zelf', 'houden', 'vervangen']" :key="choice" v-model="captions[lang].keuze" :name="`cc-caption-${lang}`" :input-value="choice" :disabled="choice === 'vervangen' && !captions[lang].ai">
              {{ t(`original.caption_choice_${choice}`) }}
            </cdx-radio>
          </div>
          <template v-if="showText(lang)">
            <cdx-text-area v-model="captions[lang].tekst" :rows="3" :aria-label="langName(lang)" :placeholder="t('original.caption_write')" />
            <p class="cc-klein" :class="{ 'cc-te-lang': length(lang) > CAPTION_MAX }">
              {{ t("original.caption_count", { n: length(lang), max: CAPTION_MAX }) }}
              <template v-if="captions[lang].start"> · <button type="button" class="cc-link" @click="resetText(lang)">{{ t("original.caption_reset") }}</button></template>
            </p>
          </template>
          <p v-if="captions[lang].existing && captions[lang].keuze === 'vervangen'" class="cc-klein">{{ t("original.caption_replace_note") }}</p>
        </div>
        <!-- Another language: a code or a name from the list; then write the caption yourself. -->
        <div class="cc-origineel-taal-erbij">
          <h4 class="cc-commons-kop"><label for="cc-origineel-taal">{{ t("original.caption_lang_add") }}</label></h4>
          <div class="cc-origineel-taal-invoer">
            <cdx-combobox
              id="cc-origineel-taal"
              v-model:selected="newLanguage"
              :menu-items="languageMenu"
              :placeholder="t('original.caption_lang_placeholder')"
              @keydown.enter="addLanguage"
            />
            <cdx-button action="progressive" :disabled="!newLanguage" @click="addLanguage">{{ t("original.caption_lang_add_button") }}</cdx-button>
          </div>
          <p v-if="languageError" class="cc-klein cc-te-lang">{{ languageError }}</p>
        </div>
      </section>

      <!-- 4. Review: exactly what would change on Commons, with a way back to each step. -->
      <section v-show="step === 'controleren'" class="cc-origineel-stap cc-origineel-controle">
        <h3 class="cc-origineel-stapkop">{{ t("original.step_n", { n: stepNumber("controleren"), total: steps.length }) }} · {{ t("original.step_check") }}</h3>
        <p class="cc-uitleg">{{ t("original.check_intro") }}</p>
        <p v-if="!changeCount" class="cc-uitleg">{{ t("original.check_nothing") }}</p>
        <div v-if="positionChanges.length" class="cc-origineel-groep">
          <h4 class="cc-commons-kop">{{ t("original.check_positions", { n: positionChanges.length }) }} <button type="button" class="cc-link cc-klein" @click="go('bestaand')">{{ t("original.check_edit") }}</button></h4>
          <ul class="cc-origineel-commons">
            <li v-for="item in positionChanges" :key="item.q">
              {{ t("original.check_positions_row", { item: item.label, n: item.chosen }) }}
              <span class="cc-klein">({{ item.q }})</span>
            </li>
          </ul>
        </div>
        <div v-if="depictsChanges.length" class="cc-origineel-groep">
          <h4 class="cc-commons-kop">{{ t("original.check_depicts", { n: depictsChanges.length }) }} <button type="button" class="cc-link cc-klein" @click="go('nieuw')">{{ t("original.check_edit") }}</button></h4>
          <ul class="cc-origineel-commons">
            <li v-for="item in depictsChanges" :key="item.q">
              {{ item.withPlace ? t("original.check_depicts_place", { item: item.label, n: item.statements }) : t("original.check_depicts_plain", { item: item.label }) }}
              <span class="cc-klein">({{ item.q }})</span>
            </li>
          </ul>
        </div>
        <div v-if="captionChanges.length" class="cc-origineel-groep">
          <h4 class="cc-commons-kop">{{ t("original.check_captions", { n: captionChanges.length }) }} <button type="button" class="cc-link cc-klein" @click="go('bijschriften')">{{ t("original.check_edit") }}</button></h4>
          <ul class="cc-origineel-commons">
            <li v-for="change in captionChanges" :key="change.lang">
              <span class="cc-taal-code">{{ change.lang }}</span> {{ langName(change.lang) }}: {{ t(change.existing ? "original.check_caption_changed" : "original.check_caption_added") }}
              <div v-if="change.existing" class="cc-klein cc-origineel-was"><strong>{{ t("original.check_old") }}</strong> {{ change.existing }}</div>
              <div class="cc-klein"><strong>{{ t("original.check_new") }}</strong> {{ change.tekst }}</div>
            </li>
          </ul>
        </div>
        <p class="cc-uitleg">{{ t(unchangedLanguages ? "original.check_unchanged" : "original.check_unchanged_depicts", { depicts: data.op_commons.beeldt_af.length, languages: unchangedLanguages }) }}</p>
        <div v-if="summaryText" class="cc-origineel-groep">
          <h4 class="cc-commons-kop">{{ t("original.check_summary") }}</h4>
          <p class="cc-klein"><code>{{ summaryText }}</code></p>
        </div>
      </section>
    </template>

    <!-- A larger view of an item's image while the mouse is on its thumbnail (wish Olaf);
         on the page itself, so the dialog's edges do not cut it off. -->
    <teleport to="body">
      <img v-if="zoom.show" class="cc-item-zoom" :src="zoom.src" alt="" :style="{ left: `${zoom.x}px`, top: `${zoom.y}px`, maxWidth: `${zoom.size}px`, maxHeight: `${zoom.size}px` }" />
    </teleport>

    <template #footer>
      <div class="cc-origineel-voet">
        <p class="cc-klein cc-origineel-concept-regel">
          {{ t("original.summary", { depicts: chosenRows.length + positionChanges.length, captions: captionChanges.length }) }}
          <!-- What a draft is, where it is kept and how you get it back (wish Olaf 13-11-2026). -->
          · <info-dialog :title="t('original.draft_info_title')" :label="t('panel.info_label', { section: t('original.draft_info_title') })" :text="t('original.draft_info_title')" :paragraphs="draftInfo" />
          <template v-if="data?.concept">
            · {{ t("original.draft_saved_at", { when: formatStamp(data.concept.bewaard_op, config.taal) }) }}
            · <button type="button" class="cc-link" @click="downloadDraft">{{ t("original.draft_download") }}</button>
          </template>
        </p>
        <cdx-message v-if="savedAt" type="success" :allow-user-dismiss="true" :dismiss-button-label="t('actions.close')" @user-dismissed="savedAt = ''">{{ t("original.saved", { when: formatStamp(savedAt, config.taal) }) }}</cdx-message>
        <p v-if="tooLong" class="cc-klein cc-te-lang">{{ t("original.too_long_in", { languages: tooLongIn.map(langName).join(", ") }) }}</p>
        <div class="cc-origineel-knoppen">
          <cdx-button @click="emit('close')">{{ t("actions.cancel") }}</cdx-button>
          <cdx-button v-if="stepIndex > 0" @click="go(steps[stepIndex - 1].key)">{{ t("original.step_previous") }}</cdx-button>
          <cdx-button v-if="!lastStep" action="progressive" :disabled="!data || saving || tooLong" @click="save">{{ t("original.save_draft") }}</cdx-button>
          <cdx-button v-if="!lastStep" action="progressive" weight="primary" :disabled="!data" @click="go(steps[stepIndex + 1].key)">
            {{ t("original.step_next", { step: steps[stepIndex + 1].label }) }}
          </cdx-button>
          <!-- Saving on Commons comes in phase 2 (after logging in): disabled, not hidden. -->
          <cdx-button v-if="lastStep" action="progressive" disabled :title="t('original.to_commons_later')">{{ t("original.to_commons") }}</cdx-button>
          <cdx-button v-if="lastStep" action="progressive" weight="primary" :disabled="!data || saving || tooLong" @click="save">{{ t("original.save_draft") }}</cdx-button>
        </div>
        <p v-if="lastStep" class="cc-uitleg">{{ t("original.to_commons_later") }}</p>
      </div>
    </template>
  </cdx-dialog>
</template>

<script setup>
import { computed, inject, nextTick, onBeforeUnmount, reactive, ref, watch } from "vue";
import { CdxButton, CdxCombobox, CdxDialog, CdxMessage, CdxRadio, CdxTextArea, CdxTextInput } from "@wikimedia/codex";
import { errorText, get, objectPath, pagePath, put } from "../api.js";
import { formatStamp, useT } from "../i18n.js";
import { itemImage, searchItems } from "../wikidata.js";
import { movableDialog } from "../movable.js";
import { commonsFileUrl } from "../state.js";
import { COMMON_LANGUAGES, editSummary, languageFromInput, languageName } from "../original.js";
import AiBadge from "./AiBadge.vue";
import OriginalRow from "./OriginalRow.vue";
import StepBar from "./StepBar.vue";
import TickLinks from "./TickLinks.vue";
import InfoDialog from "./InfoDialog.vue";
import BusyNote from "./BusyNote.vue";
import UndoMessage from "./UndoMessage.vue";
import { useUndoMessage } from "../undo.js";

const props = defineProps({
  open: { type: Boolean, default: false },
  file: { type: Object, required: true },
  page: { type: Object, required: true },
  // The page overview (for a new AI caption) and whether the app is busy asking it.
  inventory: { type: Object, default: null },
  busy: { type: Boolean, default: false },
  cost: { type: String, default: "" },
});
const emit = defineEmits(["close", "ask-caption"]);
const t = useT();
const config = inject("config");

// The AI writes captions in these languages; others you write yourself.
const AI_LANGUAGES = ["nl", "en"];
const CAPTION_MAX = 250;
const data = ref(null);
const loading = ref(false);
const resolving = ref(false);
const saving = ref(false);
const error = ref("");
const savedAt = ref("");
const rows = ref([]);
// Per existing statement without a box: the ids of the found objects that get theirs
// ({ q: [ids] }). Each box becomes a P2677 qualifier on that statement; no new
// statements for the same item (decision Olaf 13-11-2026).
const addPosition = ref({});
const openItems = reactive({});
const captions = reactive({});
const captionLangs = ref([]);
// "loaded": going on with a draft; "fresh": started afresh (the draft is still on the server
// until you keep a new one). Nothing on disk changes until "Concept bewaren". Declared here,
// before load() runs (the watch on "open" is immediate).
const draftState = ref("");
const keptDraft = ref(null);
// The image (P18) of a Wikidata item (itemImage); hidden when there is none.
const hideImage = (event) => (event.target.style.visibility = "hidden");
// A larger view beside the thumbnail, kept on screen; only for a thumbnail that loaded.
const ZOOM_SIZE = 260;
const zoom = reactive({ show: false, src: "", x: 0, y: 0, size: ZOOM_SIZE });
// `src`: another image than the item's own, such as the cut-out of an object (wish Olaf 13-11-2026).
function showZoom(event, q, src = "", size = ZOOM_SIZE) {
  const img = event.target;
  if (!img.naturalWidth) return;
  const rect = img.getBoundingClientRect();
  let x = rect.right + 8;
  if (x + size > window.innerWidth) x = Math.max(0, rect.left - size - 8);
  const y = Math.min(Math.max(0, rect.top - 40), window.innerHeight - size - 8);
  Object.assign(zoom, { show: true, src: src || itemImage(q, 240), x, y, size });
}
const hideZoom = () => (zoom.show = false);
const commonsUrl = computed(() => commonsFileUrl(props.file.titel, "P180"));
const langName = (lang) => languageName(lang, config.taal);

// -- The steps -----------------------------------------------------------------------------

const step = ref("bestaand");
// Without depicts on Commons there is no step 1 (wish Olaf 13-11-2026): three steps then.
const steps = computed(() => [
  ...(data.value?.op_commons.beeldt_af.length ? [{ key: "bestaand", label: t("original.step_existing"), count: positionChanges.value.length }] : []),
  { key: "nieuw", label: t("original.step_new"), count: chosenRows.value.length },
  { key: "bijschriften", label: t("original.step_captions"), count: captionChanges.value.length },
  { key: "controleren", label: t("original.step_check"), count: 0 },
]);
const stepNumber = (key) => steps.value.findIndex((s) => s.key === key) + 1;
const stepIndex = computed(() => steps.value.findIndex((s) => s.key === step.value));
const lastStep = computed(() => stepIndex.value === steps.value.length - 1);
// Another step: from its top (the dialog body scrolls, not the page).
watch(step, async () => {
  await nextTick();
  document.querySelector(".cc-origineel .cdx-dialog__body")?.scrollTo({ top: 0 });
});
const go = (key) => (step.value = key);

// -- Loading and building the rows ---------------------------------------------------------

// Move by the title bar, resize at the edges (wish Olaf), as the magnifier; Codex renders
// the dialog elsewhere in the page (teleport). Double-click the title bar to centre it again.
const mover = movableDialog(".cc-origineel", {
  storageKey: "cc-origineel-plaats",
  labels: { move: t("magnifier.move"), resize: t("magnifier.resize") },
  min: { width: 420, height: 300 },
});
watch(
  () => props.open,
  async (open) => {
    if (!open) {
      mover.disable();
      return;
    }
    load();
    await nextTick();
    mover.enable();
  },
  { immediate: true }
);
onBeforeUnmount(() => mover.disable());

async function load() {
  loading.value = true;
  error.value = "";
  savedAt.value = "";
  draftState.value = "";
  step.value = "bestaand";
  try {
    data.value = await get(`${pagePath(props.file.mid, props.page.n)}/origineel`);
    buildCaptions();
    await buildRows();
    keptDraft.value = data.value.concept;
    if (keptDraft.value) draftState.value = "loaded";
    // Nothing on Commons yet: start with the new depicts.
    if (!data.value.op_commons.beeldt_af.length) step.value = "nieuw";
  } catch (e) {
    error.value = errorText(t, e);
  } finally {
    loading.value = false;
  }
}

function newRow(fields) {
  return { key: "", q: null, label: "", beschrijving: "", bronnen: [], terms: [], objecten: [], checked: false, met_positie: true, ai: false, ...fields };
}

async function buildRows() {
  const d = data.value;
  const list = [];
  for (const item of d.gekozen) list.push(newRow({ key: `q:${item.q}`, q: item.q, label: item.label, bronnen: ["gekozen"], objecten: item.objecten, checked: true }));
  for (const term of d.zoektermen) list.push(newRow({ key: `t:${term.en}`, bronnen: ["zoekterm"], terms: [config.taal === "nl" ? term.nl : term.en], search: term.en, objecten: term.objecten, ai: true }));
  for (const s of d.suggesties) list.push(newRow({ key: `s:${s.term}`, bronnen: ["suggestie"], terms: [s.term], search: s.term, objecten: s.objecten, ai: true }));
  // Your own items from an earlier draft.
  for (const entry of d.concept?.beeldt_af || []) {
    if (entry.bron === "eigen") list.push(newRow({ key: `e:${entry.q}`, q: entry.q, label: entry.label, bronnen: ["eigen"], checked: true, met_positie: false }));
  }
  // The AI terms are looked up on Wikidata (free, cached), a few at a time: the best hit.
  resolving.value = true;
  const open = list.filter((row) => row.search);
  for (let i = 0; i < open.length; i += 3) {
    await Promise.all(
      open.slice(i, i + 3).map(async (row) => {
        try {
          const hits = await searchItems(row.search, "en");
          const term = row.search.trim().toLowerCase();
          // The label exactly as the term first ("lemon" the fruit, not "LemON" the band),
          // then the same letters in another case, then a label containing it, else the first hit.
          const hit =
            hits.find((h) => h.label === row.search.trim()) ||
            hits.find((h) => (h.label || "").toLowerCase() === term) ||
            hits.find((h) => (h.label || "").toLowerCase().includes(term)) ||
            hits[0];
          if (hit) Object.assign(row, { q: hit.q, label: hit.label, beschrijving: hit.beschrijving || "" });
        } catch {
          // No answer from Wikidata: the row stays without an item (not shown).
        }
      })
    );
  }
  resolving.value = false;
  // The draft: what was chosen, with another item where the user picked one.
  const draft = d.concept?.beeldt_af;
  if (draft) {
    for (const row of list) {
      const stored = draft.find((e) => (row.search && e.term === row.search) || (!row.search && e.q === row.q));
      if (stored) Object.assign(row, { q: stored.q, label: stored.label, checked: true, met_positie: stored.met_positie });
      else row.checked = false;
    }
    hidden.value = [...(d.concept.verborgen || [])];
  }
  rows.value = list.filter((row) => row.q);
  // Boxes for existing statements from the draft; a bare Q-id (older drafts) is all its objects.
  addPosition.value = {};
  for (const entry of d.concept?.positie_bij_bestaande || []) {
    const q = typeof entry === "string" ? entry : entry.q;
    const all = merged.value.find((row) => row.q === q)?.objecten.map((o) => o.id) || [];
    const ids = typeof entry === "string" || !entry.objecten ? all : entry.objecten.filter((id) => all.includes(id));
    if (ids.length) addPosition.value[q] = ids;
  }
  // Without a draft every located object is ticked: you untick what is not right (wish Olaf 13-11-2026).
  if (!d.concept) for (const item of foundItems.value) addPosition.value[item.q] = item.objects.map((o) => o.id);
}

// The rows per item: the same item from several sources is one row (9.7).
const merged = computed(() => {
  const byQ = new Map();
  for (const row of rows.value) {
    const one = byQ.get(row.q);
    if (!one) {
      byQ.set(row.q, { ...row, members: [row], bronnen: [...row.bronnen], terms: [...row.terms], objecten: [...row.objecten] });
      continue;
    }
    one.members.push(row);
    for (const b of row.bronnen) if (!one.bronnen.includes(b)) one.bronnen.push(b);
    for (const term of row.terms) if (!one.terms.includes(term)) one.terms.push(term);
    for (const o of row.objecten) if (!one.objecten.some((x) => x.id === o.id)) one.objecten.push(o);
    one.ai = one.ai && row.ai;
  }
  // A checkbox of a merged row speaks for all its members.
  return [...byQ.values()].map((one) => reactiveRow(one));
});
function reactiveRow(one) {
  return {
    ...one,
    get checked() {
      return one.members.some((m) => m.checked);
    },
    set checked(value) {
      one.members.forEach((m) => (m.checked = value));
    },
    get met_positie() {
      return one.members.every((m) => m.met_positie);
    },
    set met_positie(value) {
      one.members.forEach((m) => (m.met_positie = value));
    },
  };
}

// What Commons already has, per item; an item there leaves the proposals (decision 2).
const commonsItems = computed(() => {
  const byQ = new Map();
  for (const s of data.value?.op_commons.beeldt_af || []) {
    const item = byQ.get(s.q) || { q: s.q, label: (config.taal === "en" ? s.label_en : s.label) || s.label || s.q, label_en: s.label_en || "", description: (s.beschrijving || {})[config.taal] || "", positions: 0 };
    if (s.positie) item.positions += 1;
    byQ.set(s.q, item);
  }
  for (const item of byQ.values()) {
    const found = merged.value.find((row) => row.q === item.q);
    item.objects = found ? found.objecten : [];
    item.found = item.objects.length;
    item.canAddPosition = !item.positions && item.found > 0 && !data.value.meerdere_paginas;
  }
  return [...byQ.values()];
});
// Step 1: the items found here, whose statement can get a place. Nothing can be removed.
const foundItems = computed(() => commonsItems.value.filter((item) => item.canAddPosition));
// Step 1: what a box can be added to on top, then the rest, each in the order of Commons (wish Olaf 13-11-2026).
const existingRows = computed(() => [...foundItems.value, ...commonsItems.value.filter((item) => !item.canAddPosition)]);
// The chosen objects of an item, in the order of its objects .
const boxesFor = (item) => item.objects.map((o) => o.id).filter((id) => (addPosition.value[item.q] || []).includes(id));
function setBoxes(item, ids) {
  const next = { ...addPosition.value };
  if (ids.length) next[item.q] = ids;
  else delete next[item.q];
  addPosition.value = next;
}
const toggleBox = (item, id, on) => setBoxes(item, on ? [...boxesFor(item), id] : boxesFor(item).filter((x) => x !== id));
// "3 of 7: 3 bounding boxes on this statement". All chosen boxes go onto the existing statement,
// as P2677 qualifiers; no new statements for the same item (wish Olaf 13-11-2026).
const boxesText = (item) => t("original.boxes_chosen", { k: boxesFor(item).length, n: item.objects.length });
const onCommons = computed(() => new Set(commonsItems.value.map((item) => item.q)));
// The (i) of the proposals: what a row shows and what "with place" means.
const proposalsInfo = computed(() => [1, 2, 3, 4, 5].map((n) => t(`original.info_${n}`)));
// Rows you removed with the bin (wish Olaf): out of view and unticked; kept in the draft.
const hidden = ref([]);
// Undo (only here, nothing was saved yet): the row back in view, ticked again when it was.
const rowNote = useUndoMessage(t);
function hideRow(row) {
  const q = row.q;
  const wasChecked = row.checked;
  row.checked = false;
  if (!hidden.value.includes(q)) hidden.value = [...hidden.value, q];
  rowNote.show("warning", t("feedback.row_hidden", { item: row.label || q }), () => {
    hidden.value = hidden.value.filter((h) => h !== q);
    if (wasChecked) {
      const back = merged.value.find((r) => r.q === q);
      if (back) back.checked = true;
    }
  }, { done: t("feedback.row_back", { item: row.label || q }) });
}
const visibleRows = computed(() => merged.value.filter((row) => !onCommons.value.has(row.q) && !hidden.value.includes(row.q)));
const proposalRows = computed(() => visibleRows.value.filter((row) => row.objecten.length || !row.bronnen.every((b) => b === "zoekterm")));
const emptyRows = computed(() => visibleRows.value.filter((row) => !row.objecten.length && row.bronnen.every((b) => b === "zoekterm")));
const chosenRows = computed(() => [...proposalRows.value, ...emptyRows.value].filter((row) => row.checked));

// -- Another item for a row, or an item of your own ---------------------------------------

const otherFor = ref(null);
const otherText = ref("");
const otherHits = ref([]);
let otherAsked = 0;
function startOther(row) {
  otherFor.value = row.key;
  otherText.value = row.terms[0] || row.label;
  searchOther(otherText.value);
}
async function searchOther(text) {
  const mine = ++otherAsked;
  if ((text || "").trim().length < 2) return (otherHits.value = []);
  const hits = await searchItems(text.trim(), config.taal).catch(() => []);
  if (mine === otherAsked) otherHits.value = hits;
}
// What a row (OriginalRow.vue) shows of the search for another item, and what it can ask.
const rowProps = (row) => ({ row, searching: otherFor.value === row.key, text: otherText.value, hits: otherHits.value });
const rowEvents = (row) => ({
  other: () => startOther(row),
  "update:text": (text) => (otherText.value = text),
  search: searchOther,
  choose: (hit) => chooseOther(row, hit),
  cancel: () => (otherFor.value = null),
  hide: () => hideRow(row),
  zoom: showZoom,
  unzoom: hideZoom,
});
function chooseOther(row, hit) {
  for (const member of row.members) Object.assign(member, { q: hit.q, label: hit.label, beschrijving: hit.beschrijving || "", checked: true });
  otherFor.value = null;
  otherHits.value = [];
}
const ownText = ref("");
const ownHits = ref([]);
let ownAsked = 0;
async function searchOwn(text) {
  const mine = ++ownAsked;
  if ((text || "").trim().length < 2) return (ownHits.value = []);
  const hits = await searchItems(text.trim(), config.taal).catch(() => []);
  if (mine === ownAsked) ownHits.value = hits;
}
function addOwn(hit) {
  if (!rows.value.some((row) => row.q === hit.q)) {
    rows.value.push(newRow({ key: `e:${hit.q}`, q: hit.q, label: hit.label, beschrijving: hit.beschrijving || "", bronnen: ["eigen"], checked: true, met_positie: false }));
  } else {
    rows.value.filter((row) => row.q === hit.q).forEach((row) => (row.checked = true));
  }
  ownText.value = "";
  ownHits.value = [];
}

// -- Captions -------------------------------------------------------------------------------

const aiCaption = (lang) => (lang === "nl" ? data.value.ai_caption.nl : lang === "en" ? data.value.ai_caption.en : "") || "";
// One language: what Commons has, the AI proposal (nl/en), and the choice (from the draft).
function makeCaption(lang, stored) {
  const existing = data.value.op_commons.captions[lang] || "";
  const ai = aiCaption(lang);
  const start = existing ? [existing, ai].filter(Boolean).join("\n") : ai;
  const own = !AI_LANGUAGES.includes(lang);
  return {
    existing,
    ai,
    start,
    // A language you added yourself (no caption on Commons yet): it can go again.
    added: own && !existing,
    include: stored ? stored.keuze === "toevoegen" : own ? !existing : Boolean(ai) && clean(ai).length <= CAPTION_MAX,
    // An existing caption: write your own (decision 5) in nl/en; keep it in other languages.
    keuze: stored ? (existing ? stored.keuze : "toevoegen") : existing ? (own ? "houden" : "zelf") : "toevoegen",
    tekst: stored?.tekst || start,
  };
}
// Dutch and English first, then every language with a caption on Commons, then your own.
function buildCaptions() {
  for (const lang of Object.keys(captions)) delete captions[lang];
  const stored = data.value.concept?.captions || {};
  const onCommonsLangs = Object.entries(data.value.op_commons.captions || {}).filter(([, text]) => text).map(([lang]) => lang).sort();
  const order = [...new Set([...AI_LANGUAGES, ...onCommonsLangs, ...Object.keys(stored)])];
  for (const lang of order) captions[lang] = makeCaption(lang, stored[lang]);
  captionLangs.value = order;
}
// "Add a language": a code, or a name from the list.
const newLanguage = ref("");
const languageError = ref("");
const languageMenu = computed(() =>
  COMMON_LANGUAGES.filter((code) => !captionLangs.value.includes(code)).map((code) => ({ value: code, label: `${langName(code)} (${code})` }))
);
async function addLanguage() {
  const code = languageFromInput(newLanguage.value, config.taal);
  if (!code) {
    languageError.value = t("original.caption_lang_bad", { text: newLanguage.value });
    return;
  }
  languageError.value = "";
  if (!captions[code]) {
    captions[code] = { ...makeCaption(code, null), added: true, include: true };
    captionLangs.value = [...captionLangs.value, code];
  }
  newLanguage.value = "";
  await nextTick();
  const card = document.querySelector(`.cc-origineel [data-taal="${code}"]`);
  card?.scrollIntoView({ block: "center" });
  card?.querySelector("textarea")?.focus();
}
function removeLanguage(lang) {
  captionLangs.value = captionLangs.value.filter((l) => l !== lang);
  delete captions[lang];
}
const showText = (lang) => (captions[lang].existing ? captions[lang].keuze === "zelf" : captions[lang].include);
const clean = (text) => String(text || "").split(/\s+/).filter(Boolean).join(" ");
const length = (lang) => clean(captions[lang].tekst).length;
// At most 250 characters: after the last whole sentence that fits, else the last whole
// word with "…" (the same rule as the server's cap_caption).
function capCaption(text) {
  const all = clean(text);
  if (all.length <= CAPTION_MAX) return all;
  const head = all.slice(0, CAPTION_MAX);
  const end = Math.max(head.lastIndexOf(". "), head.lastIndexOf("! "), head.lastIndexOf("? "), head.endsWith(".") ? head.length - 1 : -1);
  if (end >= CAPTION_MAX / 2) return head.slice(0, end + 1);
  return all.slice(0, CAPTION_MAX - 1).replace(/\s+\S*$/, "").replace(/[\s,;:]+$/, "") + "…";
}
// Shorten the AI proposal into the text field (free), and choose to use it.
function shorten(lang) {
  const c = captions[lang];
  c.tekst = capCaption(c.ai);
  if (c.existing) c.keuze = "zelf";
  else c.include = true;
}
// A new AI caption (asked from here): the proposals follow; your own edits stay.
watch(
  () => [props.inventory?.samenvatting, props.inventory?.samenvatting_en, props.inventory?.beschrijvingsniveau],
  ([nl, en, level]) => {
    if (!data.value) return;
    data.value.ai_caption = { nl: nl || "", en: en || "", beschrijvingsniveau: level || null };
    for (const lang of AI_LANGUAGES) {
      const c = captions[lang];
      if (!c) continue;
      const untouched = clean(c.tekst) === clean(c.start);
      c.ai = (lang === "nl" ? nl : en) || "";
      c.start = c.existing ? [c.existing, c.ai].filter(Boolean).join("\n") : c.ai;
      if (untouched) c.tekst = c.start;
      if (!c.existing && clean(c.ai).length <= CAPTION_MAX && c.ai) c.include = true;
    }
  }
);

function resetText(lang) {
  captions[lang].tekst = captions[lang].start;
}
// What each language would do: nothing, add, replace, or your own text.
function captionChoice(lang) {
  const c = captions[lang];
  if (!c) return null;
  if (!c.existing) return c.include && clean(c.tekst) ? { keuze: "toevoegen", tekst: clean(c.tekst) } : { keuze: "houden", tekst: "" };
  if (c.keuze === "vervangen") return { keuze: "vervangen", tekst: clean(c.ai) };
  // Your own text only counts once you changed it: the untouched start (both texts) changes nothing.
  if (c.keuze === "zelf") return clean(c.tekst) === clean(c.start) ? { keuze: "houden", tekst: "" } : { keuze: "zelf", tekst: clean(c.tekst) };
  return { keuze: "houden", tekst: "" };
}
// The captions that would change on Commons (step 4).
const captionChanges = computed(() =>
  captionLangs.value
    .map((lang) => ({ lang, existing: captions[lang]?.existing || "", ...captionChoice(lang) }))
    .filter((change) => change.keuze !== "houden" && change.tekst && change.tekst !== clean(change.existing))
);
const tooLongIn = computed(() => captionChanges.value.filter((change) => change.tekst.length > CAPTION_MAX).map((change) => change.lang));
const tooLong = computed(() => tooLongIn.value.length > 0);

// -- Step 4: what would change --------------------------------------------------------------

const depictsChanges = computed(() =>
  chosenRows.value.map((row) => {
    const withPlace = Boolean(row.met_positie && row.objecten.length && !data.value.meerdere_paginas);
    return { q: row.q, label: row.label, withPlace, statements: withPlace ? row.objecten.length : 1 };
  })
);
const positionChanges = computed(() =>
  foundItems.value.map((item) => ({ q: item.q, label: item.label, chosen: boxesFor(item).length })).filter((item) => item.chosen)
);
const changeCount = computed(() => depictsChanges.value.length + positionChanges.value.length + captionChanges.value.length);
const unchangedLanguages = computed(() => Object.entries(data.value?.op_commons.captions || {}).filter(([lang, text]) => text && !captionChanges.value.some((c) => c.lang === lang)).length);
const summaryText = computed(() =>
  editSummary({
    depicts: depictsChanges.value.reduce((sum, item) => sum + item.statements, 0),
    positions: positionChanges.value.length,
    added: captionChanges.value.filter((c) => !c.existing).map((c) => c.lang),
    changed: captionChanges.value.filter((c) => c.existing).map((c) => c.lang),
  })
);

// -- The draft: kept on the app's server, per image and page --------------------------------

async function rebuild(concept) {
  data.value.concept = concept;
  hidden.value = [];
  buildCaptions();
  await buildRows();
}
async function startFresh() {
  await rebuild(null);
  draftState.value = "fresh";
}
async function backToDraft() {
  await rebuild(keptDraft.value);
  draftState.value = "loaded";
}
const draftInfo = computed(() => [1, 2, 3, 4].map((k) => t(`original.draft_info_${k}`, { mid: props.file.mid, n: props.page.n })));
// The draft as a JSON file, to look at or keep (free; nothing is asked).
function downloadDraft() {
  const blob = new Blob([JSON.stringify(data.value.concept, null, 2)], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `origineel-${props.file.mid}-pagina-${props.page.n}.json`;
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000);
}

// -- Saving the draft -----------------------------------------------------------------------

async function save() {
  saving.value = true;
  error.value = "";
  try {
    const body = {
      beeldt_af: chosenRows.value.map((row) => ({
        q: row.q,
        label: row.label,
        met_positie: Boolean(row.met_positie && row.objecten.length),
        objecten: row.objecten.map((o) => o.id),
        bron: row.bronnen[0],
        term: row.members.find((m) => m.search)?.search || null,
      })),
      positie_bij_bestaande: positionChanges.value.map((item) => ({ q: item.q, objecten: boxesFor(foundItems.value.find((f) => f.q === item.q)) })),
      verborgen: hidden.value,
      // Every language that has something to say; a language you added and left empty does not.
      captions: Object.fromEntries(
        captionLangs.value
          .map((lang) => [lang, captionChoice(lang)])
          .filter(([lang, choice]) => choice && (choice.keuze !== "houden" || !captions[lang].added))
      ),
    };
    const result = await put(`${pagePath(props.file.mid, props.page.n)}/origineel`, body);
    data.value.concept = result.concept;
    keptDraft.value = result.concept;
    draftState.value = "";
    savedAt.value = result.concept.bewaard_op;
  } catch (e) {
    error.value = errorText(t, e);
  } finally {
    saving.value = false;
  }
}
</script>
