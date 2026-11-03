// Moving and resizing a dialog (the magnifier): drag the title bar to move it,
// drag an edge or corner to resize it. Plain JS, like the viewer; the Vue
// component only switches it on. Position and size are remembered per browser.

export const EDGES = ["n", "s", "e", "w", "ne", "nw", "se", "sw"];

/* The new rectangle {left, top, width, height} after dragging `edge` by dx, dy:
   at least `min` wide and high, and never beyond the viewport. */
export function resizeRect(rect, edge, dx, dy, min = { width: 320, height: 200 }, viewport = { width: Infinity, height: Infinity }) {
  let { left, top, width, height } = rect;
  if (edge.includes("e")) width = Math.min(Math.max(min.width, width + dx), viewport.width - left);
  if (edge.includes("s")) height = Math.min(Math.max(min.height, height + dy), viewport.height - top);
  if (edge.includes("w")) {
    const right = left + width;
    left = Math.min(Math.max(0, left + dx), right - min.width);
    width = right - left;
  }
  if (edge.includes("n")) {
    const bottom = top + height;
    top = Math.min(Math.max(0, top + dy), bottom - min.height);
    height = bottom - top;
  }
  return { left, top, width, height };
}

/* The rectangle moved by dx, dy, kept entirely on screen (so the close button stays reachable). */
export function moveRect(rect, dx, dy, viewport = { width: Infinity, height: Infinity }) {
  return {
    ...rect,
    left: Math.min(Math.max(0, rect.left + dx), Math.max(0, viewport.width - rect.width)),
    top: Math.min(Math.max(0, rect.top + dy), Math.max(0, viewport.height - rect.height)),
  };
}

function load(key) {
  try {
    return JSON.parse(localStorage.getItem(key) || "null");
  } catch {
    return null;
  }
}

function save(key, rect) {
  try {
    localStorage.setItem(key, JSON.stringify(rect));
  } catch {
    // Private mode or blocked storage: it simply is not remembered.
  }
}

/* Makes `dialog` movable by `handle` and resizable at its edges. Returns a function that undoes it. */
export function makeMovable(dialog, { handle, storageKey, labels = {}, min } = {}) {
  const viewport = () => ({ width: window.innerWidth, height: window.innerHeight });

  function apply(rect) {
    Object.assign(dialog.style, {
      position: "fixed",
      margin: "0",
      left: `${rect.left}px`,
      top: `${rect.top}px`,
      width: `${rect.width}px`,
      height: `${rect.height}px`,
      maxWidth: "none",
      maxHeight: "none",
    });
  }

  function current() {
    const box = dialog.getBoundingClientRect();
    return { left: box.left, top: box.top, width: box.width, height: box.height };
  }

  const remembered = storageKey && load(storageKey);
  if (remembered && remembered.width > 0) {
    const fitted = resizeRect(moveRect(remembered, 0, 0, viewport()), "se", 0, 0, min, viewport());
    apply(fitted);
  }

  // Dragging: the pointer is captured, so moving fast or over the page still works.
  function drag(event, change) {
    if (event.button !== 0) return;
    event.preventDefault();
    const start = { x: event.clientX, y: event.clientY, rect: current() };
    const target = event.currentTarget;
    try {
      target.setPointerCapture(event.pointerId);
    } catch {
      // Without capture dragging still works while the pointer stays on the grip.
    }
    dialog.classList.add("cc-slepen");
    const onMove = (e) => apply(change(start.rect, e.clientX - start.x, e.clientY - start.y));
    const onUp = () => {
      target.removeEventListener("pointermove", onMove);
      target.removeEventListener("pointerup", onUp);
      target.removeEventListener("pointercancel", onUp);
      dialog.classList.remove("cc-slepen");
      if (storageKey) save(storageKey, current());
    };
    target.addEventListener("pointermove", onMove);
    target.addEventListener("pointerup", onUp);
    target.addEventListener("pointercancel", onUp);
  }

  const onHandleDown = (event) => {
    if (event.target.closest("button, a, input, textarea, select")) return; // the close button stays a button
    drag(event, (rect, dx, dy) => moveRect(rect, dx, dy, viewport()));
  };
  handle?.addEventListener("pointerdown", onHandleDown);
  handle?.classList.add("cc-sleepgreep");
  if (handle && labels.move) handle.title = labels.move;

  const grips = EDGES.map((edge) => {
    const grip = document.createElement("div");
    grip.className = `cc-rand cc-rand-${edge}`;
    grip.setAttribute("aria-hidden", "true");
    if (labels.resize) grip.title = labels.resize;
    grip.addEventListener("pointerdown", (event) => drag(event, (rect, dx, dy) => resizeRect(rect, edge, dx, dy, min, viewport())));
    dialog.append(grip);
    return grip;
  });
  dialog.classList.add("cc-verplaatsbaar");

  return () => {
    handle?.removeEventListener("pointerdown", onHandleDown);
    handle?.classList.remove("cc-sleepgreep");
    grips.forEach((grip) => grip.remove());
    dialog.classList.remove("cc-verplaatsbaar");
  };
}

/* Forget the remembered position and size (the dialog is centred again next time). */
export function forgetPlacement(storageKey) {
  try {
    localStorage.removeItem(storageKey);
  } catch {
    // nothing to forget
  }
}
