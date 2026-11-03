<!--
  /objecten (functional design 10.4): all detected and saved objects over all
  files, with facets (source, saved) and the trash.
-->
<template>
  <div class="cc-pagina-objecten">
    <cdx-tabs v-model:active="tab" :framed="true">
      <cdx-tab name="objecten" :label="t('objects.tab_objects', { n: objects.length })">
        <div class="cc-facetten">
          <cdx-field :is-fieldset="true">
            <template #label>{{ t("objects.facet_source") }}</template>
            <cdx-checkbox v-for="source in sources" :key="source" v-model="chosenSources" :input-value="source" :inline="true">
              {{ t(`source.${source}`) }} ({{ count(source) }})
            </cdx-checkbox>
          </cdx-field>
          <cdx-toggle-switch v-model="onlySaved">{{ t("objects.only_saved") }}</cdx-toggle-switch>
        </div>
        <p v-if="!shown.length" class="cc-leeg">{{ t("objects.none_found") }}</p>
        <ul class="cc-raster">
          <li v-for="obj in shown" :key="obj.mid + obj.id">
            <a :href="obj.app_url">
              <img :src="`${obj.uitsnede_url}?w=200`" :alt="name(obj)" loading="lazy" />
            </a>
            <strong>{{ name(obj) }}</strong>
            <small>{{ t(`source.${obj.bron}`) }}<template v-if="obj.opgeslagen"> · {{ t("objects.saved") }}</template></small>
            <small class="cc-afkappen" :title="obj.bestand_titel">{{ obj.bestand_titel }}</small>
          </li>
        </ul>
      </cdx-tab>
      <cdx-tab name="prullenbak" :label="t('objects.tab_trash', { n: trash.length })">
        <p v-if="!trash.length" class="cc-leeg">{{ t("objects.trash_empty") }}</p>
        <template v-else>
          <cdx-button action="destructive" @click="emptyTrash">{{ t("objects.empty_trash") }}</cdx-button>
          <ul class="cc-raster">
            <li v-for="obj in trash" :key="obj.mid + obj.id">
              <img :src="`${obj.uitsnede_url}?w=200`" :alt="name(obj)" loading="lazy" />
              <strong>{{ name(obj) }}</strong>
              <small class="cc-afkappen">{{ obj.bestand_titel }}</small>
              <span class="cc-knoppen">
                <cdx-button size="small" @click="restore(obj)"><cdx-icon :icon="cdxIconRestore" /> {{ t("objects.restore") }}</cdx-button>
                <cdx-button size="small" action="destructive" @click="purge(obj)">{{ t("objects.delete_forever") }}</cdx-button>
              </span>
            </li>
          </ul>
        </template>
      </cdx-tab>
    </cdx-tabs>
    <cdx-message v-if="error" type="error">{{ error }}</cdx-message>
    <confirm-dialog />
  </div>
</template>

<script setup>
import { computed, inject, onMounted, ref } from "vue";
import { CdxButton, CdxCheckbox, CdxField, CdxIcon, CdxMessage, CdxTab, CdxTabs, CdxToggleSwitch } from "@wikimedia/codex";
import { cdxIconRestore } from "@wikimedia/codex-icons";
import { API, del, errorText, get, objectPath, patch } from "../api.js";
import { askConfirm } from "../confirm.js";
import { useT } from "../i18n.js";
import ConfirmDialog from "./ConfirmDialog.vue";
import { objectName } from "../state.js";

const t = useT();
const language = inject("language", "nl");
// ?tab=prullenbak opens the trash directly (the link after "Naar de prullenbak").
const tab = ref(new URLSearchParams(window.location.search).get("tab") === "prullenbak" ? "prullenbak" : "objecten");
const objects = ref([]);
const trash = ref([]);
const chosenSources = ref([]);
const onlySaved = ref(false);
const error = ref("");

const sources = computed(() => [...new Set(objects.value.map((o) => o.bron))].sort());
const count = (source) => objects.value.filter((o) => o.bron === source).length;
const name = (obj) => objectName(obj, language, t);
const shown = computed(() =>
  objects.value.filter((o) => (!chosenSources.value.length || chosenSources.value.includes(o.bron)) && (!onlySaved.value || o.opgeslagen))
);

async function load() {
  try {
    objects.value = (await get(`${API}/objecten`)).objecten;
    trash.value = (await get(`${API}/prullenbak`)).objecten;
  } catch (e) {
    error.value = errorText(t, e);
  }
}

async function restore(obj) {
  try {
    await patch(objectPath(obj.mid, obj.pagina, obj.id), { prullenbak: false });
    await load();
  } catch (e) {
    error.value = errorText(t, e);
  }
}

async function purge(obj) {
  if (!(await askConfirm(t("objects.delete_confirm"), { go: t("objects.delete_forever"), destructive: true }))) return;
  try {
    await del(`${API}/prullenbak/${obj.mid}/${obj.pagina}/${encodeURIComponent(obj.id)}`);
    await load();
  } catch (e) {
    error.value = errorText(t, e);
  }
}

async function emptyTrash() {
  if (!(await askConfirm(t("objects.empty_confirm", { n: trash.value.length }), { go: t("objects.empty_trash"), destructive: true }))) return;
  try {
    await del(`${API}/prullenbak`);
    await load();
  } catch (e) {
    error.value = errorText(t, e);
  }
}

onMounted(load);
</script>
