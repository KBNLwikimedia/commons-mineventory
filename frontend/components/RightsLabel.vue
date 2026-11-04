<!--
  A rights label (functional design 5.3) as a Codex info chip, in the same
  style as the licence chip, with the explanation in a tooltip.
-->
<template>
  <span v-tooltip="t(`rights_help.${label}`)" class="cc-rechtenlabel" tabindex="0" role="note" :aria-label="`${t(`rights.${label}`)}: ${t(`rights_help.${label}`)}`">
    <cdx-info-chip :status="status">{{ t(`rights.${label}`) }}</cdx-info-chip>
  </span>
</template>

<script setup>
import { computed } from "vue";
import { CdxInfoChip, CdxTooltip } from "@wikimedia/codex";
import { useT } from "../i18n.js";

const props = defineProps({ label: { type: String, required: true } });
const t = useT();
const vTooltip = CdxTooltip;

// The chip's colour follows how serious the label is.
const STATUS = {
  in_orde: "success",
  naamsvermelding: "notice",
  merk: "warning",
  persoonlijkheidsrechten: "warning",
  alleen_vs: "warning",
  ter_discussie: "error",
};
const status = computed(() => STATUS[props.label] || "notice");
</script>
