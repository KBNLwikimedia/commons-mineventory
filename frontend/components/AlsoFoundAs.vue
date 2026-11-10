<!--
  "Also found as: boy × child ×" (wish Olaf): the words an object was also found with before two finds
  were merged. The × removes a word where the image detection was wrong (the doll found as "boy");
  the object then no longer counts under it; Undo puts it back.
-->
<template>
  <span v-if="words.length || dropped" class="cc-ook-regel">
    <template v-if="words.length">
      <template v-if="label">{{ t("objects.also_found_as") + " " }}</template>
      <span v-for="word in shownWords" :key="word" class="cc-ook-woord">
        <!-- A word its name or description also uses is right (wish Olaf): no × to remove it. -->
        <template v-if="confirmed(word)"><span :title="t('objects.also_confirmed_help', { word })">{{ word }}</span></template>
        <template v-else>{{ word }}<button type="button" class="cc-ook-weg" :disabled="working" :aria-label="t('objects.also_drop', { word })" :title="t('objects.also_drop_help', { word })" @click.stop.prevent="drop(word)">×</button></template>
      </span>
      <!-- More than `fold` words (the list, wish Olaf): the rest behind a fold-out. -->
      <button v-if="hidden" type="button" class="cc-link cc-ook-meer" :aria-expanded="String(open)" @click.stop.prevent="open = !open">
        {{ open ? t("objects.also_less") : t("objects.also_more", { n: hidden }) }}
      </button>
    </template>
    <span v-if="dropped && undo" class="cc-ook-ongedaan">
      {{ t("objects.also_dropped", { word: dropped }) }}
      <button type="button" class="cc-link" :disabled="working" @click.stop.prevent="restore">↶ {{ t("magnifier.undo") }}</button>
    </span>
  </span>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import { del, objectPath, post } from "../api.js";
import { useT } from "../i18n.js";
import { isPlaceholderTerm } from "../class-colors.js";

const props = defineProps({
  object: { type: Object, required: true },
  mid: { type: String, required: true },
  n: { type: Number, required: true },
  // Undo after removing (the magnifier and the list, wish Olaf).
  undo: { type: Boolean, default: false },
  // "Also found as:" in front; off where a heading says so already (the magnifier).
  label: { type: Boolean, default: true },
  // Show at most this many words, the rest behind "+n more" (0: all).
  fold: { type: Number, default: 0 },
});
const emit = defineEmits(["changed", "error", "pending"]);
const t = useT();

// Each word once; clicks and drawn rectangles have no word of their own.
const words = computed(() => [...new Set((props.object.ook || []).map((e) => String(e.zoekterm || "").trim()).filter((w) => w && !isPlaceholderTerm(w)))]);
// The texts that name the object: your own name, its own search term (vintage car), the AI subject
// (Dutch and English), your caption.
const nameText = computed(() =>
  [props.object.naam, props.object.groep?.naam, props.object.zoekterm, props.object.label_item, props.object.beschrijving?.onderwerp, props.object.beschrijving?.onderwerp_en, props.object.bijschrift?.tekst]
    .filter(Boolean)
    .join(" \n ")
);
const escape = (text) => text.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
// "boy" in "Boy in white sailor suit": a whole word (also plural), not part of another word.
const confirmed = (word) => new RegExp(`(^|[^\\p{L}\\p{N}])${escape(word)}(s|es)?($|[^\\p{L}\\p{N}])`, "iu").test(nameText.value);
const open = ref(false);
const folded = computed(() => props.fold > 0 && words.value.length > props.fold);
const shownWords = computed(() => (folded.value && !open.value ? words.value.slice(0, props.fold) : words.value));
const hidden = computed(() => (folded.value ? words.value.length - props.fold : 0));
const dropped = ref("");
const working = ref(false);
watch(
  () => props.object.id,
  () => {
    dropped.value = "";
    emit("pending", false);
  }
);

// Undo is announced before the change goes up: the magnifier keeps its row around it only when it
// knows in time (Olaf: the row with Undo vanished when the last word went).
async function change(request, word) {
  working.value = true;
  try {
    const result = await request();
    dropped.value = word;
    emit("pending", Boolean(word && props.undo));
    emit("changed", result.object);
  } catch (e) {
    emit("error", e);
  } finally {
    working.value = false;
  }
}
const drop = (word) => change(() => del(`${objectPath(props.mid, props.n, props.object.id)}/ook/${encodeURIComponent(word)}`), word);
const restore = () => change(() => post(`${objectPath(props.mid, props.n, props.object.id)}/ook`, { woord: dropped.value }), "");
</script>
