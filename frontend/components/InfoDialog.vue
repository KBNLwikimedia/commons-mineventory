<!--
  A small (i) button that opens a popup with an explanation: a title and a few
  paragraphs. It may sit in an accordion title, so the click does not toggle
  the accordion (as with the AI mark).
-->
<template>
  <cdx-button
    action="progressive"
    weight="quiet"
    size="small"
    class="cc-info-knop"
    :aria-label="label"
    :title="label"
    @click.stop.prevent="open = true"
  >
    <cdx-icon :icon="cdxIconInfo" size="small" /><template v-if="text"> {{ text }}</template>
  </cdx-button>
  <cdx-dialog
    v-model:open="open"
    class="cc-info-uitleg"
    :title="title"
    :use-close-button="true"
    :close-button-label="t('actions.close')"
    :default-action="{ label: t('actions.close') }"
    @default="open = false"
  >
    <!-- **text** in a paragraph is shown bold (no HTML from the texts); lines starting
         with "- " become a bulleted list. -->
    <template v-for="(block, i) in blocks" :key="i">
      <p v-if="block.text">
        <template v-for="(part, j) in block.text.split('**')" :key="j"><strong v-if="j % 2">{{ part }}</strong><template v-else>{{ part }}</template></template>
      </p>
      <ul v-if="block.items.length" class="cc-info-lijst">
        <li v-for="(item, k) in block.items" :key="k">
          <template v-for="(part, j) in item.split('**')" :key="j"><strong v-if="j % 2">{{ part }}</strong><template v-else>{{ part }}</template></template>
        </li>
      </ul>
    </template>
  </cdx-dialog>
</template>

<script setup>
import { computed, ref } from "vue";
import { CdxButton, CdxDialog, CdxIcon } from "@wikimedia/codex";
import { cdxIconInfo } from "@wikimedia/codex-icons";
import { useT } from "../i18n.js";

const props = defineProps({
  title: { type: String, required: true },
  label: { type: String, required: true },
  paragraphs: { type: Array, default: () => [] },
  // Optional visible text beside the (i), where the symbol alone does not say what it is about.
  text: { type: String, default: "" },
});
const t = useT();
const open = ref(false);

// Each paragraph: its text, and the "- " lines as list items.
const blocks = computed(() =>
  (props.paragraphs || []).map((paragraph) => {
    const lines = String(paragraph).split("\n");
    const items = lines.filter((line) => line.startsWith("- ")).map((line) => line.slice(2));
    return { text: lines.filter((line) => !line.startsWith("- ")).join(" ").trim(), items };
  })
);
</script>
