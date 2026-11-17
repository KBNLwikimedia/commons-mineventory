// A larger view beside a thumbnail while the mouse is on it (wish Olaf): the image (P18) of a
// Wikidata item, or another image such as the cut-out of an object. Shared by the window for
// the whole image (OriginalData.vue) and the window of a cut-out (Magnifier.vue); ItemZoom.vue
// shows it. Only for a thumbnail that loaded; kept on screen.
import { reactive } from "vue";
import { itemImage } from "./wikidata.js";

export const ZOOM_SIZE = 260;

export function useItemZoom() {
  const zoom = reactive({ show: false, src: "", x: 0, y: 0, size: ZOOM_SIZE });
  function showZoom(event, q, src = "", size = ZOOM_SIZE) {
    const img = event.target;
    if (!img.naturalWidth) return;
    const rect = img.getBoundingClientRect();
    let x = rect.right + 8;
    if (x + size > window.innerWidth) x = Math.max(0, rect.left - size - 8);
    const y = Math.min(Math.max(0, rect.top - 40), window.innerHeight - size - 8);
    Object.assign(zoom, { show: true, src: src || itemImage(q, 240), x, y, size });
  }
  const hideZoom = () => (zoom.show = false);
  return { zoom, showZoom, hideZoom };
}
