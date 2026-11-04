<!-- Input bar and file information (functional design 10.4). -->
<template>
  <section class="cc-invoer">
    <form class="cc-invoer-form" @submit.prevent="submit">
      <cdx-field :hide-label="true">
        <cdx-text-input
          v-model="text"
          :start-icon="cdxIconSearch"
          :placeholder="t('input.placeholder')"
          :aria-label="t('input.label')"
          clearable
        />
        <template #label>{{ t("input.label") }}</template>
      </cdx-field>
      <cdx-button action="progressive" weight="primary" type="submit" :disabled="loading || !text.trim()">
        {{ loading ? t("input.loading") : t("input.open") }}
      </cdx-button>
    </form>

    <div v-if="file" class="cc-bestand">
      <img
        v-if="file.ondersteund"
        class="cc-bestand-miniatuur"
        :src="`/api/v1/bestand/${file.mid}/pagina/1/afbeelding?w=120`"
        alt=""
      />
      <div class="cc-bestand-gegevens">
        <h2 class="cc-bestand-titel">
          <a :href="file.url" target="_blank" rel="noopener">{{ file.naam }}</a>
          <cdx-icon :icon="cdxIconLinkExternal" size="small" />
        </h2>
        <!-- Licence, rights and facts on one line, to keep the top of the page low. -->
        <p class="cc-bestand-regel cc-klein">
          <cdx-info-chip status="notice">{{ file.licentie.kort || t("file.licence_unknown") }}</cdx-info-chip>
          <rights-label v-for="label in file.rechten.labels" :key="label" :label="label" />
          <span v-if="file.maker">{{ t("file.maker") }}: {{ file.maker }}</span>
          <span v-if="file.datum"> · {{ t("file.date") }}: {{ file.datum }}</span>
          <span> · {{ file.mid }} · {{ file.breedte }} × {{ file.hoogte }} px</span>
          <span v-if="file.paginas > 1"> · {{ t("file.pages", { n: file.paginas }) }}</span>
        </p>
        <p v-if="file.tegels" class="cc-klein">{{ t("file.tiles", { mp: file.megapixels }) }}</p>
        <cdx-message v-if="file.ondersteund && !file.uitsnijden_mogelijk" type="warning" :inline="true">
          {{ t("file.too_large", { mp: file.megapixels }) }}
        </cdx-message>
        <cdx-message v-if="!file.rechten.upload_toegestaan" type="warning" :inline="true">
          {{ t("rights.upload_blocked") }}
        </cdx-message>
        <cdx-accordion class="cc-metadata">
          <template #title>{{ t("file.metadata") }}</template>
          <dl>
            <dt>{{ t("file.description") }}</dt>
            <dd>{{ file.beschrijving || "—" }}</dd>
            <template v-if="Object.keys(file.sdc.captions).length">
              <dt>{{ t("file.captions") }}</dt>
              <dd v-for="(value, lang) in file.sdc.captions" :key="lang">{{ lang }}: {{ value }}</dd>
            </template>
            <dt>{{ t("file.categories") }}</dt>
            <dd>{{ file.categorieen.join(" · ") || "—" }}</dd>
            <dt>{{ t("file.depicts") }}</dt>
            <dd>
              <span v-if="!file.sdc.beeldt_af.length">—</span>
              <span v-for="(item, i) in file.sdc.beeldt_af" :key="i" class="cc-depicts">
                {{ item.label }}<small v-if="item.positie"> ▭</small>
              </span>
            </dd>
            <dt>{{ t("file.rights_reasons") }}</dt>
            <dd v-for="(reason, i) in file.rechten.redenen" :key="`r${i}`">{{ reason }}</dd>
            <dd v-if="!file.rechten.redenen.length">{{ t("rights.in_orde") }}</dd>
            <!-- The work on Wikidata, as {{Artwork}} shows it on Commons (|wikidata= or the file's P6243). -->
            <template v-if="file.werk">
              <dt>{{ t("file.work") }}</dt>
              <dd>
                <a :href="`https://www.wikidata.org/wiki/${file.werk.wikidata}`" target="_blank" rel="noopener">{{ workName }}</a>
                <small class="cc-qid">{{ file.werk.wikidata }}</small>
                <small class="cc-werk-via">{{ t(file.werk.via === "sdc" ? "file.work_via_sdc" : "file.work_via_template") }}</small>
              </dd>
              <template v-for="row in workRows" :key="row.key">
                <dt class="cc-werk-veld">{{ t(`file.work_${row.key}`) }}</dt>
                <dd>
                  <template v-for="(part, i) in row.parts" :key="i">
                    <template v-if="i"> · </template>
                    <a v-if="part.href" :href="part.href" target="_blank" rel="noopener">{{ part.text }}</a>
                    <template v-else>{{ part.text }}</template>
                  </template>
                </dd>
              </template>
            </template>
            <dt>{{ t("file.licence_templates") }}</dt>
            <dd><code v-for="(tpl, i) in file.licentie.sjablonen" :key="i">{{ tpl }}</code></dd>
          </dl>
        </cdx-accordion>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, inject, ref, watch } from "vue";
import { CdxAccordion, CdxButton, CdxField, CdxIcon, CdxInfoChip, CdxMessage, CdxTextInput } from "@wikimedia/codex";
import { cdxIconLinkExternal, cdxIconSearch } from "@wikimedia/codex-icons";
import { useT } from "../i18n.js";
import RightsLabel from "./RightsLabel.vue";

const props = defineProps({
  file: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  initial: { type: String, default: "" },
});
const emit = defineEmits(["open"]);
const t = useT();
const language = inject("language", "nl");
const text = ref(props.initial);

// The work's fields in the order of {{Artwork}} on Commons; empty ones are left out.
const workName = computed(() => {
  const work = props.file?.werk || {};
  return (language === "en" ? work.label_en || work.label : work.label || work.label_en) || work.wikidata;
});
const WIKIDATA = "https://www.wikidata.org/wiki/";
function itemParts(items) {
  return (items || []).map((item) => ({
    text: (language === "en" ? item.en || item.nl : item.nl || item.en) || item.id,
    href: WIKIDATA + item.id,
  }));
}
const workRows = computed(() => {
  const work = props.file?.werk;
  if (!work) return [];
  const description = language === "en" ? work.beschrijving?.en || work.beschrijving?.nl : work.beschrijving?.nl || work.beschrijving?.en;
  const sizes = (work.afmetingen || []).map((s) => `${t(`file.work_${s.maat}`)} ${Number(s.waarde).toLocaleString(language)}${s.eenheid ? ` ${s.eenheid}` : ""}`);
  const inventory = [...(work.collectie || []).flatMap((c) => c.inventarisnummers || []), ...(work.inventarisnummers || [])];
  const host = (url) => {
    try {
      return new URL(url).hostname.replace(/^www\./, "");
    } catch {
      return url;
    }
  };
  const rows = [
    ["titel", work.titel && work.titel !== workName.value ? [{ text: work.titel }] : []],
    ["makers", (work.makers || []).map((text) => ({ text }))],
    ["datum", work.datum ? [{ text: work.datum }] : []],
    ["beschrijving", description ? [{ text: description }] : []],
    ["soort", itemParts(work.soort)],
    ["onderdeel_van", itemParts(work.onderdeel_van)],
    ["beeldt_af", itemParts(work.beeldt_af)],
    ["materiaal", itemParts(work.materiaal)],
    ["afmetingen", sizes.length ? [{ text: sizes.join(" × ") }] : []],
    ["collectie", itemParts(work.collectie)],
    ["inventarisnummer", inventory.map((text) => ({ text }))],
    ["locatie", itemParts(work.locatie)],
    ["plaats", itemParts(work.plaats)],
    ["links", (work.links || []).map((url) => ({ text: host(url), href: url }))],
  ];
  return rows.filter(([, parts]) => parts.length).map(([key, parts]) => ({ key, parts }));
});

watch(
  () => props.file,
  (file) => {
    if (file && !text.value) text.value = file.url;
  }
);


function submit() {
  if (text.value.trim()) emit("open", text.value.trim());
}
</script>
