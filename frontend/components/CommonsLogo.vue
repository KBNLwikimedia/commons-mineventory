<!-- The Wikimedia Commons logo from Codex (a caption belongs to the structured data on Commons;
     wish Olaf). Part of the npm package, so the browser loads nothing from Wikimedia. -->
<template>
  <cdx-icon :icon="cdxIconLogoWikimediaCommons" size="small" class="cc-commons-merkje" />
</template>

<script setup>
import { CdxIcon } from "@wikimedia/codex";
import { cdxIconLogoWikimediaCommons } from "@wikimedia/codex-icons";
</script>
