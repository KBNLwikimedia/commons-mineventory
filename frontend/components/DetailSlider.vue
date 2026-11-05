<!--
  The level of detail for the AI search terms (functional design 7.6): how many kinds
  of objects the AI image description suggests, from the one main subject to many small
  details. A slider with four stops; the chosen stop is shown in words beside it.
-->
<template>
  <div class="cc-schuif">
    <label class="cc-schuif-kop" :for="id">{{ t("detail.label") }}</label>
    <input
      :id="id"
      type="range"
      min="0"
      :max="DETAIL_LEVELS.length - 1"
      step="1"
      :value="index"
      :disabled="disabled"
      :aria-valuetext="t(`detail.${modelValue}`)"
      @input="emit('update:modelValue', DETAIL_LEVELS[Number($event.target.value)])"
    />
    <span class="cc-schuif-waarde">{{ t(`detail.${modelValue}`) }}</span>
    <p class="cc-uitleg">{{ t("detail.help") }}</p>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { useT } from "../i18n.js";

// The same levels, in the same order, as DETAIL_LEVELS in cutter/beschrijving.py.
const DETAIL_LEVELS = ["hoofdonderwerp", "hoofdzaken", "normaal", "details"];

const props = defineProps({
  modelValue: { type: String, default: "normaal" },
  disabled: { type: Boolean, default: false },
});
const emit = defineEmits(["update:modelValue"]);
const t = useT();
const id = `cc-detail-${Math.random().toString(36).slice(2, 8)}`;
const index = computed(() => Math.max(0, DETAIL_LEVELS.indexOf(props.modelValue)));
</script>
