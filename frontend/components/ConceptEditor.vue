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
        <!-- File name and, right beside it, the format (it sets the extension). -->
        <div class="cc-naam-formaat">
          <cdx-field class="cc-naam-veld">
            <template #label>{{ t("concept.filename") }}</template>
            <template #help-text>{{ t("concept.filename_help") }} {{ t(`concept.format_${draft.formaat}`) }}</template>
            <cdx-text-input v-model="draft.bestandsnaam" />
          </cdx-field>
          <cdx-field :is-fieldset="true" class="cc-formaat-veld">
            <template #label>{{ t("concept.format") }}</template>
            <cdx-toggle-button-group v-model="draft.formaat" :buttons="formats" />
          </cdx-field>
        </div>
      </div>
      <cutout-preview :src="previewUrl" :caption="t('concept.preview_image')" />
    </div>
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

    <!-- The file page as on Commons: two tabs, "File information" and "Structured data", with
         Edit / [edit] links in the same places; a pencil on every row too. -->
    <section class="cc-commons-pagina">
      <h3 class="cc-blok-kop">{{ t("concept.preview") }}</h3>
      <p class="cc-klein">{{ concept.samenvatting }}</p>
      <cdx-tabs v-model:active="pageTab" class="cc-commons-tabs">
        <cdx-tab name="info" :label="t('concept.tab_info')">
          <!-- Captions: on Commons above the summary, with Edit at the right. -->
          <div class="cc-commons-kader">
            <div class="cc-commons-kader-kop">
              <strong>{{ t("sdc.captions") }}</strong>
              <button type="button" class="cc-link" @click="openEdit('caption')">{{ t("concept.edit_link") }}</button>
            </div>
            <table class="cc-captions">
              <tr v-for="lang in ['en', 'nl']" :key="lang">
                <th>{{ t(`concept.language_${lang}`) }}</th>
                <td :class="{ leeg: !draft.caption[lang] }">{{ draft.caption[lang] || t("concept.caption_empty") }}</td>
              </tr>
            </table>
          </div>
          <div class="cc-voorbeeld-kop">
            <span class="cc-klein">{{ wikitextView === "weergave" ? t("concept.rendered_note_edit") : t("concept.source_note") }}</span>
            <cdx-toggle-button-group v-model="wikitextView" :buttons="views" :aria-label="t('concept.view')" />
          </div>
          <template v-if="wikitextView === 'weergave'">
            <p v-if="rendering && !renderedHtml" class="cc-klein">{{ t("concept.rendering") }}</p>
            <cdx-message v-if="renderError" type="error" :inline="true">{{ renderError }}</cdx-message>
            <!-- Made by Commons, cleaned by the server (cutter/weergave.py): safe tags only. -->
            <div v-if="renderedHtml" ref="renderedBox" class="cc-weergave-commons" :class="{ bezig: rendering }" @click="onRenderedClick" v-html="renderedHtml"></div>
          </template>
          <pre v-else class="cc-wikitekst">{{ concept.wikitekst }}</pre>
          <!-- Categories, as at the bottom of a Commons page: remove with ×, add below. -->
          <div class="cc-categorie-balk">
            <strong>{{ t("concept.categories") }}:</strong>
            <template v-for="(category, i) in draft.categorieen" :key="category.naam + i">
              <span v-if="category.gekozen" class="cc-categorie">
                <a :href="`https://commons.wikimedia.org/wiki/Category:${encodeURIComponent(category.naam.replace(/ /g, '_'))}`" target="_blank" rel="noopener">{{ category.naam }}</a>
                <button type="button" class="cc-categorie-weg" :aria-label="`${t('actions.remove')}: ${category.naam}`" :title="t('actions.remove')" @click="category.gekozen = false">×</button>
              </span>
            </template>
            <form class="cc-categorie-erbij" @submit.prevent="addCategory">
              <cdx-text-input v-model="newCategory" :placeholder="t('concept.category_add')" :aria-label="t('concept.category_add')" />
              <cdx-button action="progressive" type="submit" :disabled="!newCategory.trim()">+</cdx-button>
            </form>
            <span v-if="draft.categorieen.some((c) => !c.gekozen)" class="cc-klein cc-categorie-uit">
              {{ t("concept.categories_removed") }}
              <template v-for="(category, i) in draft.categorieen.filter((c) => !c.gekozen)" :key="'uit' + i">
                <button type="button" class="cc-link" :title="t('concept.category_back')" @click="category.gekozen = true">↶ {{ category.naam }}</button>{{ " " }}
              </template>
            </span>
          </div>
          <cdx-button action="progressive" size="small" @click="copy(concept.wikitekst)"><cdx-icon :icon="cdxIconCopy" /> {{ t("concept.copy") }}</cdx-button>
        </cdx-tab>

        <cdx-tab name="sdc" :label="t('concept.tab_sdc')">
          <!-- The app has a simple editor; fine-tuning the structured data happens on Commons itself. -->
          <cdx-message type="notice" :inline="true" class="cc-sdc-melding">{{ t("concept.sdc_simple") }}</cdx-message>
          <div class="cc-voorbeeld-kop">
            <span class="cc-klein">{{ sdcView === "weergave" ? t("concept.sdc_note_edit") : t("concept.source_note") }}</span>
            <cdx-toggle-button-group v-model="sdcView" :buttons="views" :aria-label="t('concept.view')" />
          </div>
          <!-- As the Structured data tab: the statements (the captions are on the first tab). -->
          <sdc-preview
            v-if="sdcView === 'weergave'"
            :sdc="concept.sdc"
            :labels="concept.sdc_labels || {}"
            :captions-shown="false"
            :editable="true"
            :overrides="draft.sdc_waarden"
            @remove-depicts="removeDepicts"
            @save-statement="saveStatement"
          >
            <template #depicts-add>
              <cdx-lookup
                v-model:selected="lookupSelected"
                v-model:input-value="lookupText"
                :menu-items="lookupItems"
                :placeholder="t('concept.depicts_search')"
                :start-icon="cdxIconSearch"
                class="cc-sdc-erbij"
                @input="lookup"
                @update:selected="pickLookup"
              />
            </template>
          </sdc-preview>
          <pre v-else class="cc-wikitekst">{{ JSON.stringify(concept.sdc, null, 2) }}</pre>
        </cdx-tab>
      </cdx-tabs>

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
    </section>

    <!-- Editing one row of the Commons page: Opslaan or Annuleren. -->
    <cdx-dialog
      v-model:open="editOpen"
      class="cc-veld-dialoog"
      :title="editTitle"
      :use-close-button="true"
      :close-button-label="t('actions.close')"
      :primary-action="{ label: t('actions.save_short'), actionType: 'progressive' }"
      :default-action="{ label: t('actions.cancel') }"
      @primary="saveEdit"
      @default="editOpen = false"
    >
      <template v-for="field in editFields" :key="field">
        <template v-if="field === 'caption' || field === 'beschrijving'">
          <cdx-field v-for="lang in ['nl', 'en']" :key="`${field}.${lang}`">
            <template #label>{{ t(field === "caption" ? "concept.caption" : "concept.description") }} ({{ lang }})</template>
            <template v-if="canUndo(field, lang, editDraft)" #help-text>
              <button type="button" class="cc-link" @click="undoFill(field, lang, editDraft)">↶ {{ t("magnifier.undo") }}</button>
            </template>
            <div class="cc-veld-met-menu">
              <cdx-text-input v-if="field === 'caption'" v-model="editDraft[field][lang]" />
              <cdx-text-area v-else v-model="editDraft[field][lang]" :autosize="true" />
              <cdx-menu-button
                v-if="fillOptions(field, lang, editDraft).length"
                :selected="null"
                :menu-items="fillOptions(field, lang, editDraft)"
                :aria-label="t('concept.fill_from')"
                :title="t('concept.fill_from')"
                @update:selected="(value) => fillField(field, lang, value, editDraft)"
              >
                <cdx-icon :icon="cdxIconEllipsis" />
              </cdx-menu-button>
            </div>
          </cdx-field>
        </template>
        <cdx-field v-else>
          <template #label>{{ t(field === "datum" ? "concept.date" : "concept.maker") }}</template>
          <template v-if="concept.herkomst?.[field]" #help-text><source-note :source="concept.herkomst[field]" /></template>
          <cdx-text-input v-model="editDraft[field]" />
        </cdx-field>
      </template>
      <p v-if="editField === 'samenvatting'" class="cc-klein">
        {{ t("concept.summary_edit_note") }}
        <button type="button" class="cc-link" @click="editOpen = false; emit('edit-texts')">{{ t("concept.edit_teksten") }}</button>
      </p>
    </cdx-dialog>
  </div>
  <p v-else class="cc-klein">{{ t("concept.loading") }}</p>
</template>

<script setup>
import { computed, inject, nextTick, onBeforeUnmount, reactive, ref, watch } from "vue";
import {
  CdxButton, CdxCheckbox, CdxDialog, CdxField, CdxIcon, CdxLookup, CdxMenuButton, CdxMessage, CdxTab, CdxTabs, CdxToggleButtonGroup, CdxTextArea, CdxTextInput,
} from "@wikimedia/codex";
import { cdxIconCopy, cdxIconEllipsis, cdxIconSearch } from "@wikimedia/codex-icons";
import { API, errorText, get, objectPath, patch, query } from "../api.js";
import { makeCollapsible } from "../collapsible.js";
import { askConfirm } from "../confirm.js";
import { useT } from "../i18n.js";
import CutoutPreview from "./CutoutPreview.vue";
import RightsLabel from "./RightsLabel.vue";
import SdcPreview from "./SdcPreview.vue";
import SourceNote from "./SourceNote.vue";

const props = defineProps({ mid: { type: String, required: true }, n: { type: Number, required: true }, objectId: { type: String, required: true } });
const emit = defineEmits(["saved", "edit-texts"]);
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
// The Commons page is always shown now (it is where you edit): rendered by Commons, a read.
const previewOpen = ref(true);
const wikitextView = ref("weergave");
const sdcView = ref("weergave");
const originalView = ref("weergave");
const renderedHtml = ref("");
const renderedBox = ref(null);
// Boxes that start closed on Commons (institution, creator) start closed here too;
// and every row that comes from the concept gets a pencil.
watch(renderedHtml, async () => {
  await nextTick();
  if (!renderedBox.value) return;
  makeCollapsible(renderedBox.value, { open: t("concept.box_open"), close: t("concept.box_close") });
  addPencils(renderedBox.value);
});

// Rows of the information templates (their ids, kept by cutter/weergave.py) and what edits them.
const ROW_FIELDS = {
  fileinfotpl_desc: "beschrijving",
  fileinfotpl_art_title: "caption",
  fileinfotpl_date: "datum",
  fileinfotpl_publication_date: "datum",
  fileinfotpl_aut: "maker",
  fileinfotpl_art_inscriptions: "teksten",
};
const INSCRIPTION_LABELS = ["inscriptions", "inscripties", "inscription", "inscriptie"];
const PENCIL =
  '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 20 20" aria-hidden="true"><path fill="currentColor" d="m16.77 8 1.94-2a1 1 0 000-1.41l-3.34-3.3a1 1 0 00-1.41 0L12 3.23zM1 14.25V19h4.75l9.96-9.96-4.75-4.75z"/></svg>';

function pencilFor(field) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "cc-weergave-potlood";
  button.dataset.veld = field;
  const label = t(`concept.edit_${field}`);
  button.setAttribute("aria-label", label);
  button.title = label;
  button.innerHTML = PENCIL;
  return button;
}

// After the section headings, as on Commons: [edit] at Summary; at Licensing a note
// instead (the licence is taken over from the original and is not changed here).
function addSectionLinks(box) {
  const headings = box.querySelectorAll("h2");
  const summary = headings[0];
  const licence = headings[1];
  if (summary && !summary.parentElement.querySelector(".cc-sectie-edit")) {
    const link = document.createElement("button");
    link.type = "button";
    link.className = "cc-sectie-edit cc-weergave-potlood-tekst";
    link.dataset.veld = "samenvatting";
    link.textContent = `[ ${t("concept.edit_section")} ]`;
    summary.after(link);
  }
  if (licence && !licence.parentElement.querySelector(".cc-sectie-edit")) {
    const note = document.createElement("span");
    note.className = "cc-sectie-edit cc-sectie-vast";
    note.textContent = `[ ${t("concept.licence_fixed")} ]`;
    note.title = t("concept.licence_fixed_help");
    licence.after(note);
  }
}

function addPencils(box) {
  addSectionLinks(box);
  const book = /\{\{\s*book\b/i.test(concept.value?.wikitekst || "");
  for (const [id, field] of Object.entries(ROW_FIELDS)) {
    if (book && field === "caption") continue; // {{Book}}: the title is the book's
    const cell = box.querySelector(`#${id}`);
    if (cell && !cell.querySelector(".cc-weergave-potlood")) cell.append(" ", pencilFor(field));
  }
  // {{Information}} and {{Book}}: the inscriptions are an extra row without an id.
  box.querySelectorAll("td, th").forEach((cell) => {
    // The visible label only ({{Information field}} adds a hidden "InfoField").
    const text = (cell.firstChild?.nodeType === 3 ? cell.firstChild.textContent : cell.textContent).trim().toLowerCase();
    if (INSCRIPTION_LABELS.includes(text) && !cell.querySelector(".cc-weergave-potlood")) cell.append(" ", pencilFor("teksten"));
  });
}

function onRenderedClick(event) {
  const button = event.target.closest(".cc-weergave-potlood, .cc-weergave-potlood-tekst");
  if (!button) return;
  event.preventDefault();
  if (button.dataset.veld === "teksten") emit("edit-texts");
  else openEdit(button.dataset.veld);
}

// The small window for one row: a copy of those fields, back into the draft on Opslaan.
const editOpen = ref(false);
const editField = ref("");
const editDraft = ref(null);
const editTitle = computed(() => (editField.value ? t(`concept.edit_${editField.value}`) : ""));
// What each edit link or pencil opens; Summary [edit] opens all its fields at once.
const EDIT_GROUPS = { caption: ["caption"], beschrijving: ["beschrijving"], datum: ["datum"], maker: ["maker"], samenvatting: ["beschrijving", "datum", "maker"] };
const editFields = computed(() => EDIT_GROUPS[editField.value] || []);
function openEdit(group) {
  editField.value = group;
  editDraft.value = JSON.parse(JSON.stringify(Object.fromEntries(EDIT_GROUPS[group].map((field) => [field, draft.value[field]]))));
  editOpen.value = true;
}
function saveEdit() {
  for (const field of editFields.value) draft.value[field] = JSON.parse(JSON.stringify(editDraft.value[field]));
  editOpen.value = false;
  save();
}
// "File information" or "Structured data", as the two tabs of a file page on Commons.
const pageTab = ref("info");

// New values for one statement taken over from the original (an empty list removes it).
function saveStatement({ property, values }) {
  draft.value.sdc_waarden = { ...draft.value.sdc_waarden, [property]: values };
  save();
}

function removeDepicts(q) {
  draft.value.beeldt_af = draft.value.beeldt_af.filter((item) => item.q !== q);
}
const rendering = ref(false);
const renderError = ref("");
let renderTimer = null;
let renderedText = null;

// Commons renders the wikitext (a read, cached on the server); again after a
// change, a moment after the concept has been saved.
async function render() {
  const text = concept.value?.wikitekst;
  if (!previewOpen.value || pageTab.value !== "info" || wikitextView.value !== "weergave" || !text || text === renderedText) return;
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

watch([() => concept.value?.wikitekst, wikitextView, previewOpen, () => pageTab.value], () => {
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
    sdc_waarden: data.sdc_waarden || {},
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
function differsFromAi(field, language, target = draft.value) {
  const ai = concept.value?.ai?.[field]?.[language];
  return Boolean(ai) && target[field][language].trim() !== ai.trim();
}

// (undoValues, declared at the top, keeps what a field held before an action.)

function setValue(field, language, value, target = draft.value) {
  undoValues[`${field}.${language}`] = { before: target[field][language], after: value };
  target[field][language] = value;
}

function backToAi(field, language, target = draft.value) {
  setValue(field, language, concept.value.ai[field][language].slice(0, field === "caption" ? 250 : undefined), target);
}

// The caption (from the Cut-out tab) as an extra sentence under the description.
function addCaptionToDescription(target = draft.value) {
  const current = target.beschrijving.nl.trim();
  setValue("beschrijving", "nl", current ? `${current}
${concept.value.bijschrift}` : concept.value.bijschrift, target);
}


// What the menu beside a field can fill it with; only what would change it.
function fillOptions(field, language, target = draft.value) {
  const options = [];
  const current = target[field][language];
  const caption = concept.value?.bijschrift;
  if (caption && language === "nl" && field === "caption" && current !== caption) {
    options.push({ value: "caption", label: t("concept.use_caption") });
  }
  if (caption && language === "nl" && field === "beschrijving" && !current.includes(caption)) {
    options.push({ value: "caption", label: t("concept.use_caption_description") });
  }
  if (differsFromAi(field, language, target)) options.push({ value: "ai", label: t("concept.back_to_ai") });
  return options;
}

function fillField(field, language, value, target = draft.value) {
  if (value === "ai") backToAi(field, language, target);
  else if (field === "caption") setValue("caption", "nl", concept.value.bijschrift.slice(0, 250), target);
  else addCaptionToDescription(target);
}

// Undo only while the field still holds what the fill put there; typing
// afterwards has the browser's own undo.
function canUndo(field, language, target = draft.value) {
  const saved = undoValues[`${field}.${language}`];
  return Boolean(saved) && target[field][language] === saved.after;
}

function undoFill(field, language, target = draft.value) {
  const key = `${field}.${language}`;
  target[field][language] = undoValues[key].before;
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

defineExpose({ reload, addDepicts, openEdit });
</script>
