<!--
  The level of detail for the AI search terms (functional design 7.6): how many kinds
  of objects the AI image description suggests, from the one main subject to many small
  details. A slider with four stops; the chosen stop is shown in words beside it.
-->
<template>
  <div class="cc-schuif" :class="{ 'cc-schuif-compact': compact }" :title="compact ? t(`${prefix}.help`) : undefined">
    <label class="cc-schuif-kop" :for="id">{{ t(`${prefix}.label`) }}</label>
    <input
      :id="id"
      type="range"
      min="0"
      :max="levels.length - 1"
      step="1"
      :value="index"
      :disabled="disabled"
      :aria-valuetext="t(`${prefix}.${modelValue}`)"
      @input="emit('update:modelValue', levels[Number($event.target.value)])"
    />
    <span class="cc-schuif-waarde">{{ t(`${prefix}.${modelValue}`) }}</span>
    <!-- Compact (above the search terms): the explanation is the tooltip instead. -->
    <p v-if="!compact" class="cc-uitleg">{{ t(`${prefix}.help`) }}</p>
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
  compact: { type: Boolean, default: false },
  // Other levels and texts: e.g. the length of the description (prefix "descdetail").
  // (A literal list: defineProps cannot use a variable of the component.)
  levels: { type: Array, default: () => ["hoofdonderwerp", "hoofdzaken", "normaal", "details"] },
  prefix: { type: String, default: "detail" },
});
const emit = defineEmits(["update:modelValue"]);
const t = useT();
const id = `cc-detail-${Math.random().toString(36).slice(2, 8)}`;
const index = computed(() => Math.max(0, props.levels.indexOf(props.modelValue)));
</script>
