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
    <p>
      <template v-for="(part, i) in textParts(state.text, state.links)" :key="i">
        <a v-if="part.link" :href="part.link.href" target="_blank" rel="noopener">{{ part.link.label }}</a>
        <template v-else>{{ part.text }}</template>
      </template>
    </p>
  </cdx-dialog>
</template>

<script setup>
import { CdxDialog } from "@wikimedia/codex";
import { answerConfirm, confirmState as state, textParts } from "../confirm.js";
import { useT } from "../i18n.js";

const t = useT();
</script>
