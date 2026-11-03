<!-- Waiting feedback right where the user clicked: a Codex progress bar and the elapsed seconds. -->
<template>
  <div class="cc-bezig" role="status">
    <cdx-progress-bar :inline="true" :aria-label="text" />
    <p class="cc-klein">{{ text }}</p>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from "vue";
import { CdxProgressBar } from "@wikimedia/codex";
import { useT } from "../i18n.js";

const props = defineProps({ message: { type: String, required: true } });
const t = useT();
const seconds = ref(0);
const timer = setInterval(() => seconds.value++, 1000);
onBeforeUnmount(() => clearInterval(timer));
const text = computed(() => `${props.message} ${t("busy.seconds", { seconds: seconds.value })}`);
</script>
