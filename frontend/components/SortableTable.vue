<!--
  A table whose columns sort with a click on their heading (wish Olaf): first ascending, then
  descending. Until you click, the rows stay in the order they came in. A cell can be filled with a
  slot named after its column.
-->
<template>
  <table class="cc-tabel cc-sorteerbaar">
    <thead>
      <tr>
        <th v-for="column in columns" :key="column.key" :class="{ getal: column.numeric }" :aria-sort="ariaSort(column)">
          <button v-if="column.value" type="button" class="cc-sorteer" :title="t('table.sort_by', { column: column.label })" @click="sortBy(column)">
            {{ column.label }}<span class="cc-sorteer-pijl" aria-hidden="true">{{ arrow(column) }}</span>
          </button>
          <template v-else>{{ column.label }}</template>
        </th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="(row, i) in sorted" :key="rowKey ? rowKey(row) : i">
        <td v-for="column in columns" :key="column.key" :class="{ getal: column.numeric }">
          <slot :name="column.key" :row="row">{{ column.value?.(row) }}</slot>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { useT } from "../i18n.js";
import { sortRows } from "../facets.js";

const props = defineProps({
  // [{key, label, value?: (row) => what it shows and sorts on, numeric?}]; no value: not sortable.
  columns: { type: Array, required: true },
  rows: { type: Array, required: true },
  rowKey: { type: Function, default: null },
});
const emit = defineEmits(["sorted"]);
const t = useT();

const sortKey = ref(null);
const direction = ref(1);

function sortBy(column) {
  if (sortKey.value === column.key) direction.value = -direction.value;
  else {
    sortKey.value = column.key;
    direction.value = 1;
  }
}

const sorted = computed(() => {
  const column = props.columns.find((c) => c.key === sortKey.value);
  return column ? sortRows(props.rows, column.value, direction.value) : props.rows;
});
// The order on screen, for ‹ › in the magnifier.
watch(sorted, (rows) => emit("sorted", rows), { immediate: true });

const ariaSort = (column) => (sortKey.value === column.key ? (direction.value > 0 ? "ascending" : "descending") : undefined);
const arrow = (column) => (sortKey.value === column.key ? (direction.value > 0 ? "▲" : "▼") : "");
</script>
