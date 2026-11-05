<!--
  /commons?mid=… (functional design 9.1): the upload menu of one file. All
  saved cut-outs with thumbnail, concept, rights label and a checkbox; the
  check before upload (read-only on Commons) and the preview. Uploading itself
  is phase 2: the button stays off while COMMONS_UPLOAD=uit.
-->
<template>
  <div class="cc-uploadmenu">
    <p v-if="!mid" class="cc-leeg">{{ t("upload.no_file") }}</p>
    <template v-else-if="menu">
      <h2><a :href="menu.bestand.url" target="_blank" rel="noopener">{{ menu.bestand.naam }}</a></h2>
      <p v-if="!menu.uitsneden.length" class="cc-leeg">{{ t("upload.nothing_saved") }}</p>
      <ul class="cc-uploadlijst">
        <li v-for="item in menu.uitsneden" :key="item.id" :class="{ uit: !item.gekozen }">
          <cdx-checkbox :model-value="item.gekozen" :disabled="!item.upload_toegestaan" @update:model-value="choose(item, $event)">
            <span class="cc-visually-hidden">{{ item.bestandsnaam }}</span>
          </cdx-checkbox>
          <img :src="`${item.object.uitsnede_url}?w=160`" alt="" loading="lazy" />
          <div>
            <strong>{{ item.bestandsnaam }}</strong>
            <p class="cc-bestand-regel">
              <rights-label v-for="label in item.rechten.labels" :key="label" :label="label" />
              <span class="cc-klein">{{ item.formaat.toUpperCase() }} · {{ item.object.opgeslagen.breedte }} × {{ item.object.opgeslagen.hoogte }} px</span>
            </p>
            <p class="cc-klein">{{ item.caption[language] || item.caption.nl || item.caption.en }}</p>
            <ul v-if="check[item.id]" class="cc-controle">
              <li v-if="check[item.id].in_orde" class="goed">{{ t("upload.check_ok") }}</li>
              <li v-for="warning in check[item.id].waarschuwingen" :key="warning.code" class="fout">{{ t(`check.${warning.code}`) }} — {{ t(`check.${warning.code}_text`, { detail: warning.detail ?? "" }) }}</li>
            </ul>
            <details v-if="preview">
              <summary>{{ t("concept.preview") }}</summary>
              <pre class="cc-wikitekst">{{ item.wikitekst }}</pre>
              <pre class="cc-wikitekst">{{ JSON.stringify(item.sdc, null, 2) }}</pre>
            </details>
            <a class="cc-klein" :href="`/?mid=${mid}&pagina=${item.pagina}&object=${item.id}`">{{ t("upload.edit") }}</a>
          </div>
        </li>
      </ul>

      <div v-if="menu.uitsneden.length" class="cc-upload-acties">
        <cdx-button action="progressive" :disabled="busy || !chosen.length" @click="runCheck">{{ t("upload.check", { n: chosen.length }) }}</cdx-button>
        <cdx-toggle-switch v-model="preview">{{ t("upload.preview") }}</cdx-toggle-switch>
        <cdx-button action="progressive" @click="downloadZip"><cdx-icon :icon="cdxIconDownload" /> {{ t("actions.zip") }}</cdx-button>
        <cdx-checkbox v-model="confirmed">{{ t("upload.confirm") }}</cdx-checkbox>
        <cdx-button action="progressive" weight="primary" :disabled="!confirmed || !chosen.length || !menu.upload_aan || busy" @click="upload">
          <cdx-icon :icon="cdxIconUpload" /> {{ t("upload.upload", { n: chosen.length }) }}
        </cdx-button>
        <cdx-message v-if="!menu.upload_aan" type="notice" :inline="true">{{ t("upload.disabled") }}</cdx-message>
      </div>
    </template>
    <cdx-message v-if="error" type="error">{{ error }}</cdx-message>
  </div>
</template>

<script setup>
import { computed, inject, onMounted, ref } from "vue";
import { CdxButton, CdxCheckbox, CdxIcon, CdxMessage, CdxToggleSwitch } from "@wikimedia/codex";
import { cdxIconDownload, cdxIconUpload } from "@wikimedia/codex-icons";
import { errorText, filePath, get, objectPath, patch, post, query } from "../api.js";
import { useT } from "../i18n.js";
import RightsLabel from "./RightsLabel.vue";

const props = defineProps({ mid: { type: String, default: "" } });
const t = useT();
const language = inject("language", "nl");
const menu = ref(null);
const check = ref({});
const preview = ref(false);
const confirmed = ref(false);
const busy = ref(false);
const error = ref("");
const chosen = computed(() => (menu.value?.uitsneden || []).filter((item) => item.gekozen));

async function load() {
  try {
    menu.value = await get(`${filePath(props.mid)}/commons`);
  } catch (e) {
    error.value = errorText(t, e);
  }
}

async function choose(item, value) {
  try {
    await patch(`${objectPath(props.mid, item.pagina, item.id)}/commons`, { gekozen: value });
    item.gekozen = value;
  } catch (e) {
    error.value = errorText(t, e);
  }
}

async function runCheck() {
  busy.value = true;
  error.value = "";
  try {
    const objecten = chosen.value.map((item) => `${item.pagina}:${item.id}`).join(",");
    check.value = (await get(`${filePath(props.mid)}/commons/controle${query({ objecten })}`)).controle;
  } catch (e) {
    error.value = errorText(t, e);
  } finally {
    busy.value = false;
  }
}

async function upload() {
  busy.value = true;
  try {
    await post(`${filePath(props.mid)}/commons/uploads`, { bevestigd: true, objecten: chosen.value.map((i) => ({ pagina: i.pagina, id: i.id })) });
  } catch (e) {
    error.value = errorText(t, e);
  } finally {
    busy.value = false;
  }
}

function downloadZip() {
  window.location.href = `${filePath(props.mid)}/export?formaat=zip`;
}

onMounted(() => props.mid && load());
</script>
