<!-- Messages as Codex Message (notice, warning, error, success), functional design 10.4. -->
<template>
  <div class="cc-meldingen" aria-live="polite">
    <cdx-message
      v-for="notice in notices"
      :key="notice.id"
      :type="notice.type"
      :allow-user-dismiss="true"
      :dismiss-button-label="t('actions.close')"
      :auto-dismiss="notice.type === 'success' ? 4000 : false"
      @user-dismissed="emit('dismiss', notice.id)"
      @auto-dismissed="emit('dismiss', notice.id)"
    >
      {{ notice.text }}
    </cdx-message>
  </div>
</template>

<script setup>
import { CdxMessage } from "@wikimedia/codex";
import { useT } from "../i18n.js";

defineProps({ notices: { type: Array, required: true } });
const emit = defineEmits(["dismiss"]);
const t = useT();
</script>
