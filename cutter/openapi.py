"""OpenAPI 3.1 description of /api/v1 (functional design 11). Kept next to the
code: tests/test_api.py checks that every route is described here and that
nothing is described that does not exist."""

from . import __version__

MID = {"name": "mid", "in": "path", "required": True, "schema": {"type": "string", "pattern": "^M\\d+$"}, "description": "M-id, bijv. M28830642"}
N = {"name": "n", "in": "path", "required": True, "schema": {"type": "integer", "minimum": 1}, "description": "Paginanummer (1 bij een gewone afbeelding)"}
OID = {"name": "object_id", "in": "path", "required": True, "schema": {"type": "string"}, "description": "Object-id, bijv. obj-1a2b3c4d5e"}


def _q(name, description, kind="string"):
    return {"name": name, "in": "query", "required": False, "schema": {"type": kind}, "description": description}


PAGE = "/bestand/{mid}/pagina/{n}"
OBJECT = PAGE + "/objecten/{object_id}"
OLD_OBJECT = PAGE + "/object/{object_id}"  # deprecated since 0.29.0, gone in 0.33.0
VERSIE = {"name": "versie", "in": "path", "required": True, "schema": {"type": "string"}, "description": "De versie uit de geschiedenis (een tijd, bijv. 2026-11-04T10:12:03.123+00:00)"}
DEEL = {"name": "deel", "in": "path", "required": True, "schema": {"type": "string", "enum": ["beschrijving", "zoektermen"]}, "description": "Het deel van het paginaoverzicht"}

# (method, path, summary, parameters, request body description, success status, kost geld?)
ENDPOINTS = [
    ("get", "/bestand", "Invoer normaliseren en het bestand ophalen: titel, M-id, afmetingen, MIME, SHA-1, licentie, maker, categorieën, SDC, rechtenlabels, pagina's",
     [_q("url", "Commons-URL (bestandspagina of upload.wikimedia.org)"), _q("titel", "Titel, met of zonder File:"), _q("mid", "M-id")], None, 200, False),
    ("get", "/bestand/{mid}", "Het bestand op M-id", [MID], None, 200, False),
    ("get", PAGE, "Pagina: afmetingen, objecten, aantal regio's uit Commons", [MID, N], None, 200, False),
    ("get", PAGE + "/afbeelding", "Verkleinde afbeelding (Commons-thumbnailstap, gecachet)", [MID, N, _q("w", "Gewenste breedte in pixels", "integer")], None, 200, False),
    ("post", PAGE + "/detecties", "Detectie: zoekterm, modus (prompt, alles, commons), punt, rechthoek of masker_voor",
     [MID, N], '{"prompt", "modus", "minscore"} | {"punt": {x, y}} | {"rechthoek": {x, y, w, h}} | {"masker_voor": id}', 201, True),
    ("get", PAGE + "/detecties/raming", "Kostenraming van een detectie; voert niets uit",
     [MID, N, _q("prompt", "Zoekterm"), _q("modus", "prompt, alles of commons"), _q("minscore", "Laagste score, 0-1")], None, 200, False),
    ("get", PAGE + "/inventaris", "Paginaoverzicht (opgeslagen) en de kosten van een nieuw", [MID, N], None, 200, False),
    ("delete", PAGE + "/inventaris", "Het hele paginaoverzicht verwijderen (gratis)", [MID, N], None, 200, False),
    ("post", PAGE + "/inventaris", "Wat staat op deze pagina? (Muse Spark)", [MID, N], '{"model": "auto|standaard|contributor", "opnieuw": false, "detailniveau": "hoofdonderwerp|hoofdzaken|normaal|details", "beschrijvingsniveau": "kort|normaal|uitgebreid"}', 200, True),
    ("delete", PAGE + "/inventaris/{deel}", "Eén deel van het paginaoverzicht verwijderen (gratis)", [MID, N, DEEL], None, 200, False),
    ("post", PAGE + "/inventaris/{deel}", "Eén deel van het paginaoverzicht opnieuw vragen (Muse Spark; altijd een nieuw antwoord)", [MID, N, DEEL], '{"model": "auto|standaard|contributor", "detailniveau": "hoofdonderwerp|hoofdzaken|normaal|details", "beschrijvingsniveau": "kort|normaal|uitgebreid"}', 200, True),
    ("patch", PAGE + "/inventaris", "De beschrijving van de afbeelding met de hand wijzigen (gratis)", [MID, N], '{"paginasoort", "paginasoort_en", "samenvatting", "samenvatting_en", "tekst"}', 200, False),
    ("get", PAGE + "/inventaris/geschiedenis", "Eerdere beschrijvingen van de afbeelding, nieuwste eerst", [MID, N], None, 200, False),
    ("delete", PAGE + "/inventaris/geschiedenis/{versie}", "Eén eerdere beschrijving van de afbeelding verwijderen (gratis)", [MID, N, VERSIE], None, 200, False),
    ("put", PAGE + "/inventaris/{deel}", "Een eerdere beschrijving van de afbeelding weer de huidige maken (alleen deel = beschrijving; gratis)", [MID, N, DEEL], '{"versie": "…"}', 200, False),
    ("post", PAGE + "/samenvoegingen", "Dubbelingen samenvoegen (gratis)", [MID, N], None, 200, False),
    ("get", OBJECT + "/aanvulling", "De AI-aangevulde versie van de uitsnede en de kosten van een nieuwe (gratis)", [MID, N, OID], None, 200, False),
    ("post", OBJECT + "/aanvulling", "De uitsnede laten aanvullen door Muse Image (betaald; verzonnen, nooit een bron)", [MID, N, OID], '{"opnieuw": false}', 201, True),
    ("delete", OBJECT + "/aanvulling", "De AI-aangevulde versie weghalen (gratis)", [MID, N, OID], None, 200, False),
    ("get", OBJECT + "/aangevuld.png", "De AI-aangevulde versie als PNG", [MID, N, OID], None, 200, False),
    ("get", OBJECT + "/aangevuld-ingevuld.png", "Wat de AI invulde, als doorzichtige laag over de AI-aangevulde versie (bij benadering)", [MID, N, OID], None, 200, False),
    ("post", PAGE + "/groepen", "Objecten groeperen tot één object (gratis)", [MID, N], '{"objecten": [ids], "naam": "…"} | {"zoekterm": "…", "naam": "…"}', 201, False),
    ("delete", PAGE + "/groepen/{object_id}", "Een groep opheffen: de leden komen terug (gratis)", [MID, N, OID], None, 200, False),
    ("get", OBJECT + "/beschrijving/geschiedenis", "Eerdere beschrijvingen van het object, nieuwste eerst", [MID, N, OID], None, 200, False),
    ("delete", OBJECT + "/beschrijving/geschiedenis/{versie}", "Eén eerdere versie verwijderen (gratis)", [MID, N, OID, VERSIE], None, 200, False),
    ("put", OBJECT + "/beschrijving", "Een eerdere versie (AI of met de hand) weer de huidige beschrijving maken (gratis)", [MID, N, OID], '{"versie": "…"}', 200, False),
    ("get", OBJECT + "/beschrijving/invoer.jpg", "Wat de AI-beeldbeschrijving zou zien, met ?marge= (0-1), het kader in rood; ?max= (tot 4000 px) voor een grotere versie", [MID, N, OID, _q("marge", "Ruimte rond het kader, 0-1"), _q("max", "Langste zijde in pixels, 1024-4000")], None, 200, False),
    ("patch", PAGE + "/objecten", "Selectie of status wijzigen", [MID, N], '{"geselecteerd": [ids]} | {"objecten": [{id, status}]} ({"samenvoegen": true} is verouderd: POST …/samenvoegingen)', 200, False),
    ("get", OBJECT, "Eén object (ook in de prullenbak)", [MID, N, OID], None, 200, False),
    ("patch", OBJECT, "Object wijzigen: bijschrift, status, prullenbak", [MID, N, OID], '{"bijschrift": {"tekst"} | null, "status", "prullenbak": bool}', 200, False),
    ("delete", OBJECT, "Object naar de prullenbak", [MID, N, OID], None, 200, False),
    ("get", OBJECT + "/uitsnede.jpg", "De rechthoek als JPG, in volledige resolutie (of een voorbeeld met w)", [MID, N, OID, _q("w", "Breedte van een voorbeeld", "integer")], None, 200, False),
    ("get", OBJECT + "/uitsnede.png", "De vorm van het object als transparante PNG, in volledige resolutie", [MID, N, OID], None, 200, False),
    ("get", OBJECT + "/masker.png", "Het masker (wit is het object)", [MID, N, OID], None, 200, False),
    ("get", OBJECT + "/beschrijving", "Opgeslagen beschrijving en de kosten van een nieuwe", [MID, N, OID], None, 200, False),
    ("post", OBJECT + "/beschrijving", "Wat staat hierop? (Muse Spark)", [MID, N, OID], '{"model": "auto|standaard|contributor", "opnieuw": false, "aanwijzing": "…", "marge": 0.25}', 200, True),
    ("patch", OBJECT + "/beschrijving", "De teksten van de beschrijving met de hand wijzigen", [MID, N, OID], '{"onderwerp", "onderwerp_en", "bedrijf_of_naam", "beschrijving", "beschrijving_en", "tekst_in_beeld", "tekst_rond_beeld"}', 200, False),
    ("delete", OBJECT + "/beschrijving", "Beschrijving vergeten (het antwoord blijft in de cache)", [MID, N, OID], None, 200, False),
    ("get", OBJECT + "/commons", "Het Commons-concept: naam, teksten, licentie, categorieën, beeldt af, rechtenlabel, wikitekst, SDC", [MID, N, OID], None, 200, False),
    ("get", OBJECT + "/commons/weergave", "De wikitekst van het concept zoals Commons hem weergeeft (opgeschoond HTML)", [MID, N, OID], None, 200, False),
    ("patch", OBJECT + "/commons", "Het Commons-concept wijzigen, of terug naar het voorstel", [MID, N, OID], '{"bestandsnaam", "formaat", "beschrijving", "caption", "datum", "maker", "categorieen", "beeldt_af", "image_extracted", "merk_bevestigd", "gekozen", "sdc_waarden"} | {"herstel": true}', 200, False),
    ("get", PAGE + "/uitsneden", "Opgeslagen uitsneden van een pagina", [MID, N], None, 200, False),
    ("post", PAGE + "/uitsneden", "Uitsneden opslaan (volledige resolutie)", [MID, N], '{"ids": [...]} (standaard: de geselecteerde)', 201, False),
    ("get", "/bestand/{mid}/commons", "Het keuzemenu voor Commons", [MID], None, 200, False),
    ("get", "/bestand/{mid}/commons/controle", "Controle vooraf (alleen lezen op Commons)", [MID, _q("objecten", "pagina:id, gescheiden door komma's; zonder: de aangevinkte")], None, 200, False),
    ("post", "/bestand/{mid}/commons/uploads", "Uploaden (fase 2); vereist login, bevestiging en COMMONS_UPLOAD=aan", [MID], '{"bevestigd": true, "objecten": [...]}', 202, False),
    ("get", "/uploads/{task}", "Voortgang van een upload (fase 2)", [{"name": "task", "in": "path", "required": True, "schema": {"type": "string"}}], None, 200, False),
    ("get", "/bestand/{mid}/export", "Exporteren: zip (met wikitekst per uitsnede) of json", [MID, _q("formaat", "zip of json")], None, 200, False),
    ("get", "/prullenbak", "De prullenbak", [_q("bron", "Bronnen, komma-gescheiden"), _q("mid", "Eén bestand")], None, 200, False),
    ("delete", "/prullenbak", "Prullenbak legen (alles of een lijst)", [], '{"objecten": [{mid, pagina, id}]}', 200, False),
    ("delete", "/prullenbak/{mid}/{n}/{object_id}", "Eén object definitief verwijderen", [MID, N, OID], None, 200, False),
    ("get", "/objecten", "Alle objecten, met filters", [_q("bron", "Bronnen, komma-gescheiden"), _q("mid", "Eén bestand"), _q("opgeslagen", "1 of 0")], None, 200, False),
    ("get", "/wikidata/zoek", "Wikidata-items zoeken voor beeldt af (gratis)", [_q("q", "Zoekterm"), _q("taal", "nl of en")], None, 200, False),
    ("get", "/verbruik", "Verbruikslog", [_q("van", "JJJJ-MM-DD"), _q("tot", "JJJJ-MM-DD")], None, 200, False),
    ("get", "/verbruik/{datum}", "Verbruik van één dag", [{"name": "datum", "in": "path", "required": True, "schema": {"type": "string", "format": "date"}}], None, 200, False),
    ("get", "/status", "Versie, modus, gebruiker, budgetten", [], None, 200, False),
    ("get", "/openapi.json", "Deze beschrijving", [], None, 200, False),
]

# Old paths that still work until 0.33.0 (Deprecation header, Link to the successor).
DEPRECATED = [
    *[(method, OLD_OBJECT + path[len(OBJECT):], summary, parameters, body, status, paid)
      for method, path, summary, parameters, body, status, paid in ENDPOINTS
      if path.startswith(OBJECT) and (method, path) not in {("put", OBJECT + "/beschrijving"), ("delete", OBJECT + "/beschrijving/geschiedenis/{versie}")}
      and not path.startswith((OBJECT + "/aanvulling", OBJECT + "/aangevuld"))],  # new since 0.32.4: no old path
    ("post", OLD_OBJECT + "/beschrijving/terugzetten", "Verouderd: PUT …/objecten/{object_id}/beschrijving", [MID, N, OID], '{"versie": "…"} | {"tijdstempel": "…", "bewerkt": false}', 200, False),
    ("delete", OLD_OBJECT + "/beschrijving/geschiedenis", "Verouderd: DELETE …/objecten/{object_id}/beschrijving/geschiedenis/{versie}", [MID, N, OID, _q("versie", "De versie uit de geschiedenis")], None, 200, False),
    ("post", "/bestand/{mid}/commons/controle", "Verouderd: GET …/commons/controle?objecten=", [MID], '{"objecten": [{pagina, id}]}', 200, False),
]

ERROR = {
    "type": "object",
    "properties": {"fout": {"type": "string", "description": "Melding in het Nederlands"}, "code": {"type": "string", "description": "Vaste code, door de UI vertaald"}},
    "required": ["fout", "code"],
}


def openapi_spec():
    paths = {}
    for deprecated, (method, path, summary, parameters, body, status, paid) in [(False, e) for e in ENDPOINTS] + [(True, e) for e in DEPRECATED]:
        operation = {
            "summary": summary,
            "parameters": parameters,
            "responses": {
                str(status): {"description": "OK"},
                "4XX": {"description": "Fout", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Fout"}}}},
            },
        }
        if body:
            operation["requestBody"] = {"description": body, "content": {"application/json": {"schema": {"type": "object"}}}}
        if paid:
            operation["description"] = "Kost geld in live-modus (SAM of Muse Spark); vraag eerst de raming op. Gratis met de dummydetector."
        if deprecated:
            operation["deprecated"] = True
            operation["description"] = (operation.get("description", "") + " Verouderd sinds 0.29.0, vervalt in 0.33.0.").strip()
        paths.setdefault(path, {})[method] = operation
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "Commons Mineventory API",
            "version": __version__,
            "description": "Experiment. Geen officiële dienst van de KB of de Wikimedia Foundation. Een GET kost nooit geld en verandert niets.",
            "license": {"name": "MIT"},
        },
        "servers": [{"url": "/api/v1"}],
        "paths": paths,
        "components": {"schemas": {"Fout": ERROR}},
    }
