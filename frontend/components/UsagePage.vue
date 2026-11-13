<!-- /verbruik: paid calls today, per day and the log (functional design 6.4, 8.3). -->
<template>
  <div class="cc-verbruik">
    <template v-if="data">
      <section class="cc-tegels">
        <div class="cc-tegel">
          <span>{{ t("usage.today") }}</span>
          <strong>{{ data.vandaag.gebruikt_vandaag }} / {{ data.vandaag.daglimiet }}</strong>
        </div>
        <div class="cc-tegel">
          <span>{{ t("usage.cost_today") }}</span>
          <strong>{{ money(data.vandaag.kosten_vandaag_usd, language) }} / {{ money(data.vandaag.dagbudget_usd, language) }}</strong>
        </div>
        <div class="cc-tegel">
          <span>{{ t("usage.total") }}</span>
          <strong>{{ data.totaal.aanroepen }} · {{ money(data.totaal.kosten_usd, language) }}</strong>
        </div>
      </section>
      <p v-if="!data.logboek.length" class="cc-leeg">{{ t("usage.empty") }}</p>
      <!-- Facets on the left, as on the Objects page; the log on the right (wish Olaf). -->
      <div v-else class="cc-objecten-indeling">
      <list-facets
        v-model:query="query"
        :groups="groups"
        :filters="filters"
        :search-label="t('usage.search_label')"
        :search-help="t('usage.search_help')"
        :result="result"
      >
        <template #export>
          <export-links :url="`${API}/verbruik/export`" :params="{ ...filters, q: query }" :filtered="Boolean(result)" :n="shown.length" />
        </template>
      </list-facets>
      <column-splitter variable="--cc-facet-breedte" side="left" storage-key="cc-breedte-facetten" area=".cc-objecten-indeling" :label="t('objects.resize_facets')" :min="160" :max="520" class="cc-facet-rand" />
      <div class="cc-objecten-inhoud">
      <p v-if="data.logboek.length >= 500" class="cc-uitleg">{{ t("usage.capped", { n: data.logboek.length }) }}</p>
      <p v-if="!shown.length" class="cc-leeg">{{ t("usage.none_found") }}</p>
      <sortable-table v-else v-model:sort="sortParam" :columns="columns" :rows="shown">
        <template #bestand="{ row: { entry } }"><a v-if="entry.bestand" :href="`/?mid=${entry.bestand}&pagina=${entry.pagina || 1}`">{{ entry.titel || entry.bestand }}</a></template>
        <template #kosten="{ row: { entry } }">{{ money(entry.kosten_usd, language) }}</template>
      </sortable-table>
      </div>
      </div>
    </template>
    <cdx-message v-if="error" type="error">{{ error }}</cdx-message>
  </div>
</template>

<script setup>
import { computed, inject, onMounted, reactive, ref, watch } from "vue";
import { CdxMessage } from "@wikimedia/codex";
import { API, errorText, get } from "../api.js";
import { money, useT } from "../i18n.js";
import { applyListFilters, facetOptions, fileImage, newestFirst, readAddress, writeAddress } from "../facets.js";
import { fileName } from "../state.js";
import ExportLinks from "./ExportLinks.vue";
import ListFacets from "./ListFacets.vue";
import SortableTable from "./SortableTable.vue";
import ColumnSplitter from "./ColumnSplitter.vue";

const t = useT();
const language = inject("language", "nl");
const data = ref(null);
const error = ref("");
// The choice in the address and back (wish Olaf: RESTful), with the names of the export.
const fromAddress = readAddress(["soort", "datum", "bestand", "model", "gebruiker"]);
const query = ref(fromAddress.q);
const filters = reactive({ soort: fromAddress.soort, datum: fromAddress.datum, bestand: fromAddress.bestand, model: fromAddress.model, gebruiker: fromAddress.gebruiker });
watch([query, () => ({ ...filters })], ([q, chosen]) => writeAddress({ ...chosen, q }), { deep: true });
// The sorted column too (wish Olaf): "sorteer=kosten", or "-kosten" descending.
const sortParam = ref(new URLSearchParams(window.location.search).get("sorteer") || "");
watch(sortParam, (sorteer) => writeAddress({ sorteer }));

const kindLabel = (entry) => t(`usage.kind_${entry.soort || "sam"}`);
// SAM: the search term; an AI description: its model (and the part asked anew).
const detail = (entry) => ((entry.soort || "sam") === "sam" ? entry.term : [entry.deel && t(`usage.part_${entry.deel}`), entry.model].filter(Boolean).join(" · ") || entry.term);

// The models in the log, with their key in the texts; a model not listed just has no description.
const MODEL_TEXTS = { "sam-3.1": "sam", "muse-spark-1.3": "muse_spark", "muse-spark-1.3-contributor": "muse_contributor", "muse-image-1.0": "muse_image" };
const modelInfo = computed(() => ({
  title: t("usage.models_info_title"),
  label: t("usage.models_info_label"),
  paragraphs: [1, 2, 3, 4, 5, 6].map((n) => t(`usage.models_info_${n}`)),
}));

const rows = computed(() =>
  (data.value?.logboek || []).map((entry) => ({
    entry,
    values: { soort: entry.soort || "sam", datum: entry.tijd.slice(0, 10), bestand: entry.bestand, model: entry.model, gebruiker: entry.gebruiker },
    text: [entry.tijd.replace("T", " "), kindLabel(entry), entry.bestand, entry.titel, entry.term, detail(entry), entry.model, entry.gebruiker].filter(Boolean).join(" ").toLowerCase(),
  }))
);

function fileOptions() {
  const first = new Map([...rows.value].reverse().map(({ entry }) => [entry.bestand, entry]));
  const label = (mid) => fileName(first.get(mid)?.titel) || mid;
  return facetOptions(rows.value, "bestand").map((option) => ({
    ...option,
    label: label(option.value),
    image: fileImage({ mid: option.value, pagina: first.get(option.value)?.pagina }, 80),
  }));
}

const groups = computed(() => [
  { key: "soort", label: t("usage.kind"), options: facetOptions(rows.value, "soort").map((o) => ({ ...o, label: t(`usage.kind_${o.value}`) })) },
  { key: "datum", label: t("usage.facet_date"), options: facetOptions(rows.value, "datum", newestFirst) },
  { key: "bestand", label: t("usage.file"), options: fileOptions() },
  {
    key: "model",
    label: t("usage.facet_model"),
    info: modelInfo.value,
    options: facetOptions(rows.value, "model").map((o) => ({ ...o, description: MODEL_TEXTS[o.value] ? t(`usage.model_${MODEL_TEXTS[o.value]}`) : "" })),
  },
  { key: "gebruiker", label: t("usage.user"), options: facetOptions(rows.value, "gebruiker") },
]);

const columns = computed(() => [
  { key: "tijd", label: t("usage.time"), value: ({ entry }) => entry.tijd.replace("T", " ") },
  { key: "soort", label: t("usage.kind"), value: ({ entry }) => kindLabel(entry) },
  { key: "bestand", label: t("usage.file"), value: ({ entry }) => entry.titel || entry.bestand },
  { key: "term", label: t("usage.term"), value: ({ entry }) => detail(entry) },
  { key: "gebruiker", label: t("usage.user"), value: ({ entry }) => entry.gebruiker || "—" },
  { key: "kosten", label: t("usage.cost"), numeric: true, value: ({ entry }) => entry.kosten_usd },
]);

const shown = computed(() => applyListFilters(rows.value, filters, query.value));
const result = computed(() => {
  if (!query.value.trim() && !Object.values(filters).some((chosen) => chosen.length)) return "";
  const cost = shown.value.reduce((sum, { entry }) => sum + (entry.kosten_usd || 0), 0);
  return t("usage.result", { n: shown.value.length, total: rows.value.length, cost: money(cost, language) });
});

onMounted(async () => {
  try {
    data.value = await get(`${API}/verbruik`);
  } catch (e) {
    error.value = errorText(t, e);
  }
});
</script>
