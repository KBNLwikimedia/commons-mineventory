<!--
  "Bekeken": the files opened in this browser, in two areas. On top the active
  ones; below, under a header that folds, the ones set aside ("Opzij gezet").
  The bin of an active entry sets it aside; drag a row to the other area to
  move it there. Opening a file again brings it back to the active area.
-->
<template>
  <div class="cc-bekeken">
    <div
      class="cc-sleepvak"
      :class="{ erboven: over === 'actief' }"
      @dragover="dragOver($event, 'actief')"
      @dragleave="dragLeave($event, 'actief')"
      @drop="drop($event, false)"
    >
      <history-list v-if="active.length" :entries="active" :current="current" @aside="emit('aside', $event, true)" @open="emit('open', $event)" @start-over="emit('start-over', $event)" :work="work" />
      <p v-else class="cc-uitleg">{{ t(asideEntries.length ? "history.all_aside" : "layout.history_empty") }}</p>
    </div>
    <div
      class="cc-sleepvak cc-opzij"
      :class="{ erboven: over === 'opzij' }"
      @dragover="dragOver($event, 'opzij')"
      @dragleave="dragLeave($event, 'opzij')"
      @drop="drop($event, true)"
    >
      <cdx-accordion v-model="asideOpen">
        <template #title>{{ t("history.aside_title") }} <small>({{ asideEntries.length }})</small></template>
        <p class="cc-uitleg">{{ t("history.aside_help") }}</p>
        <history-list
          v-if="asideEntries.length"
          :entries="asideEntries"
          :current="current"
          aside
          @restore="emit('aside', $event, false)"
          @remove="emit('remove', $event)"
          @open="emit('open', $event)"
        />
      </cdx-accordion>
    </div>
    <button v-if="entries.length" type="button" class="cc-link cc-klein" @click="emit('clear')">{{ t("history.clear") }}</button>
  </div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { CdxAccordion } from "@wikimedia/codex";
import { useT } from "../i18n.js";
import { DRAG_TYPE } from "../state.js";
import HistoryList from "./HistoryList.vue";

const props = defineProps({
  // {mid: whether anything is kept for that image}, for ↻.
  work: { type: Object, default: () => ({}) },
  entries: { type: Array, required: true },
  current: { type: String, default: null },
});
// aside(mid, true|false), remove(mid), clear()
const emit = defineEmits(["aside", "remove", "clear", "open", "start-over"]);
const t = useT();

const active = computed(() => props.entries.filter((e) => !e.opzij));
const asideEntries = computed(() => props.entries.filter((e) => e.opzij));

// The folding header of "Opzij gezet": remembered in this browser.
const OPEN_KEY = "cc-opzij-open";
const asideOpen = ref(false);
try {
  asideOpen.value = window.localStorage.getItem(OPEN_KEY) === "1";
} catch {
  // Blocked storage: folded.
}
watch(asideOpen, (open) => {
  try {
    window.localStorage.setItem(OPEN_KEY, open ? "1" : "0");
  } catch {
    // Blocked storage: the choice holds until the page is reloaded.
  }
});

// Drag and drop: only rows of this list (their M-id), highlighted while above an area.
const over = ref(null);
const carries = (event) => [...(event.dataTransfer?.types || [])].includes(DRAG_TYPE);
function dragOver(event, area) {
  if (!carries(event)) return;
  event.preventDefault();
  event.dataTransfer.dropEffect = "move";
  over.value = area;
}
function dragLeave(event, area) {
  if (!event.currentTarget.contains(event.relatedTarget) && over.value === area) over.value = null;
}
function drop(event, aside) {
  over.value = null;
  const mid = event.dataTransfer?.getData(DRAG_TYPE);
  if (!mid) return;
  event.preventDefault();
  const entry = props.entries.find((e) => e.mid === mid);
  if (entry && Boolean(entry.opzij) !== aside) {
    emit("aside", mid, aside);
    if (aside) asideOpen.value = true; // show where it went
  }
}
</script>
