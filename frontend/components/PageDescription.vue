<!--
  The description of the whole image (the "beschrijving" part of the page
  overview): kind and summary in Dutch and English, and the text read in and
  under the image. As with a cut-out (Magnifier.vue): a pencil after each text
  to edit it in place, "Met de hand aangepast" with "Terug naar de AI-tekst",
  "Ongedaan maken", and "Eerdere beschrijvingen": every version, by the AI or
  by hand, to use again or to delete. All of this is free; asking the AI anew
  and removing are events for the panel.
-->
<template>
  <div class="cc-pagina-beschrijving">
    <!-- First what makes the description (as with the search terms, wish Olaf): how long it is,
         and under the slider, side by side, asking anew (paid) and removing (free). -->
    <div class="cc-termen-bron">
      <detail-slider v-model="descLevel" :disabled="busy" :levels="DESCRIPTION_LEVELS" prefix="descdetail" compact />
      <!-- A Wikidata caption (at most 250 characters) in one click: puts the slider on that stop. -->
      <cdx-toggle-switch :model-value="descLevel === 'caption'" :disabled="busy" class="cc-wikidata-schakelaar" :title="t('descdetail.caption_help')" @update:model-value="setCaption">
        <svg class="cc-wikidata-logo" viewBox="0 0 22 14" aria-hidden="true" focusable="false">
          <rect x="0" y="0" width="2" height="14" fill="#990000" />
          <rect x="3" y="0" width="3" height="14" fill="#990000" />
          <rect x="7" y="0" width="3" height="14" fill="#339966" />
          <rect x="11" y="0" width="2" height="14" fill="#339966" />
          <rect x="14" y="0" width="3" height="14" fill="#006699" />
          <rect x="18" y="0" width="1" height="14" fill="#006699" />
          <rect x="20" y="0" width="2" height="14" fill="#006699" />
        </svg>
        {{ t("descdetail.caption_switch") }}
      </cdx-toggle-switch>
      <div class="cc-termen-knoppen">
        <cdx-button action="progressive" weight="quiet" size="small" :disabled="busy" :title="`${t('panel.part_again_help_beschrijving')} ${t('panel.parts_help')}`" @click="emit('again', descLevel)">
          {{ t(hasDescription ? "panel.part_again_beschrijving" : "panel.part_ask_beschrijving") }} <span class="cc-kosten">{{ cost }}</span>
        </cdx-button>
        <cdx-button v-if="hasDescription" action="destructive" weight="quiet" size="small" :disabled="busy" @click="emit('forget')">
          <cdx-icon :icon="cdxIconTrash" size="small" /> {{ t("panel.part_forget_beschrijving_button") }}
        </cdx-button>
      </div>
      <!-- Explanation under the buttons, like under the search terms (wish Olaf). -->
      <p class="cc-uitleg cc-termen-uitleg">{{ t("panel.description_help") }} {{ t("panel.parts_help") }}</p>
    </div>
    <div v-if="hasDescription || editing" class="cc-ai-resultaat">
      <template v-for="group in GROUPS" :key="group.key">
        <div v-if="editing === group.key" ref="editBox" class="cc-veld-bewerken">
          <cdx-field v-for="field in group.fields" :key="field">
            <template #label>{{ t(`page.field_${field}`) }}</template>
            <cdx-text-area v-if="group.long || field.startsWith('samenvatting')" v-model="draft[field]" :autosize="true" @keydown.esc.stop.prevent="cancel" />
            <cdx-text-input v-else v-model="draft[field]" @keydown.esc.stop.prevent="cancel" @keydown.enter="save" />
          </cdx-field>
          <div class="cc-knoppen">
            <cdx-button action="progressive" weight="primary" :disabled="!changed || busy" @click="save">{{ t("actions.save_short") }}</cdx-button>
            <cdx-button @click="cancel">{{ t("actions.cancel") }}</cdx-button>
          </div>
        </div>
        <div v-else-if="group.fields.some((f) => inventory[f])" class="cc-ai-groep">
          <template v-if="group.key === 'tekst'">
            <strong>{{ t("panel.inventory_text") }}</strong>
            <blockquote>{{ inventory.tekst }}{{ " " }}<edit-pencil :label="t(`page.group_${group.key}`)" :disabled="busy || Boolean(editing)" @click="start(group)" /></blockquote>
          </template>
          <p v-else :class="{ 'cc-ai-en': group.key === 'en' }">
            {{ inventory[group.fields[0]] }}<template v-if="inventory[group.fields[0]] && inventory[group.fields[1]]"> — </template>{{ inventory[group.fields[1]] }}
            <edit-pencil :label="t(`page.group_${group.key}`)" :disabled="busy || Boolean(editing)" @click="start(group)" />
            <ai-badge v-if="group.key === 'en' || (group.key === 'nl' && !inventory.samenvatting_en)" kind="pagina" :model="made.model" :edited="Boolean(inventory.bewerkt)" />
          </p>
        </div>
      </template>
    </div>
    <p v-else class="cc-uitleg">{{ t("panel.part_none_beschrijving") }}</p>

    <p v-if="inventory.bewerkt || undoTexts" class="cc-klein cc-tekst-acties">
      <template v-if="inventory.bewerkt">
        <cdx-info-chip>{{ t("describe.edited") }}</cdx-info-chip>
        <button type="button" class="cc-link" :disabled="busy" @click="backToAi">{{ t("describe.back_to_ai") }}</button>
      </template>
      <template v-if="undoTexts">
        {{ t("describe.saved_edit") }}
        <button type="button" class="cc-link" :disabled="busy" @click="undo">↶ {{ t("magnifier.undo") }}</button>
      </template>
    </p>
    <cdx-message v-if="error" type="error" :inline="true">{{ error }}</cdx-message>

    <!-- Earlier descriptions of the image, to use again or to delete (free). -->
    <cdx-accordion v-if="history.length" v-model="historyOpen" class="cc-beschrijving-blok">
      <template #title>{{ t("describe.history", { n: history.length }) }}</template>
      <template #description>{{ t("describe.history_short") }}</template>
      <!-- One version at a time: Previous / Next, "2 of 5" and dots (VersionCarousel.vue). -->
      <version-carousel :items="history" item-key="versie" :label="t('describe.history_short')">
        <template #default="{ item: entry }">
          <div
            class="cc-geschiedenis-tekstblok"
            :class="{ open: expanded[entry.versie] }"
            role="button"
            tabindex="0"
            :aria-expanded="expanded[entry.versie] ? 'true' : 'false'"
            :title="expanded[entry.versie] ? '' : fullText(entry)"
            @click="expanded[entry.versie] = !expanded[entry.versie]"
            @keydown.enter.space.prevent="expanded[entry.versie] = !expanded[entry.versie]"
          >
            <strong>{{ language === "en" ? entry.paginasoort_en || entry.paginasoort : entry.paginasoort || entry.paginasoort_en }}</strong>
            <span class="cc-klein cc-geschiedenis-beschrijving">{{ language === "en" ? entry.samenvatting_en || entry.samenvatting : entry.samenvatting || entry.samenvatting_en }}</span>
            <span v-if="entry.tekst" class="cc-klein cc-geschiedenis-beschrijving">{{ t("page.field_tekst") }}: {{ entry.tekst }}</span>
            <span class="cc-klein cc-geschiedenis-meta">{{ meta(entry) }}</span>
            <span class="cc-link cc-klein cc-geschiedenis-meer">{{ expanded[entry.versie] ? t("describe.history_less") : t("describe.history_more") }}</span>
          </div>
        </template>
        <template #actions="{ item: entry }">
          <cdx-button action="progressive" size="small" :disabled="busy" @click="use(entry)">{{ t("describe.history_use") }}</cdx-button>
          <cdx-button action="destructive" weight="quiet" size="small" :disabled="busy" :aria-label="t('describe.history_delete')" :title="t('describe.history_delete')" @click="remove(entry)">
            <cdx-icon :icon="cdxIconTrash" size="small" />
          </cdx-button>
        </template>
      </version-carousel>
    </cdx-accordion>
  </div>
</template>

<script setup>
import { computed, inject, nextTick, reactive, ref, watch } from "vue";
import { CdxAccordion, CdxButton, CdxField, CdxIcon, CdxInfoChip, CdxMessage, CdxTextArea, CdxTextInput, CdxToggleSwitch } from "@wikimedia/codex";
import { cdxIconTrash } from "@wikimedia/codex-icons";
import { del, errorText, get, pagePath, patch, put } from "../api.js";
import { fitToText } from "../autosize.js";
import { askConfirm } from "../confirm.js";
import { useT } from "../i18n.js";
import DetailSlider from "./DetailSlider.vue";
import VersionCarousel from "./VersionCarousel.vue";
import AiBadge from "./AiBadge.vue";
import EditPencil from "./EditPencil.vue";

const props = defineProps({
  mid: { type: String, required: true },
  n: { type: Number, required: true },
  inventory: { type: Object, required: true },
  busy: { type: Boolean, default: false },
  // The price of asking the description anew, e.g. "(US$ 0,0084)".
  cost: { type: String, default: "" },
});
// changed(overview): a new overview after an edit or a version put back; again; forget.
const emit = defineEmits(["changed", "again", "forget"]);
// The length of the description: that of the overview, else the last one chosen in this browser.
const DESCRIPTION_LEVELS = ["kort", "normaal", "caption", "uitgebreid"];
const DESC_KEY = "cc-beschrijvingsniveau";
function storedDescLevel() {
  try {
    return window.localStorage.getItem(DESC_KEY) || "normaal";
  } catch {
    return "normaal";
  }
}
const descLevel = ref(props.inventory?.beschrijvingsniveau || storedDescLevel());
// The Wikidata switch: on puts the slider on "caption"; off goes back to the stop before it.
let levelBeforeCaption = descLevel.value === "caption" ? "normaal" : descLevel.value;
function setCaption(on) {
  if (on) {
    if (descLevel.value !== "caption") levelBeforeCaption = descLevel.value;
    descLevel.value = "caption";
  } else {
    descLevel.value = levelBeforeCaption === "caption" ? "normaal" : levelBeforeCaption;
  }
}
watch(() => props.inventory?.beschrijvingsniveau, (level) => level && (descLevel.value = level));
watch(descLevel, (level) => {
  try {
    window.localStorage.setItem(DESC_KEY, level);
  } catch {
    // Blocked storage: the level holds until the page is reloaded.
  }
});
const t = useT();
const language = inject("language", "nl");

const FIELDS = ["paginasoort", "paginasoort_en", "samenvatting", "samenvatting_en", "tekst"];
const GROUPS = [
  { key: "nl", fields: ["paginasoort", "samenvatting"] },
  { key: "en", fields: ["paginasoort_en", "samenvatting_en"] },
  { key: "tekst", fields: ["tekst"], long: true },
];
const base = computed(() => `${pagePath(props.mid, props.n)}/inventaris`);
const hasDescription = computed(() => FIELDS.some((f) => props.inventory[f]));
// Model and time of the AI description: of the part asked anew, else of the overview.
const made = computed(() => props.inventory.delen?.beschrijving || props.inventory);
const error = ref("");

// Editing one group of texts in place.
const editing = ref(null);
const draft = ref({});
const editBox = ref(null);
const changed = computed(() => Object.entries(draft.value).some(([f, v]) => v.trim() !== (props.inventory[f] || "")));
async function start(group) {
  editing.value = group.key;
  draft.value = Object.fromEntries(group.fields.map((f) => [f, props.inventory[f] || ""]));
  await nextTick();
  const box = Array.isArray(editBox.value) ? editBox.value[0] : editBox.value;
  box?.querySelectorAll("textarea").forEach(fitToText);
  box?.querySelector("textarea, input")?.focus();
}
function cancel() {
  editing.value = null;
  draft.value = {};
}
function save() {
  if (changed.value) saveTexts({ ...draft.value });
}

// "Ongedaan maken": the texts as they were before the last change.
const undoTexts = ref(null);
const current = () => Object.fromEntries(FIELDS.map((f) => [f, props.inventory[f] || ""]));
async function saveTexts(texts, { undoable = true } = {}) {
  const before = current();
  error.value = "";
  try {
    emit("changed", (await patch(base.value, texts)).inventaris);
    cancel();
    undoTexts.value = undoable ? before : null;
  } catch (e) {
    error.value = errorText(t, e);
  }
}
const backToAi = () => saveTexts({ ...current(), ...props.inventory.ai_origineel });
const undo = () => saveTexts(undoTexts.value, { undoable: false });

// Earlier descriptions: reloaded whenever the overview changes (free).
const history = ref([]);
const historyOpen = ref(false);
async function loadHistory() {
  try {
    history.value = (await get(`${base.value}/geschiedenis`)).geschiedenis;
  } catch {
    history.value = [];
  }
}
watch(() => [props.mid, props.n, props.inventory], loadHistory, { immediate: true });

async function use(entry) {
  error.value = "";
  try {
    const result = await put(`${base.value}/beschrijving`, { versie: entry.versie });
    undoTexts.value = null;
    emit("changed", result.inventaris);
  } catch (e) {
    error.value = errorText(t, e);
  }
}
async function remove(entry) {
  if (!(await askConfirm(t("describe.history_delete_confirm"), { title: t("describe.history_delete"), go: t("describe.history_delete"), destructive: true }))) return;
  error.value = "";
  try {
    history.value = (await del(`${base.value}/geschiedenis/${encodeURIComponent(entry.versie)}`)).geschiedenis;
  } catch (e) {
    error.value = errorText(t, e);
  }
}

// Earlier versions: unfolded ones (by versie), and the whole text for the hover popup.
const expanded = reactive({});
function fullText(entry) {
  return [
    [entry.paginasoort, entry.samenvatting].filter(Boolean).join(" — "),
    [entry.paginasoort_en, entry.samenvatting_en].filter(Boolean).join(" — "),
    entry.tekst && `${t("page.field_tekst")}: ${entry.tekst}`,
  ].filter(Boolean).join("\n\n");
}

const time = (value) => (value ? new Date(value).toLocaleString(language, { dateStyle: "short", timeStyle: "short" }) : "");
function meta(entry) {
  if (entry.bewerkt_op) return t("describe.history_by_hand", { when: time(entry.bewerkt_op) });
  // An AI version also says how long it was asked to be (Short, Normal, Extensive); versions
  // that went into the history before this was kept do not know it, and then show nothing.
  const length = entry.beschrijvingsniveau ? t("descdetail.used", { level: t(`descdetail.${entry.beschrijvingsniveau}`) }) : "";
  return [time(entry.tijdstempel), entry.model, length].filter(Boolean).join(" · ");
}
</script>
