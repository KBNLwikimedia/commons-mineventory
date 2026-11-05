<!-- The small pencil after a text: edit that text in place (as in the magnifier). -->
<template>
  <cdx-button
    class="cc-veld-potlood"
    weight="quiet"
    action="progressive"
    size="small"
    :disabled="disabled"
    :aria-label="`${t('lightbox.edit')}: ${label}`"
    :title="`${t('lightbox.edit')}: ${label}`"
    @click="emit('click')"
  >
    <cdx-icon :icon="cdxIconEdit" size="small" />
  </cdx-button>
</template>

<script setup>
import { CdxButton, CdxIcon } from "@wikimedia/codex";
import { cdxIconEdit } from "@wikimedia/codex-icons";
import { useT } from "../i18n.js";

defineProps({
  label: { type: String, required: true },
  disabled: { type: Boolean, default: false },
});
const emit = defineEmits(["click"]);
const t = useT();
</script>
