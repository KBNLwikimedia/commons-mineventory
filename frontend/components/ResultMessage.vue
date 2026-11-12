<!--
  The outcome of an action in the detection panel, under the button that asked for it (one
  component instead of six copies, 12-11-2026): what was found, where the other finds went
  (merged, in a group, in the trash, with "Restore from trash"), and after nothing was found
  the other ways to get the object.
-->
<template>
  <cdx-message :type="type" :allow-user-dismiss="true" :dismiss-button-label="t('actions.close')" class="cc-zoekresultaat" @user-dismissed="emit('dismiss')">
    {{ text }}
    <p v-if="also" class="cc-melding-alinea">
      {{ also }}<template v-if="result.trashIds?.length"> <button type="button" class="cc-link" :disabled="busy" @click="emit('restore-trash')">↶ {{ t("panel.result_restore_trash") }}</button></template>
    </p>
    <p v-if="result.restoreError" class="cc-melding-alinea">{{ result.restoreError }}</p>
    <ul v-if="merged.length" class="cc-melding-lijst" :aria-label="t('panel.result_merged_into')">
      <li v-for="name in merged" :key="name">{{ name }}</li>
    </ul>
    <!-- Nothing found: the other ways to get the object, as links to their sections. -->
    <template v-if="otherWays">
      {{ t("panel.result_none_next") }}
      <ul class="cc-andere-weg">
        <li v-if="searchLink"><button type="button" class="cc-link" @click="emit('try-search')">{{ t("panel.result_try_search") }}</button></li>
        <li><button type="button" class="cc-link" @click="emit('try-point', 'point')">{{ t("panel.result_try_point") }}</button></li>
        <li><button type="button" class="cc-link" @click="emit('try-point', 'draw')">{{ t("panel.result_try_draw") }}</button></li>
      </ul>
    </template>
  </cdx-message>
</template>

<script setup>
import { CdxMessage } from "@wikimedia/codex";
import { useT } from "../i18n.js";

defineProps({
  result: { type: Object, required: true },
  type: { type: String, default: "success" },
  text: { type: String, default: "" },
  also: { type: String, default: "" },
  merged: { type: Array, default: () => [] },
  busy: { type: Boolean, default: false },
  // After nothing was found: the other ways; Search leaves out the link to itself.
  otherWays: { type: Boolean, default: false },
  searchLink: { type: Boolean, default: true },
});
const emit = defineEmits(["dismiss", "restore-trash", "try-search", "try-point"]);
const t = useT();
</script>
