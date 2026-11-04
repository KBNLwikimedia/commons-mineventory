<!--
  A small preview of the cut-out, on a checkerboard so transparency shows
  (magnifier tabs). With `large`, a click opens it big in a lightbox, with
  `texts` beside it to compare (e.g. the text the AI read in the image).
-->
<template>
  <figure class="cc-concept-voorbeeld">
    <button v-if="large" type="button" class="cc-voorbeeld-knop" :title="t('lightbox.open')" :aria-label="t('lightbox.open')" @click="open = true">
      <img :src="src" :alt="caption" />
      <span class="cc-voorbeeld-vergroot" aria-hidden="true"><cdx-icon :icon="cdxIconZoomIn" size="small" /></span>
    </button>
    <img v-else :src="src" :alt="caption" />
    <figcaption class="cc-klein">{{ caption }}<template v-if="large"> · <button type="button" class="cc-link" @click="open = true">{{ t("lightbox.open_short") }}</button></template></figcaption>
    <lightbox v-if="large" v-model:open="open" :src="large" :title="lightboxTitle || caption" :texts="texts" @save-text="emit('save-text', $event)" />
  </figure>
</template>

<script setup>
import { ref } from "vue";
import { CdxIcon } from "@wikimedia/codex";
import { cdxIconZoomIn } from "@wikimedia/codex-icons";
import { useT } from "../i18n.js";
import Lightbox from "./Lightbox.vue";

defineProps({
  src: { type: String, required: true },
  caption: { type: String, required: true },
  large: { type: String, default: "" },
  lightboxTitle: { type: String, default: "" },
  texts: { type: Array, default: () => [] },
});
const emit = defineEmits(["save-text"]);
const t = useT();
const open = ref(false);
</script>
