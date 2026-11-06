<!--
  A large view of an image (lightbox), to read and check the text in it: the
  image fitted to the window or at 100% (scroll to move), and beside it the
  texts to compare (for example the text the AI read). A dialog of its own,
  so it also works on top of the magnifier.
-->
<template>
  <cdx-dialog
    :open="open"
    class="cc-lightbox"
    :title="title"
    :use-close-button="true"
    :close-button-label="t('actions.close')"
    @update:open="emit('update:open', $event)"
  >
    <!-- Fit, 100% and a zoom slider; on the image the scroll wheel zooms and dragging moves, as in the main viewer. -->
    <div class="cc-lightbox-balk">
      <cdx-button action="progressive" :weight="mode === 'fit' ? 'primary' : 'normal'" @click="fit">{{ t("lightbox.fit") }}</cdx-button>
      <cdx-button action="progressive" :weight="mode === 'full' ? 'primary' : 'normal'" @click="setZoom(100, 'full')">100%</cdx-button>
      <label class="cc-lightbox-zoom">
        <span class="cc-visually-hidden">{{ t("lightbox.zoom") }}</span>
        <input
          type="range"
          :min="MIN_ZOOM"
          :max="MAX_ZOOM"
          step="5"
          :value="Math.round(zoom)"
          :aria-label="t('lightbox.zoom')"
          :aria-valuetext="`${Math.round(zoom)}%`"
          @input="setZoom(Number($event.target.value), 'custom')"
        />
        <output>{{ Math.round(zoom) }}%</output>
      </label>
      <span class="cc-klein">{{ t("lightbox.zoom_help") }}</span>
    </div>
    <div class="cc-lightbox-inhoud" :class="{ 'met-teksten': visibleTexts.length }">
      <div
        ref="pane"
        class="cc-lightbox-beeld"
        :class="{ 'cc-slepen': dragging }"
        :aria-busy="loading ? 'true' : 'false'"
        @wheel="onWheel"
        @pointerdown="startDrag"
        @pointermove="drag"
        @pointerup="endDrag"
        @pointercancel="endDrag"
      >
        <div v-if="loading" class="cc-beeld-laden" role="status">
          <cdx-progress-bar :inline="true" :aria-label="t('lightbox.loading')" />
          <p class="cc-klein">{{ t("lightbox.loading") }}</p>
        </div>
        <div v-if="failed" class="cc-beeld-laden" role="alert">
          <p>{{ t("lightbox.error") }}</p>
          <cdx-button action="progressive" @click="retry">{{ t("lightbox.retry") }}</cdx-button>
        </div>
        <img
          v-show="!loading && !failed"
          ref="img"
          :src="shownSrc"
          :alt="title"
          :style="imageStyle"
          :class="mode === 'fit' ? 'cc-zoom-in' : 'cc-zoom-out'"
          @load="onLoad"
          @error="onError"
          draggable="false"
          @click="onImageClick"
        />
      </div>
      <aside v-if="visibleTexts.length" class="cc-lightbox-teksten">
        <!-- What these fields are for: the AI may have missed text, which you can add here. -->
        <p v-if="visibleTexts.some((item) => item.key)" class="cc-uitleg cc-lightbox-teksten-uitleg">{{ t("lightbox.texts_help") }}</p>
        <section v-for="item in visibleTexts" :key="item.key || item.label">
          <h3>
            {{ item.label }} <ai-badge v-if="item.ai" kind="beschrijving" :model="item.model || ''" :edited="item.edited" />
            <cdx-button v-if="item.key && editing !== item.key" weight="quiet" action="progressive" size="small" @click="startEdit(item)">
              <cdx-icon :icon="cdxIconEdit" size="small" /> {{ t("lightbox.edit") }}
            </cdx-button>
          </h3>
          <!-- Edit by hand while looking at the image: Opslaan or Annuleren. -->
          <template v-if="editing === item.key">
            <cdx-text-area v-model="draft" :aria-label="item.label" autosize class="cc-lightbox-bewerk" @keydown.esc.stop.prevent="cancelEdit" />
            <div class="cc-knoppen">
              <cdx-button action="progressive" weight="primary" :disabled="draft.trim() === (item.text || '').trim()" @click="saveEdit(item)">{{ t("actions.save_short") }}</cdx-button>
              <cdx-button @click="cancelEdit">{{ t("actions.cancel") }}</cdx-button>
            </div>
          </template>
          <p v-else-if="item.text" class="cc-lightbox-tekst">{{ item.text }}</p>
          <p v-else class="cc-leeg">{{ t("lightbox.no_text") }}</p>
        </section>
      </aside>
    </div>
  </cdx-dialog>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref, watch } from "vue";
import { CdxButton, CdxDialog, CdxIcon, CdxProgressBar, CdxTextArea } from "@wikimedia/codex";
import { cdxIconEdit } from "@wikimedia/codex-icons";
import { fitToText } from "../autosize.js";
import { useT } from "../i18n.js";
import AiBadge from "./AiBadge.vue";

const props = defineProps({
  open: { type: Boolean, default: false },
  src: { type: String, required: true },
  title: { type: String, required: true },
  // [{label, text, ai?, model?, edited?, key?}]: shown beside the image, to compare.
  // With a key the text can be edited here; "save-text" {key, value} goes to the parent.
  texts: { type: Array, default: () => [] },
});
const emit = defineEmits(["update:open", "save-text"]);
const t = useT();
const MIN_ZOOM = 10;
const MAX_ZOOM = 400;
const loading = ref(true);
const failed = ref(false);
const attempt = ref(0);
// A new attempt gets its own URL, so the browser asks again instead of using the failed answer.
const shownSrc = computed(() => (attempt.value ? `${props.src}${props.src.includes("?") ? "&" : "?"}poging=${attempt.value}` : props.src));
const img = ref(null);
function onError() {
  loading.value = false;
  failed.value = true;
}
function retry() {
  failed.value = false;
  loading.value = true;
  attempt.value += 1;
}
const pane = ref(null);
// Zoom in percent of the image's own pixels; mode "fit" follows the window.
const zoom = ref(100);
const mode = ref("fit");
const natural = ref({ width: 0, height: 0 });
const imageStyle = computed(() =>
  natural.value.width ? { width: `${(natural.value.width * zoom.value) / 100}px`, height: "auto", maxWidth: "none", maxHeight: "none" } : {}
);

function fitZoom() {
  const box = pane.value;
  if (!box || !natural.value.width) return 100;
  const scale = Math.min((box.clientWidth - 8) / natural.value.width, (box.clientHeight - 8) / natural.value.height);
  return Math.max(1, Math.min(100, scale * 100));
}

// Zoom around a point of the pane (the mouse pointer; else the middle of what is
// visible), so the part being read stays under it.
async function setZoom(value, newMode, at = null) {
  const box = pane.value;
  const before = zoom.value;
  const next = Math.max(newMode === "fit" ? 1 : MIN_ZOOM, Math.min(MAX_ZOOM, value));
  const point = box ? at || { x: box.clientWidth / 2, y: box.clientHeight / 2 } : null;
  const anchor = box ? { x: (box.scrollLeft + point.x) / before, y: (box.scrollTop + point.y) / before } : null;
  zoom.value = next;
  mode.value = newMode;
  await nextTick();
  if (box && anchor) {
    box.scrollLeft = anchor.x * next - point.x;
    box.scrollTop = anchor.y * next - point.y;
  }
}

function fit() {
  setZoom(fitZoom(), "fit");
}

function onLoad() {
  natural.value = { width: img.value.naturalWidth, height: img.value.naturalHeight };
  loading.value = false;
  nextTick(fit);
}

// The scroll wheel zooms around the mouse pointer, as in the main viewer.
function onWheel(event) {
  if (loading.value) return;
  event.preventDefault();
  const rect = pane.value.getBoundingClientRect();
  setZoom(zoom.value * (event.deltaY < 0 ? 1.15 : 1 / 1.15), "custom", { x: event.clientX - rect.left, y: event.clientY - rect.top });
}

// Dragging moves the image; a click without moving switches between 100% and fit.
const dragging = ref(false);
let start = null;
let moved = false;
function startDrag(event) {
  if (event.button !== 0 || loading.value) return;
  start = { x: event.clientX, y: event.clientY, left: pane.value.scrollLeft, top: pane.value.scrollTop };
  moved = false;
}
function drag(event) {
  if (!start) return;
  const dx = event.clientX - start.x;
  const dy = event.clientY - start.y;
  if (!moved && Math.hypot(dx, dy) < 4) return;
  if (!moved) pane.value.setPointerCapture?.(event.pointerId);
  moved = true;
  dragging.value = true;
  pane.value.scrollLeft = start.left - dx;
  pane.value.scrollTop = start.top - dy;
}
function endDrag() {
  start = null;
  dragging.value = false;
}
function onImageClick(event) {
  if (moved) return;
  const rect = pane.value.getBoundingClientRect();
  const at = { x: event.clientX - rect.left, y: event.clientY - rect.top };
  if (mode.value === "fit") setZoom(100, "full", at);
  else fit();
}

// The window changes size: a fitted image fits again.
let observer = null;
watch(pane, (element) => {
  observer?.disconnect();
  if (element && typeof ResizeObserver !== "undefined") {
    observer = new ResizeObserver(() => mode.value === "fit" && natural.value.width && fit());
    observer.observe(element);
  }
});
onBeforeUnmount(() => observer?.disconnect());
const visibleTexts = computed(() => props.texts.filter((item) => item.key || (item.text && String(item.text).trim())));

// Editing one text at a time.
const editing = ref(null);
const draft = ref("");
async function startEdit(item) {
  editing.value = item.key;
  draft.value = item.text || "";
  // As high as the text in it (autosize only reacts once you type); long texts scroll.
  await nextTick();
  const area = document.querySelector(".cc-lightbox-bewerk textarea");
  fitToText(area);
  area?.focus();
}
function cancelEdit() {
  editing.value = null;
  draft.value = "";
}
function saveEdit(item) {
  emit("save-text", { key: item.key, value: draft.value.trim() });
  cancelEdit();
}
watch(
  () => [props.open, props.src],
  async ([open]) => {
    if (!open) return;
    loading.value = true;
    failed.value = false;
    await nextTick();
    // From the browser cache the load event may already have passed.
    if (img.value?.complete && img.value.naturalWidth) onLoad();
  }
);
</script>
