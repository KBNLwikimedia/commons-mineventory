<!--
  One image to zoom and pan, as in the main viewer (the same PageViewer module, without
  objects): a toolbar with zoom out/in, the current zoom, a logarithmic slider, "Actual
  size" and "Fit"; the mouse wheel zooms and dragging pans. Used in the magnifier for the
  cut-out and the AI-completed version. The background is a checkerboard, so transparent
  parts show as transparent. An optional overlay image lies exactly over the image.
-->
<template>
  <div class="cc-zoombeeld">
    <div class="cc-viewer-balk" role="toolbar" :aria-label="t('viewer.toolbar')">
      <cdx-button action="progressive" weight="quiet" :aria-label="t('viewer.zoom_out')" @click="viewer?.zoomStep(-1)"><cdx-icon :icon="cdxIconZoomOut" /></cdx-button>
      <span class="cc-zoom" :title="t('viewer.zoom_now')">{{ Math.round(scale * 100) }}%</span>
      <cdx-button action="progressive" weight="quiet" :aria-label="t('viewer.zoom_in')" @click="viewer?.zoomStep(1)"><cdx-icon :icon="cdxIconZoomIn" /></cdx-button>
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
    </div>
    <div ref="host" class="viewer cc-zoombeeld-vlak" :aria-label="alt" role="img"></div>
  </div>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref, shallowRef, watch } from "vue";
import { CdxButton, CdxIcon } from "@wikimedia/codex";
import { cdxIconZoomIn, cdxIconZoomOut } from "@wikimedia/codex-icons";
import { useT } from "../i18n.js";
import { PageViewer } from "../viewer/viewer.js";

const props = defineProps({
  src: { type: String, required: true },
  // The image's own size in pixels (100% = one image pixel per screen pixel).
  width: { type: Number, required: true },
  height: { type: Number, required: true },
  alt: { type: String, default: "" },
  // Optional: an image of the same size laid exactly over it (e.g. what the AI filled in).
  overlay: { type: String, default: "" },
});
const emit = defineEmits(["load", "error"]);
const t = useT();
const host = ref(null);
const viewer = shallowRef(null);
const scale = ref(1);
const ZOOM_MIN_LOG = Math.log2(0.02); // MIN_SCALE in viewer.js
const ZOOM_MAX_LOG = Math.log2(3); // MAX_SCALE in viewer.js
let layer = null;

function load() {
  viewer.value.load({ width: Math.max(1, props.width), height: Math.max(1, props.height), src: props.src, srcWidth: props.width, srcLarge: null });
}

function setOverlay(src) {
  if (!src) {
    layer?.remove();
    layer = null;
    return;
  }
  if (!layer) {
    layer = document.createElement("img");
    layer.className = "cc-zoombeeld-laag";
    layer.alt = "";
    layer.draggable = false;
    viewer.value.stage.append(layer);
  }
  layer.src = src;
}

onMounted(() => {
  viewer.value = new PageViewer(host.value);
  viewer.value.on("zoom", (s) => (scale.value = s));
  viewer.value.on("imageload", () => {
    viewer.value.fit();
    emit("load");
  });
  viewer.value.on("imageerror", () => emit("error"));
  load();
  setOverlay(props.overlay);
});

onBeforeUnmount(() => {
  viewer.value?.destroy();
  host.value?.replaceChildren();
});

watch(() => [props.src, props.width, props.height], () => viewer.value && load());
watch(() => props.overlay, (src) => viewer.value && setOverlay(src));
</script>
