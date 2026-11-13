<!--
  "Vinkjes selecteren: All · None · Invert" for a set of tick boxes (objects, terms, legend).
  The parent does the ticking: it gets "all", "none" or "invert". The texts are keys
  (objects.* by default, panel.terms_* in the detection panel); `dots` uses the separate
  grey dots of the legend (cc-punt) instead of " · " in the text. The root element (`tag`)
  carries the class of each place, for its CSS.
-->
<template>
  <component :is="tag">
    <template v-if="label">{{ `${label} ` }}</template>
    <button type="button" class="cc-link" :disabled="disabled || disabledAll" :title="titles.all" @click="emit('all')">{{ t(keys.all) }}</button>
    <span v-if="dots" class="cc-punt" aria-hidden="true">·</span>
    <template v-else> · </template>
    <button type="button" class="cc-link" :disabled="disabled || disabledNone" :title="titles.none" @click="emit('none')">{{ t(keys.none) }}</button>
    <span v-if="dots" class="cc-punt" aria-hidden="true">·</span>
    <template v-else> · </template>
    <button type="button" class="cc-link" :disabled="disabled" :title="titles.invert" @click="emit('invert')">{{ t(keys.invert) }}</button>
  </component>
</template>

<script setup>
import { useT } from "../i18n.js";

defineProps({
  tag: { type: String, default: "span" },
  // The text in front of the links ("Vinkjes selecteren:"), if any.
  label: { type: String, default: "" },
  keys: { type: Object, default: () => ({ all: "objects.all", none: "objects.none", invert: "objects.invert" }) },
  // Tooltips per link ({all, none, invert}); none by default.
  titles: { type: Object, default: () => ({}) },
  // All three off (busy), or only All (everything ticked) or None (nothing ticked).
  disabled: { type: Boolean, default: false },
  disabledAll: { type: Boolean, default: false },
  disabledNone: { type: Boolean, default: false },
  dots: { type: Boolean, default: false },
});
const emit = defineEmits(["all", "none", "invert"]);
const t = useT();
</script>
