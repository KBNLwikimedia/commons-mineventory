<!--
  The facets of the Objects page (functional design 10.4): source, AI-augmented, file (with a
  thumbnail that shows the image large) and saved only. Used by both tabs, Objects and Trash
  (wish Olaf), each with its own choice. The filtering itself is applyFacets() in facets.js.
-->
<template>
  <aside class="cc-facetten">
    <!-- Search and export on top, as on Changelog and Usage (wish Olaf). -->
    <div class="cc-facet-zoek">
      <cdx-text-input
        v-model="filters.query"
        class="cc-objecten-zoek"
        input-type="search"
        :start-icon="cdxIconSearch"
        clearable
        :placeholder="t('objects.search_placeholder')"
        :aria-label="t('objects.search_label')"
        :title="t('objects.page_search_help')"
      />
      <p v-if="result" class="cc-uitleg cc-objecten-zoek-uitkomst">{{ result }}</p>
      <slot name="export" />
    </div>
    <cdx-field :is-fieldset="true">
      <template #label>{{ t("objects.facet_source") }}</template>
      <cdx-checkbox v-for="source in sources" :key="source" v-model="filters.sources" :input-value="source">
        {{ t(`source.${source}`) }} ({{ count(source) }})
      </cdx-checkbox>
    </cdx-field>
    <!-- Objects with an AI-augmented version (magnifier, FO 7.7); wish Olaf. -->
    <cdx-field :is-fieldset="true">
      <template #label>{{ t("objects.facet_ai") }}</template>
      <cdx-checkbox v-model="filters.augmented" :disabled="!augmentedCount && !filters.augmented">
        {{ t("objects.ai_augmented") }} ({{ augmentedCount }})
      </cdx-checkbox>
    </cdx-field>
    <cdx-field v-if="files.length" :is-fieldset="true">
      <template #label>{{ t("objects.facet_file") }}</template>
      <cdx-checkbox v-for="f in files" :key="f.mid" v-model="filters.files" :input-value="f.mid" class="cc-facet-met-duim">
        <button type="button" class="cc-facet-duim" :aria-label="t('objects.file_preview', { name: f.titel })" :title="t('objects.file_preview', { name: f.titel })" @click.prevent.stop="emit('preview', f)">
          <img :src="fileImage(f, 80)" alt="" loading="lazy" />
        </button>
        <span class="cc-afkappen cc-facet-bestand" :title="f.titel">{{ f.titel }}</span> ({{ f.n }})
      </cdx-checkbox>
    </cdx-field>
    <cdx-toggle-switch v-model="filters.saved">{{ t("objects.only_saved") }}</cdx-toggle-switch>
  </aside>
</template>

<script setup>
import { computed, watch } from "vue";
import { CdxCheckbox, CdxField, CdxTextInput, CdxToggleSwitch } from "@wikimedia/codex";
import { cdxIconSearch } from "@wikimedia/codex-icons";
import { useT } from "../i18n.js";
import { applyFacets, fileImage, filesOf } from "../facets.js";

const props = defineProps({
  objects: { type: Array, required: true },
  // {sources: [], files: [], saved: false, augmented: false, query: ""}, changed in place.
  filters: { type: Object, required: true },
});
const emit = defineEmits(["preview"]);
const t = useT();

const sources = computed(() => [...new Set(props.objects.map((o) => o.bron))].sort());
const count = (source) => props.objects.filter((o) => o.bron === source).length;
const augmentedCount = computed(() => props.objects.filter((o) => o.aangevuld).length);
const files = computed(() => filesOf(props.objects));
// What the choice leaves, under the search box; empty when nothing is chosen.
const result = computed(() => {
  const { query, sources, files: chosenFiles, saved, augmented } = props.filters;
  if (!query.trim() && !sources.length && !chosenFiles.length && !saved && !augmented) return "";
  return t("objects.page_search_result", { n: applyFacets(props.objects, props.filters).length, total: props.objects.length });
});

// A chosen source or file that no longer has objects (all moved away) is dropped from the
// choice; otherwise the list stays empty with no box to untick.
watch(
  () => props.objects,
  () => {
    const present = new Set(sources.value);
    props.filters.sources = props.filters.sources.filter((source) => present.has(source));
    const mids = new Set(files.value.map((f) => f.mid));
    props.filters.files = props.filters.files.filter((mid) => mids.has(mid));
  }
);
</script>
