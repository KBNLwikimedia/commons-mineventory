<!--
  Asking a part of the image's AI suggestions anew (wish Olaf 13-11-2026): "Beschrijvingen
  opnieuw laten maken" and "Zoektermen opnieuw laten maken" (`part`). First what will happen and
  what it costs; then, folded away as a refinement, the prompt the AI gets for that part, which
  you may change, with your earlier prompts. Like the own prompt of "Wat staat hierop?" for an
  object, but in a window of its own, so the panel stays calm. The first time always goes with
  the app's prompt; this window is only for asking anew.
-->
<template>
  <cdx-dialog
    :open="open"
    class="cc-pagina-beschrijven"
    :title="t(key('title'))"
    :use-close-button="true"
    :close-button-label="t('actions.close')"
    :primary-action="{ label: goLabel, actionType: 'progressive', disabled: saving || !info || changed }"
    :default-action="{ label: t('actions.cancel') }"
    @primary="go"
    @default="emit('answer', false)"
    @update:open="(value) => !value && emit('answer', false)"
  >
    <p>{{ t(key("intro"), { level: levelText }) }}</p>
    <!-- Search terms: how many kinds the AI suggests, chosen here when asking anew (wish Olaf). -->
    <detail-slider v-if="part === 'zoektermen'" v-model="level" class="cc-pagina-detail" />
    <p class="cc-bevestig-noot">{{ t(key("note")) }}</p>
    <p v-if="costLine"><strong>{{ costLine }}</strong></p>

    <!-- AI steering, folded away (wish Olaf 13-11-2026): a hint at the end of the prompt, how hard
         the AI thinks (the price follows), and at the bottom the prompt itself. -->
    <cdx-accordion v-model="steerOpen" class="cc-pagina-prompt cc-ai-bijsturing">
      <template #title>{{ t("pagedescribe.steer_title") }}</template>
      <template #description>{{ steerSummary }}</template>
      <cdx-field class="cc-pagina-veld" :optional="true" :optional-flag="t('confirm.optional')">
        <template #label>{{ t("pagedescribe.hint_label") }}</template>
        <template #help-text>{{ t(key("hint_help")) }}</template>
        <cdx-text-input v-model="hint" clearable :placeholder="t(key('hint_placeholder'))" :maxlength="300" />
      </cdx-field>
      <cdx-field class="cc-pagina-veld" :is-fieldset="true">
        <template #label>{{ t("pagedescribe.effort_label") }}</template>
        <template #help-text>{{ t("pagedescribe.effort_help") }}</template>
        <cdx-radio v-for="level in EFFORTS" :key="level" v-model="effort" name="cc-pagina-redeneren" :input-value="level">
          {{ t(`pagedescribe.effort_${level}`) }}<span v-if="paid" class="cc-kosten"> ({{ money(costs[level], language) }})</span>
        </cdx-radio>
      </cdx-field>
      <!-- The prompt: the heaviest way to steer, inside AI steering and folded itself (wish Olaf). -->
      <cdx-accordion v-model="promptOpen" class="cc-pagina-prompt cc-ai-bijsturing-deel">
        <template #title>{{ t("pagedescribe.prompt_title") }}</template>
        <template #description>
          <span :class="{ 'cc-eigen-prompt': info?.eigen }">{{ info?.eigen ? t("describe.prompt_own_on", { time: formatTime(info.eigen_prompt?.bewaard_op) }) : t("describe.prompt_app") }}</span>
        </template>
        <p class="cc-uitleg">{{ t(key("prompt_help")) }}</p>
        <p v-if="error" class="cc-klein cc-te-lang">{{ error }}</p>
        <cdx-text-area v-model="draft" :rows="12" class="cc-eigen-prompt-veld" :disabled="!info || saving" :aria-label="t('pagedescribe.prompt_title')" />
        <!-- Only a saved prompt (yours, or the app's) goes to the AI (wish Olaf 13-11-2026): a changed
             one is saved first with this button, or the change is undone; until then
             "Beschrijvingen maken" is off. -->
        <div class="cc-pagina-prompt-acties">
          <cdx-button action="progressive" :disabled="!changed || saving" @click="save">{{ t("describe.prompt_save") }}</cdx-button>
          <button v-if="changed" type="button" class="cc-link" :disabled="saving" @click="undoChange">{{ t("pagedescribe.prompt_undo") }}</button>
          <button v-else-if="info?.eigen" type="button" class="cc-link" :disabled="saving" @click="backToApp">{{ t("describe.prompt_back") }}</button>
        </div>
        <p v-if="changed" class="cc-klein cc-pagina-prompt-let-op">{{ t(key("prompt_unsaved")) }}</p>
        <!-- What saving or using a prompt did, with Undo (wish Olaf 13-11-2026). -->
        <undo-message :note="note" />
        <template v-if="info?.geschiedenis?.length">
          <p class="cc-versie-label">{{ t("describe.prompt_history", { n: info.geschiedenis.length }) }}</p>
          <version-carousel :items="info.geschiedenis" item-key="bewaard_op" :label="t('describe.prompt_history_short')" :disabled="saving" @use="useEarlier" @delete="deleteEarlier">
            <template #default="{ item }">
              <pre class="cc-prompt-tekst cc-prompt-kort">{{ item.tekst }}</pre>
              <span class="cc-klein cc-geschiedenis-meta">{{ formatTime(item.bewaard_op) }}</span>
            </template>
          </version-carousel>
        </template>
      </cdx-accordion>
    </cdx-accordion>

  </cdx-dialog>
</template>

<script setup>
import { computed, inject, ref, watch } from "vue";
import { CdxAccordion, CdxButton, CdxDialog, CdxField, CdxRadio, CdxTextArea, CdxTextInput } from "@wikimedia/codex";
import { del, errorText, get, put } from "../api.js";
import { confirmDeleteVersion } from "../confirm.js";
import { formatStamp, money, useT } from "../i18n.js";
import VersionCarousel from "./VersionCarousel.vue";
import DetailSlider from "./DetailSlider.vue";
import UndoMessage from "./UndoMessage.vue";
import { promptBack, useUndoMessage } from "../undo.js";

const props = defineProps({
  open: { type: Boolean, default: false },
  // The page, e.g. /api/v1/bestand/M1/pagina/1.
  path: { type: String, default: "" },
  // Paid (live mode): the price shows on the button and in the cost line.
  paid: { type: Boolean, default: false },
  // What asking anew costs per reasoning effort ({low, medium, high} in USD).
  costs: { type: Object, default: () => ({}) },
  // The effort the app uses when you choose nothing (its setting).
  defaultEffort: { type: String, default: "low" },
  // Which part is asked anew: "beschrijving" or "zoektermen".
  part: { type: String, default: "beschrijving" },
  // For the search terms: the level of detail (DETAIL_LEVELS), which shapes the app's prompt.
  detail: { type: String, default: "" },
});
// answer: {hint, effort} to ask anew with the saved prompt, or false (cancelled).
const emit = defineEmits(["answer"]);
const t = useT();
const language = inject("language", "nl");

const info = ref(null); // {prompt, standaard_prompt, eigen, eigen_prompt, geschiedenis}
const draft = ref("");
const promptOpen = ref(false);
const saving = ref(false);
const error = ref("");
const promptUrl = computed(() => `${props.path}/inventaris/${props.part}/prompt`);
// The texts of this part: pagedescribe.* (description) or pageterms.* (search terms).
const key = (name) => `${props.part === "zoektermen" ? "pageterms" : "pagedescribe"}.${name}`;
// The level of detail of the search terms, chosen in this window (starts at the panel's).
const level = ref(props.detail || "normaal");
const levelText = computed(() => (level.value ? t(`detail.${level.value}`) : ""));
// Every keystroke counts as a change, also a space at the end (wish Olaf 13-11-2026); saving tidies
// spaces at the ends, and the tidy text then shows.
const changed = computed(() => Boolean(info.value) && draft.value !== (info.value.prompt || ""));
// AI steering: a hint and the reasoning effort, both for this one question.
const EFFORTS = ["low", "medium", "high"];
const steerOpen = ref(false);
const hint = ref("");
const effort = ref("low");
const amount = computed(() => props.costs?.[effort.value] ?? 0);
const price = computed(() => (props.paid ? `(${money(amount.value, language)})` : ""));
const costLine = computed(() => (props.paid ? t("confirm.cost", { n: 1, amount: money(amount.value, language) }) : ""));
const steerSummary = computed(() =>
  [
    hint.value.trim() ? t("pagedescribe.steer_hint", { hint: hint.value.trim() }) : t("pagedescribe.steer_no_hint"),
    t(`pagedescribe.effort_${effort.value}`),
    info.value?.eigen ? t("pagedescribe.steer_own_prompt") : t("pagedescribe.steer_app_prompt"),
  ].join(" · ")
);
const goLabel = computed(() => `${t(key("go"))}${price.value ? ` ${price.value}` : ""}`);

const promptQueryUrl = () => `${promptUrl.value}${props.part === "zoektermen" ? `?detailniveau=${encodeURIComponent(level.value)}` : ""}`;
// Another level of detail: the app's prompt follows; a change of your own in the text stays.
watch(level, async () => {
  if (!props.open || props.part !== "zoektermen" || !info.value) return;
  try {
    const answer = await get(promptQueryUrl());
    if (changed.value) info.value = { ...info.value, standaard_prompt: answer.standaard_prompt };
    else show(answer);
  } catch (failure) {
    error.value = errorText(t, failure);
  }
});
function show(answer) {
  info.value = answer;
  draft.value = answer.prompt || "";
}
// Each time the window opens: the prompt as it would go now, folded away.
watch(
  () => props.open,
  async (open) => {
    if (!open) return;
    info.value = null;
    draft.value = "";
    error.value = "";
    promptOpen.value = false;
    note.clear();
    steerOpen.value = false;
    hint.value = "";
    effort.value = EFFORTS.includes(props.defaultEffort) ? props.defaultEffort : "low";
    try {
      level.value = props.detail || "normaal";
      show(await get(promptQueryUrl()));
    } catch (failure) {
      error.value = errorText(t, failure);
    }
  }
);

// The message after a change of the prompt (undo.js): Undo goes back to the prompt before.
const note = useUndoMessage(t);
// `done`: the message afterwards; with `undoable` it gets Undo.
async function change(request, done, undoable = true) {
  saving.value = true;
  error.value = "";
  const back = promptBack(promptUrl.value, info.value);
  try {
    show(await request());
    note.show("success", done, undoable ? async () => show(await back()) : null);
    return true;
  } catch (failure) {
    error.value = errorText(t, failure);
    return false;
  } finally {
    saving.value = false;
  }
}
// The app's prompt typed back in is no prompt of your own: then back to the app's.
const typedApp = () => draft.value.trim() === (info.value?.standaard_prompt || "").trim();
const saveDraft = () => (typedApp() ? del(promptUrl.value) : put(promptUrl.value, { prompt: draft.value }));
const save = () => change(saveDraft, t(typedApp() ? "feedback.prompt_app" : "feedback.prompt_saved"));
const backToApp = () => change(() => del(promptUrl.value), t("feedback.prompt_app"));
// An earlier prompt was saved before: "Use this one" makes it the prompt at once, so
// "Beschrijvingen maken" can go straight away (wish Olaf 13-11-2026); only a change of your own
// still needs "Prompt bewaren".
const useEarlier = (entry) => change(() => put(promptUrl.value, { prompt: entry.tekst }), t("feedback.prompt_used"));
const undoChange = () => (draft.value = info.value?.prompt || "");
async function deleteEarlier(entry) {
  if (!(await confirmDeleteVersion(t("describe.prompt_history_delete_confirm"), t, entry.tekst))) return;
  await change(() => del(`${promptUrl.value}/geschiedenis/${encodeURIComponent(entry.bewaard_op)}`), t("feedback.version_deleted"), false);
}
// Describe anew, with the saved prompt (the button is off while a change is not saved).
function go() {
  if (changed.value) {
    steerOpen.value = true;
    promptOpen.value = true;
    return;
  }
  emit("answer", { hint: hint.value.trim(), effort: effort.value, ...(props.part === "zoektermen" ? { detail: level.value } : {}) });
}

const formatTime = (stamp) => formatStamp(stamp, language);
</script>
