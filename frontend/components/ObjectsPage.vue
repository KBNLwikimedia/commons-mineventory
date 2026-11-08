<!--
  /objecten (functional design 10.4): all detected and saved objects over all
  files, with facets (source, file, saved) and the trash. Each object can go to
  the trash, and so can everything the facets show, in one go; both with Undo.
-->
<template>
  <div class="cc-pagina-objecten">
    <!-- Not everything is kept forever: say so where the saved cut-outs are. -->
    <p class="cc-klein cc-bewaren">{{ t("retention.short", { n: config.bewaren?.uitsneden ?? 30 }) }} <retention-info /></p>
    <!-- What an object is and what a cut-out is: both are on this page. -->
    <p class="cc-uitleg cc-begrippen">
      <template v-for="(part, j) in t('terms.objects_cutouts').split('**')" :key="j"><strong v-if="j % 2">{{ part }}</strong><template v-else>{{ part }}</template></template>
    </p>
    <cdx-tabs v-model:active="tab" :framed="true">
      <cdx-tab name="objecten" :label="t('objects.tab_objects', { n: objects.length })">
        <!-- Facets on the left, stacked; the objects on the right. -->
        <div class="cc-objecten-indeling">
        <object-facets :objects="objects" :filters="objectFilters" @preview="openPreview" />
        <column-splitter variable="--cc-facet-breedte" side="left" storage-key="cc-breedte-facetten" area=".cc-objecten-indeling" :label="t('objects.resize_facets')" :min="160" :max="520" class="cc-facet-rand" />
        <div class="cc-objecten-inhoud">
        <!-- Bulk: everything the facets show now. -->
        <div v-if="shown.length" class="cc-knoppen cc-objecten-bulk">
          <cdx-button action="destructive" :disabled="busy" @click="trashShown">
            <cdx-icon :icon="cdxIconTrash" /> {{ t(filtered ? "objects.trash_shown" : "objects.trash_all", { n: shown.length }) }}
          </cdx-button>
        </div>
        <cdx-message v-if="undo" type="notice" :allow-user-dismiss="true" :dismiss-button-label="t('actions.close')" @user-dismissed="undo = null">
          {{ t("objects.trashed_n", { n: undo.length }) }}
          <button type="button" class="cc-link" :disabled="busy" @click="restoreMany(undo)">↶ {{ t("magnifier.undo") }}</button>
          <span aria-hidden="true"> · </span>
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
              <a class="cc-kaart-oog" :href="magnifierUrl(obj)" @click="openHere($event, obj)" :aria-label="t(augmentedEye(obj) ? 'objects.open_augmented' : 'objects.open_magnifier')" :title="t(augmentedEye(obj) ? 'objects.open_augmented' : 'objects.open_magnifier')">
                <cdx-icon :icon="cdxIconEye" size="small" />
              </a>
              <cdx-button action="destructive" weight="quiet" size="small" :disabled="busy" :aria-label="t('objects.trash')" :title="t('objects.trash')" @click="trashOne(obj)">
                <cdx-icon :icon="cdxIconTrash" size="small" />
              </cdx-button>
            </span>
            <small>{{ t(`source.${obj.bron}`) }}<template v-if="obj.aangevuld"> · {{ t("objects.ai_augmented") }}</template><template v-if="obj.opgeslagen"> · <saved-label :object="obj" /></template></small>
            <!-- A saved cut-out: open or download the file; on your own computer also show it in its folder (wish Olaf). -->
            <small v-if="obj.opgeslagen" class="cc-kaart-bestand">
              <a :href="savedUrl(obj)" target="_blank" rel="noopener">{{ t("objects.file_open_cutout") }}</a>
              <span aria-hidden="true"> · </span><a :href="`${savedUrl(obj)}?download=1`">{{ t("objects.file_download") }}</a>
              <template v-if="config.lokaal"><span aria-hidden="true"> · </span><button type="button" class="cc-link" :title="t('objects.show_in_folder_help')" @click="showInFolder(obj)">{{ t("objects.show_in_folder") }}</button></template>
            </small>
            <!-- The original the object comes from, linked to its page on Commons. -->
            <small class="cc-afkappen" :title="obj.bestand_titel">
              {{ t("objects.source_file") }}
              <a v-if="obj.bestand_url" :href="obj.bestand_url" target="_blank" rel="noopener">{{ fileName(obj.bestand_titel) }}</a>
              <template v-else>{{ fileName(obj.bestand_titel) }}</template>
            </small>
          </li>
        </ul>
        </div>
        </div>
      </cdx-tab>
      <cdx-tab name="prullenbak" :label="t('objects.tab_trash', { n: trash.length })">
        <p v-if="!trash.length" class="cc-leeg">{{ t("objects.trash_empty") }}</p>
        <!-- The same facets as the objects, with their own choice (wish Olaf). -->
        <div v-else class="cc-objecten-indeling">
        <object-facets :objects="trash" :filters="trashFilters" @preview="openPreview" />
        <column-splitter variable="--cc-facet-breedte" side="left" storage-key="cc-breedte-facetten" area=".cc-objecten-indeling" :label="t('objects.resize_facets')" :min="160" :max="520" class="cc-facet-rand" />
        <div class="cc-objecten-inhoud">
          <!-- Bulk: what the facets show; without a filter, the whole trash. -->
          <div v-if="shownTrash.length" class="cc-knoppen cc-objecten-bulk">
            <cdx-button action="progressive" :disabled="busy" @click="restoreShown">
              <cdx-icon :icon="cdxIconRestore" /> {{ t(trashFiltered ? "objects.restore_shown" : "objects.restore_all", { n: shownTrash.length }) }}
            </cdx-button>
            <cdx-button action="destructive" :disabled="busy" @click="trashFiltered ? purgeShown() : emptyTrash()">
              {{ trashFiltered ? t("objects.delete_shown", { n: shownTrash.length }) : t("objects.empty_trash") }}
            </cdx-button>
          </div>
          <p v-if="!shownTrash.length" class="cc-leeg">{{ t("objects.none_found") }}</p>
          <ul class="cc-raster">
            <li v-for="obj in shownTrash" :key="obj.mid + obj.id">
              <img :src="`${obj.uitsnede_url}?w=200`" :alt="name(obj)" loading="lazy" />
              <!-- The eye: the magnifier, also for a trashed object (wish Olaf). -->
              <span class="cc-kaart-kop">
                <strong>{{ name(obj) }}</strong>
                <button type="button" class="cc-kaart-oog" :aria-label="t('objects.open_magnifier')" :title="t('objects.open_magnifier')" @click="openTrashed(obj)">
                  <cdx-icon :icon="cdxIconEye" size="small" />
                </button>
              </span>
              <!-- As on the objects: a trashed object keeps its saved cut-outs until the trash is emptied. -->
              <small>{{ t(`source.${obj.bron}`) }}<template v-if="obj.aangevuld"> · {{ t("objects.ai_augmented") }}</template><template v-if="obj.opgeslagen"> · <saved-label :object="obj" /></template></small>
              <!-- A saved cut-out: open or download the file; on your own computer also show it in its folder (wish Olaf). -->
              <small v-if="obj.opgeslagen" class="cc-kaart-bestand">
                <a :href="savedUrl(obj)" target="_blank" rel="noopener">{{ t("objects.file_open_cutout") }}</a>
                <span aria-hidden="true"> · </span><a :href="`${savedUrl(obj)}?download=1`">{{ t("objects.file_download") }}</a>
                <template v-if="config.lokaal"><span aria-hidden="true"> · </span><button type="button" class="cc-link" :title="t('objects.show_in_folder_help')" @click="showInFolder(obj)">{{ t("objects.show_in_folder") }}</button></template>
              </small>
              <small class="cc-afkappen" :title="obj.bestand_titel">
                {{ t("objects.source_file") }}
                <a v-if="obj.bestand_url" :href="obj.bestand_url" target="_blank" rel="noopener">{{ fileName(obj.bestand_titel) }}</a>
                <template v-else>{{ fileName(obj.bestand_titel) }}</template>
              </small>
              <span class="cc-knoppen">
                <cdx-button action="progressive" size="small" @click="restore(obj)"><cdx-icon :icon="cdxIconRestore" /> {{ t("objects.restore") }}</cdx-button>
                <cdx-button size="small" action="destructive" @click="purge(obj)">{{ t("objects.delete_forever") }}</cdx-button>
              </span>
            </li>
          </ul>
        </div>
        </div>
      </cdx-tab>
    </cdx-tabs>
    <cdx-message v-if="error" type="error">{{ error }}</cdx-message>
    <!-- The magnifier on this page (wish Olaf): ‹ › go through the objects the filters show. -->
    <magnifier
      v-if="magnified"
      v-model:open="magnifierOpen"
      :file="magnifiedFile"
      :n="magnified.pagina"
      :object="magnified"
      :position="{ index: magnifiedIndex + 1, total: magnifierList.length }"
      :list-name="name(magnified)"
      :start-tab="magnifierTab"
      :in-trash="magnifierFrom === 'prullenbak'"
      @step="stepMagnifier"
      @changed="replaceObject"
      @trashed="trashFromMagnifier"
      @refine="toImagePage"
    />
    <cdx-dialog v-model:open="previewOpen" :title="preview?.titel || ''" :use-close-button="true" :close-button-label="t('actions.close')" class="cc-bestand-voorbeeld">
      <template v-if="preview">
        <div class="cc-knoppen">
          <a :href="`/?mid=${encodeURIComponent(preview.mid)}${preview.pagina > 1 ? `&pagina=${preview.pagina}` : ''}`"><img src="/static/img/icoon.svg" alt="" width="16" height="16" class="cc-app-merkje" />{{ t("objects.file_open") }}</a>
          <a v-if="preview.url" :href="preview.url" target="_blank" rel="noopener"><commons-logo />{{ t("objects.file_commons") }}</a>
        </div>
        <!-- One image to zoom (slider, wheel, buttons), drag and scroll, as in the magnifier (wish Olaf). -->
        <p v-if="previewState === 'error'" class="cc-leeg">{{ t("magnifier.load_error") }}</p>
        <zoom-image
          v-else-if="previewPage"
          class="cc-bestand-zoom"
          :src="fileImage(preview, 2560)"
          :width="previewPage.breedte"
          :height="previewPage.hoogte"
          :alt="preview.titel"
          :objects="previewObjects"
          :describe="describePreview"
          @error="previewState = 'error'"
        />
        <p v-else class="cc-leeg">{{ t("viewer.loading") }}</p>
      </template>
    </cdx-dialog>
    <confirm-dialog />
  </div>
</template>

<script setup>
import { computed, inject, onMounted, reactive, ref } from "vue";
import { CdxButton, CdxDialog, CdxIcon, CdxMessage, CdxTab, CdxTabs } from "@wikimedia/codex";
import { cdxIconEye, cdxIconRestore, cdxIconTrash } from "@wikimedia/codex-icons";
import { API, del, errorText, get, objectPath, patch, post } from "../api.js";
import { askConfirm } from "../confirm.js";
import { useT } from "../i18n.js";
import SavedLabel from "./SavedLabel.vue";
import ColumnSplitter from "./ColumnSplitter.vue";
import CommonsLogo from "./CommonsLogo.vue";
import ConfirmDialog from "./ConfirmDialog.vue";
import Magnifier from "./Magnifier.vue";
import ObjectFacets from "./ObjectFacets.vue";
import ZoomImage from "./ZoomImage.vue";
import { applyFacets, emptyFilters, fileImage } from "../facets.js";
import RetentionInfo from "./RetentionInfo.vue";
import { fileName, objectName } from "../state.js";

const t = useT();
const language = inject("language", "nl");
const config = inject("config", {});
// ?tab=prullenbak opens the trash directly (the link after "Naar de prullenbak").
const tab = ref(new URLSearchParams(window.location.search).get("tab") === "prullenbak" ? "prullenbak" : "objecten");
const objects = ref([]);
const trash = ref([]);
// The choice in the facets, per tab.
const objectFilters = reactive(emptyFilters());
const trashFilters = reactive(emptyFilters());
const error = ref("");
const busy = ref(false);
// The objects of the last move to the trash, for Undo.
const undo = ref(null);

// The eye opens the object in the magnifier; with the facet AI-augmented on, straight at its
// AI-augmented version (wish Olaf).
const augmentedEye = (obj) => objectFilters.augmented && Boolean(obj.aangevuld);
const magnifierUrl = (obj) => `${obj.app_url}&vergroten=${augmentedEye(obj) ? "aangevuld" : "1"}`;
const name = (obj) => objectName(obj, language, t);
const shown = computed(() => applyFacets(objects.value, objectFilters));
const filtered = computed(() => shown.value.length !== objects.value.length);
const shownTrash = computed(() => applyFacets(trash.value, trashFilters));
const trashFiltered = computed(() => shownTrash.value.length !== trash.value.length);

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

// One object from its card: first a confirmation, like every move to the trash (wish Olaf).
async function trashOne(obj) {
  let text = t("objects.trash_one_confirm", { name: name(obj) });
  if (obj.bron === "commons") text += "\n\n" + t("objects.trash_one_commons");
  // With its thumbnail, so you see what goes (wish Olaf).
  const objects = [{ image: `${obj.uitsnede_url}?w=96`, name: name(obj) }];
  if (!(await askConfirm(text, { title: t("objects.trash"), go: t("objects.trash"), destructive: true, objects }))) return;
  await trashMany([obj]);
}

async function trashShown() {
  const n = shown.value.length;
  const text = t(filtered.value ? "objects.trash_shown_confirm" : "objects.trash_all_confirm", { n });
  // The thumbnails too, as long as the list stays readable.
  const objects = n <= 40 ? shown.value.map((o) => ({ image: `${o.uitsnede_url}?w=96`, name: name(o) })) : [];
  if (!(await askConfirm(text, { title: t("objects.trash"), go: t("objects.trash"), destructive: true, objects }))) return;
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

// What the facets show in the trash: back, or gone for good (with a confirmation).
async function restoreShown() {
  await restoreMany([...shownTrash.value]);
}
async function purgeShown() {
  const list = [...shownTrash.value];
  const objects = list.length <= 40 ? list.map((o) => ({ image: `${o.uitsnede_url}?w=96`, name: name(o) })) : [];
  if (!(await askConfirm(t("objects.delete_shown_confirm", { n: list.length }), { go: t("objects.delete_forever"), destructive: true, objects }))) return;
  busy.value = true;
  try {
    for (const obj of list) await del(`${API}/prullenbak/${obj.mid}/${obj.pagina}/${encodeURIComponent(obj.id)}`);
  } catch (e) {
    error.value = errorText(t, e);
  } finally {
    busy.value = false;
    await load();
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

// -- The magnifier on this page ------------------------------------------------------------
const keyOf = (obj) => `${obj.mid}/${obj.pagina}/${obj.id}`;
const magnifiedKey = ref(null);
const magnifierOpen = ref(false);
const magnifierTab = ref("");
// From which tab the magnifier was opened: its objects (as the filters show them) are the ones
// ‹ › go through.
const magnifierFrom = ref("objecten");
const magnifierList = computed(() => (magnifierFrom.value === "prullenbak" ? shownTrash.value : shown.value));
const magnified = computed(() => (magnifierFrom.value === "prullenbak" ? trash.value : objects.value).find((o) => keyOf(o) === magnifiedKey.value) || null);
const magnifiedIndex = computed(() => magnifierList.value.findIndex((o) => keyOf(o) === magnifiedKey.value));
// What the magnifier needs of the file, from the fields every object here carries.
const magnifiedFile = computed(() => ({ mid: magnified.value.mid, titel: magnified.value.bestand_titel, url: magnified.value.bestand_url }));

function openHere(event, obj) {
  if (event.ctrlKey || event.metaKey || event.shiftKey || event.button !== 0) return; // a new tab: the image page
  event.preventDefault();
  magnifierFrom.value = "objecten";
  magnifiedKey.value = keyOf(obj);
  magnifierTab.value = augmentedEye(obj) ? "aangevuld" : "";
  magnifierOpen.value = true;
}
function openTrashed(obj) {
  magnifierFrom.value = "prullenbak";
  magnifiedKey.value = keyOf(obj);
  magnifierTab.value = "";
  magnifierOpen.value = true;
}
function stepMagnifier(step) {
  const next = magnifierList.value[magnifiedIndex.value + step];
  if (next) magnifiedKey.value = keyOf(next);
}
// A change in the magnifier (caption, description, AI-augmented version): into the list,
// keeping the fields of this page (file, page, URLs).
function replaceObject(changed) {
  if (!changed?.id || !magnified.value) return;
  const key = `${magnified.value.mid}/${magnified.value.pagina}/${changed.id}`;
  const list = magnifierFrom.value === "prullenbak" ? trash : objects;
  list.value = list.value.map((o) => (keyOf(o) === key ? { ...o, ...changed } : o));
}
async function trashFromMagnifier() {
  const obj = magnified.value;
  if (!obj) return;
  magnifierOpen.value = false;
  await trashOne(obj);
}
// A shape with SAM costs money and needs the image: that is done on the image page.
function toImagePage(obj) {
  const target = obj || magnified.value;
  if (target) window.location.href = `${target.app_url}&vergroten=1`;
}

// -- The image of a file, small in the facet and large in a dialog (wish Olaf) --------------
const preview = ref(null);
const previewOpen = ref(false);
// The size of the image (its page), which the zoom needs; read once per file (free, cached).
const previewPage = ref(null);
const previewState = ref("");
// Where the objects are on the image (wish Olaf): the outline of the mask of each object of this
// file, from the tab the preview was opened on (Objects or Trash); without a shape, its frame.
const previewFrom = ref("objecten");
const previewObjects = computed(() => {
  if (!preview.value) return [];
  const list = previewFrom.value === "prullenbak" ? trash.value : objects.value;
  return list
    .filter((o) => o.mid === preview.value.mid && (o.pagina || 1) === (preview.value.pagina || 1) && o.box)
    // Trashed ones too: the viewer leaves out the mask of an excluded object only.
    .map((o) => ({ ...o, status: o.status === "uitgesloten" ? "kandidaat" : o.status }));
});
const describePreview = (obj) => ({ title: name(obj), details: [t(`source.${obj.bron}`)], hint: "" });

async function openPreview(f) {
  previewFrom.value = tab.value;
  preview.value = f;
  previewPage.value = null;
  previewState.value = "";
  previewOpen.value = true;
  try {
    const page = await get(`${API}/bestand/${encodeURIComponent(f.mid)}/pagina/${f.pagina || 1}`);
    if (preview.value?.mid === f.mid) previewPage.value = { breedte: page.breedte, hoogte: page.hoogte };
  } catch {
    if (preview.value?.mid === f.mid) previewState.value = "error";
  }
}

// -- A saved cut-out on disk ----------------------------------------------------------------
// The file itself: the PNG of the shape when there is one, else the JPG of the frame.
const savedUrl = (obj) => (obj.opgeslagen?.png ? obj.uitsnede_png_url : obj.uitsnede_url);
// Only when the app runs on your own computer (config.lokaal): a window of the file manager.
async function showInFolder(obj) {
  error.value = "";
  try {
    await post(`${objectPath(obj.mid, obj.pagina, obj.id)}/uitsnede/mapvenster`, {});
  } catch (e) {
    error.value = errorText(t, e);
  }
}

onMounted(load);
</script>
