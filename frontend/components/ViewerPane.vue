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
    <!-- What the colours of the frames mean: only with the boxes shown, folded away by default. -->
    <cdx-accordion v-if="show.boxen && legend.length" class="cc-legenda-blok">
      <template #title>{{ t("legend.title") }}</template>
      <ul class="cc-legenda">
        <li v-for="item in legend" :key="item"><span :class="['cc-legenda-staal', `cc-legenda-${item}`]"></span>{{ t(`legend.${item}`) }}</li>
        <li><info-dialog :title="t('legend.info_title')" :label="t('legend.info_label')" :paragraphs="colourInfo" /></li>
      </ul>
    </cdx-accordion>
    <!-- A colour per kind of object, each a checkbox: ticked kinds are shown (all to start
         with), with All · None · Invert as in the object list (wish Olaf). Only with the masks shown. -->
    <ul v-if="show.maskers && kinds.length" class="cc-legenda cc-legenda-soorten">
      <!-- What the colour of the masks shows: the kind (default) or, as the frames, the status. -->
      <li class="cc-maskers-kleur">
        <!-- What every colour means, the masks, by kind / by status and Show only (wish Olaf). -->
        <info-dialog :title="t('legend.info_title')" :label="t('legend.info_label')" :paragraphs="colourInfo" />
        <span class="cc-legenda-soorten-kop">{{ t("legend.masks_by") }}</span>
        <cdx-toggle-button-group v-model="maskColoringModel" :buttons="maskColorings" :aria-label="t('legend.masks_by')" />
      </li>
      <li class="cc-legenda-soorten-kop">{{ t("legend.kinds") }}</li>
      <li v-for="[kind, color] in kinds" :key="kind">
        <cdx-checkbox v-model="shownKinds" :input-value="kind" :inline="true" class="cc-soort-vinkje" :title="t('legend.kind_only', { kind })">
          <span v-if="byKind" class="cc-klasse-stip" :style="{ background: color }"></span>{{ kind }}
        </cdx-checkbox>
      </li>
      <li class="cc-soorten-alles">
        <button type="button" class="cc-link" :disabled="!hiddenKinds.length" @click="hiddenKinds = []">{{ t("objects.all") }}</button>
        ·
        <button type="button" class="cc-link" :disabled="hiddenKinds.length === kinds.length" @click="hiddenKinds = kinds.map(([kind]) => kind)">{{ t("objects.none") }}</button>
        ·
        <button type="button" class="cc-link" @click="hiddenKinds = shownKinds">{{ t("objects.invert") }}</button>
      </li>
    </ul>
    <div class="cc-viewer-vlak">
      <div ref="host" class="viewer" :class="{ 'maskers-verborgen': !show.maskers, 'boxen-verborgen': !show.boxen, 'namen-zichtbaar': show.namen, 'cc-skelet': imageState === 'loading' }" :aria-busy="imageState === 'loading' ? 'true' : 'false'"></div>
      <!-- Waiting feedback while the image comes in: the first time, the server fetches the original from Commons. -->
      <busy-note v-if="imageState === 'loading'" class="cc-viewer-laden" :message="t('viewer.loading')" />
      <cdx-message v-else-if="imageState === 'error'" type="error" class="cc-viewer-laden">{{ t("viewer.load_error") }}</cdx-message>
    </div>
  </div>
</template>

<script setup>
import { computed, inject, onBeforeUnmount, onMounted, reactive, ref, shallowRef, watch } from "vue";
import { CdxAccordion, CdxButton, CdxCheckbox, CdxIcon, CdxMessage, CdxToggleButtonGroup } from "@wikimedia/codex";
import { cdxIconZoomIn, cdxIconZoomOut } from "@wikimedia/codex-icons";
import { useT } from "../i18n.js";
import { numberedNames, objectName } from "../state.js";
import { PageViewer } from "../viewer/viewer.js";
import BusyNote from "./BusyNote.vue";
import InfoDialog from "./InfoDialog.vue";

const props = defineProps({
  mid: { type: String, required: true },
  page: { type: Object, required: true },
  objects: { type: Array, required: true },
  // {kind: colour} when the page has more than one kind of object (class-colors.js).
  classColors: { type: Object, default: () => ({}) },
  // What the colour of the masks shows: "soort" (the kind) or "status" (as the frames).
  maskColoring: { type: String, default: "soort" },
  newIds: { type: Array, default: () => [] },
  pointMode: { type: Boolean, default: false },
  drawMode: { type: Boolean, default: false },
});
const emit = defineEmits(["object-click", "object-open", "object-hover", "point", "rectangle", "update:maskColoring"]);
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
const kinds = computed(() => Object.entries(props.classColors || {}));
const colourInfo = computed(() => [1, 2, 3, 4, 5, 6].map((i) => t(`legend.info_${i}`)));
const maskColoringModel = computed({ get: () => props.maskColoring, set: (value) => emit("update:maskColoring", value) });
const byKind = computed(() => props.maskColoring !== "status");
const maskColorings = computed(() => [
  { value: "soort", label: t("legend.by_kind") },
  { value: "status", label: t("legend.by_status") },
]);
// The colours the viewer uses for the masks: per kind, or none (then the colour of the status).
const shownColors = computed(() => (byKind.value ? props.classColors : {}));
// The kinds you unticked: their objects fade. Kept as the hidden ones, so a kind found later
// shows (ticked) at once. A kind that is gone is dropped.
const hiddenKinds = ref([]);
const shownKinds = computed({
  get: () => kinds.value.map(([kind]) => kind).filter((kind) => !hiddenKinds.value.includes(kind)),
  set: (list) => (hiddenKinds.value = kinds.value.map(([kind]) => kind).filter((kind) => !list.includes(kind))),
});
// To the viewer: null when nothing is hidden (no filter), else the kinds to show.
watch(shownKinds, (list) => viewer.value?.setKindFilter(hiddenKinds.value.length ? list : null));
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
// Masks, boxes and names on the image: on/off, remembered in this browser.
const SHOW_KEY = "cc-weergave";
function storedShow() {
  try {
    return JSON.parse(window.localStorage.getItem(SHOW_KEY) || "{}");
  } catch {
    return {};
  }
}
const show = reactive({ maskers: true, boxen: true, namen: false, ...storedShow() });
watch(
  show,
  () => {
    viewer.value?.setLabels(show.namen);
    try {
      window.localStorage.setItem(SHOW_KEY, JSON.stringify(show));
    } catch {
      // Blocked storage: the choice is simply not remembered.
    }
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
  viewer.value.setObjects(props.objects, props.newIds, shownColors.value);
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
watch(() => [props.objects, props.newIds, shownColors.value], () => viewer.value?.setObjects(props.objects, props.newIds, shownColors.value));
watch(() => props.pointMode, (on) => viewer.value?.setPointMode(on));
watch(() => props.drawMode, (on) => viewer.value?.setDrawMode(on));

defineExpose({
  zoomToBox: (box) => viewer.value?.zoomToBox(box),
  focusObject: (id, zoom) => viewer.value?.focusObject(id, zoom),
  setObjectHover: (id, on) => viewer.value?.setObjectHover(id, on),
});
</script>
