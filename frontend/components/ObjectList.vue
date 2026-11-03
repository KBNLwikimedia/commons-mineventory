<!-- The objects of the page with checkboxes (functional design 10.4). -->
<template>
  <section class="cc-objecten">
    <header class="cc-objecten-kop">
      <h3>{{ t("objects.title") }} <small>({{ objects.length }})</small></h3>
      <span v-if="objects.length" class="cc-objecten-alles">
        <button type="button" class="cc-link" @click="emit('select', objects.filter((o) => o.status !== 'uitgesloten').map((o) => o.id))">
          {{ t("objects.all") }}
        </button>
        ·
        <button type="button" class="cc-link" @click="emit('select', [])">{{ t("objects.none") }}</button>
      </span>
    </header>
    <p v-if="!objects.length" class="cc-leeg">{{ t("objects.empty") }}</p>
    <ul>
      <li
        v-for="obj in sorted"
        :key="obj.id"
        :class="[`cc-object-${obj.status}`, `cc-bron-${obj.bron}`, { focus: obj.id === focused }]"
        @mouseenter="emit('hover', obj.id, true)"
        @mouseleave="emit('hover', obj.id, false)"
      >
        <cdx-checkbox
          :model-value="obj.status === 'geselecteerd'"
          :disabled="obj.status === 'uitgesloten'"
          @update:model-value="emit('toggle', obj.id)"
        >
          <span class="cc-object-naam" @click.prevent="emit('focus', obj.id)">{{ name(obj) }}</span>
          <template #description>
            {{ t(`source.${obj.bron}`) }}<template v-if="obj.score != null"> · {{ Math.round(obj.score * 100) }}%</template>
            <template v-if="obj.opgeslagen"> · {{ t("objects.saved") }}</template>
            <template v-if="obj.al_uitgesneden"> · {{ t("objects.already_extracted") }}</template>
            <span v-if="obj.bijschrift?.tekst" class="cc-object-bijschrift" :title="obj.bijschrift.tekst">“{{ obj.bijschrift.tekst }}”</span>
            <template v-if="obj.status === 'uitgesloten'"> · {{ t("status.uitgesloten") }}</template>
          </template>
        </cdx-checkbox>
        <span class="cc-object-knoppen">
          <cdx-button weight="quiet" size="small" :aria-label="t('objects.open')" @click="emit('open', obj.id)">
            <cdx-icon :icon="cdxIconEye" />
          </cdx-button>
          <cdx-button weight="quiet" size="small" action="destructive" :aria-label="t('objects.trash')" @click="emit('trash', obj.id)">
            <cdx-icon :icon="cdxIconTrash" />
          </cdx-button>
        </span>
      </li>
    </ul>
  </section>
</template>

<script setup>
import { computed, inject } from "vue";
import { CdxButton, CdxCheckbox, CdxIcon } from "@wikimedia/codex";
import { cdxIconEye, cdxIconTrash } from "@wikimedia/codex-icons";
import { useT } from "../i18n.js";
import { objectName } from "../state.js";

const props = defineProps({ objects: { type: Array, required: true }, focused: { type: String, default: null } });
const emit = defineEmits(["toggle", "select", "focus", "open", "hover", "trash"]);
const t = useT();
const language = inject("language", "nl");
const name = (obj) => objectName(obj, language);
// Regions from Commons first (in reading order), then the rest from top to bottom.
const sorted = computed(() =>
  [...props.objects].sort((a, b) => (a.bron === "commons") === (b.bron === "commons") ? a.box.y - b.box.y || a.box.x - b.box.x : a.bron === "commons" ? -1 : 1)
);
</script>
