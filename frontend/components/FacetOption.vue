<!-- One value of a facet on the list pages (ListFacets.vue): a checkbox with its name and number. -->
<template>
  <cdx-checkbox :model-value="modelValue" :input-value="option.value" :class="{ 'cc-facet-met-duim': option.image }" @update:model-value="emit('update:modelValue', $event)">
    <span v-if="option.image" class="cc-facet-duim"><img :src="option.image" alt="" loading="lazy" /></span>
    <span :class="{ 'cc-afkappen cc-facet-bestand': option.image }" :title="option.label || option.value">{{ option.label || option.value }}</span> ({{ option.n }})
    <span v-if="option.description" class="cc-facet-uitleg">{{ option.description }}</span>
  </cdx-checkbox>
</template>

<script setup>
import { CdxCheckbox } from "@wikimedia/codex";

defineProps({
  // {value, label?, n, image?, description?}
  option: { type: Object, required: true },
  // The chosen values of this facet.
  modelValue: { type: Array, required: true },
});
const emit = defineEmits(["update:modelValue"]);
</script>
