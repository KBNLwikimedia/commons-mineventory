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

    <section v-if="!file && !loadingFile && (visited.length || noticesAt('bekeken').length)" class="cc-start-geschiedenis">
      <h2>{{ t("history.title") }}</h2>
      <notice-list :notices="noticesAt('bekeken')" @dismiss="dismiss" />
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
          <!-- What removing from the list or starting over did, with Undo where it can (wish Olaf). -->
          <notice-list :notices="noticesAt('bekeken')" @dismiss="dismiss" />
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
          :waiting="maskWait"
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
          :busy-elsewhere="busyAt === 'objecten'"
          :inventory="inventory"
          :page-usd="prices?.page ?? null"
          :objects="objects"
          :trash-terms="trashTerms"
          :last-result="lastResult"
          @dismiss-result="lastResult = null"
          @undo-result="undoDrawn"
          @restore-trash="restoreFound"
          @read-again="readAgain"
          :point-mode="pointMode"
          @detect="detect"
          @inventory="askInventory(Boolean(inventory), $event?.deel || null, $event?.detailniveau, $event?.beschrijvingsniveau)"
          @forget-inventory="forgetInventory($event?.deel || null)"
          :notices="notices.filter((n) => n.where === 'commons' || String(n.where || '').startsWith('ai-'))"
          @dismiss-notice="dismiss"
          @inventory-changed="inventory = $event"
          :draw-mode="drawMode"
          :hints="hints"
          @hint="hints[$event.kind] = $event.text"
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
          <!-- What this section is for, in one or two sentences (wish Olaf). -->
          <p class="cc-uitleg cc-sectie-intro">{{ t("bulk.intro") }}</p>
          <!-- Every outcome of the four bulk actions in one fixed place, above the tabs, so it is always in
               view (wish Olaf 13-11-2026): describing, merging, grouping and the trash (with Undo), the
               same kind of message, one at a time, until you close it or a newer one replaces it. -->
          <notice-list :notices="noticesAt('bulk')" @dismiss="dismiss" />
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
                <kind-links :items="describableTerms" :disabled="busy" :help="t('bulk.describe_kind_help')" :price="costFor" @pick="describeAll({ term: $event })" />
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
                <kind-links :items="groupableTerms" :disabled="busy" :help="t('panel.group_all_help')" @pick="groupTerm" />
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
                <kind-links :items="termKinds" :disabled="busy" :help="t('panel.bulk_trash_item_help')" remove @pick="trashTerm" />
                <p class="cc-uitleg">{{ t("panel.bulk_trash_help") }}</p>
              </cdx-tab>
            </cdx-tabs>
          </div>
          <busy-note v-if="busy && busyAt === 'objecten'" :message="maskWait || t('busy.describe')" />
          </cdx-accordion>
          <cdx-accordion v-model="actionsOpen.save" class="cc-acties-uitklap">
          <template #title>{{ t("bulk.save_title") }}</template>
          <p class="cc-uitleg cc-sectie-intro">{{ t("bulk.save_intro") }}</p>
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
      :refine-busy="busy"
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
      :unit-usd="bulkDescribe.unitUsd"
      :paid="bulkDescribe.paid"
      :language="bulkDescribe.language"
      @answer="answerBulkDescribe"
    />
    <!-- Locating: what is searched, the cost, and (folded away) the search words (wish Olaf). -->
    <locate-dialog
      :open="locate.open"
      :path="locate.path"
      :prompt="locate.prompt"
      :ask-word="locate.askWord"
      :paid="config.betaald"
      :sam-usd="config.sam_usd"
      :language="config.taal"
      @answer="answerLocate"
    />
    <!-- Describe the whole image anew: what happens, the cost, and (folded away) the prompt (wish Olaf). -->
    <page-describe-dialog
      :open="pageDescribe.open"
      :path="pageDescribe.path"
      :paid="pageDescribe.paid"
      :costs="pageDescribe.costs"
      :default-effort="pageDescribe.defaultEffort"
      :part="pageDescribe.part"
      :detail="pageDescribe.detail"
      :steer="pageDescribe.steer"
      @answer="answerPageDescribe"
    />
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, reactive, ref, watch } from "vue";
import { CdxAccordion, CdxButton, CdxIcon, CdxMessage, CdxTab, CdxTabs, CdxTextInput } from "@wikimedia/codex";
import { cdxIconDownload, cdxIconPrevious, cdxIconSearch, cdxIconTrash, cdxIconUpload } from "@wikimedia/codex-icons";
import { API, del, errorText, filePath, get, newestOnly, objectPath, pagePath, patch, post, query } from "../api.js";
import { cleanText, searchWords } from "../text.js";
import { classColors } from "../class-colors.js";
import { writeAddress } from "../facets.js";
import { askConfirm, askConfirmValue, askRemoval } from "../confirm.js";
import { formatStamp, money, priceLabel, useT } from "../i18n.js";
import BulkDescribeDialog from "./BulkDescribeDialog.vue";
import PageDescribeDialog from "./PageDescribeDialog.vue";
import LocateDialog from "./LocateDialog.vue";
import BusyNote from "./BusyNote.vue";
import ColumnHeader from "./ColumnHeader.vue";
import ColumnSplitter from "./ColumnSplitter.vue";
import ColumnStrip from "./ColumnStrip.vue";
import ConfirmDialog from "./ConfirmDialog.vue";
import { addToHistory, appUrl, clearHistory, commonsFileUrl, forgetFileInBrowser, kindsOf, numberedNames, objectName, pageNumber, readHistory, readStart, removeFromHistory, restoreHistory, setAside } from "../state.js";
import { pageDescriptionVersion, versionBack } from "../undo.js";
import { readStored, writeStored } from "../storage.js";
import ViewedPanel from "./ViewedPanel.vue";
import DetectionPanel from "./DetectionPanel.vue";
import FileBar from "./FileBar.vue";
import Magnifier from "./Magnifier.vue";
import NoticeList from "./NoticeList.vue";
import RetentionInfo from "./RetentionInfo.vue";
import InfoDialog from "./InfoDialog.vue";
import KindLinks from "./KindLinks.vue";
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
// A hint per way (wish Olaf, 12-11-2026): the word SAM looks for at the click or in the rectangle.
const hints = reactive({ point: "", draw: "" });

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
// Blocked storage: every column starts open.
const closed = reactive(Object.fromEntries(COLUMNS.map((column) => [column, readStored(`cc-kolom-dicht-${column}`) === "1"])));
function setClosed(column, value) {
  closed[column] = value;
  writeStored(`cc-kolom-dicht-${column}`, value ? "1" : "0");
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
  const value = Number(readStored(CERTAINTY_KEY));
  return value >= 0 && value <= 0.95 ? value : 0;
}
// The address wins (wish Olaf: zekerheid=57 in a shared link), else this browser's last choice.
const askedCertainty = Number(new URLSearchParams(window.location.search).get("zekerheid"));
const minScore = ref(askedCertainty > 0 && askedCertainty <= 95 ? askedCertainty / 100 : readCertainty());
watch(minScore, (value) => writeAddress({ zekerheid: value > 0 ? String(Math.round(value * 100)) : "" }));
watch(minScore, (value) => writeStored(CERTAINTY_KEY, String(value)));
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
  // A name of your own replaces the AI's search term (wish Olaf, 12-11-2026): "car" no longer
  // finds the suitcase that was found as "cardboard box".
  // (label and label_nl are that term and its Dutch, so they go too; label_item is the Wikidata item.)
  // The same rule as the Objects page and the export (facets.js, api.py): a group's name counts as
  // a name of its own, and a region from Commons keeps its label (that is Commons' word, not the AI's).
  const own = o.naam || o.groep?.naam;
  const ai = own ? (o.bron === "commons" ? [o.label] : []) : [o.label, o.label_nl, o.zoekterm];
  return [listNames.value[o.id], o.naam, ...ai, o.label_item, o.wikidata, o.bijschrift?.tekst, ...description]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}
const visibleObjects = computed(() => {
  const words = searchWords(objectQuery.value); // zero-width or only spaces: no search
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
// The object in the magnifier is gone from the list (trashed or merged in another tab, a group undone):
// the magnifier closes and says so, instead of vanishing without a word.
watch(magnified, (now, before) => {
  if (now || !before || !magnifierOpen.value) return;
  magnifierOpen.value = false;
  notify("warning", t("objects.magnified_gone", { name: objectName(before, props.config.taal, t) }), { where: "objecten" });
});

// -- Answers that arrive late ---------------------------------------------------------------
// The file and page an action started on. An answer for a page that was left meanwhile (another
// page, another file from the history) is not put on the new one: it is on the server, and shows
// when that page is opened again.
const pageKey = () => `${file.value?.mid || ""}/${pageN.value}`;
const stillOn = (key) => key === pageKey();
// The file and page whose objects are shown now ("" before the first page came in).
let shownPage = "";

// -- Notices --------------------------------------------------------------------------

let noticeId = 0;
// A notice shows at the top of the page, or with where: "objecten" in the objects column,
// where the action it reports on took place.
/* Colours of messages (Codex, decision Olaf 12-11-2026): "error" (red) only when something went
   wrong; "warning" (yellow) for anything to note or to undo (to the trash, nothing found, merged);
   "success" (green) when it worked; "notice" (grey) only for fixed explanations, not as a message. */
// One message per place (wish Olaf 13-11-2026): a new one with a `where` replaces the one there.
function notify(type, text, extra = {}) {
  const kept = extra.where ? notices.value.filter((n) => n.where !== extra.where) : notices.value;
  notices.value = [...kept.slice(-3), { id: ++noticeId, type, text, ...extra }];
}
// The Undo button of a notice (actions): runs `run`, then says so in green at the same place, or the
// error in red. `label` replaces "↶ Ongedaan maken" (e.g. "Vorige versie terugzetten").
function undoAction(run, where, done = t("feedback.undone"), label = "") {
  return {
    label: label || `↶ ${t("magnifier.undo")}`,
    run: async () => {
      try {
        await run();
        notify("success", done, { where });
      } catch (error) {
        fail(error, where);
      }
    },
  };
}
// Only what is about the whole file goes on top; the outcome of an action shows near the button that
// asked for it (wish Olaf), with `where`: commons, ai-beschrijving, ai-zoektermen, ai-alles,
// vergroter, opslaan, objecten, bulk (just above the bulk tabs).
const topNotices = computed(() => notices.value.filter((n) => !n.where));
const objectNotices = computed(() => notices.value.filter((n) => n.where === "objecten"));
const noticesAt = (where) => notices.value.filter((n) => n.where === where);
function dismiss(id) {
  const notice = notices.value.find((n) => n.id === id);
  // A warning that should not come back once read (a damaged store): remembered in this browser.
  if (notice?.remember) writeStored(SEEN_DAMAGED_KEY, [...new Set([...seenDamaged(), ...notice.remember])], { json: true });
  notices.value = notices.value.filter((n) => n.id !== id);
}
// The page's objecten.json could not be read (wish Olaf 13-11-2026): the page shows as empty,
// what was there is kept aside on the server. A yellow notice in the objects column says so, once
// per kept copy (closing it remembers that you saw it).
const SEEN_DAMAGED_KEY = "cc-kapot-gezien";
const seenDamaged = () => {
  const list = readStored(SEEN_DAMAGED_KEY, [], { json: true });
  return Array.isArray(list) ? list : [];
};
function warnDamaged(copies) {
  const seen = seenDamaged();
  const fresh = (Array.isArray(copies) ? copies : []).filter((c) => c?.bestand && !seen.includes(`${file.value?.mid}/${pageN.value}/${c.bestand}`));
  if (!fresh.length) return;
  notify("warning", t("objects.damaged_store", { files: fresh.map((c) => c.bestand).join(", "), when: formatStamp(fresh[fresh.length - 1].gewijzigd, props.config.taal) }), {
    where: "objecten",
    remember: fresh.map((c) => `${file.value?.mid}/${pageN.value}/${c.bestand}`),
  });
}
function fail(error, where = undefined) {
  // Not found: the object (or page) changed elsewhere, e.g. in another tab. The list is loaded
  // again, so it shows what is really there, and the message says so.
  const stale = error?.status === 404 && Boolean(file.value && page.value);
  notify("error", errorText(t, error) + (stale ? ` ${t("feedback.list_reloaded")}` : ""), where ? { where } : {});
  if (stale) reloadObjects();
}
// The objects of the open page as the server has them now (free).
async function reloadObjects() {
  const key = pageKey();
  const data = await get(pagePath(file.value.mid, pageN.value)).catch(() => null);
  if (!data || !stillOn(key)) return;
  objects.value = data.objecten;
  trashTerms.value = data.prullenbak_termen || {};
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
  // `objects`: what the question is about, as a list with small cut-outs (like grouping); the
  // cost then comes after them.
  if (objects.length) return askConfirm(action || cost, { title: t("confirm.cost_title"), objects, note: action ? cost : "" });
  return askConfirm(action ? `${action}\n\n${cost}` : cost, { title: t("confirm.cost_title") });
}

// Some of the words were searched on this image before: use SAM's saved answers (free for those
// words) or ask SAM anew for all of them (paid). null: cancelled; true: anew.
async function chooseFreshDetection(action, calls) {
  const usd = (n) => money(props.config.betaald ? n * props.config.sam_usd : 0, props.config.taal);
  const saved = usd(calls.betaald);
  const anew = usd(props.config.betaald ? calls.termen : 0);
  const savedText = calls.in_cache >= calls.termen ? t("confirm.detect_saved_all") : t("confirm.detect_saved", { n: calls.in_cache, total: calls.termen });
  const text = [action, savedText].join("\n\n");
  const choices = [
    { value: "cache", label: t("confirm.detect_choice_saved", { amount: saved }), help: t(calls.betaald ? "confirm.detect_choice_saved_help_new" : "confirm.detect_choice_saved_help", { n: calls.termen - calls.in_cache }), go: t("confirm.detect_go_saved") },
    { value: "vers", label: t("confirm.detect_choice_fresh", { amount: anew }), help: t("confirm.detect_choice_fresh_help", { n: calls.termen }), go: t("confirm.detect_go_fresh", { amount: anew }) },
  ];
  const answer = await askConfirmValue(text, { title: t("confirm.detect_title"), choices });
  if (!answer.ok) return null;
  return answer.choice === "vers";
}

// -- Loading --------------------------------------------------------------------------

// Only the file asked last opens: a slow answer for one asked before does not replace it.
const fileLoad = newestOnly();
async function openFile(text) {
  const current = fileLoad();
  loadingFile.value = true;
  try {
    const value = cleanText(text);
    const isMid = /^m\d+$/i.test(value);
    const found = await get(`${API}/bestand${query(isMid ? { mid: value } : { url: value })}`);
    if (!current()) return;
    file.value = found;
    if (found.doorverwezen_van) notify("warning", t("file.redirected", { from: found.doorverwezen_van, to: found.titel }));
    if (found.ondersteund) await goToPage(start.mid === found.mid && start.pagina ? start.pagina : 1);
  } catch (error) {
    if (!current()) return;
    file.value = null;
    page.value = null;
    fail(error);
  } finally {
    if (current()) loadingFile.value = false;
  }
}

// Read the open file from Commons again (the app keeps what it read for a day), e.g.
// after adding a caption or depicts there. Free; the page and its objects stay.
async function readAgain() {
  if (!file.value || busy.value) return;
  const mid = file.value.mid;
  busy.value = true;
  try {
    const fresh = await post(`${API}/bestand/${mid}/opnieuw-lezen`, {});
    if (file.value?.mid !== mid) return; // another file was opened meanwhile
    file.value = fresh;
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

// Only the page asked last is shown (page after page quickly, or a page asked while a file opened).
const pageLoad = newestOnly();
async function goToPage(asked) {
  const mid = file.value.mid;
  const n = pageNumber(asked, file.value.paginas); // "abc", 0 or a page the file no longer has: the nearest
  const before = pageN.value;
  const current = pageLoad();
  pageN.value = n;
  try {
    const data = await get(pagePath(mid, n));
    if (!current() || file.value?.mid !== mid) return;
    // Another page: the magnifier of the previous one closes first (it is not "gone").
    if (shownPage !== `${mid}/${n}`) magnifierOpen.value = false;
    shownPage = `${mid}/${n}`;
    page.value = data;
    objects.value = data.objecten;
    trashTerms.value = data.prullenbak_termen || {};
    warnDamaged(data.beschadigd);
    newIds.value = [];
    inventory.value = null;
    // Only the parameters of the file and page change; the choices on the page (q, zekerheid, maskers, kaders, uselang) stay.
    writeAddress({ mid: file.value.mid, pagina: n > 1 ? String(n) : "", object: "", vergroten: "", url: "", titel: "" });
    visited.value = addToHistory({ mid: file.value.mid, naam: file.value.naam, pagina: n, paginas: file.value.paginas });
    const asked = `${file.value.mid}/${n}`;
    get(`${pagePath(file.value.mid, n)}/inventaris`)
      .then((plan) => {
        if (asked !== `${file.value?.mid}/${pageN.value}`) return; // not for a page left meanwhile
        inventory.value = plan.inventaris;
        setPrices(plan);
      })
      .catch(() => {});
    if (start.object) {
      const id = start.object;
      const magnify = start.vergroten; // from the eye on the Objects page
      const key = pageKey();
      start.object = "";
      start.vergroten = "";
      setTimeout(() => {
        if (!stillOn(key)) return;
        // An old link: the object was trashed, merged or the image started over since.
        if (!objects.value.some((o) => o.id === id)) {
          notify("warning", t("objects.link_missing"), { where: "objecten" });
          return;
        }
        focusObject(id);
        if (magnify) openMagnifier(id, magnify === "aangevuld" ? "aangevuld" : "");
      }, 300);
    }
  } catch (error) {
    if (!current()) return;
    // Never the objects of another page or file under this one: back to the page that was shown,
    // or, when it was another file's, nothing (with the error and a way to try again).
    if (shownPage.startsWith(`${mid}/`) && page.value) pageN.value = before;
    else {
      page.value = null;
      objects.value = [];
      inventory.value = null;
      shownPage = "";
    }
    notify("error", errorText(t, error), { actions: [{ label: t("actions.try_again"), run: () => file.value?.mid === mid && goToPage(n) }] });
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
    fail(error, "bekeken"); // by the list it was asked from (also on the start page, without a file)
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
    fail(error, "bekeken");
    return;
  }
  forgetFileInBrowser(entry.mid);
  workKept.value = { ...workKept.value, [entry.mid]: false };
  if (file.value?.mid === entry.mid) window.location.reload();
  else notify("success", t("feedback.started_over", { name: entry.naam || entry.mid }), { where: "bekeken" });
}

// Your own name for an object (from the list); "" goes back to the automatic name.
// A name that is the word of a depicts item of this file (its label in either language, capitals
// ignored) also links the object to that item, so it counts there and goes to Commons as its
// depicts with this box; a link to another depicts item is dropped (wish Olaf: child 3 renamed
// to doll). With a notice and Undo.
async function renameObject(id, typed) {
  const name = cleanText(typed); // only spaces or invisible characters: back to the automatic name
  const obj = objects.value.find((o) => o.id === id);
  const mid = file.value.mid;
  const n = pageN.value;
  const key = pageKey();
  const body = { naam: name || null };
  const before = { naam: obj?.naam || null, item: obj?.wikidata ? { q: obj.wikidata, label: obj.label_item || "" } : null };
  const match = name ? depictsItemFor(name) : null;
  const linkedToDepicts = obj?.wikidata && depictsItems().some((item) => item.q === obj.wikidata);
  if (match && match.q !== obj?.wikidata) body.item = { q: match.q, label: match.label };
  else if (name && !match && linkedToDepicts) body.item = null;
  try {
    const changed = await patch(objectPath(mid, n, id), body);
    if (stillOn(key)) replaceObject(changed);
    const undo = undoAction(() => undoRename(id, n, mid, before), "objecten", t("feedback.name_back"));
    if ("item" in body) {
      const oldLabel = before.item ? depictsItems().find((item) => item.q === before.item.q)?.label || before.item.label || before.item.q : "";
      const text = body.item ? t("objects.renamed_linked", { item: match.label, q: match.q }) : t("objects.renamed_unlinked", { item: oldLabel });
      notify("warning", text, { where: "objecten", object: shownObject(changed, n), actions: [undo] });
    } else {
      // A plain rename: green, with Undo (wish Olaf 13-11-2026).
      notify("success", t("feedback.renamed"), { where: "objecten", object: shownObject(changed, n), actions: [undo] });
    }
  } catch (error) {
    fail(error, "objecten");
  }
}

async function undoRename(id, n, mid, before) {
  const changed = await patch(objectPath(mid, n, id), before);
  if (file.value?.mid === mid && pageN.value === n) replaceObject(changed);
}

// The depicts items of this file on Commons ({q, label, words}): their labels in both languages.
function depictsItems() {
  const seen = new Map();
  for (const statement of file.value?.sdc?.beeldt_af || []) {
    if (statement.soort !== "item" || seen.has(statement.waarde)) continue;
    const label = (props.config.taal === "en" ? statement.label_en : statement.label) || statement.label || statement.label_en || statement.waarde;
    const all = [statement.label, statement.label_en].filter(Boolean).map((w) => String(w).trim().toLowerCase());
    seen.set(statement.waarde, { q: statement.waarde, label, words: all });
  }
  return [...seen.values()];
}
function depictsItemFor(name) {
  const word = String(name).trim().toLowerCase();
  return word ? depictsItems().find((item) => item.words.includes(word)) || null : null;
}

function replaceObject(changed) {
  objects.value = objects.value.map((o) => (o.id === changed.id ? changed : o));
}

// -- Detection (7) ----------------------------------------------------------------------

// The outcome of the last detection, for the panel ({found, excluded, prompt, modus}).
const lastResult = ref(null);
const resultIds = computed(() => lastResult.value?.ids || []);

// Searching: the window first; only after you confirm does the app say it is busy (wish Olaf
// 13-11-2026: no busy bar behind a window that is not confirmed yet).
let askingDetect = false;
async function detect(request) {
  if (busy.value || askingDetect) return; // one search at a time: a second click never asks (or pays) twice
  lastResult.value = null;
  const asked = request.prompt || ""; // as asked, before any word was changed in the window
  const base = pagePath(file.value.mid, pageN.value);
  const key = pageKey();
  askingDetect = true;
  try {
    if (request.modus === "prompt") {
      // Search words: one window with what is searched, saved answers or SAM anew, the cost, and
      // (folded away) the words themselves to change first (AI steering, wish Olaf 13-11-2026).
      // Without an English label on Wikidata the window opens with the words, asking for one.
      const { askWord, ...asked } = request;
      const answer = await askLocate({ path: base, prompt: request.prompt || "", askWord: Boolean(askWord) });
      if (!answer) return;
      request = {
        ...asked,
        prompt: answer.prompt,
        ...(Object.keys(answer.als).length ? { als: answer.als } : {}),
        ...(answer.fresh ? { vers: true } : {}),
      };
    } else if (request.modus !== "commons") {
      const { items, ...asked } = request; // items (Q-ids) do not change the cost
      const estimate = await get(`${base}/detecties/raming${query(asked)}`);
      // The terms as a list (scrolls when long, wish Olaf): one per line.
      const termList = String(request.prompt || "").split(",").map((term) => term.trim()).filter(Boolean).map((term) => `- ${term}`).join("\n");
      const action = request.modus === "prompt" ? t("confirm.action_detect", { terms: termList }) : t("confirm.action_detect_all");
      const calls = estimate.aanroepen;
      if (calls.in_cache) {
        // Words searched before: the saved answer (free) or SAM anew (paid), your choice (wish Olaf).
        const fresh = await chooseFreshDetection(action, calls);
        if (fresh === null) return;
        if (fresh) request = { ...request, vers: true };
      } else if (!(await confirmCost(calls.betaald, calls.betaald * props.config.sam_usd, action))) return;
    }
    busy.value = true; // confirmed: now SAM is at work
    const result = await post(`${base}/detecties`, request);
    if (!stillOn(key)) return; // found on the page left meanwhile: there when it is opened again
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
      // Which ones, so the message can offer to restore them (wish Olaf, 12-11-2026).
      trashIds: elders.in_prullenbak || [],
      holders: holders.map((id) => listNames.value[id] || objectName(result.objecten.find((o) => o.id === id) || {}, props.config.taal, t)).filter(Boolean),
      // The words as asked, so the panel marks those terms as searched (also when a word was changed).
      prompt: asked || request.prompt || "",
      modus: request.modus,
      at: Date.now(),
    };
  } catch (error) {
    // Under the button that asked for it, like a result (wish Olaf), not at the top of the page.
    if (!stillOn(key)) return fail(error);
    lastResult.value = { fout: errorText(t, error), prompt: request.prompt || "", modus: request.modus, at: Date.now() };
  } finally {
    askingDetect = false;
    busy.value = false;
  }
}

// Remove the page overview, or one part of it ("beschrijving" or "zoektermen"), after a confirmation.
async function forgetInventory(part = null) {
  const key = part || "alles";
  // What goes, one bullet per thing with what it says now (wish Olaf 13-11-2026): the kind of
  // image, the description in its four lengths, the text read, and/or the search terms.
  const overview = inventory.value || {};
  const en = props.config.taal === "en";
  const pick = (nl, other) => (en ? other || nl : nl || other) || "";
  const fields = [];
  if (key !== "zoektermen") {
    fields.push({ label: t("panel.part_forget_item_kind"), value: pick(overview.paginasoort, overview.paginasoort_en) });
    fields.push({ label: t("panel.part_forget_item_lengths"), help: t("panel.part_forget_item_lengths_help"), value: pick(overview.samenvatting, overview.samenvatting_en) });
    // The text read keeps its lines (stored with " | " between them).
    fields.push({ label: t("panel.part_forget_item_text"), help: t("panel.part_forget_item_text_help"), value: String(overview.tekst || "").split(/\s*\|\s*/).join("\n") });
  }
  if (key !== "beschrijving") {
    fields.push({ label: t("panel.part_forget_item_terms"), items: (overview.zoektermen || []).map((term) => (en ? term.en : term.nl || term.en)) });
  }
  const [question, ...rest] = t(`panel.part_forget_confirm_${key}`).split(/\n\s*\n/);
  if (!(await askConfirm(question, { title: t(`panel.part_forget_title_${key}`), go: t(key === "zoektermen" ? "panel.part_forget_zoektermen_button" : key === "beschrijving" ? "panel.part_forget_beschrijving_go" : "panel.part_forget"), destructive: true, fields, fieldsTitle: t("panel.part_forget_goes"), note: rest.join("\n\n") }))) return;
  const base = `${pagePath(file.value.mid, pageN.value)}/inventaris`;
  // The description goes into its history, so Undo puts it back (the search terms do not come back).
  const removed = key === "zoektermen" ? "" : pageDescriptionVersion(inventory.value);
  try {
    const result = await del(`${base}${part ? `/${part}` : ""}`);
    showInventory(base, result.inventaris); // only while that page is still open
    const where = `ai-${key}`;
    const undo = undoAction(async () => showInventory(base, (await versionBack(`${base}/beschrijving`, "versie", removed)()).inventaris), where, t("feedback.description_back"));
    notify("warning", t(`panel.part_forgotten_${key}`) + (removed && key === "alles" ? ` ${t("feedback.terms_not_back")}` : ""), { where, actions: removed ? [undo] : [] });
  } catch (error) {
    fail(error, `ai-${key}`);
  }
}

// The page overview. With `again` the model is really asked anew (paid);
// otherwise a stored answer for this page and model comes from the cache, free.
// With `part` ("beschrijving" or "zoektermen") only that part is asked anew.
// Asking the overview: the window first, and only after you confirm does the app say it is busy
// (wish Olaf 13-11-2026: the bar ran behind the window before anything was confirmed).
let askingInventory = false;
async function askInventory(again = false, part = null, detail = undefined, descLevel = undefined) {
  if (busy.value || askingInventory) return; // never two (paid) questions from one double click
  const base = pagePath(file.value.mid, pageN.value);
  askingInventory = true;
  try {
    const plan = await get(`${base}/inventaris`);
    setPrices(plan);
    // The description or the search terms asked anew (there are some already): a window of its
    // own, where the prompt can be changed too (wish Olaf 13-11-2026). The first time goes with
    // the app's prompt.
    const hasDescription = Boolean(inventory.value?.samenvatting || inventory.value?.samenvatting_en || Object.keys(inventory.value?.beschrijvingen || {}).length);
    const hasTerms = Boolean(inventory.value?.zoektermen?.length);
    let steer = {};
    if ((part === "beschrijving" && hasDescription) || (part === "zoektermen" && hasTerms)) {
      const answer = await askPageDescribe({
        path: base,
        part,
        detail: part === "zoektermen" ? detail || inventory.value?.detailniveau || "normaal" : "",
        paid: plan.betaald,
        costs: plan.kosten_per_redeneren || {},
        defaultEffort: plan.redeneren || "low",
      });
      if (!answer) return;
      steer = { ...(answer.hint ? { aanwijzing: answer.hint } : {}), redeneren: answer.effort, ...(answer.detail ? { detailniveau: answer.detail } : {}) };
    } else if (part !== "beschrijving") {
      // The first search terms, or the whole first overview: the same window, with the level of
      // detail in it and no steering (wish Olaf 13-11-2026); the first time goes with the app's prompt.
      const answer = await askPageDescribe({
        path: base,
        part: part || "alles",
        steer: false,
        detail: "normaal", // the first time always starts at Normal (wish Olaf 13-11-2026)
        paid: plan.betaald,
        costs: plan.kosten_per_redeneren || {},
        defaultEffort: plan.redeneren || "low",
      });
      if (!answer) return;
      if (answer.detail) detail = answer.detail;
    } else {
      const action = t("confirm.action_page_description", { length: t(`descdetail.${descLevel || "normaal"}`) });
      if (!(await confirmCost(plan.betaald ? 1 : 0, plan.kosten_schatting_usd, action))) return;
    }
    busy.value = true; // confirmed: now the AI is at work
    const level = {
      ...(detail && part !== "beschrijving" ? { detailniveau: detail } : {}),
      ...(descLevel && part !== "zoektermen" ? { beschrijvingsniveau: descLevel } : {}),
    };
    const previous = part === "zoektermen" ? "" : pageDescriptionVersion(inventory.value);
    const result = await post(part ? `${base}/inventaris/${part}` : `${base}/inventaris`, part ? { ...level, ...steer } : { opnieuw: again, ...level });
    showInventory(`${base}/inventaris`, result.inventaris); // only while that page is still open
    // Green, under the button that asked (wish Olaf 13-11-2026). A paid answer is not undone, but the
    // description it replaced can be put back (free).
    const where = `ai-${part || "alles"}`;
    const replaced = previous && previous !== pageDescriptionVersion(result.inventaris);
    const back = undoAction(async () => showInventory(`${base}/inventaris`, (await versionBack(`${base}/inventaris/beschrijving`, "versie", previous)()).inventaris), where, t("feedback.previous_restored"), t("feedback.previous_back"));
    notify("success", t(`feedback.made_${part || "alles"}`), { where, actions: replaced ? [back] : [] });
  } catch (error) {
    fail(error);
  } finally {
    askingInventory = false;
    busy.value = false;
  }
}

// An overview from an Undo: shown only while its page is still open.
function showInventory(base, overview) {
  if (base === `${pagePath(file.value?.mid, pageN.value)}/inventaris`) inventory.value = overview;
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
    // Leave one out after all; a group needs at least two (wish Olaf 13-11-2026).
    pick: { min: 2, text: (n) => t("objects.group_confirm", { n }) },
    note: t("objects.group_note"),
    input: { label: t("objects.group_name"), placeholder, help: t("objects.group_name_help") },
  });
  if (!answer.ok) return null;
  // Some unticked: group just the ticked ones (by id, also when it was "all of one kind").
  const picked = answer.picked.length < members.length ? { objecten: answer.picked.map((i) => members[i].id) } : body;
  const groupName = cleanText(answer.value);
  const key = pageKey();
  const grouped = await withMaskWait(t("busy.group"), async () => {
    const result = await post(`${pagePath(file.value.mid, pageN.value)}/groepen`, { ...picked, ...(groupName ? { naam: groupName } : {}) });
    await loadMasks([result.object]);
    if (stillOn(key)) objects.value = result.objecten;
    return { id: result.object.id, n: result.object.groep.aantal, name: objectName(result.object, props.config.taal, t) };
  });
  // Green, above the bulk tabs, with Undo (wish Olaf 13-11-2026): ungroups it again.
  const n = pageN.value;
  const mid = file.value.mid;
  notify("success", t("panel.grouped", { n: grouped.n, name: grouped.name }), {
    where: "bulk",
    actions: [{ label: `↶ ${t("magnifier.undo")}`, run: () => undoGroup(grouped.id, n, mid, grouped.n) }],
  });
  return grouped;
}

// Undo a grouping from its notice: the group is undone and its members come back as they were.
async function undoGroup(id, n, mid, count) {
  try {
    await withMaskWait(t("busy.ungroup"), async () => {
      const result = await del(`${pagePath(mid, n)}/groepen/${id}`);
      if (mid === file.value?.mid && n === pageN.value) {
        await loadMasks(result.objecten.filter((o) => o.groep_van === id || !objects.value.some((x) => x.id === o.id)));
        objects.value = result.objecten;
      }
    });
    notify("success", t("panel.ungrouped", { n: count }), { where: "bulk" });
  } catch (error) {
    fail(error, "bulk");
  }
}

/* Grouping and ungrouping take a moment: the server joins (or splits) the masks, then the image
   fetches them. Meanwhile a note over the image and under the bulk buttons (wish Olaf 12-11-2026);
   it goes when the new masks are in, so they show at once. */
const maskWait = ref("");
async function withMaskWait(text, work) {
  maskWait.value = text;
  busy.value = true;
  busyAt.value = "objecten";
  try {
    return await work();
  } finally {
    maskWait.value = "";
    busy.value = false;
    busyAt.value = null;
  }
}
// Fetch the masks of these objects into the browser cache before they are shown; at most 20 s.
function loadMasks(list) {
  const urls = list.map((o) => o?.masker_url).filter(Boolean);
  return Promise.all(urls.map((url) => new Promise((resolve) => {
    const image = new Image();
    const timer = setTimeout(resolve, 20000);
    image.onload = image.onerror = () => { clearTimeout(timer); resolve(); };
    image.src = url;
  })));
}

// The visible objects per search term (no groups), named as in the list (Dutch name when there
// is one): for the trash in bulk; with two or more, to group per kind in one click; without a
// description, to describe per kind.
const termKinds = computed(() => kindsOf(visibleObjects.value, props.config.taal));
const groupableTerms = computed(() => termKinds.value.filter((item) => item.n >= 2));
const describableTerms = computed(() => kindsOf(visibleObjects.value, props.config.taal, (o) => o.beschrijving));
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
  const links = trashLinks(fromCommons);
  const one = members.length === 1;
  const text = t(one ? "panel.bulk_trash_confirm_one" : "panel.bulk_trash_confirm", { n: members.length, term: name });
  const note = [t(one ? "panel.bulk_trash_note_one" : "panel.bulk_trash_note"), fromCommons ? t("objects.trash_confirm_commons") : ""].filter(Boolean).join("\n\n");
  // Each object a tick box: leave one out after all (wish Olaf 13-11-2026).
  const pick = { min: 1, text: (k) => t(k === 1 ? "panel.bulk_trash_confirm_one" : "panel.bulk_trash_confirm", { n: k, term: name }), go: (k) => t("panel.bulk_trash_go", { n: k }) };
  const answer = await askConfirmValue(text, { title, go: t("panel.bulk_trash_go", { n: members.length }), destructive: true, links, objects: members.map((o) => shownObject(o)), note, pick: members.length > 1 ? pick : null });
  if (!answer.ok) return;
  const n = pageN.value;
  const mid = file.value.mid;
  const ids = answer.picked.map((i) => members[i].id);
  busy.value = true;
  try {
    let result = null;
    for (const id of ids) result = await del(objectPath(mid, n, id));
    if (stillOn(`${mid}/${n}`)) {
      if (magnifierOpen.value && ids.includes(magnifiedId.value)) magnifierOpen.value = false;
      if (result) objects.value = result.objecten;
    }
    refreshTrashTerms(n, mid);
    notify("warning", t(ids.length === 1 ? "panel.bulk_trashed_one" : "panel.bulk_trashed", { n: ids.length, term: name }), {
      where: "bulk",
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

// "Restore from trash" in a search message: the hits that were in the trash come back as
// objects; the message says so itself, under the button that asked (wish Olaf, 12-11-2026).
async function restoreFound(result) {
  const ids = result?.trashIds || [];
  if (!ids.length || busy.value) return;
  const n = pageN.value;
  const mid = file.value.mid;
  busy.value = true;
  try {
    await restoreIds(ids, n, mid);
    if (lastResult.value === result) {
      lastResult.value = { ...result, inTrash: 0, trashIds: [], restored: ids.length, ids: [...(result.ids || []), ...ids] };
    }
  } catch (error) {
    if (lastResult.value === result) lastResult.value = { ...result, restoreError: errorText(t, error) };
  } finally {
    busy.value = false;
  }
}

// Objects back from the trash; when their page is still open it shows them again (Undo can come
// after another file was opened: then only the server changes).
async function restoreIds(ids, n, mid) {
  for (const id of ids) await patch(objectPath(mid, n, id), { prullenbak: false });
  if (mid === file.value?.mid && n === pageN.value) {
    const data = await get(pagePath(mid, n));
    objects.value = data.objecten;
    trashTerms.value = data.prullenbak_termen || {};
  }
}

async function restoreMany(ids, n, mid, name) {
  try {
    await restoreIds(ids, n, mid);
    notify("success", t(ids.length === 1 ? "panel.bulk_restored_one" : "panel.bulk_restored", { n: ids.length, term: name }), { where: "bulk" });
  } catch (error) {
    fail(error, "bulk");
  }
}

// "Groeperen (n)": the selected objects; the outcome under the buttons.
async function groupSelected() {
  actionResult.value = null;
  try {
    const members = objects.value.filter((o) => o.status === "geselecteerd");
    // The confirmation said what happens; a notice with Undo says it happened.
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
  const text = t("objects.ungroup_confirm_list", { n: members.length });
  const note = t("objects.ungroup_note") + (loses ? `\n\n${t("objects.ungroup_confirm")}` : "");
  const shown = members.map((m) => ({ image: `${objectPath(file.value.mid, pageN.value, m.id)}/uitsnede.jpg?w=96`, name: objectName(m, props.config.taal, t) })); // the same name as in the list
  if (!(await askConfirm(text, { title: t("objects.ungroup"), go: t("objects.ungroup"), destructive: Boolean(loses), objects: shown, note }))) return;
  const n = pageN.value;
  const mid = file.value.mid;
  try {
    await withMaskWait(t("busy.ungroup"), async () => {
      const result = await del(`${pagePath(mid, n)}/groepen/${id}`);
      await loadMasks(result.objecten.filter((o) => members.some((m) => m.id === o.id)));
      if (stillOn(`${mid}/${n}`)) objects.value = result.objecten;
    });
    // Green, near the list, so you see it worked (wish Olaf 13-11-2026); Undo groups the same
    // members again, with the group's own name (its caption or description does not come back).
    const name = group.groep?.naam;
    const regroup = undoAction(
      () => withMaskWait(t("busy.group"), async () => {
        const result = await post(`${pagePath(mid, n)}/groepen`, { objecten: members.map((m) => m.id), ...(name ? { naam: name } : {}) });
        if (mid === file.value?.mid && n === pageN.value) {
          await loadMasks([result.object]);
          objects.value = result.objecten;
        }
      }),
      "objecten",
      t("feedback.regrouped")
    );
    notify("success", t("panel.ungrouped", { n: members.length }) + (loses ? ` ${t("feedback.ungroup_undo_loses")}` : ""), { where: "objecten", actions: [regroup] });
  } catch (error) {
    fail(error);
  }
}

async function mergeDuplicates(scope = "alle") {
  if (busy.value) return; // a double click merges once
  actionResult.value = null;
  const key = pageKey();
  busy.value = true;
  try {
    const among = scope === "selectie" ? objects.value.filter((o) => o.status === "geselecteerd") : visibleObjects.value;
    const result = await post(`${pagePath(file.value.mid, pageN.value)}/samenvoegingen`, { objecten: among.map((o) => o.id) });
    if (!stillOn(key)) return;
    replaceObjects(result.objecten);
    // Which object went into which (wish Olaf): "suitcase → cardboard box".
    const pairs = (result.paren || []).map((pair) => t("detect.merged_pair", { gone: objectName(pair.weg, props.config.taal, t), kept: objectName(pair.in, props.config.taal, t) }));
    actionResult.value = result.samengevoegd
      ? { type: "success", text: t("detect.merged_list", { n: result.samengevoegd }), list: pairs }
      : { type: "warning", text: t("objects.merged_none") };
  } catch (error) {
    failInTab(error);
  } finally {
    busy.value = false;
  }
}

// Ticked objects without a description: what "Describe selected objects" describes, and its price.
const toDescribe = computed(() => objects.value.filter((o) => o.status === "geselecteerd" && !o.beschrijving).length);
const describeCost = computed(() => costFor(toDescribe.value));
// Everything visible without a description: "Describe all".
const toDescribeAll = computed(() => visibleObjects.value.filter((o) => !o.beschrijving).length);
const describeAllCost = computed(() => costFor(toDescribeAll.value));
// What Muse Spark costs for THIS file (bug found by Olaf 13-11-2026): a public-domain file without
// rights labels goes to the cheaper Contributor model, so the general prices in the settings (the
// standard model) were too high. Taken from the page's plan (GET …/inventaris, free): the price of
// the whole image as the server estimates it, and per object the price of the model it chose.
const prices = ref(null);
function setPrices(plan) {
  const cheap = plan?.model && plan.model === props.config.muse.rechtenvrij_model;
  prices.value = plan ? { page: plan.kosten_schatting_usd, object: cheap ? props.config.muse.beschrijving_rechtenvrij_usd : props.config.muse.beschrijving_usd } : null;
}
const objectUsd = computed(() => prices.value?.object ?? props.config.muse.beschrijving_usd);
// The price of describing n objects, as on the buttons.
function costFor(n) {
  return priceLabel(objectUsd.value * n, props.config.betaald, props.config.taal, t);
}
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
// The outcome of describing or merging in bulk shows as the bulk notice (one kind, one place).
watch(actionResult, (result) => {
  if (!result) return;
  notify(result.type, result.text, { where: "bulk", ...(result.list?.length ? { list: result.list } : {}) });
  actionResult.value = null;
});
watch(() => [file.value?.mid, pageN.value], () => { actionResult.value = null; });

// scope: "selectie", "alle" (everything visible) or { term } (the visible objects of one kind).
async function describeAll(scope = "selectie") {
  if (busy.value) return; // a second click while describing never describes (and pays) twice
  actionResult.value = null;
  const kind = scope && typeof scope === "object" ? scope.term : null;
  const among = kind
    ? visibleObjects.value.filter((o) => o.bron !== "groep" && o.zoekterm === kind)
    : scope === "alle"
      ? visibleObjects.value
      : objects.value.filter((o) => o.status === "geselecteerd");
  const chosen = among.filter((o) => !o.beschrijving);
  if (!chosen.length) {
    actionResult.value = { type: "warning", text: t("describe.nothing_to_do") };
    return;
  }
  // The objects as a list with small cut-outs, as when grouping, and the AI settings (wish Olaf).
  const kindName = kind ? describableTerms.value.find((item) => item.term === kind)?.name || kind : "";
  const action = kind
    ? t("confirm.action_describe_kind", { n: chosen.length, term: kindName })
    : t(scope === "alle" ? "confirm.action_describe_visible" : "confirm.action_describe_all", { n: chosen.length });
  const settings = await askBulkDescribe({
    objects: chosen.map((o) => ({ ...shownObject(o), ownPrompt: Boolean(o.prompt_eigen) })),
    paths: chosen.map((o) => objectPath(file.value.mid, pageN.value, o.id)),
    action,
    unitUsd: objectUsd.value,
    paid: Boolean(props.config.betaald),
    language: props.config.taal,
  });
  if (!settings) return;
  // The file and page they are on, fixed: going to another page meanwhile does not send the rest there.
  const mid = file.value.mid;
  const n = pageN.value;
  const key = pageKey();
  const total = chosen.filter((_, i) => settings[i]).length;
  busy.value = true;
  busyAt.value = "objecten";
  let done = 0;
  try {
    // Every object with its own settings from the dialog (wish Olaf); an unticked one is skipped.
    for (const [i, obj] of chosen.entries()) {
      if (!settings[i]) continue;
      const result = await post(`${objectPath(mid, n, obj.id)}/beschrijving`, settings[i]);
      if (stillOn(key)) replaceObject(result.object);
      done += 1;
    }
    actionResult.value = { type: "success", text: t("describe.done", { n: done }) };
  } catch (error) {
    // Some were described (and paid) before it went wrong: say how many, so none is asked twice.
    if (done) actionResult.value = { type: "error", text: t("describe.partly", { done, n: total, error: errorText(t, error) }) };
    else failInTab(error);
  } finally {
    busy.value = false;
    busyAt.value = null;
  }
}

// The dialog of Describe in bulk: resolves with the settings per object, or null when cancelled.
const bulkDescribe = reactive({ open: false, objects: [], paths: [], action: "", unitUsd: 0, paid: false, language: "nl" });
let bulkDescribeAnswer = null;
function askBulkDescribe(question) {
  Object.assign(bulkDescribe, question, { open: true });
  return new Promise((resolve) => (bulkDescribeAnswer = resolve));
}
// The window of locating: {prompt, als, fresh} to go ahead, null when cancelled.
const locate = reactive({ open: false, path: "", prompt: "", askWord: false });
let locateAnswer = null;
function askLocate(question) {
  Object.assign(locate, { askWord: false }, question, { open: true });
  return new Promise((resolve) => (locateAnswer = resolve));
}
function answerLocate(answer) {
  locate.open = false;
  locateAnswer?.(answer);
  locateAnswer = null;
}
// The window of "… opnieuw laten maken": {hint, effort} to go ahead, false when cancelled.
const pageDescribe = reactive({ open: false, path: "", paid: false, costs: {}, defaultEffort: "low", part: "beschrijving", detail: "", steer: true });
let pageDescribeAnswer = null;
function askPageDescribe(question) {
  Object.assign(pageDescribe, { steer: true }, question, { open: true });
  return new Promise((resolve) => (pageDescribeAnswer = resolve));
}
function answerPageDescribe(ok) {
  pageDescribe.open = false;
  pageDescribeAnswer?.(ok);
  pageDescribeAnswer = null;
}
function answerBulkDescribe(settings) {
  bulkDescribe.open = false;
  bulkDescribeAnswer?.(settings);
  bulkDescribeAnswer = null;
}

async function onPoint({ x, y }) {
  if (!pointMode.value || busy.value) return; // a click while the last one is asked: nothing (no second payment)
  lastResult.value = null;
  // Always the price first: only a click on the shape of a known object is free,
  // and the shapes are on the server (a click in a box beside its shape is a new search).
  const hint = cleanText(hints.point);
  const key = pageKey();
  if (!(await confirmCost(1, props.config.sam_usd, hint ? t("confirm.action_point_hint", { hint }) : t("confirm.action_point")))) return;
  busy.value = true;
  try {
    const result = await post(`${pagePath(file.value.mid, pageN.value)}/detecties`, { punt: { x, y }, ...(hint ? { hint } : {}) });
    if (!stillOn(key)) return;
    // The outcome in the panel, under "Aanwijzen of tekenen": new, already known, or nothing.
    if (!result.object) {
      lastResult.value = { section: "point", modus: "punt", outcome: "niets", hint, at: Date.now() };
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
  // The hint only counts with the Draw switch on: a Shift-drag stays free.
  const hint = drawMode.value ? cleanText(hints.draw) : "";
  const key = pageKey();
  if (hint) {
    if (busy.value) return; // paid: one at a time
    lastResult.value = null;
    if (!(await confirmCost(1, props.config.sam_usd, t("confirm.action_draw_hint", { hint })))) return;
    busy.value = true;
  }
  try {
    const result = await post(`${pagePath(file.value.mid, pageN.value)}/detecties`, { rechthoek: rect, ...(hint ? { hint } : {}) });
    if (!stillOn(key) || !result?.object) return;
    objects.value = [...objects.value.filter((o) => o.id !== result.object.id), result.object];
    newIds.value = [result.object.id];
    focusedId.value = result.object.id;
    lastResult.value = {
      section: "point",
      modus: "rechthoek",
      outcome: "nieuw",
      hint,
      gevonden: result.gevonden,
      name: listNames.value[result.object.id] || objectName(result.object, props.config.taal, t),
      // Undo in the message (to the trash): drawn without a hint, or with one that found the object.
      undo: !hint || result.gevonden ? { id: result.object.id, mid: file.value.mid, n: pageN.value } : null,
      at: Date.now(),
    };
  } catch (error) {
    fail(error);
  } finally {
    busy.value = false;
  }
}

// Undo of a drawn rectangle, from its message: the object goes to the trash (free).
async function undoDrawn(result) {
  const drawn = result?.undo;
  if (!drawn || busy.value) return;
  busy.value = true;
  try {
    const data = await del(objectPath(drawn.mid, drawn.n, drawn.id));
    if (drawn.mid === file.value?.mid && drawn.n === pageN.value) {
      if (magnifiedId.value === drawn.id) magnifierOpen.value = false;
      objects.value = data.objecten;
      refreshTrashTerms(drawn.n, drawn.mid);
    }
    if (lastResult.value === result) lastResult.value = { ...result, undo: null, undone: t("feedback.drawn_undone", { name: result.name }) };
  } catch (error) {
    if (lastResult.value === result) lastResult.value = { ...result, restoreError: errorText(t, error) };
  } finally {
    busy.value = false;
  }
}

async function refineMask(obj) {
  if (busy.value) return; // paid: never twice from one double click
  if (!(await confirmCost(1, props.config.sam_usd, t("confirm.action_mask", { name: listNames.value[obj.id] || objectName(obj, props.config.taal, t) })))) return;
  const n = pageN.value;
  const mid = file.value.mid;
  busy.value = true;
  try {
    const result = await post(`${pagePath(mid, n)}/detecties`, { masker_voor: obj.id });
    if (stillOn(`${mid}/${n}`)) replaceObject(result.object);
    // Undo removes the shape again (free): the object keeps its rectangle.
    const undo = undoAction(async () => {
      const back = await del(`${objectPath(mid, n, obj.id)}/vorm`);
      if (mid === file.value?.mid && n === pageN.value) replaceObject(back.object);
    }, "vergroter", t("feedback.shape_back"));
    notify("success", t("detect.mask_done"), { where: "vergroter", actions: [undo] });
  } catch (error) {
    fail(error, "vergroter");
  } finally {
    busy.value = false;
  }
}

// -- Selection and objects ----------------------------------------------------------------

// Ticking shows at once, before the server answers, so a quick second tick builds on the first
// (it used to send the list without the first one, which then came unticked). Only the answer to
// the last tick counts; after an error the list shows what the server really has.
const selectionSave = newestOnly();
async function setSelection(ids) {
  const key = pageKey();
  const chosen = new Set(ids);
  objects.value = objects.value.map((o) => {
    const status = chosen.has(o.id) ? "geselecteerd" : o.status === "geselecteerd" ? "kandidaat" : o.status;
    return status === o.status ? o : { ...o, status };
  });
  const current = selectionSave();
  try {
    const result = await patch(`${pagePath(file.value.mid, pageN.value)}/objecten`, { geselecteerd: ids });
    if (current() && stillOn(key)) objects.value = result.objecten;
  } catch (error) {
    if (!stillOn(key)) return;
    fail(error, "objecten");
    if (error?.status !== 404 && current()) reloadObjects(); // a 404 reloads already (fail)
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
  const key = pageKey();
  try {
    const result = await del(`${objectPath(file.value.mid, pageN.value, id)}/vorm`);
    if (stillOn(key)) objects.value = objects.value.map((o) => (o.id === id ? result.object : o));
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
  const links = trashLinks(fromCommons);
  const choices = shaped
    ? [
        { value: "vorm", label: t("objects.trash_choice_shape"), help: t(fromCommons ? "objects.trash_choice_shape_help_commons" : "objects.trash_choice_shape_help"), go: t("objects.trash_shape_go"), destructive: false },
        { value: "prullenbak", label: t("objects.trash_choice_object"), help: t("objects.trash_choice_object_help"), go: t("objects.trash"), destructive: true },
      ]
    : [];
  const commonsNote = fromCommons ? t("objects.trash_confirm_commons") : "";
  const answer = await askConfirmValue(shaped ? t(fromCommons ? "objects.trash_shape_intro_commons" : "objects.trash_shape_intro") : t("objects.trash_confirm"), {
    title: shaped ? t("objects.trash_shape_title") : t("objects.trash"),
    go: t("objects.trash"),
    destructive: true,
    links,
    choices,
    // Always asked (wish Olaf), with the object itself in the question; no "don't ask again".
    objects: target ? [shownObject(target)] : [],
    note: shaped ? commonsNote : [t("objects.trash_note"), commonsNote].filter(Boolean).join("\n\n"),
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
    const result = await del(objectPath(mid, n, id));
    const here = stillOn(`${mid}/${n}`); // another page meanwhile: its list stays as it is
    if (here && magnifiedId.value === id) {
      if (neighbour && result.objecten.some((o) => o.id === neighbour)) {
        magnifiedId.value = neighbour; // before the list changes, so the magnifier is not closed in between
        focusedId.value = neighbour;
      } else {
        magnifierOpen.value = false;
      }
    }
    if (here) objects.value = result.objecten;
    refreshTrashTerms(n, mid);
    notify("warning", t("objects.trashed"), {
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
    await restoreIds([id], n, mid);
    notify("success", t("objects.restored"), { where: "objecten", object: shown }); // with the object: which one came back
  } catch (error) {
    fail(error);
  }
}

// The trash counts per search term, fetched again after a move to or from the trash.
function refreshTrashTerms(n, mid = file.value?.mid) {
  get(pagePath(mid, n))
    .then((data) => {
      if (stillOn(`${mid}/${n}`)) trashTerms.value = data.prullenbak_termen || {};
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
// The links in a trash question; for objects from Commons also to the depicts of the file there.
const trashLinks = (fromCommons) => ({
  ...objectsLinks(),
  ...(fromCommons ? { commons: { href: commonsFileUrl(file.value.titel, "P180"), label: t("objects.trash_commons_link") } } : {}),
});

async function forget(mid) {
  const entry = visited.value.find((e) => e.mid === mid);
  const name = entry?.naam || mid;
  const links = {
    ...objectsLinks(),
    // The M-id opens the image again (in the input bar, and back in the active list).
    mid: { href: appUrl(mid, entry?.pagina || 1), label: mid, sameTab: true, class: "cc-mid-link" },
  };
  const image = { image: `/api/v1/bestand/${mid}/pagina/1/afbeelding?w=120`, name };
  if (!(await askRemoval(t("history.remove_confirm", { name }), { title: t("history.remove"), go: t("history.remove"), destructive: true, links }, { objects: [image] }))) return;
  const index = visited.value.findIndex((e) => e.mid === mid);
  visited.value = removeFromHistory(mid);
  // Undo puts the entry back at its place (only in this browser; nothing else was removed).
  const undo = undoAction(() => {
    const list = readHistory().filter((e) => e.mid !== mid);
    if (entry) list.splice(Math.min(index, list.length), 0, entry);
    visited.value = restoreHistory(list);
  }, "bekeken", t("feedback.viewed_back_one", { name }));
  notify("warning", t("feedback.viewed_removed_one", { name }), { where: "bekeken", actions: [undo] });
}

async function forgetAll() {
  if (!(await askConfirm(t("history.clear_confirm"), { title: t("history.clear"), go: t("history.clear"), destructive: true, links: objectsLinks() }))) return;
  const before = readHistory();
  visited.value = clearHistory();
  // Undo: the list as it was, after what was opened since.
  const undo = undoAction(() => {
    const now = readHistory();
    visited.value = restoreHistory([...now, ...before.filter((e) => !now.some((x) => x.mid === e.mid))]);
  }, "bekeken", t("feedback.viewed_back_all"));
  notify("warning", t("feedback.viewed_cleared", { n: before.length }), { where: "bekeken", actions: [undo] });
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
  if (busy.value) return;
  const key = pageKey();
  busy.value = true;
  try {
    const result = await post(`${pagePath(file.value.mid, pageN.value)}/uitsneden`, {});
    if (stillOn(key)) objects.value = result.objecten;
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
