<!--
  The larger view of a thumbnail (zoom.js), on the page itself, so the edges of a dialog do not
  cut it off.
-->
<template>
  <teleport to="body">
    <img v-if="zoom.show" class="cc-item-zoom" :src="zoom.src" alt="" :style="{ left: `${zoom.x}px`, top: `${zoom.y}px`, maxWidth: `${zoom.size}px`, maxHeight: `${zoom.size}px` }" />
  </teleport>
</template>

<script setup>
defineProps({ zoom: { type: Object, required: true } });
</script>
