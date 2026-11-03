<!--
  A draggable border between two columns of the work area. It changes one CSS
  width variable (in px) on the work area; arrow keys move it too, and a
  double-click puts it back. The width is remembered in this browser.
-->
<template>
  <div
    ref="root"
    class="cc-splitter"
    role="separator"
    tabindex="0"
    aria-orientation="vertical"
    :aria-label="label"
    :title="label"
    :aria-valuenow="Math.round(width)"
    :aria-valuemin="min"
    :aria-valuemax="max"
    @pointerdown="start"
    @keydown="key"
    @dblclick="reset"
  ></div>
</template>

<script setup>
import { onMounted, ref } from "vue";

const props = defineProps({
  // The CSS variable on the work area, e.g. "--cc-links-breedte".
  variable: { type: String, required: true },
  // Which column it sizes: "left" grows when dragged right, "right" the other way.
  side: { type: String, required: true },
  storageKey: { type: String, required: true },
  label: { type: String, required: true },
  min: { type: Number, default: 160 },
  max: { type: Number, default: 640 },
});

const width = ref(0);

function area(el) {
  return el?.closest(".cc-werkblad");
}

function column(el) {
  return props.side === "left" ? el.previousElementSibling : el.nextElementSibling;
}

function apply(el, value, save = true) {
  width.value = Math.min(props.max, Math.max(props.min, value));
  area(el)?.style.setProperty(props.variable, `${width.value}px`);
  if (!save) return;
  try {
    window.localStorage.setItem(props.storageKey, String(Math.round(width.value)));
  } catch {
    // Blocked storage: the width is simply not remembered.
  }
}

const root = ref(null);

onMounted(() => {
  const el = root.value;
  let stored = null;
  try {
    stored = Number(window.localStorage.getItem(props.storageKey));
  } catch {
    stored = null;
  }
  if (stored) apply(el, stored, false);
  else width.value = column(el)?.getBoundingClientRect().width || props.min;
});

function start(event) {
  const el = event.currentTarget;
  const startX = event.clientX;
  const startWidth = column(el).getBoundingClientRect().width;
  const sign = props.side === "left" ? 1 : -1;
  el.setPointerCapture(event.pointerId);
  el.classList.add("actief");
  const move = (e) => apply(el, startWidth + sign * (e.clientX - startX));
  const stop = () => {
    el.classList.remove("actief");
    el.removeEventListener("pointermove", move);
    el.removeEventListener("pointerup", stop);
    el.removeEventListener("pointercancel", stop);
  };
  el.addEventListener("pointermove", move);
  el.addEventListener("pointerup", stop);
  el.addEventListener("pointercancel", stop);
  event.preventDefault();
}

function key(event) {
  const step = event.shiftKey ? 64 : 16;
  const sign = props.side === "left" ? 1 : -1;
  if (event.key === "ArrowLeft") apply(event.currentTarget, width.value - sign * step);
  else if (event.key === "ArrowRight") apply(event.currentTarget, width.value + sign * step);
  else return;
  event.preventDefault();
}

function reset(event) {
  const el = event.currentTarget;
  area(el)?.style.removeProperty(props.variable);
  try {
    window.localStorage.removeItem(props.storageKey);
  } catch {
    // Nothing to forget.
  }
  width.value = column(el)?.getBoundingClientRect().width || props.min;
}
</script>
