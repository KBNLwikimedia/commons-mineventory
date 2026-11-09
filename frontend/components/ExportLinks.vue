<!--
  "Export: JSON · CSV · Excel" for the pages that are a list (wish Olaf): links that download what the
  facets and the search show now, from GET …/export. Free; nothing changes.
-->
<template>
  <p class="cc-exporteren">
    <span>{{ filtered ? t("export.label_shown", { n }) : t("export.label") }}</span>
    <template v-for="(format, i) in FORMATS" :key="format">
      <a :href="exportUrl(url, params, format)" download :title="t('export.help')">{{ t(`export.format_${format}`) }}</a><span v-if="i < FORMATS.length - 1" class="cc-punt" aria-hidden="true"> · </span>
    </template>
  </p>
</template>

<script setup>
import { useT } from "../i18n.js";
import { exportUrl } from "../facets.js";

defineProps({
  // The export path, e.g. /api/v1/verbruik/export.
  url: { type: String, required: true },
  // The current choice: {parameter: value or list of values}.
  params: { type: Object, default: () => ({}) },
  // Whether facets or a search limit the list, and to how many.
  filtered: { type: Boolean, default: false },
  n: { type: Number, default: 0 },
});
const FORMATS = ["json", "csv", "xlsx"];
const t = useT();
</script>
