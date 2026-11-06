<!-- The objects of the page with checkboxes (functional design 10.4). -->
<template>
  <section ref="root" class="cc-objecten">
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
        :data-id="obj.id"
        :class="[`cc-object-${obj.status}`, `cc-bron-${obj.bron}`, { focus: obj.id === focused, hover: obj.id === hovered, 'cc-nieuw': newIds.includes(obj.id), 'cc-uitkomst': resultIds.includes(obj.id) }]"
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
          <!-- Double-click (or the pencil) to rename it, like a layer in Photoshop. -->
          <input
            v-if="editingId === obj.id"
            ref="nameInput"
            v-model="draft"
            class="cc-object-naam-veld"
            :aria-label="t('objects.rename')"
            :placeholder="autoName(obj)"
            maxlength="120"
            @click.stop.prevent
            @keydown.enter.prevent="saveName(obj)"
            @keydown.esc.prevent="editingId = null"
            @blur="saveName(obj)"
          />
          <span v-else class="cc-object-naam" :title="t('objects.rename_help')" @click.prevent="emit('focus', obj.id)" @dblclick.prevent.stop="startRename(obj)">{{ listName(obj) }}</span>
          <template #description>
            {{ t(`source.${obj.bron}`) }}<template v-if="obj.score != null"> · {{ Math.round(obj.score * 100) }}%</template>
            <!-- Described: "Describe selected objects" skips it, so show it in the row. -->
            <template v-if="obj.beschrijving"> · <span class="cc-beschreven-label" :title="t('objects.described_help')">{{ t("objects.described") }}</span></template>
            <template v-if="obj.opgeslagen"> · <saved-label :object="obj" /></template>
            <template v-if="obj.al_uitgesneden"> · {{ t("objects.already_extracted") }}</template>
            <span v-if="obj.bijschrift?.tekst && name(obj) !== obj.bijschrift.tekst" class="cc-object-bijschrift" :title="obj.bijschrift.tekst">“{{ obj.bijschrift.tekst }}”</span>
            <template v-if="obj.status === 'uitgesloten'"> · {{ t("status.uitgesloten") }}</template>
            <template v-if="obj.bron === 'groep'"> · <button type="button" class="cc-link" @click.prevent.stop="emit('ungroup', obj.id)">{{ t("objects.ungroup") }}</button></template>
          </template>
        </cdx-checkbox>
        <span class="cc-object-knoppen">
          <cdx-button action="progressive" weight="quiet" size="small" :aria-label="`${t('objects.rename')}: ${listName(obj)}`" :title="t('objects.rename_help')" @click="startRename(obj)">
            <cdx-icon :icon="cdxIconEdit" />
          </cdx-button>
          <cdx-button action="progressive" weight="quiet" size="small" :aria-label="`${t('objects.open')}: ${listName(obj)}`" :title="t('objects.open')" @click="emit('open', obj.id)">
            <cdx-icon :icon="cdxIconEye" />
          </cdx-button>
          <cdx-button weight="quiet" size="small" action="destructive" :aria-label="`${t('objects.trash')}: ${listName(obj)}`" :title="t('objects.trash')" @click="emit('trash', obj.id)">
            <cdx-icon :icon="cdxIconTrash" />
          </cdx-button>
        </span>
      </li>
    </ul>
  </section>
</template>

<script setup>
import { computed, inject, nextTick, onBeforeUnmount, ref, watch } from "vue";
import { CdxButton, CdxCheckbox, CdxIcon } from "@wikimedia/codex";
import { cdxIconEdit, cdxIconEye, cdxIconTrash } from "@wikimedia/codex-icons";
import { objectPath } from "../api.js";
import { useT } from "../i18n.js";
import SavedLabel from "./SavedLabel.vue";
import { numberedNames, objectName } from "../state.js";

const props = defineProps({
  objects: { type: Array, required: true },
  focused: { type: String, default: null },
  hovered: { type: String, default: null },
  // Objects from the latest search: their frame is orange, so is their outline here.
  newIds: { type: Array, default: () => [] },
  // Objects the latest search message is about (found, or where a hit went): a green outline.
  resultIds: { type: Array, default: () => [] },
  mid: { type: String, required: true },
  n: { type: Number, required: true },
});
const emit = defineEmits(["toggle", "select", "focus", "open", "hover", "trash", "ungroup", "rename"]);

// Renaming in the list: Enter or leaving the field saves, Esc cancels; empty goes back
// to the automatic name (which shows in grey while typing).
const editingId = ref(null);
const draft = ref("");
const nameInput = ref(null);
function autoName(obj) {
  return objectName({ ...obj, naam: null }, language, t);
}
async function startRename(obj) {
  editingId.value = obj.id;
  // Start from the name as the list shows it, so you can edit it (wish Olaf); selected, so typing replaces it.
  draft.value = listName(obj);
  await nextTick();
  const input = Array.isArray(nameInput.value) ? nameInput.value[0] : nameInput.value;
  input?.focus();
  input?.select();
}
function saveName(obj) {
  if (editingId.value !== obj.id) return;
  editingId.value = null;
  const name = draft.value.trim();
  if (!obj.naam && name === listName(obj)) return; // unchanged automatic name: nothing to store
  if (name !== (obj.naam || "")) emit("rename", obj.id, name);
}
const t = useT();
const language = inject("language", "nl");

// The mouse on an object in the image: its row scrolls into view in the list, if it
// is out of view. Only the list's own column scrolls (never the page), after a short
// pause, so moving the mouse across the image does not make the list jump.
const root = ref(null);
let scrollTimer = null;
function scrollContainer(element) {
  for (let node = element?.parentElement; node; node = node.parentElement) {
    const overflow = getComputedStyle(node).overflowY;
    if ((overflow === "auto" || overflow === "scroll") && node.scrollHeight > node.clientHeight) return node;
  }
  return null;
}
function revealRow(id) {
  const row = root.value?.querySelector(`li[data-id="${CSS.escape(id)}"]`);
  const box = scrollContainer(row);
  if (!row || !box) return;
  const rowRect = row.getBoundingClientRect();
  const boxRect = box.getBoundingClientRect();
  const margin = 8;
  let delta = 0;
  if (rowRect.top < boxRect.top + margin) delta = rowRect.top - boxRect.top - margin;
  else if (rowRect.bottom > boxRect.bottom - margin) delta = rowRect.bottom - boxRect.bottom + margin;
  if (!delta) return;
  animateScroll(box, box.scrollTop + delta);
}

// A short glide of our own (native smooth scrolling is not reliable everywhere);
// it always ends at the target, also when the browser does not animate.
function animateScroll(box, target) {
  const start = box.scrollTop;
  if (window.matchMedia?.("(prefers-reduced-motion: reduce)").matches || !window.requestAnimationFrame) {
    box.scrollTop = target;
    return;
  }
  const duration = 200;
  const began = performance.now();
  const step = (now) => {
    const k = Math.min(1, (now - began) / duration);
    box.scrollTop = start + (target - start) * (1 - (1 - k) ** 3);
    if (k < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
  setTimeout(() => (box.scrollTop = target), duration + 50);
}
watch(
  () => props.hovered,
  (id) => {
    clearTimeout(scrollTimer);
    if (id) scrollTimer = setTimeout(() => props.hovered === id && revealRow(id), 150);
  }
);
onBeforeUnmount(() => clearTimeout(scrollTimer));
const name = (obj) => objectName(obj, language, t);
// A small cut-out; the box in the URL makes a changed object load anew.
const thumbnail = (obj) => `${objectPath(props.mid, props.n, obj.id)}/uitsnede.jpg?w=96&v=${obj.box.x}-${obj.box.y}-${obj.box.w}-${obj.box.h}`;
// Alphabetically by name; the same name in reading order (top to bottom, left to right).
const sorted = computed(() =>
  [...props.objects].sort((a, b) => name(a).localeCompare(name(b), language, { sensitivity: "base" }) || a.box.y - b.box.y || a.box.x - b.box.x)
);
// Names that occur more than once get a number ("house 1", "house 2"), the same
// as the names in the image (numberedNames); the magnifier and Commons keep the name.
const numbered = computed(() => numberedNames(props.objects, language, t));
const listName = (obj) => numbered.value[obj.id] || name(obj);
// A new search message: the first object it is about (in list order) scrolls into view,
// once the list shows it (wish Olaf).
watch(
  () => props.resultIds,
  async (ids) => {
    if (!ids?.length) return;
    await nextTick();
    const first = sorted.value.find((obj) => ids.includes(obj.id));
    if (first) revealRow(first.id);
  }
);
</script>
