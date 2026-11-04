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
    </h2>
    <p>{{ t(`layout.${column}_intro`) }}</p>
  </header>
</template>

<script setup>
import { computed } from "vue";
import { useT } from "../i18n.js";
import InfoDialog from "./InfoDialog.vue";

const props = defineProps({
  // "left" or "right"
  column: { type: String, required: true },
});
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
