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
            <img class="cc-item-beeld cc-item-beeld-klein" :src="itemImage(item.q, 60)" alt="" loading="lazy" @mouseenter="showZoom($event, item.q)" @mouseleave="hideZoom" @error="hideImage" />
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

        <!-- The proposals, with an (i) that explains a row, and All · None · Invert (wish Olaf). -->
        <div class="cc-origineel-kop">
          <h4 class="cc-commons-kop">{{ t("original.proposals") }} <info-dialog :title="t('original.proposals')" :label="t('panel.info_label', { section: t('original.proposals') })" :paragraphs="proposalsInfo" /></h4>
          <tick-links
            v-if="proposalRows.length"
            class="cc-klein cc-origineel-selectie"
            @all="proposalRows.forEach((row) => (row.checked = true))"
            @none="proposalRows.forEach((row) => (row.checked = false))"
            @invert="proposalRows.forEach((row) => (row.checked = !row.checked))"
          />
        </div>
        <busy-note v-if="resolving" :message="t('original.resolving')" />
        <p v-if="!proposalRows.length && !resolving" class="cc-uitleg">{{ t("original.proposals_none") }}</p>
        <ul class="cc-origineel-rijen">
          <original-row
            v-for="row in proposalRows"
            :key="row.key"
            v-bind="rowProps(row)"
            :ai="row.ai"
            :changeable="Boolean(row.terms.length || row.bronnen.includes('eigen'))"
            v-on="rowEvents(row)"
          >
            <template #source>
              <div class="cc-klein cc-origineel-bron">
                {{ row.bronnen.map((b) => t(`original.source_${b}`)).join(" · ") }}<template v-if="row.terms.length"> ({{ row.terms.join(", ") }})</template>
                <template v-if="row.objecten.length"> · {{ t("original.objects", { n: row.objecten.length }) }}</template>
              </div>
              <!-- Rule 4 of 9.7: an object whose cut-out is saved gets its region on the original
                   with its upload; one statement per object, not two. -->
              <div v-if="row.objecten.some((o) => o.upload)" class="cc-klein cc-origineel-upload">
                {{ t("original.with_upload", { n: row.objecten.filter((o) => o.upload).length, names: row.objecten.filter((o) => o.upload).map((o) => o.naam).join(", ") }) }}
              </div>
            </template>
            <!-- "With place", with an (i) that explains it for this very row (wish Olaf). -->
            <span v-if="row.objecten.length && !data.meerdere_paginas" class="cc-origineel-met-positie">
              <!-- The property links to Wikidata (a link inside a label does not tick the box). -->
              <label>
                <input v-model="row.met_positie" type="checkbox" />
                {{ t("original.with_position_before") }}
                (<a href="https://www.wikidata.org/wiki/Property:P2677" target="_blank" rel="noopener">P2677</a>)
                {{ t("original.with_position_after") }}
              </label>
              <info-dialog
                :title="t('original.with_position_title')"
                :label="t('panel.info_label', { section: t('original.with_position_title') })"
                :paragraphs="[
                  t('original.with_position_on', { item: row.label, n: row.objecten.length }),
                  t('original.with_position_off', { item: row.label }),
                  t('original.with_position_default'),
                ]"
              />
            </span>
          </original-row>
        </ul>
        <!-- Search terms without a found object: under their own heading, only along when ticked. -->
        <div v-if="emptyRows.length" class="cc-origineel-leeg">
          <h4 class="cc-commons-kop">{{ t("original.terms_without_objects", { n: emptyRows.length }) }}</h4>
          <ul class="cc-origineel-rijen">
            <!-- As the proposals above (wish Olaf): the item's image, its description, another item. -->
            <original-row v-for="row in emptyRows" :key="row.key" v-bind="rowProps(row)" ai changeable v-on="rowEvents(row)">
              <template #source>
                <div class="cc-klein cc-origineel-bron">{{ t("original.source_zoekterm") }} ({{ row.terms.join(", ") }}) · {{ t("original.no_objects") }}</div>
              </template>
            </original-row>
          </ul>
        </div>
        <!-- A row removed with the bin: yellow, with Undo (wish Olaf 13-11-2026). -->
        <undo-message :note="rowNote" />
        <p v-if="hidden.length" class="cc-klein">
          {{ t("original.hidden_rows", { n: hidden.length }) }}
          <button type="button" class="cc-link" @click="hidden = []">{{ t("original.hidden_show") }}</button>
        </p>
        <!-- Another item, for what the AI did not find. -->
        <div class="cc-origineel-zoek">
          <label class="cc-klein" for="cc-origineel-eigen">{{ t("original.add_item") }}</label>
          <cdx-text-input clearable id="cc-origineel-eigen" v-model="ownText" :placeholder="t('original.search_placeholder')" @update:model-value="searchOwn" />
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
        <div v-if="data.ai_caption.beschrijvingsniveau && data.ai_caption.beschrijvingsniveau !== 'caption'" class="cc-origineel-caption-vraag">
          <p class="cc-uitleg">{{ t("original.caption_level_note") }}</p>
          <!-- Ask the AI for a Commons caption (paid, with the confirmation of the app); the
               current description goes to Earlier descriptions. Or shorten it here, free. -->
          <cdx-button action="progressive" :disabled="busy" @click="emit('ask-caption')">
            {{ t("original.caption_ask") }} <span class="cc-kosten">{{ cost }}</span>
          </cdx-button>
          <busy-note v-if="busy" :message="t('busy.muse_page')" />
        </div>
        <p v-if="!data.ai_caption.nl && !data.ai_caption.en" class="cc-uitleg">{{ t("original.caption_no_ai") }}</p>
        <div v-for="lang in LANGUAGES" :key="lang" class="cc-origineel-caption">
          <h4 class="cc-commons-kop">{{ t(`original.lang_${lang}`) }}</h4>
          <p class="cc-klein"><strong>{{ t("original.caption_now") }}</strong> {{ captions[lang].existing || t("original.caption_none") }}</p>
          <p v-if="captions[lang].ai" class="cc-klein">
            <strong>{{ t("original.caption_ai") }}</strong> {{ captions[lang].ai }} <ai-badge kind="beschrijving" :model="''" />
          </p>
          <p v-if="captions[lang].ai && clean(captions[lang].ai).length > CAPTION_MAX" class="cc-klein cc-te-lang">
            {{ t("original.caption_ai_too_long", { n: clean(captions[lang].ai).length, max: CAPTION_MAX }) }}
            <button type="button" class="cc-link" @click="shorten(lang)">{{ t("original.caption_shorten") }}</button>
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

    <!-- A larger view of an item's image while the mouse is on its thumbnail (wish Olaf);
         on the page itself, so the dialog's edges do not cut it off. -->
    <teleport to="body">
      <img v-if="zoom.show" class="cc-item-zoom" :src="zoom.src" alt="" :style="{ left: `${zoom.x}px`, top: `${zoom.y}px` }" />
    </teleport>

    <template #footer>
      <div class="cc-origineel-voet">
        <p class="cc-klein">{{ t("original.summary", { depicts: chosenRows.length + addPosition.length, captions: changedCaptions }) }}</p>
        <cdx-message v-if="savedAt" type="success" :allow-user-dismiss="true" :dismiss-button-label="t('actions.close')" @user-dismissed="savedAt = ''">{{ t("original.saved") }}</cdx-message>
        <p v-if="tooLong" class="cc-klein cc-te-lang">{{ t("original.too_long_in", { languages: tooLongIn.map((lang) => t(`original.lang_${lang}`)).join(", ") }) }}</p>
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
import { computed, inject, nextTick, onBeforeUnmount, reactive, ref, watch } from "vue";
import { CdxButton, CdxDialog, CdxMessage, CdxRadio, CdxTab, CdxTabs, CdxTextArea, CdxTextInput } from "@wikimedia/codex";
import { errorText, get, pagePath, put } from "../api.js";
import { useT } from "../i18n.js";
import { itemImage, searchItems } from "../wikidata.js";
import { movableDialog } from "../movable.js";
import { commonsFileUrl } from "../state.js";
import AiBadge from "./AiBadge.vue";
import OriginalRow from "./OriginalRow.vue";
import TickLinks from "./TickLinks.vue";
import InfoDialog from "./InfoDialog.vue";
import BusyNote from "./BusyNote.vue";
import UndoMessage from "./UndoMessage.vue";
import { useUndoMessage } from "../undo.js";

const props = defineProps({
  open: { type: Boolean, default: false },
  file: { type: Object, required: true },
  page: { type: Object, required: true },
  // The page overview (for a new AI caption) and whether the app is busy asking it.
  inventory: { type: Object, default: null },
  busy: { type: Boolean, default: false },
  cost: { type: String, default: "" },
});
const emit = defineEmits(["close", "ask-caption"]);
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
// The image (P18) of a Wikidata item (itemImage); hidden when there is none.
const hideImage = (event) => (event.target.style.visibility = "hidden");
// A larger view beside the thumbnail, kept on screen; only for a thumbnail that loaded.
const ZOOM_SIZE = 260;
const zoom = reactive({ show: false, src: "", x: 0, y: 0 });
function showZoom(event, q) {
  const img = event.target;
  if (!img.naturalWidth) return;
  const rect = img.getBoundingClientRect();
  let x = rect.right + 8;
  if (x + ZOOM_SIZE > window.innerWidth) x = Math.max(0, rect.left - ZOOM_SIZE - 8);
  const y = Math.min(Math.max(0, rect.top - 40), window.innerHeight - ZOOM_SIZE - 8);
  Object.assign(zoom, { show: true, src: itemImage(q, 240), x, y });
}
const hideZoom = () => (zoom.show = false);
const commonsUrl = computed(() => commonsFileUrl(props.file.titel, "P180"));

// -- Loading and building the rows ---------------------------------------------------------

// Move by the title bar, resize at the edges (wish Olaf), as the magnifier; Codex renders
// the dialog elsewhere in the page (teleport). Double-click the title bar to centre it again.
const mover = movableDialog(".cc-origineel", {
  storageKey: "cc-origineel-plaats",
  labels: { move: t("magnifier.move"), resize: t("magnifier.resize") },
  min: { width: 420, height: 300 },
});
watch(
  () => props.open,
  async (open) => {
    if (!open) {
      mover.disable();
      return;
    }
    load();
    await nextTick();
    mover.enable();
  },
  { immediate: true }
);
onBeforeUnmount(() => mover.disable());

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
          const hits = await searchItems(row.search, "en");
          const term = row.search.trim().toLowerCase();
          // The label exactly as the term first ("lemon" the fruit, not "LemON" the band),
          // then the same letters in another case, then a label containing it, else the first hit.
          const hit =
            hits.find((h) => h.label === row.search.trim()) ||
            hits.find((h) => (h.label || "").toLowerCase() === term) ||
            hits.find((h) => (h.label || "").toLowerCase().includes(term)) ||
            hits[0];
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
    hidden.value = [...(d.concept.verborgen || [])];
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
// The (i) of the proposals: what a row shows and what "with place" means.
const proposalsInfo = computed(() => [1, 2, 3, 4, 5].map((n) => t(`original.info_${n}`)));
// Rows you removed with the bin (wish Olaf): out of view and unticked; kept in the draft.
const hidden = ref([]);
// Undo (only here, nothing was saved yet): the row back in view, ticked again when it was.
const rowNote = useUndoMessage(t);
function hideRow(row) {
  const q = row.q;
  const wasChecked = row.checked;
  row.checked = false;
  if (!hidden.value.includes(q)) hidden.value = [...hidden.value, q];
  rowNote.show("warning", t("feedback.row_hidden", { item: row.label || q }), () => {
    hidden.value = hidden.value.filter((h) => h !== q);
    if (wasChecked) {
      const back = merged.value.find((r) => r.q === q);
      if (back) back.checked = true;
    }
  }, { done: t("feedback.row_back", { item: row.label || q }) });
}
const visibleRows = computed(() => merged.value.filter((row) => !onCommons.value.has(row.q) && !hidden.value.includes(row.q)));
const proposalRows = computed(() => visibleRows.value.filter((row) => row.objecten.length || !row.bronnen.every((b) => b === "zoekterm")));
const emptyRows = computed(() => visibleRows.value.filter((row) => !row.objecten.length && row.bronnen.every((b) => b === "zoekterm")));
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
// What a row (OriginalRow.vue) shows of the search for another item, and what it can ask.
const rowProps = (row) => ({ row, searching: otherFor.value === row.key, text: otherText.value, hits: otherHits.value });
const rowEvents = (row) => ({
  other: () => startOther(row),
  "update:text": (text) => (otherText.value = text),
  search: searchOther,
  choose: (hit) => chooseOther(row, hit),
  cancel: () => (otherFor.value = null),
  hide: () => hideRow(row),
  zoom: showZoom,
  unzoom: hideZoom,
});
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
      include: stored ? stored.keuze === "toevoegen" : Boolean(ai) && clean(ai).length <= CAPTION_MAX,
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
// At most 250 characters: after the last whole sentence that fits, else the last whole
// word with "…" (the same rule as the server's cap_caption).
function capCaption(text) {
  const all = clean(text);
  if (all.length <= CAPTION_MAX) return all;
  const head = all.slice(0, CAPTION_MAX);
  const end = Math.max(head.lastIndexOf(". "), head.lastIndexOf("! "), head.lastIndexOf("? "), head.endsWith(".") ? head.length - 1 : -1);
  if (end >= CAPTION_MAX / 2) return head.slice(0, end + 1);
  return all.slice(0, CAPTION_MAX - 1).replace(/\s+\S*$/, "").replace(/[\s,;:]+$/, "") + "…";
}
// Shorten the AI proposal into the text field (free), and choose to use it.
function shorten(lang) {
  const c = captions[lang];
  c.tekst = capCaption(c.ai);
  if (c.existing) c.keuze = "zelf";
  else c.include = true;
}
// A new AI caption (asked from here): the proposals follow; your own edits stay.
watch(
  () => [props.inventory?.samenvatting, props.inventory?.samenvatting_en, props.inventory?.beschrijvingsniveau],
  ([nl, en, level]) => {
    if (!data.value) return;
    data.value.ai_caption = { nl: nl || "", en: en || "", beschrijvingsniveau: level || null };
    for (const lang of LANGUAGES) {
      const c = captions[lang];
      if (!c) continue;
      const untouched = clean(c.tekst) === clean(c.start);
      c.ai = (lang === "nl" ? nl : en) || "";
      c.start = c.existing ? [c.existing, c.ai].filter(Boolean).join("\n") : c.ai;
      if (untouched) c.tekst = c.start;
      if (!c.existing && clean(c.ai).length <= CAPTION_MAX && c.ai) c.include = true;
    }
  }
);

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
const tooLongIn = computed(() =>
  LANGUAGES.filter((lang) => {
    const choice = captionChoice(lang);
    return choice && choice.keuze !== "houden" && choice.tekst.length > CAPTION_MAX;
  })
);
const tooLong = computed(() => tooLongIn.value.length > 0);

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
      verborgen: hidden.value,
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
