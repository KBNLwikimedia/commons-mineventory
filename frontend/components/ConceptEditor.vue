<!--
  The Commons concept of one cut-out (functional design 9.1-9.4): file name,
  format, caption and description in Dutch and English, date, maker,
  categories, depicts, the rights label, and the wikitext and SDC preview.
  Free: it only reads and writes the concept in this app.
-->
<template>
  <div v-if="concept" class="cc-concept">
    <cdx-message v-if="!concept.upload_toegestaan" type="warning" :inline="true">{{ t("concept.not_allowed") }}</cdx-message>
    <div class="cc-concept-kop">
      <figure class="cc-concept-voorbeeld">
        <img :src="previewUrl" :alt="t('concept.preview_image')" />
        <figcaption class="cc-klein">{{ draft.formaat.toUpperCase() }} · {{ t("concept.preview_image") }}</figcaption>
      </figure>
      <p class="cc-bestand-regel">
        <rights-label v-for="label in concept.rechten.labels" :key="label" :label="label" />
      </p>
    </div>

    <cdx-field>
      <template #label>{{ t("concept.filename") }}</template>
      <template #help-text>{{ t("concept.filename_help") }}</template>
      <cdx-text-input v-model="draft.bestandsnaam" />
    </cdx-field>
    <cdx-field>
      <template #label>{{ t("concept.format") }}</template>
      <cdx-select v-model:selected="draft.formaat" :menu-items="formats" />
    </cdx-field>
    <div class="cc-twee">
      <cdx-field>
        <template #label>{{ t("concept.caption") }} (nl)</template>
        <cdx-text-input v-model="draft.caption.nl" />
      </cdx-field>
      <cdx-field>
        <template #label>{{ t("concept.caption") }} (en)</template>
        <cdx-text-input v-model="draft.caption.en" />
      </cdx-field>
      <cdx-field>
        <template #label>{{ t("concept.description") }} (nl)</template>
        <cdx-text-area v-model="draft.beschrijving.nl" :autosize="true" />
      </cdx-field>
      <cdx-field>
        <template #label>{{ t("concept.description") }} (en)</template>
        <cdx-text-area v-model="draft.beschrijving.en" :autosize="true" />
      </cdx-field>
      <cdx-field>
        <template #label>{{ t("concept.date") }}</template>
        <cdx-text-input v-model="draft.datum" />
      </cdx-field>
      <cdx-field>
        <template #label>{{ t("concept.maker") }}</template>
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
          <small class="cc-qid">{{ item.q }}</small>
          <cdx-button size="small" weight="quiet" action="destructive" :aria-label="t('actions.remove')" @click="draft.beeldt_af.splice(i, 1)">×</cdx-button>
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
      <cdx-button action="progressive" weight="primary" :disabled="saving" @click="save">{{ t("actions.save_short") }}</cdx-button>
      <cdx-button :disabled="saving" @click="reset">{{ t("concept.reset") }}</cdx-button>
    </div>
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
import { computed, inject, ref, watch } from "vue";
import {
  CdxAccordion, CdxButton, CdxCheckbox, CdxField, CdxIcon, CdxLookup, CdxMessage, CdxSelect, CdxTextArea, CdxTextInput,
} from "@wikimedia/codex";
import { cdxIconCopy } from "@wikimedia/codex-icons";
import { API, errorText, get, objectPath, patch, query } from "../api.js";
import { askConfirm } from "../confirm.js";
import { useT } from "../i18n.js";
import RightsLabel from "./RightsLabel.vue";

const props = defineProps({ mid: { type: String, required: true }, n: { type: Number, required: true }, objectId: { type: String, required: true } });
const emit = defineEmits(["saved"]);
const t = useT();
const language = inject("language", "nl");
const concept = ref(null);
const draft = ref(null);
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
}

async function reload() {
  try {
    fill(await get(path.value));
  } catch (e) {
    message.value = errorText(t, e);
    messageType.value = "error";
  }
}
watch(path, reload, { immediate: true });

async function send(body) {
  saving.value = true;
  message.value = "";
  try {
    fill(await patch(path.value, body));
    message.value = t("concept.saved");
    messageType.value = "success";
    emit("saved", concept.value);
  } catch (e) {
    message.value = errorText(t, e);
    messageType.value = "error";
  } finally {
    saving.value = false;
  }
}

function save() {
  // The extension follows the format; the server makes them match.
  const body = { ...draft.value, merk_bevestigd: draft.value.merk_bevestigd.trim() || null };
  return send(body);
}

// Throws away the user's changes (texts, categories, chosen Wikidata items) and
// puts back the draft the app composes itself; so it asks first.
async function reset() {
  const ok = await askConfirm(t("concept.reset_confirm"), { title: t("concept.reset"), go: t("concept.reset_go"), destructive: true });
  if (ok) return send({ herstel: true });
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
