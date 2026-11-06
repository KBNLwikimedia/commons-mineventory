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
    <!-- The link says what the large view offers: the image only, or also the text the AI
         read in and around it (to check and correct), or that it read none (to add it). -->
    <figcaption class="cc-klein">{{ caption }}<template v-if="large"> · <button type="button" class="cc-link" :title="linkHelp" @click="open = true">{{ linkText }}</button></template></figcaption>
    <lightbox v-if="large" v-model:open="open" :src="large" :title="lightboxTitle || caption" :texts="texts" @save-text="emit('save-text', $event)" />
  </figure>
</template>

<script setup>
import { computed, ref } from "vue";
import { CdxIcon } from "@wikimedia/codex";
import { cdxIconZoomIn } from "@wikimedia/codex-icons";
import { useT } from "../i18n.js";
import Lightbox from "./Lightbox.vue";

const props = defineProps({
  src: { type: String, required: true },
  caption: { type: String, required: true },
  large: { type: String, default: "" },
  lightboxTitle: { type: String, default: "" },
  texts: { type: Array, default: () => [] },
});
const emit = defineEmits(["save-text"]);
const t = useT();
const open = ref(false);
// Texts the AI read (e.g. a caption printed under the picture); empty fields that can be filled in.
const readCount = computed(() => props.texts.filter((item) => item.text && String(item.text).trim()).length);
const linkText = computed(() =>
  !props.texts.length ? t("lightbox.open_view") : readCount.value ? t("lightbox.open_texts", { n: readCount.value }) : t("lightbox.open_no_text")
);
const linkHelp = computed(() => (!props.texts.length ? t("lightbox.open_view_help") : readCount.value ? t("lightbox.open") : t("lightbox.open_no_text_help")));
</script>
