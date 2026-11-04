// Smooth folding for every Codex Accordion in the app: the content grows open
// and shrinks closed (speeding up, then slowing down) instead of jumping.
// Codex uses a native <details>; opening is left to it and then animated,
// closing is held back until the content has shrunk. Before closing, the
// <details> gets a "cc-closing" event, so a page can react at the start.
// Nothing moves when the system asks for reduced motion.

export const DURATION = 350;
export const EASE = "cubic-bezier(0.65, 0, 0.35, 1)";

function reducedMotion() {
  return Boolean(window.matchMedia?.("(prefers-reduced-motion: reduce)").matches);
}

function content(details) {
  return details.querySelector(":scope > .cdx-accordion__content");
}

// The content's padding folds along, so nothing appears in one jump.
function animateHeight(element, from, to, done) {
  if (!element.animate) return done?.();
  const style = getComputedStyle(element);
  const shown = { paddingTop: style.paddingTop, paddingBottom: style.paddingBottom, opacity: 1 };
  const hidden = { paddingTop: "0px", paddingBottom: "0px", opacity: 0 };
  element.style.overflow = "hidden";
  const animation = element.animate(
    [
      { height: `${from}px`, ...(from ? shown : hidden) },
      { height: `${to}px`, ...(to ? shown : hidden) },
    ],
    { duration: DURATION, easing: EASE }
  );
  animation.onfinish = animation.oncancel = () => {
    element.style.overflow = "";
    done?.();
  };
}

function onClick(event) {
  const summary = event.target.closest("details.cdx-accordion > summary");
  if (!summary || reducedMotion()) return;
  // A button or link inside the title (an AI mark) does not fold.
  const control = event.target.closest("button, a, input, select, textarea");
  if (control && summary.contains(control)) return;
  const details = summary.parentElement;
  if (details.dataset.ccFolding) {
    event.preventDefault();
    return;
  }
  if (!details.open) {
    // Let the browser (and Codex) open it, then grow the content.
    requestAnimationFrame(() => {
      const box = content(details);
      if (box) animateHeight(box, 0, box.scrollHeight);
    });
    return;
  }
  const box = content(details);
  if (!box) return;
  event.preventDefault();
  details.dataset.ccFolding = "1";
  details.dispatchEvent(new CustomEvent("cc-closing"));
  animateHeight(box, box.offsetHeight, 0, () => {
    delete details.dataset.ccFolding;
    details.open = false; // Codex follows through the toggle event
  });
}

let installed = false;

/* Once per page: listens on the document, so accordions in dialogs count too. */
export function smoothAccordions(root = document) {
  if (installed) return;
  installed = true;
  root.addEventListener("click", onClick, true);
}
