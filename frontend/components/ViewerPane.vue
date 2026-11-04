<!--
  Thin Vue wrapper around the plain-JS viewer (frontend/viewer/viewer.js):
  it mounts the viewer, passes objects in and events out (functional design 10.2).
-->
<template>
  <div class="cc-viewer-kader">
    <div class="cc-viewer-balk" role="toolbar" :aria-label="t('viewer.toolbar')">
      <cdx-button action="progressive" weight="quiet" :aria-label="t('viewer.zoom_out')" @click="viewer?.zoomStep(-1)"><cdx-icon :icon="cdxIconZoomOut" /></cdx-button>
      <span class="cc-zoom">{{ Math.round(scale * 100) }}%</span>
      <cdx-button action="progressive" weight="quiet" :aria-label="t('viewer.zoom_in')" @click="viewer?.zoomStep(1)"><cdx-icon :icon="cdxIconZoomIn" /></cdx-button>
      <cdx-button action="progressive" weight="quiet" @click="viewer?.zoomTo(1)">100%</cdx-button>
      <cdx-button action="progressive" weight="quiet" @click="viewer?.fit()">{{ t("viewer.fit") }}</cdx-button>
      <span class="cc-viewer-hint">{{ drawMode ? t("viewer.hint_draw") : pointMode ? t("viewer.hint_point") : t("viewer.hint") }}</span>
    </div>
    <div ref="host" class="viewer"></div>
  </div>
</template>

<script setup>
import { inject, onBeforeUnmount, onMounted, ref, shallowRef, watch } from "vue";
import { CdxButton, CdxIcon } from "@wikimedia/codex";
import { cdxIconZoomIn, cdxIconZoomOut } from "@wikimedia/codex-icons";
import { useT } from "../i18n.js";
import { objectName } from "../state.js";
import { PageViewer } from "../viewer/viewer.js";

const props = defineProps({
  mid: { type: String, required: true },
  page: { type: Object, required: true },
  objects: { type: Array, required: true },
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

// Commons thumbnail steps: the viewer starts at 1280 px and swaps in 3840 px when zoomed in.
const SMALL = 1280;
const LARGE = 3840;

function describe(obj) {
  const details = [t(`status.${obj.status}`), t(`source.${obj.bron}`)];
  if (obj.score != null) details.push(`${Math.round(obj.score * 100)}%`);
  if (obj.wikidata) details.push(obj.wikidata);
  // The caption (in quotes) and the description by the AI image description, when there are.
  const title = objectName(obj, language, t);
  const caption = obj.bijschrift?.tekst && obj.bijschrift.tekst !== title ? `“${obj.bijschrift.tekst}”` : "";
  // The AI description in the interface language, else the other one.
  const description = obj.beschrijving && ((language === "en" ? obj.beschrijving.beschrijving_en : obj.beschrijving.beschrijving) || obj.beschrijving.beschrijving || obj.beschrijving.beschrijving_en);
  const text = [caption, description].filter(Boolean).join(" — ");
  return { title, details, text, hint: t("viewer.tooltip_hint") };
}

function load() {
  const page = props.page;
  viewer.value.load({
    width: page.breedte,
    height: page.hoogte,
    src: `${page.afbeelding_url}?w=${SMALL}`,
    srcWidth: Math.min(SMALL, page.breedte),
    srcLarge: page.breedte > SMALL ? `${page.afbeelding_url}?w=${Math.min(LARGE, page.breedte)}` : null,
  });
  viewer.value.setObjects(props.objects, props.newIds);
}

onMounted(() => {
  viewer.value = new PageViewer(host.value, { describe });
  viewer.value.on("object-click", (e) => emit("object-click", e));
  viewer.value.on("object-open", (obj) => emit("object-open", obj));
  viewer.value.on("object-hover", (obj) => emit("object-hover", obj?.id || null));
  viewer.value.on("point", (e) => emit("point", e));
  viewer.value.on("rectangle", (rect) => emit("rectangle", rect));
  viewer.value.on("zoom", (s) => (scale.value = s));
  load();
  viewer.value.setPointMode(props.pointMode);
  viewer.value.setDrawMode(props.drawMode);
});

onBeforeUnmount(() => host.value?.replaceChildren());

watch(() => [props.page, props.mid], load);
watch(() => [props.objects, props.newIds], () => viewer.value?.setObjects(props.objects, props.newIds));
watch(() => props.pointMode, (on) => viewer.value?.setPointMode(on));
watch(() => props.drawMode, (on) => viewer.value?.setDrawMode(on));

defineExpose({
  zoomToBox: (box) => viewer.value?.zoomToBox(box),
  focusObject: (id, zoom) => viewer.value?.focusObject(id, zoom),
  setObjectHover: (id, on) => viewer.value?.setObjectHover(id, on),
});
</script>
