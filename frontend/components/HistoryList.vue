<!--
  "Laatst bezocht": the files opened in this browser, newest first, with the
  page that was open. Click to open again; the bin removes one entry.
-->
<template>
  <section v-if="entries.length" class="cc-geschiedenis">
    <ul>
      <li v-for="entry in entries" :key="entry.mid" :class="{ huidig: entry.mid === current }">
        <a :href="appUrl(entry.mid, entry.pagina || 1)" :aria-current="entry.mid === current ? 'page' : undefined">
          <img :src="`/api/v1/bestand/${entry.mid}/pagina/1/afbeelding?w=120`" alt="" loading="lazy" />
          <span class="cc-geschiedenis-tekst">
            <strong class="cc-afkappen" :title="entry.naam">{{ entry.naam || entry.mid }}</strong>
            <small>
              {{ entry.mid }}<template v-if="entry.paginas > 1"> · {{ t("pages.page", { n: entry.pagina || 1 }) }}</template>
              · {{ when(entry.tijd) }}
            </small>
          </span>
        </a>
        <cdx-button action="progressive" weight="quiet" size="small" :aria-label="`${t('history.remove')}: ${entry.naam || entry.mid}`" :title="t('history.remove')" @click="emit('remove', entry.mid)">
          <cdx-icon :icon="cdxIconTrash" />
        </cdx-button>
      </li>
    </ul>
    <button type="button" class="cc-link cc-klein" @click="emit('clear')">{{ t("history.clear") }}</button>
  </section>
</template>

<script setup>
import { inject } from "vue";
import { CdxButton, CdxIcon } from "@wikimedia/codex";
import { cdxIconTrash } from "@wikimedia/codex-icons";
import { useT } from "../i18n.js";
import { appUrl } from "../state.js";

defineProps({ entries: { type: Array, required: true }, current: { type: String, default: null } });
const emit = defineEmits(["remove", "clear"]);
const t = useT();
const language = inject("language", "nl");

const format = new Intl.DateTimeFormat(language === "nl" ? "nl-NL" : "en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
function when(iso) {
  try {
    return format.format(new Date(iso));
  } catch {
    return "";
  }
}
</script>
