<!--
  A list of opened files ("Bekeken"), newest first, with the page that was open.
  Click to open again. In the active list the bin sets an entry aside; in the
  list of entries set aside, the arrow up brings it back and the bin takes it off
  the list (after a confirmation). Every row can be dragged to the other list.
-->
<template>
  <ul class="cc-geschiedenis">
    <li
      v-for="entry in entries"
      :key="entry.mid"
      :class="{ huidig: entry.mid === current }"
      draggable="true"
      :title="t('history.drag')"
      @dragstart="dragStart($event, entry)"
    >
      <a :href="appUrl(entry.mid, entry.pagina || 1)" draggable="false" :aria-current="entry.mid === current ? 'page' : undefined" @click="open($event, entry)">
        <img :src="`/api/v1/bestand/${entry.mid}/pagina/1/afbeelding?w=120`" alt="" loading="lazy" draggable="false" />
        <span class="cc-geschiedenis-tekst">
          <strong class="cc-afkappen" :title="entry.naam">{{ entry.naam || entry.mid }}</strong>
          <small>
            {{ entry.mid }}<template v-if="entry.paginas > 1"> · {{ t("pages.page", { n: entry.pagina || 1 }) }}</template>
            · {{ when(entry.tijd) }}
          </small>
        </span>
      </a>
      <!-- Set aside: back (blue) above, off the list (red) below, so the name keeps its room. -->
      <span v-if="aside" class="cc-geschiedenis-knoppen">
        <cdx-button action="progressive" weight="quiet" size="small" :aria-label="`${t('history.restore')}: ${entry.naam || entry.mid}`" :title="t('history.restore')" @click="emit('restore', entry.mid)">
          <cdx-icon :icon="cdxIconArrowUp" />
        </cdx-button>
        <cdx-button action="destructive" weight="quiet" size="small" :aria-label="`${t('history.remove')}: ${entry.naam || entry.mid}`" :title="t('history.remove')" @click="emit('remove', entry.mid)">
          <cdx-icon :icon="cdxIconTrash" />
        </cdx-button>
      </span>
      <cdx-button v-else action="progressive" weight="quiet" size="small" :aria-label="`${t('history.set_aside')}: ${entry.naam || entry.mid}`" :title="t('history.set_aside')" @click="emit('aside', entry.mid)">
        <cdx-icon :icon="cdxIconTrash" />
      </cdx-button>
    </li>
  </ul>
</template>

<script setup>
import { inject } from "vue";
import { CdxButton, CdxIcon } from "@wikimedia/codex";
import { cdxIconArrowUp, cdxIconTrash } from "@wikimedia/codex-icons";
import { useT } from "../i18n.js";
import { DRAG_TYPE, appUrl } from "../state.js";

defineProps({
  entries: { type: Array, required: true },
  current: { type: String, default: null },
  // The list of entries set aside (other buttons).
  aside: { type: Boolean, default: false },
});
const emit = defineEmits(["aside", "restore", "remove", "open"]);

// A plain click opens the file within the app, so the waiting feedback shows at once;
// Ctrl-, Shift- or middle-click keeps the link (a new tab or window).
function open(event, entry) {
  if (event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
  event.preventDefault();
  emit("open", entry);
}
const t = useT();
const language = inject("language", "nl");

// Dragging a row carries its M-id; ViewedPanel.vue decides where it lands.
function dragStart(event, entry) {
  event.dataTransfer.setData(DRAG_TYPE, entry.mid);
  event.dataTransfer.setData("text/plain", entry.mid);
  event.dataTransfer.effectAllowed = "move";
}

const format = new Intl.DateTimeFormat(language === "nl" ? "nl-NL" : "en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
function when(iso) {
  try {
    return format.format(new Date(iso));
  } catch {
    return "";
  }
}
</script>
