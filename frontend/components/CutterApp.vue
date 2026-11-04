<!--
  The start page (functional design 10.4): input bar and file information,
  pages and objects on the left, the viewer in the middle, the detection panel
  on the right, and the magnifier as a dialog. All data comes from /api/v1.
-->
<template>
  <div class="cc-app">
    <file-bar :file="file" :loading="loadingFile" :initial="initialInput" @open="openFile" />

    <notice-list :notices="notices" @dismiss="dismiss" />

    <section v-if="!file && !loadingFile && visited.length" class="cc-start-geschiedenis">
      <h2>{{ t("history.title") }}</h2>
      <history-list :entries="visited" @remove="forget" @clear="forgetAll" />
    </section>

    <!-- On a phone (functional design 10.5) the three columns are tabs; on larger screens this bar is hidden. -->
    <div v-if="file && file.ondersteund && page" class="cc-mobiel-tabs" role="tablist" :aria-label="t('layout.tabs')">
      <button
        v-for="item in MOBILE_TABS"
        :id="`cc-tab-${item}`"
        :key="item"
        type="button"
        role="tab"
        class="cc-mobiel-tab"
        :aria-selected="mobileTab === item ? 'true' : 'false'"
        :aria-controls="`cc-kolom-${item}`"
        @click="mobileTab = item"
      >
        {{ item === "links" ? t("layout.tab_objects", { n: objects.length }) : t(`layout.tab_${item}`) }}
      </button>
    </div>

    <div v-if="file && !file.ondersteund" class="cc-unsupported">
      <cdx-message type="warning">{{ file.niet_ondersteund }}</cdx-message>
    </div>

    <div v-else-if="file && page" class="cc-werkblad" :class="`cc-mobiel-${mobileTab}`">
      <aside id="cc-kolom-links" class="cc-links" :aria-label="t('layout.left')">
        <cdx-accordion v-if="visited.length > 1" class="cc-geschiedenis-blok">
          <template #title>{{ t("history.title") }} <small>({{ visited.length }})</small></template>
          <history-list :entries="visited" :current="file.mid" @remove="forget" @clear="forgetAll" />
        </cdx-accordion>
        <page-list v-if="file.paginas > 1" :file="file" :current="pageN" @select="goToPage" />
        <object-list
          :mid="file.mid"
          :n="pageN"
          :objects="objects"
          :focused="focusedId"
          :hovered="hoveredId"
          :new-ids="newIds"
          @toggle="toggleSelected"
          @select="setSelection"
          @focus="focusObject"
          @open="openMagnifier"
          @hover="hoverObject"
          @trash="trashObject"
        />
      </aside>
      <column-splitter variable="--cc-links-breedte" side="left" storage-key="cc-breedte-links" :label="t('layout.resize_left')" />

      <section id="cc-kolom-midden" class="cc-midden">
        <viewer-pane
          ref="viewer"
          :mid="file.mid"
          :page="page"
          :objects="objects"
          :new-ids="newIds"
          :point-mode="pointMode"
          :draw-mode="drawMode"
          @object-click="onObjectClick"
          @object-open="openMagnifier($event.id)"
          @object-hover="hoveredId = $event"
          @point="onPoint"
          @rectangle="onRectangle"
        />
      </section>
      <column-splitter variable="--cc-paneel-breedte" side="right" storage-key="cc-breedte-rechts" :label="t('layout.resize_right')" :max="800" />

      <aside id="cc-kolom-rechts" class="cc-rechts" :aria-label="t('layout.right')">
        <detection-panel
          :file="file"
          :page="page"
          :busy="busy"
          :inventory="inventory"
          :objects="objects"
          :trash-terms="trashTerms"
          :point-mode="pointMode"
          @detect="detect"
          @smart="smartDetect"
          @inventory="askInventory(Boolean(inventory))"
          @merge="mergeDuplicates"
          @describe-all="describeAll"
          :draw-mode="drawMode"
          @point-mode="setMode('point', $event)"
          @draw-mode="setMode('draw', $event)"
        />
        <div class="cc-acties">
          <p class="cc-telling">{{ t("objects.count", { n: objects.length, selected: selectedCount }) }} <retention-info /></p>
          <cdx-button action="progressive" weight="primary" :disabled="!selectedCount || busy" @click="saveSelection">
            {{ t("actions.save", { n: selectedCount }) }}
          </cdx-button>
          <cdx-button action="progressive" :disabled="!savedCount" @click="downloadZip">
            <cdx-icon :icon="cdxIconDownload" /> {{ t("actions.zip") }}
          </cdx-button>
          <cdx-button action="progressive" :disabled="!savedCount" @click="toCommons">
            <cdx-icon :icon="cdxIconUpload" /> {{ t("actions.to_commons") }}
          </cdx-button>
        </div>
      </aside>
    </div>

    <magnifier
      v-if="magnified"
      v-model:open="magnifierOpen"
      :file="file"
      :n="pageN"
      :object="magnified"
      @changed="replaceObject"
      @trashed="trashObject($event)"
      @refine="refineMask"
    />

    <confirm-dialog />
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { CdxAccordion, CdxButton, CdxIcon, CdxMessage } from "@wikimedia/codex";
import { cdxIconDownload, cdxIconUpload } from "@wikimedia/codex-icons";
import { API, del, errorText, filePath, get, objectPath, pagePath, patch, post, query } from "../api.js";
import { askConfirm } from "../confirm.js";
import { money, useT } from "../i18n.js";
import ColumnSplitter from "./ColumnSplitter.vue";
import ConfirmDialog from "./ConfirmDialog.vue";
import { addToHistory, appUrl, clearHistory, objectName, readHistory, readStart, removeFromHistory } from "../state.js";
import HistoryList from "./HistoryList.vue";
import DetectionPanel from "./DetectionPanel.vue";
import FileBar from "./FileBar.vue";
import Magnifier from "./Magnifier.vue";
import NoticeList from "./NoticeList.vue";
import RetentionInfo from "./RetentionInfo.vue";
import ObjectList from "./ObjectList.vue";
import PageList from "./PageList.vue";
import ViewerPane from "./ViewerPane.vue";

const props = defineProps({ config: { type: Object, required: true } });
const t = useT();

const file = ref(null);
const pageN = ref(1);
const page = ref(null);
// Per search term: objects of this page in the trash (for the AI suggestions).
const trashTerms = ref({});
const objects = ref([]);
const newIds = ref([]);
// Phone: which column shows (objects, image, detection); the image first.
const MOBILE_TABS = ["links", "midden", "rechts"];
const mobileTab = ref("midden");
const inventory = ref(null);
const focusedId = ref(null);
// The object under the mouse in the viewer, so the list can light it up too.
const hoveredId = ref(null);
const pointMode = ref(false);
const drawMode = ref(false);

// Aanwijzen and Rechthoek tekenen exclude each other.
function setMode(mode, on) {
  pointMode.value = mode === "point" && on;
  drawMode.value = mode === "draw" && on;
}
const loadingFile = ref(false);
const busy = ref(false);
const notices = ref([]);
const viewer = ref(null);
const magnifierOpen = ref(false);
const magnifiedId = ref(null);
const start = readStart(window.location.search);
const visited = ref(readHistory());
// A bare start page (e.g. back from /objecten) reopens the file that was open last.
if (!start.url && !start.titel && !start.mid && visited.value.length) {
  start.mid = visited.value[0].mid;
  start.pagina = String(visited.value[0].pagina || 1);
}
const initialInput = start.url || start.titel || start.mid || "";

const selectedCount = computed(() => objects.value.filter((o) => o.status === "geselecteerd").length);
const savedCount = computed(() => objects.value.filter((o) => o.opgeslagen).length);
const magnified = computed(() => objects.value.find((o) => o.id === magnifiedId.value) || null);

// -- Notices --------------------------------------------------------------------------

let noticeId = 0;
function notify(type, text, extra = {}) {
  notices.value = [...notices.value.slice(-3), { id: ++noticeId, type, text, ...extra }];
}
function dismiss(id) {
  notices.value = notices.value.filter((n) => n.id !== id);
}
function fail(error) {
  notify("error", errorText(t, error));
}

// -- Confirming paid actions (6.4): only in live mode, with the amount --------------------

async function confirmCost(calls, usd) {
  if (!props.config.betaald || !calls) return true;
  return askConfirm(t("confirm.cost", { n: calls, amount: money(usd, props.config.taal) }), { title: t("confirm.cost_title") });
}

// -- Loading --------------------------------------------------------------------------

async function openFile(text) {
  loadingFile.value = true;
  try {
    const isMid = /^m\d+$/i.test(text.trim());
    const found = await get(`${API}/bestand${query(isMid ? { mid: text.trim() } : { url: text.trim() })}`);
    file.value = found;
    if (found.doorverwezen_van) notify("notice", t("file.redirected", { from: found.doorverwezen_van, to: found.titel }));
    if (found.ondersteund) await goToPage(start.mid === found.mid && start.pagina ? Number(start.pagina) : 1);
  } catch (error) {
    file.value = null;
    page.value = null;
    fail(error);
  } finally {
    loadingFile.value = false;
  }
}

async function goToPage(n) {
  pageN.value = n;
  try {
    const data = await get(pagePath(file.value.mid, n));
    page.value = data;
    objects.value = data.objecten;
    trashTerms.value = data.prullenbak_termen || {};
    newIds.value = [];
    inventory.value = null;
    window.history.replaceState(null, "", appUrl(file.value.mid, n));
    visited.value = addToHistory({ mid: file.value.mid, naam: file.value.naam, pagina: n, paginas: file.value.paginas });
    get(`${pagePath(file.value.mid, n)}/inventaris`).then((plan) => (inventory.value = plan.inventaris)).catch(() => {});
    if (start.object) {
      const id = start.object;
      start.object = "";
      setTimeout(() => focusObject(id), 300);
    }
  } catch (error) {
    fail(error);
  }
}

function replaceObjects(list, fresh = []) {
  objects.value = list;
  newIds.value = fresh;
}

function replaceObject(changed) {
  objects.value = objects.value.map((o) => (o.id === changed.id ? changed : o));
}

// -- Detection (7) ----------------------------------------------------------------------

async function detect(request) {
  const base = pagePath(file.value.mid, pageN.value);
  busy.value = true;
  try {
    if (request.modus !== "commons") {
      const estimate = await get(`${base}/detecties/raming${query(request)}`);
      if (!(await confirmCost(estimate.aanroepen.betaald, estimate.aanroepen.betaald * 0.0025))) return;
    }
    const result = await post(`${base}/detecties`, request);
    replaceObjects(result.objecten, result.nieuw);
    if (result.niets_gevonden) notify("notice", t("detect.nothing"));
    else notify("success", t("detect.found", { n: result.nieuw.length }));
  } catch (error) {
    fail(error);
  } finally {
    busy.value = false;
  }
}

// The page overview. With `again` the model is really asked anew (paid);
// otherwise a stored answer for this page and model comes from the cache, free.
async function askInventory(again = false) {
  const base = pagePath(file.value.mid, pageN.value);
  busy.value = true;
  try {
    const plan = await get(`${base}/inventaris`);
    if (!(await confirmCost(plan.betaald ? 1 : 0, plan.kosten_schatting_usd))) return;
    const result = await post(`${base}/inventaris`, { opnieuw: again });
    inventory.value = result.inventaris;
  } catch (error) {
    fail(error);
  } finally {
    busy.value = false;
  }
}

// Slim detecteren (7.4): first the page overview, then SAM with the suggested terms.
async function smartDetect() {
  await askInventory();
  const terms = (inventory.value?.zoektermen || []).map((term) => term.en);
  if (terms.length) await detect({ modus: "prompt", prompt: terms.join(", ") });
}

async function mergeDuplicates() {
  try {
    const result = await patch(`${pagePath(file.value.mid, pageN.value)}/objecten`, { samenvoegen: true });
    replaceObjects(result.objecten);
    notify("success", t("detect.merged", { n: result.samengevoegd }));
  } catch (error) {
    fail(error);
  }
}

async function describeAll() {
  const chosen = objects.value.filter((o) => o.status === "geselecteerd" && !o.beschrijving);
  if (!chosen.length) return notify("notice", t("describe.nothing_to_do"));
  const usd = props.config.muse.beschrijving_usd * chosen.length;
  if (!(await confirmCost(chosen.length, usd))) return;
  busy.value = true;
  try {
    for (const obj of chosen) {
      const result = await post(`${objectPath(file.value.mid, pageN.value, obj.id)}/beschrijving`, {});
      replaceObject(result.object);
    }
    notify("success", t("describe.done", { n: chosen.length }));
  } catch (error) {
    fail(error);
  } finally {
    busy.value = false;
  }
}

async function onPoint({ x, y }) {
  if (!pointMode.value) return;
  const hit = objects.value.find((o) => o.box.x <= x && x <= o.box.x + o.box.w && o.box.y <= y && y <= o.box.y + o.box.h);
  if (!hit && !(await confirmCost(1, 0.0025))) return;
  busy.value = true;
  try {
    const result = await post(`${pagePath(file.value.mid, pageN.value)}/detecties`, { punt: { x, y } });
    if (!result.object) return notify("notice", t("detect.nothing"));
    if (result.nieuw) objects.value = [...objects.value.filter((o) => o.id !== result.object.id), result.object];
    newIds.value = [result.object.id];
    focusedId.value = result.object.id;
  } catch (error) {
    fail(error);
  } finally {
    busy.value = false;
  }
}

async function onRectangle(rect) {
  try {
    const result = await post(`${pagePath(file.value.mid, pageN.value)}/detecties`, { rechthoek: rect });
    objects.value = [...objects.value.filter((o) => o.id !== result.object.id), result.object];
    newIds.value = [result.object.id];
    focusedId.value = result.object.id;
    notify("success", t("detect.rectangle"));
  } catch (error) {
    fail(error);
  }
}

async function refineMask(obj) {
  if (!(await confirmCost(1, 0.0025))) return;
  try {
    const result = await post(`${pagePath(file.value.mid, pageN.value)}/detecties`, { masker_voor: obj.id });
    replaceObject(result.object);
    notify("success", t("detect.mask_done"));
  } catch (error) {
    fail(error);
  }
}

// -- Selection and objects ----------------------------------------------------------------

async function setSelection(ids) {
  try {
    const result = await patch(`${pagePath(file.value.mid, pageN.value)}/objecten`, { geselecteerd: ids });
    objects.value = result.objecten;
  } catch (error) {
    fail(error);
  }
}

function toggleSelected(id) {
  const selected = objects.value.filter((o) => o.status === "geselecteerd").map((o) => o.id);
  setSelection(selected.includes(id) ? selected.filter((s) => s !== id) : [...selected, id]);
}

function onObjectClick({ object, ctrl }) {
  if (ctrl) toggleSelected(object.id);
  else focusObject(object.id, false);
}

function focusObject(id, zoom = true) {
  focusedId.value = id;
  viewer.value?.focusObject(id, zoom);
}

function hoverObject(id, on) {
  viewer.value?.setObjectHover(id, on);
}

// To the trash: first a confirmation that says where the trash is, afterwards
// a notice with Undo and a link to the trash (/objecten, tab Prullenbak).
async function trashObject(id) {
  const ok = await askConfirm(t("objects.trash_confirm"), {
    title: t("objects.trash"),
    go: t("objects.trash"),
    destructive: true,
    links: {
      objects: { href: "/objecten", label: t("objects.page_link") },
      trash: { href: "/objecten?tab=prullenbak", label: t("objects.trash_link") },
    },
  });
  if (!ok) return;
  const n = pageN.value;
  // What the notice shows of the object: taken before it leaves the list.
  const obj = objects.value.find((o) => o.id === id);
  const shown = obj && {
    image: `${objectPath(file.value.mid, n, id)}/uitsnede.jpg?w=96`,
    name: objectName(obj, props.config.taal, t),
    description: (props.config.taal === "en" ? obj.beschrijving?.beschrijving_en : obj.beschrijving?.beschrijving) || obj.beschrijving?.beschrijving || obj.bijschrift?.tekst || "",
  };
  try {
    const result = await del(objectPath(file.value.mid, n, id));
    objects.value = result.objecten;
    refreshTrashTerms(n);
    if (magnifiedId.value === id) magnifierOpen.value = false;
    notify("notice", t("objects.trashed"), {
      object: shown,
      actions: [{ label: `↶ ${t("magnifier.undo")}`, run: () => restoreObject(id, n) }],
      link: { href: "/objecten?tab=prullenbak", label: t("objects.to_trash") },
    });
  } catch (error) {
    fail(error);
  }
}

async function restoreObject(id, n) {
  try {
    await patch(objectPath(file.value.mid, n, id), { prullenbak: false });
    if (n === pageN.value) {
      const data = await get(pagePath(file.value.mid, n));
      objects.value = data.objecten;
      trashTerms.value = data.prullenbak_termen || {};
    }
    notify("success", t("objects.restored"));
  } catch (error) {
    fail(error);
  }
}

// The trash counts per search term, fetched again after a move to or from the trash.
function refreshTrashTerms(n) {
  get(pagePath(file.value.mid, n))
    .then((data) => {
      if (n === pageN.value) trashTerms.value = data.prullenbak_termen || {};
    })
    .catch(() => {});
}

// -- History ("Laatst bezocht") ----------------------------------------------------------

function forget(mid) {
  visited.value = removeFromHistory(mid);
}

async function forgetAll() {
  if (await askConfirm(t("history.clear_confirm"), { go: t("history.clear"), destructive: true })) visited.value = clearHistory();
}

function openMagnifier(id) {
  magnifiedId.value = id;
  magnifierOpen.value = true;
}

// -- Saving and export (9.5) ---------------------------------------------------------------

async function saveSelection() {
  busy.value = true;
  try {
    const result = await post(`${pagePath(file.value.mid, pageN.value)}/uitsneden`, {});
    objects.value = result.objecten;
    notify("success", t("save.done", { n: result.opgeslagen.length }));
  } catch (error) {
    fail(error);
  } finally {
    busy.value = false;
  }
}

function downloadZip() {
  window.location.href = `${filePath(file.value.mid)}/export?formaat=zip`;
}

function toCommons() {
  window.location.href = `/commons?mid=${encodeURIComponent(file.value.mid)}`;
}

onMounted(() => {
  if (initialInput) openFile(initialInput);
});
</script>
