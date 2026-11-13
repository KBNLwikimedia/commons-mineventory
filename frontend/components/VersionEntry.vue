<!--
  One earlier version in a VersionCarousel (object description, page description): its
  labelled fields (cc-versie-veld, in the slot), when and how it was made (`meta`), and
  "More"/"Less". A click or Enter/Space unfolds it; folded, the whole text (`title`) is the
  tooltip. The parent keeps which versions are unfolded (v-model:open), so a version stays
  unfolded when you page away and back.
-->
<template>
  <div
    class="cc-geschiedenis-tekstblok"
    :class="{ open }"
    role="button"
    tabindex="0"
    :aria-expanded="open ? 'true' : 'false'"
    :title="open ? '' : title"
    @click="emit('update:open', !open)"
    @keydown.enter.space.prevent="emit('update:open', !open)"
  >
    <slot />
    <span class="cc-klein cc-geschiedenis-meta">{{ meta }}</span>
    <span class="cc-link cc-klein cc-geschiedenis-meer">{{ open ? t("describe.history_less") : t("describe.history_more") }}</span>
  </div>
</template>

<script setup>
import { useT } from "../i18n.js";

defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: "" },
  meta: { type: String, default: "" },
});
const emit = defineEmits(["update:open"]);
const t = useT();
</script>
