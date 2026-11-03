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
      props: { objects: structuredClone(objects).map((o) => ({ ...o, status: o.id === "a" ? "geselecteerd" : "kandidaat" })) },
      global: { provide: { t: (key) => key, language: "nl" } },
    });
    const names = wrapper.findAll(".cc-object-naam").map((n) => n.text());
    expect(names).toEqual(["Catharina", "wapen"]);
    await wrapper.findAll('input[type="checkbox"]')[0].setValue(true);
    expect(wrapper.emitted("toggle")[0]).toEqual(["b"]);
  });
});
