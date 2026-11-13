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
      <!-- All four lengths come at once: the slider shows another one, live and free (wish Olaf). -->
      <detail-slider v-model="descLevel" :disabled="busy || Boolean(editing)" :levels="DESCRIPTION_LEVELS" prefix="descdetail" compact>
        <!-- A Commons caption (at most 250 characters) in one click: puts the slider on that stop.
             A caption belongs to the structured data on Commons, hence a Commons mark (wish Olaf).
             Right behind the slider, without a text of its own: the slider already names the
             length, so "Commons caption" is not said twice (wish Olaf 13-11-2026). -->
        <template #after>
          <span class="cc-caption-schakelaar" :title="t('descdetail.caption_help')">
            <cdx-toggle-switch :model-value="descLevel === 'caption'" :disabled="busy || Boolean(editing)" :aria-label="t('descdetail.caption_switch')" @update:model-value="setCaption" />
            <commons-logo colour />
          </span>
        </template>
      </detail-slider>
      <div class="cc-termen-knoppen">
        <cdx-button action="progressive" weight="quiet" size="small" :disabled="busy" :title="`${t('panel.part_again_help_beschrijving')} ${t('panel.parts_help')}`" @click="emit('again', descLevel)">
          {{ t(hasDescription ? "panel.part_again_beschrijving" : "panel.part_ask_beschrijving") }} <span class="cc-kosten">{{ cost }}</span>
        </cdx-button>
        <cdx-button v-if="hasDescription" action="destructive" weight="quiet" size="small" :disabled="busy" @click="emit('forget')">
          <cdx-icon :icon="cdxIconTrash" size="small" /> {{ t("panel.part_forget_beschrijving_button") }}
        </cdx-button>
      </div>
      <!-- While the AI works: the waiting bar right under the button that asked (wish Olaf, 12-11-2026). -->
      <slot name="wachten" />
      <!-- Explanation under the buttons, like under the search terms (wish Olaf). -->
      <p class="cc-uitleg cc-termen-uitleg">{{ t("panel.description_help") }} {{ t("panel.parts_help") }}</p>
    </div>
    <!-- A description from before the four lengths has only the one it was asked in. -->
    <!-- Made with the four lengths, but the AI left this one empty: another message (asking anew helps). -->
    <p v-if="lengthMissing" class="cc-uitleg cc-lengte-ontbreekt">{{ lengthMissingText }}</p>
    <div v-if="hasDescription || editing" class="cc-ai-resultaat">
      <template v-for="group in GROUPS" :key="group.key">
        <div v-if="editing === group.key" ref="editBox" class="cc-veld-bewerken">
          <cdx-field v-for="field in group.fields" :key="field">
            <template #label>{{ t(`page.field_${field}`) }}</template>
            <cdx-text-area v-if="group.long || field.startsWith('samenvatting')" v-model="draft[field]" :autosize="true" @keydown.esc.stop.prevent="cancel" />
            <cdx-text-input v-else v-model="draft[field]" @keydown.esc.stop.prevent="cancel" @keydown.enter="save" />
            <!-- A Commons caption may hold at most 250 characters: count while you edit (wish Olaf). -->
            <template v-if="captionField(field)" #help-text>
              <span :class="{ 'cc-te-lang': captionLength(field) > CAPTION_MAX }">{{ t(captionLength(field) > CAPTION_MAX ? "page.caption_too_long" : "original.caption_count", { n: captionLength(field), max: CAPTION_MAX }) }}</span>
            </template>
          </cdx-field>
          <div class="cc-knoppen">
            <cdx-button action="progressive" weight="primary" :disabled="!changed || busy || captionTooLong" @click="save">{{ t("actions.save_short") }}</cdx-button>
            <cdx-button @click="cancel">{{ t("actions.cancel") }}</cdx-button>
          </div>
        </div>
        <div v-else-if="group.fields.some((f) => inventory[f])" class="cc-ai-groep">
          <template v-if="group.key === 'tekst'">
            <strong>{{ t("panel.inventory_text") }}</strong>
            <blockquote>{{ inventory.tekst }}{{ " " }}<edit-pencil :label="t(`page.group_${group.key}`)" :disabled="busy || Boolean(editing)" @click="start(group)" /></blockquote>
          </template>
          <!-- A box of fixed height that scrolls when the text is longer: the slider changes the
               length of the text, not the height of the page (wish Olaf, 12-11-2026). -->
          <div v-else class="cc-lengte-vak">
            <p class="cc-lengte-tekst" :class="{ 'cc-ai-en': group.key === 'en' }" tabindex="0">
              {{ inventory[group.fields[0]] }}<template v-if="inventory[group.fields[0]] && inventory[group.fields[1]]"> — </template>{{ inventory[group.fields[1]] }}
            </p>
            <span class="cc-lengte-acties">
              <edit-pencil :label="t(`page.group_${group.key}`)" :disabled="busy || Boolean(editing)" @click="start(group)" />
              <ai-badge v-if="group.key === 'en' || (group.key === 'nl' && !inventory.samenvatting_en)" kind="pagina" :model="made.model" :edited="Boolean(inventory.bewerkt)" />
            </span>
          </div>
        </div>
      </template>
    </div>
    <p v-else class="cc-uitleg">{{ t("panel.part_none_beschrijving") }}</p>

    <p v-if="inventory.bewerkt" class="cc-klein cc-tekst-acties">
      <cdx-info-chip>{{ t("describe.edited") }}</cdx-info-chip>
      <button type="button" class="cc-link" :disabled="busy" @click="backToAi">{{ t("describe.back_to_ai") }}</button>
    </p>
    <cdx-message v-if="error" type="error" :inline="true">{{ error }}</cdx-message>
    <!-- What the last change did (texts saved, an earlier version used or deleted), with Undo. -->
    <undo-message :note="note" />

    <!-- Earlier descriptions of the image, to use again or to delete (free). -->
    <cdx-accordion v-if="history.length" v-model="historyOpen" class="cc-beschrijving-blok">
      <template #title>{{ t("describe.history", { n: history.length }) }}</template>
      <template #description>{{ t("describe.history_short") }}</template>
      <!-- One version at a time: Previous / Next, "2 of 5" and dots (VersionCarousel.vue). -->
      <version-carousel :items="history" item-key="versie" :label="t('describe.history_short')" :disabled="busy" @use="use" @delete="remove">
        <template #default="{ item: entry }">
          <version-entry v-model:open="expanded[entry.versie]" :title="fullText(entry)" :meta="meta(entry)">
            <div class="cc-versie-veld">
              <span class="cc-versie-label">{{ t("version.kind") }}</span>
              <strong>{{ language === "en" ? entry.paginasoort_en || entry.paginasoort : entry.paginasoort || entry.paginasoort_en }}</strong>
            </div>
            <div class="cc-versie-veld">
              <span class="cc-versie-label">{{ t("version.description") }}</span>
              <span class="cc-geschiedenis-beschrijving">{{ entryText(entry, language === "en" ? "en" : "nl") || entryText(entry, language === "en" ? "nl" : "en") }}</span>
            </div>
            <div v-if="entry.tekst" class="cc-versie-veld cc-versie-tekst">
              <span class="cc-versie-label">{{ t("page.field_tekst") }}</span>
              <span class="cc-geschiedenis-beschrijving">{{ readLines(entry.tekst) }}</span>
            </div>
          </version-entry>
        </template>
      </version-carousel>
    </cdx-accordion>
  </div>
</template>

<script setup>
import CommonsLogo from "./CommonsLogo.vue";
import { computed, inject, nextTick, reactive, ref, watch } from "vue";
import { CdxAccordion, CdxButton, CdxField, CdxIcon, CdxInfoChip, CdxMessage, CdxTextArea, CdxTextInput, CdxToggleSwitch } from "@wikimedia/codex";
import { cdxIconTrash } from "@wikimedia/codex-icons";
import { del, errorText, get, pagePath, patch, put } from "../api.js";
import { fitToText } from "../autosize.js";
import { confirmDeleteVersion } from "../confirm.js";
import { formatStamp, useT } from "../i18n.js";
import { readStored, writeStored } from "../storage.js";
import DetailSlider from "./DetailSlider.vue";
import VersionCarousel from "./VersionCarousel.vue";
import VersionEntry from "./VersionEntry.vue";
import AiBadge from "./AiBadge.vue";
import EditPencil from "./EditPencil.vue";
import UndoMessage from "./UndoMessage.vue";
import { pageDescriptionVersion, useUndoMessage, versionBack } from "../undo.js";

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
// The length of the description: that of the overview, else the last one chosen in this browser,
// else a Commons caption (the default of a new description, wish Olaf 11-11-2026).
const DESCRIPTION_LEVELS = ["kort", "normaal", "caption", "uitgebreid"];
const DESC_KEY = "cc-beschrijvingsniveau";
const descLevel = ref(props.inventory?.beschrijvingsniveau || readStored(DESC_KEY, "caption"));
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
  writeStored(DESC_KEY, level);
  // Another length that was made with the others: show it (free, no new version). Each length
  // keeps its own hand edits; "Ongedaan maken" belonged to the length you left.
  if (level !== props.inventory?.beschrijvingsniveau && props.inventory?.beschrijvingen?.[level]) showLength(level);
});
async function showLength(level) {
  error.value = "";
  try {
    const result = await patch(base.value, { beschrijvingsniveau: level });
    note.clear();
    emit("changed", result.inventaris);
  } catch (e) {
    error.value = errorText(t, e);
  }
}
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
// The slider on a length this description does not have (asked before 0.39.0): ask anew for all four.
// Made with the four lengths but this one came back empty, or made before the four lengths.
const lengthMissingText = computed(() =>
  Object.keys(props.inventory.beschrijvingen || {}).length
    ? t("page.length_empty", { level: t(`descdetail.${descLevel.value}`) })
    : t("page.length_not_made", { level: t(`descdetail.${props.inventory.beschrijvingsniveau || "normaal"}`) }),
);
const lengthMissing = computed(() =>hasDescription.value && descLevel.value !== props.inventory.beschrijvingsniveau && !props.inventory.beschrijvingen?.[descLevel.value]);
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
// A description made as a Commons caption: its summary must stay within 250 characters.
const CAPTION_MAX = 250;
const captionField = (field) => props.inventory?.beschrijvingsniveau === "caption" && field.startsWith("samenvatting");
const captionLength = (field) => (draft.value[field] || "").split(/\s+/).filter(Boolean).join(" ").length;
const captionTooLong = computed(() => Object.keys(draft.value).some((f) => captionField(f) && captionLength(f) > CAPTION_MAX));
function save() {
  if (changed.value && !captionTooLong.value) saveTexts({ ...draft.value });
}

// The message after a change (undo.js); "Ongedaan maken" puts back the texts as they were.
const note = useUndoMessage(t);
watch(() => [props.mid, props.n], () => note.clear());
const current = () => Object.fromEntries(FIELDS.map((f) => [f, props.inventory[f] || ""]));
async function saveTexts(texts) {
  const before = current();
  const path = base.value;
  error.value = "";
  try {
    emit("changed", (await patch(path, texts)).inventaris);
    cancel();
    note.show("success", t("describe.saved_edit"), async () => emit("changed", (await patch(path, before)).inventaris));
  } catch (e) {
    error.value = errorText(t, e);
  }
}
const backToAi = () => saveTexts({ ...current(), ...props.inventory.ai_origineel });

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

// An earlier version made current; Undo puts back the one it replaced (or removes it again
// when there was none: DELETE on the same path).
async function use(entry) {
  error.value = "";
  const path = `${base.value}/beschrijving`;
  const back = versionBack(path, "versie", pageDescriptionVersion(props.inventory));
  try {
    emit("changed", (await put(path, { versie: entry.versie })).inventaris);
    note.show("success", t("feedback.version_used"), async () => emit("changed", (await back()).inventaris));
  } catch (e) {
    error.value = errorText(t, e);
  }
}
async function remove(entry) {
  const kind = language === "en" ? entry.paginasoort_en || entry.paginasoort : entry.paginasoort || entry.paginasoort_en;
  const text = entryText(entry, language === "en" ? "en" : "nl") || entryText(entry, language === "en" ? "nl" : "en");
  if (!(await confirmDeleteVersion(t("describe.history_delete_confirm"), t, [kind, text].filter(Boolean).join("\n")))) return;
  error.value = "";
  try {
    history.value = (await del(`${base.value}/geschiedenis/${encodeURIComponent(entry.versie)}`)).geschiedenis;
    note.show("success", t("feedback.version_deleted"));
  } catch (e) {
    error.value = errorText(t, e);
  }
}

// Earlier versions: unfolded ones (by versie), and the whole text for the hover popup.
const expanded = reactive({});
// The text of an earlier version at the length on the slider (a version holds all four lengths
// since 0.39.0); an older version has only its own length.
function entryText(entry, lang) {
  const length = entry.beschrijvingen?.[descLevel.value];
  if (length) return length[lang] || "";
  return lang === "en" ? entry.samenvatting_en : entry.samenvatting;
}
// The text read from the image is kept with " | " between its lines: one line each again.
const readLines = (text) => String(text || "").split(/\s*\|\s*/).join("\n");
function fullText(entry) {
  return [
    [entry.paginasoort, entryText(entry, "nl")].filter(Boolean).join(" — "),
    [entry.paginasoort_en, entryText(entry, "en")].filter(Boolean).join(" — "),
    entry.tekst && `${t("page.field_tekst")}: ${entry.tekst}`,
  ].filter(Boolean).join("\n\n");
}

const time = (value) => formatStamp(value, language, "short");
function meta(entry) {
  if (entry.bewerkt_op) return t("describe.history_by_hand", { when: time(entry.bewerkt_op) });
  // An AI version also says how long it was asked to be (Short, Normal, Extensive); versions
  // that went into the history before this was kept do not know it, and then show nothing.
  const length = entry.beschrijvingen ? t("descdetail.all_lengths") : entry.beschrijvingsniveau ? t("descdetail.used", { level: t(`descdetail.${entry.beschrijvingsniveau}`) }) : "";
  return [time(entry.tijdstempel), entry.model, length].filter(Boolean).join(" · ");
}
</script>
