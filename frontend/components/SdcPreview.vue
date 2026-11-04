<!--
  The structured data of the concept the way the "Structured data" tab of a
  file page on Commons shows it: the captions, then per property its values,
  with qualifiers below them. Depicts (P180) comes first, as on Commons.
  Labels come from Wikidata through the concept (sdc_labels); without a label
  the id is shown.
-->
<template>
  <div class="cc-sdc">
    <section v-if="captionsShown" class="cc-sdc-groep">
      <h5 class="cc-sdc-kop">
        {{ t("sdc.captions") }}
        <cdx-button v-if="editable" class="cc-veld-potlood" weight="quiet" action="progressive" size="small" :aria-label="t('concept.edit_caption')" :title="t('concept.edit_caption')" @click="emit('edit-captions')">
          <cdx-icon :icon="cdxIconEdit" size="small" />
        </cdx-button>
      </h5>
      <ul v-if="captions.length" class="cc-sdc-waarden">
        <li v-for="caption in captions" :key="caption.language">
          <span class="cc-sdc-taal">{{ caption.language }}</span> {{ caption.value }}
        </li>
      </ul>
      <p v-else class="cc-klein cc-leeg">{{ t("sdc.no_captions") }}</p>
    </section>
    <section v-for="group in groups" :key="group.property" class="cc-sdc-groep">
      <h5 class="cc-sdc-kop">
        <!-- As on Commons: depicts has a title of its own, with the property below it. -->
        <template v-if="group.property === 'P180'">{{ t("sdc.depicts_title") }}<br /></template>
        <a :class="{ 'cc-sdc-eigenschap': group.property === 'P180' }" :href="`https://www.wikidata.org/wiki/Property:${group.property}`" target="_blank" rel="noopener">{{ label(group.property) }}</a>
      </h5>
      <ul class="cc-sdc-waarden">
        <li v-for="(claim, i) in group.claims" :key="i">
          <sdc-value :snak="claim.mainsnak" />
          <!-- Editable: a depicts item can be removed (the others come from the original). -->
          <cdx-button
            v-if="editable && group.property === 'P180' && claim.mainsnak?.datavalue?.value?.id"
            size="small"
            weight="quiet"
            action="destructive"
            :aria-label="`${t('actions.remove')}: ${label(claim.mainsnak.datavalue.value.id)}`"
            :title="t('actions.remove')"
            @click="emit('remove-depicts', claim.mainsnak.datavalue.value.id)"
          >×</cdx-button>
          <dl v-if="claim.qualifiers" class="cc-sdc-kwalificaties">
            <template v-for="(snaks, prop) in claim.qualifiers" :key="prop">
              <dt>{{ label(prop) }}</dt>
              <dd v-for="(snak, j) in snaks" :key="j"><sdc-value :snak="snak" /></dd>
            </template>
          </dl>
        </li>
      </ul>
      <slot v-if="editable && group.property === 'P180'" name="depicts-add" />
    </section>
    <!-- No depicts yet: the group with only the field to add one. -->
    <section v-if="editable && !groups.some((g) => g.property === 'P180')" class="cc-sdc-groep">
      <h5 class="cc-sdc-kop">{{ t("sdc.depicts_title") }}<br /><a class="cc-sdc-eigenschap" href="https://www.wikidata.org/wiki/Property:P180" target="_blank" rel="noopener">{{ label("P180") }}</a></h5>
      <slot name="depicts-add" />
    </section>
    <p v-if="!groups.length" class="cc-klein cc-leeg">{{ t("sdc.no_statements") }}</p>
  </div>
</template>

<script setup>
import { computed, h, inject } from "vue";
import { CdxButton, CdxIcon } from "@wikimedia/codex";
import { cdxIconEdit } from "@wikimedia/codex-icons";
import { useT } from "../i18n.js";

const props = defineProps({
  sdc: { type: Object, required: true },
  labels: { type: Object, default: () => ({}) },
  // Without captions: for statements added to an existing file (the original).
  captionsShown: { type: Boolean, default: true },
  // Editable (the concept): a pencil for the captions, × per depicts item, and a slot to add one.
  editable: { type: Boolean, default: false },
});
const emit = defineEmits(["edit-captions", "remove-depicts"]);
const t = useT();
const language = inject("language", "nl");

function label(id) {
  const names = props.labels[id];
  return names?.[language] || names?.[language === "nl" ? "en" : "nl"] || id;
}

const captions = computed(() => Object.values(props.sdc.labels || {}));

// Claims grouped by property, depicts first, otherwise in the order given.
const groups = computed(() => {
  const byProperty = new Map();
  for (const claim of props.sdc.claims || []) {
    const property = claim.mainsnak?.property;
    if (!byProperty.has(property)) byProperty.set(property, []);
    byProperty.get(property).push(claim);
  }
  const list = [...byProperty].map(([property, claims]) => ({ property, claims }));
  return list.sort((a, b) => (b.property === "P180") - (a.property === "P180"));
});

// Precision of a Wikibase time: 11 day, 10 month, 9 year, 8 decade, 7 century.
function formatTime(value) {
  const match = /^([+-])(\d+)-(\d\d)-(\d\d)/.exec(value.time || "");
  if (!match) return value.time;
  const year = Number(match[2]) * (match[1] === "-" ? -1 : 1);
  const precision = value.precision;
  if (precision >= 11) return new Date(Date.UTC(year, Number(match[3]) - 1, Number(match[4]))).toLocaleDateString(language, { timeZone: "UTC", dateStyle: "long" });
  if (precision === 10) return new Date(Date.UTC(year, Number(match[3]) - 1, 1)).toLocaleDateString(language, { timeZone: "UTC", year: "numeric", month: "long" });
  if (precision === 8) return t("sdc.decade", { year: Math.floor(year / 10) * 10 });
  if (precision === 7) return t("sdc.century", { n: Math.ceil(year / 100) });
  return String(year);
}

// One value, as text or a link to Wikidata.
const SdcValue = (componentProps) => {
  const snak = componentProps.snak || {};
  if (snak.snaktype === "somevalue") return h("i", t("sdc.unknown_value"));
  if (snak.snaktype === "novalue") return h("i", t("sdc.no_value"));
  const data = snak.datavalue || {};
  const value = data.value;
  if (data.type === "wikibase-entityid") {
    return h("a", { href: `https://www.wikidata.org/wiki/${value.id}`, target: "_blank", rel: "noopener" }, label(value.id));
  }
  if (data.type === "time") return formatTime(value);
  if (data.type === "monolingualtext") return `${value.text} (${value.language})`;
  if (data.type === "quantity") {
    // As on Commons: "5,775,624 byte", "1,928 pixel".
    const amount = Number(value.amount).toLocaleString(language);
    const unit = String(value.unit || "").startsWith("http") ? label(value.unit.split("/").pop()) : "";
    return unit ? `${amount} ${unit}` : amount;
  }
  if (data.type === "globecoordinate") return `${value.latitude}, ${value.longitude}`;
  if (typeof value === "string" && /^https?:\/\//.test(value)) return h("a", { href: value, target: "_blank", rel: "noopener" }, value);
  return typeof value === "string" ? value : JSON.stringify(value);
};
SdcValue.props = ["snak"];
</script>
