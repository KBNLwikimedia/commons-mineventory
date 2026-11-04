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
OBJECT = PAGE + "/object/{object_id}"

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
     [MID, N, _q("prompt", "Zoekterm"), _q("modus", "prompt, alles of commons")], None, 200, False),
    ("get", PAGE + "/inventaris", "Paginaoverzicht (opgeslagen) en de kosten van een nieuw", [MID, N], None, 200, False),
    ("post", PAGE + "/inventaris", "Wat staat op deze pagina? (Muse Spark)", [MID, N], '{"model": "auto|standaard|contributor", "opnieuw": false, "aanwijzing": "…", "marge": 0.25}', 200, True),
    ("get", OBJECT + "/beschrijving/geschiedenis", "Eerdere beschrijvingen van het object, nieuwste eerst", [MID, N, OID], None, 200, False),
    ("post", OBJECT + "/beschrijving/terugzetten", "Een eerdere beschrijving weer de huidige maken (gratis)", [MID, N, OID], '{"tijdstempel": "…", "bewerkt": false}', 200, False),
    ("get", OBJECT + "/beschrijving/invoer.jpg", "Wat de AI-beeldbeschrijving zou zien, met ?marge= (0-1), het kader in rood", [MID, N, OID], None, 200, False),
    ("patch", PAGE + "/objecten", "Selectie of status wijzigen, of dubbelingen samenvoegen", [MID, N], '{"geselecteerd": [ids]} | {"objecten": [{id, status}]} | {"samenvoegen": true}', 200, False),
    ("get", OBJECT, "Eén object (ook in de prullenbak)", [MID, N, OID], None, 200, False),
    ("patch", OBJECT, "Object wijzigen: bijschrift, status, prullenbak", [MID, N, OID], '{"bijschrift": {"tekst"} | null, "status", "prullenbak": bool}', 200, False),
    ("delete", OBJECT, "Object naar de prullenbak", [MID, N, OID], None, 200, False),
    ("get", OBJECT + "/uitsnede.jpg", "De rechthoek als JPG, in volledige resolutie (of een voorbeeld met w)", [MID, N, OID, _q("w", "Breedte van een voorbeeld", "integer")], None, 200, False),
    ("get", OBJECT + "/uitsnede.png", "De vorm van het object als transparante PNG, in volledige resolutie", [MID, N, OID], None, 200, False),
    ("get", OBJECT + "/masker.png", "Het masker (wit is het object)", [MID, N, OID], None, 200, False),
    ("get", OBJECT + "/beschrijving", "Opgeslagen beschrijving en de kosten van een nieuwe", [MID, N, OID], None, 200, False),
    ("post", OBJECT + "/beschrijving", "Wat staat hierop? (Muse Spark)", [MID, N, OID], '{"model": "auto|standaard|contributor", "opnieuw": false}', 200, True),
    ("patch", OBJECT + "/beschrijving", "De teksten van de beschrijving met de hand wijzigen", [MID, N, OID], '{"onderwerp", "onderwerp_en", "beschrijving", "beschrijving_en", "tekst_in_beeld", "tekst_rond_beeld"}', 200, False),
    ("delete", OBJECT + "/beschrijving", "Beschrijving vergeten (het antwoord blijft in de cache)", [MID, N, OID], None, 200, False),
    ("get", OBJECT + "/commons", "Het Commons-concept: naam, teksten, licentie, categorieën, beeldt af, rechtenlabel, wikitekst, SDC", [MID, N, OID], None, 200, False),
    ("get", OBJECT + "/commons/weergave", "De wikitekst van het concept zoals Commons hem weergeeft (opgeschoond HTML)", [MID, N, OID], None, 200, False),
    ("patch", OBJECT + "/commons", "Het Commons-concept wijzigen, of terug naar het voorstel", [MID, N, OID], '{"bestandsnaam", "formaat", "beschrijving", "caption", "categorieen", "beeldt_af", …} | {"herstel": true}', 200, False),
    ("get", PAGE + "/uitsneden", "Opgeslagen uitsneden van een pagina", [MID, N], None, 200, False),
    ("post", PAGE + "/uitsneden", "Uitsneden opslaan (volledige resolutie)", [MID, N], '{"ids": [...]} (standaard: de geselecteerde)', 201, False),
    ("get", "/bestand/{mid}/commons", "Het keuzemenu voor Commons", [MID], None, 200, False),
    ("post", "/bestand/{mid}/commons/controle", "Controle vooraf (alleen lezen op Commons)", [MID], '{"objecten": [{pagina, id}]}', 200, False),
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

ERROR = {
    "type": "object",
    "properties": {"fout": {"type": "string", "description": "Melding in het Nederlands"}, "code": {"type": "string", "description": "Vaste code, door de UI vertaald"}},
    "required": ["fout", "code"],
}


def openapi_spec():
    paths = {}
    for method, path, summary, parameters, body, status, paid in ENDPOINTS:
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
        paths.setdefault(path, {})[method] = operation
    return {
        "openapi": "3.1.0",
        "info": {
            "title": "Commons Cutter API",
            "version": __version__,
            "description": "Experiment. Geen officiële dienst van de KB of de Wikimedia Foundation. Een GET kost nooit geld en verandert niets.",
            "license": {"name": "MIT"},
        },
        "servers": [{"url": "/api/v1"}],
        "paths": paths,
        "components": {"schemas": {"Fout": ERROR}},
    }
