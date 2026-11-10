<!-- The list view of the Objects page, for both tabs (wish Olaf); the buttons per object come from the page. -->
<template>
  <sortable-table :columns="columns" :rows="objects" :row-key="(obj) => obj.mid + obj.id" :sort="sort" @sorted="emit('sorted', $event)" @update:sort="emit('update:sort', $event)">
    <template #beeld="{ row: obj }">
      <a v-if="linkImages" :href="obj.app_url"><img class="cc-lijst-duim" :src="`${obj.uitsnede_url}?w=96`" :alt="name(obj)" loading="lazy" /></a>
      <img v-else class="cc-lijst-duim" :src="`${obj.uitsnede_url}?w=96`" :alt="name(obj)" loading="lazy" />
    </template>
    <template #naam="{ row: obj }"><strong>{{ name(obj) }}</strong></template>
    <template #zekerheid="{ row: obj }">{{ certainty(obj) }}</template>
    <template #bron="{ row: obj }">
      {{ t(`source.${obj.bron}`) }}<small v-if="obj.aangevuld" class="cc-lijst-regel">{{ t("objects.ai_augmented") }}</small>
    </template>
    <template #opgeslagen="{ row: obj }">
      <!-- Always an element: an empty slot would show the column's value (false). -->
      <div v-if="!obj.opgeslagen"></div>
      <template v-else>
        <saved-label :object="obj" />
        <small class="cc-lijst-regel">
          <a :href="savedUrl(obj)" target="_blank" rel="noopener">{{ t("objects.file_open_cutout") }}</a>
          <span aria-hidden="true"> · </span><a :href="`${savedUrl(obj)}?download=1`">{{ t("objects.file_download") }}</a>
          <template v-if="config.lokaal"><span aria-hidden="true"> · </span><button type="button" class="cc-link" :title="t('objects.show_in_folder_help')" @click="emit('show-in-folder', obj)">{{ t("objects.show_in_folder") }}</button></template>
        </small>
      </template>
    </template>
    <template #bestand="{ row: obj }">
      <a v-if="obj.bestand_url" :href="obj.bestand_url" target="_blank" rel="noopener">{{ fileName(obj.bestand_titel) }}</a>
      <template v-else>{{ fileName(obj.bestand_titel) }}</template>
    </template>
    <template #acties="{ row: obj }"><span class="cc-lijst-acties"><slot name="actions" :object="obj" /></span></template>
  </sortable-table>
</template>

<script setup>
import { computed, inject } from "vue";
import { useT } from "../i18n.js";
import { fileName } from "../state.js";
import SavedLabel from "./SavedLabel.vue";
import SortableTable from "./SortableTable.vue";

const props = defineProps({
  objects: { type: Array, required: true },
  // The name as the page shows it, and the address of a saved cut-out.
  name: { type: Function, required: true },
  savedUrl: { type: Function, required: true },
  linkImages: { type: Boolean, default: false },
  // The sorted column, as in the address (v-model:sort).
  sort: { type: String, default: "" },
});
const emit = defineEmits(["sorted", "show-in-folder", "update:sort"]);
const t = useT();
const config = inject("config", {});

const certainty = (obj) => (obj.score == null ? "" : `${Math.round(obj.score * 100)}%`);
const columns = computed(() => [
  { key: "beeld", label: t("objects.col_image") },
  { key: "naam", label: t("objects.col_name"), value: props.name },
  { key: "bron", label: t("objects.col_source"), value: (obj) => t(`source.${obj.bron}`) },
  { key: "zekerheid", label: t("objects.col_certainty"), numeric: true, value: (obj) => obj.score ?? "" },
  { key: "status", label: t("objects.col_status"), value: (obj) => t(`status.${obj.status}`) },
  { key: "opgeslagen", label: t("objects.col_saved"), value: (obj) => Boolean(obj.opgeslagen) },
  { key: "bestand", label: t("objects.col_file"), value: (obj) => fileName(obj.bestand_titel) },
  { key: "acties", label: t("objects.col_actions") },
]);
</script>
