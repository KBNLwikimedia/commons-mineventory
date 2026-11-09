<!--
  A search box with checkbox facets, in the look of the Objects page, for the pages that are
  a list: Changelog and Usage (wish Olaf). The filtering itself is applyListFilters() in facets.js.
-->
<template>
  <aside class="cc-facetten cc-facetten-lijst">
    <div class="cc-facet-zoek">
      <cdx-text-input
        :model-value="query"
        class="cc-objecten-zoek"
        input-type="search"
        :start-icon="cdxIconSearch"
        clearable
        :placeholder="t('objects.search_placeholder')"
        :aria-label="searchLabel"
        :title="searchHelp"
        @update:model-value="emit('update:query', $event)"
      />
      <p v-if="result" class="cc-uitleg cc-objecten-zoek-uitkomst">{{ result }}</p>
      <slot name="export" />
    </div>
    <template v-for="group in groups" :key="group.key">
      <cdx-field v-if="group.options.length" :is-fieldset="true">
        <template #label>{{ group.label }} <info-dialog v-if="group.info" v-bind="group.info" /></template>
        <facet-option v-for="option in group.options.slice(0, SHOWN)" :key="option.value" v-model="filters[group.key]" :option="option" />
        <!-- The 7th and further in a fold-out (wish Olaf); it says when something in it is ticked. -->
        <cdx-accordion v-if="group.options.length > SHOWN" class="cc-facet-meer">
          <template #title>
            {{ t("facets.more", { n: group.options.length - SHOWN }) }}<template v-if="chosenInside(group)"> · {{ t("facets.more_chosen", { n: chosenInside(group) }) }}</template>
          </template>
          <facet-option v-for="option in group.options.slice(SHOWN)" :key="option.value" v-model="filters[group.key]" :option="option" />
        </cdx-accordion>
      </cdx-field>
    </template>
  </aside>
</template>

<script setup>
import { CdxAccordion, CdxField, CdxTextInput } from "@wikimedia/codex";
import { cdxIconSearch } from "@wikimedia/codex-icons";
import { useT } from "../i18n.js";
import FacetOption from "./FacetOption.vue";
import InfoDialog from "./InfoDialog.vue";

const SHOWN = 6;

const props = defineProps({
  // [{key, label, info?: {title, label, paragraphs}, options: [{value, label?, n, image?, description?}]}];
  // a group without options is left out.
  groups: { type: Array, required: true },
  // {key: [chosen values]}, changed in place.
  filters: { type: Object, required: true },
  query: { type: String, default: "" },
  searchLabel: { type: String, required: true },
  searchHelp: { type: String, default: "" },
  // What the choice leaves, under the search box; empty when nothing is chosen.
  result: { type: String, default: "" },
});
const emit = defineEmits(["update:query"]);
const t = useT();
const chosenInside = (group) => group.options.slice(SHOWN).filter((option) => props.filters[group.key].includes(option.value)).length;
</script>
