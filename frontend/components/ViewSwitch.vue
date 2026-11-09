<!-- A choice between two views of a list (wish Olaf), remembered in this browser. -->
<template>
  <cdx-toggle-button-group class="cc-weergave" :model-value="modelValue" :buttons="buttons" @update:model-value="choose" />
</template>

<script setup>
import { onMounted } from "vue";
import { CdxToggleButtonGroup } from "@wikimedia/codex";

const props = defineProps({
  modelValue: { type: String, required: true },
  // [{value, label}]
  buttons: { type: Array, required: true },
  storageKey: { type: String, required: true },
});
const emit = defineEmits(["update:modelValue"]);

function choose(value) {
  emit("update:modelValue", value);
  try {
    localStorage.setItem(props.storageKey, value);
  } catch {
    // Storage can be off in a private window; the choice then lasts as long as the page.
  }
}

onMounted(() => {
  let stored = null;
  try {
    stored = localStorage.getItem(props.storageKey);
  } catch {
    return;
  }
  if (stored && props.buttons.some((button) => button.value === stored)) emit("update:modelValue", stored);
});
</script>
