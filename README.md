# Commons Cutter

Een experimentele webapp om objecten te vinden in afbeeldingen op [Wikimedia Commons](https://commons.wikimedia.org/), ze uit te snijden als transparante PNG of als JPG, ze te laten beschrijven, en de uitsneden na controle weer op Commons te publiceren, met een koppeling naar het origineel. Een verdieping op [CropTool](https://commons.wikimedia.org/wiki/Commons:CropTool): niet één rechthoek met de hand, maar veel objecten tegelijk, gevonden met AI.

De app is afgeleid van de [Delpher Uitsnijder](https://github.com/ookgezellig/delpher-uitsnijder), die hetzelfde doet voor pagina's uit Delpher.

> **Dit is een experiment.** Het is geen officiële dienst van de KB, nationale bibliotheek, of van de Wikimedia Foundation. Aan deze toepassing kunnen geen rechten worden ontleend.

## Status

Fase 1 is klaar (versie 0.13.0): alles werkt lokaal behalve inloggen en uploaden. Standaard draait de app met een nagebootste detector en beschrijving (`DETECTIE_MODUS=dummy`, gratis). Met een eigen sleutel van de Meta Model API in `.env` (`MODEL_API_KEY`, `DETECTIE_MODUS=live`) zijn SAM en Muse Spark echt te gebruiken; elke betaalde actie vraagt eerst om bevestiging, met het bedrag. Het ontwerp staat in [docs/functioneel-ontwerp.md](docs/functioneel-ontwerp.md), de API in [docs/api.md](docs/api.md).

## Lokaal draaien

Eenmalig (Python 3.11+ en Node.js):

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
npm install
copy .env.example .env
```

Daarna in twee terminals:

```
flask --app app run --debug
npm run dev
```

en open http://localhost:5000. Zonder `npm run dev` gebruikt Flask de gebouwde bestanden (`npm run build`). Tests: `pytest` en `npm test`.

## Wat de app nu doet

- Een Commons-bestand openen via de URL, de titel of de M-id; ook PDF- en DjVu-pagina's. *Laatst bezocht* onthoudt je bestanden in deze browser.
- Objecten en maskers detecteren met SAM 3.1 (Meta Model API): zoeken met een zoekterm, AI-suggesties voor de afbeelding, Aanwijzen, Alles detecteren, Slim detecteren. Of zelf een rechthoek tekenen (gratis).
- Regio's overnemen die al op Commons staan (de gele rechthoeken van *beeldt af* met positie, en bestandsnotities), gratis, en elke regio als apart bestand uitsnijden.
- "Wat staat hierop?" en "Wat staat op deze pagina?" met Muse Spark, in het Nederlands en het Engels. AI-teksten zijn herkenbaar aan een AI-merkje met uitleg, en met de hand aan te passen (met *Ongedaan maken* en *Terug naar de AI-tekst*).
- Uitsneden opslaan in volledige resolutie, als JPG (rechthoek) of transparante PNG (vorm), los of als zip; een overzicht van alle uitsneden en een prullenbak.
- Een Commons-concept per uitsnede: bestandsnaam, caption en beschrijving (nl/en), datum, maker, licentie, categorieën, *beeldt af* met Wikidata-beschrijvingen, en een proefweergave van de wikitekst en de gestructureerde gegevens zoals Commons ze toont, met een voorbeeld van de regio die het origineel zou krijgen.
- Een tweetalige interface (Nederlands en Engels) in de stijl van Wikimedia, met [Codex](https://doc.wikimedia.org/codex/latest/) en Vue 3, gebouwd met Vite. De server is Python (Flask); Node.js is alleen nodig om de frontend te bouwen.
- Een REST-API onder `/api/v1`, met OpenAPI-beschrijving.

## Wat nog komt

- Inloggen met je Commons-account (OAuth 2.0) en een beheerpaneel (fase 2).
- Uitsneden uploaden naar Commons, op je eigen naam, na een overzicht en een bevestiging: met `{{Extracted from}}`, de licentie van het origineel, categorieën en gestructureerde gegevens; eerst op een testwiki (fase 2).
- Draaien op [Wikimedia Toolforge](https://toolforge.org/) (fase 3).
- Regio's terugschrijven naar het origineel, batches over een categorie, en meer (fase 4; zie de [backlog](BACKLOG.md)).

## Documentatie

- [Functioneel ontwerp](docs/functioneel-ontwerp.md)
- [REST-API](docs/api.md)
- [Privacy (concept)](docs/privacy.md)
- [Backlog](BACKLOG.md)
- [Changelog](CHANGELOG.md)

## Broncode

Komt op GitHub als [KBNLwikimedia/commons-cutter](https://github.com/KBNLwikimedia/commons-cutter) en draait straks als `commons-cutter` op Toolforge.

## Licentie

MIT voor de code. Onderdelen van derden houden hun eigen licentie: Codex (GPL-2.0-or-later), Vue (MIT) en `meta-sam-parser` (SAM License).
