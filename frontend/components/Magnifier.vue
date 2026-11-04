<!--
  The magnifier (functional design 10.4): the cut-out, "Wat staat hierop?",
  the caption and the Commons concept, in tabs.
-->
<template>
  <cdx-dialog
    :open="open"
    class="cc-vergroter"
    :title="name"
    :subtitle="subtitle"
    :use-close-button="true"
    :close-button-label="t('actions.close')"
    @update:open="emit('update:open', $event)"
  >
    <cdx-tabs v-model:active="tab" :framed="true">
      <cdx-tab name="uitsnede" :label="t('magnifier.cutout')">
        <div v-if="object.masker" class="cc-weergave">
          <cdx-toggle-button-group v-model="view" :buttons="views" :aria-label="t('magnifier.view')" />
          <span class="cc-klein">{{ t(`concept.format_${view}`) }}</span>
        </div>
        <div class="cc-vergroter-beeld">
          <img :src="imageUrl" :alt="name" />
        </div>
        <dl class="cc-gegevens">
          <dt>{{ t("magnifier.source") }}</dt>
          <dd>{{ t(`source.${object.bron}`) }} <ai-badge v-if="object.bron === 'sam'" kind="detectie" :model="object.herkomst?.model || config.sam_model" :score="object.score" /><template v-if="object.wikidata"> · <a :href="`https://www.wikidata.org/wiki/${object.wikidata}`" target="_blank" rel="noopener">{{ object.wikidata }}</a></template></dd>
          <dt>{{ t("magnifier.box") }}</dt>
          <dd>{{ object.box.x }}, {{ object.box.y }} · {{ object.box.w }} × {{ object.box.h }} px</dd>
          <template v-if="object.herkomst?.p2677"><dt>P2677</dt><dd><code>{{ object.herkomst.p2677 }}</code></dd></template>
          <dt>
            {{ t("magnifier.caption") }}
            <info-button v-model:open="captionInfo" :label="t('magnifier.caption_info')" />
          </dt>
          <dd v-if="captionInfo" class="cc-info-tekst">
            <cdx-message type="notice" :inline="true">{{ t("magnifier.caption_help") }}</cdx-message>
          </dd>
          <dd class="cc-bijschrift">
            <span class="cc-invoer-met-knop" :class="{ 'met-tekstknop': removedCaption && !caption }">
              <cdx-text-input
                v-model="caption"
                :aria-label="t('magnifier.caption')"
                :placeholder="removedCaption ? t('magnifier.caption_removed', { text: removedCaption }) : ''"
              />
              <cdx-button
                v-if="removedCaption && !caption"
                class="cc-invoer-knop cc-invoer-knop-tekst"
                weight="quiet"
                size="small"
                action="progressive"
                @click="undoRemoveCaption"
              >
                ↶ {{ t("magnifier.undo") }}
              </cdx-button>
              <cdx-button
                v-else-if="caption || object.bijschrift?.tekst"
                class="cc-invoer-knop"
                weight="quiet"
                size="small"
                action="destructive"
                :aria-label="t('magnifier.caption_remove')"
                :title="t('magnifier.caption_remove')"
                @click="removeCaption"
              >
                <cdx-icon :icon="cdxIconTrash" size="small" />
              </cdx-button>
            </span>
            <cdx-button action="progressive" size="small" :disabled="caption === (object.bijschrift?.tekst || '')" @click="saveCaption">{{ t("actions.save_short") }}</cdx-button>
          </dd>
        </dl>
        <div class="cc-knoppen">
          <span class="cc-knopgroep" role="group" :aria-label="t('magnifier.download')">
            <span class="cc-klein">{{ t("magnifier.download") }}</span>
            <cdx-button action="progressive" @click="download('jpg')"><cdx-icon :icon="cdxIconDownload" /> JPG</cdx-button>
            <cdx-button action="progressive" @click="download('png')"><cdx-icon :icon="cdxIconDownload" /> PNG</cdx-button>
          </span>
          <span class="cc-knopgroep" role="group" :aria-label="t('magnifier.view_full')">
            <span class="cc-klein">{{ t("magnifier.view_full") }}</span>
            <cdx-button action="progressive" weight="quiet" @click="viewFull('jpg')"><cdx-icon :icon="cdxIconLinkExternal" /> JPG</cdx-button>
            <cdx-button action="progressive" weight="quiet" @click="viewFull('png')"><cdx-icon :icon="cdxIconLinkExternal" /> PNG</cdx-button>
          </span>
          <!-- CropTool with this box as its selection (only for single images: the box is in pixels of the original). -->
          <a
            v-if="cropToolUrl"
            class="cdx-button cdx-button--fake-button cdx-button--fake-button--enabled cdx-button--action-progressive cdx-button--weight-quiet"
            :href="cropToolUrl"
            target="_blank"
            rel="noopener"
            :title="t('magnifier.croptool_help')"
          ><cdx-icon :icon="cdxIconLinkExternal" /> {{ t("magnifier.croptool") }}</a>
          <cdx-button action="progressive" v-if="!object.masker" @click="emit('refine', object)">{{ t("magnifier.refine_mask") }}</cdx-button>
          <cdx-button action="destructive" @click="emit('trashed', object.id)"><cdx-icon :icon="cdxIconTrash" /> {{ t("objects.trash") }}</cdx-button>
        </div>
      </cdx-tab>

      <cdx-tab name="beschrijving" :label="t('describe.title')">
        <!--
          One flow for the first and every later question:
          1. the answer (or, before the first one, what you get), with its own actions;
          2. the button that asks the AI, with the cost;
          3. folded away: AI modifiers, earlier descriptions, model and cost.
        -->

        <!-- Step 1 on the left; on the right the cut-out as the AI sees it (red frame, chosen space). -->
        <div class="cc-concept-kop">
        <div class="cc-concept-links">
        <!-- 1a. Before the first answer: what the AI will do, and the caption that goes along. -->
        <section v-if="!description" class="cc-uitleg-vooraf">
          <p>{{ t("describe.intro") }}</p>
          <p>{{ t("describe.intro_modifiers") }}</p>
          <p v-if="object.bijschrift?.tekst" class="cc-klein">
            {{ t("magnifier.caption") }}: <strong>{{ object.bijschrift.tekst }}</strong> — {{ t("describe.caption_goes_along") }}
          </p>
        </section>

        <!-- 1b. The answer. -->
        <section v-else class="cc-antwoord">
          <dl class="cc-gegevens">
            <dt>{{ t("describe.kind") }} <ai-badge kind="soort" :model="description.model" /></dt>
            <dd>{{ fixedValue("kind", description.soort) }} · {{ t("describe.certainty") }}: {{ fixedValue("certainty", description.zekerheid) }}</dd>
            <template v-if="!textDraft">
              <dt>{{ t("describe.subject") }} <ai-badge :model="description.model" :edited="aiEdited('onderwerp')" /></dt>
              <dd>{{ description.onderwerp }}<br /><i>{{ description.onderwerp_en }}</i></dd>
            </template>
            <template v-if="description.bedrijf_of_naam"><dt>{{ t("describe.name") }}</dt><dd>{{ description.bedrijf_of_naam }}</dd></template>
            <template v-if="!textDraft">
              <dt>{{ t("describe.description") }} <ai-badge :model="description.model" :edited="aiEdited('beschrijving')" /></dt>
              <dd>{{ description.beschrijving }}<br /><i>{{ description.beschrijving_en }}</i></dd>
            </template>
            <!-- Legible text read by the AI: editable with the rest, or removed with the bin. -->
            <template v-for="field in READ_TEXTS" :key="field">
              <template v-if="!textDraft && description[field]">
                <dt>{{ t(`describe.field_${field}`) }}</dt>
                <dd class="cc-gelezen-tekst">
                  {{ description[field] }}
                  <cdx-button
                    weight="quiet"
                    size="small"
                    action="destructive"
                    :disabled="busy"
                    :aria-label="t('describe.remove_text')"
                    :title="t('describe.remove_text')"
                    @click="saveTexts({ ...currentTexts(), [field]: '' })"
                  >
                    <cdx-icon :icon="cdxIconTrash" size="small" />
                  </cdx-button>
                </dd>
              </template>
            </template>
          </dl>

          <!-- Editing the texts by hand, in both languages. -->
          <div v-if="textDraft" class="cc-tekst-bewerken">
            <p class="cc-klein">{{ t("describe.edit_help") }}</p>
            <cdx-field v-for="field in EDITABLE" :key="field">
              <template #label>{{ t(`describe.field_${field}`) }}</template>
              <cdx-text-input v-if="field.startsWith('onderwerp') || field.startsWith('tekst_')" v-model="textDraft[field]" />
              <cdx-text-area v-else v-model="textDraft[field]" :autosize="true" />
            </cdx-field>
            <div class="cc-knoppen">
              <cdx-button action="progressive" weight="primary" :disabled="!draftChanged" @click="saveTexts(textDraft)">{{ t("actions.save_short") }}</cdx-button>
              <cdx-button action="progressive" @click="textDraft = null">{{ t("actions.cancel") }}</cdx-button>
            </div>
          </div>
          <!-- What you can do with this answer: edit, undo, go back to the AI text, or remove it. -->
          <div v-else class="cc-knoppen cc-tekst-acties">
            <cdx-button action="progressive" size="small" @click="startEditing"><cdx-icon :icon="cdxIconEdit" size="small" /> {{ t("describe.edit") }}</cdx-button>
            <template v-if="description.bewerkt">
              <cdx-info-chip>{{ t("describe.edited") }}</cdx-info-chip>
              <button type="button" class="cc-link" @click="backToAi">{{ t("describe.back_to_ai") }}</button>
            </template>
            <span v-if="undoTexts" class="cc-klein">
              {{ t("describe.saved_edit") }}
              <button type="button" class="cc-link" @click="undoEdit">↶ {{ t("magnifier.undo") }}</button>
            </span>
            <cdx-button class="cc-rechts-uitlijnen" size="small" weight="quiet" action="destructive" :disabled="busy" @click="removeDescription">
              <cdx-icon :icon="cdxIconTrash" size="small" /> {{ t("describe.remove") }}
            </cdx-button>
          </div>
        </section>
        </div>
        <!-- The image moves to the AI modifiers while they are open, beside the slider (see glidePreview). -->
        <cutout-preview v-if="!previewInModifiers" class="cc-ai-voorbeeld" :src="modelInputUrl" :caption="t('describe.model_sees')" />
        </div>

        <!-- 2. AI modifiers: steer the next question (hint, and the space around the cut-out). -->
        <cdx-accordion v-model="openModifiers" class="cc-beschrijving-blok" @cc-closing="previewInModifiers = false">
          <template #title>{{ t("describe.modifiers") }}</template>
          <template #description>{{ modifiersSummary || t("describe.modifiers_default") }}</template>
          <p class="cc-klein">{{ t("describe.modifiers_help") }}</p>
          <div class="cc-concept-kop cc-ai-sturing">
            <div class="cc-concept-links">
              <!-- An optional hint, e.g. "only the boy"; not the caption, not for Commons. -->
              <cdx-field class="cc-aanwijzing">
                <template #label>{{ t("describe.hint") }}</template>
                <template #help-text>{{ t("describe.hint_help") }}</template>
                <cdx-text-input v-model="hint" :placeholder="t('describe.hint_placeholder')" :maxlength="300" @keydown.enter="describe(Boolean(description))" />
              </cdx-field>
              <label class="cc-marge">
                <span>{{ t("describe.margin", { pct: Math.round(margin * 100) }) }}</span>
                <input v-model.number="margin" type="range" min="0" max="1" step="0.05" :aria-label="t('describe.margin_label')" />
                <span class="cc-klein">{{ t("describe.margin_help") }}</span>
              </label>
            </div>
            <cutout-preview v-if="previewInModifiers" class="cc-ai-voorbeeld" :src="modelInputUrl" :caption="t('describe.model_sees')" />
          </div>
        </cdx-accordion>

        <!-- 3. Ask the AI, under the modifiers that steer it: the first time it is the main action. -->
        <div class="cc-vraag-knop">
          <cdx-button action="progressive" :weight="description ? 'normal' : 'primary'" :disabled="busy" @click="describe(Boolean(description))">
            {{ description ? t("describe.again") : t("describe.ask") }} <span class="cc-kosten">{{ costLabel }}</span>
          </cdx-button>
          <span v-if="modifiersSummary" class="cc-klein">{{ t("describe.with_modifiers", { what: modifiersSummary }) }}</span>
        </div>
        <div v-if="busy" class="cc-bezig" role="status">
          <cdx-progress-bar :inline="true" :aria-label="t('describe.busy', { seconds })" />
          <p class="cc-klein">{{ t("describe.busy", { seconds }) }}</p>
        </div>

        <!-- 3b. Earlier descriptions of this object, to choose from again (free). -->
        <cdx-accordion v-if="history.length" v-model="openHistory" class="cc-beschrijving-blok">
          <template #title>{{ t("describe.history", { n: history.length }) }}</template>
          <template #description>{{ t("describe.history_short") }}</template>
          <ul class="cc-geschiedenis-lijst">
            <li v-for="entry in history" :key="entry.tijdstempel + (entry.bewerkt ? 'b' : '')">
              <div>
                <strong>{{ language === "en" ? entry.onderwerp_en || entry.onderwerp : entry.onderwerp || entry.onderwerp_en }}</strong>
                <span class="cc-klein cc-geschiedenis-beschrijving">{{ language === "en" ? entry.beschrijving_en || entry.beschrijving : entry.beschrijving || entry.beschrijving_en }}</span>
                <span class="cc-klein cc-geschiedenis-meta">{{ historyMeta(entry) }}</span>
              </div>
              <cdx-button action="progressive" size="small" :disabled="busy" @click="restoreDescription(entry)">{{ t("describe.history_use") }}</cdx-button>
            </li>
          </ul>
        </cdx-accordion>

        <!-- Suggestions for depicts: the next step after a description. -->
        <section v-if="description?.wikidata_suggesties?.length" class="cc-blok">
          <h3 class="cc-blok-kop">{{ t("describe.suggestions") }}</h3>
          <p class="cc-klein">{{ t("describe.suggestions_help") }}</p>
          <div class="cc-knoppen">
            <cdx-button action="progressive" v-for="term in description.wikidata_suggesties" :key="term" size="small" @click="searchWikidata(term)">
              <cdx-icon :icon="cdxIconSearch" /> {{ term }}
            </cdx-button>
          </div>
          <ul v-if="hits.length" class="cc-treffers">
            <li v-for="hit in hits" :key="hit.q">
              <cdx-button size="small" weight="quiet" action="progressive" @click="addDepicts(hit)">+ {{ hit.label }}</cdx-button>
              <small><a :href="`https://www.wikidata.org/wiki/${hit.q}`" target="_blank" rel="noopener">{{ hit.q }}</a> · {{ hit.beschrijving }}</small>
            </li>
          </ul>
        </section>

        <!-- 3c. Secondary: which model, why, what this answer cost, and how far to trust it. -->
        <cdx-accordion v-if="plan || description" class="cc-beschrijving-blok">
          <template #title>{{ t("describe.model_block") }}</template>
          <template #description>{{ (description || plan).model }}</template>
          <p class="cc-klein">
            <template v-for="(part, i) in textParts(modelReason, reasonLinks)" :key="i">
              <a v-if="part.link" :href="part.link.href" target="_blank" rel="noopener">{{ part.link.label }}</a>
              <template v-else>{{ part.text }}</template>
            </template>
            <template v-if="description?.aanwijzing"><br />{{ t("describe.hint_used", { hint: description.aanwijzing }) }}</template>
            <template v-if="description && description.kosten_usd != null">
              <br />{{ t("describe.paid", { amount: money(description.kosten_usd, language) }) }}
              <template v-if="description.tokens?.invoer != null"> · {{ t("describe.tokens", { input: description.tokens.invoer, output: description.tokens.uitvoer }) }}</template>
            </template>
          </p>
          <p class="cc-klein cc-waarschuwing">{{ t("describe.caution") }}</p>
        </cdx-accordion>
      </cdx-tab>

      <cdx-tab name="commons" :label="t('concept.tab')">
        <concept-editor ref="editor" :mid="file.mid" :n="n" :object-id="object.id" />
      </cdx-tab>
    </cdx-tabs>
    <cdx-message v-if="error" type="error" :inline="true">{{ error }}</cdx-message>
  </cdx-dialog>
</template>

<script setup>
import { computed, inject, nextTick, onBeforeUnmount, ref, watch } from "vue";
import { CdxAccordion, CdxButton, CdxDialog, CdxField, CdxIcon, CdxInfoChip, CdxMessage, CdxProgressBar, CdxTab, CdxTabs, CdxTextArea, CdxTextInput, CdxToggleButtonGroup } from "@wikimedia/codex";
import { cdxIconDownload, cdxIconEdit, cdxIconLinkExternal, cdxIconSearch, cdxIconTrash } from "@wikimedia/codex-icons";
import { API, del, errorText, get, objectPath, patch, post, query } from "../api.js";
import { askConfirm, textParts } from "../confirm.js";
import { money, useT } from "../i18n.js";
import { forgetPlacement, makeMovable } from "../movable.js";
import { cropToolLink, objectName } from "../state.js";
import AiBadge from "./AiBadge.vue";
import ConceptEditor from "./ConceptEditor.vue";
import CutoutPreview from "./CutoutPreview.vue";
import InfoButton from "./InfoButton.vue";

const props = defineProps({
  open: { type: Boolean, default: false },
  file: { type: Object, required: true },
  n: { type: Number, required: true },
  object: { type: Object, required: true },
});
const emit = defineEmits(["update:open", "changed", "trashed", "refine"]);
const t = useT();
const language = inject("language", "nl");
const config = inject("config");
const tab = ref("uitsnede");
const caption = ref(props.object.bijschrift?.tekst || "");
const cropToolUrl = computed(() => cropToolLink(props.file, props.object));
const captionInfo = ref(false);
const plan = ref(null);
const busy = ref(false);
const seconds = ref(0);
let ticker = null;
const error = ref("");
// The hint for the next "Ask again" (sent once, then cleared).
const hint = ref("");
// Folded away until wanted: the AI modifiers and the earlier descriptions.
const openModifiers = ref(false);
const openHistory = ref(false);

// Where the preview sits: beside the slider while the AI modifiers are open.
// It moves as soon as they start to open or close (the fold itself is
// animated by accordion-motion.js), and glides there: a copy flies from the
// old place to the new one, above everything, so the folding content does not
// clip it (FLIP: measure before and after, animate the difference).
const previewInModifiers = ref(false);
watch(openModifiers, (open) => {
  previewInModifiers.value = open;
});
function visiblePreview() {
  return [...document.querySelectorAll(".cc-vergroter .cc-ai-voorbeeld")].find((el) => el.offsetParent);
}
let previewBefore = null;
watch(previewInModifiers, () => (previewBefore = visiblePreview()?.getBoundingClientRect() || null), { flush: "pre" });
watch(previewInModifiers, async () => {
  await nextTick();
  const el = visiblePreview();
  if (!el || !previewBefore || window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
  // Measured after the accordion has started to open, so the target is known.
  await new Promise((resolve) => requestAnimationFrame(resolve));
  const after = el.getBoundingClientRect();
  const flyer = el.cloneNode(true);
  Object.assign(flyer.style, {
    position: "fixed", left: `${previewBefore.left}px`, top: `${previewBefore.top}px`, width: `${after.width}px`,
    margin: "0", zIndex: "1000", pointerEvents: "none",
  });
  document.body.appendChild(flyer);
  el.style.visibility = "hidden";
  const move = flyer.animate(
    [{ transform: "translate(0, 0)" }, { transform: `translate(${after.left - previewBefore.left}px, ${after.top - previewBefore.top}px)` }],
    { duration: 600, easing: "cubic-bezier(0.65, 0, 0.35, 1)" } // speeds up, then slows down
  );
  move.onfinish = move.oncancel = () => {
    el.style.visibility = "";
    flyer.remove();
  };
});
// How much of the surroundings the AI sees, as a share of the box on every
// side (0-1): what the last description used, else 25 %.
const DEFAULT_MARGIN = 0.25;
const margin = ref(props.object.beschrijving?.marge ?? DEFAULT_MARGIN);
// What the next question will use besides the defaults, in a few words
// (shown beside the button and on the folded AI modifiers).
const modifiersSummary = computed(() => {
  const parts = [];
  if (Math.round(margin.value * 100) !== Math.round(DEFAULT_MARGIN * 100)) parts.push(t("describe.history_margin", { pct: Math.round(margin.value * 100) }));
  if (hint.value.trim()) parts.push(t("describe.history_hint", { hint: hint.value.trim() }));
  return parts.join(" · ");
});
// The preview follows the slider a moment after it stops moving.
const shownMargin = ref(margin.value);
let marginTimer = null;
watch(margin, (value) => {
  clearTimeout(marginTimer);
  marginTimer = setTimeout(() => (shownMargin.value = value), 250);
});
const hits = ref([]);
const editor = ref(null);

// Move by the title bar, resize at the edges; double-click the title bar to
// centre it again. Codex renders the dialog elsewhere in the page (teleport).
const PLACEMENT_KEY = "cc-vergroter-plaats";
let undoMovable = null;

function enableMoving() {
  undoMovable?.();
  undoMovable = null;
  const dialog = document.querySelector(".cc-vergroter");
  const header = dialog?.querySelector(".cdx-dialog__header");
  if (!dialog || !header) return;
  undoMovable = makeMovable(dialog, {
    handle: header,
    storageKey: PLACEMENT_KEY,
    labels: { move: t("magnifier.move"), resize: t("magnifier.resize") },
    min: { width: 360, height: 240 },
  });
  header.ondblclick = (event) => {
    if (event.target.closest("button")) return;
    forgetPlacement(PLACEMENT_KEY);
    dialog.removeAttribute("style");
  };
}

watch(
  () => props.open,
  async (open) => {
    if (!open) {
      undoMovable?.();
      undoMovable = null;
      return;
    }
    await nextTick();
    enableMoving();
  },
  { immediate: true }
);
onBeforeUnmount(() => undoMovable?.());

const base = computed(() => objectPath(props.file.mid, props.n, props.object.id));
const name = computed(() => objectName(props.object, language, t));
const subtitle = computed(() => `${t(`source.${props.object.bron}`)} · ${t(`status.${props.object.status}`)}`);
const description = computed(() => props.object.beschrijving || null);
// Whether the user changed this AI text (NL or EN) by hand.
function aiEdited(field) {
  const original = description.value?.ai_origineel || {};
  return field in original || `${field}_en` in original;
}

// Kind and certainty come from a fixed Dutch list (the model's answer schema);
// shown in the interface language, or as given when not in the list.
function fixedValue(group, value) {
  const text = t(`${group}.${value}`);
  return text === `${group}.${value}` ? value : text;
}
// Why this model, in plain words. Descriptions stored before the reason had a
// code fall back to the current choice for the file (the same rules).
const modelReason = computed(() => {
  const d = description.value;
  const code = d ? d.model_reden_code || plan.value?.reden_code : plan.value?.reden_code;
  if (!code) return d?.model_reden || plan.value?.reden || "";
  const labels = (d?.model_reden_labels || plan.value?.labels || []).map((label) => t(`rights.${label}`)).join(", ");
  return t(`describe.reason_${code}`, { labels });
});
// "Contributor" links to Meta's explanation of that mode (cheaper; Meta may train on the input).
const reasonLinks = {
  contributor: { href: "https://dev.meta.ai/docs/pricing-rate-limits#contributor-mode", label: t("describe.contributor_link") },
};
// The cost on the buttons: an estimate in live mode, free with the dummy.
const costLabel = computed(() => (plan.value?.betaald ? `± ${money(plan.value.kosten_schatting_usd, language)}` : t("describe.free_short")));
// What the image description would see with the chosen margin (free; nothing goes to the model).
const modelInputUrl = computed(() => `${base.value}/beschrijving/invoer.jpg?marge=${shownMargin.value}`);
// View on the Cut-out tab: the shape (PNG, transparent) or the rectangle (JPG).
// Only a view; what goes to Commons is the format in the Commons concept.
const views = [
  { value: "png", label: "PNG" },
  { value: "jpg", label: "JPG" },
];
const view = ref(props.object.masker ? "png" : "jpg");
const imageUrl = computed(() => (props.object.masker && view.value === "png" ? `${base.value}/uitsnede.png` : `${base.value}/uitsnede.jpg?w=1200`));

watch(
  () => props.object.id,
  () => {
    caption.value = props.object.bijschrift?.tekst || "";
    view.value = props.object.masker ? "png" : "jpg";
    removedCaption.value = "";
    hint.value = "";
    margin.value = props.object.beschrijving?.marge ?? DEFAULT_MARGIN;
    shownMargin.value = margin.value;
    loadHistory();
    textDraft.value = null;
    undoTexts.value = null;
    hits.value = [];
    loadPlan();
  }
);

async function loadPlan() {
  try {
    plan.value = await get(`${base.value}/beschrijving`);
  } catch (e) {
    error.value = errorText(t, e);
  }
}
loadPlan();

async function describe(again) {
  // Asking again always costs money; a first question may still come from the
  // cache (free), but the estimate is asked to confirm all the same.
  const paid = again || !description.value;
  if (paid && config.betaald && plan.value?.betaald && !(await askConfirm(t("describe.confirm", { amount: money(plan.value.kosten_schatting_usd, language) }), { title: t("confirm.cost_title") }))) return;
  busy.value = true;
  seconds.value = 0;
  ticker = setInterval(() => seconds.value++, 1000);
  error.value = "";
  try {
    const body = { opnieuw: again, marge: margin.value };
    if (hint.value.trim()) body.aanwijzing = hint.value.trim();
    const result = await post(`${base.value}/beschrijving`, body);
    emit("changed", result.object);
    hint.value = "";
    textDraft.value = null;
    undoTexts.value = null;
    editor.value?.reload();
    loadHistory();
  } catch (e) {
    error.value = errorText(t, e);
  } finally {
    busy.value = false;
    clearInterval(ticker);
  }
}

// Earlier descriptions (kept history plus answers still in the cache), newest first.
const history = ref([]);

async function loadHistory() {
  try {
    history.value = (await get(`${base.value}/beschrijving/geschiedenis`)).geschiedenis;
  } catch {
    history.value = [];
  }
}
loadHistory();

function historyMeta(entry) {
  const when = entry.tijdstempel ? new Date(entry.tijdstempel).toLocaleString(language, { dateStyle: "short", timeStyle: "short" }) : "";
  const parts = [when, entry.model];
  if (entry.aanwijzing) parts.push(t("describe.history_hint", { hint: entry.aanwijzing }));
  parts.push(t("describe.history_margin", { pct: Math.round((entry.marge ?? DEFAULT_MARGIN) * 100) }));
  if (entry.bewerkt) parts.push(t("describe.edited"));
  return parts.filter(Boolean).join(" · ");
}

// Make an earlier description current again; the current one goes into the history.
async function restoreDescription(entry) {
  error.value = "";
  try {
    const changed = await post(`${base.value}/beschrijving/terugzetten`, { tijdstempel: entry.tijdstempel, bewerkt: Boolean(entry.bewerkt) });
    emit("changed", changed);
    textDraft.value = null;
    undoTexts.value = null;
    margin.value = changed.beschrijving?.marge ?? DEFAULT_MARGIN;
    editor.value?.reload();
    loadHistory();
  } catch (e) {
    error.value = errorText(t, e);
  }
}

// Forget the description; the answer stays in the cache, so asking again is free.
async function removeDescription() {
  if (!(await askConfirm(t("describe.remove_confirm"), { go: t("describe.remove"), destructive: true }))) return;
  try {
    emit("changed", await del(`${base.value}/beschrijving`));
    textDraft.value = null;
    undoTexts.value = null;
    editor.value?.reload();
    loadPlan();
    loadHistory();
  } catch (e) {
    error.value = errorText(t, e);
  }
}

// Editing the AI texts by hand (subject and description, NL and EN). The
// server keeps the original AI text, for "Terug naar de AI-tekst"; "Ongedaan
// maken" puts back what was there before the last change.
const READ_TEXTS = ["tekst_in_beeld", "tekst_rond_beeld"];
const EDITABLE = ["onderwerp", "onderwerp_en", "beschrijving", "beschrijving_en", ...READ_TEXTS];
const textDraft = ref(null);
const undoTexts = ref(null);

function currentTexts() {
  return Object.fromEntries(EDITABLE.map((field) => [field, description.value?.[field] || ""]));
}

const draftChanged = computed(() => {
  const now = currentTexts();
  return !!textDraft.value && EDITABLE.some((field) => textDraft.value[field].trim() !== now[field]);
});

function startEditing() {
  textDraft.value = currentTexts();
}

async function saveTexts(texts, { undoable = true } = {}) {
  const before = currentTexts();
  try {
    emit("changed", await patch(`${base.value}/beschrijving`, texts));
    textDraft.value = null;
    undoTexts.value = undoable ? before : null;
    editor.value?.reload();
  } catch (e) {
    error.value = errorText(t, e);
  }
}

function backToAi() {
  saveTexts({ ...currentTexts(), ...description.value.ai_origineel });
}

function undoEdit() {
  saveTexts(undoTexts.value, { undoable: false });
}

// Empty the caption and remove it from the object at once (no Opslaan needed);
// what was there can be put back with "Ongedaan maken".
const removedCaption = ref("");

async function removeCaption() {
  const previous = (props.object.bijschrift?.tekst || caption.value).trim();
  caption.value = "";
  await saveCaption();
  removedCaption.value = previous;
}

async function undoRemoveCaption() {
  caption.value = removedCaption.value;
  removedCaption.value = "";
  await saveCaption();
}

async function saveCaption() {
  try {
    const text = caption.value.trim();
    const result = await patch(base.value, { bijschrift: text ? { tekst: text } : null });
    emit("changed", result);
  } catch (e) {
    error.value = errorText(t, e);
  }
}

async function searchWikidata(term) {
  try {
    hits.value = (await get(`${API}/wikidata/zoek${query({ q: term, taal: language })}`)).resultaten;
  } catch (e) {
    error.value = errorText(t, e);
  }
}

async function addDepicts(hit) {
  await editor.value?.addDepicts({ q: hit.q, label: hit.label });
  tab.value = "commons";
}

// Download saves the file (named after the Commons concept); view opens it in a new tab.
function download(kind) {
  window.location.href = `${base.value}/uitsnede.${kind}?download=1`;
}

function viewFull(kind) {
  window.open(`${base.value}/uitsnede.${kind}`, "_blank", "noopener");
}
</script>
