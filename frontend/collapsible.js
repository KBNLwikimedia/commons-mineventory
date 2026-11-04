// Collapsible boxes in the rendered wikitext, as Commons does with JavaScript
// (functional design 9.1, preview): tables with the class "collapsible" or
// "mw-collapsible" show only their first row, plus a button to open them;
// "collapsed" / "mw-collapsed" means they start closed. Divs hide their
// .mw-collapsible-content.
export function makeCollapsible(container, labels = { open: "Show", close: "Hide" }) {
  const boxes = container.querySelectorAll("table.collapsible, table.mw-collapsible, div.mw-collapsible");
  boxes.forEach((box) => {
    if (box.dataset.ccInklapbaar) return;
    box.dataset.ccInklapbaar = "1";
    const isTable = box.tagName === "TABLE";
    const rows = isTable ? [...box.rows].slice(1) : [...box.querySelectorAll(":scope > .mw-collapsible-content")];
    const header = isTable ? box.rows[0]?.cells[box.rows[0].cells.length - 1] : box;
    if (!rows.length || !header) return;
    const button = document.createElement("button");
    button.type = "button";
    button.className = "cc-inklap-knop";
    const set = (open) => {
      rows.forEach((row) => (row.hidden = !open));
      button.textContent = open ? `▾ ${labels.close}` : `▸ ${labels.open}`;
      button.setAttribute("aria-expanded", String(open));
    };
    button.addEventListener("click", () => set(button.getAttribute("aria-expanded") !== "true"));
    header.prepend(button);
    set(!box.classList.contains("collapsed") && !box.classList.contains("mw-collapsed"));
  });
}
