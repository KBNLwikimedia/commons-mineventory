<!--
  /objecten (functional design 10.4): all detected and saved objects over all
  files, with facets (source, file, saved) and the trash. Each object can go to
  the trash, and so can everything the facets show, in one go; both with Undo.
-->
<template>
  <div class="cc-pagina-objecten">
    <!-- Not everything is kept forever: say so where the saved cut-outs are. -->
    <p class="cc-klein cc-bewaren">{{ t("retention.short", { n: config.bewaren?.uitsneden ?? 30 }) }} <retention-info /></p>
    <cdx-tabs v-model:active="tab" :framed="true">
      <cdx-tab name="objecten" :label="t('objects.tab_objects', { n: objects.length })">
        <!-- Facets on the left, stacked; the objects on the right. -->
        <div class="cc-objecten-indeling">
        <aside class="cc-facetten">
          <cdx-field :is-fieldset="true">
            <template #label>{{ t("objects.facet_source") }}</template>
            <cdx-checkbox v-for="source in sources" :key="source" v-model="chosenSources" :input-value="source" >
              {{ t(`source.${source}`) }} ({{ count(source) }})
            </cdx-checkbox>
          </cdx-field>
          <cdx-field v-if="files.length > 1" :is-fieldset="true">
            <template #label>{{ t("objects.facet_file") }}</template>
            <cdx-checkbox v-for="f in files" :key="f.mid" v-model="chosenFiles" :input-value="f.mid" >
              <span class="cc-afkappen cc-facet-bestand" :title="f.titel">{{ f.titel }}</span> ({{ f.n }})
            </cdx-checkbox>
          </cdx-field>
          <cdx-toggle-switch v-model="onlySaved">{{ t("objects.only_saved") }}</cdx-toggle-switch>
        </aside>
        <div class="cc-objecten-inhoud">
        <!-- Bulk: everything the facets show now. -->
        <div v-if="shown.length" class="cc-knoppen cc-bulk">
          <cdx-button action="destructive" :disabled="busy" @click="trashShown">
            <cdx-icon :icon="cdxIconTrash" /> {{ t(filtered ? "objects.trash_shown" : "objects.trash_all", { n: shown.length }) }}
          </cdx-button>
        </div>
        <cdx-message v-if="undo" type="notice" :allow-user-dismiss="true" :dismiss-button-label="t('actions.close')" @user-dismissed="undo = null">
          {{ t("objects.trashed_n", { n: undo.length }) }}
          <button type="button" class="cc-link" :disabled="busy" @click="restoreMany(undo)">↶ {{ t("magnifier.undo") }}</button>
          <button type="button" class="cc-link" @click="tab = 'prullenbak'">{{ t("objects.to_trash") }}</button>
        </cdx-message>
        <p v-if="!shown.length" class="cc-leeg">{{ t("objects.none_found") }}</p>
        <ul class="cc-raster">
          <li v-for="obj in shown" :key="obj.mid + obj.id">
            <a :href="obj.app_url">
              <img :src="`${obj.uitsnede_url}?w=200`" :alt="name(obj)" loading="lazy" />
            </a>
            <!-- Name with a small trash button beside it. -->
            <span class="cc-kaart-kop">
              <strong>{{ name(obj) }}</strong>
              <cdx-button action="destructive" weight="quiet" size="small" :disabled="busy" :aria-label="t('objects.trash')" :title="t('objects.trash')" @click="trashMany([obj])">
                <cdx-icon :icon="cdxIconTrash" size="small" />
              </cdx-button>
            </span>
            <small>{{ t(`source.${obj.bron}`) }}<template v-if="obj.opgeslagen"> · <span :class="{ 'cc-verloopt-bijna': savedLabel(obj, t, language).soon }" :title="savedLabel(obj, t, language).title">{{ savedLabel(obj, t, language).text }}</span></template></small>
            <small class="cc-afkappen" :title="obj.bestand_titel">{{ obj.bestand_titel }}</small>
          </li>
        </ul>
        </div>
        </div>
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
                <cdx-button action="progressive" size="small" @click="restore(obj)"><cdx-icon :icon="cdxIconRestore" /> {{ t("objects.restore") }}</cdx-button>
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
import { cdxIconRestore, cdxIconTrash } from "@wikimedia/codex-icons";
import { API, del, errorText, get, objectPath, patch } from "../api.js";
import { askConfirm } from "../confirm.js";
import { useT } from "../i18n.js";
import ConfirmDialog from "./ConfirmDialog.vue";
import RetentionInfo from "./RetentionInfo.vue";
import { objectName, savedLabel } from "../state.js";

const t = useT();
const language = inject("language", "nl");
const config = inject("config", {});
// ?tab=prullenbak opens the trash directly (the link after "Naar de prullenbak").
const tab = ref(new URLSearchParams(window.location.search).get("tab") === "prullenbak" ? "prullenbak" : "objecten");
const objects = ref([]);
const trash = ref([]);
const chosenSources = ref([]);
const chosenFiles = ref([]);
const onlySaved = ref(false);
const error = ref("");
const busy = ref(false);
// The objects of the last move to the trash, for Undo.
const undo = ref(null);

const sources = computed(() => [...new Set(objects.value.map((o) => o.bron))].sort());
const count = (source) => objects.value.filter((o) => o.bron === source).length;
const name = (obj) => objectName(obj, language, t);
// The files with objects, for the file facet.
const files = computed(() => {
  const byMid = new Map();
  for (const o of objects.value) {
    const entry = byMid.get(o.mid) || { mid: o.mid, titel: "", n: 0 };
    // Not every object carries the file title; take the first one that does.
    entry.titel ||= (o.bestand_titel || "").replace(/^File:/, "");
    entry.n += 1;
    byMid.set(o.mid, entry);
  }
  return [...byMid.values()].map((f) => ({ ...f, titel: f.titel || f.mid })).sort((a, b) => a.titel.localeCompare(b.titel));
});
const shown = computed(() =>
  objects.value.filter(
    (o) =>
      (!chosenSources.value.length || chosenSources.value.includes(o.bron)) &&
      (!chosenFiles.value.length || chosenFiles.value.includes(o.mid)) &&
      (!onlySaved.value || o.opgeslagen)
  )
);
const filtered = computed(() => shown.value.length !== objects.value.length);

async function load() {
  try {
    objects.value = (await get(`${API}/objecten`)).objecten;
    trash.value = (await get(`${API}/prullenbak`)).objecten;
  } catch (e) {
    error.value = errorText(t, e);
  }
}

// To the trash, one by one on the server (each is a small, locked change).
async function trashMany(list) {
  busy.value = true;
  error.value = "";
  const done = [];
  try {
    for (const obj of list) {
      await del(objectPath(obj.mid, obj.pagina, obj.id));
      done.push(obj);
    }
  } catch (e) {
    error.value = errorText(t, e);
  } finally {
    undo.value = done.length ? done : null;
    busy.value = false;
    await load();
  }
}

async function trashShown() {
  const n = shown.value.length;
  const text = t(filtered.value ? "objects.trash_shown_confirm" : "objects.trash_all_confirm", { n });
  if (!(await askConfirm(text, { title: t("objects.trash"), go: t("objects.trash"), destructive: true }))) return;
  await trashMany([...shown.value]);
}

async function restoreMany(list) {
  busy.value = true;
  try {
    for (const obj of list) await patch(objectPath(obj.mid, obj.pagina, obj.id), { prullenbak: false });
    undo.value = null;
  } catch (e) {
    error.value = errorText(t, e);
  } finally {
    busy.value = false;
    await load();
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
  const n = trash.value.length;
  const text = n === 1 ? t("objects.empty_confirm_one") : t("objects.empty_confirm", { n });
  if (!(await askConfirm(text, { go: t("objects.delete_forever"), destructive: true }))) return;
  try {
    await del(`${API}/prullenbak`);
    await load();
  } catch (e) {
    error.value = errorText(t, e);
  }
}

onMounted(load);
</script>
