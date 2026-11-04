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
      <!-- Optionally the object it is about: a small cut-out, its name and description. -->
      <span v-if="notice.object" class="cc-melding-object">
        <img :src="notice.object.image" alt="" />
        <span>
          <strong>{{ notice.object.name }}</strong>
          <span v-if="notice.object.description && notice.object.description !== notice.object.name" class="cc-klein cc-melding-beschrijving">{{ notice.object.description }}</span>
        </span>
      </span>
      {{ notice.text }}
      <span v-if="notice.actions?.length || notice.link" class="cc-melding-acties">
        <button v-for="action in notice.actions || []" :key="action.label" type="button" class="cc-link" @click="action.run(); emit('dismiss', notice.id)">
          {{ action.label }}
        </button>
        <a v-if="notice.link" :href="notice.link.href">{{ notice.link.label }}</a>
      </span>
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
