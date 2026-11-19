<!-- Where a value in the Commons concept comes from: the wikitext, the SDC, or the work's Wikidata item. -->
<template>
  <span v-if="source.bron === 'wikidata'">
    {{ t("origin.wikidata") }}
    <qid-link :q="source.item" />,
    <template v-if="source.eigenschap === 'onbekend'">{{ t("origin.unknown") }}</template>
    <a v-else :href="`https://www.wikidata.org/wiki/Property:${source.eigenschap}`" target="_blank" rel="noopener">{{ source.eigenschap }}</a>.
  </span>
  <span v-else-if="source.bron === 'sdc'">{{ t("origin.sdc", { property: source.eigenschap }) }}</span>
  <span v-else>{{ t("origin.wikitekst") }}</span>
</template>

<script setup>
import { useT } from "../i18n.js";
import QidLink from "./QidLink.vue";

defineProps({ source: { type: Object, required: true } });
const t = useT();
</script>
