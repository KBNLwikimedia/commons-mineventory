<!--
  Describe in bulk (functional design 7.4): before the AI describes several objects, the
  settings it gets are explicit, as in "What is this?" in the magnifier (wish Olaf,
  8-11-2026): an optional hint, the length of the description, the space around the
  cut-out (0% to start with) and, to read, the prompt that goes to the model. Then the
  objects with their small cut-outs and the price; nothing is sent before Continue.
  Every object has its own settings: with "All objects" chosen a change goes to all of
  them, with one object chosen only to that one (wish Olaf).
-->
<template>
  <cdx-dialog
    :open="open"
    class="cc-bevestig cc-bulk-beschrijven"
    :title="t('bulkdescribe.title')"
    :use-close-button="true"
    :close-button-label="t('actions.close')"
    :primary-action="{ label: t('bulkdescribe.go', { n: objects.length }), actionType: 'progressive' }"
    :default-action="{ label: t('actions.cancel') }"
    @primary="answer(true)"
    @default="answer(false)"
    @update:open="(value) => !value && answer(false)"
  >
    <p>{{ action }}</p>
    <!-- A table: each object with the AI parameters it will be asked with. Click "All objects"
         to change them for all, or one object to change only that one (wish Olaf). -->
    <div class="cc-bulk-tabel-houder">
      <!-- Fixed column widths: they do not move when the settings change (wish Olaf). -->
      <table class="cc-bulk-tabel">
        <colgroup>
          <col class="cc-kol-object" />
          <col class="cc-kol-lengte" />
          <col class="cc-kol-ruimte" />
          <col class="cc-kol-aanwijzing" />
          <col class="cc-kol-prompt" />
        </colgroup>
        <thead>
          <tr>
            <th>{{ t("bulkdescribe.col_object") }}</th>
            <th>{{ t("objdetail.label") }}</th>
            <th>{{ t("bulkdescribe.col_space") }}</th>
            <th>{{ t("bulkdescribe.col_hint") }}</th>
            <th>{{ t("bulkdescribe.col_prompt") }}</th>
          </tr>
        </thead>
        <tbody>
          <tr class="cc-bulk-alle" :class="{ 'cc-gekozen': current === ALL }">
            <td colspan="5">
              <button type="button" class="cc-bulk-object" :aria-pressed="current === ALL" @click="current = ALL">
                <strong>{{ t("bulkdescribe.all_objects", { n: objects.length }) }}</strong>
              </button>
              <!-- Back to the starting values for every object (wish Olaf). -->
              <button type="button" class="cc-link cc-bulk-standaard" :disabled="allDefault" :title="t('bulkdescribe.reset_help')" @click="resetDefaults">{{ t("bulkdescribe.reset") }}</button>
            </td>
          </tr>
          <tr v-for="(obj, i) in objects" :key="i" :class="{ 'cc-gekozen': i === current }">
            <td>
              <button type="button" class="cc-bulk-object" :aria-pressed="i === current" :title="t('bulkdescribe.show_object', { name: obj.name })" @click="current = i">
                <img v-if="obj.image" :src="obj.image" alt="" loading="lazy" />
                <span>{{ obj.name }}</span>
              </button>
            </td>
            <td>{{ t(`bulkdescribe.param_${perObject[i]?.level}`) }}</td>
            <td>{{ Math.round((perObject[i]?.margin || 0) * 100) }}%</td>
            <td :title="perObject[i]?.hint.trim()">{{ perObject[i]?.hint.trim() || "–" }}</td>
            <td>{{ obj.ownPrompt ? t("bulkdescribe.param_own_prompt") : t("bulkdescribe.param_app_prompt") }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- The settings, up to and including the prompt, as one fold-out: closed to start with; a
         click on one object in the table opens it (wish Olaf). -->
    <cdx-accordion v-model="settingsOpen" class="cc-bulk-uitklap cc-ai-bijsturing">
    <template #title>{{ t("bulkdescribe.settings") }}</template>
    <p class="cc-uitleg">
      <strong>{{ current === ALL ? t("bulkdescribe.editing_all", { n: objects.length }) : t("bulkdescribe.editing_one", { name: objects[current]?.name || "" }) }}</strong>
      {{ t("bulkdescribe.settings_help") }}
    </p>
    <div class="cc-bulk-instellingen">
    <div class="cc-bulk-velden">
    <!-- 1. An optional hint, as in "What is this?"; it goes along with every object. -->
    <cdx-field class="cc-aanwijzing">
      <template #label>{{ t("describe.hint") }}</template>
      <template #help-text>{{ t("bulkdescribe.hint_help") }}</template>
      <cdx-text-input clearable v-model="hint" :placeholder="t('describe.hint_placeholder')" :maxlength="300" />
    </cdx-field>
    <!-- 2. The length, from a few words via a Commons caption (at most 250 characters) to a paragraph. -->
    <!-- A Commons caption in one click, with the Commons mark, as for the whole image (wish Olaf). -->
    <div class="cc-bulk-lengte">
      <detail-slider v-model="level" :levels="LEVELS" prefix="objdetail">
        <!-- Right behind the slider, without a text of its own (wish Olaf 13-11-2026). -->
        <template #after>
          <span class="cc-caption-schakelaar" :title="t('descdetail.caption_help')">
            <cdx-toggle-switch :model-value="level === 'caption'" :aria-label="t('descdetail.caption_switch')" @update:model-value="(on) => (level = on ? 'caption' : 'normaal')" />
            <commons-logo colour />
          </span>
        </template>
      </detail-slider>
    </div>
    <!-- 3. The space around the cut-out the AI sees: 0% here, only the object itself. -->
    <label class="cc-marge">
      <span>{{ t("describe.margin", { pct: Math.round(margin * 100) }) }}</span>
      <input v-model.number="margin" type="range" min="0" max="1" step="0.05" :aria-label="t('describe.margin_label')" />
      <span class="cc-klein">{{ t("bulkdescribe.margin_help") }}</span>
    </label>
    </div>
    <!-- What the AI sees for the chosen object, as in "What is this?": the red box is the cut-out;
         it follows the space slider. Arrows step through the objects. -->
    <figure v-if="paths[shown]" class="cc-bulk-voorbeeld">
      <cutout-preview :src="inputUrl" :caption="t('bulkdescribe.model_sees', { name: objects[shown]?.name || '' })" />
      <div v-if="objects.length > 1" class="cc-bulk-stappen">
        <cdx-button weight="quiet" size="small" :disabled="current === ALL" :aria-label="t('magnifier.previous')" @click="current -= 1"><cdx-icon :icon="cdxIconPrevious" size="small" /></cdx-button>
        <span class="cc-klein">{{ current === ALL ? t("bulkdescribe.all_short") : `${current + 1} / ${objects.length}` }}</span>
        <cdx-button weight="quiet" size="small" :disabled="current === objects.length - 1" :aria-label="t('magnifier.next')" @click="current += 1"><cdx-icon :icon="cdxIconNext" size="small" /></cdx-button>
      </div>
    </figure>
    </div>
    <!-- 4. The prompt as it goes to the model, for the shown object (to read; the app makes it). -->
    <cdx-accordion v-model="promptOpen" class="cc-bulk-prompt cc-ai-bijsturing-deel">
      <template #title>{{ t("bulkdescribe.prompt") }}</template>
      <template #description>{{ t("bulkdescribe.prompt_for", { name: objects[shown]?.name || "" }) }}</template>
      <p class="cc-uitleg">{{ t("bulkdescribe.prompt_help") }}</p>
      <p v-if="promptError" class="cc-klein cc-te-lang">{{ promptError }}</p>
      <pre v-else class="cc-prompt-tekst">{{ prompt || t("bulkdescribe.prompt_loading") }}</pre>
    </cdx-accordion>
    </cdx-accordion>

    <!-- Afterwards, per object: the magnifier (the eye in the list), wish Olaf. -->
    <h3 class="cc-blok-kop cc-bulk-kop">{{ t("bulkdescribe.unhappy_title") }}</h3>
    <p class="cc-uitleg cc-bulk-ontevreden">
      {{ t("bulkdescribe.unhappy_before") }}
      <cdx-icon :icon="cdxIconEye" size="small" class="cc-bulk-oog" :aria-label="t('objects.open')" />
      {{ t("bulkdescribe.unhappy_after") }}
    </p>

    <p class="cc-bulk-kosten"><strong>{{ costLine }}</strong></p>
  </cdx-dialog>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { CdxAccordion, CdxButton, CdxDialog, CdxField, CdxIcon, CdxTextInput, CdxToggleSwitch } from "@wikimedia/codex";
import CommonsLogo from "./CommonsLogo.vue";
import { cdxIconEye, cdxIconNext, cdxIconPrevious } from "@wikimedia/codex-icons";
import CutoutPreview from "./CutoutPreview.vue";
import { errorText, get } from "../api.js";
import { useT } from "../i18n.js";
import DetailSlider from "./DetailSlider.vue";

const props = defineProps({
  open: { type: Boolean, default: false },
  // What will be described: [{ image, name }], and the API path of each object.
  objects: { type: Array, default: () => [] },
  paths: { type: Array, default: () => [] },
  action: { type: String, default: "" },
  // "This takes n paid call(s), about $…" or "free".
  costLine: { type: String, default: "" },
});
const emit = defineEmits(["answer"]);
const t = useT();

// The same levels as OBJECT_DESCRIPTION_LEVELS in cutter/beschrijving.py and the magnifier.
const LEVELS = ["kort", "normaal", "caption", "uitgebreid"];
// The starting values for every object (0% space, a Commons caption, no hint; wish Olaf).
const START = () => ({ level: "caption", margin: 0, hint: "" });
// The settings of each object, and which one you are changing: ALL (every object) or one index.
const ALL = -1;
const perObject = ref([]);
const current = ref(ALL);
// The object whose preview and prompt are shown: the chosen one, or the first with "All objects".
const shown = computed(() => (current.value === ALL ? 0 : current.value));
// The controls: read from the shown object; a change goes to the chosen object, or to all.
function setting(key) {
  return computed({
    get: () => perObject.value[shown.value]?.[key] ?? START()[key],
    set: (value) => {
      if (current.value === ALL) perObject.value.forEach((s) => (s[key] = value));
      else if (perObject.value[current.value]) perObject.value[current.value][key] = value;
    },
  });
}
const hint = setting("hint");
const level = setting("level");
const margin = setting("margin");
// "Reset defaults": every object back to the starting values, "All objects" chosen again.
const allDefault = computed(() => perObject.value.every((s) => s.level === START().level && s.margin === START().margin && !s.hint.trim()));
function resetDefaults() {
  perObject.value = props.objects.map(() => START());
  current.value = ALL;
}
const promptOpen = ref(false);
// The fold-out "Settings for the AI": closed when the dialog opens, opened by a click on one object.
const settingsOpen = ref(false);
watch(current, (value) => {
  if (value !== ALL) settingsOpen.value = true;
});
const prompt = ref("");
const promptError = ref("");
const inputUrl = computed(() => `${props.paths[shown.value]}/beschrijving/invoer.jpg?marge=${margin.value}`);

// Every time the dialog opens: the starting values for every object, "All objects" chosen.
watch(
  () => props.open,
  (open) => {
    if (!open) return;
    perObject.value = props.objects.map(() => START());
    current.value = ALL;
    settingsOpen.value = false;
    promptOpen.value = false;
    prompt.value = "";
    promptError.value = "";
  }
);

// The prompt follows the settings (free GET), fetched only while it is unfolded.
let timer = null;
let asked = 0;
async function loadPrompt() {
  const path = props.paths[shown.value];
  if (!path || !promptOpen.value) return;
  const ask = ++asked;
  const query = new URLSearchParams({ beschrijvingsniveau: level.value, marge: String(margin.value) });
  if (hint.value.trim()) query.set("aanwijzing", hint.value.trim());
  try {
    const result = await get(`${path}/beschrijving/prompt?${query}`);
    if (ask === asked) {
      prompt.value = result.prompt;
      promptError.value = "";
    }
  } catch (error) {
    if (ask === asked) promptError.value = errorText(t, error);
  }
}
watch([promptOpen, level, margin, hint, shown], () => {
  clearTimeout(timer);
  timer = setTimeout(loadPrompt, 300);
});

// Per object, in the order of the list, the body of its question.
function bodies() {
  return perObject.value.map((s) => {
    const body = { beschrijvingsniveau: s.level, marge: s.margin };
    if (s.hint.trim()) body.aanwijzing = s.hint.trim();
    return body;
  });
}
function answer(go) {
  emit("answer", go ? bodies() : null);
}
</script>
