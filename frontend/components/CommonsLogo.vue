<!-- The Wikimedia Commons logo from Codex (a caption belongs to the structured data on Commons;
     wish Olaf). Part of the npm package, so the browser loads nothing from Wikimedia. -->
<template>
  <!-- In colour (blue and red, as static/img/commons.svg), e.g. beside the caption switch (wish Olaf). -->
  <svg v-if="colour" class="cc-commons-merkje cc-commons-kleur" viewBox="0 0 20 20" aria-hidden="true">
    <path fill="#069" d="M13.09 6.18a3.68 3.68 0 01-2.18-2.55c.09.09 1.82.91 1.82.91L10 0 7.27 4.55l1.82-.91a5.1 5.1 0 00.55 1.91 5.13 5.13 0 002 2 9 9 0 012 1.18l-.64.63-.45-.45-.26 1.54 1.54-.26-.45-.45.62-.65a5.7 5.7 0 011.45 3.45h-.91v-.73l-1.26.91 1.26.91v-.73h.91A5.2 5.2 0 0114 16.36l-.64-.64.45-.45-1.53-.27.26 1.54.45-.45.64.64a5.7 5.7 0 01-3.45 1.45v-.91h.73L10 16l-.91 1.27h.73v.91a5.2 5.2 0 01-3.45-1.45l.63-.64.45.45.27-1.54-1.54.26.45.45-.63.65a5.7 5.7 0 01-1.45-3.45h.91v.73l1.26-.91-1.26-.91v.73h-.91A5.2 5.2 0 016 9.09l.64.64-.45.45 1.54.26-.28-1.53-.45.45-.64-.64L5 7.45a7.29 7.29 0 108.09-1.27" />
    <circle fill="#900" cx="10" cy="12.7" r="2.5" />
  </svg>
  <cdx-icon v-else :icon="cdxIconLogoWikimediaCommons" size="small" class="cc-commons-merkje" />
</template>

<script setup>
import { CdxIcon } from "@wikimedia/codex";
import { cdxIconLogoWikimediaCommons } from "@wikimedia/codex-icons";

defineProps({ colour: { type: Boolean, default: false } });
</script>
