<!--
  The magnifier (functional design 10.4): the cut-out, "Wat staat hierop?",
  the caption and the Commons concept, in tabs.
-->
<template>
  <cdx-dialog
    :open="open"
    class="cc-vergroter"
    :title="name"
    :use-close-button="true"
    :close-button-label="t('actions.close')"
    @update:open="emit('update:open', $event)"
  >
    <!-- Own header (the Codex classes), so the subtitle can link to the original on Commons, on every tab. -->
    <template #header>
      <div class="cdx-dialog__header__title-group">
        <h2 class="cdx-dialog__header__title">{{ name }}</h2>
        <p class="cdx-dialog__header__subtitle">
          {{ subtitle }}
          <template v-if="file.url">
            · {{ t("objects.source_file") }}
            <a :href="file.url" target="_blank" rel="noopener">{{ file.naam || String(file.titel || "").replace(/^File:/, "") }}</a>
            <cdx-icon :icon="cdxIconLinkExternal" size="x-small" />
          </template>
        </p>
      </div>
      <cdx-button
        class="cdx-dialog__header__close-button"
        weight="quiet"
        type="button"
        :aria-label="t('actions.close')"
        @click="emit('update:open', false)"
      >
        <cdx-icon :icon="cdxIconClose" />
      </cdx-button>
    </template>
    <cdx-tabs v-model:active="tab" :framed="true">
      <cdx-tab name="uitsnede" :label="t('magnifier.cutout')">
        <div v-if="object.masker" class="cc-weergave">
          <cdx-toggle-button-group v-model="view" :buttons="views" :aria-label="t('magnifier.view')" />
          <span class="cc-klein">{{ t(`concept.format_${view}`) }}</span>
        </div>
        <!-- While the cut-out is made (from a large original this can take a while): a progress bar and a text. -->
        <div class="cc-vergroter-beeld" :class="{ 'cc-laden': imageState === 'loading' }" :aria-busy="imageState === 'loading' ? 'true' : 'false'">
          <div v-if="imageState === 'loading'" class="cc-beeld-laden" role="status">
            <cdx-progress-bar :inline="true" :aria-label="t('magnifier.loading')" />
            <p class="cc-klein">{{ t("magnifier.loading") }}</p>
          </div>
          <cdx-message v-else-if="imageState === 'error'" type="error" :inline="true">{{ t("magnifier.load_error") }}</cdx-message>
          <img v-show="imageState === 'loaded'" :src="imageUrl" :alt="name" @load="imageState = 'loaded'" @error="imageState = 'error'" />
        </div>
        <dl class="cc-gegevens">
          <dt>{{ t("magnifier.source") }}</dt>
          <dd>{{ t(`source.${object.bron}`) }} <ai-badge v-if="object.bron === 'sam'" kind="detectie" :model="object.herkomst?.model || config.sam_model" :score="object.score" /><template v-if="object.wikidata"> · <a :href="`https://www.wikidata.org/wiki/${object.wikidata}`" target="_blank" rel="noopener">{{ object.wikidata }}</a></template></dd>
          <dt>{{ t("magnifier.box") }}</dt>
          <dd>{{ object.box.x }}, {{ object.box.y }} · {{ object.box.w }} × {{ object.box.h }} px</dd>
          <template v-if="savedInfo">
            <dt>{{ t("magnifier.saved") }}</dt>
            <dd>{{ savedInfo.text }}<template v-if="savedInfo.left">, <em class="cc-verloopt" :class="{ 'cc-verloopt-bijna': savedInfo.soon }">{{ savedInfo.left }}</em></template> <retention-info /><br /><span class="cc-klein">{{ savedInfo.title }}</span></dd>
          </template>
          <template v-if="object.herkomst?.p2677"><dt>P2677</dt><dd><code>{{ object.herkomst.p2677 }}</code></dd></template>
          <dt>
            {{ t("magnifier.caption") }}
            <info-button v-model:open="captionInfo" :label="t('magnifier.caption_info')" />
          </dt>
          <dd v-if="captionInfo" class="cc-info-tekst">
            <cdx-message type="notice" :inline="true">{{ t("magnifier.caption_help") }}</cdx-message>
          </dd>
          <dd class="cc-bijschrift">
            <span class="cc-invoer-met-knop" :class="{ 'met-tekstknop': removedCaption && !caption }">
              <cdx-text-input
                v-model="caption"
                :aria-label="t('magnifier.caption')"
                :placeholder="removedCaption ? t('magnifier.caption_removed', { text: removedCaption }) : ''"
              />
              <cdx-button
                v-if="removedCaption && !caption"
                class="cc-invoer-knop cc-invoer-knop-tekst"
                weight="quiet"
                size="small"
                action="progressive"
                @click="undoRemoveCaption"
              >
                ↶ {{ t("magnifier.undo") }}
              </cdx-button>
              <cdx-button
                v-else-if="caption || object.bijschrift?.tekst"
                class="cc-invoer-knop"
                weight="quiet"
                size="small"
                action="destructive"
                :aria-label="t('magnifier.caption_remove')"
                :title="t('magnifier.caption_remove')"
                @click="removeCaption"
              >
                <cdx-icon :icon="cdxIconTrash" size="small" />
              </cdx-button>
            </span>
            <cdx-button action="progressive" size="small" :disabled="caption === (object.bijschrift?.tekst || '')" @click="saveCaption">{{ t("actions.save_short") }}</cdx-button>
          </dd>
        </dl>
        <div class="cc-knoppen">
          <span class="cc-knopgroep" role="group" :aria-label="t('magnifier.download')">
            <span class="cc-klein">{{ t("magnifier.download") }}</span>
            <cdx-button action="progressive" @click="download('jpg')"><cdx-icon :icon="cdxIconDownload" /> JPG</cdx-button>
            <cdx-button action="progressive" @click="download('png')"><cdx-icon :icon="cdxIconDownload" /> PNG</cdx-button>
          </span>
          <span class="cc-knopgroep" role="group" :aria-label="t('magnifier.view_full')">
            <span class="cc-klein">{{ t("magnifier.view_full") }}</span>
            <cdx-button action="progressive" weight="quiet" @click="viewFull('jpg')"><cdx-icon :icon="cdxIconLinkExternal" /> JPG</cdx-button>
            <cdx-button action="progressive" weight="quiet" @click="viewFull('png')"><cdx-icon :icon="cdxIconLinkExternal" /> PNG</cdx-button>
          </span>
          <cdx-button action="progressive" v-if="!object.masker" @click="emit('refine', object)">{{ t("magnifier.refine_mask") }}</cdx-button>
          <cdx-button action="destructive" @click="emit('trashed', object.id)"><cdx-icon :icon="cdxIconTrash" /> {{ t("objects.trash") }}</cdx-button>
        </div>
      </cdx-tab>

      <cdx-tab name="beschrijving" :label="t('describe.title')">
        <!--
          One flow for the first and every later question:
          1. the answer (or, before the first one, what you get), with its own actions;
          2. the button that asks the AI, with the cost;
          3. folded away: AI modifiers, earlier descriptions, model and cost.
        -->

        <!-- Step 1 on the left; on the right the cut-out as the AI sees it (red frame, chosen space). -->
        <div class="cc-concept-kop">
        <div class="cc-concept-links">
        <!-- 1a. Before the first answer: what the AI will do, and the caption that goes along. -->
        <section v-if="!description" class="cc-uitleg-vooraf">
          <p>{{ t("describe.intro") }}</p>
          <p>{{ t("describe.intro_modifiers") }}</p>
          <p v-if="object.bijschrift?.tekst" class="cc-klein">
            {{ t("magnifier.caption") }}: <strong>{{ object.bijschrift.tekst }}</strong> — {{ t("describe.caption_goes_along") }}
          </p>
        </section>

        <!-- 1b. The answer. -->
        <section v-else class="cc-antwoord">
          <dl class="cc-gegevens">
            <dt>{{ t("describe.kind") }} <ai-badge kind="soort" :model="description.model" /></dt>
            <dd>{{ fixedValue("kind", description.soort) }} · {{ t("describe.certainty") }}: {{ fixedValue("certainty", description.zekerheid) }}</dd>
            <!-- Each text has its own pencil: edit it in place, with Opslaan and Annuleren. -->
            <template v-for="group in TEXT_GROUPS" :key="group.key">
              <template v-if="group.always || group.fields.some((f) => description[f]) || editingGroup === group.key">
                <dt>
                  {{ t(group.label) }}
                  <ai-badge v-if="group.ai" :model="description.model" :edited="group.fields.some((f) => aiEdited(f))" />
                </dt>
                <dd v-if="editingGroup === group.key" ref="editBox" class="cc-veld-bewerken">
                  <template v-for="field in group.fields" :key="field">
                    <!-- A label only for the NL/EN pairs; a single field has its label on the left. -->
                    <cdx-field :hide-label="group.fields.length === 1">
                      <template #label>{{ t(`describe.field_${field}`) }}</template>
                      <cdx-text-area v-if="group.long" v-model="fieldDraft[field]" :autosize="true" @keydown.esc.stop.prevent="cancelEditing" />
                      <cdx-text-input v-else v-model="fieldDraft[field]" @keydown.esc.stop.prevent="cancelEditing" @keydown.enter="saveEditing" />
                    </cdx-field>
                  </template>
                  <div class="cc-knoppen">
                    <cdx-button action="progressive" weight="primary" :disabled="!fieldChanged" @click="saveEditing">{{ t("actions.save_short") }}</cdx-button>
                    <cdx-button @click="cancelEditing">{{ t("actions.cancel") }}</cdx-button>
                  </div>
                </dd>
                <dd v-else :class="{ 'cc-gelezen-tekst': group.read }">
                  <template v-if="group.fields.length === 2">{{ description[group.fields[0]] }}<br /><i>{{ description[group.fields[1]] }}</i></template>
                  <template v-else>{{ description[group.fields[0]] }}</template>
                  <!-- The pencil after the text: edit this field in place. -->
                  <cdx-button
                    class="cc-veld-potlood"
                    weight="quiet"
                    action="progressive"
                    size="small"
                    :disabled="busy"
                    :aria-label="`${t('lightbox.edit')}: ${t(group.label)}`"
                    :title="`${t('lightbox.edit')}: ${t(group.label)}`"
                    @click="startEditing(group)"
                  >
                    <cdx-icon :icon="cdxIconEdit" size="small" />
                  </cdx-button>
                  <!-- Legible text read by the AI can also be removed with the bin. -->
                  <cdx-button
                    v-if="group.read"
                    weight="quiet"
                    size="small"
                    action="destructive"
                    :disabled="busy"
                    :aria-label="t('describe.remove_text')"
                    :title="t('describe.remove_text')"
                    @click="saveTexts({ [group.fields[0]]: '' })"
                  >
                    <cdx-icon :icon="cdxIconTrash" size="small" />
                  </cdx-button>
                </dd>
              </template>
            </template>
          </dl>

          <!-- What you can do with this answer: undo, go back to the AI text, or remove it. -->
          <div class="cc-knoppen cc-tekst-acties">
            <template v-if="description.bewerkt">
              <cdx-info-chip>{{ t("describe.edited") }}</cdx-info-chip>
              <button type="button" class="cc-link" @click="backToAi">{{ t("describe.back_to_ai") }}</button>
            </template>
            <span v-if="undoTexts" class="cc-klein">
              {{ t("describe.saved_edit") }}
              <button type="button" class="cc-link" @click="undoEdit">↶ {{ t("magnifier.undo") }}</button>
            </span>
            <cdx-button class="cc-rechts-uitlijnen" size="small" weight="quiet" action="destructive" :disabled="busy" @click="removeDescription">
              <cdx-icon :icon="cdxIconTrash" size="small" /> {{ t("describe.remove") }}
            </cdx-button>
          </div>
        </section>
        </div>
        <!-- The image moves to the AI modifiers while they are open, beside the slider (see glidePreview). -->
        <cutout-preview v-if="!previewInModifiers" class="cc-ai-voorbeeld" :src="modelInputUrl" :caption="t('describe.model_sees')" :large="largeInputUrl" :lightbox-title="name" :texts="readTexts" @save-text="saveTexts({ [$event.key]: $event.value })" />
        </div>

        <!-- 2. AI modifiers: steer the next question (hint, and the space around the cut-out). -->
        <cdx-accordion v-model="openModifiers" class="cc-beschrijving-blok" @cc-closing="previewInModifiers = false">
          <template #title>{{ t("describe.modifiers") }}</template>
          <template #description>{{ modifiersSummary || t("describe.modifiers_default") }}</template>
          <p class="cc-klein">{{ t("describe.modifiers_help") }}</p>
          <div class="cc-concept-kop cc-ai-sturing">
            <div class="cc-concept-links">
              <!-- An optional hint, e.g. "only the boy"; not the caption, not for Commons. -->
              <cdx-field class="cc-aanwijzing">
                <template #label>{{ t("describe.hint") }}</template>
                <template #help-text>{{ t("describe.hint_help") }}</template>
                <cdx-text-input v-model="hint" :placeholder="t('describe.hint_placeholder')" :maxlength="300" @keydown.enter="describe(Boolean(description))" />
              </cdx-field>
              <label class="cc-marge">
                <span>{{ t("describe.margin", { pct: Math.round(margin * 100) }) }}</span>
                <input v-model.number="margin" type="range" min="0" max="1" step="0.05" :aria-label="t('describe.margin_label')" />
                <span class="cc-klein">{{ t("describe.margin_help") }}</span>
              </label>
            </div>
            <cutout-preview v-if="previewInModifiers" class="cc-ai-voorbeeld" :src="modelInputUrl" :caption="t('describe.model_sees')" :large="largeInputUrl" :lightbox-title="name" :texts="readTexts" @save-text="saveTexts({ [$event.key]: $event.value })" />
          </div>
        </cdx-accordion>

        <!-- 3. Ask the AI, under the modifiers that steer it: the first time it is the main action. -->
        <div class="cc-vraag-knop">
          <cdx-button action="progressive" :weight="description ? 'normal' : 'primary'" :disabled="busy" @click="describe(Boolean(description))">
            {{ description ? t("describe.again") : t("describe.ask") }} <span class="cc-kosten">{{ costLabel }}</span>
          </cdx-button>
          <span v-if="modifiersSummary" class="cc-klein">{{ t("describe.with_modifiers", { what: modifiersSummary }) }}</span>
        </div>
        <div v-if="busy" class="cc-bezig" role="status">
          <cdx-progress-bar :inline="true" :aria-label="t('describe.busy', { seconds })" />
          <p class="cc-klein">{{ t("describe.busy", { seconds }) }}</p>
        </div>

        <!-- 3b. Earlier descriptions of this object, to choose from again (free). -->
        <cdx-accordion v-if="history.length" v-model="openHistory" class="cc-beschrijving-blok">
          <template #title>{{ t("describe.history", { n: history.length }) }}</template>
          <template #description>{{ t("describe.history_short") }}</template>
          <ul class="cc-geschiedenis-lijst">
            <li v-for="entry in history" :key="entry.tijdstempel + (entry.bewerkt ? 'b' : '')">
              <div>
                <strong>{{ language === "en" ? entry.onderwerp_en || entry.onderwerp : entry.onderwerp || entry.onderwerp_en }}</strong>
                <span class="cc-klein cc-geschiedenis-beschrijving">{{ language === "en" ? entry.beschrijving_en || entry.beschrijving : entry.beschrijving || entry.beschrijving_en }}</span>
                <span class="cc-klein cc-geschiedenis-meta">{{ historyMeta(entry) }}</span>
              </div>
              <cdx-button action="progressive" size="small" :disabled="busy" @click="restoreDescription(entry)">{{ t("describe.history_use") }}</cdx-button>
            </li>
          </ul>
        </cdx-accordion>

        <!-- Suggestions for depicts: the next step after a description. -->
        <section class="cc-blok" :class="{ 'cc-menu-open': lookupItems.length && ownTerm.trim().length >= 2 }">
          <h3 class="cc-blok-kop">
            {{ t("describe.suggestions") }}
            (<a href="https://www.wikidata.org/wiki/Property:P180" target="_blank" rel="noopener">P180</a>)
          </h3>
          <p v-if="description?.wikidata_suggesties?.length" class="cc-klein">{{ t("describe.suggestions_help") }}</p>
          <!-- Search Wikidata yourself (free, only reading). -->
          <!-- Autosuggest while typing (Codex Lookup); choosing an item adds it to 'beeldt af'.
               Enter or Zoeken shows all results as a list below. -->
          <form class="cc-zoek cc-wikidata-zoek" @submit.prevent="searchWikidata(ownTerm)">
            <cdx-lookup
              v-model:selected="lookupChoice"
              v-model:input-value="ownTerm"
              :menu-items="lookupItems"
              :menu-config="{ visibleItemLimit: 8 }"
              :start-icon="cdxIconSearch"
              :placeholder="t('describe.search_placeholder')"
              :aria-label="t('describe.search_label')"
              @input="onLookupInput"
              @update:selected="onLookupSelect"
            >
              <template #no-results><template v-if="lookupDone">{{ t("describe.search_none", { term: ownTerm }) }}</template><template v-else>{{ t("describe.search_busy") }}</template></template>
            </cdx-lookup>
            <cdx-button type="submit" action="progressive" :disabled="!ownTerm.trim()">{{ t("describe.search_button") }}</cdx-button>
          </form>
          <div v-if="description?.wikidata_suggesties?.length" class="cc-knoppen">
            <cdx-button action="progressive" v-for="term in description.wikidata_suggesties" :key="term" size="small" @click="searchWikidata(term)">
              <cdx-icon :icon="cdxIconSearch" /> {{ term }}
            </cdx-button>
          </div>
          <p v-if="searched && !hits.length" class="cc-klein">{{ t("describe.search_none", { term: searched }) }}</p>
          <ul v-if="hits.length" class="cc-treffers">
            <li v-for="hit in hits" :key="hit.q">
              <cdx-button size="small" weight="quiet" action="progressive" @click="addDepicts(hit)">+ {{ hit.label }}</cdx-button>
              <small><a :href="`https://www.wikidata.org/wiki/${hit.q}`" target="_blank" rel="noopener">{{ hit.q }}</a> · {{ hit.beschrijving }}</small>
            </li>
          </ul>
        </section>

        <!-- 3c. Secondary: which model, why, what this answer cost, and how far to trust it. -->
        <cdx-accordion v-if="plan || description" class="cc-beschrijving-blok">
          <template #title>{{ t("describe.model_block") }}</template>
          <template #description>{{ (description || plan).model }}</template>
          <p class="cc-klein">
            <template v-for="(part, i) in textParts(modelReason, reasonLinks)" :key="i">
              <a v-if="part.link" :href="part.link.href" target="_blank" rel="noopener">{{ part.link.label }}</a>
              <template v-else>{{ part.text }}</template>
            </template>
            <template v-if="description?.aanwijzing"><br />{{ t("describe.hint_used", { hint: description.aanwijzing }) }}</template>
            <template v-if="description && description.kosten_usd != null">
              <br />{{ t("describe.paid", { amount: money(description.kosten_usd, language) }) }}
              <template v-if="description.tokens?.invoer != null"> · {{ t("describe.tokens", { input: description.tokens.invoer, output: description.tokens.uitvoer }) }}</template>
            </template>
          </p>
          <p class="cc-klein cc-waarschuwing">{{ t("describe.caution") }}</p>
        </cdx-accordion>
      </cdx-tab>

      <cdx-tab name="commons" :label="t('concept.tab')">
        <concept-editor ref="editor" :mid="file.mid" :n="n" :object-id="object.id" @texts-changed="emit('changed', $event)" />
      </cdx-tab>
    </cdx-tabs>
    <cdx-message v-if="error" type="error" :inline="true">{{ error }}</cdx-message>
  </cdx-dialog>
</template>

<script setup>
import { computed, inject, nextTick, onBeforeUnmount, ref, watch } from "vue";
import { CdxAccordion, CdxButton, CdxDialog, CdxField, CdxIcon, CdxInfoChip, CdxLookup, CdxMessage, CdxProgressBar, CdxTab, CdxTabs, CdxTextArea, CdxTextInput, CdxToggleButtonGroup } from "@wikimedia/codex";
import { cdxIconClose, cdxIconDownload, cdxIconEdit, cdxIconLinkExternal, cdxIconSearch, cdxIconTrash } from "@wikimedia/codex-icons";
import { API, del, errorText, get, objectPath, patch, post, query } from "../api.js";
import { askConfirm, textParts } from "../confirm.js";
import { money, useT } from "../i18n.js";
import { forgetPlacement, makeMovable } from "../movable.js";
import { objectName, savedLabel } from "../state.js";
import AiBadge from "./AiBadge.vue";
import ConceptEditor from "./ConceptEditor.vue";
import CutoutPreview from "./CutoutPreview.vue";
import InfoButton from "./InfoButton.vue";
import RetentionInfo from "./RetentionInfo.vue";

const props = defineProps({
  open: { type: Boolean, default: false },
  file: { type: Object, required: true },
  n: { type: Number, required: true },
  object: { type: Object, required: true },
});
const emit = defineEmits(["update:open", "changed", "trashed", "refine"]);
const t = useT();
const language = inject("language", "nl");
const config = inject("config");
const tab = ref("uitsnede");
const caption = ref(props.object.bijschrift?.tekst || "");
const savedInfo = computed(() => savedLabel(props.object, t, language));
const captionInfo = ref(false);
const plan = ref(null);
const busy = ref(false);
const seconds = ref(0);
let ticker = null;
const error = ref("");
// The hint for the next "Ask again" (sent once, then cleared).
const hint = ref("");
// Folded away until wanted: the AI modifiers and the earlier descriptions.
const openModifiers = ref(false);
const openHistory = ref(false);

// Where the preview sits: beside the slider while the AI modifiers are open.
// It moves as soon as they start to open or close (the fold itself is
// animated by accordion-motion.js), and glides there: a copy flies from the
// old place to the new one, above everything, so the folding content does not
// clip it (FLIP: measure before and after, animate the difference).
const previewInModifiers = ref(false);
watch(openModifiers, (open) => {
  previewInModifiers.value = open;
});
function visiblePreview() {
  return [...document.querySelectorAll(".cc-vergroter .cc-ai-voorbeeld")].find((el) => el.offsetParent);
}
let previewBefore = null;
watch(previewInModifiers, () => (previewBefore = visiblePreview()?.getBoundingClientRect() || null), { flush: "pre" });
watch(previewInModifiers, async () => {
  await nextTick();
  const el = visiblePreview();
  if (!el || !previewBefore || window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
  // Measured after the accordion has started to open, so the target is known.
  await new Promise((resolve) => requestAnimationFrame(resolve));
  const after = el.getBoundingClientRect();
  const flyer = el.cloneNode(true);
  Object.assign(flyer.style, {
    position: "fixed", left: `${previewBefore.left}px`, top: `${previewBefore.top}px`, width: `${after.width}px`,
    margin: "0", zIndex: "1000", pointerEvents: "none",
  });
  document.body.appendChild(flyer);
  el.style.visibility = "hidden";
  const move = flyer.animate(
    [{ transform: "translate(0, 0)" }, { transform: `translate(${after.left - previewBefore.left}px, ${after.top - previewBefore.top}px)` }],
    { duration: 600, easing: "cubic-bezier(0.65, 0, 0.35, 1)" } // speeds up, then slows down
  );
  move.onfinish = move.oncancel = () => {
    el.style.visibility = "";
    flyer.remove();
  };
});
// How much of the surroundings the AI sees, as a share of the box on every
// side (0-1): what the last description used, else 25 %.
const DEFAULT_MARGIN = 0.25;
const margin = ref(props.object.beschrijving?.marge ?? DEFAULT_MARGIN);
// What the next question will use besides the defaults, in a few words
// (shown beside the button and on the folded AI modifiers).
const modifiersSummary = computed(() => {
  const parts = [];
  if (Math.round(margin.value * 100) !== Math.round(DEFAULT_MARGIN * 100)) parts.push(t("describe.history_margin", { pct: Math.round(margin.value * 100) }));
  if (hint.value.trim()) parts.push(t("describe.history_hint", { hint: hint.value.trim() }));
  return parts.join(" · ");
});
// The preview follows the slider a moment after it stops moving.
const shownMargin = ref(margin.value);
let marginTimer = null;
watch(margin, (value) => {
  clearTimeout(marginTimer);
  marginTimer = setTimeout(() => (shownMargin.value = value), 250);
});
const hits = ref([]);
const editor = ref(null);

// Move by the title bar, resize at the edges; double-click the title bar to
// centre it again. Codex renders the dialog elsewhere in the page (teleport).
const PLACEMENT_KEY = "cc-vergroter-plaats";
let undoMovable = null;

function enableMoving() {
  undoMovable?.();
  undoMovable = null;
  const dialog = document.querySelector(".cc-vergroter");
  const header = dialog?.querySelector(".cdx-dialog__header");
  if (!dialog || !header) return;
  undoMovable = makeMovable(dialog, {
    handle: header,
    storageKey: PLACEMENT_KEY,
    labels: { move: t("magnifier.move"), resize: t("magnifier.resize") },
    min: { width: 360, height: 240 },
  });
  header.ondblclick = (event) => {
    if (event.target.closest("button")) return;
    forgetPlacement(PLACEMENT_KEY);
    dialog.removeAttribute("style");
  };
}

watch(
  () => props.open,
  async (open) => {
    if (!open) {
      undoMovable?.();
      undoMovable = null;
      return;
    }
    await nextTick();
    enableMoving();
  },
  { immediate: true }
);
onBeforeUnmount(() => undoMovable?.());

const base = computed(() => objectPath(props.file.mid, props.n, props.object.id));
const name = computed(() => objectName(props.object, language, t));
const subtitle = computed(() => `${t(`source.${props.object.bron}`)} · ${t(`status.${props.object.status}`)}`);
const description = computed(() => props.object.beschrijving || null);
// Whether the user changed this AI text (NL or EN) by hand.
function aiEdited(field) {
  const original = description.value?.ai_origineel || {};
  return field in original || `${field}_en` in original;
}

// Kind and certainty come from a fixed Dutch list (the model's answer schema);
// shown in the interface language, or as given when not in the list.
function fixedValue(group, value) {
  const text = t(`${group}.${value}`);
  return text === `${group}.${value}` ? value : text;
}
// Why this model, in plain words. Descriptions stored before the reason had a
// code fall back to the current choice for the file (the same rules).
const modelReason = computed(() => {
  const d = description.value;
  const code = d ? d.model_reden_code || plan.value?.reden_code : plan.value?.reden_code;
  if (!code) return d?.model_reden || plan.value?.reden || "";
  const labels = (d?.model_reden_labels || plan.value?.labels || []).map((label) => t(`rights.${label}`)).join(", ");
  return t(`describe.reason_${code}`, { labels });
});
// "Contributor" links to Meta's explanation of that mode (cheaper; Meta may train on the input).
const reasonLinks = {
  contributor: { href: "https://dev.meta.ai/docs/pricing-rate-limits#contributor-mode", label: t("describe.contributor_link") },
};
// The cost on the buttons: an estimate in live mode, free with the dummy.
const costLabel = computed(() => (plan.value?.betaald ? `± ${money(plan.value.kosten_schatting_usd, language)}` : t("describe.free_short")));
// What the image description would see with the chosen margin (free; nothing goes to the model).
const modelInputUrl = computed(() => `${base.value}/beschrijving/invoer.jpg?marge=${shownMargin.value}`);
// The same, large (up to 3000 px), for the lightbox: to read and check the text in the image.
const largeInputUrl = computed(() => `${modelInputUrl.value}&max=3000`);
// The texts the AI read, beside the large image in the lightbox, to compare.
const readTexts = computed(() =>
  description.value
    ? [
        ...READ_TEXTS.map((key) => ({
          key,
          label: t(`describe.field_${key}`),
          text: description.value[key],
          ai: true,
          model: description.value.model,
          edited: key in (description.value.ai_origineel || {}),
        })),
      ]
    : []
);
// View on the Cut-out tab: the shape (PNG, transparent) or the rectangle (JPG).
// Only a view; what goes to Commons is the format in the Commons concept.
const views = [
  { value: "png", label: "PNG" },
  { value: "jpg", label: "JPG" },
];
const view = ref(props.object.masker ? "png" : "jpg");
// "loading" until the browser has the cut-out; again after switching between PNG and JPG.
const imageState = ref("loading");
const imageUrl = computed(() => (props.object.masker && view.value === "png" ? `${base.value}/uitsnede.png` : `${base.value}/uitsnede.jpg?w=1200`));
watch(imageUrl, () => {
  imageState.value = "loading";
});

watch(
  () => props.object.id,
  () => {
    caption.value = props.object.bijschrift?.tekst || "";
    view.value = props.object.masker ? "png" : "jpg";
    removedCaption.value = "";
    hint.value = "";
    margin.value = props.object.beschrijving?.marge ?? DEFAULT_MARGIN;
    shownMargin.value = margin.value;
    loadHistory();
    cancelEditing();
    undoTexts.value = null;
    hits.value = [];
    // Nothing of the previous object's search or errors stays in view.
    searched.value = "";
    ownTerm.value = "";
    lookupItems.value = [];
    error.value = "";
    loadPlan();
  }
);

async function loadPlan() {
  try {
    plan.value = await get(`${base.value}/beschrijving`);
  } catch (e) {
    error.value = errorText(t, e);
  }
}
loadPlan();

async function describe(again) {
  // Asking again always costs money; a first question may still come from the
  // cache (free), but the estimate is asked to confirm all the same.
  const paid = again || !description.value;
  if (paid && config.betaald && plan.value?.betaald && !(await askConfirm(t("describe.confirm", { amount: money(plan.value.kosten_schatting_usd, language) }), { title: t("confirm.cost_title") }))) return;
  busy.value = true;
  seconds.value = 0;
  ticker = setInterval(() => seconds.value++, 1000);
  error.value = "";
  try {
    const body = { opnieuw: again, marge: margin.value };
    if (hint.value.trim()) body.aanwijzing = hint.value.trim();
    const result = await post(`${base.value}/beschrijving`, body);
    emit("changed", result.object);
    hint.value = "";
    cancelEditing();
    undoTexts.value = null;
    editor.value?.reload();
    loadHistory();
  } catch (e) {
    error.value = errorText(t, e);
  } finally {
    busy.value = false;
    clearInterval(ticker);
  }
}

// Earlier descriptions (kept history plus answers still in the cache), newest first.
const history = ref([]);

async function loadHistory() {
  try {
    history.value = (await get(`${base.value}/beschrijving/geschiedenis`)).geschiedenis;
  } catch {
    history.value = [];
  }
}
loadHistory();

function historyMeta(entry) {
  const when = entry.tijdstempel ? new Date(entry.tijdstempel).toLocaleString(language, { dateStyle: "short", timeStyle: "short" }) : "";
  const parts = [when, entry.model];
  if (entry.aanwijzing) parts.push(t("describe.history_hint", { hint: entry.aanwijzing }));
  parts.push(t("describe.history_margin", { pct: Math.round((entry.marge ?? DEFAULT_MARGIN) * 100) }));
  if (entry.bewerkt) parts.push(t("describe.edited"));
  return parts.filter(Boolean).join(" · ");
}

// Make an earlier description current again; the current one goes into the history.
async function restoreDescription(entry) {
  error.value = "";
  try {
    const changed = await post(`${base.value}/beschrijving/terugzetten`, { tijdstempel: entry.tijdstempel, bewerkt: Boolean(entry.bewerkt) });
    emit("changed", changed);
    cancelEditing();
    undoTexts.value = null;
    margin.value = changed.beschrijving?.marge ?? DEFAULT_MARGIN;
    editor.value?.reload();
    loadHistory();
  } catch (e) {
    error.value = errorText(t, e);
  }
}

// Forget the description; the answer stays in the cache, so asking again is free.
async function removeDescription() {
  if (!(await askConfirm(t("describe.remove_confirm"), { go: t("describe.remove"), destructive: true }))) return;
  try {
    emit("changed", await del(`${base.value}/beschrijving`));
    cancelEditing();
    undoTexts.value = null;
    editor.value?.reload();
    loadPlan();
    loadHistory();
  } catch (e) {
    error.value = errorText(t, e);
  }
}

// Editing the AI texts by hand, one field (or NL/EN pair) at a time with its own
// pencil. The server keeps the original AI text, for "Terug naar de AI-tekst";
// "Ongedaan maken" puts back what was there before the last change.
const READ_TEXTS = ["tekst_in_beeld", "tekst_rond_beeld"];
const EDITABLE = ["onderwerp", "onderwerp_en", "bedrijf_of_naam", "beschrijving", "beschrijving_en", ...READ_TEXTS];
const TEXT_GROUPS = [
  { key: "onderwerp", label: "describe.subject", fields: ["onderwerp", "onderwerp_en"], ai: true, always: true },
  { key: "naam", label: "describe.name", fields: ["bedrijf_of_naam"] },
  { key: "beschrijving", label: "describe.description", fields: ["beschrijving", "beschrijving_en"], ai: true, always: true, long: true },
  { key: "tekst_in_beeld", label: "describe.field_tekst_in_beeld", fields: ["tekst_in_beeld"], read: true, long: true },
  { key: "tekst_rond_beeld", label: "describe.field_tekst_rond_beeld", fields: ["tekst_rond_beeld"], read: true, long: true },
];
const editingGroup = ref(null);
const fieldDraft = ref({});
const undoTexts = ref(null);

function currentTexts() {
  return Object.fromEntries(EDITABLE.map((field) => [field, description.value?.[field] || ""]));
}

const fieldChanged = computed(() => Object.entries(fieldDraft.value).some(([field, value]) => value.trim() !== (description.value?.[field] || "")));

const editBox = ref(null);
async function startEditing(group) {
  editingGroup.value = group.key;
  fieldDraft.value = Object.fromEntries(group.fields.map((field) => [field, description.value?.[field] || ""]));
  // As high as the text itself right away (autosize only reacts once you type).
  await nextTick();
  const box = Array.isArray(editBox.value) ? editBox.value[0] : editBox.value;
  box?.querySelectorAll("textarea").forEach((area) => {
    area.style.height = "auto";
    area.style.height = `${area.scrollHeight + 2}px`;
  });
  box?.querySelector("textarea, input")?.focus();
}

function cancelEditing() {
  editingGroup.value = null;
  fieldDraft.value = {};
}

function saveEditing() {
  if (fieldChanged.value) saveTexts({ ...fieldDraft.value });
}

async function saveTexts(texts, { undoable = true } = {}) {
  const before = currentTexts();
  try {
    emit("changed", await patch(`${base.value}/beschrijving`, texts));
    cancelEditing();
    undoTexts.value = undoable ? before : null;
    editor.value?.reload();
  } catch (e) {
    error.value = errorText(t, e);
  }
}

function backToAi() {
  saveTexts({ ...currentTexts(), ...description.value.ai_origineel });
}

function undoEdit() {
  saveTexts(undoTexts.value, { undoable: false });
}

// Empty the caption and remove it from the object at once (no Opslaan needed);
// what was there can be put back with "Ongedaan maken".
const removedCaption = ref("");

async function removeCaption() {
  const previous = (props.object.bijschrift?.tekst || caption.value).trim();
  caption.value = "";
  await saveCaption();
  removedCaption.value = previous;
}

async function undoRemoveCaption() {
  caption.value = removedCaption.value;
  removedCaption.value = "";
  await saveCaption();
}

async function saveCaption() {
  try {
    const text = caption.value.trim();
    const result = await patch(base.value, { bijschrift: text ? { tekst: text } : null });
    emit("changed", result);
  } catch (e) {
    error.value = errorText(t, e);
  }
}

const ownTerm = ref("");
const searched = ref("");
// Autosuggest: Wikidata items as you type, after 2 letters and a short pause.
const lookupItems = ref([]);
const lookupChoice = ref(null);
const lookupDone = ref(false); // "nothing found" only after an answer, not while waiting
let lookupTimer = null;
let lookupSeq = 0;
function onLookupInput(value) {
  clearTimeout(lookupTimer);
  const term = (value || "").trim();
  lookupDone.value = false;
  if (term.length < 2) {
    lookupItems.value = [];
    return;
  }
  lookupTimer = setTimeout(async () => {
    const seq = ++lookupSeq;
    try {
      const found = (await get(`${API}/wikidata/zoek${query({ q: term, taal: language })}`)).resultaten;
      if (seq !== lookupSeq) return; // an older answer after a newer question
      lookupItems.value = found.map((hit) => ({ value: hit.q, label: hit.label, description: [hit.q, hit.beschrijving].filter(Boolean).join(" · "), hit }));
    } catch {
      lookupItems.value = [];
    }
    if (seq === lookupSeq) lookupDone.value = true;
  }, 300);
}
async function onLookupSelect(q) {
  const item = lookupItems.value.find((entry) => entry.value === q);
  if (!item) return;
  await addDepicts(item.hit);
  lookupChoice.value = null;
}
async function searchWikidata(term) {
  term = (term || "").trim();
  if (!term) return;
  try {
    hits.value = (await get(`${API}/wikidata/zoek${query({ q: term, taal: language })}`)).resultaten;
    searched.value = term;
  } catch (e) {
    error.value = errorText(t, e);
  }
}

async function addDepicts(hit) {
  await editor.value?.addDepicts({ q: hit.q, label: hit.label });
  tab.value = "commons";
}

// Download saves the file (named after the Commons concept); view opens it in a new tab.
function download(kind) {
  window.location.href = `${base.value}/uitsnede.${kind}?download=1`;
}

function viewFull(kind) {
  window.open(`${base.value}/uitsnede.${kind}`, "_blank", "noopener");
}
</script>
