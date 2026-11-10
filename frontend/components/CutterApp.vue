<!--
  The start page (functional design 10.4): input bar and file information,
  pages and objects on the left, the viewer in the middle, the detection panel
  on the right, and the magnifier as a dialog. All data comes from /api/v1.
-->
<template>
  <div class="cc-app">
    <file-bar :file="file" :loading="loadingFile" :initial="initialInput" @open="openFile" />

    <notice-list :notices="topNotices" @dismiss="dismiss" />

    <!-- While a file is being opened: what is happening, and a grey placeholder where the work area comes. -->
    <section v-if="loadingFile" class="cc-bestand-laden" :aria-label="t('input.loading_file')">
      <busy-note :message="t('input.loading_file')" />
      <div class="cc-skelet cc-skelet-werkblad" aria-hidden="true"></div>
    </section>

    <section v-if="!file && !loadingFile && visited.length" class="cc-start-geschiedenis">
      <h2>{{ t("history.title") }}</h2>
      <viewed-panel :entries="visited" @aside="setAsideEntry" @remove="forget" @clear="forgetAll" @open="openFromHistory" @start-over="startOver" :work="workKept" />
    </section>

    <!-- On a phone (functional design 10.5) the three columns are tabs; on larger screens this bar is hidden. -->
    <div v-if="file && file.ondersteund && page && !loadingFile" class="cc-mobiel-tabs" role="tablist" :aria-label="t('layout.tabs')">
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

    <div v-if="!loadingFile && file && !file.ondersteund" class="cc-unsupported">
      <cdx-message type="warning">{{ file.niet_ondersteund_code ? t(`file.unsupported_${file.niet_ondersteund_code}`, { mime: file.mime || "?" }) : file.niet_ondersteund }}</cdx-message>
    </div>

    <div v-else-if="!loadingFile && file && page" class="cc-werkblad" :class="`cc-mobiel-${mobileTab}`" :style="{ '--cc-kolommen': gridColumns }">
      <!-- The images viewed in this browser, with thumbnails. Every column folds away
           to a narrow strip (closed.*, remembered in this browser); on narrow screens not. -->
      <aside class="cc-historie cc-kolom" :class="{ dicht: closed.historie }" :aria-label="t('layout.history_title')">
        <div class="cc-kolom-inhoud">
          <column-header column="history" closable side="left" @close="setClosed('historie', true)" />
          <viewed-panel :entries="visited" :current="file.mid" @aside="setAsideEntry" @remove="forget" @clear="forgetAll" @open="openFromHistory" @start-over="startOver" :work="workKept" />
        </div>
        <column-strip v-if="closed.historie" :name="t('layout.history_title')" :count="visited.length" side="left" @open="setClosed('historie', false)" />
      </aside>
      <column-splitter variable="--cc-historie-breedte" side="left" storage-key="cc-breedte-historie" :label="t('layout.resize_history')" :min="140" :max="420" :class="['cc-historie-rand', { 'cc-splitter-uit': !resizable('historie') }]" />
      <!-- Workflow from left to right, as in the Delpher Uitsnijder: the image, finding
           objects (detection), then what you found, with the buttons to save it.
           (The class names cc-links/cc-rechts are historical: the objects column is cc-links.) -->
      <section id="cc-kolom-midden" class="cc-midden cc-kolom" :class="{ dicht: closed.beeld }" role="tabpanel" aria-labelledby="cc-tab-midden">
        <div class="cc-kolom-inhoud">
        <!-- A header like the other columns (wish Olaf); its arrow folds the column away. -->
        <column-header column="image" closable side="left" @close="setClosed('beeld', true)" />
        <viewer-pane
          ref="viewer"
          :mid="file.mid"
          :page="page"
          :objects="visibleObjects"
          :class-colors="kindColors"
          :search-text="objectQuery"
          :new-ids="newIds"
          :point-mode="pointMode"
          :draw-mode="drawMode"
          @object-click="onObjectClick"
          @object-open="openMagnifier($event.id)"
          @object-hover="hoveredId = $event"
          @point="onPoint"
          @rectangle="onRectangle"
        >
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
          @dismiss-result="lastResult = null"
          @read-again="readAgain"
          :point-mode="pointMode"
          @detect="detect"
          @inventory="askInventory(Boolean(inventory), $event?.deel || null, $event?.detailniveau, $event?.beschrijvingsniveau)"
          @forget-inventory="forgetInventory($event?.deel || null)"
          :notices="notices.filter((n) => n.where === 'commons' || String(n.where || '').startsWith('ai-'))"
          @dismiss-notice="dismiss"
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
        <!-- The outcome of moving an object to the trash (with Undo), where it happened: above the list. -->
        <notice-list :notices="objectNotices" @dismiss="dismiss" />
        <!-- Minimum certainty: hides objects of the AI image detection it is less sure of (free,
             on what was found already). Hidden objects are not selected, so they are not saved. -->
        <div v-if="hasScores" class="cc-schuif cc-zekerheid">
          <label class="cc-schuif-kop" for="cc-zekerheid">{{ t("certainty.label") }}</label>
          <input
            id="cc-zekerheid"
            type="range"
            :min="scoreRange.min"
            :max="scoreRange.max"
            step="1"
            :value="shownCertainty"
            :aria-valuetext="t('certainty.value', { n: shownCertainty })"
            @input="minScore = Number($event.target.value) / 100"
            @change="deselectHidden"
          />
          <span class="cc-schuif-waarde">{{ t("certainty.value", { n: shownCertainty }) }}</span>
          <p class="cc-uitleg">{{ hiddenCount ? t("certainty.hidden", { n: hiddenCount }) : t("certainty.help") }}</p>
        </div>
        <object-list
          :mid="file.mid"
          :n="pageN"
          :objects="visibleObjects"
          :class-colors="kindColors"
          :empty-text="objectQuery.trim() && certainObjects.length ? t('objects.search_none') : ''"
          :focused="focusedId"
          :hovered="hoveredId"
          :new-ids="newIds"
          :result-ids="resultIds"
          @toggle="toggleSelected"
          @select="selectInList"
          @focus="focusObject"
          @open="openMagnifier"
          @hover="hoverObject"
          @trash="trashObject"
          @ungroup="ungroupObject"
          @rename="renameObject"
          @changed="replaceObject"
          @error="failInTab"
        >
          <!-- Search the list (wish Olaf), next to All · None · Invert: only objects whose name, search
               term, item, caption or description contain every word. A view only: nothing is unticked. -->
          <template #search>
            <span v-if="objects.length" class="cc-objecten-zoek-groep">
            <cdx-text-input
              v-model="objectQuery"
              class="cc-objecten-zoek"
              input-type="search"
              :start-icon="cdxIconSearch"
              clearable
              :placeholder="t('objects.search_placeholder')"
              :aria-label="t('objects.search_label')"
              :title="t('objects.search_help')"
            />
            <info-dialog
              :title="t('objects.search_info_title')"
              :label="t('objects.search_info_label')"
              :paragraphs="[1, 2, 3, 4].map((n) => t(`objects.search_info_${n}`))"
            />
            </span>
          </template>
          <template #under-header>
            <p v-if="objectQuery.trim()" class="cc-uitleg cc-objecten-zoek-uitkomst">{{ t("objects.search_result", { n: visibleObjects.length, total: certainObjects.length }) }}</p>
          </template>
        </object-list>
        <div class="cc-acties">
          <p class="cc-telling">{{ t("objects.count", { n: objects.length, selected: selectedCount }) }}</p>
          <!-- What you do with what you found: describe the ticked ones, merge duplicates,
               save. A button is disabled when there is nothing to do. -->
          <!-- What you do with what you found, in four tabs (wish Olaf, 6-11-2026; FO 7.4):
               each with the selection, everything visible, and (group, trash) per kind.
               A button is disabled when there is nothing to do. -->
          <!-- Two fold-outs, closed by default (wish Olaf): Bulk actions, and Save and export. -->
          <cdx-accordion v-model="actionsOpen.bulk" class="cc-acties-uitklap">
          <template #title>{{ t("bulk.title") }}</template>
          <div class="cc-acties-rij cc-bulk">
            <cdx-tabs v-model:active="bulkTab" :framed="true">
              <cdx-tab name="beschrijven" :label="t('bulk.tab_describe', { n: toDescribe })">
                <div class="cc-bulk-knoppen">
                  <cdx-button action="progressive" :disabled="busy || !toDescribe" :title="t('objects.describe_help')" @click="describeAll('selectie')">
                    {{ t("bulk.describe_selected", { n: toDescribe }) }} <span v-if="toDescribe" class="cc-kosten">{{ describeCost }}</span>
                  </cdx-button>
                  <cdx-button action="progressive" weight="quiet" :disabled="busy || !toDescribeAll" @click="describeAll('alle')">
                    {{ t("bulk.describe_all", { n: toDescribeAll }) }} <span v-if="toDescribeAll" class="cc-kosten">{{ describeAllCost }}</span>
                  </cdx-button>
                </div>
                <!-- Per kind, as in Group and Trash (wish Olaf, 7-11-2026): the visible objects of one
                     search term without a description; paid, so each link carries its amount. -->
                <p v-if="describableTerms.length" class="cc-groeperen">
                  {{ t("bulk.per_kind") }}
                  <template v-for="(item, i) in describableTerms" :key="item.term">
                    <template v-if="i"> · </template>
                    <button type="button" class="cc-link" :disabled="busy" :title="t('bulk.describe_kind_help')" @click="describeAll({ term: item.term })">
                      {{ t("panel.group_all", { term: item.name, n: item.n }) }} <span class="cc-kosten">{{ costFor(item.n) }}</span>
                    </button>
                  </template>
                </p>
                <p class="cc-uitleg">{{ describeNote }} {{ t("bulk.describe_help") }}</p>
              </cdx-tab>
              <cdx-tab name="ontdubbelen" :label="t('bulk.tab_dedupe')">
                <div class="cc-bulk-knoppen">
                  <cdx-button action="progressive" :disabled="busy || selectedCount < 2" @click="mergeDuplicates('selectie')">
                    {{ t("bulk.dedupe_selected", { n: selectedCount }) }}
                  </cdx-button>
                  <cdx-button action="progressive" weight="quiet" :disabled="busy || visibleObjects.length < 2" @click="mergeDuplicates('alle')">
                    {{ t("bulk.dedupe_all", { n: visibleObjects.length }) }}
                  </cdx-button>
                </div>
                <p class="cc-uitleg">{{ t("bulk.dedupe_help") }}</p>
              </cdx-tab>
              <cdx-tab name="groeperen" :label="t('bulk.tab_group', { n: selectedCount })">
                <div class="cc-bulk-knoppen">
                  <cdx-button action="progressive" :disabled="busy || selectedCount < 2" :title="t('objects.group_help')" @click="groupSelected">
                    {{ t("bulk.group_selected", { n: selectedCount }) }}
                  </cdx-button>
                  <cdx-button action="progressive" weight="quiet" :disabled="busy || visibleObjects.length < 2" @click="groupAllVisible">
                    {{ t("bulk.group_all", { n: visibleObjects.length }) }}
                  </cdx-button>
                </div>
                <p v-if="groupableTerms.length" class="cc-groeperen">
                  {{ t("bulk.per_kind") }}
                  <template v-for="(item, i) in groupableTerms" :key="item.term">
                    <template v-if="i"> · </template>
                    <button type="button" class="cc-link" :disabled="busy" :title="t('panel.group_all_help')" @click="groupTerm(item.term)">
                      {{ t("panel.group_all", { term: item.name, n: item.n }) }}
                    </button>
                  </template>
                </p>
                <p class="cc-uitleg">{{ t("panel.bulk_group_help") }}</p>
              </cdx-tab>
              <cdx-tab name="prullenbak" :label="t('bulk.tab_trash', { n: selectedCount })">
                <div class="cc-bulk-knoppen">
                  <cdx-button action="destructive" :disabled="busy || !selectedCount" @click="trashSelected">
                    <cdx-icon :icon="cdxIconTrash" size="small" /> {{ t("bulk.trash_selected", { n: selectedCount }) }}
                  </cdx-button>
                  <cdx-button action="destructive" weight="quiet" :disabled="busy || !visibleObjects.length" @click="trashAllVisible">
                    {{ t("bulk.trash_all", { n: visibleObjects.length }) }}
                  </cdx-button>
                </div>
                <p v-if="trashableTerms.length" class="cc-groeperen">
                  {{ t("bulk.per_kind") }}
                  <template v-for="(item, i) in trashableTerms" :key="item.term">
                    <template v-if="i"> · </template>
                    <button type="button" class="cc-link cc-link-weg" :disabled="busy" :title="t('panel.bulk_trash_item_help')" @click="trashTerm(item.term)">
                      {{ t("panel.group_all", { term: item.name, n: item.n }) }}
                    </button>
                  </template>
                </p>
                <p class="cc-uitleg">{{ t("panel.bulk_trash_help") }}</p>
              </cdx-tab>
            </cdx-tabs>
            <!-- The outcome of the last action, directly under the tabs that asked for it;
                 red when nothing could be done. -->
            <cdx-message v-if="actionResult && !busy" :type="actionResult.type" :allow-user-dismiss="true" :dismiss-button-label="t('actions.close')" class="cc-acties-melding" @user-dismissed="actionResult = null">{{ actionResult.text }}<ul v-if="actionResult.list?.length" class="cc-melding-lijst"><li v-for="line in actionResult.list" :key="line">{{ line }}</li></ul></cdx-message>
          </div>
          <busy-note v-if="busy && busyAt === 'objecten'" :message="t('busy.describe')" />
          </cdx-accordion>
          <cdx-accordion v-model="actionsOpen.save" class="cc-acties-uitklap">
          <template #title>{{ t("bulk.save_title") }}</template>
          <div class="cc-acties-opslaan">
          <cdx-button action="progressive" weight="primary" :disabled="!selectedCount || busy" @click="saveSelection">
            {{ t("actions.save", { n: selectedCount }) }}
          </cdx-button>
          <cdx-button action="progressive" :disabled="!savedCount" @click="downloadZip">
            <cdx-icon :icon="cdxIconDownload" /> {{ t("actions.zip") }}
          </cdx-button>
          <cdx-button action="progressive" :disabled="!savedCount" @click="toCommons">
            <cdx-icon :icon="cdxIconUpload" /> {{ t("actions.to_commons") }}
          </cdx-button>
          <!-- Retention is about saved cut-outs, so it goes with saving, not with the selection count. -->
          <p class="cc-bewaar-regel"><retention-info labelled /></p>
          </div>
          <notice-list :notices="noticesAt('opslaan')" @dismiss="dismiss" />
          </cdx-accordion>
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
      :start-tab="magnifierTab"
      @step="stepMagnifier"
      @changed="replaceObject"
      @trashed="trashObject($event)"
      @refine="refineMask"
      :notices="noticesAt('vergroter')"
      @dismiss-notice="dismiss"
    />

    <confirm-dialog />
    <!-- Describe in bulk: the AI settings made explicit before anything is sent (wish Olaf). -->
    <bulk-describe-dialog
      :open="bulkDescribe.open"
      :objects="bulkDescribe.objects"
      :paths="bulkDescribe.paths"
      :action="bulkDescribe.action"
      :cost-line="bulkDescribe.costLine"
      @answer="answerBulkDescribe"
    />
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from "vue";
import { CdxAccordion, CdxButton, CdxIcon, CdxMessage, CdxTab, CdxTabs, CdxTextInput } from "@wikimedia/codex";
import { cdxIconDownload, cdxIconPrevious, cdxIconSearch, cdxIconTrash, cdxIconUpload } from "@wikimedia/codex-icons";
import { API, del, errorText, filePath, get, objectPath, pagePath, patch, post, query } from "../api.js";
import { classColors } from "../class-colors.js";
import { writeAddress } from "../facets.js";
import { askConfirm, askConfirmValue } from "../confirm.js";
import { money, useT } from "../i18n.js";
import BulkDescribeDialog from "./BulkDescribeDialog.vue";
import BusyNote from "./BusyNote.vue";
import ColumnHeader from "./ColumnHeader.vue";
import ColumnSplitter from "./ColumnSplitter.vue";
import ColumnStrip from "./ColumnStrip.vue";
import ConfirmDialog from "./ConfirmDialog.vue";
import { addToHistory, appUrl, clearHistory, forgetFileInBrowser, numberedNames, objectName, readHistory, readStart, removeFromHistory, setAside } from "../state.js";
import ViewedPanel from "./ViewedPanel.vue";
import DetectionPanel from "./DetectionPanel.vue";
import FileBar from "./FileBar.vue";
import Magnifier from "./Magnifier.vue";
import NoticeList from "./NoticeList.vue";
import RetentionInfo from "./RetentionInfo.vue";
import InfoDialog from "./InfoDialog.vue";
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
// Per viewed image whether anything is kept for it (objects, trash, AI suggestions, a draft): ↻ is
// only active then (wish Olaf). Asked from the server (free); the open image again after each change.
const workKept = ref({});
async function checkWork(mid) {
  try {
    const kept = await get(`${filePath(mid)}/werk`);
    workKept.value = { ...workKept.value, [mid]: Boolean(kept.objecten || kept.prullenbak || kept.ai_suggesties || kept.concepten) };
  } catch {
    workKept.value = { ...workKept.value, [mid]: true }; // unknown: leave the button usable
  }
}
watch(
  () => visited.value.map((entry) => entry.mid).join(","),
  () => visited.value.filter((entry) => !(entry.mid in workKept.value)).forEach((entry) => checkWork(entry.mid)),
  { immediate: true }
);
let workTimer = null;
watch(
  () => [file.value?.mid, objects.value.length, Boolean(inventory.value)],
  ([mid]) => {
    clearTimeout(workTimer);
    if (mid) workTimer = setTimeout(() => checkWork(mid), 800);
  }
);
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

// Minimum certainty (0 to 0.95) for objects of the AI image detection; others (by hand,
// from Commons) have no score and always show. Remembered in this browser.
const CERTAINTY_KEY = "cc-min-zekerheid";
function readCertainty() {
  try {
    const value = Number(window.localStorage.getItem(CERTAINTY_KEY));
    return value >= 0 && value <= 0.95 ? value : 0;
  } catch {
    return 0;
  }
}
// The address wins (wish Olaf: zekerheid=57 in a shared link), else this browser's last choice.
const askedCertainty = Number(new URLSearchParams(window.location.search).get("zekerheid"));
const minScore = ref(askedCertainty > 0 && askedCertainty <= 95 ? askedCertainty / 100 : readCertainty());
watch(minScore, (value) => writeAddress({ zekerheid: value > 0 ? String(Math.round(value * 100)) : "" }));
watch(minScore, (value) => {
  try {
    window.localStorage.setItem(CERTAINTY_KEY, String(value));
  } catch {
    // Blocked storage: the value holds until the page is reloaded.
  }
});
const hasScores = computed(() => objects.value.some((o) => o.score != null));
// The slider runs from the lowest to the highest certainty found: below the lowest
// nothing would change, above the highest everything would be hidden.
const scoreRange = computed(() => {
  const scores = objects.value.filter((o) => o.score != null).map((o) => Math.round(o.score * 100));
  if (!scores.length) return { min: 0, max: 100 };
  const min = Math.min(...scores);
  return { min, max: Math.max(min + 1, Math.max(...scores)) };
});
const shownCertainty = computed(() => Math.min(scoreRange.value.max, Math.max(scoreRange.value.min, Math.round(minScore.value * 100))));
// Compared in whole percents, as the slider shows them; the threshold kept within the slider's range.
const isVisible = (o) => o.score == null || Math.round(o.score * 100) >= shownCertainty.value;
const certainObjects = computed(() => objects.value.filter(isVisible));
// A colour per kind of object (wish Olaf), from all objects of the page, so it stays put while
// the certainty slider or the search hides some.
const kindColors = computed(() => classColors(objects.value));
const hiddenCount = computed(() => objects.value.length - certainObjects.value.length);
// The search box above the list (wish Olaf): every word must occur in the object's texts,
// case-insensitive. It narrows what you see, in the list and in the image, and what "all"
// means in the bulk actions; unlike the certainty it unticks nothing.
const objectQuery = ref("");
// The search of the object list in the address (wish Olaf): q=…, for the image the address opened.
let askedQuery = new URLSearchParams(window.location.search).get("q");
const askedQueryMid = new URLSearchParams(window.location.search).get("mid");
watch(objectQuery, (q) => writeAddress({ q }));
function objectText(o) {
  const description = o.beschrijving && typeof o.beschrijving === "object" ? Object.values(o.beschrijving).filter((v) => typeof v === "string") : [];
  return [listNames.value[o.id], o.naam, o.label, o.label_nl, o.label_item, o.zoekterm, o.wikidata, o.bijschrift?.tekst, ...description]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}
const visibleObjects = computed(() => {
  const words = objectQuery.value.toLowerCase().split(/\s+/).filter(Boolean);
  if (!words.length) return certainObjects.value;
  return certainObjects.value.filter((o) => {
    const text = objectText(o);
    return words.every((word) => text.includes(word));
  });
});
// All, None and Invert in the list act on what the list shows; the selection outside a
// search stays as it was.
function selectInList(ids) {
  const shown = new Set(visibleObjects.value.map((o) => o.id));
  const kept = objects.value.filter((o) => o.status === "geselecteerd" && !shown.has(o.id)).map((o) => o.id);
  setSelection([...kept, ...ids]);
}
// What you do not see is not selected: saving or describing never takes a hidden object along.
function deselectHidden() {
  const selected = objects.value.filter((o) => o.status === "geselecteerd");
  const kept = selected.filter(isVisible);
  if (kept.length !== selected.length) setSelection(kept.map((o) => o.id));
}
// New detections may bring objects under the certainty, already selected.
watch(objects, () => {
  if (minScore.value > 0) deselectHidden();
});

const selectedCount = computed(() => objects.value.filter((o) => o.status === "geselecteerd").length);
const savedCount = computed(() => objects.value.filter((o) => o.opgeslagen).length);
const magnified = computed(() => objects.value.find((o) => o.id === magnifiedId.value) || null);

// -- Notices --------------------------------------------------------------------------

let noticeId = 0;
// A notice shows at the top of the page, or with where: "objecten" in the objects column,
// where the action it reports on took place.
function notify(type, text, extra = {}) {
  notices.value = [...notices.value.slice(-3), { id: ++noticeId, type, text, ...extra }];
}
// Only what is about the whole file goes on top; the outcome of an action shows near the button that
// asked for it (wish Olaf), with `where`: commons, ai-beschrijving, ai-zoektermen, ai-alles,
// vergroter, opslaan, objecten.
const topNotices = computed(() => notices.value.filter((n) => !n.where));
const objectNotices = computed(() => notices.value.filter((n) => n.where === "objecten"));
const noticesAt = (where) => notices.value.filter((n) => n.where === where);
function dismiss(id) {
  notices.value = notices.value.filter((n) => n.id !== id);
}
function fail(error, where = undefined) {
  notify("error", errorText(t, error), where ? { where } : {});
}
// An error of a bulk action: in the tab, under the button that asked for it (wish Olaf),
// not at the top of the page.
function failInTab(error) {
  actionResult.value = { type: "error", text: errorText(t, error) };
}

// -- Confirming paid actions (6.4): only in live mode, with the amount --------------------

// `action`: what will happen, in one or two sentences, above the cost (wish Olaf).
async function confirmCost(calls, usd, action = "", objects = []) {
  if (!props.config.betaald || !calls) return true;
  const cost = t("confirm.cost", { n: calls, amount: money(usd, props.config.taal) });
  // `objects`: what the question is about, as a list with small cut-outs (like grouping).
  return askConfirm(action ? `${action}\n\n${cost}` : cost, { title: t("confirm.cost_title"), objects });
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

// Read the open file from Commons again (the app keeps what it read for a day), e.g.
// after adding a caption or depicts there. Free; the page and its objects stay.
async function readAgain() {
  if (!file.value) return;
  busy.value = true;
  try {
    file.value = await post(`${API}/bestand/${file.value.mid}/opnieuw-lezen`, {});
    await goToPage(pageN.value);
    notify("success", t("panel.commons_read_again_done"), { where: "commons" });
  } catch (error) {
    fail(error, "commons");
  } finally {
    busy.value = false;
  }
}

// Open a file from the list Bekeken within the app (no page reload), on the page that was open.
function openFromHistory(entry) {
  if (loadingFile.value) return;
  start.mid = entry.mid;
  start.pagina = String(entry.pagina || 1);
  openFile(entry.mid);
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
    // Only the parameters of the file and page change; the choices on the page (q, zekerheid, maskers, kaders, uselang) stay.
    writeAddress({ mid: file.value.mid, pagina: n > 1 ? String(n) : "", object: "", vergroten: "", url: "", titel: "" });
    visited.value = addToHistory({ mid: file.value.mid, naam: file.value.naam, pagina: n, paginas: file.value.paginas });
    const asked = `${file.value.mid}/${n}`;
    get(`${pagePath(file.value.mid, n)}/inventaris`)
      .then((plan) => {
        if (asked === `${file.value?.mid}/${pageN.value}`) inventory.value = plan.inventaris; // not for a page left meanwhile
      })
      .catch(() => {});
    if (start.object) {
      const id = start.object;
      const magnify = start.vergroten; // from the eye on the Objects page
      start.object = "";
      start.vergroten = "";
      setTimeout(() => {
        focusObject(id);
        if (magnify && objects.value.some((o) => o.id === id)) openMagnifier(id, magnify === "aangevuld" ? "aangevuld" : "");
      }, 300);
    }
  } catch (error) {
    fail(error);
  }
}

function replaceObjects(list, fresh = []) {
  objects.value = list;
  newIds.value = fresh;
}

// Start an image over (wish Olaf): first say what goes, then remove it on the server and forget what
// this browser keeps for it. The open image is loaded anew, so every panel starts empty.
async function startOver(entry) {
  const base = `${filePath(entry.mid)}/werk`;
  let kept;
  try {
    kept = await get(base);
  } catch (error) {
    failInTab(error);
    return;
  }
  // What goes, as a list under a heading (wish Olaf); what stays below it.
  // Each with a link to where you see it (wish Olaf), in a new tab so the question stays open.
  const mid = encodeURIComponent(entry.mid);
  const links = {
    objects: { href: `/objecten?mid=${mid}`, label: t("history.start_over_objects", { n: kept.objecten }) },
    trash: { href: `/objecten?tab=prullenbak&mid=${mid}`, label: t("history.start_over_trash", { n: kept.prullenbak }) },
    saved: { href: `/objecten?mid=${mid}&opgeslagen=1`, label: t("history.start_over_saved", { n: kept.opgeslagen }) },
    ai: { href: `${appUrl(entry.mid, entry.pagina || 1)}#ai-suggesties`, label: t("history.start_over_ai") },
  };
  const linked = (name, n) => (n ? `{${name}}` : links[name].label); // nothing to see: no link
  // Two groups (wish Olaf): what goes from the image itself, and from its objects and cut-outs.
  const fromImage = [kept.ai_suggesties && "{ai}", kept.concepten && t("history.start_over_draft"), t("history.start_over_buttons")].filter(Boolean);
  const fromObjects = [
    // With what was changed on them, so it is clear everything about the objects goes.
    kept.objecten ? `${linked("objects", kept.objecten)} ${t("history.start_over_objects_with")}` : linked("objects", kept.objecten),
    linked("trash", kept.prullenbak),
    linked("saved", kept.opgeslagen),
  ];
  const group = (heading, lines) => [`**${heading}**`, ...lines.map((line) => `- ${line}`)].join("\n");
  const text = [
    t("history.start_over_confirm", { name: entry.naam || entry.mid }),
    group(t("history.start_over_from_image"), fromImage),
    group(t("history.start_over_from_objects"), fromObjects),
    t("history.start_over_keeps"),
  ].join("\n\n");
  // Keep the earlier AI answers (free when asked again) or ask the AI anew (wish Olaf).
  const choices = [
    { value: "houden", label: t("history.start_over_keep_ai"), help: t("history.start_over_keep_ai_help") },
    { value: "opnieuw", label: t("history.start_over_fresh_ai"), help: t("history.start_over_fresh_ai_help") },
  ];
  // With a thumbnail of the image, so you see which one goes (wish Olaf).
  // Only the picture: the sentence below names the file (wish Olaf).
  const image = [{ image: `${filePath(entry.mid)}/pagina/${entry.pagina || 1}/afbeelding?w=480`, name: "" }];
  const answer = await askConfirmValue(text, { title: t("history.start_over"), go: t("history.start_over"), destructive: true, links, choices, objects: image, objectsFirst: true });
  if (!answer.ok) return;
  try {
    await del(answer.choice === "opnieuw" ? `${base}?ai=opnieuw` : base);
  } catch (error) {
    failInTab(error);
    return;
  }
  forgetFileInBrowser(entry.mid);
  workKept.value = { ...workKept.value, [entry.mid]: false };
  if (file.value?.mid === entry.mid) window.location.reload();
}

// Your own name for an object (from the list); "" goes back to the automatic name.
async function renameObject(id, name) {
  try {
    replaceObject(await patch(objectPath(file.value.mid, pageN.value, id), { naam: name || null }));
  } catch (error) {
    fail(error);
  }
}

function replaceObject(changed) {
  objects.value = objects.value.map((o) => (o.id === changed.id ? changed : o));
}

// -- Detection (7) ----------------------------------------------------------------------

// The outcome of the last detection, for the panel ({found, excluded, prompt, modus}).
const lastResult = ref(null);
const resultIds = computed(() => lastResult.value?.ids || []);

async function detect(request) {
  lastResult.value = null;
  const base = pagePath(file.value.mid, pageN.value);
  busy.value = true;
  try {
    if (request.modus !== "commons") {
      const { items, ...asked } = request; // items (Q-ids) do not change the cost
      const estimate = await get(`${base}/detecties/raming${query(asked)}`);
      // The terms as a list (scrolls when long, wish Olaf): one per line.
      const termList = String(request.prompt || "").split(",").map((term) => term.trim()).filter(Boolean).map((term) => `- ${term}`).join("\n");
      const action = request.modus === "prompt" ? t("confirm.action_detect", { terms: termList }) : t("confirm.action_detect_all");
      if (!(await confirmCost(estimate.aanroepen.betaald, estimate.aanroepen.betaald * props.config.sam_usd, action))) return;
    }
    const result = await post(`${base}/detecties`, request);
    replaceObjects(result.objecten, result.nieuw);
    // The outcome is shown in the panel, under the button that asked for it.
    const fresh = result.objecten.filter((o) => result.nieuw.includes(o.id));
    const excluded = fresh.filter((o) => o.status === "uitgesloten").length;
    // Found, but not shown: below the minimum certainty (hidden in the list and the image).
    const hidden = fresh.filter((o) => o.status !== "uitgesloten" && !isVisible(o)).length;
    // Found, but not as an object of its own: merged, in a group, or in the trash.
    const elders = result.elders || {};
    const holders = [...new Set([...(elders.samengevoegd || []), ...(elders.in_groep || [])].map((e) => e.met))];
    lastResult.value = {
      // The objects this message is about: what was found, and where the rest went (green in the list).
      ids: [...fresh.map((o) => o.id), ...holders],
      found: fresh.length - excluded - hidden,
      excluded,
      hidden,
      merged: (elders.samengevoegd || []).length,
      inGroup: (elders.in_groep || []).length,
      inTrash: (elders.in_prullenbak || []).length,
      holders: holders.map((id) => listNames.value[id] || objectName(result.objecten.find((o) => o.id === id) || {}, props.config.taal, t)).filter(Boolean),
      prompt: request.prompt || "",
      modus: request.modus,
      at: Date.now(),
    };
  } catch (error) {
    fail(error);
  } finally {
    busy.value = false;
  }
}

// Remove the page overview, or one part of it ("beschrijving" or "zoektermen"), after a confirmation.
async function forgetInventory(part = null) {
  const key = part || "alles";
  if (!(await askConfirm(t(`panel.part_forget_confirm_${key}`), { title: t(`panel.part_forget_title_${key}`), go: t(key === "zoektermen" ? "panel.part_forget_zoektermen_button" : key === "beschrijving" ? "panel.part_forget_beschrijving_button" : "panel.part_forget"), destructive: true }))) return;
  try {
    const result = await del(`${pagePath(file.value.mid, pageN.value)}/inventaris${part ? `/${part}` : ""}`);
    inventory.value = result.inventaris;
    notify("success", t(`panel.part_forgotten_${key}`), { where: `ai-${key}` });
  } catch (error) {
    fail(error, `ai-${key}`);
  }
}

// The page overview. With `again` the model is really asked anew (paid);
// otherwise a stored answer for this page and model comes from the cache, free.
// With `part` ("beschrijving" or "zoektermen") only that part is asked anew.
async function askInventory(again = false, part = null, detail = undefined, descLevel = undefined) {
  const base = pagePath(file.value.mid, pageN.value);
  busy.value = true;
  try {
    const plan = await get(`${base}/inventaris`);
    const action =
      part === "beschrijving"
        ? t("confirm.action_page_description", { length: t(`descdetail.${descLevel || "normaal"}`) })
        : part === "zoektermen"
          ? t("confirm.action_page_terms", { level: t(`detail.${detail || "normaal"}`) })
          : t("confirm.action_page", { level: t(`detail.${detail || "normaal"}`) });
    if (!(await confirmCost(plan.betaald ? 1 : 0, plan.kosten_schatting_usd, action))) return;
    const level = {
      ...(detail && part !== "beschrijving" ? { detailniveau: detail } : {}),
      ...(descLevel && part !== "zoektermen" ? { beschrijvingsniveau: descLevel } : {}),
    };
    const result = await post(part ? `${base}/inventaris/${part}` : `${base}/inventaris`, part ? level : { opnieuw: again, ...level });
    inventory.value = result.inventaris;
  } catch (error) {
    fail(error);
  } finally {
    busy.value = false;
  }
}

// -- Groups (7.4): many small objects as one; free ------------------------------------------

// How an object shows in a confirmation: a small cut-out and its name in the list.
function shownObject(obj, n = pageN.value) {
  return { image: `${objectPath(file.value.mid, n, obj.id)}/uitsnede.jpg?w=96`, name: listNames.value[obj.id] || objectName(obj, props.config.taal, t) };
}

// The name a group gets without one of its own, as the server makes it.
function defaultGroupName(members) {
  const kinds = [...new Set(members.map((o) => (o.zoekterm || o.label || "").toLowerCase()))];
  const kind = kinds.length === 1 ? members[0] : null;
  const name = kind ? (props.config.taal === "en" ? kind.zoekterm || kind.label : kind.label_nl || kind.zoekterm || kind.label) : "";
  return name ? t("objects.group_default", { kind: name, n: members.length }) : t("objects.group_default_mixed", { n: members.length });
}

// First a confirmation: which objects, and an optional name (the default in grey). Null when cancelled.
async function makeGroup(members, body) {
  const placeholder = defaultGroupName(members);
  const answer = await askConfirmValue(t("objects.group_confirm", { n: members.length }), {
    title: t("objects.group_title"),
    go: t("objects.group_go"),
    objects: members.map((o) => shownObject(o)),
    input: { label: t("objects.group_name"), placeholder, help: t("objects.group_name_help") },
  });
  if (!answer.ok) return null;
  const result = await post(`${pagePath(file.value.mid, pageN.value)}/groepen`, { ...body, ...(answer.value ? { naam: answer.value } : {}) });
  objects.value = result.objecten;
  return { n: result.object.groep.aantal, name: objectName(result.object, props.config.taal, t) };
}

// Search terms with two or more loose objects (not groups), to group per kind in one click;
// named as in the list (Dutch name when there is one).
// The visible objects per search term (no groups), for grouping and the trash in bulk.
const termKinds = computed(() => {
  const terms = new Map();
  for (const o of visibleObjects.value) {
    if (o.bron === "groep" || !o.zoekterm) continue;
    const item = terms.get(o.zoekterm) || { term: o.zoekterm, name: props.config.taal === "en" ? o.zoekterm : o.label_nl || o.zoekterm, n: 0 };
    item.n += 1;
    terms.set(o.zoekterm, item);
  }
  return [...terms.values()];
});
const trashableTerms = computed(() => termKinds.value);
// The tab of the bulk actions: always Beschrijven to start with, also on another file (wish Olaf).
const bulkTab = ref("beschrijven");
// The fold-outs Bulk actions and Save and export: closed by default (wish Olaf).
const actionsOpen = reactive({ bulk: false, save: false });
watch(() => [file.value?.mid, pageN.value], () => {
  bulkTab.value = "beschrijven";
  objectQuery.value = "";
  if (askedQuery && file.value?.mid === askedQueryMid) objectQuery.value = askedQuery;
  askedQuery = null;
});

// "All hats" to the trash in one go: always a confirmation listing them; one notice with
// Undo for all. Only the visible ones (the minimum certainty hides the others).
async function trashTerm(term) {
  const members = visibleObjects.value.filter((o) => o.bron !== "groep" && o.zoekterm === term);
  const name = termKinds.value.find((item) => item.term === term)?.name || term;
  await trashMany(members, name, t("panel.bulk_trash_title", { term: name }));
}
const trashSelected = () => trashMany(objects.value.filter((o) => o.status === "geselecteerd"), t("bulk.the_selection"), t("bulk.trash_selected_title"));
const trashAllVisible = () => trashMany(visibleObjects.value, t("bulk.everything"), t("bulk.trash_all_title"));

async function trashMany(members, name, title) {
  if (!members.length) return;
  const fromCommons = members.some((o) => o.bron === "commons");
  const links = { ...objectsLinks(), ...(fromCommons ? { commons: { href: `https://commons.wikimedia.org/wiki/${encodeURIComponent((file.value.titel || "").replace(/ /g, "_"))}#P180`, label: t("objects.trash_commons_link") } } : {}) };
  const text = [t(members.length === 1 ? "panel.bulk_trash_confirm_one" : "panel.bulk_trash_confirm", { n: members.length, term: name }), fromCommons ? t("objects.trash_confirm_commons") : ""].filter(Boolean).join("\n\n");
  if (!(await askConfirm(text, { title, go: t("panel.bulk_trash_go", { n: members.length }), destructive: true, links, objects: members.map((o) => shownObject(o)) }))) return;
  const n = pageN.value;
  const mid = file.value.mid;
  const ids = members.map((o) => o.id);
  busy.value = true;
  try {
    let result = null;
    for (const id of ids) result = await del(objectPath(mid, n, id));
    if (magnifierOpen.value && ids.includes(magnifiedId.value)) magnifierOpen.value = false;
    if (result) objects.value = result.objecten;
    refreshTrashTerms(n);
    notify("notice", t(ids.length === 1 ? "panel.bulk_trashed_one" : "panel.bulk_trashed", { n: ids.length, term: name }), {
      where: "objecten",
      actions: [{ label: `↶ ${t("magnifier.undo")}`, run: () => restoreMany(ids, n, mid, name) }],
      link: { href: "/objecten?tab=prullenbak", label: t("objects.to_trash") },
    });
  } catch (error) {
    failInTab(error);
    const data = await get(pagePath(mid, n)).catch(() => null); // some may have gone: show what is there
    if (data && mid === file.value?.mid && n === pageN.value) objects.value = data.objecten;
  } finally {
    busy.value = false;
  }
}

async function restoreMany(ids, n, mid, name) {
  try {
    for (const id of ids) await patch(objectPath(mid, n, id), { prullenbak: false });
    if (mid === file.value?.mid && n === pageN.value) {
      const data = await get(pagePath(mid, n));
      objects.value = data.objecten;
      trashTerms.value = data.prullenbak_termen || {};
    }
    notify("success", t(ids.length === 1 ? "panel.bulk_restored_one" : "panel.bulk_restored", { n: ids.length, term: name }), { where: "objecten" });
  } catch (error) {
    fail(error);
  }
}

const groupableTerms = computed(() => {
  const terms = new Map();
  for (const o of visibleObjects.value) {
    if (o.bron === "groep" || !o.zoekterm) continue;
    const item = terms.get(o.zoekterm) || { term: o.zoekterm, name: props.config.taal === "en" ? o.zoekterm : o.label_nl || o.zoekterm, n: 0 };
    item.n += 1;
    terms.set(o.zoekterm, item);
  }
  return [...terms.values()].filter((item) => item.n >= 2);
});

// "Groeperen (n)": the selected objects; the outcome under the buttons.
async function groupSelected() {
  actionResult.value = null;
  try {
    const members = objects.value.filter((o) => o.status === "geselecteerd");
    // The confirmation said what happens; the group shows in the list (no extra notice).
    await makeGroup(members, { objecten: members.map((o) => o.id) });
  } catch (error) {
    failInTab(error);
  }
}

// "Group all": everything visible as one group, after the same confirmation.
async function groupAllVisible() {
  actionResult.value = null;
  try {
    const members = visibleObjects.value;
    await makeGroup(members, { objecten: members.map((o) => o.id) });
  } catch (error) {
    failInTab(error);
  }
}

// "Groepeer alle …" at a search term, after the same confirmation.
async function groupTerm(term) {
  try {
    const members = objects.value.filter((o) => o.bron !== "groep" && o.zoekterm === term);
    await makeGroup(members, { zoekterm: term });
  } catch (error) {
    failInTab(error);
  }
}

// "Groep opheffen": first a confirmation listing the objects that come back; a caption,
// description or saved cut-out of the group is lost, and then the question says so.
async function ungroupObject(id) {
  const group = objects.value.find((o) => o.id === id);
  const members = group?.groep?.leden || [];
  const loses = group && (group.bijschrift?.tekst || group.beschrijving || group.opgeslagen);
  const text = t("objects.ungroup_confirm_list", { n: members.length }) + (loses ? `\n\n${t("objects.ungroup_confirm")}` : "");
  const shown = members.map((m) => ({ image: `${objectPath(file.value.mid, pageN.value, m.id)}/uitsnede.jpg?w=96`, name: objectName(m, props.config.taal, t) })); // the same name as in the list
  if (!(await askConfirm(text, { title: t("objects.ungroup"), go: t("objects.ungroup"), destructive: Boolean(loses), objects: shown }))) return;
  try {
    const result = await del(`${pagePath(file.value.mid, pageN.value)}/groepen/${id}`);
    objects.value = result.objecten;
  } catch (error) {
    fail(error);
  }
}

async function mergeDuplicates(scope = "alle") {
  actionResult.value = null;
  try {
    const among = scope === "selectie" ? objects.value.filter((o) => o.status === "geselecteerd") : visibleObjects.value;
    const result = await post(`${pagePath(file.value.mid, pageN.value)}/samenvoegingen`, { objecten: among.map((o) => o.id) });
    replaceObjects(result.objecten);
    // Which object went into which (wish Olaf): "suitcase → cardboard box".
    const pairs = (result.paren || []).map((pair) => t("detect.merged_pair", { gone: objectName(pair.weg, props.config.taal, t), kept: objectName(pair.in, props.config.taal, t) }));
    actionResult.value = result.samengevoegd
      ? { type: "success", text: t("detect.merged_list", { n: result.samengevoegd }), list: pairs }
      : { type: "error", text: t("objects.merged_none") };
  } catch (error) {
    failInTab(error);
  }
}

// Ticked objects without a description: what "Describe selected objects" describes, and its price.
const toDescribe = computed(() => objects.value.filter((o) => o.status === "geselecteerd" && !o.beschrijving).length);
const describeCost = computed(() => (props.config.betaald ? `(${money(props.config.muse.beschrijving_usd * toDescribe.value, props.config.taal)})` : t("panel.free")));
// Everything visible without a description: "Describe all".
const toDescribeAll = computed(() => visibleObjects.value.filter((o) => !o.beschrijving).length);
const describeAllCost = computed(() => costFor(toDescribeAll.value));
// The price of describing n objects, as on the buttons.
function costFor(n) {
  return props.config.betaald ? `(${money(props.config.muse.beschrijving_usd * n, props.config.taal)})` : t("panel.free");
}
// Per kind (wish Olaf): the visible objects of a search term without a description (no groups,
// as in Group and Trash), named as in the list.
const describableTerms = computed(() => {
  const terms = new Map();
  for (const o of visibleObjects.value) {
    if (o.bron === "groep" || !o.zoekterm || o.beschrijving) continue;
    const item = terms.get(o.zoekterm) || { term: o.zoekterm, name: props.config.taal === "en" ? o.zoekterm : o.label_nl || o.zoekterm, n: 0 };
    item.n += 1;
    terms.set(o.zoekterm, item);
  }
  return [...terms.values()];
});
// The line under the describe button: what it will do with the ticked objects.
const describeNote = computed(() => {
  const selected = selectedCount.value;
  const todo = toDescribe.value;
  if (!selected) return t("objects.describe_note_none");
  if (!todo) return t("objects.describe_note_all_done", { selected });
  if (todo < selected) return t("objects.describe_note_some", { todo, selected, done: selected - todo });
  return t("objects.describe_note_all", { todo });
});
// Where the waiting feedback goes for actions in the objects column.
const busyAt = ref(null);
// The outcome of the last describe or merge, shown under those buttons.
const actionResult = ref(null);
watch(() => [file.value?.mid, pageN.value], () => { actionResult.value = null; });

// scope: "selectie", "alle" (everything visible) or { term } (the visible objects of one kind).
async function describeAll(scope = "selectie") {
  busyAt.value = "objecten";
  actionResult.value = null;
  const kind = scope && typeof scope === "object" ? scope.term : null;
  const among = kind
    ? visibleObjects.value.filter((o) => o.bron !== "groep" && o.zoekterm === kind)
    : scope === "alle"
      ? visibleObjects.value
      : objects.value.filter((o) => o.status === "geselecteerd");
  const chosen = among.filter((o) => !o.beschrijving);
  if (!chosen.length) {
    actionResult.value = { type: "error", text: t("describe.nothing_to_do") };
    return;
  }
  const usd = props.config.muse.beschrijving_usd * chosen.length;
  // The objects as a list with small cut-outs, as when grouping, and the AI settings (wish Olaf).
  const kindName = kind ? describableTerms.value.find((item) => item.term === kind)?.name || kind : "";
  const action = kind
    ? t("confirm.action_describe_kind", { n: chosen.length, term: kindName })
    : t(scope === "alle" ? "confirm.action_describe_visible" : "confirm.action_describe_all", { n: chosen.length });
  const settings = await askBulkDescribe({
    objects: chosen.map((o) => ({ ...shownObject(o), ownPrompt: Boolean(o.prompt_eigen) })),
    paths: chosen.map((o) => objectPath(file.value.mid, pageN.value, o.id)),
    action,
    costLine: props.config.betaald ? t("confirm.cost", { n: chosen.length, amount: money(usd, props.config.taal) }) : t("bulkdescribe.free"),
  });
  if (!settings) {
    busyAt.value = null;
    return;
  }
  busy.value = true;
  try {
    // Every object with its own settings from the dialog (wish Olaf).
    for (const [i, obj] of chosen.entries()) {
      const result = await post(`${objectPath(file.value.mid, pageN.value, obj.id)}/beschrijving`, settings[i]);
      replaceObject(result.object);
    }
    actionResult.value = { type: "success", text: t("describe.done", { n: chosen.length }) };
  } catch (error) {
    failInTab(error);
  } finally {
    busy.value = false;
    busyAt.value = null;
  }
}

// The dialog of Describe in bulk: resolves with the settings per object, or null when cancelled.
const bulkDescribe = reactive({ open: false, objects: [], paths: [], action: "", costLine: "" });
let bulkDescribeAnswer = null;
function askBulkDescribe(question) {
  Object.assign(bulkDescribe, question, { open: true });
  return new Promise((resolve) => (bulkDescribeAnswer = resolve));
}
function answerBulkDescribe(settings) {
  bulkDescribe.open = false;
  bulkDescribeAnswer?.(settings);
  bulkDescribeAnswer = null;
}

async function onPoint({ x, y }) {
  if (!pointMode.value) return;
  lastResult.value = null;
  // Always the price first: only a click on the shape of a known object is free,
  // and the shapes are on the server (a click in a box beside its shape is a new search).
  if (!(await confirmCost(1, props.config.sam_usd, t("confirm.action_point")))) return;
  busy.value = true;
  try {
    const result = await post(`${pagePath(file.value.mid, pageN.value)}/detecties`, { punt: { x, y } });
    // The outcome in the panel, under "Aanwijzen of tekenen": new, already known, or nothing.
    if (!result.object) {
      lastResult.value = { section: "point", modus: "punt", outcome: "niets", at: Date.now() };
      return;
    }
    if (result.nieuw) objects.value = [...objects.value.filter((o) => o.id !== result.object.id), result.object];
    newIds.value = [result.object.id];
    focusedId.value = result.object.id;
    lastResult.value = { section: "point", modus: "punt", outcome: result.nieuw ? "nieuw" : "bekend", name: listNames.value[result.object.id] || objectName(result.object, props.config.taal, t), at: Date.now() };
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
    lastResult.value = { section: "point", modus: "rechthoek", outcome: "nieuw", name: listNames.value[result.object.id] || objectName(result.object, props.config.taal, t), at: Date.now() };
  } catch (error) {
    fail(error);
  }
}

async function refineMask(obj) {
  if (!(await confirmCost(1, props.config.sam_usd, t("confirm.action_mask", { name: listNames.value[obj.id] || objectName(obj, props.config.taal, t) })))) return;
  try {
    const result = await post(`${pagePath(file.value.mid, pageN.value)}/detecties`, { masker_voor: obj.id });
    replaceObject(result.object);
    notify("success", t("detect.mask_done"), { where: "vergroter" });
  } catch (error) {
    fail(error, "vergroter");
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
// Remove only the shape SAM gave a rectangle: the object stays, with its own rectangle
// (for a region: the one on Commons). Free; nothing changes on Commons.
async function removeShape(id) {
  try {
    const result = await del(`${objectPath(file.value.mid, pageN.value, id)}/vorm`);
    objects.value = objects.value.map((o) => (o.id === id ? result.object : o));
    notify("success", t("objects.shape_removed", { name: objectName(result.object, props.config.taal, t) }), { where: "objecten" });
  } catch (error) {
    fail(error, "objecten");
  }
}

async function trashObject(id) {
  const target = objects.value.find((o) => o.id === id);
  // A region from Commons, or a rectangle with a shape from SAM: say what the trash does
  // and does not do, and offer to remove only SAM's shape (wish Olaf, 6-11-2026).
  const fromCommons = target?.bron === "commons";
  const shaped = Boolean(target?.box_regio && target?.masker);
  const links = { ...objectsLinks(), ...(fromCommons ? { commons: { href: `https://commons.wikimedia.org/wiki/${encodeURIComponent((file.value.titel || "").replace(/ /g, "_"))}#P180`, label: t("objects.trash_commons_link") } } : {}) };
  const choices = shaped
    ? [
        { value: "vorm", label: t("objects.trash_choice_shape"), help: t(fromCommons ? "objects.trash_choice_shape_help_commons" : "objects.trash_choice_shape_help"), go: t("objects.trash_shape_go"), destructive: false },
        { value: "prullenbak", label: t("objects.trash_choice_object"), help: t("objects.trash_choice_object_help"), go: t("objects.trash"), destructive: true },
      ]
    : [];
  const text = [t("objects.trash_confirm"), fromCommons ? t("objects.trash_confirm_commons") : ""].filter(Boolean).join("\n\n");
  const answer = await askConfirmValue(shaped ? t(fromCommons ? "objects.trash_shape_intro_commons" : "objects.trash_shape_intro") + (fromCommons ? "\n\n" + t("objects.trash_confirm_commons") : "") : text, {
    title: shaped ? t("objects.trash_shape_title") : t("objects.trash"),
    go: t("objects.trash"),
    destructive: true,
    links,
    choices,
    // Always asked (wish Olaf), with the object itself in the question; no "don't ask again".
    objects: target ? [shownObject(target)] : [],
  });
  if (!answer.ok) return;
  if (answer.choice === "vorm") {
    await removeShape(id);
    return;
  }
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
      where: "objecten",
      object: shown,
      actions: [{ label: `↶ ${t("magnifier.undo")}`, run: () => restoreObject(id, n, mid, shown) }],
      link: { href: "/objecten?tab=prullenbak", label: t("objects.to_trash") },
    });
  } catch (error) {
    fail(error);
  }
}

async function restoreObject(id, n, mid = file.value.mid, shown = null) {
  try {
    await patch(objectPath(mid, n, id), { prullenbak: false });
    if (mid === file.value?.mid && n === pageN.value) {
      const data = await get(pagePath(file.value.mid, n));
      objects.value = data.objecten;
      trashTerms.value = data.prullenbak_termen || {};
    }
    notify("success", t("objects.restored"), { where: "objecten", object: shown }); // with the object: which one came back
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

// `tab`: the tab to open on ("aangevuld" from the eye on the Objects page); else the cut-out.
const magnifierTab = ref("");
function openMagnifier(id, tab = "") {
  magnifiedId.value = id;
  magnifierTab.value = tab;
  magnifierOpen.value = true;
}

// Previous and next in the magnifier: the order of the list "Gevonden objecten (uitsneden)".
const listNames = computed(() => numberedNames(objects.value, props.config.taal, t));
const listOrder = computed(() => Object.keys(listNames.value).filter((id) => visibleObjects.value.some((o) => o.id === id)));
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
    notify("success", t("save.done", { n: result.opgeslagen.length }), { where: "opslaan" });
  } catch (error) {
    fail(error, "opslaan");
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
