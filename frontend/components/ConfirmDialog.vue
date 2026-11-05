<!-- Shows the question from askConfirm() (frontend/confirm.js) as a Codex dialog. -->
<template>
  <cdx-dialog
    :open="state.open"
    class="cc-bevestig"
    :title="state.title || t('confirm.title')"
    :use-close-button="true"
    :close-button-label="t('actions.close')"
    :primary-action="{ label: state.go || t('confirm.go'), actionType: state.destructive ? 'destructive' : 'progressive' }"
    :default-action="{ label: t('actions.cancel') }"
    @primary="answerConfirm(true)"
    @default="answerConfirm(false)"
    @update:open="(open) => !open && answerConfirm(false)"
  >
    <!-- The text in blocks (a blank line between them): a block may start with a
         **heading** line, and lines starting with "- " become a list. -->
    <div v-for="(block, b) in blocks" :key="b" class="cc-bevestig-blok">
      <strong v-if="block.heading" class="cc-bevestig-kop">{{ block.heading }}</strong>
      <ul v-if="block.items">
        <li v-for="(item, k) in block.items" :key="k">
          <template v-for="(part, i) in parts(item)" :key="i">
            <a v-if="part.link" :href="part.link.href" :class="part.link.class" :target="part.link.sameTab ? undefined : '_blank'" :rel="part.link.sameTab ? undefined : 'noopener'">{{ part.link.label }}</a>
            <strong v-else-if="part.bold">{{ part.text }}</strong>
            <template v-else>{{ part.text }}</template>
          </template>
        </li>
      </ul>
      <p v-else-if="block.text">
        <template v-for="(part, i) in parts(block.text)" :key="i">
          <a v-if="part.link" :href="part.link.href" :class="part.link.class" :target="part.link.sameTab ? undefined : '_blank'" :rel="part.link.sameTab ? undefined : 'noopener'">{{ part.link.label }}</a>
          <strong v-else-if="part.bold">{{ part.text }}</strong>
          <template v-else>{{ part.text }}</template>
        </template>
      </p>
    </div>
    <!-- For questions that may be switched off for this session ("Niet meer vragen"). -->
    <cdx-checkbox v-if="state.dontAsk" v-model="state.dontAskChecked" class="cc-niet-vragen">{{ t("confirm.dont_ask") }}</cdx-checkbox>
  </cdx-dialog>
</template>

<script setup>
import { computed } from "vue";
import { CdxCheckbox, CdxDialog } from "@wikimedia/codex";
import { answerConfirm, confirmState as state, textParts } from "../confirm.js";
import { useT } from "../i18n.js";

const t = useT();

// Blocks of the text: an optional **heading** line, then a list ("- " lines) or a paragraph.
const blocks = computed(() =>
  String(state.text || "")
    .split(/\n\s*\n/)
    .map((block) => {
      const lines = block.split("\n").map((line) => line.trim()).filter(Boolean);
      const heading = /^\*\*(.+)\*\*$/.exec(lines[0] || "")?.[1];
      const rest = heading ? lines.slice(1) : lines;
      const items = rest.length && rest.every((line) => line.startsWith("- ")) ? rest.map((line) => line.slice(2)) : null;
      return { heading, items, text: items ? "" : rest.join(" ") };
    })
);
// Links ({name} placeholders) and **bold** inside a line.
function parts(text) {
  return textParts(text, state.links).flatMap((part) =>
    part.link ? [part] : part.text.split("**").map((piece, i) => ({ text: piece, bold: i % 2 === 1 })).filter((p) => p.text)
  );
}
</script>
