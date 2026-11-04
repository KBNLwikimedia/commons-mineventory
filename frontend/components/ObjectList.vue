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
        ·
        <button type="button" class="cc-link" @click="emit('select', objects.filter((o) => o.status !== 'uitgesloten' && o.status !== 'geselecteerd').map((o) => o.id))">
          {{ t("objects.invert") }}
        </button>
      </span>
    </header>
    <p v-if="!objects.length" class="cc-leeg">{{ t("objects.empty") }}</p>
    <ul>
      <li
        v-for="obj in sorted"
        :key="obj.id"
        :class="[`cc-object-${obj.status}`, `cc-bron-${obj.bron}`, { focus: obj.id === focused, hover: obj.id === hovered }]"
        @mouseenter="emit('hover', obj.id, true)"
        @mouseleave="emit('hover', obj.id, false)"
      >
        <button type="button" class="cc-object-duim" :aria-label="t('objects.open')" :title="t('objects.open')" @click="emit('open', obj.id)">
          <img :src="thumbnail(obj)" alt="" loading="lazy" />
        </button>
        <cdx-checkbox
          class="cc-object-vinkje"
          :model-value="obj.status === 'geselecteerd'"
          :disabled="obj.status === 'uitgesloten'"
          @update:model-value="emit('toggle', obj.id)"
        >
          <span class="cc-object-naam" @click.prevent="emit('focus', obj.id)">{{ listName(obj) }}</span>
          <template #description>
            {{ t(`source.${obj.bron}`) }}<template v-if="obj.score != null"> · {{ Math.round(obj.score * 100) }}%</template>
            <template v-if="obj.opgeslagen"> · {{ t("objects.saved") }}</template>
            <template v-if="obj.al_uitgesneden"> · {{ t("objects.already_extracted") }}</template>
            <span v-if="obj.bijschrift?.tekst && name(obj) !== obj.bijschrift.tekst" class="cc-object-bijschrift" :title="obj.bijschrift.tekst">“{{ obj.bijschrift.tekst }}”</span>
            <template v-if="obj.status === 'uitgesloten'"> · {{ t("status.uitgesloten") }}</template>
          </template>
        </cdx-checkbox>
        <span class="cc-object-knoppen">
          <cdx-button action="progressive" weight="quiet" size="small" :aria-label="t('objects.open')" @click="emit('open', obj.id)">
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
import { objectPath } from "../api.js";
import { useT } from "../i18n.js";
import { objectName } from "../state.js";

const props = defineProps({
  objects: { type: Array, required: true },
  focused: { type: String, default: null },
  hovered: { type: String, default: null },
  mid: { type: String, required: true },
  n: { type: Number, required: true },
});
const emit = defineEmits(["toggle", "select", "focus", "open", "hover", "trash"]);
const t = useT();
const language = inject("language", "nl");
const name = (obj) => objectName(obj, language, t);
// A small cut-out; the box in the URL makes a changed object load anew.
const thumbnail = (obj) => `${objectPath(props.mid, props.n, obj.id)}/uitsnede.jpg?w=96&v=${obj.box.x}-${obj.box.y}-${obj.box.w}-${obj.box.h}`;
// Alphabetically by name; the same name in reading order (top to bottom, left to right).
const sorted = computed(() =>
  [...props.objects].sort((a, b) => name(a).localeCompare(name(b), language, { sensitivity: "base" }) || a.box.y - b.box.y || a.box.x - b.box.x)
);
// Names that occur more than once get a number in this list only ("house 1",
// "house 2"), so they can be told apart; the magnifier and Commons keep the name.
const numbers = computed(() => {
  const counts = {};
  const result = {};
  for (const obj of sorted.value) {
    const key = name(obj).toLocaleLowerCase(language);
    counts[key] = (counts[key] || 0) + 1;
    result[obj.id] = counts[key];
  }
  for (const obj of sorted.value) if (counts[name(obj).toLocaleLowerCase(language)] === 1) delete result[obj.id];
  return result;
});
const listName = (obj) => (numbers.value[obj.id] ? `${name(obj)} ${numbers.value[obj.id]}` : name(obj));
</script>
