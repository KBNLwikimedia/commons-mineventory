<!--
  A row of numbered steps (wish Olaf 13-11-2026: "Naar Commons" step by step). Each step can
  be clicked; the current one is marked (aria-current="step"), earlier ones as done. A count
  after a label says how many changes that step has. Generic: the parent gives the steps.
-->
<template>
  <ol class="cc-stappen" :aria-label="label">
    <li v-for="(step, i) in steps" :key="step.key">
      <button
        type="button"
        class="cc-stap"
        :class="{ 'cc-stap-actief': step.key === modelValue, 'cc-stap-gedaan': i < current }"
        :aria-current="step.key === modelValue ? 'step' : undefined"
        @click="emit('update:modelValue', step.key)"
      >
        <span class="cc-stap-nummer">{{ i + 1 }}</span>
        <span class="cc-stap-naam">{{ step.label }}</span>
        <span v-if="step.count" class="cc-stap-aantal" :title="step.countTitle">{{ step.count }}</span>
      </button>
    </li>
  </ol>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  // [{ key, label, count?, countTitle? }]
  steps: { type: Array, required: true },
  modelValue: { type: String, required: true },
  label: { type: String, default: "" },
});
const emit = defineEmits(["update:modelValue"]);
const current = computed(() => props.steps.findIndex((step) => step.key === props.modelValue));
</script>
