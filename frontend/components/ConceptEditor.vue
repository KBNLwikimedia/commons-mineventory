<!--
  The Commons concept of one cut-out (functional design 9.1-9.4): file name,
  format, caption and description in Dutch and English, date, maker,
  categories, depicts, the rights label, and the wikitext and SDC preview.
  Free: it only reads and writes the concept in this app.
-->
<template>
  <div v-if="concept" class="cc-concept">
    <cdx-message v-if="!concept.upload_toegestaan" type="warning" :inline="true">{{ t("concept.not_allowed") }}</cdx-message>
    <!-- Left: rights label, file name and format; right: the cut-out as it goes to Commons. -->
    <div class="cc-concept-kop">
      <div class="cc-concept-links">
        <p class="cc-bestand-regel">
          <rights-label v-for="label in concept.rechten.labels" :key="label" :label="label" />
        </p>
        <cdx-field>
          <template #label>{{ t("concept.filename") }}</template>
          <template #help-text>{{ t("concept.filename_help") }}</template>
          <cdx-text-input v-model="draft.bestandsnaam" />
        </cdx-field>
        <cdx-field :is-fieldset="true">
          <template #label>{{ t("concept.format") }}</template>
          <template #help-text>{{ t(`concept.format_${draft.formaat}`) }}</template>
          <cdx-toggle-button-group v-model="draft.formaat" :buttons="formats" />
        </cdx-field>
      </div>
      <cutout-preview :src="previewUrl" :caption="t('concept.preview_image')" />
    </div>
    <div class="cc-twee">
      <!-- Caption and description, NL and EN. Filling a field from the caption
           or the AI description sits in one small menu beside it; "Ongedaan
           maken" shows only right after such a fill. -->
      <cdx-field v-for="[field, lang] in TEXT_FIELDS" :key="`${field}.${lang}`">
        <template #label>{{ t(field === "caption" ? "concept.caption" : "concept.description") }} ({{ lang }})</template>
        <template v-if="canUndo(field, lang)" #help-text>
          <button type="button" class="cc-link" @click="undoFill(field, lang)">↶ {{ t("magnifier.undo") }}</button>
        </template>
        <div class="cc-veld-met-menu">
          <cdx-text-input v-if="field === 'caption'" v-model="draft.caption[lang]" />
          <cdx-text-area v-else v-model="draft.beschrijving[lang]" :autosize="true" />
          <cdx-menu-button
            v-if="fillOptions(field, lang).length"
            :selected="null"
            :menu-items="fillOptions(field, lang)"
            :aria-label="t('concept.fill_from')"
            :title="t('concept.fill_from')"
            @update:selected="(value) => fillField(field, lang, value)"
          >
            <cdx-icon :icon="cdxIconEllipsis" />
          </cdx-menu-button>
        </div>
      </cdx-field>
      <cdx-field>
        <template #label>{{ t("concept.date") }}</template>
        <template v-if="concept.herkomst?.datum" #help-text><source-note :source="concept.herkomst.datum" /></template>
        <cdx-text-input v-model="draft.datum" />
      </cdx-field>
      <cdx-field>
        <template #label>{{ t("concept.maker") }}</template>
        <template v-if="concept.herkomst?.maker" #help-text><source-note :source="concept.herkomst.maker" /></template>
        <cdx-text-input v-model="draft.maker" />
      </cdx-field>
    </div>

    <cdx-field :is-fieldset="true">
      <template #label>{{ t("concept.categories") }}</template>
      <cdx-checkbox v-for="(category, i) in draft.categorieen" :key="category.naam + i" v-model="category.gekozen">{{ category.naam }}</cdx-checkbox>
      <form class="cc-zoek" @submit.prevent="addCategory">
        <cdx-text-input v-model="newCategory" :placeholder="t('concept.category_add')" :aria-label="t('concept.category_add')" />
        <cdx-button action="progressive" type="submit" :disabled="!newCategory.trim()">+</cdx-button>
      </form>
    </cdx-field>

    <cdx-field :is-fieldset="true">
      <template #label>{{ t("concept.depicts") }}</template>
      <ul class="cc-beeldt-af">
        <li v-for="(item, i) in draft.beeldt_af" :key="item.q">
          <a :href="`https://www.wikidata.org/wiki/${item.q}`" target="_blank" rel="noopener">{{ item.label || item.q }}</a>
          <small class="cc-qid"><a :href="`https://www.wikidata.org/wiki/${item.q}`" target="_blank" rel="noopener">{{ item.q }}</a></small>
          <cdx-button size="small" weight="quiet" action="destructive" :aria-label="t('actions.remove')" @click="draft.beeldt_af.splice(i, 1)">×</cdx-button>
          <span v-if="itemDescription(item.q) !== null" class="cc-item-beschrijving" :class="{ leeg: !itemDescription(item.q) }">
            {{ itemDescription(item.q) || t("concept.no_item_description") }}
          </span>
        </li>
      </ul>
      <cdx-lookup
        v-model:selected="lookupSelected"
        v-model:input-value="lookupText"
        :menu-items="lookupItems"
        :placeholder="t('concept.depicts_add')"
        @input="lookup"
        @update:selected="pickLookup"
      />
    </cdx-field>

    <cdx-checkbox v-model="draft.image_extracted">{{ t("concept.image_extracted") }}</cdx-checkbox>
    <cdx-field v-if="concept.rechten.labels.includes('merk')">
      <template #label>{{ t("concept.trademark") }}</template>
      <template #help-text>{{ t("concept.trademark_help") }}</template>
      <cdx-text-input v-model="draft.merk_bevestigd" />
    </cdx-field>

    <div class="cc-knoppen">
      <cdx-button action="progressive" :disabled="saving" @click="reset">{{ t("concept.reset") }}</cdx-button>
    </div>
    <p class="cc-klein cc-opslagstatus" role="status">{{ saving ? t("concept.saving") : t("concept.autosave") }}</p>
    <cdx-message v-if="message" :type="messageType" :inline="true">{{ message }}</cdx-message>

    <cdx-accordion v-model="previewOpen">
      <template #title>{{ t("concept.preview") }}</template>
      <p class="cc-klein">{{ concept.samenvatting }}</p>
      <!-- Wikitext: as Commons renders it, or the source. -->
      <div class="cc-voorbeeld-kop">
        <h4>{{ t("concept.wikitext") }}</h4>
        <cdx-toggle-button-group v-model="wikitextView" :buttons="views" :aria-label="t('concept.view')" />
      </div>
      <template v-if="wikitextView === 'weergave'">
        <p class="cc-klein">{{ t("concept.rendered_note") }}</p>
        <p v-if="rendering && !renderedHtml" class="cc-klein">{{ t("concept.rendering") }}</p>
        <cdx-message v-if="renderError" type="error" :inline="true">{{ renderError }}</cdx-message>
        <!-- Made by Commons, cleaned by the server (cutter/weergave.py): safe tags only. -->
        <div v-if="renderedHtml" ref="renderedBox" class="cc-weergave-commons" :class="{ bezig: rendering }" v-html="renderedHtml"></div>
      </template>
      <template v-else>
        <pre class="cc-wikitekst">{{ concept.wikitekst }}</pre>
      </template>
      <cdx-button action="progressive" size="small" @click="copy(concept.wikitekst)"><cdx-icon :icon="cdxIconCopy" /> {{ t("concept.copy") }}</cdx-button>

      <!-- Structured data: as the Structured data tab on Commons shows it, or the JSON. -->
      <div class="cc-voorbeeld-kop">
        <h4>{{ t("concept.sdc") }}</h4>
        <cdx-toggle-button-group v-model="sdcView" :buttons="views" :aria-label="t('concept.view')" />
      </div>
      <template v-if="sdcView === 'weergave'">
        <p class="cc-klein">{{ t("concept.sdc_note") }}</p>
        <sdc-preview :sdc="concept.sdc" :labels="concept.sdc_labels || {}" />
      </template>
      <pre v-else class="cc-wikitekst">{{ JSON.stringify(concept.sdc, null, 2) }}</pre>

      <!-- The other way round: what the original would get, the cut-out as a region (phase 2). -->
      <div class="cc-voorbeeld-kop">
        <h4>{{ t("concept.original_regions") }}</h4>
        <cdx-toggle-button-group v-if="concept.origineel?.sdc.claims.length" v-model="originalView" :buttons="views" :aria-label="t('concept.view')" />
      </div>
      <p v-if="!concept.origineel" class="cc-klein">{{ t("concept.original_regions_na") }}</p>
      <p v-else-if="!concept.origineel.regios.length" class="cc-klein">{{ t("concept.original_regions_none") }}</p>
      <template v-else>
        <p class="cc-klein">{{ t("concept.original_regions_help") }}</p>
        <ul v-if="concept.origineel.regios.some((r) => r.aanwezig)" class="cc-klein">
          <li v-for="r in concept.origineel.regios.filter((x) => x.aanwezig)" :key="r.q">{{ t("concept.original_region_present", { item: concept.sdc_labels?.[r.q]?.[language] || r.q }) }}</li>
        </ul>
        <template v-if="concept.origineel.sdc.claims.length">
          <sdc-preview v-if="originalView === 'weergave'" :sdc="concept.origineel.sdc" :labels="concept.sdc_labels || {}" :captions-shown="false" />
          <pre v-else class="cc-wikitekst">{{ JSON.stringify(concept.origineel.sdc, null, 2) }}</pre>
        </template>
      </template>
    </cdx-accordion>
  </div>
  <p v-else class="cc-klein">{{ t("concept.loading") }}</p>
</template>

<script setup>
import { computed, inject, nextTick, onBeforeUnmount, reactive, ref, watch } from "vue";
import {
  CdxAccordion, CdxButton, CdxCheckbox, CdxField, CdxIcon, CdxLookup, CdxMenuButton, CdxMessage, CdxToggleButtonGroup, CdxTextArea, CdxTextInput,
} from "@wikimedia/codex";
import { cdxIconCopy, cdxIconEllipsis } from "@wikimedia/codex-icons";
import { API, errorText, get, objectPath, patch, query } from "../api.js";
import { makeCollapsible } from "../collapsible.js";
import { askConfirm } from "../confirm.js";
import { useT } from "../i18n.js";
import CutoutPreview from "./CutoutPreview.vue";
import RightsLabel from "./RightsLabel.vue";
import SdcPreview from "./SdcPreview.vue";
import SourceNote from "./SourceNote.vue";

const props = defineProps({ mid: { type: String, required: true }, n: { type: Number, required: true }, objectId: { type: String, required: true } });
const emit = defineEmits(["saved"]);
const t = useT();
const language = inject("language", "nl");
const concept = ref(null);
const draft = ref(null);
// Every action that fills a field remembers what was there, so "Ongedaan
// maken" can put it back (also when the AI description is gone).
const undoValues = reactive({});
const saving = ref(false);
const message = ref("");
const messageType = ref("success");
const newCategory = ref("");
const lookupText = ref("");
const lookupSelected = ref(null);
const lookupItems = ref([]);
// Preview or source, for the wikitext and the structured data.
const views = [
  { value: "weergave", label: t("concept.view_rendered") },
  { value: "broncode", label: t("concept.view_source") },
];
// Only rendered while the preview is open: no request to Commons otherwise.
const previewOpen = ref(false);
const wikitextView = ref("weergave");
const sdcView = ref("weergave");
const originalView = ref("weergave");
const renderedHtml = ref("");
const renderedBox = ref(null);
// Boxes that start closed on Commons (institution, creator) start closed here too.
watch(renderedHtml, async () => {
  await nextTick();
  if (renderedBox.value) makeCollapsible(renderedBox.value, { open: t("concept.box_open"), close: t("concept.box_close") });
});
const rendering = ref(false);
const renderError = ref("");
let renderTimer = null;
let renderedText = null;

// Commons renders the wikitext (a read, cached on the server); again after a
// change, a moment after the concept has been saved.
async function render() {
  const text = concept.value?.wikitekst;
  if (!previewOpen.value || wikitextView.value !== "weergave" || !text || text === renderedText) return;
  rendering.value = true;
  renderError.value = "";
  try {
    const data = await get(`${path.value}/weergave`);
    if (concept.value?.wikitekst === text) {
      renderedHtml.value = data.html;
      renderedText = text;
    }
  } catch (e) {
    renderError.value = errorText(t, e);
  } finally {
    rendering.value = false;
  }
}

watch([() => concept.value?.wikitekst, wikitextView, previewOpen], () => {
  clearTimeout(renderTimer);
  renderTimer = setTimeout(render, renderedText === null ? 0 : 800);
});

const formats = [
  { value: "jpg", label: "JPG" },
  { value: "png", label: "PNG" },
];
const path = computed(() => `${objectPath(props.mid, props.n, props.objectId)}/commons`);
// The cut-out as it would be uploaded: JPG (the rectangle, a light preview) or
// PNG (the shape of the object, transparent outside it).
const previewUrl = computed(() => {
  const base = objectPath(props.mid, props.n, props.objectId);
  return draft.value?.formaat === "png" ? `${base}/uitsnede.png` : `${base}/uitsnede.jpg?w=480`;
});

// Every change is saved by itself, shortly after the last keystroke or click,
// and right away when the magnifier closes; so nothing gets lost.
const AUTOSAVE_MS = 600;
let lastSaved = "";
let saveTimer = null;
const bodyOf = (d) => ({ ...d, merk_bevestigd: (d.merk_bevestigd || "").trim() || null });

function fill(data) {
  concept.value = data;
  draft.value = JSON.parse(JSON.stringify({
    bestandsnaam: data.bestandsnaam,
    formaat: data.formaat,
    caption: { nl: data.caption.nl || "", en: data.caption.en || "" },
    beschrijving: { nl: data.beschrijving.nl || "", en: data.beschrijving.en || "" },
    datum: data.datum,
    maker: data.maker,
    categorieen: data.categorieen,
    beeldt_af: data.beeldt_af,
    image_extracted: data.image_extracted,
    merk_bevestigd: data.merk_bevestigd || "",
  }));
  lastSaved = JSON.stringify(bodyOf(draft.value));
}

watch(
  draft,
  () => {
    if (!draft.value || JSON.stringify(bodyOf(draft.value)) === lastSaved) return;
    clearTimeout(saveTimer);
    saveTimer = setTimeout(save, AUTOSAVE_MS);
  },
  { deep: true }
);

onBeforeUnmount(() => {
  if (saveTimer && draft.value && JSON.stringify(bodyOf(draft.value)) !== lastSaved) save();
  clearTimeout(saveTimer);
  clearTimeout(renderTimer);
});

async function reload() {
  try {
    fill(await get(path.value));
  } catch (e) {
    message.value = errorText(t, e);
    messageType.value = "error";
  }
}
watch(path, () => {
  Object.keys(undoValues).forEach((key) => delete undoValues[key]);
  renderedHtml.value = "";
  renderedText = null;
  reload();
}, { immediate: true });

async function send(body, { announce = false } = {}) {
  saving.value = true;
  message.value = "";
  const sent = JSON.stringify(body);
  try {
    const data = await patch(path.value, body);
    // Typed on while saving? Keep what is in the form; the next save follows.
    if (body.herstel || JSON.stringify(bodyOf(draft.value)) === sent) fill(data);
    else {
      concept.value = data;
      lastSaved = sent;
    }
    if (announce) {
      message.value = t("concept.saved");
      messageType.value = "success";
    }
    emit("saved", concept.value);
  } catch (e) {
    message.value = errorText(t, e);
    messageType.value = "error";
  } finally {
    saving.value = false;
  }
}

function save() {
  clearTimeout(saveTimer);
  saveTimer = null;
  // The extension follows the format; the server makes them match.
  return send(bodyOf(draft.value));
}

// Throws away the user's changes (texts, categories, chosen Wikidata items) and
// puts back the draft the app composes itself; so it asks first.
async function reset() {
  const ok = await askConfirm(t("concept.reset_confirm"), { title: t("concept.reset"), go: t("concept.reset_go"), destructive: true });
  if (ok) {
    Object.keys(undoValues).forEach((key) => delete undoValues[key]);
    clearTimeout(saveTimer);
    return send({ herstel: true }, { announce: true });
  }
}

// Back to what "Wat staat hierop?" (the AI image description) said, per field.
function differsFromAi(field, language) {
  const ai = concept.value?.ai?.[field]?.[language];
  return Boolean(ai) && draft.value[field][language].trim() !== ai.trim();
}

// (undoValues, declared at the top, keeps what a field held before an action.)

function setValue(field, language, value) {
  undoValues[`${field}.${language}`] = { before: draft.value[field][language], after: value };
  draft.value[field][language] = value;
}

function backToAi(field, language) {
  setValue(field, language, concept.value.ai[field][language].slice(0, field === "caption" ? 250 : undefined));
}

// The caption (from the Cut-out tab) as an extra sentence under the description.
function addCaptionToDescription() {
  const current = draft.value.beschrijving.nl.trim();
  setValue("beschrijving", "nl", current ? `${current}
${concept.value.bijschrift}` : concept.value.bijschrift);
}

/* The links under a caption or description field: undo the last action,
   take over the caption, go back to the AI image description. */
const TEXT_FIELDS = [["caption", "nl"], ["caption", "en"], ["beschrijving", "nl"], ["beschrijving", "en"]];

// What the menu beside a field can fill it with; only what would change it.
function fillOptions(field, language) {
  const options = [];
  const current = draft.value[field][language];
  const caption = concept.value?.bijschrift;
  if (caption && language === "nl" && field === "caption" && current !== caption) {
    options.push({ value: "caption", label: t("concept.use_caption") });
  }
  if (caption && language === "nl" && field === "beschrijving" && !current.includes(caption)) {
    options.push({ value: "caption", label: t("concept.use_caption_description") });
  }
  if (differsFromAi(field, language)) options.push({ value: "ai", label: t("concept.back_to_ai") });
  return options;
}

function fillField(field, language, value) {
  if (value === "ai") backToAi(field, language);
  else if (field === "caption") setValue("caption", "nl", concept.value.bijschrift.slice(0, 250));
  else addCaptionToDescription();
}

// Undo only while the field still holds what the fill put there; typing
// afterwards has the browser's own undo.
function canUndo(field, language) {
  const saved = undoValues[`${field}.${language}`];
  return Boolean(saved) && draft.value[field][language] === saved.after;
}

function undoFill(field, language) {
  const key = `${field}.${language}`;
  draft.value[field][language] = undoValues[key].before;
  delete undoValues[key];
}

// The short Wikidata description of a depicts item: in the interface language,
// else the other one; "" when Wikidata has neither, null when not (yet) known.
function itemDescription(q) {
  const info = concept.value?.beeldt_af_info?.[q];
  if (!info) return null;
  const other = language === "nl" ? "en" : "nl";
  return info.beschrijving?.[language] || info.beschrijving?.[other] || "";
}

function addCategory() {
  const name = newCategory.value.trim().replace(/^Category:/i, "");
  if (name) draft.value.categorieen.push({ naam: name, gekozen: true });
  newCategory.value = "";
}

let timer = null;
function lookup(text) {
  clearTimeout(timer);
  if (!text || text.length < 2) {
    lookupItems.value = [];
    return;
  }
  timer = setTimeout(async () => {
    try {
      const data = await get(`${API}/wikidata/zoek${query({ q: text, taal: language })}`);
      lookupItems.value = data.resultaten.map((hit) => ({ value: hit.q, label: hit.label, description: `${hit.q} · ${hit.beschrijving || ""}` }));
    } catch {
      lookupItems.value = [];
    }
  }, 300);
}

function pickLookup(q) {
  const hit = lookupItems.value.find((item) => item.value === q);
  if (hit) addDepicts({ q, label: hit.label }, false);
  lookupSelected.value = null;
  lookupText.value = "";
}

async function addDepicts(item, persist = true) {
  if (!draft.value) await reload();
  if (!draft.value.beeldt_af.some((d) => d.q === item.q)) draft.value.beeldt_af.push(item);
  if (persist) await save();
}

async function copy(text) {
  try {
    await navigator.clipboard.writeText(text);
    message.value = t("concept.copied");
    messageType.value = "success";
  } catch {
    message.value = t("concept.copy_failed");
    messageType.value = "warning";
  }
}

defineExpose({ reload, addDepicts });
</script>
