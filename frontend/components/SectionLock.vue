<!--
  The lock pin in the title of a section of the detection panel (wish Olaf, 12-11-2026):
  locked, the section stays open or closed as it was, also after loading the app again.
  It sits inside the <summary>, so its click must not fold the section.
-->
<template>
  <button
    type="button"
    class="cc-slot"
    :class="{ vast: locked }"
    :aria-pressed="locked"
    :aria-label="label"
    :title="label"
    @click.stop.prevent="emit('toggle')"
  >
    <cdx-icon :icon="locked ? cdxIconLock : cdxIconUnLock" size="small" />
  </button>
</template>

<script setup>
import { CdxIcon } from "@wikimedia/codex";
import { cdxIconLock, cdxIconUnLock } from "@wikimedia/codex-icons";

defineProps({
  locked: { type: Boolean, default: false },
  label: { type: String, required: true },
});
const emit = defineEmits(["toggle"]);
</script>
