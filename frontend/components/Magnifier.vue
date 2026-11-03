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
        <div class="cc-vergroter-beeld">
          <img :src="imageUrl" :alt="name" />
        </div>
        <dl class="cc-gegevens">
          <dt>{{ t("magnifier.source") }}</dt>
          <dd>{{ t(`source.${object.bron}`) }}<template v-if="object.wikidata"> · <a :href="`https://www.wikidata.org/wiki/${object.wikidata}`" target="_blank" rel="noopener">{{ object.wikidata }}</a></template></dd>
          <dt>{{ t("magnifier.box") }}</dt>
          <dd>{{ object.box.x }}, {{ object.box.y }} · {{ object.box.w }} × {{ object.box.h }} px</dd>
          <template v-if="object.herkomst?.p2677"><dt>P2677</dt><dd><code>{{ object.herkomst.p2677 }}</code></dd></template>
          <dt>{{ t("magnifier.caption") }}</dt>
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
        <template v-if="description">
          <dl class="cc-gegevens">
            <dt>{{ t("describe.kind") }}</dt><dd>{{ description.soort }} · {{ t("describe.certainty") }}: {{ description.zekerheid }}</dd>
            <dt>{{ t("describe.subject") }}</dt><dd>{{ description.onderwerp }}<br /><i>{{ description.onderwerp_en }}</i></dd>
            <template v-if="description.bedrijf_of_naam"><dt>{{ t("describe.name") }}</dt><dd>{{ description.bedrijf_of_naam }}</dd></template>
            <dt>{{ t("describe.description") }}</dt><dd>{{ description.beschrijving }}<br /><i>{{ description.beschrijving_en }}</i></dd>
            <template v-if="description.tekst_in_beeld"><dt>{{ t("describe.text_in") }}</dt><dd>{{ description.tekst_in_beeld }}</dd></template>
            <template v-if="description.tekst_rond_beeld"><dt>{{ t("describe.text_around") }}</dt><dd>{{ description.tekst_rond_beeld }}</dd></template>
            <dt>{{ t("describe.model") }}</dt><dd class="cc-klein">{{ description.model }} — {{ description.model_reden }}</dd>
          </dl>
          <section v-if="description.wikidata_suggesties?.length" class="cc-suggesties">
            <h4>{{ t("describe.suggestions") }}</h4>
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
        </template>
        <p v-else class="cc-klein">{{ t("describe.none_yet") }}</p>
        <cdx-message v-if="plan" type="notice" :inline="true">
          {{ plan.betaald ? t("describe.cost", { amount: money(plan.kosten_schatting_usd, language), model: plan.model }) : t("describe.free") }}
          <span class="cc-klein">{{ plan.reden }}</span>
        </cdx-message>
        <div class="cc-knoppen">
          <cdx-button action="progressive" :disabled="busy" @click="describe(false)">{{ description ? t("describe.again_cache") : t("describe.ask") }}</cdx-button>
          <cdx-button v-if="description" :disabled="busy" @click="describe(true)">{{ t("describe.again") }}</cdx-button>
        </div>
        <div v-if="busy" class="cc-bezig" role="status">
          <cdx-progress-bar :inline="true" :aria-label="t('describe.busy', { seconds })" />
          <p class="cc-klein">{{ t("describe.busy", { seconds }) }}</p>
        </div>
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
import { CdxButton, CdxDialog, CdxIcon, CdxMessage, CdxProgressBar, CdxTab, CdxTabs, CdxTextInput } from "@wikimedia/codex";
import { cdxIconDownload, cdxIconSearch, cdxIconTrash } from "@wikimedia/codex-icons";
import { API, errorText, get, objectPath, patch, post, query } from "../api.js";
import { askConfirm } from "../confirm.js";
import { money, useT } from "../i18n.js";
import { forgetPlacement, makeMovable } from "../movable.js";
import { objectName } from "../state.js";
import ConceptEditor from "./ConceptEditor.vue";

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
const imageUrl = computed(() => (props.object.masker ? `${base.value}/uitsnede.png` : `${base.value}/uitsnede.jpg?w=1200`));

watch(
  () => props.object.id,
  () => {
    caption.value = props.object.bijschrift?.tekst || "";
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
  if (paid && config.betaald && plan.value?.betaald && !(await askConfirm(t("describe.confirm", { amount: money(plan.value.kosten_schatting_usd, language) })))) return;
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
