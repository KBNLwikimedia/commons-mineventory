<!-- Shows the question from askConfirm() (frontend/confirm.js) as a Codex dialog. -->
<template>
  <cdx-dialog
    :open="state.open"
    class="cc-bevestig"
    :title="state.title || t('confirm.title')"
    :use-close-button="true"
    :close-button-label="t('actions.close')"
    :primary-action="{ label: chosen?.go || state.go || t('confirm.go'), actionType: (chosen ? chosen.destructive : state.destructive) ? 'destructive' : 'progressive' }"
    :default-action="{ label: t('actions.cancel') }"
    @primary="answerConfirm(true)"
    @default="answerConfirm(false)"
    @update:open="(open) => !open && answerConfirm(false)"
  >
    <!-- The text in blocks (a blank line between them): a block may start with a
         **heading** line, and lines starting with "- " become a list. -->
    <ul v-if="state.objects?.length && state.objectsFirst" class="cc-bevestig-objecten cc-bevestig-objecten-boven">
      <li v-for="(obj, i) in state.objects" :key="i">
        <img v-if="obj.image" :src="obj.image" alt="" loading="lazy" />
        <span v-if="obj.name">{{ obj.name }}</span>
      </li>
    </ul>
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
    <!-- The objects the question is about, each with a small cut-out (below the text, or on top). -->
    <ul v-if="state.objects?.length && !state.objectsFirst" class="cc-bevestig-objecten">
      <li v-for="(obj, i) in state.objects" :key="i">
        <img v-if="obj.image" :src="obj.image" alt="" loading="lazy" />
        <span v-if="obj.name">{{ obj.name }}</span>
      </li>
    </ul>
    <!-- An optional choice: what the button does follows the chosen option. -->
    <div v-if="state.choices?.length" class="cc-bevestig-keuze" role="radiogroup">
      <cdx-radio v-for="option in state.choices" :key="option.value" v-model="state.choice" name="cc-bevestig-keuze" :input-value="option.value">
        {{ option.label }}
        <template v-if="option.help" #description>{{ option.help }}</template>
      </cdx-radio>
    </div>
    <!-- An optional text field; the placeholder (grey) is what is used when it stays empty. -->
    <cdx-field v-if="state.input" class="cc-bevestig-veld" :optional="true" :optional-flag="t('confirm.optional')">
      <cdx-text-input v-model="state.inputValue" :placeholder="state.input.placeholder" @keydown.enter.prevent="answerConfirm(true)" />
      <template #label>{{ state.input.label }}</template>
      <template v-if="state.input.help" #help-text>{{ state.input.help }}</template>
    </cdx-field>
    <!-- For questions that may be switched off for this session ("Niet meer vragen"). -->
    <cdx-checkbox v-if="state.dontAsk" v-model="state.dontAskChecked" class="cc-niet-vragen">{{ t("confirm.dont_ask") }}</cdx-checkbox>
  </cdx-dialog>
</template>

<script setup>
import { computed } from "vue";
import { CdxCheckbox, CdxDialog, CdxField, CdxRadio, CdxTextInput } from "@wikimedia/codex";
import { answerConfirm, confirmState as state, textParts } from "../confirm.js";
import { useT } from "../i18n.js";

const t = useT();
const chosen = computed(() => (state.choices || []).find((option) => option.value === state.choice) || null);

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
