<!--
  A small (i) button that shows or hides an explanation; the parent places the
  text (v-model:open), so it can sit where there is room.
-->
<template>
  <cdx-button
    action="progressive"
    weight="quiet"
    size="small"
    class="cc-info-knop"
    :aria-label="label"
    :aria-expanded="open ? 'true' : 'false'"
    :title="label"
    @click="emit('update:open', !open)"
  >
    <cdx-icon :icon="cdxIconInfo" size="small" />
  </cdx-button>
</template>

<script setup>
import { CdxButton, CdxIcon } from "@wikimedia/codex";
import { cdxIconInfo } from "@wikimedia/codex-icons";

defineProps({ open: { type: Boolean, default: false }, label: { type: String, required: true } });
const emit = defineEmits(["update:open"]);
</script>
