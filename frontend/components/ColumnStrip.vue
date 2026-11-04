<!--
  A column of the workspace folded away: a narrow strip with its name (written
  upwards) and an arrow. A click opens the column again.
-->
<template>
  <cdx-button weight="quiet" class="cc-kolom-strook" :aria-label="t('layout.column_open', { name })" :title="t('layout.column_open', { name })" @click="emit('open')">
    <cdx-icon :icon="side === 'left' ? cdxIconNext : cdxIconPrevious" />
    <span class="cc-kolom-strook-tekst">{{ name }}<template v-if="count != null"> ({{ count }})</template></span>
  </cdx-button>
</template>

<script setup>
import { CdxButton, CdxIcon } from "@wikimedia/codex";
import { cdxIconNext, cdxIconPrevious } from "@wikimedia/codex-icons";
import { useT } from "../i18n.js";

defineProps({
  name: { type: String, required: true },
  count: { type: Number, default: null },
  // Which side the column folds to: "left" (the arrow to open points right) or "right".
  side: { type: String, default: "left" },
});
const emit = defineEmits(["open"]);
const t = useT();
</script>
