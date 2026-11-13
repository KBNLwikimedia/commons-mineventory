<!--
  One row of "Gegevens van deze afbeelding" (OriginalData.vue): a proposal or a search term
  without objects. Tick box, the item's image, its Wikidata link, the pencil for another item
  (with its search, free) and the bin. Slot "source" holds where the row comes from; the
  default slot what comes before the bin ("with place"). The parent keeps the state: the
  search text and hits, and the larger view of an image (zoom/unzoom).
-->
<template>
  <li class="cc-origineel-rij">
    <input v-model="row.checked" type="checkbox" :aria-label="t('original.include', { item: row.label })" />
    <!-- The item's own image (P18) on Wikidata, where it has one: helps to see whether it is the right item. -->
    <span :key="row.q" class="cc-item-beeld-kader"><img class="cc-item-beeld" :src="itemImage(row.q)" :alt="t('original.item_image', { item: row.label })" :title="t('original.item_image', { item: row.label })" loading="lazy" @mouseenter="emit('zoom', $event, row.q)" @mouseleave="emit('unzoom')" @error="noImage" /><span class="cc-geen-beeld">{{ t("original.no_image") }}</span></span>
    <div class="cc-origineel-item">
      <div>
        <a :href="`https://www.wikidata.org/wiki/${row.q}`" target="_blank" rel="noopener">{{ row.label }}</a>
        <span class="cc-klein"> ({{ row.q }})</span>
        <ai-badge v-if="ai" kind="beschrijving" :model="''" />
        <cdx-button v-if="changeable" action="progressive" weight="quiet" size="small" :aria-label="t('original.other_item')" :title="t('original.other_item')" @click="emit('other')">
          <cdx-icon :icon="cdxIconEdit" size="small" />
        </cdx-button>
      </div>
      <div v-if="row.beschrijving" class="cc-klein">{{ row.beschrijving }}</div>
      <slot name="source" />
      <!-- Another item for this row: search Wikidata (free) and pick. -->
      <div v-if="searching" class="cc-origineel-zoek">
        <cdx-text-input
          clearable
          :model-value="text"
          :placeholder="t('original.search_placeholder')"
          @update:model-value="typed"
        />
        <ul class="cc-origineel-treffers">
          <li v-for="hit in hits" :key="hit.q">
            <img class="cc-item-beeld cc-item-beeld-klein" :src="itemImage(hit.q, 60)" alt="" loading="lazy" @mouseenter="emit('zoom', $event, hit.q)" @mouseleave="emit('unzoom')" @error="hideImage" />
            <button type="button" class="cc-link" @click="emit('choose', hit)">{{ hit.label }}</button>
            <span class="cc-klein"> ({{ hit.q }}) {{ hit.beschrijving }}</span>
          </li>
        </ul>
        <button type="button" class="cc-link" @click="emit('cancel')">{{ t("actions.cancel") }}</button>
      </div>
    </div>
    <slot />
    <cdx-button action="destructive" weight="quiet" size="small" :aria-label="t('original.hide_row', { item: row.label })" :title="t('original.hide_row', { item: row.label })" @click="emit('hide')">
      <cdx-icon :icon="cdxIconTrash" size="small" />
    </cdx-button>
  </li>
</template>

<script setup>
import { CdxButton, CdxIcon, CdxTextInput } from "@wikimedia/codex";
import { cdxIconEdit, cdxIconTrash } from "@wikimedia/codex-icons";
import { useT } from "../i18n.js";
import { itemImage } from "../wikidata.js";
import AiBadge from "./AiBadge.vue";

defineProps({
  // A merged row of OriginalData (its tick box speaks for all its members).
  row: { type: Object, required: true },
  ai: { type: Boolean, default: false },
  // Whether the pencil (another item) is there.
  changeable: { type: Boolean, default: false },
  // The search for another item, open for this row: its text and hits.
  searching: { type: Boolean, default: false },
  text: { type: String, default: "" },
  hits: { type: Array, default: () => [] },
});
const emit = defineEmits(["other", "search", "update:text", "choose", "cancel", "hide", "zoom", "unzoom"]);
const t = useT();
function typed(value) {
  emit("update:text", value);
  emit("search", value);
}
const hideImage = (event) => (event.target.style.visibility = "hidden");
// Without an image: a grey square that says so, so the rows stay aligned (wish Olaf).
const noImage = (event) => event.target.parentElement?.classList.add("cc-zonder-beeld");
</script>
