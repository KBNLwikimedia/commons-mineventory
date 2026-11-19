<!--
  A Q-id as a link to its item on Wikidata, in a new tab (wish Olaf 19-11-2026): every place in
  the app that shows a Q-id uses this, so it is always clickable and looks the same.
-->
<template>
  <a v-if="/^Q\d+$/.test(q)" class="cc-qid-link" :href="`https://www.wikidata.org/wiki/${q}`" target="_blank" rel="noopener" :title="t('wikidata.open_item', { q })">{{ q }}</a>
  <template v-else>{{ q }}</template>
</template>

<script setup>
import { useT } from "../i18n.js";

defineProps({ q: { type: String, default: "" } });
const t = useT();
</script>
