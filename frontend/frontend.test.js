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
import TickLinks from "./components/TickLinks.vue";
import { invertedIn, toggledIn } from "./storage.js";
import ChangelogFacets from "./components/ChangelogFacets.vue";
import ListFacets from "./components/ListFacets.vue";
import ObjectsTable from "./components/ObjectsTable.vue";
import AlsoFoundAs from "./components/AlsoFoundAs.vue";
import SortableTable from "./components/SortableTable.vue";
import { applyFacets, applyListFilters, emptyFilters, exportUrl, facetOptions, newestFirst, objectsWithTerm, readAddress, sortRows, writeAddress } from "./facets.js";
import { QUERY_COLOUR, classColors, classKey, classKeys, kindsWithQuery } from "./class-colors.js";

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
    expect(objectPath("M1", 2, "obj-a b")).toBe("/api/v1/bestand/M1/pagina/2/objecten/obj-a%20b");
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

  it("in English translates the error code (never the Dutch message); in Dutch shows the API's own message", () => {
    const en = (key) => ({ "meta.language": "en", "error.daily_limit": "Daily limit reached.", "error.error": "Something went wrong." })[key] ?? key;
    expect(errorText(en, new ApiError(429, { fout: "x", code: "daily_limit" }))).toBe("Daily limit reached.");
    expect(errorText(en, new ApiError(500, { fout: "Iets anders", code: "weird" }))).toBe("Something went wrong.");
    const nl = (key) => ({ "meta.language": "nl", "error.daily_limit": "Daglimiet bereikt.", "error.error": "Er ging iets mis." })[key] ?? key;
    expect(errorText(nl, new ApiError(429, { fout: "De daglimiet is bereikt; nog 3 uur.", code: "daily_limit" }))).toBe("De daglimiet is bereikt; nog 3 uur.");
    expect(errorText(nl, new ApiError(500, null))).toBe("Er ging iets mis.");
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

  it("fades the other objects only while one is really under the mouse", () => {
    const { host, viewer } = viewerWithPage();
    viewer.setObjects(objects);
    viewer.setObjectHover("a", true);
    expect(host.classList.contains("object-aangewezen")).toBe(true);
    // The object under the mouse is gone after a redraw: nothing may stay faded.
    viewer.setObjects(objects.filter((o) => o.id !== "a"));
    expect(host.classList.contains("object-aangewezen")).toBe(false);
    // Leaving an object that no longer exists clears it too.
    viewer.setObjects(objects);
    viewer.setObjectHover("a", true);
    viewer.setObjects(objects.filter((o) => o.id !== "a"));
    viewer.setObjectHover("a", false);
    expect(host.classList.contains("object-aangewezen")).toBe(false);
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

  it("keeps the hover and highlight marks when the selection changes", () => {
    const { host, viewer } = viewerWithPage();
    viewer.setObjects(objects);
    viewer.setObjectHover("a", true);
    viewer.focusObject("a", false);
    viewer.setSelection([]);
    viewer.setSelection(["a"]);
    const group = host.querySelector('g[data-id="a"]');
    expect(group.classList.contains("hover")).toBe(true);
    expect(group.classList.contains("uitgelicht")).toBe(true);
    expect(group.classList.contains("object-geselecteerd")).toBe(true);
  });

  it("keeps the hover mark when the objects are drawn again", () => {
    const { host, viewer } = viewerWithPage();
    viewer.setObjects(objects);
    viewer.setObjectHover("a", true);
    viewer.setObjects(objects);
    expect(host.querySelector('g[data-id="a"]').classList.contains("hover")).toBe(true);
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
  it("lists objects alphabetically, numbers equal names, and emits the toggle", async () => {
    const wrapper = mount(ObjectList, {
      props: { mid: "M1", n: 1, objects: structuredClone(objects).map((o) => ({ ...o, status: o.id === "a" ? "geselecteerd" : "kandidaat" })) },
      global: { provide: { t: (key) => key, language: "nl" } },
    });
    const names = wrapper.findAll(".cc-object-naam").map((n) => n.text());
    expect(names).toEqual(["Catharina", "wapen"]);
    const twice = [...objects, { id: "c", label: "wapen", status: "kandidaat", bron: "dummy", box: { x: 0, y: 500, w: 10, h: 10 }, masker: null }];
    const numbered = mount(ObjectList, { props: { mid: "M1", n: 1, objects: twice }, global: { provide: { t: (key) => key, language: "nl" } } });
    expect(numbered.findAll(".cc-object-naam").map((n) => n.text())).toEqual(["Catharina", "wapen 1", "wapen 2"]);
    expect(wrapper.find(".cc-object-duim img").attributes("src")).toContain("/objecten/b/uitsnede.jpg?w=96");
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
  const { addToHistory, clearHistory, lastFileUrl, readHistory, removeFromHistory, setAside, MAX_HISTORY } = await import("./state.js");
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

  it("writes a list back for Undo: valid entries once each, capped", async () => {
    const { restoreHistory } = await import("./state.js");
    const store = memory();
    addToHistory({ mid: "M1", naam: "a.jpg", pagina: 2 }, store);
    const before = readHistory(store);
    clearHistory(store);
    expect(restoreHistory(before, store)).toEqual(before);
    expect(readHistory(store)).toEqual(before);
    const messy = [{ mid: "M2" }, { mid: "kapot" }, null, { mid: "M2" }, { mid: "M3" }];
    expect(restoreHistory(messy, store).map((e) => e.mid)).toEqual(["M2", "M3"]);
    const many = Array.from({ length: MAX_HISTORY + 3 }, (_, i) => ({ mid: `M${i}` }));
    expect(restoreHistory(many, store)).toHaveLength(MAX_HISTORY);
    expect(restoreHistory("geen lijst", store)).toEqual([]);
  });

  it("puts back the versions an Undo needs (undo.js)", async () => {
    const { descriptionVersion, pageDescriptionVersion } = await import("./undo.js");
    expect(descriptionVersion({ tijdstempel: "t1" })).toBe("t1");
    expect(descriptionVersion({ tijdstempel: "t1", bewerkt_op: "b1" })).toBe("b1");
    expect(descriptionVersion(null)).toBe("");
    expect(pageDescriptionVersion({ samenvatting: "x", tijdstempel: "t0", delen: { beschrijving: { tijdstempel: "t2" } } })).toBe("t2");
    expect(pageDescriptionVersion({ samenvatting: "x", tijdstempel: "t0", bewerkt_op: "b2" })).toBe("b2");
    expect(pageDescriptionVersion({ zoektermen: [{ nl: "hoed" }], tijdstempel: "t0" })).toBe("");
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

  it("sets an entry aside and back; opening it again brings it back too", () => {
    const store = memory();
    addToHistory({ mid: "M1", naam: "a.jpg", pagina: 1 }, store);
    addToHistory({ mid: "M2", naam: "b.jpg", pagina: 1 }, store);
    setAside("M1", true, store);
    expect(readHistory(store).find((e) => e.mid === "M1").opzij).toBe(true);
    setAside("M1", false, store);
    expect(readHistory(store).find((e) => e.mid === "M1").opzij).toBeUndefined();
    setAside("M2", true, store);
    addToHistory({ mid: "M2", naam: "b.jpg", pagina: 1 }, store);
    expect(readHistory(store)[0]).toMatchObject({ mid: "M2" });
    expect(readHistory(store)[0].opzij).toBeUndefined();
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
  it("edits a row in its own window: takes over the caption, can undo it, and saves", async () => {
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
      global: { provide: { t: (key) => key, language: "nl" }, stubs: { teleport: true } },
    });
    await flushPromises();
    // The pencil of the caption row opens a window with the caption fields.
    wrapper.vm.openEdit("caption");
    await wrapper.vm.$nextTick();
    const field = () => wrapper.find(".cc-veld-dialoog input");
    expect(field().element.value).toBe("rechthoek");
    // Its menu offers the caption; choosing it fills the field.
    const menu = wrapper.findComponent({ name: "CdxMenuButton" });
    expect(menu.props("menuItems").map((item) => item.value)).toEqual(["caption"]);
    menu.vm.$emit("update:selected", "caption");
    await wrapper.vm.$nextTick();
    expect(field().element.value).toBe("Man met pijp");
    const undo = wrapper.findAll("button.cc-link").find((b) => b.text().includes("magnifier.undo"));
    expect(undo).toBeTruthy();
    await undo.trigger("click");
    expect(field().element.value).toBe("rechthoek");
    // Opslaan sends the edited caption.
    wrapper.findComponent({ name: "CdxMenuButton" }).vm.$emit("update:selected", "caption");
    await wrapper.vm.$nextTick();
    expect(field().element.value).toBe("Man met pijp");
    wrapper.findComponent({ name: "CdxDialog" }).vm.$emit("primary");
    await flushPromises();
    const sent = fetch.mock.calls.map(([, options]) => options?.body).filter(Boolean).map((body) => JSON.parse(body));
    expect(sent.at(-1).caption.nl).toBe("Man met pijp");
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

describe("SdcPreview component", () => {
  it("shows captions, depicts first with labels, dates and unknown values", async () => {
    const { default: SdcPreview } = await import("./components/SdcPreview.vue");
    const item = (prop, id) => ({ snaktype: "value", property: prop, datavalue: { type: "wikibase-entityid", value: { id } } });
    const sdc = {
      labels: { nl: { language: "nl", value: "Man met pijp" } },
      claims: [
        { mainsnak: item("P6216", "Q19652") },
        { mainsnak: { snaktype: "value", property: "P571", datavalue: { type: "time", value: { time: "+1920-00-00T00:00:00Z", precision: 8 } } } },
        { mainsnak: item("P180", "Q1420") },
        { mainsnak: { snaktype: "somevalue", property: "P170" } },
      ],
    };
    const labels = { P180: { en: "depicts" }, Q1420: { nl: "auto", en: "car" }, P6216: { en: "copyright status" } };
    const wrapper = mount(SdcPreview, { props: { sdc, labels }, global: { provide: { t: (key, p) => (p ? `${key}:${Object.values(p)}` : key), language: "nl" } } });
    const heads = wrapper.findAll(".cc-sdc-kop").map((h) => h.text());
    expect(heads[0]).toBe("sdc.captions");
    expect(heads[1]).toContain("sdc.depicts_title");
    expect(wrapper.text()).toContain("Man met pijp");
    expect(wrapper.text()).toContain("auto");
    expect(wrapper.text()).toContain("sdc.decade:1920");
    expect(wrapper.text()).toContain("sdc.unknown_value");
    expect(wrapper.text()).toContain("P571");
  });
});

describe("collapsible boxes", () => {
  it("closes a collapsed table to its first row and opens it again", async () => {
    const { makeCollapsible } = await import("./collapsible.js");
    const box = document.createElement("div");
    box.innerHTML = '<table class="toccolours collapsible collapsed"><tr><th>KB</th></tr><tr><td>Den Haag</td></tr></table><table class="wikitable"><tr><td>a</td></tr><tr><td>b</td></tr></table>';
    makeCollapsible(box, { open: "Show", close: "Hide" });
    const [first, other] = box.querySelectorAll("table");
    expect(first.rows[1].hidden).toBe(true);
    expect(other.rows[1].hidden).toBe(false);
    const button = first.querySelector("button");
    expect(button.textContent).toContain("Show");
    button.click();
    expect(first.rows[1].hidden).toBe(false);
    expect(button.getAttribute("aria-expanded")).toBe("true");
  });
});

describe("SdcPreview quantities", () => {
  it("shows an amount with its unit label", async () => {
    const { default: SdcPreview } = await import("./components/SdcPreview.vue");
    const sdc = { labels: {}, claims: [{ mainsnak: { snaktype: "value", property: "P3575", datavalue: { type: "quantity", value: { amount: "+5775624", unit: "http://www.wikidata.org/entity/Q8799" } } } }] };
    const wrapper = mount(SdcPreview, { props: { sdc, labels: { Q8799: { en: "byte" } } }, global: { provide: { t: (k) => k, language: "en" } } });
    expect(wrapper.text()).toContain("5,775,624 byte");
  });
});

describe("smooth accordions", () => {
  it("holds a closing fold back, announces it, then closes", async () => {
    const { smoothAccordions } = await import("./accordion-motion.js");
    document.body.innerHTML = '<details class="cdx-accordion" open><summary>Title</summary><div class="cdx-accordion__content">Content</div></details>';
    smoothAccordions();
    const details = document.querySelector("details");
    let announced = false;
    details.addEventListener("cc-closing", () => (announced = true));
    // jsdom has no Element.animate, so the fold finishes at once.
    const click = new MouseEvent("click", { bubbles: true, cancelable: true });
    details.querySelector("summary").dispatchEvent(click);
    expect(click.defaultPrevented).toBe(true);
    expect(announced).toBe(true);
    expect(details.open).toBe(false);
    document.body.innerHTML = "";
  });
});

describe("cropToolLink", () => {
  it("opens CropTool on the whole file, only for single images", async () => {
    const { cropToolLink } = await import("./state.js");
    const file = { naam: "A b.jpg", titel: "File:A b.jpg", paginas: 1, mime: "image/jpeg" };
    expect(cropToolLink(file)).toBe("https://croptool2.toolforge.org/?title=A+b.jpg");
    expect(cropToolLink({ ...file, paginas: 3 })).toBeNull();
    expect(cropToolLink({ ...file, mime: "application/pdf" })).toBeNull();
  });
});

describe("savedLabel", () => {
  it("says how many days a saved cut-out has left, and warns in the last week", async () => {
    const { savedLabel } = await import("./state.js");
    const t = (key, vars = {}) => `${key}:${Object.values(vars).join(",")}`;
    const now = Date.parse("2026-11-04T12:00:00Z");
    expect(savedLabel({}, t)).toBeNull();
    expect(savedLabel({ opgeslagen: { jpg: "a.jpg" } }, t)).toMatchObject({ text: "objects.saved:" });
    const later = savedLabel({ opgeslagen: { verloopt: "2026-11-27T12:00:00Z" } }, t, "nl", now);
    expect(later).toMatchObject({ text: "objects.saved:", left: "objects.saved_days:23" });
    expect(later.soon).toBe(false);
    expect(later.title).toContain("27 november 2026");
    expect(savedLabel({ opgeslagen: { verloopt: "2026-11-05T10:00:00Z" } }, t, "nl", now)).toMatchObject({ left: "objects.saved_one_day:", soon: true });
  });
});

describe("numbered names", async () => {
  const { numberedNames } = await import("./state.js");
  it("numbers names that occur more than once, in reading order, the same for list and image", () => {
    const box = (x, y) => ({ x, y, w: 10, h: 10 });
    const objects = [
      { id: "a", label: "man", box: box(50, 10) },
      { id: "b", label: "horse", box: box(0, 0) },
      { id: "c", label: "man", box: box(0, 5) },
    ];
    expect(numberedNames(objects, "en")).toEqual({ c: "man 1", a: "man 2", b: "horse" });
  });
});

describe("confirmation that may be switched off", async () => {
  const { askConfirm, answerConfirm, confirmState } = await import("./confirm.js");
  const memory = () => {
    const data = {};
    return { getItem: (k) => data[k] ?? null, setItem: (k, v) => (data[k] = String(v)) };
  };
  it("asks until a yes with the box ticked, then answers yes at once", async () => {
    const store = memory();
    let answer = askConfirm("x", { dontAsk: "trash", store });
    expect(confirmState.open && confirmState.dontAsk).toBe("trash");
    answerConfirm(true); // yes, box not ticked: ask again next time
    expect(await answer).toBe(true);
    answer = askConfirm("x", { dontAsk: "trash", store });
    expect(confirmState.open).toBe(true);
    confirmState.dontAskChecked = true;
    answerConfirm(false); // cancelled with the box ticked: still ask
    expect(await answer).toBe(false);
    answer = askConfirm("x", { dontAsk: "trash", store });
    confirmState.dontAskChecked = true;
    answerConfirm(true);
    expect(await answer).toBe(true);
    confirmState.open = false;
    expect(await askConfirm("x", { dontAsk: "trash", store })).toBe(true);
    expect(confirmState.open).toBe(false); // not asked
  });
});

describe("facets and search on the list pages", () => {
  const rows = [
    { values: { soort: "Toegevoegd", reeks: "0.9" }, text: "0.9.1 new tick box" },
    { values: { soort: "Opgelost", reeks: "0.33" }, text: "0.33.2 tick fixed" },
    { values: { soort: "Toegevoegd", reeks: "0.33" }, text: "0.33.1 facets" },
    { values: { soort: "Toegevoegd", reeks: "" }, text: "unreleased work" },
  ];

  it("combines facets and every word of the search", () => {
    const none = { soort: [], reeks: [] };
    expect(applyListFilters(rows, none, "")).toHaveLength(4);
    expect(applyListFilters(rows, none, " TICK  box".toLowerCase())).toEqual([rows[0]]);
    expect(applyListFilters(rows, { soort: ["Toegevoegd"], reeks: ["0.33", "0.9"] })).toEqual([rows[0], rows[2]]);
    expect(applyListFilters(rows, { soort: ["Opgelost"], reeks: [] }, "facets")).toEqual([]);
  });

  it("searches the objects on the Objects page together with the facets", () => {
    const doll = { id: "a", bron: "sam", mid: "M1", bestand_titel: "File:Album.jpg", zoekterm: "person", beschrijving: { onderwerp: "Pop in groene jurk", onderwerp_en: "Doll in green dress" } };
    const group = { id: "b", bron: "groep", mid: "M2", groep: { naam: "Family" }, bijschrift: { tekst: "Op het strand" } };
    const search = (query, extra = {}) => applyFacets([doll, group], { ...emptyFilters(), query, ...extra }).map((o) => o.id);
    expect(search("")).toEqual(["a", "b"]);
    expect(search("DOLL green")).toEqual(["a"]);
    expect(search("doll red")).toEqual([]);
    expect(search("family")).toEqual(["b"]);
    expect(search("strand")).toEqual(["b"]);
    expect(search("album")).toEqual(["a"]);
    expect(search("doll", { sources: ["groep"] })).toEqual([]);
  });

  it("sorts numbers, versions and yes/no, with empty values last", () => {
    const by = (values, direction) => sortRows(values.map((v) => ({ v })), (r) => r.v, direction).map((r) => r.v);
    expect(by([0.01, 0.0025, null, 0.5], 1)).toEqual([0.0025, 0.01, 0.5, null]);
    expect(by([0.01, 0.0025, null, 0.5], -1)).toEqual([0.5, 0.01, 0.0025, null]);
    expect(by(["0.33.1", "", "0.9.2"], 1)).toEqual(["0.9.2", "0.33.1", ""]);
    expect(by([true, false, true], 1)).toEqual([false, true, true]);
  });

  it("starts sorted as the address says and reports a new sorting for the address", async () => {
    const columns = [{ key: "a", label: "A", value: (r) => r.a }];
    const rows = [{ a: "2" }, { a: "10" }, { a: "1" }];
    const wrapper = mount(SortableTable, { props: { columns, rows, sort: "-a" }, global: { provide: { t: (key) => key } } });
    expect(wrapper.findAll("tbody tr").map((tr) => tr.text())).toEqual(["10", "2", "1"]);
    await wrapper.find("th button").trigger("click");
    expect(wrapper.emitted("update:sort").at(-1)).toEqual(["a"]);
  });

  it("sorts a table with a click on a heading, and only columns with a value", async () => {
    const columns = [{ key: "a", label: "A", value: (r) => r.a }, { key: "b", label: "B" }];
    const rows = [{ a: "2" }, { a: "10" }, { a: "1" }];
    const wrapper = mount(SortableTable, { props: { columns, rows }, global: { provide: { t: (key) => key, language: "nl" } } });
    const first = () => wrapper.findAll("tbody tr").map((tr) => tr.find("td").text());
    expect(first()).toEqual(["2", "10", "1"]); // as they came, until you click
    expect(wrapper.findAll("th button")).toHaveLength(1);
    await wrapper.find("th button").trigger("click");
    expect(first()).toEqual(["1", "2", "10"]);
    expect(wrapper.find("th").attributes("aria-sort")).toBe("ascending");
    await wrapper.find("th button").trigger("click");
    expect(first()).toEqual(["10", "2", "1"]);
    expect(wrapper.emitted("sorted").at(-1)[0][0]).toEqual({ a: "10" });
  });

  it("shows each word an object was also found with once, with a ×, without clicks and rectangles", () => {
    const object = { id: "a", ook: [{ id: "x", zoekterm: "boy" }, { id: "y", zoekterm: "child" }, { id: "z", zoekterm: "boy" }, { id: "k", zoekterm: "klik" }] };
    const wrapper = mount(AlsoFoundAs, { props: { object, mid: "M1", n: 1 }, global: { provide: { t: (key) => key, language: "nl" } } });
    expect(wrapper.findAll(".cc-ook-woord").map((w) => w.text().replace("×", "").trim())).toEqual(["boy", "child"]);
    expect(wrapper.findAll(".cc-ook-weg")).toHaveLength(2);
    expect(wrapper.text()).toContain("objects.also_found_as");
    expect(mount(AlsoFoundAs, { props: { object, mid: "M1", n: 1, label: false }, global: { provide: { t: (key) => key } } }).text()).not.toContain("objects.also_found_as");
    expect(mount(AlsoFoundAs, { props: { object: { id: "b" }, mid: "M1", n: 1 }, global: { provide: { t: (key) => key } } }).text()).toBe("");
  });

  it("keeps Undo after the last word went, and says so to the row around it", async () => {
    const api = await import("./api.js");
    const spy = vi.spyOn(api, "del").mockResolvedValue({ object: { id: "a", ook: [], ook_weg: [{ id: "x", zoekterm: "girl" }] } });
    const object = { id: "a", ook: [{ id: "x", zoekterm: "girl" }] };
    const wrapper = mount(AlsoFoundAs, { props: { object, mid: "M1", n: 1, undo: true }, global: { provide: { t: (key) => key } } });
    await wrapper.find(".cc-ook-weg").trigger("click");
    await new Promise((r) => setTimeout(r, 0));
    await wrapper.setProps({ object: { id: "a", ook: [] } });
    expect(wrapper.find(".cc-ook-ongedaan").exists()).toBe(true);
    expect(wrapper.emitted("pending").at(-1)).toEqual([true]);
    // Announced before the change, so the magnifier keeps the row when the last word went.
    const order = Object.keys(wrapper.emitted());
    expect(order.indexOf("pending")).toBeLessThan(order.indexOf("changed"));
    spy.mockRestore();
  });

  it("offers no × for a word the name or description also uses", () => {
    const object = {
      id: "a",
      beschrijving: { onderwerp: "Jongen in wit matrozenpak", onderwerp_en: "Boy in white sailor suit with box" },
      ook: ["boy", "box", "boyish", "doll", "cars"].map((w, i) => ({ id: `e${i}`, zoekterm: w })),
    };
    const wrapper = mount(AlsoFoundAs, { props: { object, mid: "M1", n: 1 }, global: { provide: { t: (key) => key } } });
    const removable = wrapper.findAll(".cc-ook-woord").filter((w) => w.find(".cc-ook-weg").exists()).map((w) => w.text().replace("×", "").trim());
    expect(removable).toEqual(["boyish", "doll", "cars"]);
    const named = mount(AlsoFoundAs, { props: { object: { id: "b", naam: "Two cars", ook: [{ id: "x", zoekterm: "car" }] }, mid: "M1", n: 1 }, global: { provide: { t: (key) => key } } });
    expect(named.find(".cc-ook-weg").exists()).toBe(false);
    const vintage = mount(AlsoFoundAs, { props: { object: { id: "c", zoekterm: "vintage car", ook: [{ id: "y", zoekterm: "car" }] }, mid: "M1", n: 1 }, global: { provide: { t: (key) => key } } });
    expect(vintage.find(".cc-ook-weg").exists()).toBe(false);
  });

  it("forgets what the browser keeps for one file when it starts over", async () => {
    const { forgetFileInBrowser } = await import("./state.js");
    const data = { "cc-gezocht:M1:1": "[]", "cc-items-uit:M1": "[]", "cc-gezocht:M12:1": "[]", "cc-geschiedenis": "[]", "other:M1": "x" };
    const storage = {
      get length() { return Object.keys(data).length; },
      key: (i) => Object.keys(data)[i],
      removeItem: (key) => delete data[key],
    };
    forgetFileInBrowser("M1", storage);
    expect(Object.keys(data).sort()).toEqual(["cc-geschiedenis", "cc-gezocht:M12:1", "other:M1"]);
  });

  it("shows links inside the bullets of a confirmation", async () => {
    const { askConfirm, confirmState } = await import("./confirm.js");
    const ConfirmDialog = (await import("./components/ConfirmDialog.vue")).default;
    const wrapper = mount(ConfirmDialog, { attachTo: document.body, global: { provide: { t: (key) => key } } });
    askConfirm("**Start over? This removes:**\n- {objects}\n- 0 saved\n\nNothing on Commons.", { links: { objects: { href: "/objecten?mid=M1", label: "3 objects" } } });
    await new Promise((r) => setTimeout(r, 0));
    const link = [...document.querySelectorAll("a")].find((a) => a.textContent === "3 objects");
    expect(link?.getAttribute("href")).toBe("/objecten?mid=M1");
    expect(document.querySelectorAll(".cc-bevestig-blok li")).toHaveLength(2);
    confirmState.resolve?.(false);
    wrapper.unmount();
  });

  it("only lets you start over an image that has work kept", async () => {
    const HistoryList = (await import("./components/HistoryList.vue")).default;
    const entries = [{ mid: "M1", naam: "One" }, { mid: "M2", naam: "Two" }, { mid: "M3", naam: "Three" }];
    const wrapper = mount(HistoryList, { props: { entries, work: { M1: true, M2: false } }, global: { provide: { t: (key) => key } } });
    const button = (mid) => wrapper.findAll("li").find((li) => li.text().includes(mid)).findAll("button").find((b) => (b.attributes("aria-label") || "").startsWith("history.start_over"));
    expect(button("M1").attributes("disabled")).toBeUndefined();
    expect(button("M2").attributes("disabled")).toBeDefined();
    expect(button("M3").attributes("disabled")).toBeDefined(); // not known yet
  });

  it("folds the words after the second away in the list", async () => {
    const object = { id: "a", ook: ["boy", "child", "girl", "man"].map((w, i) => ({ id: `e${i}`, zoekterm: w })) };
    const wrapper = mount(AlsoFoundAs, { props: { object, mid: "M1", n: 1, fold: 2 }, global: { provide: { t: (key, v) => (v ? `${key}:${v.n}` : key) } } });
    expect(wrapper.findAll(".cc-ook-woord")).toHaveLength(2);
    expect(wrapper.find(".cc-ook-meer").text()).toBe("objects.also_more:2");
    await wrapper.find(".cc-ook-meer").trigger("click");
    expect(wrapper.findAll(".cc-ook-woord")).toHaveLength(4);
    expect(mount(AlsoFoundAs, { props: { object: { id: "c", ook: object.ook.slice(0, 2) }, mid: "M1", n: 1, fold: 2 }, global: { provide: { t: (key) => key } } }).find(".cc-ook-meer").exists()).toBe(false);
  });

  it("shows nothing in the Saved column of an object that is not saved", () => {
    const obj = { mid: "M1", id: "a", bron: "sam", status: "kandidaat", score: 0.5, bestand_titel: "File:A.jpg", uitsnede_url: "/u.jpg", app_url: "/?mid=M1" };
    const wrapper = mount(ObjectsTable, { props: { objects: [obj], name: () => "x", savedUrl: () => "/s" }, global: { provide: { t: (key) => key, language: "nl", config: {} } } });
    expect(wrapper.text()).not.toContain("false");
  });

  it("counts an object for a search word it was also found with, also inside a group", () => {
    const objects = [
      { id: "a", zoekterm: "child", ook: [{ id: "x", zoekterm: "Girl" }] },
      { id: "b", zoekterm: "person", ook: [{ id: "y", zoekterm: "boy" }, { id: "z", zoekterm: "child" }] },
      { id: "g", bron: "groep", zoekterm: null, groep: { leden: [{ id: "m1", zoekterm: "cardboard box", ook: [{ id: "s", zoekterm: "suitcase" }] }, { id: "m2", zoekterm: "boy" }] } },
    ];
    expect(objectsWithTerm(objects, "girl")).toEqual(["a"]);
    expect(objectsWithTerm(objects, "child")).toEqual(["a", "b"]);
    expect(objectsWithTerm(objects, "boy")).toEqual(["b", "m2"]);
    expect(objectsWithTerm(objects, "suitcase")).toEqual(["m1"]);
    expect(objectsWithTerm(objects, "lawn")).toEqual([]);
  });

  it("keeps the choice of a list page in its address and reads it back", () => {
    expect(readAddress(["soort", "reeks"], "?soort=Toegevoegd,Opgelost&q=tick&uselang=en")).toEqual({ soort: ["Toegevoegd", "Opgelost"], reeks: [], q: "tick" });
    const calls = [];
    const location = { pathname: "/changelog", search: "?uselang=en&soort=Opgelost", hash: "" };
    const history = { state: null, replaceState: (state, title, url) => calls.push(url) };
    writeAddress({ soort: ["Toegevoegd"], reeks: [], q: " masker " }, location, history);
    expect(calls).toEqual(["/changelog?uselang=en&soort=Toegevoegd&q=masker"]);
    writeAddress({ soort: [], q: "" }, { ...location, search: "?uselang=en" }, history);
    expect(calls).toHaveLength(1); // nothing changed: no new address
  });

  it("builds the address of an export from the current choice", () => {
    expect(exportUrl("/x", {}, "csv")).toBe("/x?formaat=csv");
    expect(exportUrl("/x", { bron: ["sam", "groep"], mid: [], opgeslagen: true, aangevuld: false, q: " a b " }, "xlsx")).toBe("/x?formaat=xlsx&bron=sam%2Cgroep&opgeslagen=1&q=a+b");
  });

  it("sorts the values of a facet by number, a date by date", () => {
    expect(facetOptions(rows, "soort")).toEqual([{ value: "Toegevoegd", n: 3 }, { value: "Opgelost", n: 1 }]);
    const dates = [{ values: { d: "2026-11-01" } }, { values: { d: "2026-11-01" } }, { values: { d: "2026-11-08" } }];
    expect(facetOptions(dates, "d")[0].value).toBe("2026-11-01");
    expect(facetOptions(dates, "d", newestFirst)[0].value).toBe("2026-11-08");
  });

  it("shows a description after an option and an (i) with a facet", () => {
    const groups = [{ key: "model", label: "Model", info: { title: "T", label: "About", paragraphs: ["p"] }, options: [{ value: "sam-3.1", n: 2, description: "finds objects" }] }, { key: "user", label: "User", options: [{ value: "x", n: 1 }] }];
    const wrapper = mount(ListFacets, { props: { groups, filters: { model: [], user: [] }, searchLabel: "s" }, global: { provide: { t: (key) => key, language: "nl" } } });
    expect(wrapper.findAll(".cc-facet-uitleg").map((d) => d.text())).toEqual(["finds objects"]);
    expect(wrapper.findAll(".cc-info-knop")).toHaveLength(1);
  });

  it("puts the 7th value of a facet and further in a fold-out, which says what is ticked in it", async () => {
    const options = Array.from({ length: 8 }, (_, i) => ({ value: `v${i}`, n: 1 }));
    const six = [{ key: "a", label: "A", options: options.slice(0, 6) }];
    const props = { filters: { a: ["v7"] }, searchLabel: "s" };
    const provide = { t: (key, values) => (values ? `${key}:${values.n}` : key), language: "nl" };
    expect(mount(ListFacets, { props: { ...props, groups: six }, global: { provide } }).find("details").exists()).toBe(false);
    const wrapper = mount(ListFacets, { props: { ...props, groups: [{ key: "a", label: "A", options }] }, global: { provide } });
    expect(wrapper.findAll("input[type=checkbox]")).toHaveLength(8);
    expect(wrapper.findAll("details input[type=checkbox]")).toHaveLength(2);
    expect(wrapper.find("details summary").text()).toContain("facets.more:2");
    expect(wrapper.find("details summary").text()).toContain("facets.more_chosen:1");
  });

  it("hides changes, sections and versions that do not match on the changelog page", async () => {
    document.body.innerHTML = `
      <section class="cl-versie" id="a">
        <div class="cl-sectie" id="a1"><div class="cl-item" data-versie="0.2.0" data-reeks="0.2" data-datum="2026-11-02" data-soort="Toegevoegd">Facets added</div></div>
        <div class="cl-sectie" id="a2"><div class="cl-item" data-versie="0.2.0" data-reeks="0.2" data-datum="2026-11-02" data-soort="Opgelost" data-soort-naam="Fixed">Crash fixed</div></div>
      </section>
      <section class="cl-versie" id="b">
        <div class="cl-sectie" id="b1"><div class="cl-item" data-versie="0.1.0" data-reeks="0.1" data-datum="2026-11-01" data-soort="Toegevoegd">First version</div></div>
      </section>`;
    const wrapper = mount(ChangelogFacets, { global: { provide: { t: (key) => key, language: "nl" } } });
    expect(wrapper.text()).toContain("Fixed");
    await wrapper.find("input[type=search]").setValue("crash");
    expect(document.getElementById("a").hidden).toBe(false);
    expect(document.getElementById("a1").hidden).toBe(true);
    expect(document.getElementById("a2").hidden).toBe(false);
    expect(document.getElementById("b").hidden).toBe(true);
    await wrapper.find("input[type=search]").setValue("");
    expect(document.querySelectorAll("[hidden]")).toHaveLength(0);
    wrapper.unmount();
    document.body.innerHTML = "";
  });
});

describe("a colour per kind of object", () => {
  const sam = (id, zoekterm, extra = {}) => ({ id, bron: "sam", zoekterm, label: zoekterm, status: "kandidaat", box: { x: 0, y: 0, w: 10, h: 10 }, masker: "m.png", masker_url: "/m.png", ...extra });

  it("gives each search term a colour, only with two kinds or more", () => {
    expect(classColors([sam("a", "plate"), sam("b", "Plate")])).toEqual({});
    const colors = classColors([sam("a", "plate"), sam("b", "wine glass"), sam("c", "klik"), { id: "d", bron: "handmatig", zoekterm: "rechthoek" }]);
    expect(Object.keys(colors)).toEqual(["plate", "wine glass"]);
    expect(colors.plate).not.toBe(colors["wine glass"]);
    expect(classKey({ bron: "groep", zoekterm: "plate" })).toBeNull();
    expect(classKey({ bron: "commons", zoekterm: "plate" })).toBeNull();
    // A group has the kind of its members; a group of mixed kinds has none.
    expect(classKey({ bron: "groep", groep: { soort: "Cloud" } })).toBe("cloud");
    expect(classKey({ bron: "groep", groep: { soort: null } })).toBeNull();
    // A region from Commons has its name as its kind; a region without a name has none.
    expect(classKey({ bron: "commons", label: "Dog" })).toBe("dog");
    expect(classKey({ bron: "commons", label: "hond", label_en: "Dog" })).toBe("dog");
    expect(classKey({ bron: "commons", label: "regio" })).toBeNull();
  });

  it("lets your own name decide the kind", () => {
    expect(classKey(sam("a", "person", { naam: " Doll " }))).toBe("doll");
    expect(classKey({ bron: "handmatig", zoekterm: "rechthoek", naam: "Door" })).toBe("door");
    expect(classKey({ bron: "sam", zoekterm: "klik", naam: "handle" })).toBe("handle");
    expect(classKey({ bron: "groep", groep: { soort: null, naam: "Family" } })).toBe("family");
    expect(Object.keys(classColors([sam("a", "person"), sam("b", "person", { naam: "doll" })]))).toEqual(["doll", "person"]);
  });

  it("adds the text of the object search as a tick box", () => {
    const colors = { girl: "#111111", person: "#222222" };
    expect(kindsWithQuery(colors, "")).toEqual([["girl", "#111111"], ["person", "#222222"]]);
    expect(kindsWithQuery(colors, "doll")).toEqual([["doll", QUERY_COLOUR], ["girl", "#111111"], ["person", "#222222"]]);
    expect(kindsWithQuery(colors, "person")).toEqual([["person", "#222222"], ["girl", "#111111"]]);
    expect(kindsWithQuery({}, "doll")).toEqual([["doll", QUERY_COLOUR]]);
  });

  it("counts a merged object only under its own kind, not under the words it was also found with", () => {
    const child = sam("a", "child", { ook: [{ id: "x", zoekterm: "Girl" }, { id: "y", zoekterm: "klik" }] });
    expect(classKeys(child)).toEqual(["child"]);
    expect(classKey(child)).toBe("child");
    const group = { id: "g", bron: "groep", groep: { soort: null, leden: [sam("m", "cardboard box", { ook: [{ id: "s", zoekterm: "suitcase" }] })] } };
    expect(classKeys(group)).toEqual(["cardboard box"]);
    const host = document.createElement("div");
    const viewer = new PageViewer(host, () => {});
    viewer.setObjects([child, sam("f", "fence")], [], classColors([child, sam("f", "fence")]));
    viewer.setKindFilter(["girl"]);
    expect(host.querySelector('g.object[data-id="a"]').classList.contains("object-soort-aan")).toBe(false);
    viewer.setKindFilter(["child"]);
    expect(host.querySelector('g.object[data-id="a"]').classList.contains("object-soort-aan")).toBe(true);
  });

  it("counts a renamed object only under its name, no longer under its search term", () => {
    const doll = sam("a", "person", { naam: "Doll" });
    expect(classKeys(doll)).toEqual(["doll"]);
    expect(classKey(doll)).toBe("doll"); // the colour is that of your name
    expect(classKeys(sam("b", "Person", { naam: "person" }))).toEqual(["person"]);
    expect(classKeys(sam("c", "klik", { naam: "handle" }))).toEqual(["handle"]);
    // A group with a name of its own counts only under that name (wish Olaf 12-11-2026).
    expect(classKeys({ bron: "groep", groep: { soort: null, naam: "Family", leden: [sam("d", "boy"), sam("e", "person", { naam: "doll" })] } })).toEqual(["family"]);
    expect(classKeys({ bron: "groep", naam: "car-group", groep: { soort: null, leden: [sam("g", "car"), sam("h", "wheel")] } })).toEqual(["car-group"]);
    const host = document.createElement("div");
    const viewer = new PageViewer(host, () => {});
    viewer.setObjects([doll, sam("f", "fence")], [], classColors([doll, sam("f", "fence")]));
    viewer.setKindFilter(["doll"]);
    expect(host.querySelector('g.object[data-id="a"]').classList.contains("object-soort-aan")).toBe(true);
    for (const kinds of [["person"], ["fence"]]) {
      viewer.setKindFilter(kinds);
      expect(host.querySelector('g.object[data-id="a"]').classList.contains("object-soort-aan")).toBe(false);
    }
    viewer.setKindFilter(["fence"]);
    expect(host.querySelector('g.object[data-id="a"]').classList.contains("object-soort-aan")).toBe(false);
  });

  it("counts a group of mixed kinds under each of them, without a colour of a kind", () => {
    const mixed = { id: "g", bron: "groep", status: "kandidaat", box: { x: 0, y: 0, w: 10, h: 10 }, groep: { soort: null, leden: [sam("a", "boy"), sam("b", "box"), sam("c", "boy"), sam("d", "klik")] } };
    expect(classKeys(mixed)).toEqual(["boy", "box"]);
    expect(classKey(mixed)).toBeNull();
    expect(Object.keys(classColors([mixed]))).toEqual(["box", "boy"]);
    expect(classKeys({ bron: "groep", groep: { soort: "Cloud", leden: [sam("a", "cloud")] } })).toEqual(["cloud"]);
    expect(classKeys({ bron: "handmatig" })).toEqual([]);
    expect(classKeys(null)).toEqual([]);
    const host = document.createElement("div");
    const viewer = new PageViewer(host, () => {});
    viewer.setObjects([mixed, sam("e", "fence")], [], classColors([mixed, sam("e", "fence")]));
    viewer.setKindFilter(["boy"]);
    expect(host.querySelector('g.object[data-id="g"]').classList.contains("object-soort-aan")).toBe(true);
    viewer.setKindFilter(["fence"]);
    expect(host.querySelector('g.object[data-id="g"]').classList.contains("object-soort-aan")).toBe(false);
  });

  it("colours the masks in the viewer and a dot in the list", () => {
    const list = [sam("a", "plate"), sam("b", "wine glass")];
    const colors = classColors(list);
    const { host, viewer } = viewerWithPage();
    viewer.setObjects(list, [], colors);
    const group = host.querySelector('g.object[data-id="a"]');
    expect(group.getAttribute("class")).toContain("object-klasse");
    expect(group.style.getPropertyValue("--klasse")).toBe(colors.plate);
    viewer.setSelection(["a"]);
    expect(group.getAttribute("class")).toContain("object-klasse");
    const wrapper = mount(ObjectList, { props: { mid: "M1", n: 1, objects: list, classColors: colors }, global: { provide: { t: (key) => key, language: "nl" } } });
    expect(wrapper.findAll(".cc-klasse-stip")).toHaveLength(2);
  });

  it("shows only the masks of one kind, and all again", () => {
    const list = [sam("a", "plate"), sam("b", "wine glass")];
    const { host, viewer } = viewerWithPage();
    viewer.setObjects(list, [], classColors(list));
    viewer.setKindFilter("plate");
    expect(viewer.el.classList.contains("soort-filter")).toBe(true);
    expect(host.querySelector('g.object[data-id="a"]').classList.contains("object-soort-aan")).toBe(true);
    expect(host.querySelector('g.object[data-id="b"]').classList.contains("object-soort-aan")).toBe(false);
    viewer.setObjects(list, [], classColors(list)); // a redraw keeps the choice
    expect(host.querySelector('g.object[data-id="a"]').classList.contains("object-soort-aan")).toBe(true);
    viewer.setKindFilter(["plate", "wine glass"]); // several kinds at once
    expect(host.querySelectorAll(".object-soort-aan")).toHaveLength(2);
    viewer.setKindFilter([]); // None: every object fades
    expect(host.querySelectorAll(".object-soort-aan")).toHaveLength(0);
    expect(viewer.el.classList.contains("soort-filter")).toBe(true);
    viewer.setKindFilter(null); // no filter
    expect(viewer.el.classList.contains("soort-filter")).toBe(false);
    // The statuses of the frames filter too, together with the kinds (wish Olaf).
    viewer.setSelection(["a"]);
    viewer.setStatusFilter(["geselecteerd"]);
    expect(host.querySelector('g.object[data-id="a"]').classList.contains("object-soort-aan")).toBe(true);
    expect(host.querySelector('g.object[data-id="b"]').classList.contains("object-soort-aan")).toBe(false);
    viewer.setKindFilter(["wine glass"]); // selected and a wine glass: none
    expect(host.querySelectorAll(".object-soort-aan")).toHaveLength(0);
    viewer.setKindFilter(null);
    viewer.setStatusFilter(null);
    expect(viewer.el.classList.contains("soort-filter")).toBe(false);
  });

  it("outlines each mask in neutral white, and uses the status colours without kinds", () => {
    const list = [sam("a", "plate"), sam("b", "wine glass")];
    const { host, viewer } = viewerWithPage();
    viewer.setObjects(list, [], {}); // "by status": no colours per kind
    expect(host.querySelectorAll(".object-klasse")).toHaveLength(0);
    expect(host.querySelectorAll(".object-masker-rand")).toHaveLength(2);
    const floods = [...host.querySelectorAll("#masker-rand feFlood")].map((f) => f.getAttribute("flood-color"));
    expect(floods).toEqual(["#fff", "#000"]);
    expect(host.querySelectorAll("#masker-rand feMorphology")).toHaveLength(2);
  });
});

describe("searching objects after a rename", () => {
  it("no longer finds an object you named by the AI's search term", () => {
    const suitcase = { id: "a", mid: "M1", naam: "suitcase", zoekterm: "cardboard box", label_nl: "kartonnen doos" };
    const car = { id: "b", mid: "M1", zoekterm: "vintage car", label_nl: "oldtimer" };
    const found = (q) => applyFacets([suitcase, car], { ...emptyFilters(), query: q }).map((o) => o.id);
    expect(found("car")).toEqual(["b"]);
    expect(found("doos")).toEqual([]);
    expect(found("suit")).toEqual(["a"]);
    expect(found("oldtimer")).toEqual(["b"]); // without a name of its own, the AI's words still count
  });
});

describe("small shared helpers", async () => {
  const { readStored, writeStored, removeStored } = await import("./storage.js");
  const { kindsOf, commonsFileUrl } = await import("./state.js");
  const { priceLabel } = await import("./i18n.js");

  it("stores text and JSON in this browser, and falls back when there is nothing or it is broken", () => {
    writeStored("cc-test-tekst", "1");
    expect(readStored("cc-test-tekst")).toBe("1");
    writeStored("cc-test-json", { a: true }, { json: true });
    expect(readStored("cc-test-json", {}, { json: true })).toEqual({ a: true });
    window.localStorage.setItem("cc-test-json", "{kapot");
    expect(readStored("cc-test-json", [], { json: true })).toEqual([]);
    removeStored("cc-test-tekst");
    removeStored("cc-test-json");
    expect(readStored("cc-test-tekst", "x")).toBe("x");
  });

  it("swallows errors of blocked storage", () => {
    const spy = vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    const set = vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("blocked");
    });
    expect(readStored("cc-x", "fallback")).toBe("fallback");
    expect(() => writeStored("cc-x", "1")).not.toThrow();
    spy.mockRestore();
    set.mockRestore();
  });

  it("counts objects per search term without groups, named as in the list", () => {
    const objects = [
      { zoekterm: "hat", label_nl: "hoed" },
      { zoekterm: "hat", label_nl: "hoed", beschrijving: {} },
      { zoekterm: "dog" },
      { zoekterm: "hat", bron: "groep" },
      { label: "klik" },
    ];
    expect(kindsOf(objects, "nl")).toEqual([
      { term: "hat", name: "hoed", n: 2 },
      { term: "dog", name: "dog", n: 1 },
    ]);
    expect(kindsOf(objects, "en", (o) => o.beschrijving)).toEqual([
      { term: "hat", name: "hat", n: 1 },
      { term: "dog", name: "dog", n: 1 },
    ]);
  });

  it("shows a price in brackets when paid, else the word for free", () => {
    const t = (key) => ({ "panel.free": "(gratis)" })[key] ?? key;
    expect(priceLabel(0.01, true, "en", t)).toBe("($0.01)");
    expect(priceLabel(0.01, false, "nl", t)).toBe("(gratis)");
  });

  it("links to a file on Commons, optionally at an anchor", () => {
    expect(commonsFileUrl("File:A b.jpg", "P180")).toBe("https://commons.wikimedia.org/wiki/File%3AA_b.jpg#P180");
    expect(commonsFileUrl("")).toBe("https://commons.wikimedia.org/wiki/");
  });
});

describe("formatStamp", () => {
  it("shows a moment to the second (wish Olaf)", async () => {
    const { formatStamp } = await import("./i18n.js");
    expect(formatStamp("2026-11-13T11:24:07.123Z", "nl")).toMatch(/:\d\d:07$/);
    expect(formatStamp("2026-11-13T11:24:07Z", "en", "short")).toMatch(/:\d\d:07$/);
    expect(formatStamp("", "nl")).toBe("");
    expect(formatStamp("niet een tijd", "nl")).toBe("");
  });
});

describe("askRemoval", () => {
  it("shows what goes between the question and the rest of the text (wish Olaf)", async () => {
    const { askRemoval, answerConfirm, confirmState } = await import("./confirm.js");
    const asked = askRemoval("Delete this prompt?\n\nThe descriptions stay.", { title: "Delete" }, "Describe only the fruit.");
    expect(confirmState.text).toBe("Delete this prompt?");
    expect(confirmState.quote).toBe("Describe only the fruit.");
    expect(confirmState.note).toBe("The descriptions stay.");
    answerConfirm(false);
    expect(await asked).toBe(false);
    const image = askRemoval("Remove it?", { title: "Remove" }, { objects: [{ image: "/a.png", name: "a" }] });
    expect(confirmState.objects).toHaveLength(1);
    expect(confirmState.quote).toBe("");
    answerConfirm(false);
    await image;
  });
});

describe("ticking objects in a bulk question", () => {
  it("returns the ticked ones and follows the count (wish Olaf)", async () => {
    const { askConfirmValue, answerConfirm, confirmState } = await import("./confirm.js");
    const asked = askConfirmValue("Group these 3?", {
      objects: [{ name: "a" }, { name: "b" }, { name: "c" }],
      pick: { min: 2, text: (n) => `Group these ${n}?` },
    });
    expect(confirmState.picked).toEqual([true, true, true]);
    expect(confirmState.pick.min).toBe(2);
    confirmState.picked = [true, false, true];
    answerConfirm(true);
    expect((await asked).picked).toEqual([0, 2]);
    const plain = askConfirmValue("Sure?", { objects: [{ name: "a" }, { name: "b" }] });
    expect(confirmState.pick).toBe(null);
    answerConfirm(true);
    expect((await plain).picked).toEqual([0, 1]);
  });
});

describe("tick boxes", () => {
  it("toggles one value and inverts a list", () => {
    expect(toggledIn(["a", "b"], "a")).toEqual(["b"]);
    expect(toggledIn(["b"], "a")).toEqual(["b", "a"]);
    expect(invertedIn(["a", "b", "c"], ["b"])).toEqual(["a", "c"]);
    expect(invertedIn(["a"], [])).toEqual(["a"]);
  });

  it("shows All · None · Invert with the given keys and emits the choice", async () => {
    const wrapper = mount(TickLinks, {
      props: { label: "Kies:", keys: { all: "x.all", none: "x.none", invert: "x.invert" }, disabledNone: true, titles: { all: "help" } },
      global: { provide: { t: (key) => key } },
    });
    expect(wrapper.text()).toBe("Kies: x.all · x.none · x.invert");
    const [all, none, invert] = wrapper.findAll("button");
    expect(all.attributes("title")).toBe("help");
    expect(none.attributes("disabled")).toBeDefined();
    await all.trigger("click");
    await invert.trigger("click");
    expect(Object.keys(wrapper.emitted())).toEqual(expect.arrayContaining(["all", "invert"]));
    const legend = mount(TickLinks, { props: { tag: "li", dots: true }, global: { provide: { t: (key) => key } } });
    expect(legend.element.tagName).toBe("LI");
    expect(legend.findAll(".cc-punt")).toHaveLength(2);
    expect(legend.find("button").text()).toBe("objects.all");
  });
});

describe("every dialog movable", () => {
  it("wires dialogs that appear later, not the ones that do it themselves (wish Olaf)", async () => {
    const { movableDialogs } = await import("./movable.js");
    const make = (cls) => {
      const dialog = document.createElement("div");
      dialog.className = `cdx-dialog ${cls}`;
      const header = document.createElement("header");
      header.className = "cdx-dialog__header";
      dialog.append(header);
      document.body.append(dialog);
      return dialog;
    };
    const first = make("cc-bevestig");
    const stop = movableDialogs({ move: "move" });
    expect(first.classList.contains("cc-verplaatsbaar")).toBe(true);
    const later = make("cc-lokaliseren");
    const own = make("cc-vergroter");
    await new Promise((resolve) => setTimeout(resolve, 0)); // the observer runs after the change
    expect(later.classList.contains("cc-verplaatsbaar")).toBe(true);
    expect(later.querySelectorAll(".cc-rand")).toHaveLength(8);
    expect(own.classList.contains("cc-verplaatsbaar")).toBe(false);
    [first, later, own].forEach((d) => d.remove());
    stop();
  });
});

// -- Robustness (wish Olaf 13-11-2026): errors, retries, late answers, broken data ----------------

describe("api robustness", async () => {
  const { GET_TIMEOUT, isAbort, newestOnly, statusCode } = await import("./api.js");
  const answer = (status, text) => ({ ok: status >= 200 && status < 300, status, text: async () => text });
  const noWait = { delays: [0, 0] };

  it("tries a GET again when the server cannot be reached, and gives a network error after that", async () => {
    const fetchImpl = vi.fn(async () => {
      throw new TypeError("Failed to fetch");
    });
    const error = await request("GET", "/api/v1/x", undefined, { fetchImpl, ...noWait }).catch((e) => e);
    expect(fetchImpl).toHaveBeenCalledTimes(3);
    expect(error).toBeInstanceOf(ApiError);
    expect(error.code).toBe("network");
  });

  it("never tries a POST, PATCH, PUT or DELETE again (a paid call or a change happens once)", async () => {
    for (const method of ["POST", "PATCH", "PUT", "DELETE"]) {
      const fetchImpl = vi.fn(async () => answer(503, "<html>Service Unavailable</html>"));
      const error = await request(method, "/api/v1/x", {}, { fetchImpl, ...noWait }).catch((e) => e);
      expect(fetchImpl, method).toHaveBeenCalledTimes(1);
      expect(error.code).toBe("server_unavailable");
    }
  });

  it("gets through when the server is back after a restart (502 with an HTML page, then JSON)", async () => {
    const replies = [answer(502, "<html>Bad Gateway</html>"), answer(503, ""), answer(200, '{"ok":true}')];
    const fetchImpl = vi.fn(async () => replies.shift());
    expect(await request("GET", "/api/v1/x", undefined, { fetchImpl, ...noWait })).toEqual({ ok: true });
    expect(fetchImpl).toHaveBeenCalledTimes(3);
  });

  it("gives every HTTP status without a code of its own a code, with or without a JSON body", async () => {
    const cases = { 400: "bad_request", 401: "session_expired", 403: "forbidden", 404: "not_found", 409: "conflict", 410: "gone", 413: "request_too_large", 429: "too_many_requests", 500: "server_error", 503: "server_unavailable" };
    for (const [status, code] of Object.entries(cases)) {
      for (const body of ["", "<html>error</html>", '{"fout":"Iets"}']) {
        const fetchImpl = async () => answer(Number(status), body);
        const error = await request("POST", "/api/v1/x", {}, { fetchImpl }).catch((e) => e);
        expect(error.code, `${status} ${body}`).toBe(code);
        expect(error.status).toBe(Number(status));
      }
    }
    // The server's own code and text win.
    const own = await request("POST", "/x", {}, { fetchImpl: async () => answer(429, '{"code":"daily_limit","fout":"Op"}') }).catch((e) => e);
    expect([own.code, own.message]).toEqual(["daily_limit", "Op"]);
    expect(statusCode(599)).toBe("server_error");
    expect(statusCode(418)).toBe("error");
  });

  it("does not take an HTML page for an answer, and an empty one is null", async () => {
    const html = await request("GET", "/x", undefined, { fetchImpl: async () => answer(200, "<html>Log in</html>") }).catch((e) => e);
    expect(html.code).toBe("bad_response");
    expect(await request("DELETE", "/x", undefined, { fetchImpl: async () => answer(204, "") })).toBeNull();
  });

  it("gives up a GET that does not answer in time, but never times out a POST by default", async () => {
    const hanging = vi.fn((url, options) => new Promise((resolve, reject) => {
      options.signal?.addEventListener("abort", () => reject(Object.assign(new Error("aborted"), { name: "AbortError" })));
    }));
    const error = await request("GET", "/x", undefined, { fetchImpl: hanging, timeout: 10, retries: 0 }).catch((e) => e);
    expect(error.code).toBe("timeout");
    expect(GET_TIMEOUT).toBeGreaterThanOrEqual(60000);
    let settled = false;
    request("POST", "/x", {}, { fetchImpl: hanging }).finally(() => (settled = true)).catch(() => {});
    await new Promise((resolve) => setTimeout(resolve, 30));
    expect(settled).toBe(false);
  });

  it("leaves an abort by the caller an AbortError, not tried again", async () => {
    const controller = new AbortController();
    const fetchImpl = vi.fn(async () => {
      controller.abort();
      throw Object.assign(new Error("aborted"), { name: "AbortError" });
    });
    const error = await request("GET", "/x", undefined, { fetchImpl, signal: controller.signal, ...noWait }).catch((e) => e);
    expect(isAbort(error)).toBe(true);
    expect(fetchImpl).toHaveBeenCalledTimes(1);
  });

  it("has a Dutch and an English text for every code the client makes itself", () => {
    const codes = ["network", "timeout", "bad_response", "unexpected", ...[400, 401, 403, 404, 405, 409, 410, 413, 429, 500, 502].map(statusCode)];
    for (const code of codes) {
      expect(nl[`error.${code}`], code).toBeTruthy();
      expect(en[`error.${code}`], code).toBeTruthy();
    }
  });

  it("shows no technical English for a fault in the app, and the network text only for a failed fetch", () => {
    const t = (key) => ({ "meta.language": "en", "error.error": "Something went wrong.", "error.network": "No server." })[key] ?? key;
    expect(errorText(t, new TypeError("Cannot read properties of undefined (reading 'id')"))).toBe("Something went wrong.");
    expect(errorText(t, new TypeError("Failed to fetch"))).toBe("No server.");
    expect(errorText(t, new ApiError(0, { code: "network" }))).toBe("No server.");
    expect(errorText(t, undefined)).toBe("Something went wrong.");
  });

  it("lets only the newest of a series count (two quick searches, page after page)", () => {
    const newest = newestOnly();
    const first = newest();
    const second = newest();
    expect([first(), second()]).toEqual([false, true]);
  });
});

describe("typed text and page numbers", async () => {
  const { cleanText, searchWords } = await import("./text.js");
  const { pageNumber } = await import("./state.js");

  it("treats a text of only spaces or invisible characters as empty, and keeps emoji and right-to-left text", () => {
    expect(cleanText("  ​‎﻿ ⁦")).toBe("");
    expect(cleanText("​boom ")).toBe("boom");
    expect(cleanText("\u{1F468}‍\u{1F469}‍\u{1F467} family")).toBe("\u{1F468}‍\u{1F469}‍\u{1F467} family"); // the joiners inside the emoji stay
    expect(cleanText(" שלום world ")).toBe("שלום world");
    expect(cleanText(null)).toBe("");
    expect(cleanText(42)).toBe("42");
    expect(cleanText("x".repeat(10000))).toHaveLength(10000);
  });

  it("splits a search into clean words, without empty or invisible ones", () => {
    expect(searchWords(" Hoed ​  JAS ")).toEqual(["hoed", "jas"]);
    expect(searchWords("​ ‌")).toEqual([]);
  });

  it("makes any page number from an address or the history a valid one", () => {
    expect(pageNumber("3", 5)).toBe(3);
    expect(pageNumber("abc", 5)).toBe(1);
    expect(pageNumber(0, 5)).toBe(1);
    expect(pageNumber(-2)).toBe(1);
    expect(pageNumber(2.7, 5)).toBe(2);
    expect(pageNumber(9, 4)).toBe(4); // the file has fewer pages now
    expect(pageNumber(NaN)).toBe(1);
    expect(pageNumber("7", undefined)).toBe(7);
  });
});

describe("stored values of the wrong shape", async () => {
  const { readStored, writeStored, removeStored, useStoredList } = await import("./storage.js");
  const { computed } = await import("vue");

  it("gives the fallback when stored JSON is not a list or an object as expected", () => {
    writeStored("cc-test-vorm", { a: 1 }, { json: true });
    expect(readStored("cc-test-vorm", [], { json: true })).toEqual([]);
    writeStored("cc-test-vorm", [1, 2], { json: true });
    expect(readStored("cc-test-vorm", {}, { json: true })).toEqual({});
    window.localStorage.setItem("cc-test-vorm", "null");
    expect(readStored("cc-test-vorm", {}, { json: true })).toEqual({});
    expect(readStored("cc-test-vorm", null, { json: true })).toBeNull();
    removeStored("cc-test-vorm");
  });

  it("reads a list kept per file as a list, also when something else was stored under its key", () => {
    window.localStorage.setItem("cc-test-lijst", '"tekst"');
    const { list, toggle } = useStoredList(computed(() => "cc-test-lijst"));
    expect(list.value).toEqual([]);
    toggle("hoed");
    expect(readStored("cc-test-lijst", [], { json: true })).toEqual(["hoed"]);
    removeStored("cc-test-lijst");
  });
});

describe("PageViewer with broken data", async () => {
  const { validBox } = await import("./viewer/viewer.js");

  it("accepts only boxes of numbers, and turns a negative width or height round", () => {
    expect(validBox({ x: 10, y: 20, w: -5, h: 8 })).toEqual({ x: 5, y: 20, w: 5, h: 8 });
    expect(validBox({ x: "1", y: "2", w: "3", h: "4" })).toEqual({ x: 1, y: 2, w: 3, h: 4 });
    expect(validBox({ x: 0, y: 0, w: 0, h: 0 })).toEqual({ x: 0, y: 0, w: 0, h: 0 });
    for (const bad of [null, undefined, {}, { x: NaN, y: 0, w: 1, h: 1 }, { x: 0, y: 0, w: Infinity, h: 1 }, { x: "", y: 0, w: 1, h: 1 }, "box"]) expect(validBox(bad)).toBeNull();
  });

  it("draws the good objects and leaves out those without a usable box, without throwing", () => {
    const { host, viewer } = viewerWithPage();
    const broken = [
      ...objects,
      { id: "c", status: "kandidaat", bron: "dummy" },
      { id: "d", status: "kandidaat", bron: "dummy", box: { x: NaN, y: 1, w: 2, h: 2 } },
      { id: "e", status: "kandidaat", bron: "dummy", box: { x: 50, y: 50, w: -20, h: 10 } },
      // A shape without its address: only the frame, no request for "undefined".
      { id: "f", status: "geselecteerd", bron: "dummy", box: { x: 1, y: 1, w: 5, h: 5 }, masker: { breedte: 1 } },
    ];
    expect(() => viewer.setObjects(broken, ["c"])).not.toThrow();
    expect([...host.querySelectorAll("g.object")].map((g) => g.dataset.id)).toEqual(["a", "b", "e", "f"]);
    expect(host.querySelector('g[data-id="e"] rect.object-rand').getAttribute("x")).toBe("30");
    expect(broken[4].box.w).toBe(-20); // the app's own object is not changed
    expect(host.querySelector('g[data-id="f"] .object-masker')).toBeNull();
    expect(viewer.focusObject("c")).toBe(false);
  });

  it("forgets the object under the mouse once it is gone, so a double-click does not open it", () => {
    const { viewer } = viewerWithPage();
    viewer.setObjects(objects);
    viewer.hoverObject = objects[0];
    viewer.tooltip.hidden = false;
    viewer.setObjects([objects[1]]);
    expect(viewer.hoverObject).toBeNull();
    expect(viewer.tooltip.hidden).toBe(true);
    const opened = [];
    viewer.on("object-open", (o) => opened.push(o));
    viewer.el.dispatchEvent(new MouseEvent("dblclick"));
    expect(opened).toEqual([]);
  });

  it("never gets NaN in its transform: a page of size 0, a NaN box to zoom to, a viewer of size 0", () => {
    const host = document.createElement("div");
    document.body.append(host);
    const viewer = new PageViewer(host);
    viewer.load({ width: 0, height: undefined, src: "data:,", srcWidth: 0 });
    viewer.zoomToBox({ x: NaN, y: 0, w: 1, h: 1 });
    viewer.zoomStep(1);
    viewer.zoomBy(2);
    viewer.fit();
    expect(viewer.stage.style.transform).not.toMatch(/NaN|Infinity/);
    expect(Number.isFinite(viewer.scale) && viewer.scale > 0).toBe(true);
  });
});

describe("the safety net", async () => {
  const { installSafetyNet, reportUnexpected, resetSafetyNet, safetyNotices } = await import("./safety.js");
  const { createApp, h, nextTick } = await import("vue");
  const t = (key, params = {}) => (key === "error.unexpected" ? `Onverwacht: ${params.detail}` : key === "error.error" ? "Er ging iets mis." : key === "error.network" ? "Geen server." : key);

  it("shows one red message for an error nobody caught, keeps it in the console, and ignores an abort", async () => {
    resetSafetyNet();
    const target = document.createElement("div");
    document.body.append(target);
    const listeners = {};
    const win = { addEventListener: (type, fn) => (listeners[type] = fn) };
    const log = { error: vi.fn() };
    const app = createApp({ render: () => h("p") });
    installSafetyNet(app, t, { target, win, log });
    app.config.errorHandler(new TypeError("x is undefined"), null, "watcher callback");
    expect(log.error).toHaveBeenCalled();
    expect(safetyNotices.map((n) => [n.type, n.text])).toEqual([["error", "Onverwacht: Er ging iets mis."]]);
    listeners.unhandledrejection({ reason: new ApiError(0, { code: "network" }) });
    expect(safetyNotices).toHaveLength(1); // one at a time: the newest
    expect(safetyNotices[0].text).toBe("Onverwacht: Geen server.");
    expect(reportUnexpected(t, Object.assign(new Error("stop"), { name: "AbortError" }))).toBe(false);
    await nextTick();
    expect(target.textContent).toContain("Onverwacht");
    resetSafetyNet();
  });
});

it("bulletList reads bullets and sub-bullets, and nothing else", async () => {
  const { bulletList } = await import("./text.js");
  const text = ["Intro", "- Beeldt af", "  - items", "  - objecten", "- Bijschriften", "slot"].join(String.fromCharCode(10));
  expect(bulletList(text)).toEqual([
    { text: "Beeldt af", sub: ["items", "objecten"] },
    { text: "Bijschriften", sub: [] },
  ]);
  expect(bulletList("  - zonder kop")).toEqual([]);
  expect(bulletList(null)).toEqual([]);
});
