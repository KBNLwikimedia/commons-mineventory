<!--
  "Per kind:" in the bulk tabs (describe, group, trash): one link per search term with its count,
  for the visible objects of that kind. `price(n)` adds the amount (describe is paid); `remove`
  colours the links as a removal (trash).
-->
<template>
  <p v-if="items.length" class="cc-groeperen">
    {{ t("bulk.per_kind") }}
    <template v-for="(item, i) in items" :key="item.term">
      <template v-if="i"> · </template>
      <button type="button" class="cc-link" :class="{ 'cc-link-weg': remove }" :disabled="disabled" :title="help" @click="emit('pick', item.term)">
        {{ t("panel.group_all", { term: item.name, n: item.n }) }} <span v-if="price" class="cc-kosten">{{ price(item.n) }}</span>
      </button>
    </template>
  </p>
</template>

<script setup>
import { useT } from "../i18n.js";

defineProps({
  // [{term, name, n}], as kindsOf() gives them.
  items: { type: Array, required: true },
  help: { type: String, default: "" },
  disabled: { type: Boolean, default: false },
  price: { type: Function, default: null },
  remove: { type: Boolean, default: false },
});
const emit = defineEmits(["pick"]);
const t = useT();
</script>
