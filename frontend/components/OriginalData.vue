<!--
  "Gegevens van deze afbeelding" (functional design 9.7, backlog 15b): depicts (P180) and
  captions for the whole image. Brings together what the file has on Commons and what
  this app proposes (items chosen for cut-outs, the AI search terms, the Wikidata
  suggestions of "Wat staat hierop?"), and keeps the user's choices as a draft.
  Free: nothing goes to a model, nothing changes on Commons; saving to Commons is phase 2.
-->
<template>
  <cdx-dialog
    :open="open"
    class="cc-origineel"
    :title="t('original.title')"
    :subtitle="file.titel"
    :use-close-button="true"
    :close-button-label="t('actions.close')"
    @update:open="(value) => !value && emit('close')"
  >
    <p class="cc-uitleg">
      {{ t("original.intro") }}
      <a :href="commonsUrl" target="_blank" rel="noopener">{{ t("panel.commons_edit_link") }}</a>
    </p>
    <busy-note v-if="loading" :message="t('original.loading')" />
    <cdx-message v-if="error" type="error">{{ error }}</cdx-message>

    <cdx-tabs v-if="data" v-model:active="tab" :framed="true" class="cc-origineel-tabs">
      <!-- 1. Depicts (P180) -->
      <cdx-tab name="beeldtaf" :label="t('original.tab_depicts', { n: chosenRows.length + addPosition.length })">
        <!-- What the file already has: read only; the app only adds (decision 2). -->
        <h4 class="cc-commons-kop">{{ t("original.on_commons", { n: data.op_commons.beeldt_af.length }) }}</h4>
        <p v-if="!data.op_commons.beeldt_af.length" class="cc-uitleg">{{ t("original.on_commons_none") }}</p>
        <ul v-else class="cc-origineel-commons">
          <li v-for="item in commonsItems" :key="item.q">
            <a :href="`https://www.wikidata.org/wiki/${item.q}`" target="_blank" rel="noopener">{{ item.label }}</a>
            <span class="cc-klein"> ({{ item.q }})</span>
            <span v-if="item.positions" class="cc-merkje">{{ t("original.with_position", { n: item.positions }) }}</span>
            <!-- Decision 3: an item that is there without a position, and that the app found: the user chooses. -->
            <label v-if="item.canAddPosition" class="cc-origineel-positie-toevoegen">
              <input v-model="addPosition" type="checkbox" :value="item.q" />
              {{ t("original.add_position", { n: item.found }) }}
            </label>
          </li>
        </ul>
        <p v-if="commonsItems.some((item) => item.canAddPosition)" class="cc-uitleg">{{ t("original.add_position_help") }}</p>
        <p class="cc-uitleg">{{ t("original.rules") }}</p>

        <h4 class="cc-commons-kop">{{ t("original.proposals") }}</h4>
        <busy-note v-if="resolving" :message="t('original.resolving')" />
        <p v-if="!proposalRows.length && !resolving" class="cc-uitleg">{{ t("original.proposals_none") }}</p>
        <ul class="cc-origineel-rijen">
          <li v-for="row in proposalRows" :key="row.key" class="cc-origineel-rij">
            <input v-model="row.checked" type="checkbox" :aria-label="t('original.include', { item: row.label })" />
            <div class="cc-origineel-item">
              <div>
                <a :href="`https://www.wikidata.org/wiki/${row.q}`" target="_blank" rel="noopener">{{ row.label }}</a>
                <span class="cc-klein"> ({{ row.q }})</span>
                <ai-badge v-if="row.ai" kind="beschrijving" :model="''" />
                <cdx-button v-if="row.terms.length || row.bronnen.includes('eigen')" action="progressive" weight="quiet" size="small" :aria-label="t('original.other_item')" :title="t('original.other_item')" @click="startOther(row)">
                  <cdx-icon :icon="cdxIconEdit" size="small" />
                </cdx-button>
              </div>
              <div v-if="row.beschrijving" class="cc-klein">{{ row.beschrijving }}</div>
              <div class="cc-klein cc-origineel-bron">
                {{ row.bronnen.map((b) => t(`original.source_${b}`)).join(" · ") }}<template v-if="row.terms.length"> ({{ row.terms.join(", ") }})</template>
                <template v-if="row.objecten.length"> · {{ t("original.objects", { n: row.objecten.length }) }}</template>
              </div>
              <!-- Rule 4 of 9.7: an object whose cut-out is saved gets its region on the original
                   with its upload; one statement per object, not two. -->
              <div v-if="row.objecten.some((o) => o.upload)" class="cc-klein cc-origineel-upload">
                {{ t("original.with_upload", { n: row.objecten.filter((o) => o.upload).length, names: row.objecten.filter((o) => o.upload).map((o) => o.naam).join(", ") }) }}
              </div>
              <!-- Another item for this row: search Wikidata (free) and pick. -->
              <div v-if="otherFor === row.key" class="cc-origineel-zoek">
                <cdx-text-input v-model="otherText" :placeholder="t('original.search_placeholder')" @update:model-value="searchOther" />
                <ul class="cc-origineel-treffers">
                  <li v-for="hit in otherHits" :key="hit.q">
                    <button type="button" class="cc-link" @click="chooseOther(row, hit)">{{ hit.label }}</button>
                    <span class="cc-klein"> ({{ hit.q }}) {{ hit.beschrijving }}</span>
                  </li>
                </ul>
                <button type="button" class="cc-link" @click="otherFor = null">{{ t("actions.cancel") }}</button>
              </div>
            </div>
            <label v-if="row.objecten.length && !data.meerdere_paginas" class="cc-origineel-met-positie" :title="t('original.with_position_help')">
              <input v-model="row.met_positie" type="checkbox" /> {{ t("original.with_position_toggle") }}
            </label>
          </li>
        </ul>
        <!-- Search terms without a found object: folded away, only along when ticked. -->
        <details v-if="emptyRows.length" class="cc-origineel-leeg">
          <summary>{{ t("original.terms_without_objects", { n: emptyRows.length }) }}</summary>
          <ul class="cc-origineel-rijen">
            <li v-for="row in emptyRows" :key="row.key" class="cc-origineel-rij">
              <input v-model="row.checked" type="checkbox" :aria-label="t('original.include', { item: row.label })" />
              <div class="cc-origineel-item">
                <a :href="`https://www.wikidata.org/wiki/${row.q}`" target="_blank" rel="noopener">{{ row.label }}</a>
                <span class="cc-klein"> ({{ row.q }}) · {{ row.terms.join(", ") }}</span>
                <ai-badge kind="beschrijving" :model="''" />
              </div>
            </li>
          </ul>
        </details>
        <!-- Another item, for what the AI did not find. -->
        <div class="cc-origineel-zoek">
          <label class="cc-klein" for="cc-origineel-eigen">{{ t("original.add_item") }}</label>
          <cdx-text-input id="cc-origineel-eigen" v-model="ownText" :placeholder="t('original.search_placeholder')" @update:model-value="searchOwn" />
          <ul class="cc-origineel-treffers">
            <li v-for="hit in ownHits" :key="hit.q">
              <button type="button" class="cc-link" @click="addOwn(hit)">{{ hit.label }}</button>
              <span class="cc-klein"> ({{ hit.q }}) {{ hit.beschrijving }}</span>
            </li>
          </ul>
        </div>
      </cdx-tab>

      <!-- 2. Captions -->
      <cdx-tab name="captions" :label="t('original.tab_captions', { n: changedCaptions })">
        <p v-if="data.ai_caption.beschrijvingsniveau && data.ai_caption.beschrijvingsniveau !== 'caption'" class="cc-uitleg">{{ t("original.caption_level_note") }}</p>
        <p v-if="!data.ai_caption.nl && !data.ai_caption.en" class="cc-uitleg">{{ t("original.caption_no_ai") }}</p>
        <div v-for="lang in LANGUAGES" :key="lang" class="cc-origineel-caption">
          <h4 class="cc-commons-kop">{{ t(`original.lang_${lang}`) }}</h4>
          <p class="cc-klein"><strong>{{ t("original.caption_now") }}</strong> {{ captions[lang].existing || t("original.caption_none") }}</p>
          <p v-if="captions[lang].ai" class="cc-klein">
            <strong>{{ t("original.caption_ai") }}</strong> {{ captions[lang].ai }} <ai-badge kind="beschrijving" :model="''" />
          </p>
          <!-- Without a caption on Commons: add (ticked), with an editable text. -->
          <template v-if="!captions[lang].existing">
            <label><input v-model="captions[lang].include" type="checkbox" /> {{ t("original.caption_add") }}</label>
          </template>
          <!-- With one: write it yourself (default, from both texts), keep it, or replace it. -->
          <div v-else class="cc-origineel-keuze" role="radiogroup">
            <cdx-radio v-for="choice in ['zelf', 'houden', 'vervangen']" :key="choice" v-model="captions[lang].keuze" :name="`cc-caption-${lang}`" :input-value="choice" :disabled="choice === 'vervangen' && !captions[lang].ai">
              {{ t(`original.caption_choice_${choice}`) }}
            </cdx-radio>
          </div>
          <template v-if="showText(lang)">
            <cdx-text-area v-model="captions[lang].tekst" :rows="3" :aria-label="t(`original.lang_${lang}`)" />
            <p class="cc-klein" :class="{ 'cc-te-lang': length(lang) > CAPTION_MAX }">
              {{ t("original.caption_count", { n: length(lang), max: CAPTION_MAX }) }}
              · <button type="button" class="cc-link" @click="resetText(lang)">{{ t("original.caption_reset") }}</button>
            </p>
          </template>
          <p v-if="captions[lang].existing && captions[lang].keuze === 'vervangen'" class="cc-klein">{{ t("original.caption_replace_note") }}</p>
        </div>
        <div v-if="otherCaptions.length">
          <h4 class="cc-commons-kop">{{ t("original.caption_other_languages") }}</h4>
          <ul class="cc-commons-captions">
            <li v-for="caption in otherCaptions" :key="caption.lang"><span class="cc-taal-code">{{ caption.lang }}</span> {{ caption.text }}</li>
          </ul>
        </div>
      </cdx-tab>
    </cdx-tabs>

    <template #footer>
      <div class="cc-origineel-voet">
        <p class="cc-klein">{{ t("original.summary", { depicts: chosenRows.length + addPosition.length, captions: changedCaptions }) }}</p>
        <cdx-message v-if="savedAt" type="success" :allow-user-dismiss="true" :dismiss-button-label="t('actions.close')" @user-dismissed="savedAt = ''">{{ t("original.saved") }}</cdx-message>
        <p v-if="tooLong" class="cc-klein cc-te-lang">{{ t("original.too_long") }}</p>
        <div class="cc-origineel-knoppen">
          <cdx-button @click="emit('close')">{{ t("actions.cancel") }}</cdx-button>
          <!-- Saving on Commons comes in phase 2 (after logging in): disabled, not hidden. -->
          <cdx-button action="progressive" disabled :title="t('original.to_commons_later')">{{ t("original.to_commons") }}</cdx-button>
          <cdx-button action="progressive" weight="primary" :disabled="!data || saving || tooLong" @click="save">{{ t("original.save_draft") }}</cdx-button>
        </div>
        <p class="cc-uitleg">{{ t("original.to_commons_later") }}</p>
      </div>
    </template>
  </cdx-dialog>
</template>

<script setup>
import { computed, inject, reactive, ref, watch } from "vue";
import { CdxButton, CdxDialog, CdxIcon, CdxMessage, CdxRadio, CdxTab, CdxTabs, CdxTextArea, CdxTextInput } from "@wikimedia/codex";
import { cdxIconEdit } from "@wikimedia/codex-icons";
import { errorText, get, pagePath, put } from "../api.js";
import { useT } from "../i18n.js";
import { searchItems } from "../wikidata.js";
import AiBadge from "./AiBadge.vue";
import BusyNote from "./BusyNote.vue";

const props = defineProps({
  open: { type: Boolean, default: false },
  file: { type: Object, required: true },
  page: { type: Object, required: true },
});
const emit = defineEmits(["close"]);
const t = useT();
const config = inject("config");

const LANGUAGES = ["nl", "en"];
const CAPTION_MAX = 250;
const tab = ref("beeldtaf");
const data = ref(null);
const loading = ref(false);
const resolving = ref(false);
const saving = ref(false);
const error = ref("");
const savedAt = ref("");
const rows = ref([]);
const addPosition = ref([]);
const captions = reactive({});
const commonsUrl = computed(() => `https://commons.wikimedia.org/wiki/${encodeURIComponent((props.file.titel || "").replace(/ /g, "_"))}#P180`);

// -- Loading and building the rows ---------------------------------------------------------

watch(
  () => props.open,
  (open) => open && load(),
  { immediate: true }
);

async function load() {
  loading.value = true;
  error.value = "";
  savedAt.value = "";
  tab.value = "beeldtaf";
  try {
    data.value = await get(`${pagePath(props.file.mid, props.page.n)}/origineel`);
    buildCaptions();
    await buildRows();
  } catch (e) {
    error.value = errorText(t, e);
  } finally {
    loading.value = false;
  }
}

function newRow(fields) {
  return { key: "", q: null, label: "", beschrijving: "", bronnen: [], terms: [], objecten: [], checked: false, met_positie: true, ai: false, ...fields };
}

async function buildRows() {
  const d = data.value;
  const list = [];
  for (const item of d.gekozen) list.push(newRow({ key: `q:${item.q}`, q: item.q, label: item.label, bronnen: ["gekozen"], objecten: item.objecten, checked: true }));
  for (const term of d.zoektermen) list.push(newRow({ key: `t:${term.en}`, bronnen: ["zoekterm"], terms: [config.taal === "nl" ? term.nl : term.en], search: term.en, objecten: term.objecten, ai: true }));
  for (const s of d.suggesties) list.push(newRow({ key: `s:${s.term}`, bronnen: ["suggestie"], terms: [s.term], search: s.term, objecten: s.objecten, ai: true }));
  // Your own items from an earlier draft.
  for (const entry of d.concept?.beeldt_af || []) {
    if (entry.bron === "eigen") list.push(newRow({ key: `e:${entry.q}`, q: entry.q, label: entry.label, bronnen: ["eigen"], checked: true, met_positie: false }));
  }
  // The AI terms are looked up on Wikidata (free, cached), a few at a time: the best hit.
  resolving.value = true;
  const open = list.filter((row) => row.search);
  for (let i = 0; i < open.length; i += 3) {
    await Promise.all(
      open.slice(i, i + 3).map(async (row) => {
        try {
          const hit = (await searchItems(row.search, "en"))[0];
          if (hit) Object.assign(row, { q: hit.q, label: hit.label, beschrijving: hit.beschrijving || "" });
        } catch {
          // No answer from Wikidata: the row stays without an item (not shown).
        }
      })
    );
  }
  resolving.value = false;
  // The draft: what was chosen, with another item where the user picked one.
  const draft = d.concept?.beeldt_af;
  if (draft) {
    for (const row of list) {
      const stored = draft.find((e) => (row.search && e.term === row.search) || (!row.search && e.q === row.q));
      if (stored) Object.assign(row, { q: stored.q, label: stored.label, checked: true, met_positie: stored.met_positie });
      else row.checked = false;
    }
    addPosition.value = [...(d.concept.positie_bij_bestaande || [])];
  }
  rows.value = list.filter((row) => row.q);
}

// The rows per item: the same item from several sources is one row (9.7).
const merged = computed(() => {
  const byQ = new Map();
  for (const row of rows.value) {
    const one = byQ.get(row.q);
    if (!one) {
      byQ.set(row.q, { ...row, members: [row], bronnen: [...row.bronnen], terms: [...row.terms], objecten: [...row.objecten] });
      continue;
    }
    one.members.push(row);
    for (const b of row.bronnen) if (!one.bronnen.includes(b)) one.bronnen.push(b);
    for (const term of row.terms) if (!one.terms.includes(term)) one.terms.push(term);
    for (const o of row.objecten) if (!one.objecten.some((x) => x.id === o.id)) one.objecten.push(o);
    one.ai = one.ai && row.ai;
  }
  // A checkbox of a merged row speaks for all its members.
  return [...byQ.values()].map((one) => reactiveRow(one));
});
function reactiveRow(one) {
  return {
    ...one,
    get checked() {
      return one.members.some((m) => m.checked);
    },
    set checked(value) {
      one.members.forEach((m) => (m.checked = value));
    },
    get met_positie() {
      return one.members.every((m) => m.met_positie);
    },
    set met_positie(value) {
      one.members.forEach((m) => (m.met_positie = value));
    },
  };
}

// What Commons already has, per item; an item there leaves the proposals (decision 2).
const commonsItems = computed(() => {
  const byQ = new Map();
  for (const s of data.value?.op_commons.beeldt_af || []) {
    const item = byQ.get(s.q) || { q: s.q, label: (config.taal === "en" ? s.label_en : s.label) || s.label || s.q, positions: 0 };
    if (s.positie) item.positions += 1;
    byQ.set(s.q, item);
  }
  for (const item of byQ.values()) {
    const found = merged.value.find((row) => row.q === item.q);
    item.found = found ? found.objecten.length : 0;
    item.canAddPosition = !item.positions && item.found > 0 && !data.value.meerdere_paginas;
  }
  return [...byQ.values()];
});
const onCommons = computed(() => new Set(commonsItems.value.map((item) => item.q)));
const proposalRows = computed(() => merged.value.filter((row) => !onCommons.value.has(row.q) && (row.objecten.length || !row.bronnen.every((b) => b === "zoekterm"))));
const emptyRows = computed(() => merged.value.filter((row) => !onCommons.value.has(row.q) && !row.objecten.length && row.bronnen.every((b) => b === "zoekterm")));
const chosenRows = computed(() => [...proposalRows.value, ...emptyRows.value].filter((row) => row.checked));

// -- Another item for a row, or an item of your own ---------------------------------------

const otherFor = ref(null);
const otherText = ref("");
const otherHits = ref([]);
let otherAsked = 0;
function startOther(row) {
  otherFor.value = row.key;
  otherText.value = row.terms[0] || row.label;
  searchOther(otherText.value);
}
async function searchOther(text) {
  const mine = ++otherAsked;
  if ((text || "").trim().length < 2) return (otherHits.value = []);
  const hits = await searchItems(text.trim(), config.taal).catch(() => []);
  if (mine === otherAsked) otherHits.value = hits;
}
function chooseOther(row, hit) {
  for (const member of row.members) Object.assign(member, { q: hit.q, label: hit.label, beschrijving: hit.beschrijving || "", checked: true });
  otherFor.value = null;
  otherHits.value = [];
}
const ownText = ref("");
const ownHits = ref([]);
let ownAsked = 0;
async function searchOwn(text) {
  const mine = ++ownAsked;
  if ((text || "").trim().length < 2) return (ownHits.value = []);
  const hits = await searchItems(text.trim(), config.taal).catch(() => []);
  if (mine === ownAsked) ownHits.value = hits;
}
function addOwn(hit) {
  if (!rows.value.some((row) => row.q === hit.q)) {
    rows.value.push(newRow({ key: `e:${hit.q}`, q: hit.q, label: hit.label, beschrijving: hit.beschrijving || "", bronnen: ["eigen"], checked: true, met_positie: false }));
  } else {
    rows.value.filter((row) => row.q === hit.q).forEach((row) => (row.checked = true));
  }
  ownText.value = "";
  ownHits.value = [];
}

// -- Captions -------------------------------------------------------------------------------

function buildCaptions() {
  const d = data.value;
  for (const lang of LANGUAGES) {
    const existing = d.op_commons.captions[lang] || "";
    const ai = (lang === "nl" ? d.ai_caption.nl : d.ai_caption.en) || "";
    const stored = d.concept?.captions?.[lang];
    const start = existing ? [existing, ai].filter(Boolean).join("\n") : ai;
    captions[lang] = {
      existing,
      ai,
      start,
      include: stored ? stored.keuze === "toevoegen" : Boolean(ai),
      keuze: stored ? (existing ? stored.keuze : "toevoegen") : existing ? "zelf" : "toevoegen",
      tekst: stored?.tekst || start,
    };
  }
}
const otherCaptions = computed(() =>
  Object.entries(data.value?.op_commons.captions || {})
    .filter(([lang, text]) => text && !LANGUAGES.includes(lang))
    .map(([lang, text]) => ({ lang, text }))
);
const showText = (lang) => (captions[lang].existing ? captions[lang].keuze === "zelf" : captions[lang].include);
const clean = (text) => String(text || "").split(/\s+/).filter(Boolean).join(" ");
const length = (lang) => clean(captions[lang].tekst).length;
function resetText(lang) {
  captions[lang].tekst = captions[lang].start;
}
// What each language would do: nothing, add, replace, or your own text.
function captionChoice(lang) {
  const c = captions[lang];
  if (!c) return null;
  if (!c.existing) return c.include && clean(c.tekst) ? { keuze: "toevoegen", tekst: clean(c.tekst) } : { keuze: "houden", tekst: "" };
  if (c.keuze === "vervangen") return { keuze: "vervangen", tekst: clean(c.ai) };
  // Your own text only counts once you changed it: the untouched start (both texts) changes nothing.
  if (c.keuze === "zelf") return clean(c.tekst) === clean(c.start) ? { keuze: "houden", tekst: "" } : { keuze: "zelf", tekst: clean(c.tekst) };
  return { keuze: "houden", tekst: "" };
}
const changedCaptions = computed(() =>
  LANGUAGES.filter((lang) => {
    const choice = captionChoice(lang);
    return choice && choice.keuze !== "houden" && choice.tekst && choice.tekst !== clean(captions[lang].existing);
  }).length
);
const tooLong = computed(() => LANGUAGES.some((lang) => captions[lang] && showText(lang) && length(lang) > CAPTION_MAX));

// -- Saving the draft -----------------------------------------------------------------------

async function save() {
  saving.value = true;
  error.value = "";
  try {
    const body = {
      beeldt_af: chosenRows.value.map((row) => ({
        q: row.q,
        label: row.label,
        met_positie: Boolean(row.met_positie && row.objecten.length),
        objecten: row.objecten.map((o) => o.id),
        bron: row.bronnen[0],
        term: row.members.find((m) => m.search)?.search || null,
      })),
      positie_bij_bestaande: addPosition.value,
      captions: Object.fromEntries(LANGUAGES.map((lang) => [lang, captionChoice(lang)])),
    };
    const result = await put(`${pagePath(props.file.mid, props.page.n)}/origineel`, body);
    data.value.concept = result.concept;
    savedAt.value = result.concept.bewaard_op;
  } catch (e) {
    error.value = errorText(t, e);
  } finally {
    saving.value = false;
  }
}
</script>
