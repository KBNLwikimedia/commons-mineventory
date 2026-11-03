# CLAUDE.md – Commons Cutter

## Wat is dit
Experimentele Flask-app om objecten in afbeeldingen van Wikimedia Commons te detecteren en uit te snijden met SAM 3.1 via de Meta Model API, ze te laten beschrijven met Muse Spark, en de uitsneden na bevestiging door de gebruiker weer op Commons te publiceren. Een verdieping op CropTool. Afgeleid van de Delpher Uitsnijder (`D:\KB-OPEN\github-repos\delpher-uitsnijder`). Geen officiële dienst van de KB of de Wikimedia Foundation.

## Bron van waarheid
- docs/functioneel-ontwerp.md: lees dit EERST, volledig, voor elke taak.
- Voor wat ongewijzigd uit de Delpher Uitsnijder komt: de docs daar (functioneel-ontwerp.md, api.md, commons-beschrijving.md, beeld-taalmodel.md, meta-sam-api.md). Pas in die repo niets aan.
- BACKLOG.md: werk de items in volgorde af, tenzij Olaf anders zegt.
- Werk na elke afgeronde taak CHANGELOG.md bij (Keep a Changelog, semver).

## Fasering (strikt)
- Fase 1 = lokaal, zonder kosten: Commons-adapter, Codex-UI, DummyDetector, opslaan/export, Commons-concept zonder upload, REST-API.
- GEEN live aanroepen naar de Meta Model API zonder expliciete opdracht van Olaf. MetaSamDetector en de beschrijving alleen testen met fixtures.
- Uploaden naar Commons alleen na een klik en een bevestiging van de gebruiker. Eerst op een testwiki; de eerste echte upload doet Olaf zelf.
- Nooit het origineel op Commons overschrijven.

## Techniek
- Python 3.11+, Flask, requests, Pillow, numpy, meta-sam-parser. Geen zware ML-libs.
- Frontend: Flask rendert de pagina's (Jinja); daarin worden Vue 3-componenten gemount. Build-stap met Vite (Node.js alleen bij ontwikkelen en bouwen; op Toolforge draait alleen Python). Bronnen in frontend/, uitvoer in static/dist/ (niet in git).
- Stijl en componenten: Codex 2.x (Wikimedia-designsysteem) via npm. Geen externe CDN's (privacy op Toolforge).
- De viewer (canvas, zoom, pan, overlays, maskers) is een gewone JS-module zonder Vue, overgenomen uit de Delpher Uitsnijder. Niet herschrijven in Vue.
- Inloggen: OAuth 2.0 van Wikimedia (patroon uit D:\KB-OPEN\github-repos\iiif-manifest-upload-workbench).
- Configuratie: geheimen alleen via omgevingsvariabelen (.env.example bijhouden). Nooit sleutels lezen of committen (MODEL_API_KEY, OAUTH_CLIENT_SECRET, tokens). Instellingen die een beheerder mag wijzigen (toegangslijst, limieten, bewaartermijnen) staan in de database van het beheerpaneel; de omgevingsvariabelen zijn alleen de beginwaarden.
- Alles RESTful onder /api/v1; houd docs/api.md en /api/v1/openapi.json synchroon met de code. Een GET kost nooit geld en verandert niets.
- Commons netjes gebruiken: eigen User-Agent, maxlag=5, caching, ongeveer één verzoek per seconde, één upload tegelijk.
- Uitsneden en uploads altijd in de volledige resolutie van het origineel.

## Taal
- Interface: tweetalig, Nederlands en Engels, via vertaalbestanden (frontend/i18n/nl.json en en.json); geen tekst hard in de code.
- Documentatie: Nederlands. Code, identifiers en commentaar: Engels. Python-package: cutter/.

## Commando's
- Eenmalig: pip install -r requirements.txt en npm install
- Lokaal draaien: flask --app app run --debug, en in een tweede terminal npm run dev
- Frontend bouwen: npm run build
- Tests: pytest en npm test
- Deploy: Toolforge Build Service (zie docs/deploy-toolforge.md, nog te schrijven).

## Werkwijze
- Kleine, afgeronde stappen; na elke stap draaien de tests.
- Vraag Olaf bij twijfel over scope, kosten, rechten of bewerkingen op Commons.
- Commit alleen als Olaf erom vraagt.
- Zet nieuwe ideeën in BACKLOG.md in plaats van ze meteen te bouwen.
