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
          <dd>{{ t(`source.${object.bron}`) }}<template v-if="object.wikidata"> · <a :href="`https://www.wikidata.org/wiki/${object.wikidata}`" target="_blank" rel="noopener">{{ object.wikidata }}</a></template></dd>
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
            <cdx-text-input v-model="caption" :aria-label="t('magnifier.caption')" />
            <cdx-button size="small" :disabled="caption === (object.bijschrift?.tekst || '')" @click="saveCaption">{{ t("actions.save_short") }}</cdx-button>
          </dd>
        </dl>
        <div class="cc-knoppen">
          <cdx-button @click="download('jpg')"><cdx-icon :icon="cdxIconDownload" /> JPG</cdx-button>
          <cdx-button @click="download('png')"><cdx-icon :icon="cdxIconDownload" /> PNG</cdx-button>
          <cdx-button v-if="!object.masker" @click="emit('refine', object)">{{ t("magnifier.refine_mask") }}</cdx-button>
          <cdx-button action="destructive" @click="emit('trashed', object.id)"><cdx-icon :icon="cdxIconTrash" /> {{ t("objects.trash") }}</cdx-button>
        </div>
      </cdx-tab>

      <cdx-tab name="beschrijving" :label="t('describe.title')">
        <!-- The answer, with the cut-out beside it. -->
        <div class="cc-concept-kop">
          <div class="cc-concept-links">
            <template v-if="description">
              <dl class="cc-gegevens">
                <dt>{{ t("describe.kind") }}</dt><dd>{{ description.soort }} · {{ t("describe.certainty") }}: {{ description.zekerheid }}</dd>
                <dt>{{ t("describe.subject") }}</dt><dd>{{ description.onderwerp }}<br /><i>{{ description.onderwerp_en }}</i></dd>
                <template v-if="description.bedrijf_of_naam"><dt>{{ t("describe.name") }}</dt><dd>{{ description.bedrijf_of_naam }}</dd></template>
                <dt>{{ t("describe.description") }}</dt><dd>{{ description.beschrijving }}<br /><i>{{ description.beschrijving_en }}</i></dd>
                <template v-if="description.tekst_in_beeld"><dt>{{ t("describe.text_in") }}</dt><dd>{{ description.tekst_in_beeld }}</dd></template>
                <template v-if="description.tekst_rond_beeld"><dt>{{ t("describe.text_around") }}</dt><dd>{{ description.tekst_rond_beeld }}</dd></template>
              </dl>
              <p class="cc-klein cc-waarschuwing">{{ t("describe.caution") }}</p>
            </template>
            <p v-else class="cc-klein">{{ t("describe.none_yet") }}</p>

            <!-- The actions, each with what it costs. -->
            <div class="cc-knoppen">
              <cdx-button v-if="!description" action="progressive" weight="primary" :disabled="busy" @click="describe(false)">
                {{ t("describe.ask") }} <span class="cc-kosten">{{ costLabel }}</span>
              </cdx-button>
              <template v-else>
                <cdx-button :disabled="busy" @click="describe(false)">
                  {{ t("describe.again_cache") }} <span class="cc-kosten">{{ t("describe.free_short") }}</span>
                </cdx-button>
                <cdx-button :disabled="busy" @click="describe(true)">
                  {{ t("describe.again") }} <span class="cc-kosten">{{ costLabel }}</span>
                </cdx-button>
                <cdx-button :disabled="busy" action="destructive" weight="quiet" @click="removeDescription">
                  <cdx-icon :icon="cdxIconTrash" /> {{ t("describe.remove") }}
                </cdx-button>
              </template>
            </div>
            <div v-if="busy" class="cc-bezig" role="status">
              <cdx-progress-bar :inline="true" :aria-label="t('describe.busy', { seconds })" />
              <p class="cc-klein">{{ t("describe.busy", { seconds }) }}</p>
            </div>
          </div>
          <cutout-preview :src="previewUrl" :caption="t('magnifier.preview')" />
        </div>

        <!-- Suggestions for depicts: a block of its own. -->
        <section v-if="description?.wikidata_suggesties?.length" class="cc-blok">
          <h3 class="cc-blok-kop">{{ t("describe.suggestions") }}</h3>
          <p class="cc-klein">{{ t("describe.suggestions_help") }}</p>
          <div class="cc-knoppen">
            <cdx-button v-for="term in description.wikidata_suggesties" :key="term" size="small" @click="searchWikidata(term)">
              <cdx-icon :icon="cdxIconSearch" /> {{ term }}
            </cdx-button>
          </div>
          <ul v-if="hits.length" class="cc-treffers">
            <li v-for="hit in hits" :key="hit.q">
              <cdx-button size="small" weight="quiet" action="progressive" @click="addDepicts(hit)">+ {{ hit.label }}</cdx-button>
              <small>{{ hit.q }} · {{ hit.beschrijving }}</small>
            </li>
          </ul>
        </section>

        <!-- Secondary: which model, why, and what this answer cost. -->
        <section v-if="plan || description" class="cc-blok cc-blok-zacht">
          <h3 class="cc-blok-kop">{{ t("describe.model_block") }}</h3>
          <p class="cc-klein">
            {{ (description || plan).model }} — {{ description ? description.model_reden : plan.reden }}
            <template v-if="description && description.kosten_usd != null">
              <br />{{ t("describe.paid", { amount: money(description.kosten_usd, language) }) }}
              <template v-if="description.tokens?.invoer != null"> · {{ t("describe.tokens", { input: description.tokens.invoer, output: description.tokens.uitvoer }) }}</template>
            </template>
          </p>
        </section>
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
import { CdxButton, CdxDialog, CdxIcon, CdxMessage, CdxProgressBar, CdxTab, CdxTabs, CdxTextInput, CdxToggleButtonGroup } from "@wikimedia/codex";
import { cdxIconDownload, cdxIconSearch, cdxIconTrash } from "@wikimedia/codex-icons";
import { API, del, errorText, get, objectPath, patch, post, query } from "../api.js";
import { askConfirm } from "../confirm.js";
import { money, useT } from "../i18n.js";
import { forgetPlacement, makeMovable } from "../movable.js";
import { objectName } from "../state.js";
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
const captionInfo = ref(false);
const plan = ref(null);
const busy = ref(false);
const seconds = ref(0);
let ticker = null;
const error = ref("");
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
const name = computed(() => objectName(props.object, language));
const subtitle = computed(() => `${t(`source.${props.object.bron}`)} · ${t(`status.${props.object.status}`)}`);
const description = computed(() => props.object.beschrijving || null);
// The cost on the buttons: an estimate in live mode, free with the dummy.
const costLabel = computed(() => (plan.value?.betaald ? `± ${money(plan.value.kosten_schatting_usd, language)}` : t("describe.free_short")));
// The small preview on the "Wat staat hierop?" tab: the rectangle, like the model sees it.
const previewUrl = computed(() => `${base.value}/uitsnede.jpg?w=480`);
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
  // "Opnieuw tonen" comes from the cache and is free; only a new question costs money.
  const paid = again || !description.value;
  if (paid && config.betaald && plan.value?.betaald && !(await askConfirm(t("describe.confirm", { amount: money(plan.value.kosten_schatting_usd, language) }), { title: t("confirm.cost_title") }))) return;
  busy.value = true;
  seconds.value = 0;
  ticker = setInterval(() => seconds.value++, 1000);
  error.value = "";
  try {
    const result = await post(`${base.value}/beschrijving`, { opnieuw: again });
    emit("changed", result.object);
    editor.value?.reload();
  } catch (e) {
    error.value = errorText(t, e);
  } finally {
    busy.value = false;
    clearInterval(ticker);
  }
}

// Forget the description; the answer stays in the cache, so asking again is free.
async function removeDescription() {
  if (!(await askConfirm(t("describe.remove_confirm"), { go: t("describe.remove"), destructive: true }))) return;
  try {
    emit("changed", await del(`${base.value}/beschrijving`));
    editor.value?.reload();
    loadPlan();
  } catch (e) {
    error.value = errorText(t, e);
  }
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

function download(kind) {
  window.open(`${base.value}/uitsnede.${kind}`, "_blank");
}
</script>
