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
    <!-- First what the action does (the text), then the objects it is about, then what else to
         know (the note; wish Olaf 13-11-2026): the main point is never lost in one long line. -->
    <template v-for="section in sections" :key="section.key">
    <pre v-if="section.quote" class="cc-prompt-tekst cc-bevestig-citaat">{{ state.quote }}</pre>
    <div v-else-if="section.fields" class="cc-bevestig-velden">
      <strong v-if="state.fieldsTitle" class="cc-bevestig-kop">{{ state.fieldsTitle }}</strong>
      <div v-for="(field, i) in state.fields" :key="i" class="cc-bevestig-veld-waarde">
        <span class="cc-bevestig-veld-naam"><strong>{{ field.label }}</strong>{{ field.help ? ` ${field.help}` : "" }}</span>
        <span class="cc-bevestig-waarde" :class="{ leeg: !field.value }">{{ field.value || t("confirm.empty") }}</span>
      </div>
    </div>
    <ul v-else-if="section.objects" class="cc-bevestig-objecten" :class="{ 'cc-bevestig-een': state.objects.length === 1 }">
      <li v-for="(obj, i) in state.objects" :key="i">
        <img v-if="obj.image" :src="obj.image" alt="" loading="lazy" />
        <span v-if="obj.name">{{ obj.name }}</span>
      </li>
    </ul>
    <template v-else>
    <div v-for="(block, b) in section.blocks" :key="b" class="cc-bevestig-blok" :class="{ 'cc-bevestig-noot': section.key === 'note' }">
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
    </template>
    </template>
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

// Blocks of a text: an optional **heading** line, then a list ("- " lines) or a paragraph.
const blocksOf = (text) =>
  String(text || "")
    .split(/\n\s*\n/)
    .map((block) => {
      const lines = block.split("\n").map((line) => line.trim()).filter(Boolean);
      const heading = /^\*\*(.+)\*\*$/.exec(lines[0] || "")?.[1];
      const rest = heading ? lines.slice(1) : lines;
      const items = rest.length && rest.every((line) => line.startsWith("- ")) ? rest.map((line) => line.slice(2)) : null;
      return { heading, items, text: items ? "" : rest.join(" ") };
    })
    .filter((block) => block.heading || block.items || block.text);
// In order: the text, the objects (unless they are on top), the note.
const sections = computed(() => [
  { key: "text", blocks: blocksOf(state.text) },
  ...(state.quote ? [{ key: "quote", quote: true }] : []),
  ...(state.fields?.length ? [{ key: "fields", fields: true }] : []),
  ...(state.objects?.length && !state.objectsFirst ? [{ key: "objects", objects: true }] : []),
  { key: "note", blocks: blocksOf(state.note) },
]);
// Links ({name} placeholders) and **bold** inside a line.
function parts(text) {
  return textParts(text, state.links).flatMap((part) =>
    part.link ? [part] : part.text.split("**").map((piece, i) => ({ text: piece, bold: i % 2 === 1 })).filter((p) => p.text)
  );
}
</script>
