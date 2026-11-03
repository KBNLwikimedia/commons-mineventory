<!-- Pages of a PDF, DjVu or multi-page TIFF, as thumbnails (functional design 10.4). -->
<template>
  <nav class="cc-paginas" :aria-label="t('pages.title')">
    <h3>{{ t("pages.title") }}</h3>
    <ol>
      <li v-for="item in file.pagina_lijst" :key="item.n">
        <button type="button" :class="{ actief: item.n === current }" :aria-current="item.n === current" @click="emit('select', item.n)">
          <img :src="item.afbeelding_url" alt="" loading="lazy" />
          <span>{{ t("pages.page", { n: item.n }) }}</span>
        </button>
      </li>
    </ol>
  </nav>
</template>

<script setup>
import { useT } from "../i18n.js";

defineProps({ file: { type: Object, required: true }, current: { type: Number, required: true } });
const emit = defineEmits(["select"]);
const t = useT();
</script>
