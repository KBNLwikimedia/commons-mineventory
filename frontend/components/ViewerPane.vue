<!--
  Thin Vue wrapper around the plain-JS viewer (frontend/viewer/viewer.js):
  it mounts the viewer, passes objects in and events out (functional design 10.2).
-->
<template>
  <div class="cc-viewer-kader">
    <div class="cc-viewer-balk" role="toolbar" :aria-label="t('viewer.toolbar')">
      <cdx-button action="progressive" weight="quiet" :aria-label="t('viewer.zoom_out')" @click="viewer?.zoomStep(-1)"><cdx-icon :icon="cdxIconZoomOut" /></cdx-button>
      <!-- The current zoom; the button "Actual size" further on goes to 100%. -->
      <span class="cc-zoom" :title="t('viewer.zoom_now')">{{ Math.round(scale * 100) }}%</span>
      <cdx-button action="progressive" weight="quiet" :aria-label="t('viewer.zoom_in')" @click="viewer?.zoomStep(1)"><cdx-icon :icon="cdxIconZoomIn" /></cdx-button>
      <!-- Zoom slider, logarithmic: from 2% to 300%, each step the same factor. -->
      <input
        class="cc-zoom-schuif"
        type="range"
        :min="ZOOM_MIN_LOG"
        :max="ZOOM_MAX_LOG"
        step="0.05"
        :value="Math.log2(scale)"
        :aria-label="t('viewer.zoom_slider')"
        :aria-valuetext="`${Math.round(scale * 100)}%`"
        :title="t('viewer.zoom_slider')"
        @input="viewer?.zoomTo(2 ** Number($event.target.value))"
      />
      <cdx-button action="progressive" weight="quiet" :title="t('viewer.actual_size_help')" @click="viewer?.zoomTo(1)">{{ t("viewer.actual_size") }}</cdx-button>
      <cdx-button action="progressive" weight="quiet" @click="viewer?.fit()">{{ t("viewer.fit") }}</cdx-button>
      <!-- What to draw on the image, as in the Delpher Uitsnijder; remembered in this browser. -->
      <span class="cc-weergave-keuze" role="group" :aria-label="t('viewer.show')">
        <!-- Nothing to show without objects: then the choices are disabled. -->
        <cdx-checkbox v-model="show.maskers" :inline="true" :disabled="!objects.length" :title="objects.length ? '' : t('viewer.show_nothing')">{{ t("viewer.masks") }}</cdx-checkbox>
        <cdx-checkbox v-model="show.boxen" :inline="true" :disabled="!objects.length" :title="objects.length ? '' : t('viewer.show_nothing')">{{ t("viewer.boxes") }}</cdx-checkbox>
        <cdx-checkbox v-model="show.namen" :inline="true" :disabled="!objects.length" :title="objects.length ? '' : t('viewer.show_nothing')">{{ t("viewer.labels") }}</cdx-checkbox>
      </span>
      <span class="cc-viewer-hint">{{ drawMode ? t("viewer.hint_draw") : pointMode ? t("viewer.hint_point") : t("viewer.hint") }}</span>
      <slot name="balk" />
    </div>
    <!-- The colour legend (wish Olaf): what the frames and the masks show, open to start with, with
         the (i) in its heading; whenever the boxes or the masks have something to explain. -->
    <cdx-accordion v-if="(show.boxen && legend.length) || (show.maskers && kinds.length)" v-model="legendOpen" class="cc-legenda-blok">
      <!-- The (i) in the heading (wish Olaf): a button in the heading does not fold it. -->
      <!-- A click on the (i) also unfolds the legend, so its explanation and the rows go together (wish Olaf). -->
      <template #title>{{ t("legend.title") }} <span class="cc-legenda-info" @click.capture="unfoldLegend"><info-dialog :title="t('legend.info_title')" :label="t('legend.info_label')" :paragraphs="colourInfo" /></span></template>
      <p class="cc-uitleg cc-sectie-intro">{{ t("legend.intro") }}</p>
      <!-- The label in a fixed column, so the checkboxes of both rows start at the same place,
           and a second line starts under the first checkbox (wish Olaf). -->
      <div v-if="show.boxen && legend.length" class="cc-legenda-rij">
      <span class="cc-rij-kop">{{ t("legend.statuses") }}</span>
      <ul class="cc-legenda">
        <!-- A checkbox per status, in the colour of its frame (wish Olaf): unticked fades those objects. -->
        <li v-for="item in statusItems" :key="item">
          <cdx-checkbox v-model="shownStatuses" :input-value="item" :inline="true" class="cc-soort-vinkje" :class="`cc-status-${item}`" :style="{ '--soort': FRAME_COLOURS[item] }" :title="t('legend.status_only')">
            {{ t(`legend.${item}`) }} <span class="cc-soort-aantal">({{ statusCounts[item] || 0 }})</span>
          </cdx-checkbox>
        </li>
        <li v-if="statusItems.length > 1" class="cc-soorten-alles">
          <button type="button" class="cc-link" :disabled="!hiddenStatuses.length" @click="hiddenStatuses = []">{{ t("objects.all") }}</button>
          <span class="cc-punt" aria-hidden="true">·</span>
          <button type="button" class="cc-link" :disabled="hiddenStatuses.length === statusItems.length" @click="hiddenStatuses = [...statusItems]">{{ t("objects.none") }}</button>
          <span class="cc-punt" aria-hidden="true">·</span>
          <button type="button" class="cc-link" @click="hiddenStatuses = shownStatuses">{{ t("objects.invert") }}</button>
        </li>
        <!-- New and thicker are no status of their own: only explained. -->
        <li v-for="item in legend.filter((i) => !FRAME_KEYS.includes(i))" :key="item"><span :class="['cc-legenda-staal', `cc-legenda-${item}`]"></span>{{ t(`legend.${item}`) }}</li>
      </ul>
      </div>
      <!-- A colour per kind of object, each a checkbox: ticked kinds are shown (all to start
           with), with All · None · Invert as in the object list (wish Olaf). Only with the masks shown. -->
      <div v-if="show.maskers && kinds.length" class="cc-legenda-soorten">
        <!-- A mask always shows the kind, a frame the status (wish Olaf, 8-11-2026: no switch any more). -->
        <span class="cc-rij-kop cc-alleen-tonen">{{ t("legend.kinds") }}</span>
        <!-- The kinds as one block that wraps within itself: a second line starts under the first kind (wish Olaf). -->
        <ul class="cc-soorten-lijst">
          <li v-for="[kind, color] in kinds" :key="kind">
            <!-- The checkbox in the colour of the kind (wish Olaf): filled when ticked, its border when not. -->
            <cdx-checkbox v-model="shownKinds" :input-value="kind" :inline="true" class="cc-soort-vinkje" :style="{ '--soort': color }" :title="t(kind === query ? 'legend.query_only' : 'legend.kind_only', { kind })">
              {{ kind }} <span class="cc-soort-aantal">({{ kindCounts[kind] || 0 }})</span>
            </cdx-checkbox>
          </li>
          <li class="cc-soorten-alles">
            <button type="button" class="cc-link" :disabled="!hiddenKinds.length" @click="hiddenKinds = []">{{ t("objects.all") }}</button>
            <span class="cc-punt" aria-hidden="true">·</span>
            <button type="button" class="cc-link" :disabled="hiddenKinds.length === kinds.length" @click="hiddenKinds = kinds.map(([kind]) => kind)">{{ t("objects.none") }}</button>
            <span class="cc-punt" aria-hidden="true">·</span>
            <button type="button" class="cc-link" @click="hiddenKinds = shownKinds">{{ t("objects.invert") }}</button>
          </li>
        </ul>
      </div>
    </cdx-accordion>
    <div class="cc-viewer-vlak">
      <div ref="host" class="viewer" :aria-busy="imageState === 'loading' ? 'true' : 'false'"></div>
      <!-- Waiting feedback while the image comes in: the first time, the server fetches the original from Commons. -->
      <busy-note v-if="imageState === 'loading'" class="cc-viewer-laden" :message="t('viewer.loading')" />
      <!-- Waiting for something the image will show, e.g. the mask of a new group (wish Olaf). -->
      <busy-note v-else-if="waiting" class="cc-viewer-laden" :message="waiting" />
      <cdx-message v-else-if="imageState === 'error'" type="error" class="cc-viewer-laden">{{ t("viewer.load_error") }}</cdx-message>
    </div>
  </div>
</template>

<script setup>
import { computed, inject, onBeforeUnmount, onMounted, reactive, ref, shallowRef, watch, watchEffect } from "vue";
import { CdxAccordion, CdxButton, CdxCheckbox, CdxIcon, CdxMessage } from "@wikimedia/codex";
import { cdxIconZoomIn, cdxIconZoomOut } from "@wikimedia/codex-icons";
import { useT } from "../i18n.js";
import { numberedNames, objectName } from "../state.js";
import { readStored, writeStored } from "../storage.js";
import { PageViewer } from "../viewer/viewer.js";
import BusyNote from "./BusyNote.vue";
import InfoDialog from "./InfoDialog.vue";
import { FRAME_KEYS, classKeys, frameKey, kindsWithQuery } from "../class-colors.js";
import { readAddress, writeAddress } from "../facets.js";

const props = defineProps({
  mid: { type: String, required: true },
  // A text while the image waits for something (a group being made or undone); empty: nothing.
  waiting: { type: String, default: "" },
  page: { type: Object, required: true },
  objects: { type: Array, required: true },
  // {kind: colour} when the page has more than one kind of object (class-colors.js).
  classColors: { type: Object, default: () => ({}) },
  // What is typed in the search box above the object list; objects holds only what matches it.
  searchText: { type: String, default: "" },
  newIds: { type: Array, default: () => [] },
  pointMode: { type: Boolean, default: false },
  drawMode: { type: Boolean, default: false },
});
const emit = defineEmits(["object-click", "object-open", "object-hover", "point", "rectangle"]);
const t = useT();
const language = inject("language", "nl");
const host = ref(null);
const viewer = shallowRef(null);
const scale = ref(1);
const ZOOM_MIN_LOG = Math.log2(0.02);
const ZOOM_MAX_LOG = Math.log2(3); // MAX_SCALE in viewer.js
const LEGEND = ["geselecteerd", "kandidaat", "nieuw", "commons", "handmatig", "uitgesloten", "dik"];
// Only the colours that occur on this page (plus "thicker", which always can).
// The kinds with their colour, for the legend of the masks.
const query = computed(() => (props.objects.length ? props.searchText.trim().toLowerCase() : ""));
const kinds = computed(() => kindsWithQuery(props.classColors, query.value));
// How many objects of each kind are on the image now (wish Olaf), after the certainty slider and the search.
const kindCounts = computed(() => {
  const counts = {};
  for (const obj of props.objects) {
    for (const kind of classKeys(obj)) counts[kind] = (counts[kind] || 0) + 1;
  }
  if (query.value) counts[query.value] = props.objects.length;
  return counts;
});
// The colour legend of the frames: open to start with (wish Olaf).
const legendOpen = ref(true);
// The (i) in the heading also unfolds the legend (wish Olaf). On the <details> itself: the fold
// animation (accordion-motion.js) closes it directly, so the model may still say "open".
function unfoldLegend(event) {
  const details = event.currentTarget.closest("details");
  if (details && !details.open) details.open = true;
  legendOpen.value = true;
}
const colourInfo = computed(() => [1, 2, 3, 4, 5, 6].map((i) => t(`legend.info_${i}`)));
// The kinds you unticked: their objects fade. Kept as the hidden ones, so a kind found later
// shows (ticked) at once. A kind that is gone is dropped.
const hiddenKinds = ref([]);
// In the address (wish Olaf): maskers=boy,child are the ticked kinds while some are unticked ("-": none).
// Applied once, when the kinds of the image are known.
let askedKinds = new URLSearchParams(window.location.search).has("maskers") ? readAddress(["maskers"]).maskers : null;
const shownKinds = computed({
  get: () => kinds.value.map(([kind]) => kind).filter((kind) => !hiddenKinds.value.includes(kind)),
  set: (list) => (hiddenKinds.value = kinds.value.map(([kind]) => kind).filter((kind) => !list.includes(kind))),
});
// To the viewer: null when nothing is hidden (no filter), else the kinds to show. The viewer holds
// only what matches the search, so with the search text ticked everything in it may show.
const kindFilter = computed(() => (!hiddenKinds.value.length || shownKinds.value.includes(query.value) ? null : shownKinds.value));
watch(kindFilter, (list) => viewer.value?.setKindFilter(list));
watch(kinds, (list) => {
  const present = new Set(list.map(([kind]) => kind));
  if (hiddenKinds.value.some((kind) => !present.has(kind))) hiddenKinds.value = hiddenKinds.value.filter((kind) => present.has(kind));
});
const legend = computed(() => {
  const objects = props.objects;
  const present = {
    geselecteerd: objects.some((o) => o.status === "geselecteerd" && o.bron !== "commons" && o.bron !== "handmatig"),
    kandidaat: objects.some((o) => o.status === "kandidaat" && o.bron !== "commons" && o.bron !== "handmatig"),
    nieuw: props.newIds.length > 0,
    commons: objects.some((o) => o.bron === "commons"),
    handmatig: objects.some((o) => o.bron === "handmatig"),
    uitgesloten: objects.some((o) => o.status === "uitgesloten"),
    dik: objects.length > 0,
  };
  return LEGEND.filter((item) => present[item]);
});
// The statuses in the legend as checkboxes (wish Olaf): as with the kinds, the unticked ones are
// kept, so a status that appears later shows at once. Counts after the certainty slider and search.
const FRAME_COLOURS = {
  geselecteerd: "var(--cc-geselecteerd)",
  kandidaat: "var(--cc-kandidaat)",
  commons: "var(--cc-commons-rand)",
  handmatig: "var(--cc-handmatig)",
  uitgesloten: "var(--cc-uitgesloten)",
};
const statusItems = computed(() => legend.value.filter((item) => FRAME_KEYS.includes(item)));
const statusCounts = computed(() => {
  const counts = {};
  for (const obj of props.objects) counts[frameKey(obj)] = (counts[frameKey(obj)] || 0) + 1;
  return counts;
});
const hiddenStatuses = ref([]);
// kaders=geselecteerd,kandidaat the same way, for the statuses of the boxes.
let askedStatuses = new URLSearchParams(window.location.search).has("kaders") ? readAddress(["kaders"]).kaders : null;
const shownStatuses = computed({
  get: () => statusItems.value.filter((item) => !hiddenStatuses.value.includes(item)),
  set: (list) => (hiddenStatuses.value = statusItems.value.filter((item) => !list.includes(item))),
});
watch(shownStatuses, (list) => viewer.value?.setStatusFilter(hiddenStatuses.value.length ? list : null));
// Below the filters it reads (a watch before a const it reads stops the component).
watch(
  statusItems,
  (items) => {
    if (!askedStatuses || !items.length) return;
    hiddenStatuses.value = items.filter((item) => !askedStatuses.includes(item));
    askedStatuses = null;
  },
  { immediate: true }
);
watch([hiddenStatuses, shownStatuses], () => {
  if (askedStatuses) return;
  writeAddress({ kaders: hiddenStatuses.value.length ? (shownStatuses.value.length ? shownStatuses.value : ["-"]) : "" });
});
watch(
  kinds,
  (list) => {
    if (!askedKinds || !list.length) return;
    hiddenKinds.value = list.map(([kind]) => kind).filter((kind) => !askedKinds.includes(kind));
    askedKinds = null;
  },
  { immediate: true }
);
watch([hiddenKinds, shownKinds], () => {
  if (askedKinds) return;
  writeAddress({ maskers: hiddenKinds.value.length ? (shownKinds.value.length ? shownKinds.value : ["-"]) : "" });
});
// Masks, boxes and names on the image: on/off, remembered in this browser.
const SHOW_KEY = "cc-weergave";
const show = reactive({ maskers: true, boxen: true, namen: false, ...readStored(SHOW_KEY, {}, { json: true }) });
watch(
  show,
  () => {
    viewer.value?.setLabels(show.namen);
    writeStored(SHOW_KEY, show, { json: true });
  },
  { deep: true }
);

// Commons thumbnail steps: the viewer starts at 1280 px and swaps in 3840 px when zoomed in.
const SMALL = 1280;
const LARGE = 3840;

function describe(obj) {
  const details = [t(`status.${obj.status}`), t(`source.${obj.bron}`)];
  if (props.newIds.includes(obj.id)) details.unshift(t("legend.nieuw_kort"));
  if (obj.score != null) details.push(`${Math.round(obj.score * 100)}%`);
  if (obj.wikidata) details.push(obj.wikidata);
  // The caption (in quotes) and the description by the AI image description, when there are.
  const title = numbered.value[obj.id] || objectName(obj, language, t);
  const caption = obj.bijschrift?.tekst && obj.bijschrift.tekst !== title ? `“${obj.bijschrift.tekst}”` : "";
  // The AI description in the interface language, else the other one.
  const description = obj.beschrijving && ((language === "en" ? obj.beschrijving.beschrijving_en : obj.beschrijving.beschrijving) || obj.beschrijving.beschrijving || obj.beschrijving.beschrijving_en);
  const text = [caption, description].filter(Boolean).join(" — ");
  return { title, details, text, hint: t("viewer.tooltip_hint") };
}

// The name above an object when names are on (the score is in the tooltip):
// numbered like in the list ("man 1", "man 2") when a name occurs more than once.
const numbered = computed(() => numberedNames(props.objects, language, t));
function label(obj) {
  return numbered.value[obj.id] || objectName(obj, language, t);
}

// "loading" until the browser has the first image of the page; a sharper image swapped in on zooming does not count.
const imageState = ref("loading");
// The classes of the switches, one by one and not with :class: Vue would then rewrite the whole
// class list at every change and wipe what the viewer set on this element itself (the filter
// on kinds and statuses, the fading, the crosshair).
watchEffect(
  () => {
    const el = host.value;
    if (!el) return;
    el.classList.toggle("maskers-verborgen", !show.maskers);
    el.classList.toggle("boxen-verborgen", !show.boxen);
    el.classList.toggle("namen-zichtbaar", show.namen);
    el.classList.toggle("cc-skelet", imageState.value === "loading");
  },
  { flush: "post" }
);

function load() {
  const page = props.page;
  imageState.value = "loading";
  viewer.value.load({
    width: page.breedte,
    height: page.hoogte,
    src: `${page.afbeelding_url}?w=${SMALL}`,
    srcWidth: Math.min(SMALL, page.breedte),
    srcLarge: page.breedte > SMALL ? `${page.afbeelding_url}?w=${Math.min(LARGE, page.breedte)}` : null,
  });
  viewer.value.setObjects(props.objects, props.newIds, props.classColors);
}

onMounted(() => {
  viewer.value = new PageViewer(host.value, { describe, label });
  viewer.value.showLabels = show.namen;
  viewer.value.on("object-click", (e) => emit("object-click", e));
  viewer.value.on("object-open", (obj) => emit("object-open", obj));
  viewer.value.on("object-hover", (obj) => emit("object-hover", obj?.id || null));
  viewer.value.on("point", (e) => emit("point", e));
  viewer.value.on("rectangle", (rect) => emit("rectangle", rect));
  viewer.value.on("zoom", (s) => (scale.value = s));
  viewer.value.on("imageload", () => (imageState.value = "loaded"));
  viewer.value.on("imageerror", () => {
    if (imageState.value === "loading") imageState.value = "error";
  });
  load();
  viewer.value.setPointMode(props.pointMode);
  viewer.value.setDrawMode(props.drawMode);
});

onBeforeUnmount(() => {
  viewer.value?.destroy();
  host.value?.replaceChildren();
});

watch(() => [props.page, props.mid], load);
watch(() => [props.objects, props.newIds, props.classColors], () => viewer.value?.setObjects(props.objects, props.newIds, props.classColors));
watch(() => props.pointMode, (on) => viewer.value?.setPointMode(on));
watch(() => props.drawMode, (on) => viewer.value?.setDrawMode(on));

defineExpose({
  zoomToBox: (box) => viewer.value?.zoomToBox(box),
  focusObject: (id, zoom) => viewer.value?.focusObject(id, zoom),
  setObjectHover: (id, on) => viewer.value?.setObjectHover(id, on),
});
</script>
