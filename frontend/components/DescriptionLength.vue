<!--
  Which length of an AI description is shown: the whole image (PageDescription.vue) and a
  cut-out (Magnifier.vue) alike (wish Olaf 17-11-2026). The AI makes all four lengths at once,
  so the slider switches between them for free. Right behind it a switch with the Commons
  logo puts the slider on the Commons caption (at most 250 characters) in one click; off goes
  back to the stop before it.
-->
<template>
  <detail-slider :model-value="modelValue" :disabled="disabled" :levels="LEVELS" :prefix="prefix" compact @update:model-value="emit('update:modelValue', $event)">
    <!-- Without a text of its own: the slider already names the length (wish Olaf 13-11-2026). -->
    <template #after>
      <span class="cc-caption-schakelaar" :title="t('descdetail.caption_help')">
        <cdx-toggle-switch :model-value="modelValue === 'caption'" :disabled="disabled" :aria-label="t('descdetail.caption_switch')" @update:model-value="setCaption" />
        <commons-logo colour />
      </span>
    </template>
  </detail-slider>
</template>

<script setup>
import { CdxToggleSwitch } from "@wikimedia/codex";
import { useT } from "../i18n.js";
import CommonsLogo from "./CommonsLogo.vue";
import DetailSlider from "./DetailSlider.vue";

// The same lengths, in the same order, as DESCRIPTION_LEVELS in cutter/beschrijving.py.
const LEVELS = ["kort", "normaal", "caption", "uitgebreid"];

const props = defineProps({
  modelValue: { type: String, default: "normaal" },
  disabled: { type: Boolean, default: false },
  // The texts of the stops: "descdetail" for the whole image, "objdetail" for a cut-out.
  prefix: { type: String, default: "descdetail" },
});
const emit = defineEmits(["update:modelValue"]);
const t = useT();

let before = props.modelValue === "caption" ? "normaal" : props.modelValue;
function setCaption(on) {
  if (on) {
    if (props.modelValue !== "caption") before = props.modelValue;
    emit("update:modelValue", "caption");
  } else {
    emit("update:modelValue", before === "caption" ? "normaal" : before);
  }
}
</script>
