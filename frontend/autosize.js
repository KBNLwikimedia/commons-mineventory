// A text box as high as the text in it, right away: Codex' autosize only reacts
// once you type. Long texts stop at the CSS max-height and scroll.

export function fitToText(area) {
  if (!area) return;
  area.style.height = "auto";
  area.style.height = `${area.scrollHeight + 2}px`;
}
