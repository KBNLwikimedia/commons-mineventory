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
      <viewed-panel :entries="visited" @aside="setAsideEntry" @remove="forget" @clear="forgetAll" />
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
        :tabindex="mobileTab === item ? 0 : -1"
        @click="mobileTab = item"
        @keydown="onTabKey"
      >
        {{ item === "links" ? t("layout.tab_objects", { n: objects.length }) : t(`layout.tab_${item}`) }}
      </button>
    </div>

    <div v-if="file && !file.ondersteund" class="cc-unsupported">
      <cdx-message type="warning">{{ file.niet_ondersteund_code ? t(`file.unsupported_${file.niet_ondersteund_code}`, { mime: file.mime || "?" }) : file.niet_ondersteund }}</cdx-message>
    </div>

    <div v-else-if="file && page" class="cc-werkblad" :class="`cc-mobiel-${mobileTab}`" :style="{ '--cc-kolommen': gridColumns }">
      <!-- The images viewed in this browser, with thumbnails. Every column folds away
           to a narrow strip (closed.*, remembered in this browser); on narrow screens not. -->
      <aside class="cc-historie cc-kolom" :class="{ dicht: closed.historie }" :aria-label="t('layout.history_title')">
        <div class="cc-kolom-inhoud">
          <column-header column="history" closable side="left" @close="setClosed('historie', true)" />
          <viewed-panel :entries="visited" :current="file.mid" @aside="setAsideEntry" @remove="forget" @clear="forgetAll" />
        </div>
        <column-strip v-if="closed.historie" :name="t('layout.history_title')" :count="visited.length" side="left" @open="setClosed('historie', false)" />
      </aside>
      <column-splitter variable="--cc-historie-breedte" side="left" storage-key="cc-breedte-historie" :label="t('layout.resize_history')" :min="140" :max="420" :class="['cc-historie-rand', { 'cc-splitter-uit': !resizable('historie') }]" />
      <!-- Workflow from left to right, as in the Delpher Uitsnijder: the image, finding
           objects (detection), then what you found, with the buttons to save it.
           (The class names cc-links/cc-rechts are historical: the objects column is cc-links.) -->
      <section id="cc-kolom-midden" class="cc-midden cc-kolom" :class="{ dicht: closed.beeld }" role="tabpanel" aria-labelledby="cc-tab-midden">
        <div class="cc-kolom-inhoud">
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
        >
          <template #balk>
            <cdx-button weight="quiet" size="small" class="cc-kolom-dicht-knop" :aria-label="t('layout.column_close', { name: t('layout.tab_midden') })" :title="t('layout.column_close', { name: t('layout.tab_midden') })" @click="setClosed('beeld', true)">
              <cdx-icon :icon="cdxIconPrevious" size="small" />
            </cdx-button>
          </template>
        </viewer-pane>
        </div>
        <column-strip v-if="closed.beeld" :name="t('layout.tab_midden')" side="left" @open="setClosed('beeld', false)" />
      </section>
      <column-splitter variable="--cc-paneel-breedte" side="right" storage-key="cc-breedte-rechts" :label="t('layout.resize_right')" :max="800" :class="{ 'cc-splitter-uit': !resizable('zoeken') }" />
      <aside id="cc-kolom-rechts" class="cc-rechts cc-kolom" :class="{ dicht: closed.zoeken }" role="tabpanel" aria-labelledby="cc-tab-rechts" :aria-label="t('layout.right')">
        <div class="cc-kolom-inhoud">
        <column-header column="right" closable side="right" @close="setClosed('zoeken', true)" />
        <detection-panel
          :file="file"
          :page="page"
          :busy="busy"
          :inventory="inventory"
          :objects="objects"
          :trash-terms="trashTerms"
          :last-result="lastResult"
          :point-mode="pointMode"
          @detect="detect"
          @inventory="askInventory(Boolean(inventory), $event?.deel || null)"
          @forget-inventory="forgetInventory($event?.deel || null)"
          @inventory-changed="inventory = $event"
          :draw-mode="drawMode"
          @point-mode="setMode('point', $event)"
          @draw-mode="setMode('draw', $event)"
        />
        </div>
        <column-strip v-if="closed.zoeken" :name="t('layout.right_title')" side="right" @open="setClosed('zoeken', false)" />
      </aside>
      <column-splitter variable="--cc-links-breedte" side="right" storage-key="cc-breedte-links" :label="t('layout.resize_objects')" :class="{ 'cc-splitter-uit': !resizable('objecten') }" />
      <aside id="cc-kolom-links" class="cc-links cc-kolom" :class="{ dicht: closed.objecten }" role="tabpanel" aria-labelledby="cc-tab-links" :aria-label="t('layout.left')">
        <div class="cc-kolom-inhoud">
        <column-header column="left" closable side="right" @close="setClosed('objecten', true)" />
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
        <div class="cc-acties">
          <p class="cc-telling">{{ t("objects.count", { n: objects.length, selected: selectedCount }) }} <retention-info /></p>
          <!-- What you do with what you found: describe the ticked ones, merge duplicates,
               save. A button is disabled when there is nothing to do. -->
          <span class="cc-acties-rij">
            <cdx-button action="progressive" :disabled="busy || !toDescribe" :title="t('objects.describe_help')" @click="describeAll">
              {{ t("panel.describe_all") }}<template v-if="toDescribe"> ({{ toDescribe }}) <span class="cc-kosten">{{ describeCost }}</span></template>
            </cdx-button>
            <cdx-button action="progressive" weight="quiet" :disabled="busy || objects.length < 2" :title="t('objects.merge_help')" @click="mergeDuplicates">
              {{ t("panel.merge") }}
            </cdx-button>
          </span>
          <busy-note v-if="busy && busyAt === 'objecten'" :message="t('busy.describe')" />
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
        </div>
        <column-strip v-if="closed.objecten" :name="t('layout.left_title')" :count="objects.length" side="right" @open="setClosed('objecten', false)" />
      </aside>
    </div>

    <magnifier
      v-if="magnified"
      v-model:open="magnifierOpen"
      :file="file"
      :n="pageN"
      :object="magnified"
      :position="{ index: magnifiedIndex + 1, total: listOrder.length }"
      :list-name="listNames[magnifiedId] || ''"
      @step="stepMagnifier"
      @changed="replaceObject"
      @trashed="trashObject($event)"
      @refine="refineMask"
    />

    <confirm-dialog />
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref } from "vue";
import { CdxButton, CdxIcon, CdxMessage } from "@wikimedia/codex";
import { cdxIconDownload, cdxIconPrevious, cdxIconUpload } from "@wikimedia/codex-icons";
import { API, del, errorText, filePath, get, objectPath, pagePath, patch, post, query } from "../api.js";
import { askConfirm } from "../confirm.js";
import { money, useT } from "../i18n.js";
import BusyNote from "./BusyNote.vue";
import ColumnHeader from "./ColumnHeader.vue";
import ColumnSplitter from "./ColumnSplitter.vue";
import ColumnStrip from "./ColumnStrip.vue";
import ConfirmDialog from "./ConfirmDialog.vue";
import { addToHistory, appUrl, clearHistory, numberedNames, objectName, readHistory, readStart, removeFromHistory, setAside } from "../state.js";
import ViewedPanel from "./ViewedPanel.vue";
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
const MOBILE_TABS = ["midden", "rechts", "links"]; // the order of the columns
const mobileTab = ref("midden");
// Arrow keys, Home and End move between the tabs, as in every tab list.
function onTabKey(event) {
  const index = MOBILE_TABS.indexOf(mobileTab.value);
  const next = { ArrowRight: index + 1, ArrowLeft: index - 1, Home: 0, End: MOBILE_TABS.length - 1 }[event.key];
  if (next === undefined) return;
  event.preventDefault();
  mobileTab.value = MOBILE_TABS[(next + MOBILE_TABS.length) % MOBILE_TABS.length];
  nextTick(() => document.getElementById(`cc-tab-${mobileTab.value}`)?.focus());
}
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
// The four columns, left to right; each can be folded away to a narrow strip,
// remembered in this browser. The image column takes the room that is left; when
// it is folded away, the first open column of the others does.
const COLUMNS = ["historie", "beeld", "zoeken", "objecten"];
const WIDTHS = { historie: "var(--cc-historie-breedte)", zoeken: "var(--cc-paneel-breedte)", objecten: "var(--cc-links-breedte)" };
function readClosed(column) {
  try {
    return window.localStorage.getItem(`cc-kolom-dicht-${column}`) === "1";
  } catch {
    return false; // blocked storage: every column starts open
  }
}
const closed = reactive(Object.fromEntries(COLUMNS.map((column) => [column, readClosed(column)])));
function setClosed(column, value) {
  closed[column] = value;
  try {
    window.localStorage.setItem(`cc-kolom-dicht-${column}`, value ? "1" : "0");
  } catch {
    // Blocked storage: the choice holds until the page is reloaded.
  }
}
const flexibleColumn = computed(() => (closed.beeld ? ["zoeken", "objecten", "historie"].find((c) => !closed[c]) : "beeld"));
// A border can be dragged when the column it sizes is open and not the flexible one.
const resizable = (column) => !closed[column] && flexibleColumn.value !== column;
const gridColumns = computed(() => {
  const width = (column) => (closed[column] ? "2.25rem" : column === flexibleColumn.value ? "minmax(0, 1fr)" : WIDTHS[column]);
  return COLUMNS.map(width).join(" 0.75rem ");
});
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
    const asked = `${file.value.mid}/${n}`;
    get(`${pagePath(file.value.mid, n)}/inventaris`)
      .then((plan) => {
        if (asked === `${file.value?.mid}/${pageN.value}`) inventory.value = plan.inventaris; // not for a page left meanwhile
      })
      .catch(() => {});
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

// The outcome of the last detection, for the panel ({found, excluded, prompt, modus}).
const lastResult = ref(null);

async function detect(request) {
  lastResult.value = null;
  const base = pagePath(file.value.mid, pageN.value);
  busy.value = true;
  try {
    if (request.modus !== "commons") {
      const estimate = await get(`${base}/detecties/raming${query(request)}`);
      if (!(await confirmCost(estimate.aanroepen.betaald, estimate.aanroepen.betaald * props.config.sam_usd))) return;
    }
    const result = await post(`${base}/detecties`, request);
    replaceObjects(result.objecten, result.nieuw);
    // The outcome is shown in the panel, under the button that asked for it.
    const excluded = result.objecten.filter((o) => result.nieuw.includes(o.id) && o.status === "uitgesloten").length;
    lastResult.value = { found: result.nieuw.length - excluded, excluded, prompt: request.prompt || "", modus: request.modus, at: Date.now() };
  } catch (error) {
    fail(error);
  } finally {
    busy.value = false;
  }
}

// Remove the page overview, or one part of it ("beschrijving" or "zoektermen"), after a confirmation.
async function forgetInventory(part = null) {
  const key = part || "alles";
  if (!(await askConfirm(t(`panel.part_forget_confirm_${key}`), { title: t(`panel.part_forget_title_${key}`), go: t("panel.part_forget"), destructive: true }))) return;
  try {
    const result = await del(`${pagePath(file.value.mid, pageN.value)}/inventaris${part ? `/${part}` : ""}`);
    inventory.value = result.inventaris;
    notify("success", t(`panel.part_forgotten_${key}`));
  } catch (error) {
    fail(error);
  }
}

// The page overview. With `again` the model is really asked anew (paid);
// otherwise a stored answer for this page and model comes from the cache, free.
// With `part` ("beschrijving" or "zoektermen") only that part is asked anew.
async function askInventory(again = false, part = null) {
  const base = pagePath(file.value.mid, pageN.value);
  busy.value = true;
  try {
    const plan = await get(`${base}/inventaris`);
    if (!(await confirmCost(plan.betaald ? 1 : 0, plan.kosten_schatting_usd))) return;
    const result = await post(part ? `${base}/inventaris/${part}` : `${base}/inventaris`, part ? {} : { opnieuw: again });
    inventory.value = result.inventaris;
  } catch (error) {
    fail(error);
  } finally {
    busy.value = false;
  }
}

async function mergeDuplicates() {
  try {
    const result = await post(`${pagePath(file.value.mid, pageN.value)}/samenvoegingen`, {});
    replaceObjects(result.objecten);
    notify("success", t("detect.merged", { n: result.samengevoegd }));
  } catch (error) {
    fail(error);
  }
}

// Ticked objects without a description: what "Describe selection" describes, and its price.
const toDescribe = computed(() => objects.value.filter((o) => o.status === "geselecteerd" && !o.beschrijving).length);
const describeCost = computed(() => (props.config.betaald ? `(${money(props.config.muse.beschrijving_usd * toDescribe.value, props.config.taal)})` : t("panel.free")));
// Where the waiting feedback goes for actions in the objects column.
const busyAt = ref(null);

async function describeAll() {
  busyAt.value = "objecten";
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
    busyAt.value = null;
  }
}

async function onPoint({ x, y }) {
  if (!pointMode.value) return;
  // Always the price first: only a click on the shape of a known object is free,
  // and the shapes are on the server (a click in a box beside its shape is a new search).
  if (!(await confirmCost(1, props.config.sam_usd))) return;
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
  if (!(await confirmCost(1, props.config.sam_usd))) return;
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
    links: objectsLinks(),
    dontAsk: "trash", // the trash can be undone (notice with Undo), so this may be switched off
  });
  if (!ok) return;
  const n = pageN.value;
  const mid = file.value.mid; // Undo later restores in this file, also after opening another
  // What the notice shows of the object: taken before it leaves the list.
  const obj = objects.value.find((o) => o.id === id);
  const shown = obj && {
    image: `${objectPath(file.value.mid, n, id)}/uitsnede.jpg?w=96`,
    name: objectName(obj, props.config.taal, t),
    description: (props.config.taal === "en" ? obj.beschrijving?.beschrijving_en : obj.beschrijving?.beschrijving) || obj.beschrijving?.beschrijving || obj.bijschrift?.tekst || "",
  };
  // Trashed from the magnifier: it stays open, on the next object of the list
  // (or the previous one at the end); without objects left it closes.
  const order = listOrder.value;
  const at = order.indexOf(id);
  const neighbour = order[at + 1] || order[at - 1] || null;
  try {
    const result = await del(objectPath(file.value.mid, n, id));
    if (magnifiedId.value === id) {
      if (neighbour && result.objecten.some((o) => o.id === neighbour)) {
        magnifiedId.value = neighbour; // before the list changes, so the magnifier is not closed in between
        focusedId.value = neighbour;
      } else {
        magnifierOpen.value = false;
      }
    }
    objects.value = result.objecten;
    refreshTrashTerms(n);
    notify("notice", t("objects.trashed"), {
      object: shown,
      actions: [{ label: `↶ ${t("magnifier.undo")}`, run: () => restoreObject(id, n, mid) }],
      link: { href: "/objecten?tab=prullenbak", label: t("objects.to_trash") },
    });
  } catch (error) {
    fail(error);
  }
}

async function restoreObject(id, n, mid = file.value.mid) {
  try {
    await patch(objectPath(mid, n, id), { prullenbak: false });
    if (mid === file.value?.mid && n === pageN.value) {
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

// Set an image aside ("Opzij gezet") or bring it back: no confirmation, nothing is lost.
function setAsideEntry(mid, aside) {
  visited.value = setAside(mid, aside);
}

// Taking an image off the "Viewed" list removes only the entry, after a confirmation
// that says so: the image, its objects and saved cut-outs stay.
// The pages to go to from a confirmation: Objects and its Trash tab.
const objectsLinks = () => ({
  objects: { href: "/objecten", label: t("objects.page_link") },
  trash: { href: "/objecten?tab=prullenbak", label: t("objects.trash_link") },
});

async function forget(mid) {
  const entry = visited.value.find((e) => e.mid === mid);
  const name = entry?.naam || mid;
  const links = {
    ...objectsLinks(),
    // The M-id opens the image again (in the input bar, and back in the active list).
    mid: { href: appUrl(mid, entry?.pagina || 1), label: mid, sameTab: true, class: "cc-mid-link" },
  };
  if (await askConfirm(t("history.remove_confirm", { name }), { title: t("history.remove"), go: t("history.remove"), destructive: true, links })) {
    visited.value = removeFromHistory(mid);
  }
}

async function forgetAll() {
  if (await askConfirm(t("history.clear_confirm"), { title: t("history.clear"), go: t("history.clear"), destructive: true, links: objectsLinks() })) visited.value = clearHistory();
}

function openMagnifier(id) {
  magnifiedId.value = id;
  magnifierOpen.value = true;
}

// Previous and next in the magnifier: the order of the list "Wat je vond".
const listNames = computed(() => numberedNames(objects.value, props.config.taal, t));
const listOrder = computed(() => Object.keys(listNames.value));
const magnifiedIndex = computed(() => listOrder.value.indexOf(magnifiedId.value));
function stepMagnifier(step) {
  const next = listOrder.value[magnifiedIndex.value + step];
  if (!next) return;
  magnifiedId.value = next;
  focusedId.value = next; // the list and the image follow
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
