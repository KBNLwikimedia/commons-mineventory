<!-- Messages as Codex Message (notice, warning, error, success), functional design 10.4. They stay
     until you close them with the cross, also a green one (wish Olaf 13-11-2026): never by themselves. -->
<template>
  <div class="cc-meldingen" aria-live="polite">
    <cdx-message
      v-for="notice in notices"
      :key="notice.id"
      :type="notice.type"
      :class="{ 'cc-melding-compact': notice.object }"
      :allow-user-dismiss="true"
      :dismiss-button-label="t('actions.close')"
      @user-dismissed="emit('dismiss', notice.id)"
    >
      <!-- Optionally the object it is about: on one line, a small cut-out and its name
           (the description as a tooltip), then the text and the actions. -->
      <span v-if="notice.object" class="cc-melding-object" :title="notice.object.description !== notice.object.name ? notice.object.description : ''">
        <img :src="notice.object.image" alt="" />
        <strong>{{ notice.object.name }}</strong>
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
