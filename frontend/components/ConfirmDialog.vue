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
    <p>{{ state.text }}</p>
  </cdx-dialog>
</template>

<script setup>
import { CdxDialog } from "@wikimedia/codex";
import { answerConfirm, confirmState as state } from "../confirm.js";
import { useT } from "../i18n.js";

const t = useT();
</script>
