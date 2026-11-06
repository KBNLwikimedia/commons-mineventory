<!--
  Earlier versions (of a description) one at a time, as a carousel: Previous / Next,
  "2 of 5", and a row of small round dots below to jump to a version. The content and
  the actions of a version (use it, the bin) come from the slots, so the same carousel
  serves every list of versions. ← and → step through the versions while it has focus.
-->
<template>
  <div v-if="items.length" class="cc-versies" role="group" :aria-label="label" tabindex="0" @keydown.left.stop.prevent="go(index - 1)" @keydown.right.stop.prevent="go(index + 1)">
    <div class="cc-versies-balk">
      <cdx-button weight="quiet" size="small" :disabled="index === 0" :aria-label="t('version.previous')" :title="t('version.previous')" @click="go(index - 1)">
        <cdx-icon :icon="cdxIconPrevious" />
      </cdx-button>
      <span class="cc-versies-positie" aria-live="polite">{{ t("version.position", { i: index + 1, n: items.length }) }}</span>
      <cdx-button weight="quiet" size="small" :disabled="index >= items.length - 1" :aria-label="t('version.next')" :title="t('version.next')" @click="go(index + 1)">
        <cdx-icon :icon="cdxIconNext" />
      </cdx-button>
      <span class="cc-versies-acties"><slot name="actions" :item="current" :index="index" /></span>
    </div>
    <div class="cc-versies-inhoud">
      <slot :item="current" :index="index" />
    </div>
    <div v-if="items.length > 1" class="cc-versies-stippen" role="tablist" :aria-label="label">
      <button
        v-for="(item, i) in items"
        :key="keyOf(item, i)"
        type="button"
        role="tab"
        class="cc-versies-stip"
        :class="{ actief: i === index }"
        :aria-selected="i === index ? 'true' : 'false'"
        :aria-label="t('version.dot', { i: i + 1 })"
        :title="t('version.dot', { i: i + 1 })"
        @click="go(i)"
      ></button>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { CdxButton, CdxIcon } from "@wikimedia/codex";
import { cdxIconNext, cdxIconPrevious } from "@wikimedia/codex-icons";
import { useT } from "../i18n.js";

const props = defineProps({
  items: { type: Array, required: true },
  // The field that identifies a version (for the dots), e.g. "versie".
  itemKey: { type: String, default: "versie" },
  label: { type: String, default: "" },
});
const t = useT();
const index = ref(0);
const current = computed(() => props.items[index.value]);
const keyOf = (item, i) => (item && item[props.itemKey]) || i;

function go(i) {
  index.value = Math.max(0, Math.min(props.items.length - 1, i));
}
// A version removed (or added): stay at the same place, within the list.
watch(
  () => props.items.length,
  () => go(index.value)
);
</script>
