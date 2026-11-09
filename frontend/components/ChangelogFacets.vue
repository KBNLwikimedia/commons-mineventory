<!--
  Facets and search for /changelog (wish Olaf). Flask renders the whole changelog; this only hides
  what does not match, so the page stays readable without JavaScript and the texts are not sent twice.
-->
<template>
  <list-facets
    v-model:query="query"
    :groups="groups"
    :filters="filters"
    :search-label="t('changelog.search_label')"
    :search-help="t('changelog.search_help')"
    :result="result"
  >
    <template #export>
      <export-links :url="`${API}/changelog/export`" :params="{ ...filters, q: query }" :filtered="Boolean(result)" :n="shown.length" />
    </template>
  </list-facets>
  <!-- A table next to the view per version (wish Olaf: sortable columns); it goes inside the article. -->
  <teleport v-if="tableHost" :to="tableHost">
    <view-switch v-model="view" :buttons="viewButtons" storage-key="cc-weergave-changelog" />
    <sortable-table v-if="view === 'tabel'" :columns="columns" :rows="shown">
      <template #wijziging="{ row }"><div v-html="row.element.innerHTML"></div></template>
    </sortable-table>
  </teleport>
  <column-splitter variable="--cc-facet-breedte" side="left" storage-key="cc-breedte-facetten" area=".cc-objecten-indeling" :label="t('objects.resize_facets')" :min="160" :max="520" class="cc-facet-rand" />
</template>

<script setup>
import { computed, reactive, ref, watchEffect } from "vue";
import { useT } from "../i18n.js";
import { applyListFilters, facetOptions, newestFirst } from "../facets.js";
import { API } from "../api.js";
import ExportLinks from "./ExportLinks.vue";
import ListFacets from "./ListFacets.vue";
import SortableTable from "./SortableTable.vue";
import ViewSwitch from "./ViewSwitch.vue";
import ColumnSplitter from "./ColumnSplitter.vue";

const t = useT();
const query = ref("");
const filters = reactive({ soort: [], reeks: [], datum: [] });

// Every change on the page, as rendered by templates/changelog.html.
const rows = [...document.querySelectorAll(".cl-item")].map((element) => {
  const { versie, soort, reeks, datum } = element.dataset;
  return { element, versie, values: { soort, reeks, datum }, text: `${versie} ${datum} ${soort} ${element.textContent}`.toLowerCase() };
});

const groups = [
  { key: "soort", label: t("changelog.facet_kind"), options: facetOptions(rows, "soort") },
  { key: "reeks", label: t("changelog.facet_series"), options: facetOptions(rows, "reeks", newestFirst) },
  { key: "datum", label: t("changelog.facet_date"), options: facetOptions(rows, "datum", newestFirst) },
];

const tableHost = document.getElementById("cc-changelog-tabel");
const view = ref("versies");
const viewButtons = [
  { value: "versies", label: t("view.by_version") },
  { value: "tabel", label: t("view.table") },
];
const columns = [
  { key: "versie", label: t("changelog.col_version"), value: (row) => row.versie },
  { key: "datum", label: t("changelog.facet_date"), value: (row) => row.values.datum },
  { key: "reeks", label: t("changelog.facet_series"), value: (row) => row.values.reeks },
  { key: "soort", label: t("changelog.facet_kind"), value: (row) => row.values.soort },
  { key: "wijziging", label: t("changelog.col_change"), value: (row) => row.element.textContent.trim() },
];

const shown = computed(() => applyListFilters(rows, filters, query.value));
const result = computed(() =>
  query.value.trim() || Object.values(filters).some((chosen) => chosen.length) ? t("changelog.result", { n: shown.value.length, total: rows.length }) : ""
);

// In the table view the versions make way.
watchEffect(() => document.querySelector(".cc-changelog")?.classList.toggle("cc-als-tabel", view.value === "tabel"));

// A section or version without a change left disappears too.
watchEffect(() => {
  const visible = new Set(shown.value);
  for (const row of rows) row.element.hidden = !visible.has(row);
  for (const block of document.querySelectorAll(".cl-sectie, .cl-versie")) block.hidden = !block.querySelector(".cl-item:not([hidden])");
});
</script>
