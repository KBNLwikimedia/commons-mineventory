<!--
  The start page (functional design 10.4): input bar and file information,
  pages and objects on the left, the viewer in the middle, the detection panel
  on the right, and the magnifier as a dialog. All data comes from /api/v1.
-->
<template>
  <div class="cc-app">
    <file-bar :file="file" :loading="loadingFile" :initial="initialInput" @open="openFile" />

    <notice-list :notices="notices" @dismiss="dismiss" />

    <div v-if="file && !file.ondersteund" class="cc-unsupported">
      <cdx-message type="warning">{{ file.niet_ondersteund }}</cdx-message>
    </div>

    <div v-else-if="file && page" class="cc-werkblad">
      <aside class="cc-links" :aria-label="t('layout.left')">
        <page-list v-if="file.paginas > 1" :file="file" :current="pageN" @select="goToPage" />
        <object-list
          :objects="objects"
          :focused="focusedId"
          @toggle="toggleSelected"
          @select="setSelection"
          @focus="focusObject"
          @open="openMagnifier"
          @hover="hoverObject"
          @trash="trashObject"
        />
      </aside>

      <section class="cc-midden">
        <viewer-pane
          ref="viewer"
          :mid="file.mid"
          :page="page"
          :objects="objects"
          :new-ids="newIds"
          :point-mode="pointMode"
          @object-click="onObjectClick"
          @object-open="openMagnifier($event.id)"
          @point="onPoint"
          @rectangle="onRectangle"
        />
      </section>

      <aside class="cc-rechts" :aria-label="t('layout.right')">
        <detection-panel
          :file="file"
          :page="page"
          :busy="busy"
          :inventory="inventory"
          :point-mode="pointMode"
          @detect="detect"
          @smart="smartDetect"
          @inventory="askInventory"
          @merge="mergeDuplicates"
          @describe-all="describeAll"
          @point-mode="pointMode = $event"
        />
        <div class="cc-acties">
          <p class="cc-telling">{{ t("objects.count", { n: objects.length, selected: selectedCount }) }}</p>
          <cdx-button action="progressive" weight="primary" :disabled="!selectedCount || busy" @click="saveSelection">
            {{ t("actions.save", { n: selectedCount }) }}
          </cdx-button>
          <cdx-button :disabled="!savedCount" @click="downloadZip">
            <cdx-icon :icon="cdxIconDownload" /> {{ t("actions.zip") }}
          </cdx-button>
          <cdx-button :disabled="!savedCount" @click="toCommons">
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

    <cdx-dialog
      v-model:open="confirm.open"
      :title="t('confirm.title')"
      :use-close-button="true"
      :close-button-label="t('actions.close')"
      :primary-action="{ label: t('confirm.go'), actionType: 'progressive' }"
      :default-action="{ label: t('actions.cancel') }"
      @primary="confirm.resolve(true)"
      @default="confirm.resolve(false)"
      @update:open="(open) => !open && confirm.resolve(false)"
    >
      <p>{{ confirm.text }}</p>
    </cdx-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { CdxButton, CdxDialog, CdxIcon, CdxMessage } from "@wikimedia/codex";
import { cdxIconDownload, cdxIconUpload } from "@wikimedia/codex-icons";
import { API, del, errorText, filePath, get, objectPath, pagePath, patch, post, query } from "../api.js";
import { money, useT } from "../i18n.js";
import { appUrl, readStart } from "../state.js";
import DetectionPanel from "./DetectionPanel.vue";
import FileBar from "./FileBar.vue";
import Magnifier from "./Magnifier.vue";
import NoticeList from "./NoticeList.vue";
import ObjectList from "./ObjectList.vue";
import PageList from "./PageList.vue";
import ViewerPane from "./ViewerPane.vue";

const props = defineProps({ config: { type: Object, required: true } });
const t = useT();

const file = ref(null);
const pageN = ref(1);
const page = ref(null);
const objects = ref([]);
const newIds = ref([]);
const inventory = ref(null);
const focusedId = ref(null);
const pointMode = ref(false);
const loadingFile = ref(false);
const busy = ref(false);
const notices = ref([]);
const viewer = ref(null);
const magnifierOpen = ref(false);
const magnifiedId = ref(null);
const start = readStart(window.location.search);
const initialInput = start.url || start.titel || start.mid || "";

const selectedCount = computed(() => objects.value.filter((o) => o.status === "geselecteerd").length);
const savedCount = computed(() => objects.value.filter((o) => o.opgeslagen).length);
const magnified = computed(() => objects.value.find((o) => o.id === magnifiedId.value) || null);

// -- Notices --------------------------------------------------------------------------

let noticeId = 0;
function notify(type, text) {
  notices.value = [...notices.value.slice(-3), { id: ++noticeId, type, text }];
}
function dismiss(id) {
  notices.value = notices.value.filter((n) => n.id !== id);
}
function fail(error) {
  notify("error", errorText(t, error));
}

// -- Confirming paid actions (6.4): only in live mode, with the amount --------------------

const confirm = reactive({ open: false, text: "", resolve: () => {} });
function ask(text) {
  return new Promise((resolve) => {
    Object.assign(confirm, {
      open: true,
      text,
      resolve: (answer) => {
        confirm.open = false;
        confirm.resolve = () => {};
        resolve(answer);
      },
    });
  });
}
async function confirmCost(calls, usd) {
  if (!props.config.betaald || !calls) return true;
  return ask(t("confirm.cost", { n: calls, amount: money(usd, props.config.taal) }));
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
    newIds.value = [];
    inventory.value = null;
    history.replaceState(null, "", appUrl(file.value.mid, n));
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

async function askInventory() {
  const base = pagePath(file.value.mid, pageN.value);
  busy.value = true;
  try {
    const plan = await get(`${base}/inventaris`);
    if (!(await confirmCost(plan.betaald ? 1 : 0, plan.kosten_schatting_usd))) return;
    const result = await post(`${base}/inventaris`, {});
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

async function trashObject(id) {
  try {
    const result = await del(objectPath(file.value.mid, pageN.value, id));
    objects.value = result.objecten;
    if (magnifiedId.value === id) magnifierOpen.value = false;
    notify("notice", t("objects.trashed"));
  } catch (error) {
    fail(error);
  }
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
