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
        <object-facets :objects="objects" :filters="objectFilters" @preview="openPreview">
          <template #export>
            <export-links v-if="objects.length" :url="`${API}/objecten/export`" :params="exportParams(objectFilters)" :filtered="filtered" :n="shown.length" />
          </template>
        </object-facets>
        <column-splitter variable="--cc-facet-breedte" side="left" storage-key="cc-breedte-facetten" area=".cc-objecten-indeling" :label="t('objects.resize_facets')" :min="160" :max="520" class="cc-facet-rand" />
        <div class="cc-objecten-inhoud">
        <!-- Bulk: everything the facets show now. -->
        <div v-if="shown.length" class="cc-knoppen cc-objecten-bulk">
          <cdx-button action="destructive" :disabled="busy" @click="trashShown">
            <cdx-icon :icon="cdxIconTrash" /> {{ t(filtered ? "objects.trash_shown" : "objects.trash_all", { n: shown.length }) }}
          </cdx-button>
          <view-switch v-model="view" :buttons="viewButtons" storage-key="cc-weergave-objecten" :use-stored="!viewInAddress" />
        </div>
        <!-- To the trash: yellow, with Undo and the way to the trash (undo.js). -->
        <undo-message :note="objectsNote">
          <button v-if="objectsNote.message?.undo" type="button" class="cc-link" @click="tab = 'prullenbak'">{{ t("objects.to_trash") }}</button>
        </undo-message>
        <p v-if="!shown.length" class="cc-leeg">{{ t("objects.none_found") }}</p>
        <objects-table v-if="view === 'lijst' && shown.length" :objects="shown" :name="name" :saved-url="savedUrl" link-images v-model:sort="sortParam" @sorted="sortedObjects = $event" @show-in-folder="showInFolder">
          <template #actions="{ object: obj }">
            <a class="cc-kaart-oog" :href="magnifierUrl(obj)" @click="openHere($event, obj)" :aria-label="t(augmentedEye(obj) ? 'objects.open_augmented' : 'objects.open_magnifier')" :title="t(augmentedEye(obj) ? 'objects.open_augmented' : 'objects.open_magnifier')">
              <cdx-icon :icon="cdxIconEye" size="small" />
            </a>
            <cdx-button action="destructive" weight="quiet" size="small" :disabled="busy" :aria-label="t('objects.trash')" :title="t('objects.trash')" @click="trashOne(obj)">
              <cdx-icon :icon="cdxIconTrash" size="small" />
            </cdx-button>
          </template>
        </objects-table>
        <ul v-else-if="view === 'kaarten'" class="cc-raster">
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
        <!-- Back from the trash (with Undo) or deleted for good: green (wish Olaf 13-11-2026). -->
        <undo-message :note="trashNote" />
        <p v-if="!trash.length" class="cc-leeg">{{ t("objects.trash_empty") }}</p>
        <!-- The same facets as the objects, with their own choice (wish Olaf). -->
        <div v-else class="cc-objecten-indeling">
        <object-facets :objects="trash" :filters="trashFilters" @preview="openPreview">
          <template #export>
            <export-links v-if="trash.length" :url="`${API}/prullenbak/export`" :params="exportParams(trashFilters)" :filtered="trashFiltered" :n="shownTrash.length" />
          </template>
        </object-facets>
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
            <view-switch v-model="view" :buttons="viewButtons" storage-key="cc-weergave-objecten" :use-stored="!viewInAddress" />
          </div>
          <p v-if="!shownTrash.length" class="cc-leeg">{{ t("objects.none_found") }}</p>
          <objects-table v-if="view === 'lijst' && shownTrash.length" :objects="shownTrash" :name="name" :saved-url="savedUrl" v-model:sort="sortParam" @sorted="sortedTrash = $event" @show-in-folder="showInFolder">
            <template #actions="{ object: obj }">
              <button type="button" class="cc-kaart-oog" :aria-label="t('objects.open_magnifier')" :title="t('objects.open_magnifier')" @click="openTrashed(obj)">
                <cdx-icon :icon="cdxIconEye" size="small" />
              </button>
              <cdx-button action="progressive" size="small" @click="restore(obj)"><cdx-icon :icon="cdxIconRestore" /> {{ t("objects.restore") }}</cdx-button>
              <cdx-button size="small" action="destructive" @click="purge(obj)">{{ t("objects.delete_forever") }}</cdx-button>
            </template>
          </objects-table>
          <ul v-else-if="view === 'kaarten'" class="cc-raster">
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
import { computed, inject, onMounted, reactive, ref, watch } from "vue";
import { CdxButton, CdxDialog, CdxIcon, CdxMessage, CdxTab, CdxTabs } from "@wikimedia/codex";
import { cdxIconEye, cdxIconRestore, cdxIconTrash } from "@wikimedia/codex-icons";
import { API, del, errorText, get, objectPath, patch, post } from "../api.js";
import { askConfirm, askConfirmValue, askRemoval } from "../confirm.js";
import { useT } from "../i18n.js";
import SavedLabel from "./SavedLabel.vue";
import ColumnSplitter from "./ColumnSplitter.vue";
import ExportLinks from "./ExportLinks.vue";
import CommonsLogo from "./CommonsLogo.vue";
import ConfirmDialog from "./ConfirmDialog.vue";
import Magnifier from "./Magnifier.vue";
import ObjectFacets from "./ObjectFacets.vue";
import ObjectsTable from "./ObjectsTable.vue";
import ViewSwitch from "./ViewSwitch.vue";
import ZoomImage from "./ZoomImage.vue";
import { applyFacets, emptyFilters, fileImage, readAddress, writeAddress } from "../facets.js";
import RetentionInfo from "./RetentionInfo.vue";
import UndoMessage from "./UndoMessage.vue";
import { useUndoMessage } from "../undo.js";
import { fileName, objectName } from "../state.js";

const t = useT();
const language = inject("language", "nl");
const config = inject("config", {});
// ?tab=prullenbak opens the trash directly (the link after "Naar de prullenbak").
const tab = ref(new URLSearchParams(window.location.search).get("tab") === "prullenbak" ? "prullenbak" : "objecten");
const objects = ref([]);
const trash = ref([]);
// The choice in the facets, per tab.
// ?mid=M… shows one file and ?opgeslagen=1 only saved cut-outs, on the tab that opens (wish Olaf:
// the links in "Start this image over").
// The whole choice of the open tab is in the address and comes back from it (wish Olaf: RESTful),
// with the names of the export: bron, mid, opgeslagen, aangevuld, q.
const asked = new URLSearchParams(window.location.search);
const fromAddress = () => {
  const { bron, mid, q } = readAddress(["bron", "mid"]);
  return { ...emptyFilters(), sources: bron, files: mid.filter((m) => /^M\d+$/.test(m)), saved: asked.get("opgeslagen") === "1", augmented: asked.get("aangevuld") === "1", query: q };
};
const objectFilters = reactive(tab.value === "objecten" ? fromAddress() : emptyFilters());
const trashFilters = reactive(tab.value === "prullenbak" ? fromAddress() : emptyFilters());
const error = ref("");
const busy = ref(false);
// The message of each tab after a change (undo.js): to the trash, back, or deleted for good.
const objectsNote = useUndoMessage(t);
const trashNote = useUndoMessage(t);

// The eye opens the object in the magnifier; with the facet AI-augmented on, straight at its
// AI-augmented version (wish Olaf).
const augmentedEye = (obj) => objectFilters.augmented && Boolean(obj.aangevuld);
const magnifierUrl = (obj) => `${obj.app_url}&vergroten=${augmentedEye(obj) ? "aangevuld" : "1"}`;
const name = (obj) => objectName(obj, language, t);
const exportParams = (filters) => ({ bron: filters.sources, mid: filters.files, opgeslagen: filters.saved, aangevuld: filters.augmented, q: filters.query });
watch(
  () => [tab.value, exportParams(tab.value === "prullenbak" ? trashFilters : objectFilters)],
  ([open, params]) => writeAddress({ tab: open === "prullenbak" ? "prullenbak" : "", ...params }),
  { deep: true }
);
const shown = computed(() => applyFacets(objects.value, objectFilters));
const filtered = computed(() => shown.value.length !== objects.value.length);
const shownTrash = computed(() => applyFacets(trash.value, trashFilters));
const trashFiltered = computed(() => shownTrash.value.length !== trash.value.length);

// Cards or a list with sortable columns (wish Olaf), the same on both tabs.
// The view, the sorted column and an open magnifier in the address too (wish Olaf): weergave=lijst,
// sorteer=zekerheid or -zekerheid, object=M…/1/obj-…&vergroten=1|aangevuld.
const viewInAddress = asked.has("weergave");
const view = ref(asked.get("weergave") === "lijst" ? "lijst" : "kaarten");
const sortParam = ref(asked.get("sorteer") || "");
watch(view, (shown) => writeAddress({ weergave: shown === "lijst" ? "lijst" : "" }));
watch(sortParam, (sorteer) => writeAddress({ sorteer }));
const viewButtons = [
  { value: "kaarten", label: t("view.cards") },
  { value: "lijst", label: t("view.list") },
];
// The order of the list on screen, for ‹ › in the magnifier.
const sortedObjects = ref([]);
const sortedTrash = ref([]);

async function load() {
  try {
    objects.value = (await get(`${API}/objecten`)).objecten;
    trash.value = (await get(`${API}/prullenbak`)).objecten;
    openFromAddress();
  } catch (e) {
    error.value = errorText(t, e);
  }
}

// ?object=M…/1/obj-… opens that object in the magnifier, once, on the tab of the address.
let magnifierAsked = asked.get("object");
function openFromAddress() {
  if (!magnifierAsked) return;
  const from = tab.value === "prullenbak" ? "prullenbak" : "objecten";
  const found = (from === "prullenbak" ? trash.value : objects.value).find((o) => keyOf(o) === magnifierAsked);
  magnifierAsked = null;
  if (!found) return;
  magnifierFrom.value = from;
  magnifiedKey.value = keyOf(found);
  magnifierTab.value = asked.get("vergroten") === "aangevuld" ? "aangevuld" : "";
  magnifierOpen.value = true;
}

// To the trash and back, one by one on the server (each is a small, locked change); `done` collects
// the ones that went, so a failure halfway still offers Undo for those.
async function toTrash(list, done = []) {
  for (const obj of list) {
    await del(objectPath(obj.mid, obj.pagina, obj.id));
    done.push(obj);
  }
}
async function fromTrash(list, done = []) {
  for (const obj of list) {
    await patch(objectPath(obj.mid, obj.pagina, obj.id), { prullenbak: false });
    done.push(obj);
  }
}
// The work of a bulk button: busy meanwhile, an error in red, the lists loaded again afterwards.
async function working(work) {
  busy.value = true;
  error.value = "";
  try {
    await work();
  } catch (e) {
    error.value = errorText(t, e);
  } finally {
    busy.value = false;
    await load();
  }
}

async function trashMany(list) {
  const done = [];
  await working(() => toTrash(list, done));
  if (!done.length) return;
  // Yellow, with Undo: back from the trash (green afterwards).
  objectsNote.show("warning", t("objects.trashed_n", { n: done.length }), async () => {
    await fromTrash(done);
    await load();
  }, { done: t("feedback.restored_n", { n: done.length }) });
}

// One object from its card: first a confirmation, like every move to the trash (wish Olaf).
async function trashOne(obj) {
  const text = t("objects.trash_one_confirm", { name: name(obj) });
  let note = t("objects.trash_one_note");
  if (obj.bron === "commons") note += "\n\n" + t("objects.trash_one_commons");
  // With its thumbnail, so you see what goes (wish Olaf).
  const objects = [{ image: `${obj.uitsnede_url}?w=96`, name: name(obj) }];
  if (!(await askConfirm(text, { title: t("objects.trash"), go: t("objects.trash"), destructive: true, objects, note }))) return;
  await trashMany([obj]);
}

async function trashShown() {
  const n = shown.value.length;
  const text = t(filtered.value ? "objects.trash_shown_confirm" : "objects.trash_all_confirm", { n });
  // The thumbnails too, as long as the list stays readable.
  const objects = n <= 40 ? shown.value.map((o) => ({ image: `${o.uitsnede_url}?w=96`, name: name(o) })) : [];
  // Each object a tick box (wish Olaf 13-11-2026): leave one out after all.
  const pick = n > 1 && objects.length ? { min: 1, text: (k) => t(filtered.value || k < n ? "objects.trash_shown_confirm" : "objects.trash_all_confirm", { n: k }) } : null;
  const answer = await askConfirmValue(text, { title: t("objects.trash"), go: t("objects.trash"), destructive: true, objects, note: t("objects.trash_many_note"), pick });
  if (!answer.ok) return;
  await trashMany(objects.length ? answer.picked.map((i) => shown.value[i]) : [...shown.value]);
}

// Back from the trash: green, with Undo (to the trash again).
async function restoreMany(list) {
  const done = [];
  await working(() => fromTrash(list, done));
  if (!done.length) return;
  trashNote.show("success", t("feedback.restored_n", { n: done.length }), async () => {
    await toTrash(done);
    await load();
  }, { done: t("objects.trashed_n", { n: done.length }) });
}

const restore = (obj) => restoreMany([obj]);

async function purge(obj) {
  const objects = [{ image: `${obj.uitsnede_url}?w=96`, name: name(obj) }];
  if (!(await askConfirm(t("objects.delete_confirm"), { go: t("objects.delete_forever"), destructive: true, objects, note: t("objects.cannot_undo") }))) return;
  try {
    await del(`${API}/prullenbak/${obj.mid}/${obj.pagina}/${encodeURIComponent(obj.id)}`);
    await load();
    trashNote.show("success", t("feedback.deleted_n", { n: 1 }));
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
  const pick = list.length > 1 && objects.length ? { min: 1, text: (k) => t("objects.delete_shown_confirm", { n: k }) } : null;
  const answer = await askConfirmValue(t("objects.delete_shown_confirm", { n: list.length }), { go: t("objects.delete_forever"), destructive: true, objects, note: t("objects.cannot_undo"), pick });
  if (!answer.ok) return;
  const chosen = objects.length ? answer.picked.map((i) => list[i]) : list;
  let gone = 0;
  await working(async () => {
    for (const obj of chosen) {
      await del(`${API}/prullenbak/${obj.mid}/${obj.pagina}/${encodeURIComponent(obj.id)}`);
      gone += 1;
    }
  });
  if (gone) trashNote.show("success", t("feedback.deleted_n", { n: gone }));
}

async function emptyTrash() {
  const n = trash.value.length;
  const text = n === 1 ? t("objects.empty_confirm_one") : t("objects.empty_confirm", { n });
  // What goes, with its thumbnails, as long as the list stays readable (wish Olaf 13-11-2026).
  const objects = n <= 40 ? trash.value.map((o) => ({ image: `${o.uitsnede_url}?w=96`, name: name(o) })) : [];
  if (!(await askRemoval(text, { go: t("objects.delete_forever"), destructive: true }, { objects }))) return;
  try {
    await del(`${API}/prullenbak`);
    await load();
    trashNote.show("success", t("feedback.deleted_n", { n }));
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
const magnifierList = computed(() => {
  if (magnifierFrom.value === "prullenbak") return view.value === "lijst" ? sortedTrash.value : shownTrash.value;
  return view.value === "lijst" ? sortedObjects.value : shown.value;
});
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
watch(
  () => [magnifierOpen.value, magnifiedKey.value, magnifierTab.value],
  ([open, key, startTab]) => writeAddress({ object: open && key ? key : "", vergroten: open && key ? startTab || "1" : "" })
);
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
