<!--
  The header of a column of the workspace: a title with an (i) button and one
  short line on what happens in the column. The (i) opens a popup that lists
  what the column can do. Texts come from layout.<column>_* in the i18n files.
-->
<template>
  <header class="cc-kolomkop">
    <h2>
      {{ t(`layout.${column}_title`) }}
      <info-dialog :title="t(`layout.${column}_title`)" :label="t('panel.info_label', { section: t(`layout.${column}_title`) })" :paragraphs="paragraphs" />
      <!-- Fold the column away (to a narrow strip). -->
      <cdx-button v-if="closable" weight="quiet" size="small" class="cc-kolom-dicht-knop" :aria-label="t('layout.column_close', { name: t(`layout.${column}_title`) })" :title="t('layout.column_close', { name: t(`layout.${column}_title`) })" @click="emit('close')">
        <cdx-icon :icon="side === 'left' ? cdxIconPrevious : cdxIconNext" size="small" />
      </cdx-button>
    </h2>
    <p>{{ t(`layout.${column}_intro`) }}</p>
  </header>
</template>

<script setup>
import { computed } from "vue";
import { CdxButton, CdxIcon } from "@wikimedia/codex";
import { cdxIconNext, cdxIconPrevious } from "@wikimedia/codex-icons";
import { useT } from "../i18n.js";
import InfoDialog from "./InfoDialog.vue";

const props = defineProps({
  // "left" or "right"
  column: { type: String, required: true },
  // With a button to fold the column away, to the left or to the right.
  closable: { type: Boolean, default: false },
  side: { type: String, default: "left" },
});
const emit = defineEmits(["close"]);
const t = useT();
// layout.<column>_info_1, _2, … as far as they exist.
const paragraphs = computed(() => {
  const result = [];
  for (let n = 1; n <= 9; n++) {
    const key = `layout.${props.column}_info_${n}`;
    const text = t(key);
    if (text === key) break;
    result.push(text);
  }
  return result;
});
</script>
