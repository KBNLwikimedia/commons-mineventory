<!--
  The detection panel (functional design 7 and 10.4): regions from Commons,
  search, Snel zoeken, suggestions for this page, point mode and bulk
  operations. Costs are shown per button; in dummy mode everything is free.
-->
<template>
  <div class="cc-paneel">
    <p class="cc-modus" :class="{ betaald: config.betaald }">
      {{ config.betaald ? t("panel.mode_live", { model: config.sam_model }) : t("panel.mode_dummy") }}
    </p>

    <cdx-accordion v-model="open.commons">
      <template #title>{{ t("panel.from_commons") }}</template>
      <p class="cc-klein">{{ t("panel.from_commons_help") }}</p>
      <cdx-button :disabled="busy || page.n !== 1 || !regionCount" @click="emit('detect', { modus: 'commons' })">
        {{ t("panel.regions_button", { n: regionCount }) }}
      </cdx-button>
      <p v-if="page.n !== 1" class="cc-klein">{{ t("panel.regions_page_one") }}</p>
    </cdx-accordion>

    <cdx-accordion v-model="open.search">
      <template #title>{{ t("panel.search") }}</template>
      <form class="cc-zoek" @submit.prevent="search">
        <cdx-text-input v-model="prompt" :placeholder="t('panel.search_placeholder')" :aria-label="t('panel.search')" />
        <cdx-button type="submit" action="progressive" :disabled="busy || !prompt.trim()">{{ t("panel.search_button") }}</cdx-button>
      </form>
      <p class="cc-klein">{{ t("panel.search_help") }} {{ cost(1) }}</p>
    </cdx-accordion>

    <cdx-accordion v-model="open.quick">
      <template #title>{{ t("panel.quick") }}</template>
      <div class="cc-knoppen">
        <cdx-button
          v-for="group in config.snel_zoeken"
          :key="group.sleutel"
          size="small"
          :disabled="busy"
          :title="group.termen.join(', ')"
          @click="emit('detect', { modus: 'categorie', categorie: group.sleutel })"
        >
          {{ t(group.label) }}
        </cdx-button>
      </div>
    </cdx-accordion>

    <cdx-accordion v-model="open.suggestions">
      <template #title>{{ t("panel.suggestions") }}</template>
      <template v-if="inventory">
        <p class="cc-klein">{{ inventory.paginasoort }} — {{ inventory.samenvatting }}</p>
        <div class="cc-knoppen">
          <cdx-button
            v-for="term in inventory.zoektermen"
            :key="term.en"
            size="small"
            :disabled="busy"
            :title="`${term.aantal}× · ${term.waar}`"
            @click="emit('detect', { modus: 'prompt', prompt: term.en })"
          >
            {{ config.taal === "nl" ? term.nl : term.en }}
          </cdx-button>
        </div>
      </template>
      <cdx-button size="small" :disabled="busy" @click="emit('inventory')">
        {{ inventory ? t("panel.inventory_again") : t("panel.inventory") }}
      </cdx-button>
      <p class="cc-klein">{{ t("panel.inventory_help") }} {{ museCost(config.muse.pagina_usd) }}</p>
    </cdx-accordion>

    <cdx-accordion v-model="open.point">
      <template #title>{{ t("panel.point") }}</template>
      <cdx-toggle-switch :model-value="pointMode" @update:model-value="emit('point-mode', $event)">
        {{ t("panel.point_switch") }}
      </cdx-toggle-switch>
      <p class="cc-klein">{{ t("panel.point_help") }} {{ cost(1) }}</p>
    </cdx-accordion>

    <cdx-accordion v-model="open.bulk">
      <template #title>{{ t("panel.bulk") }}</template>
      <div class="cc-knoppen cc-knoppen-rij">
        <cdx-button :disabled="busy" :title="config.alles.map((a) => a.en).join(', ')" @click="emit('detect', { modus: 'alles' })">
          {{ t("panel.all") }} <small>{{ cost(config.alles.length) }}</small>
        </cdx-button>
        <cdx-button :disabled="busy" @click="emit('smart')">{{ t("panel.smart") }}</cdx-button>
        <cdx-button :disabled="busy" @click="emit('describe-all')">{{ t("panel.describe_all") }}</cdx-button>
        <cdx-button :disabled="busy" @click="emit('merge')">{{ t("panel.merge") }}</cdx-button>
      </div>
    </cdx-accordion>
    <cdx-progress-bar v-if="busy" :inline="true" :aria-label="t('panel.busy')" />
  </div>
</template>

<script setup>
import { computed, inject, reactive, ref } from "vue";
import { CdxAccordion, CdxButton, CdxProgressBar, CdxTextInput, CdxToggleSwitch } from "@wikimedia/codex";
import { money, useT } from "../i18n.js";

const props = defineProps({
  file: { type: Object, required: true },
  page: { type: Object, required: true },
  busy: { type: Boolean, default: false },
  inventory: { type: Object, default: null },
  pointMode: { type: Boolean, default: false },
});
const emit = defineEmits(["detect", "smart", "inventory", "merge", "describe-all", "point-mode"]);
const t = useT();
const config = inject("config");
const prompt = ref("");
const open = reactive({ commons: true, search: true, quick: true, suggestions: false, point: false, bulk: false });
const regionCount = computed(() => props.page.regio_aantal + props.page.notitie_aantal);

const SAM_PER_CALL = 0.0025;
const cost = (calls) => (config.betaald ? `(${money(calls * SAM_PER_CALL, config.taal)})` : t("panel.free"));
const museCost = (usd) => (config.betaald ? `(${money(usd, config.taal)})` : t("panel.free"));

function search() {
  if (prompt.value.trim()) emit("detect", { modus: "prompt", prompt: prompt.value.trim() });
}
</script>
