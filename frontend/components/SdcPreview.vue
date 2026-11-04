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
    <!-- No depicts yet: as on Commons, the depicts group still comes first, with only the field to add one. -->
    <section v-if="editable && !groups.some((g) => g.property === 'P180')" class="cc-sdc-groep">
      <h5 class="cc-sdc-kop">{{ t("sdc.depicts_title") }}<br /><a class="cc-sdc-eigenschap" href="https://www.wikidata.org/wiki/Property:P180" target="_blank" rel="noopener">{{ depictsLabel }}</a></h5>
      <slot name="depicts-add" />
    </section>
    <section v-for="group in groups" :key="group.property" class="cc-sdc-groep">
      <h5 class="cc-sdc-kop">
        <span>
          <!-- As on Commons: depicts has a title of its own, with the property below it. -->
          <template v-if="group.property === 'P180'">{{ t("sdc.depicts_title") }}<br /></template>
          <a :class="{ 'cc-sdc-eigenschap': group.property === 'P180' }" :href="`https://www.wikidata.org/wiki/Property:${group.property}`" target="_blank" rel="noopener">{{ label(group.property) }}</a>
        </span>
        <!-- Edit, as on Commons: only for the statements taken over from the original. -->
        <button v-if="editable && EDITABLE.includes(group.property) && editing !== group.property" type="button" class="cc-link cc-sdc-edit" @click="startEdit(group)">{{ t("concept.edit_link") }}</button>
        <span v-else-if="editable && FACTS.includes(group.property)" class="cc-klein cc-sdc-vast" :title="t('sdc.fact_help')">{{ t("sdc.fact") }}</span>
      </h5>
      <!-- Editing the values of one statement: Opslaan or Annuleren. -->
      <div v-if="editing === group.property" class="cc-sdc-bewerken">
        <ul class="cc-sdc-waarden">
          <li v-for="(value, i) in draft" :key="i" class="cc-sdc-bewerk-rij">
            <template v-if="value.onbekend">
              <span class="cc-leeg">{{ t("sdc.unknown_value") }}</span>
            </template>
            <cdx-text-input v-else-if="value.tijd !== undefined" v-model="value.tijd" :aria-label="label(group.property)" placeholder="1708, 1708-02, 1708-02-28" />
            <cdx-lookup
              v-else
              v-model:selected="value.item"
              v-model:input-value="value.text"
              :menu-items="value.items || []"
              :placeholder="t('concept.depicts_search')"
              :start-icon="cdxIconSearch"
              @input="(text) => search(value, text)"
              @update:selected="(q) => choose(value, q)"
            />
            <cdx-button weight="quiet" action="destructive" size="small" :aria-label="t('actions.remove')" :title="t('actions.remove')" @click="draft.splice(i, 1)">×</cdx-button>
          </li>
        </ul>
        <div class="cc-knoppen">
          <button type="button" class="cc-link" @click="addValue(group.property)">+ {{ t("sdc.add_value") }}</button>
          <button v-if="group.property === 'P170'" type="button" class="cc-link" @click="draft.push({ onbekend: true })">+ {{ t("sdc.unknown_value") }}</button>
        </div>
        <div class="cc-knoppen">
          <cdx-button action="progressive" weight="primary" :disabled="!draftValid" @click="saveEdit(group.property)">{{ t("actions.save_short") }}</cdx-button>
          <cdx-button @click="editing = null">{{ t("actions.cancel") }}</cdx-button>
        </div>
      </div>
      <ul v-else class="cc-sdc-waarden">
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
    <p v-if="!groups.length" class="cc-klein cc-leeg">{{ t("sdc.no_statements") }}</p>
  </div>
</template>

<script setup>
import { computed, h, inject, ref } from "vue";
import { CdxButton, CdxIcon, CdxLookup, CdxTextInput } from "@wikimedia/codex";
import { cdxIconEdit, cdxIconSearch } from "@wikimedia/codex-icons";
import { API, get, query } from "../api.js";
import { useT } from "../i18n.js";

const props = defineProps({
  sdc: { type: Object, required: true },
  labels: { type: Object, default: () => ({}) },
  // Without captions: for statements added to an existing file (the original).
  captionsShown: { type: Boolean, default: true },
  // Editable (the concept): a pencil for the captions, × per depicts item, and a slot to add one;
  // Edit for the values of the statements taken over from the original.
  editable: { type: Boolean, default: false },
  // The values already changed in the app ({P195: [{item, bron}], …}), so editing continues from them.
  overrides: { type: Object, default: () => ({}) },
});
const emit = defineEmits(["edit-captions", "remove-depicts", "save-statement"]);

// Which statements have Edit (as concept.EDITABLE_PROPERTIES), and which are facts of the file itself.
const EDITABLE = ["P6216", "P275", "P170", "P571", "P195"];
const FACTS = ["P31", "P1163", "P4092", "P3575", "P2048", "P2049"];
const editing = ref(null);
const draft = ref([]);

// "+1708-02-00T00:00:00Z" with precision 10 → "1708-02".
function timeText(value) {
  const match = /^([+-])(\d+)-(\d\d)-(\d\d)/.exec(value?.time || "");
  if (!match) return "";
  const year = `${match[1] === "-" ? "-" : ""}${Number(match[2])}`;
  if (value.precision >= 11) return `${year}-${match[3]}-${match[4]}`;
  if (value.precision === 10) return `${year}-${match[3]}`;
  return year;
}

function fromSnak(snak, index) {
  if (snak?.snaktype === "somevalue") return { onbekend: true, bron: index };
  const value = snak?.datavalue?.value;
  if (snak?.datavalue?.type === "time") return { tijd: timeText(value), bron: index };
  const q = value?.id;
  return { item: q || null, text: q ? label(q) : "", bron: index };
}

function startEdit(group) {
  const stored = props.overrides?.[group.property];
  draft.value = stored
    ? stored.map((v) => ({ ...v, text: v.item ? label(v.item) : "" }))
    : group.claims.map((claim, i) => fromSnak(claim.mainsnak, i));
  editing.value = group.property;
}

function addValue(property) {
  draft.value.push(property === "P571" ? { tijd: "" } : { item: null, text: "" });
}

const draftValid = computed(() =>
  draft.value.every((v) => v.onbekend || (v.tijd !== undefined ? /^-?\d{1,4}(-\d\d){0,2}$/.test(v.tijd.trim()) : /^Q\d+$/.test(v.item || "")))
);

function saveEdit(property) {
  const values = draft.value.map((v) => {
    const out = v.onbekend ? { onbekend: true } : v.tijd !== undefined ? { tijd: v.tijd.trim() } : { item: v.item };
    if (Number.isInteger(v.bron)) out.bron = v.bron;
    return out;
  });
  emit("save-statement", { property, values });
  editing.value = null;
}

// Wikidata items as you type (a read), for an item value.
let timer = null;
function search(value, text) {
  clearTimeout(timer);
  if (!text || text.length < 2) {
    value.items = [];
    return;
  }
  timer = setTimeout(async () => {
    try {
      const found = (await get(`${API}/wikidata/zoek${query({ q: text, taal: language })}`)).resultaten;
      value.items = found.map((hit) => ({ value: hit.q, label: hit.label, description: [hit.q, hit.beschrijving].filter(Boolean).join(" · ") }));
    } catch {
      value.items = [];
    }
  }, 300);
}
function choose(value, q) {
  const hit = (value.items || []).find((item) => item.value === q);
  if (hit) value.text = hit.label;
}
const t = useT();
const language = inject("language", "nl");

// The name of P180 even when no claim brought its label along.
const depictsLabel = computed(() => (props.labels.P180 ? label("P180") : t("sdc.depicts_property")));

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
