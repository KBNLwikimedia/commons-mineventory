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
      <cdx-field>
        <template #label>{{ t("concept.caption") }} (nl)</template>
        <template v-if="fieldActions('caption', 'nl').length" #help-text>
          <span class="cc-veldlinks">
            <button v-for="action in fieldActions('caption', 'nl')" :key="action.key" type="button" class="cc-link" @click="action.run">{{ action.label }}</button>
          </span>
        </template>
        <cdx-text-input v-model="draft.caption.nl" />
      </cdx-field>
      <cdx-field>
        <template #label>{{ t("concept.caption") }} (en)</template>
        <template v-if="fieldActions('caption', 'en').length" #help-text>
          <span class="cc-veldlinks">
            <button v-for="action in fieldActions('caption', 'en')" :key="action.key" type="button" class="cc-link" @click="action.run">{{ action.label }}</button>
          </span>
        </template>
        <cdx-text-input v-model="draft.caption.en" />
      </cdx-field>
      <cdx-field>
        <template #label>{{ t("concept.description") }} (nl)</template>
        <template v-if="fieldActions('beschrijving', 'nl').length" #help-text>
          <span class="cc-veldlinks">
            <button v-for="action in fieldActions('beschrijving', 'nl')" :key="action.key" type="button" class="cc-link" @click="action.run">{{ action.label }}</button>
          </span>
        </template>
        <cdx-text-area v-model="draft.beschrijving.nl" :autosize="true" />
      </cdx-field>
      <cdx-field>
        <template #label>{{ t("concept.description") }} (en)</template>
        <template v-if="fieldActions('beschrijving', 'en').length" #help-text>
          <span class="cc-veldlinks">
            <button v-for="action in fieldActions('beschrijving', 'en')" :key="action.key" type="button" class="cc-link" @click="action.run">{{ action.label }}</button>
          </span>
        </template>
        <cdx-text-area v-model="draft.beschrijving.en" :autosize="true" />
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
        <cdx-button type="submit" :disabled="!newCategory.trim()">+</cdx-button>
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
      <cdx-button :disabled="saving" @click="reset">{{ t("concept.reset") }}</cdx-button>
    </div>
    <p class="cc-klein cc-opslagstatus" role="status">{{ saving ? t("concept.saving") : t("concept.autosave") }}</p>
    <cdx-message v-if="message" :type="messageType" :inline="true">{{ message }}</cdx-message>

    <cdx-accordion>
      <template #title>{{ t("concept.preview") }}</template>
      <p class="cc-klein">{{ concept.samenvatting }}</p>
      <pre class="cc-wikitekst">{{ concept.wikitekst }}</pre>
      <cdx-button size="small" @click="copy(concept.wikitekst)"><cdx-icon :icon="cdxIconCopy" /> {{ t("concept.copy") }}</cdx-button>
      <h4>{{ t("concept.sdc") }}</h4>
      <pre class="cc-wikitekst">{{ JSON.stringify(concept.sdc, null, 2) }}</pre>
    </cdx-accordion>
  </div>
  <p v-else class="cc-klein">{{ t("concept.loading") }}</p>
</template>

<script setup>
import { computed, inject, onBeforeUnmount, reactive, ref, watch } from "vue";
import {
  CdxAccordion, CdxButton, CdxCheckbox, CdxField, CdxIcon, CdxLookup, CdxMessage, CdxToggleButtonGroup, CdxTextArea, CdxTextInput,
} from "@wikimedia/codex";
import { cdxIconCopy } from "@wikimedia/codex-icons";
import { API, errorText, get, objectPath, patch, query } from "../api.js";
import { askConfirm } from "../confirm.js";
import { useT } from "../i18n.js";
import CutoutPreview from "./CutoutPreview.vue";
import RightsLabel from "./RightsLabel.vue";
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
  undoValues[`${field}.${language}`] = draft.value[field][language];
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
function fieldActions(field, language) {
  const actions = [];
  const key = `${field}.${language}`;
  const current = draft.value[field][language];
  if (key in undoValues && undoValues[key] !== current) {
    actions.push({
      key: "undo",
      label: `↶ ${t("magnifier.undo")}`,
      run: () => {
        draft.value[field][language] = undoValues[key];
        delete undoValues[key];
      },
    });
  }
  const caption = concept.value?.bijschrift;
  if (caption && language === "nl" && field === "caption" && current !== caption) {
    actions.push({ key: "caption", label: t("concept.use_caption"), run: () => setValue("caption", "nl", caption.slice(0, 250)) });
  }
  if (caption && language === "nl" && field === "beschrijving" && !current.includes(caption)) {
    actions.push({ key: "caption", label: t("concept.use_caption_description"), run: addCaptionToDescription });
  }
  if (differsFromAi(field, language)) {
    actions.push({ key: "ai", label: `↶ ${t("concept.back_to_ai")}`, run: () => backToAi(field, language) });
  }
  return actions;
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
