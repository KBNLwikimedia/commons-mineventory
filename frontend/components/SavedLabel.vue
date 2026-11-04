<!--
  "opgeslagen, nog 23 dagen" for a saved cut-out (retention, functional design
  12.1): the period in italics, orange in the last week, the date in the tooltip.
-->
<template>
  <span v-if="info" class="cc-opgeslagen-label" :title="info.title">
    {{ info.text }}<template v-if="info.left">, <em class="cc-verloopt" :class="{ 'cc-verloopt-bijna': info.soon }">{{ info.left }}</em></template>
  </span>
</template>

<script setup>
import { computed, inject } from "vue";
import { useT } from "../i18n.js";
import { savedLabel } from "../state.js";

const props = defineProps({ object: { type: Object, required: true } });
const t = useT();
const language = inject("language", "nl");
const info = computed(() => savedLabel(props.object, t, language));
</script>
