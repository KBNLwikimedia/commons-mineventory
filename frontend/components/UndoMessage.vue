<!--
  The message after an action, with "↶ Ongedaan maken" when it can be undone (wish Olaf 13-11-2026).
  `note` is a useUndoMessage() (undo.js): one message per place, until you close it with the cross;
  never gone by itself. The slot adds a link after the undo button (e.g. "Naar de prullenbak").
-->
<template>
  <cdx-message
    v-if="note.message"
    :key="note.message.id"
    :type="note.message.type"
    class="cc-melding-compact cc-undo-melding"
    :allow-user-dismiss="true"
    :dismiss-button-label="t('actions.close')"
    @user-dismissed="note.clear()"
  >
    {{ note.message.text }}
    <span v-if="note.message.undo || $slots.default" class="cc-melding-acties">
      <button v-if="note.message.undo" type="button" class="cc-link" :disabled="note.busy" @click="note.undo()">
        {{ note.message.label || `↶ ${t("magnifier.undo")}` }}
      </button>
      <slot />
    </span>
  </cdx-message>
</template>

<script setup>
import { CdxMessage } from "@wikimedia/codex";
import { useT } from "../i18n.js";

defineProps({ note: { type: Object, required: true } });
const t = useT();
</script>
