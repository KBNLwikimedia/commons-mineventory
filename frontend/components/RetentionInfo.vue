<!--
  An (i) with a popup about how long the app keeps things (functional design
  12.1): not everything is kept forever. The periods come from the server.
-->
<template>
  <info-dialog :title="t('retention.title')" :label="t('retention.title')" :paragraphs="paragraphs" />
</template>

<script setup>
import { computed, inject } from "vue";
import { useT } from "../i18n.js";
import InfoDialog from "./InfoDialog.vue";

const t = useT();
const config = inject("config");
const paragraphs = computed(() => {
  const days = config.bewaren || { originelen: 7, uitsneden: 30, cache: 365 };
  return [
    t("retention.intro"),
    t("terms.objects_cutouts"),
    t("retention.cutouts", { n: days.uitsneden }),
    t("retention.cache", { n: days.cache }),
    t("retention.originals", { n: days.originelen }),
    t("retention.keep"),
  ];
});
</script>
