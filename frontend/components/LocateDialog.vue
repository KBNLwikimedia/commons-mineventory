<!--
  Locating with the AI image detection (SAM): what will be searched, saved answers or SAM anew,
  and the cost; then, folded away as AI steering (wish Olaf 13-11-2026), the search words SAM
  gets, which you may change before searching (e.g. "sailor hat" into "white sailor hat"). SAM
  takes only the image and a short English word, so the word is its prompt. What a changed word
  finds counts under the term it stands for, so that term's button keeps its count. The cost
  follows the words: a word not searched before is a new, paid question.
-->
<template>
  <cdx-dialog
    :open="open"
    class="cc-bevestig cc-lokaliseren"
    :title="t(inCache ? 'confirm.detect_title' : 'locate.title')"
    :use-close-button="true"
    :close-button-label="t('actions.close')"
    :primary-action="{ label: goLabel, actionType: 'progressive', disabled: !estimate || !words.some((w) => w.trim()) || estimating }"
    :default-action="{ label: t('actions.cancel') }"
    @primary="go"
    @default="emit('answer', null)"
    @update:open="(value) => !value && emit('answer', null)"
  >
    <p>{{ t("locate.intro") }}</p>
    <ul class="cc-lokaliseren-termen">
      <li v-for="(word, i) in shownWords" :key="i">{{ word }}</li>
    </ul>
    <p class="cc-bevestig-noot">{{ t("locate.note") }}</p>

    <!-- Saved answers (free) or SAM anew (paid) when some words were searched before; else the cost. -->
    <template v-if="estimate">
      <template v-if="inCache">
        <p>{{ inCache >= total ? t("confirm.detect_saved_all") : t("confirm.detect_saved", { n: inCache, total }) }}</p>
        <div class="cc-bevestig-keuze" role="radiogroup">
          <cdx-radio v-model="choice" name="cc-lokaliseren-keuze" input-value="cache">
            {{ t("confirm.detect_choice_saved", { amount: usd(paidCalls) }) }}
            <template #description>{{ t(paidCalls ? "confirm.detect_choice_saved_help_new" : "confirm.detect_choice_saved_help", { n: total - inCache }) }}</template>
          </cdx-radio>
          <cdx-radio v-model="choice" name="cc-lokaliseren-keuze" input-value="vers">
            {{ t("confirm.detect_choice_fresh", { amount: usd(total) }) }}
            <template #description>{{ t("confirm.detect_choice_fresh_help", { n: total }) }}</template>
          </cdx-radio>
        </div>
      </template>
      <p v-else-if="paid"><strong>{{ t("confirm.cost", { n: paidCalls, amount: usd(paidCalls) }) }}</strong></p>
    </template>
    <p v-else-if="error" class="cc-klein cc-te-lang">{{ error }}</p>

    <!-- AI steering: the words SAM gets, folded away (wish Olaf 13-11-2026). -->
    <cdx-accordion v-model="steerOpen" class="cc-pagina-prompt cc-ai-bijsturing">
      <template #title>{{ t("pagedescribe.steer_title") }}</template>
      <template #description>{{ changedCount ? t("locate.steer_changed", { n: changedCount }) : t("locate.steer_none") }}</template>
      <cdx-message v-if="askWord" type="warning" :inline="true" class="cc-pagina-veld">{{ t("locate.no_english") }}</cdx-message>
      <cdx-field class="cc-pagina-veld" :is-fieldset="true">
        <template #label>{{ t("locate.words_label") }}</template>
        <template #help-text>{{ t("locate.words_help") }}</template>
        <div v-for="(term, i) in terms" :key="i" class="cc-lokaliseren-woord">
          <cdx-text-input v-model="words[i]" clearable :aria-label="t('locate.word_for', { term: term.term })" />
          <span v-if="words[i].trim() && words[i].trim().toLowerCase() !== term.en.toLowerCase()" class="cc-klein">
            {{ t("locate.counts_as", { term: term.term }) }} · <button type="button" class="cc-link" @click="words[i] = term.en">{{ t("locate.word_back") }}</button>
          </span>
          <span v-else-if="term.term.toLowerCase() !== term.en.toLowerCase()" class="cc-klein">{{ t("locate.translated", { term: term.term }) }}</span>
        </div>
      </cdx-field>
    </cdx-accordion>
  </cdx-dialog>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { CdxAccordion, CdxDialog, CdxField, CdxMessage, CdxRadio, CdxTextInput } from "@wikimedia/codex";
import { errorText, get } from "../api.js";
import { money, useT } from "../i18n.js";

const props = defineProps({
  open: { type: Boolean, default: false },
  // The page, e.g. /api/v1/bestand/M1/pagina/1.
  path: { type: String, default: "" },
  // The search as asked: "man, sailor hat min text".
  prompt: { type: String, default: "" },
  paid: { type: Boolean, default: false },
  samUsd: { type: Number, default: 0 },
  language: { type: String, default: "nl" },
  // An item without an English label on Wikidata: open the words at once and ask for an English one.
  askWord: { type: Boolean, default: false },
});
// answer: {prompt, als, fresh} to locate, or null when cancelled.
const emit = defineEmits(["answer"]);
const t = useT();

const terms = ref([]); // the words to search for: [{term, en}]
const minus = ref([]); // words to leave out ("min"), kept as they are
const words = ref([]); // the English word per term, as SAM gets it (editable)
const estimate = ref(null);
const estimating = ref(false);
const error = ref("");
const choice = ref("cache");
const steerOpen = ref(false);

const usd = (calls) => money(props.paid ? calls * props.samUsd : 0, props.language);
const shownWords = computed(() => words.value.map((w) => w.trim()).filter(Boolean));
const changedCount = computed(() => terms.value.filter((term, i) => (words.value[i] || "").trim().toLowerCase() !== term.en.toLowerCase()).length);
// The search as it goes: the (changed) words, then the words to leave out.
const searchPrompt = computed(() => [shownWords.value.join(", "), ...minus.value.map((m) => `min ${m.term}`)].join(" "));
const calls = computed(() => estimate.value?.aanroepen || {});
const inCache = computed(() => calls.value.in_cache || 0);
const total = computed(() => calls.value.termen || 0);
const paidCalls = computed(() => calls.value.betaald || 0);
const goLabel = computed(() => {
  if (inCache.value && choice.value === "vers") return t("confirm.detect_go_fresh", { amount: usd(total.value) });
  if (inCache.value) return t("confirm.detect_go_saved");
  return props.paid ? `${t("confirm.detect_go_saved")} (${usd(paidCalls.value)})` : t("confirm.detect_go_saved");
});

async function estimateNow(prompt) {
  estimating.value = true;
  error.value = "";
  try {
    const answer = await get(`${props.path}/detecties/raming?prompt=${encodeURIComponent(prompt)}&modus=prompt`);
    if (prompt === searchPrompt.value || !terms.value.length) estimate.value = answer;
    return answer;
  } catch (failure) {
    error.value = errorText(t, failure);
    estimate.value = null;
    return null;
  } finally {
    estimating.value = false;
  }
}

// Each time it opens: the terms as the server reads them (with their English word), and the cost.
watch(
  () => props.open,
  async (open) => {
    if (!open) return;
    terms.value = [];
    minus.value = [];
    words.value = [];
    estimate.value = null;
    choice.value = "cache";
    steerOpen.value = props.askWord;
    const answer = await estimateNow(props.prompt);
    if (!answer) return;
    terms.value = answer.termen?.plus || [];
    minus.value = answer.termen?.min || [];
    words.value = terms.value.map((term) => term.en);
  }
);
// The cost follows the words, a moment after typing stops.
let timer = null;
watch(searchPrompt, (prompt) => {
  if (!terms.value.length || !prompt.trim()) return;
  clearTimeout(timer);
  timer = setTimeout(() => estimateNow(prompt), 400);
});

function go() {
  // A changed word counts under the term it stands for (the server stamps it so).
  const als = {};
  terms.value.forEach((term, i) => {
    const word = (words.value[i] || "").trim();
    if (word && word.toLowerCase() !== term.en.toLowerCase()) als[word] = term.term;
  });
  emit("answer", { prompt: changedCount.value ? searchPrompt.value : props.prompt, als, fresh: Boolean(inCache.value) && choice.value === "vers" });
}
</script>
