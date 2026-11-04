/*
 * Page viewer: zoom/pan over a page image with an SVG overlay in native page
 * pixels (pixels of the original on Commons). Taken over from the Delpher
 * Uitsnijder (static/js/viewer.js) as a plain ES module, deliberately without
 * Vue: drawing happens dozens of times per second (functional design 10.2).
 *
 * Interface for the Vue wrapper (ViewerPane.vue):
 *   functions  load(page), setObjects(objects, newIds), setSelection(ids),
 *              setLabels(on), zoomToBox(box), focusObject(id), setObjectHover(id, on),
 *              setPointMode(on), setDrawMode(on), fit(), zoomStep(direction), zoomTo(scale), destroy()
 *   events     "object-click" {object, ctrl}, "object-open" object,
 *              "point" {x, y, ctrl}, "rectangle" {x, y, w, h},
 *              "object-hover" object|null, "zoom" scale, "imageload", "imageerror"
 *
 * Objects are drawn with a class per status (kandidaat, geselecteerd,
 * uitgesloten) and per source (object-commons: the yellow regions from Commons).
 * Shift-drag, or any drag in draw mode, draws a manual rectangle; a click on
 * an empty spot is a point.
 */

const SVG_NS = "http://www.w3.org/2000/svg";
const DRAG_THRESHOLD = 4;
const MAX_SCALE = 3;
// Fixed steps for the + and - buttons, so that 100% can always be reached.
export const ZOOM_STEPS = [0.03, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25, 0.33, 0.5, 0.67, 0.75, 1, 1.25, 1.5, 2, 2.5, 3];

/* The next zoom step up (+1) or down (-1) from `now`, or null at the end. */
export function nextZoomStep(now, direction) {
  return direction > 0
    ? ZOOM_STEPS.find((s) => s > now * 1.01) ?? null
    : [...ZOOM_STEPS].reverse().find((s) => s < now * 0.99) ?? null;
}

/* A rectangle {x, y, w, h} from two corner points, in either order. */
export function normaliseRect(a, b) {
  return {
    x: Math.min(a.x, b.x),
    y: Math.min(a.y, b.y),
    w: Math.abs(b.x - a.x),
    h: Math.abs(b.y - a.y),
  };
}

/* Default tooltip content of an object; the app passes a richer one. */
function defaultDescribe(obj) {
  return { title: obj.label_nl || obj.label, details: [obj.status], hint: "" };
}

/* Default name above an object when labels are on; the app passes its own. */
function defaultLabel(obj) {
  return obj.label_nl || obj.label || "";
}

export class PageViewer {
  constructor(element, { describe = defaultDescribe, label = defaultLabel } = {}) {
    this.el = element;
    this.describe = describe;
    this.label = label;
    this.showLabels = false;
    this.lastObjects = [[], []];
    this.stage = document.createElement("div");
    this.stage.className = "viewer-podium";
    this.img = document.createElement("img");
    this.img.alt = "";
    this.img.draggable = false;
    this.img.addEventListener("load", () => this._emit("imageload"));
    this.img.addEventListener("error", () => this._emit("imageerror"));
    this.svg = document.createElementNS(SVG_NS, "svg");
    this.defs = document.createElementNS(SVG_NS, "defs");
    this.zoneLayer = document.createElementNS(SVG_NS, "g");
    this.objectLayer = document.createElementNS(SVG_NS, "g");
    this.drawLayer = document.createElementNS(SVG_NS, "g");
    this.svg.append(this.defs, this.zoneLayer, this.objectLayer, this.drawLayer);
    this.stage.append(this.img, this.svg);
    this.tooltip = document.createElement("div");
    this.tooltip.className = "tooltip";
    this.tooltip.hidden = true;
    this.el.append(this.stage, this.tooltip);

    this.page = null;
    this.scale = 1;
    this.tx = 0;
    this.ty = 0;
    this.handlers = {};
    this.objectElements = new Map();
    this.pointMode = false;
    this.drawMode = false;
    this._bindEvents();
  }

  on(event, fn) {
    (this.handlers[event] = this.handlers[event] || []).push(fn);
    return () => {
      this.handlers[event] = this.handlers[event].filter((f) => f !== fn);
    };
  }

  _emit(event, payload) {
    (this.handlers[event] || []).forEach((fn) => fn(payload));
  }

  /* page: {width, height, src, srcWidth, srcLarge} */
  load(page) {
    this.page = page;
    this.largeLoaded = false;
    this.stage.style.width = page.width + "px";
    this.stage.style.height = page.height + "px";
    this.svg.setAttribute("viewBox", `0 0 ${page.width} ${page.height}`);
    this.svg.setAttribute("preserveAspectRatio", "none");
    this.img.src = page.src;
    this.setZones([]);
    this.setObjects([]);
    this.fit();
  }

  /* Plain rectangles under the objects (e.g. file notes), {id, title, rechthoeken}. */
  setZones(zones) {
    this.zoneLayer.replaceChildren();
    zones.forEach((zone) => {
      zone.rechthoeken.forEach((r) => {
        const rect = document.createElementNS(SVG_NS, "rect");
        this._setBox(rect, r);
        rect.setAttribute("class", "zone");
        this.zoneLayer.append(rect);
      });
    });
  }

  /* Detected objects. Selected ones and regions show their mask: an
     accent-coloured rectangle masked by the object's mask PNG. */
  setObjects(objects, newIds) {
    this.lastObjects = [objects, newIds];
    // Marks that outlive a redraw (a new answer from the server): under the mouse, chosen in the list.
    const marked = {};
    this.objectElements.forEach((group, id) => {
      ["hover", "uitgelicht"].forEach((name) => group.classList.contains(name) && (marked[name] = id));
    });
    this.objectLayer.replaceChildren();
    this.defs.replaceChildren();
    this.objectElements.clear();
    const fresh = new Set(newIds || []);
    objects.forEach((obj) => {
      const group = document.createElementNS(SVG_NS, "g");
      group.setAttribute("class", this._classes(obj, fresh.has(obj.id)));
      group.dataset.id = obj.id;
      group.object = obj;
      if (obj.status !== "uitgesloten" && obj.masker) this._addMask(group, obj);
      const outline = document.createElementNS(SVG_NS, "rect");
      this._setBox(outline, obj.box);
      outline.setAttribute("class", "object-rand");
      outline.addEventListener("pointerenter", (e) => this._hoverObject(obj, e));
      outline.addEventListener("pointermove", (e) => this._moveTooltip(e));
      outline.addEventListener("pointerleave", () => this._hoverObject(null));
      group.append(outline);
      if (obj.bron === "commons" && obj.label) {
        const label = document.createElementNS(SVG_NS, "text");
        label.setAttribute("x", obj.box.x + 4);
        label.setAttribute("y", obj.box.y + 4);
        label.setAttribute("class", "object-naam");
        label.textContent = obj.label_nl || obj.label;
        group.append(label);
      } else if (this.showLabels) {
        // The name above the box (in the colour of its frame), like the regions on Commons.
        const label = document.createElementNS(SVG_NS, "text");
        label.setAttribute("x", obj.box.x);
        label.setAttribute("y", obj.box.y);
        label.setAttribute("class", "object-naam object-naam-boven");
        label.textContent = this.label(obj);
        group.append(label);
      }
      this.objectLayer.append(group);
      this.objectElements.set(obj.id, group);
    });
    Object.entries(marked).forEach(([name, id]) => {
      const group = this.objectElements.get(id);
      if (!group) return;
      group.classList.add(name);
      if (group.object.masker) this._addMask(group, group.object);
    });
    this._scaleLabels();
  }

  _classes(obj, fresh) {
    return [
      "object",
      `object-${obj.status}`,
      `object-${obj.bron}`,
      fresh ? "object-nieuw" : "",
      obj.masker ? "object-gemaskerd" : "",
    ].filter(Boolean).join(" ");
  }

  /* Names on the image for every object (the regions from Commons always have one). */
  setLabels(on) {
    this.showLabels = Boolean(on);
    this.setObjects(...this.lastObjects);
  }

  /* Only the status classes change (no rebuild): ids are the selected objects. */
  setSelection(ids) {
    const selected = new Set(ids);
    this.objectElements.forEach((group, id) => {
      const obj = group.object;
      obj.status = selected.has(id) ? "geselecteerd" : obj.status === "geselecteerd" ? "kandidaat" : obj.status;
      // Keep the marks that are not about the status: under the mouse, chosen in the list.
      const kept = ["hover", "uitgelicht"].filter((name) => group.classList.contains(name));
      group.setAttribute("class", [this._classes(obj, group.classList.contains("object-nieuw")), ...kept].join(" "));
    });
  }

  _addMask(group, obj) {
    if (group.querySelector(".object-masker")) return;
    const b = obj.box;
    const maskId = "masker-" + obj.id;
    const mask = document.createElementNS(SVG_NS, "mask");
    mask.setAttribute("id", maskId);
    mask.setAttribute("maskUnits", "userSpaceOnUse");
    const image = document.createElementNS(SVG_NS, "image");
    image.setAttribute("href", obj.masker_url);
    this._setBox(image, b, "width");
    image.setAttribute("preserveAspectRatio", "none");
    mask.append(image);
    this.defs.append(mask);
    const fill = document.createElementNS(SVG_NS, "rect");
    this._setBox(fill, b);
    fill.setAttribute("class", "object-masker");
    fill.setAttribute("mask", `url(#${maskId})`);
    group.prepend(fill);
  }

  _setBox(element, b) {
    element.setAttribute("x", b.x);
    element.setAttribute("y", b.y);
    element.setAttribute("width", b.w);
    element.setAttribute("height", b.h);
  }

  /* Pointer over an object in a list: it stands out on the page. */
  setObjectHover(id, on) {
    const group = this.objectElements.get(id);
    if (!group) return;
    if (on && group.object.masker) this._addMask(group, group.object);
    group.classList.toggle("hover", on);
    this.el.classList.toggle("object-aangewezen", on);
  }

  /* Zoom to a box (native pixels). */
  zoomToBox(b, fill = 0.6) {
    this.fitBox(b.x, b.y, b.w, b.h, fill);
  }

  /* Zoom to an object and mark it until another is marked. */
  focusObject(id, zoom = true) {
    this.objectLayer.querySelectorAll(".uitgelicht").forEach((g) => g.classList.remove("uitgelicht"));
    const group = this.objectElements.get(id);
    if (!group) return false;
    group.classList.add("uitgelicht");
    if (group.object.masker) this._addMask(group, group.object);
    if (zoom) this.zoomToBox(group.object.box);
    return true;
  }

  /* Point mode ("Aanwijzen"): a crosshair, and clicks on known objects also become points. */
  setPointMode(on) {
    this.pointMode = on;
    this.el.classList.toggle("aanwijzen", on);
  }

  /* Draw mode ("Rechthoek tekenen"): dragging draws a rectangle instead of panning. */
  setDrawMode(on) {
    this.drawMode = on;
    this.el.classList.toggle("tekenen", on);
  }

  /* Viewer coordinates of a pointer event, in native page pixels. */
  pagePoint(event) {
    const rect = this.el.getBoundingClientRect();
    return {
      x: Math.round((event.clientX - rect.left - this.tx) / this.scale),
      y: Math.round((event.clientY - rect.top - this.ty) / this.scale),
    };
  }

  _hoverObject(obj, event) {
    if (this.panning || this.drawing) return;
    this.hoverObject = obj;
    if (obj) {
      const info = this.describe(obj);
      this.tooltip.replaceChildren();
      const title = document.createElement("strong");
      title.textContent = info.title;
      this.tooltip.append(title, (info.details || []).filter(Boolean).join(" · "));
      if (info.text) {
        const block = document.createElement("span");
        block.className = "tooltip-beschrijving";
        block.textContent = info.text;
        this.tooltip.append(block);
      }
      if (info.hint) {
        const hint = document.createElement("small");
        hint.textContent = info.hint;
        this.tooltip.append(hint);
      }
      this.tooltip.hidden = false;
      this._moveTooltip(event);
    } else {
      this.tooltip.hidden = true;
    }
    this._emit("object-hover", obj);
  }

  fit() {
    if (!this.page) return;
    this.fitBox(0, 0, this.page.width, this.page.height, 0.96);
    this.userMoved = false;
  }

  fitBox(x, y, w, h, fill) {
    const vw = this.el.clientWidth || 800;
    const vh = this.el.clientHeight || 600;
    const s = Math.min((vw * fill) / Math.max(w, 1), (vh * fill) / Math.max(h, 1), MAX_SCALE);
    this.scale = s;
    this.tx = vw / 2 - (x + w / 2) * s;
    this.ty = vh / 2 - (y + h / 2) * s;
    this.userMoved = true;
    this._apply();
  }

  zoomStep(direction) {
    if (!this.page) return;
    const next = nextZoomStep(this.scale, direction);
    if (next) this.zoomBy(next / this.scale);
  }

  zoomTo(scale) {
    if (this.page) this.zoomBy(scale / this.scale);
  }

  zoomBy(factor, cx, cy) {
    if (!this.page) return;
    const rect = this.el.getBoundingClientRect();
    cx = cx === undefined ? rect.width / 2 : cx;
    cy = cy === undefined ? rect.height / 2 : cy;
    const minScale = Math.min(rect.width / this.page.width, rect.height / this.page.height) * 0.5 || 0.01;
    const next = Math.max(minScale, Math.min(MAX_SCALE, this.scale * factor));
    const k = next / this.scale;
    this.tx = cx - (cx - this.tx) * k;
    this.ty = cy - (cy - this.ty) * k;
    this.scale = next;
    this.userMoved = true;
    this._apply();
  }

  _apply() {
    this.stage.style.transform = `translate(${this.tx}px, ${this.ty}px) scale(${this.scale})`;
    this._maybeLoadLarge();
    this._scaleLabels();
    this._emit("zoom", this.scale);
  }

  /* Region names keep a readable size at every zoom level. */
  _scaleLabels() {
    this.svg.style.setProperty("--label-size", `${13 / this.scale}px`);
    this.svg.style.setProperty("--stroke", `${2 / this.scale}px`);
  }

  /* Swap in a sharper image once the page is shown larger than the loaded one. */
  _maybeLoadLarge() {
    const p = this.page;
    if (!p || this.largeLoaded || !p.srcLarge) return;
    if (this.scale * p.width <= p.srcWidth * 1.15) return;
    this.largeLoaded = true;
    const pre = new Image();
    pre.onload = () => {
      if (this.page === p) this.img.src = p.srcLarge;
    };
    pre.src = p.srcLarge;
  }

  _moveTooltip(event) {
    if (this.tooltip.hidden || !event) return;
    const rect = this.el.getBoundingClientRect();
    const x = Math.min(event.clientX - rect.left + 14, rect.width - this.tooltip.offsetWidth - 4);
    this.tooltip.style.left = Math.max(4, x) + "px";
    this.tooltip.style.top = event.clientY - rect.top + 16 + "px";
  }

  _drawRect(rect) {
    if (!this.rubber) {
      this.rubber = document.createElementNS(SVG_NS, "rect");
      this.rubber.setAttribute("class", "rechthoek-tekenen");
      this.drawLayer.append(this.rubber);
    }
    this._setBox(this.rubber, rect);
  }

  _bindEvents() {
    this.el.addEventListener(
      "wheel",
      (e) => {
        e.preventDefault();
        const rect = this.el.getBoundingClientRect();
        this.zoomBy(Math.exp(-e.deltaY * 0.0015), e.clientX - rect.left, e.clientY - rect.top);
      },
      { passive: false }
    );

    let start = null;
    this.el.addEventListener("pointerdown", (e) => {
      if (e.button !== 0 && e.button !== 1) return;
      start = {
        x: e.clientX,
        y: e.clientY,
        tx: this.tx,
        ty: this.ty,
        object: this.hoverObject,
        point: this.pagePoint(e),
        ctrl: e.ctrlKey || e.metaKey,
        shift: (e.shiftKey || this.drawMode) && e.button === 0,
      };
      this.el.setPointerCapture?.(e.pointerId);
    });
    this.el.addEventListener("pointermove", (e) => {
      if (!start) return;
      const dx = e.clientX - start.x;
      const dy = e.clientY - start.y;
      if (!this.panning && !this.drawing && Math.hypot(dx, dy) < DRAG_THRESHOLD) return;
      if (start.shift) {
        // Shift-drag: a manual rectangle (free).
        this.drawing = true;
        this.tooltip.hidden = true;
        this._drawRect(normaliseRect(start.point, this.pagePoint(e)));
        return;
      }
      if (!this.panning) {
        this.panning = true;
        this.tooltip.hidden = true;
        this.el.classList.add("pannen");
      }
      this.tx = start.tx + dx;
      this.ty = start.ty + dy;
      this.userMoved = true;
      this._apply();
    });
    const end = (e) => {
      if (!start) return;
      const wasPanning = this.panning;
      const wasDrawing = this.drawing;
      const click = start;
      start = null;
      this.panning = false;
      this.drawing = false;
      this.el.classList.remove("pannen");
      if (this.el.hasPointerCapture?.(e.pointerId)) this.el.releasePointerCapture(e.pointerId);
      if (wasDrawing) {
        const rect = normaliseRect(click.point, this.pagePoint(e));
        this.rubber?.remove();
        this.rubber = null;
        if (e.type !== "pointercancel" && rect.w >= 4 && rect.h >= 4) this._emit("rectangle", rect);
        return;
      }
      if (wasPanning || e.type === "pointercancel" || !this.page || this.drawMode) return;
      if (click.object && !this.pointMode) {
        this._emit("object-click", { object: click.object, ctrl: click.ctrl });
      } else {
        this._emit("point", { ...click.point, ctrl: click.ctrl });
      }
    };
    this.el.addEventListener("pointerup", end);
    this.el.addEventListener("pointercancel", end);
    // Double-click on an object: open it large (the magnifier).
    this.el.addEventListener("dblclick", () => {
      if (this.hoverObject && this.page) this._emit("object-open", this.hoverObject);
    });

    if (typeof ResizeObserver !== "undefined") {
      this.resizeObserver = new ResizeObserver(() => {
        if (this.page && !this.userMoved) this.fit();
      });
      this.resizeObserver.observe(this.el);
    }
  }

  /* When the viewer goes: stop watching the size of its element. */
  destroy() {
    this.resizeObserver?.disconnect();
    this.resizeObserver = null;
  }
}
