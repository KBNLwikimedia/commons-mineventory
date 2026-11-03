<!-- A small preview of the cut-out, on a checkerboard so transparency shows (magnifier tabs). -->
<template>
  <figure class="cc-concept-voorbeeld">
    <img :src="src" :alt="caption" />
    <figcaption class="cc-klein">{{ caption }}</figcaption>
  </figure>
</template>

<script setup>
defineProps({ src: { type: String, required: true }, caption: { type: String, required: true } });
</script>
