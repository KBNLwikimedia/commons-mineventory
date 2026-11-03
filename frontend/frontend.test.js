import { describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import en from "./i18n/en.json";
import nl from "./i18n/nl.json";
import { ApiError, errorText, objectPath, query, request } from "./api.js";
import { readConfig } from "./config.js";
import { createI18n, money, translate } from "./i18n.js";
import { appUrl, objectName, readStart } from "./state.js";
import { nextZoomStep, normaliseRect, PageViewer, ZOOM_STEPS } from "./viewer/viewer.js";
import ObjectList from "./components/ObjectList.vue";

describe("translation files", () => {
  it("have the same keys in Dutch and English", () => {
    expect(Object.keys(nl).sort()).toEqual(Object.keys(en).sort());
  });

  it("have no empty texts", () => {
    for (const messages of [nl, en]) {
      for (const [key, text] of Object.entries(messages)) expect(text.trim(), key).not.toBe("");
    }
  });

  it("use the same placeholders in both languages", () => {
    const names = (text) => [...text.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort();
    for (const key of Object.keys(nl)) expect(names(en[key]), key).toEqual(names(nl[key]));
  });
});

describe("i18n", () => {
  it("fills placeholders and falls back to the key", () => {
    expect(translate({ hi: "Hallo {name}" }, "hi", { name: "Olaf" })).toBe("Hallo Olaf");
    expect(translate({}, "missing.key")).toBe("missing.key");
    expect(translate({ a: "{x} en {y}" }, "a", { x: 1 })).toBe("1 en {y}");
  });

  it("provides $t to components", () => {
    const i18n = createI18n({ x: "y" }, "nl");
    expect(i18n.t("x")).toBe("y");
    expect(i18n.language).toBe("nl");
  });

  it("formats dollars per language", () => {
    expect(money(0.0025, "en")).toBe("$0.0025");
    expect(money(2, "nl")).toMatch(/2,00/);
  });
});

describe("api", () => {
  it("builds paths and query strings", () => {
    expect(objectPath("M1", 2, "obj-a b")).toBe("/api/v1/bestand/M1/pagina/2/object/obj-a%20b");
    expect(query({ a: 1, b: "", c: null, d: "x y" })).toBe("?a=1&d=x+y");
    expect(query({})).toBe("");
  });

  it("sends JSON and turns errors into ApiError with the code", async () => {
    const fetchImpl = vi.fn(async () => ({ ok: false, status: 429, json: async () => ({ fout: "Daglimiet bereikt", code: "daily_limit" }) }));
    const error = await request("POST", "/api/v1/x", { a: 1 }, { fetchImpl }).catch((e) => e);
    expect(error).toBeInstanceOf(ApiError);
    expect(error.code).toBe("daily_limit");
    expect(fetchImpl.mock.calls[0][1].body).toBe('{"a":1}');
    expect(fetchImpl.mock.calls[0][1].headers["Content-Type"]).toBe("application/json");
  });

  it("translates a known error code, else shows the API's message", () => {
    const t = (key) => ({ "error.daily_limit": "Daily limit reached." })[key] ?? key;
    expect(errorText(t, new ApiError(429, { fout: "x", code: "daily_limit" }))).toBe("Daily limit reached.");
    expect(errorText(t, new ApiError(500, { fout: "Iets anders", code: "weird" }))).toBe("Iets anders");
  });
});

describe("page state in the URL", () => {
  it("reads and writes the start parameters", () => {
    expect(readStart("?mid=M5&pagina=2&object=obj-1")).toMatchObject({ mid: "M5", pagina: "2", object: "obj-1", url: "" });
    expect(appUrl("M5")).toBe("/?mid=M5");
    expect(appUrl("M5", 3, "obj-1")).toBe("/?mid=M5&pagina=3&object=obj-1");
  });

  it("names objects by language, preferring the description", () => {
    const obj = { label: "coat of arms", label_nl: "wapen", beschrijving: { onderwerp: "wapen van X", onderwerp_en: "Arms of X" } };
    expect(objectName(obj, "nl")).toBe("wapen van X");
    expect(objectName(obj, "en")).toBe("Arms of X");
    expect(objectName({ label: "Catharina", label_en: "Catherine" }, "en")).toBe("Catherine");
    expect(objectName({ label: "person", label_nl: "persoon", bijschrift: { tekst: "Man met pijp" } }, "nl")).toBe("Man met pijp");
    // The app's own labels follow the interface language.
    const t = (key) => translate(en, key);
    expect(objectName({ label: "rechthoek" }, "en", t)).toBe("rectangle");
    expect(objectName({ label: "klik" }, "en", t)).toBe("pointed-out object");
  });

  it("reads the embedded configuration", () => {
    document.body.innerHTML = '<script id="cutter-config" type="application/json">{"taal": "nl", "teksten": {"a": "b"}}</script>';
    expect(readConfig()).toEqual({ taal: "nl", teksten: { a: "b" } });
  });
});

describe("viewer helpers", () => {
  it("steps through the fixed zoom levels and reaches 100%", () => {
    expect(nextZoomStep(0.9, 1)).toBe(1);
    expect(nextZoomStep(1, -1)).toBe(0.75);
    expect(nextZoomStep(3, 1)).toBeNull();
    expect(ZOOM_STEPS).toContain(1);
  });

  it("normalises a dragged rectangle in any direction", () => {
    expect(normaliseRect({ x: 50, y: 80 }, { x: 10, y: 20 })).toEqual({ x: 10, y: 20, w: 40, h: 60 });
  });
});

function viewerWithPage() {
  const host = document.createElement("div");
  document.body.append(host);
  const viewer = new PageViewer(host);
  viewer.load({ width: 1000, height: 800, src: "data:,", srcWidth: 1000 });
  return { host, viewer };
}

const objects = [
  { id: "a", label: "wapen", status: "geselecteerd", bron: "dummy", box: { x: 10, y: 10, w: 100, h: 100 }, masker: { breedte: 4 }, masker_url: "/m.png" },
  { id: "b", label: "Catharina", status: "kandidaat", bron: "commons", box: { x: 300, y: 300, w: 50, h: 50 }, masker: null },
];

describe("PageViewer", () => {
  it("draws objects with classes per status and source, and region names", () => {
    const { host, viewer } = viewerWithPage();
    viewer.setObjects(objects, ["b"]);
    const groups = host.querySelectorAll("g.object");
    expect(groups).toHaveLength(2);
    expect(groups[0].getAttribute("class")).toContain("object-geselecteerd");
    expect(groups[0].querySelector(".object-masker")).not.toBeNull();
    expect(groups[1].getAttribute("class")).toContain("object-commons");
    expect(groups[1].getAttribute("class")).toContain("object-nieuw");
    expect(groups[1].querySelector("text").textContent).toBe("Catharina");
  });

  it("changes the selection without rebuilding", () => {
    const { host, viewer } = viewerWithPage();
    viewer.setObjects(objects);
    const before = host.querySelector('g[data-id="b"]');
    viewer.setSelection(["b"]);
    expect(host.querySelector('g[data-id="b"]')).toBe(before);
    expect(before.getAttribute("class")).toContain("object-geselecteerd");
    expect(host.querySelector('g[data-id="a"]').getAttribute("class")).toContain("object-kandidaat");
  });

  it("emits events and can unsubscribe", () => {
    const { viewer } = viewerWithPage();
    const seen = [];
    const off = viewer.on("rectangle", (r) => seen.push(r));
    viewer._emit("rectangle", { x: 1, y: 2, w: 3, h: 4 });
    off();
    viewer._emit("rectangle", { x: 0, y: 0, w: 9, h: 9 });
    expect(seen).toEqual([{ x: 1, y: 2, w: 3, h: 4 }]);
  });

  it("switches point mode", () => {
    const { host, viewer } = viewerWithPage();
    viewer.setPointMode(true);
    expect(host.classList.contains("aanwijzen")).toBe(true);
    expect(viewer.focusObject("unknown")).toBe(false);
  });
});

describe("ObjectList component", () => {
  it("lists regions from Commons first and emits the toggle", async () => {
    const wrapper = mount(ObjectList, {
      props: { mid: "M1", n: 1, objects: structuredClone(objects).map((o) => ({ ...o, status: o.id === "a" ? "geselecteerd" : "kandidaat" })) },
      global: { provide: { t: (key) => key, language: "nl" } },
    });
    const names = wrapper.findAll(".cc-object-naam").map((n) => n.text());
    expect(names).toEqual(["Catharina", "wapen"]);
    expect(wrapper.find(".cc-object-duim img").attributes("src")).toContain("/object/b/uitsnede.jpg?w=96");
    await wrapper.findAll('input[type="checkbox"]')[0].setValue(true);
    expect(wrapper.emitted("toggle")[0]).toEqual(["b"]);
  });
});

describe("confirmation dialog", () => {
  it("resolves with the answer, and a newer question cancels an open one", async () => {
    const { askConfirm, answerConfirm, confirmState } = await import("./confirm.js");
    const first = askConfirm("Eerste?");
    const second = askConfirm("Tweede?", { destructive: true });
    expect(await first).toBe(false);
    expect(confirmState).toMatchObject({ open: true, text: "Tweede?", destructive: true });
    answerConfirm(true);
    expect(await second).toBe(true);
    expect(confirmState.open).toBe(false);
  });
});

describe("moving and resizing the magnifier", async () => {
  const { makeMovable, moveRect, resizeRect } = await import("./movable.js");
  const rect = { left: 100, top: 100, width: 500, height: 400 };
  const viewport = { width: 1200, height: 800 };

  it("resizes from each edge, with a minimum and within the screen", () => {
    expect(resizeRect(rect, "e", 50, 0)).toEqual({ ...rect, width: 550 });
    expect(resizeRect(rect, "sw", -40, 30)).toEqual({ left: 60, top: 100, width: 540, height: 430 });
    expect(resizeRect(rect, "n", 0, 350, { width: 320, height: 200 })).toEqual({ left: 100, top: 300, width: 500, height: 200 });
    expect(resizeRect(rect, "w", -500, 0)).toEqual({ left: 0, top: 100, width: 600, height: 400 });
    expect(resizeRect(rect, "se", 2000, 2000, undefined, viewport)).toEqual({ left: 100, top: 100, width: 1100, height: 700 });
  });

  it("moves, but keeps the whole dialog on screen", () => {
    expect(moveRect(rect, 20, -30, viewport)).toEqual({ ...rect, left: 120, top: 70 });
    expect(moveRect(rect, 5000, 5000, viewport)).toEqual({ ...rect, left: 700, top: 400 });
    expect(moveRect(rect, 0, -500, viewport).top).toBe(0);
  });

  it("adds edge grips and removes them again", () => {
    const dialog = document.createElement("div");
    const header = document.createElement("header");
    dialog.append(header);
    document.body.append(dialog);
    const undo = makeMovable(dialog, { handle: header });
    expect(dialog.querySelectorAll(".cc-rand")).toHaveLength(8);
    expect(header.classList.contains("cc-sleepgreep")).toBe(true);
    undo();
    expect(dialog.querySelectorAll(".cc-rand")).toHaveLength(0);
  });
});

describe("history of opened files", async () => {
  const { addToHistory, clearHistory, lastFileUrl, readHistory, removeFromHistory, MAX_HISTORY } = await import("./state.js");
  const memory = () => {
    const data = {};
    return { getItem: (k) => data[k] ?? null, setItem: (k, v) => (data[k] = String(v)) };
  };

  it("keeps files newest first, once each, with the page", () => {
    const store = memory();
    addToHistory({ mid: "M1", naam: "a.jpg", pagina: 1 }, store);
    addToHistory({ mid: "M2", naam: "b.pdf", pagina: 3 }, store);
    addToHistory({ mid: "M1", naam: "a.jpg", pagina: 1 }, store);
    expect(readHistory(store).map((e) => e.mid)).toEqual(["M1", "M2"]);
    expect(lastFileUrl(store)).toBe("/?mid=M1");
    removeFromHistory("M1", store);
    expect(lastFileUrl(store)).toBe("/?mid=M2&pagina=3");
    clearHistory(store);
    expect(readHistory(store)).toEqual([]);
    expect(lastFileUrl(store)).toBeNull();
  });

  it("is capped and survives broken or missing storage", () => {
    const store = memory();
    for (let i = 0; i < MAX_HISTORY + 5; i++) addToHistory({ mid: `M${i}`, naam: "x", pagina: 1 }, store);
    expect(readHistory(store)).toHaveLength(MAX_HISTORY);
    store.setItem("cc-geschiedenis", "{kapot");
    expect(readHistory(store)).toEqual([]);
    expect(readHistory(null)).toEqual([]);
    expect(addToHistory({ mid: "M9" }, null)).toHaveLength(1);
  });
});

describe("draw mode", () => {
  it("lets a plain drag draw a rectangle and shows a crosshair", () => {
    const { host, viewer } = viewerWithPage();
    viewer.setDrawMode(true);
    expect(host.classList.contains("tekenen")).toBe(true);
    expect(viewer.drawMode).toBe(true);
    viewer.setDrawMode(false);
    expect(host.classList.contains("tekenen")).toBe(false);
  });
});

describe("links in a confirmation", async () => {
  const { textParts } = await import("./confirm.js");
  it("turns named placeholders into links and leaves the rest as text", () => {
    const parts = textParts("Op de {objects}, tabblad {trash}; {onbekend} blijft.", {
      objects: { href: "/objecten", label: "pagina Objecten" },
      trash: { href: "/objecten?tab=prullenbak", label: "Prullenbak" },
    });
    expect(parts).toEqual([
      { text: "Op de " },
      { link: { href: "/objecten", label: "pagina Objecten" } },
      { text: ", tabblad " },
      { link: { href: "/objecten?tab=prullenbak", label: "Prullenbak" } },
      { text: "; " },
      { text: "{onbekend}" },
      { text: " blijft." },
    ]);
  });
});

describe("ConceptEditor component", () => {
  it("opens, takes over the caption and can undo it", async () => {
    const { default: ConceptEditor } = await import("./components/ConceptEditor.vue");
    const { flushPromises } = await import("@vue/test-utils");
    const draft = {
      bestandsnaam: "Detail – extracted from X.jpg", formaat: "jpg", caption: { nl: "rechthoek", en: "" },
      beschrijving: { nl: "", en: "" }, datum: "", maker: "", categorieen: [], beeldt_af: [], image_extracted: true,
      merk_bevestigd: null, rechten: { labels: ["in_orde"] }, upload_toegestaan: true, wikitekst: "", sdc: {},
      samenvatting: "", herkomst: {}, bijschrift: "Man met pijp", ai: null,
    };
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: true, status: 200, json: async () => draft })));
    const wrapper = mount(ConceptEditor, {
      props: { mid: "M1", n: 1, objectId: "obj-1" },
      global: { provide: { t: (key) => key, language: "nl" } },
    });
    await flushPromises();
    const take = wrapper.findAll("button.cc-link").find((b) => b.text() === "concept.use_caption");
    expect(take).toBeTruthy();
    await take.trigger("click");
    expect(wrapper.find("input").element.value).not.toBe("");
    const undo = wrapper.findAll("button.cc-link").find((b) => b.text().includes("magnifier.undo"));
    expect(undo).toBeTruthy();
    await undo.trigger("click");
    vi.unstubAllGlobals();
  });
});

describe("column splitter", () => {
  it("changes the column width with the arrow keys, within limits, and remembers it", async () => {
    const { default: ColumnSplitter } = await import("./components/ColumnSplitter.vue");
    const area = document.createElement("div");
    area.className = "cc-werkblad";
    area.appendChild(document.createElement("aside"));
    const host = document.createElement("div");
    area.appendChild(host);
    document.body.appendChild(area);
    window.localStorage.removeItem("test-breedte");
    const wrapper = mount(ColumnSplitter, {
      attachTo: host,
      props: { variable: "--test-breedte", side: "left", storageKey: "test-breedte", label: "Breedte", min: 100, max: 300 },
    });
    await wrapper.trigger("keydown", { key: "ArrowRight", shiftKey: true });
    expect(area.style.getPropertyValue("--test-breedte")).toBe("164px");
    expect(window.localStorage.getItem("test-breedte")).toBe("164");
    for (let i = 0; i < 10; i++) await wrapper.trigger("keydown", { key: "ArrowRight", shiftKey: true });
    expect(area.style.getPropertyValue("--test-breedte")).toBe("300px");
    await wrapper.trigger("dblclick");
    expect(area.style.getPropertyValue("--test-breedte")).toBe("");
    expect(window.localStorage.getItem("test-breedte")).toBeNull();
    wrapper.unmount();
    area.remove();
  });
});
