# Commons Mineventory

Een experimentele webapp om objecten te vinden in afbeeldingen op [Wikimedia Commons](https://commons.wikimedia.org/), ze uit te snijden als transparante PNG of als JPG, ze te laten beschrijven, en de uitsneden na controle weer op Commons te publiceren, met een koppeling naar het origineel. Een verdieping op [CropTool](https://commons.wikimedia.org/wiki/Commons:CropTool): niet één rechthoek met de hand, maar veel objecten tegelijk, gevonden met AI.

De app is afgeleid van de [Delpher Uitsnijder](https://github.com/ookgezellig/delpher-uitsnijder), die hetzelfde doet voor pagina's uit Delpher.

> **Dit is een experiment.** Het is geen officiële dienst van de KB, nationale bibliotheek, of van de Wikimedia Foundation. Aan deze toepassing kunnen geen rechten worden ontleend.

**Object en uitsnede.** Een *object* is wat er op de afbeelding gevonden is: een kader (soms met de vorm, het masker), een naam, een status en eventueel een beschrijving en een Commons-concept. Het is alleen gegevens, en het wordt bewaard tot de pagina een jaar niet geopend is. Een *uitsnede* is het beeldbestand dat je van een object maakt met *Selectie opslaan*: een JPG van het kader en een PNG van de vorm, in de volledige resolutie van het origineel. Uitsneden worden 30 dagen na het laatste gebruik verwijderd (tenzij ze op Commons staan); het object blijft dan, en opnieuw opslaan maakt de uitsnede opnieuw. Elke uitsnede hoort bij een object; een object heeft pas een uitsnede als je het opslaat. De miniaturen in de lijsten zijn geen uitsneden: die maakt de app telkens even voor het tonen.

## Status

Fase 1 is klaar (versie 0.31.1): alles werkt lokaal behalve inloggen en uploaden. Standaard draait de app met een nagebootste detector en beschrijving (`DETECTIE_MODUS=dummy`, gratis). Met een eigen sleutel van de Meta Model API in `.env` (`MODEL_API_KEY`, `DETECTIE_MODUS=live`) zijn SAM en Muse Spark echt te gebruiken; elke betaalde actie vraagt eerst om bevestiging, met het bedrag. Het ontwerp staat in [docs/functioneel-ontwerp.md](docs/functioneel-ontwerp.md), de API in [docs/api.md](docs/api.md).

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

Opruimen volgens de bewaartermijnen (originelen 7 dagen, uitsneden 30 dagen, detecties en beschrijvingen 1 jaar, telkens vanaf het laatste gebruik): `flask --app app opruimen` telt wat weg zou gaan, `flask --app app opruimen --echt` verwijdert het. Op Toolforge wordt dat een dagelijkse taak.

## Wat de app nu doet

- Een Commons-bestand openen via de URL, de titel of de M-id; ook PDF- en DjVu-pagina's, en originelen boven 100 megapixel (die worden met libvips stuk voor stuk gelezen). Het werkblad heeft vier kolommen in de volgorde van het werk: *Bekeken* (je geopende afbeeldingen, met *Opzij gezet*), *Beeld*, *Objecten zoeken* en *Wat je vond*; elke kolom schuift in tot een strook. Op een telefoon zijn de kolommen tabbladen.
- Objecten en maskers detecteren met SAM 3.1 (Meta Model API): zoeken met een zoekterm, AI-suggesties voor de afbeelding (de aangevinkte zoektermen in één keer), Aanwijzen (ook binnen het kader van een ander object). Of zelf een rechthoek tekenen (gratis) en er later een transparante PNG van laten maken. Na elke actie staat de uitkomst in het paneel.
- Regio's overnemen die al op Commons staan (de gele rechthoeken van *beeldt af* met positie, en bestandsnotities), gratis, en elke regio als apart bestand uitsnijden.
- "Wat staat hierop?" en "Wat staat op deze pagina?" met Muse Spark, in het Nederlands en het Engels, ook met de tekst die in het beeld staat. Van de hele afbeelding zijn beschrijving en zoektermen elk apart opnieuw te vragen of te verwijderen; de beschrijving is met de hand aan te passen en houdt *Eerdere beschrijvingen* bij, net als die van een uitsnede. AI-teksten zijn herkenbaar aan een AI-merkje met uitleg, en per veld met de hand aan te passen (met *Ongedaan maken* en *Terug naar de AI-tekst*), ook in een lightbox naast het grote beeld. Met AI-bijsturing (een aanwijzing, meer ruimte rond de uitsnede) stuur je de volgende vraag bij.
- Uitsneden opslaan in volledige resolutie, als JPG (rechthoek) of transparante PNG (vorm), los of als zip; een overzicht van alle uitsneden en een prullenbak (met *Ongedaan maken*). Bij elke opgeslagen uitsnede staat hoe lang die nog bewaard wordt. De vergroter bladert met *Vorige* en *Volgende* door de objecten.
- Een Commons-concept per uitsnede, te bewerken op een weergave zoals de bestandspagina op Commons: tabbladen *Bestandsinformatie* en *Gestructureerde gegevens*, met *Bewerken* en potloodjes. Bestandsnaam, caption en beschrijving (nl/en), datum, maker, inscripties (`{{Inscription}}`), licentie, categorieën, *beeldt af* (zoeken op Wikidata), de waarden van de overgenomen uitspraken, en een voorbeeld van de regio die het origineel zou krijgen. De velden van `{{Artwork}}`, `{{Book}}`, `{{Photograph}}` en `{{Map}}` volgen docs/artwork-velden.md.
- *Bijsnijden in CropTool* voor het hele bestand.
- Een volledig tweetalige interface (Nederlands en Engels, ook de foutmeldingen en de privacyverklaring) in de stijl van Wikimedia, met [Codex](https://doc.wikimedia.org/codex/latest/) en Vue 3, gebouwd met Vite. De server is Python (Flask); Node.js is alleen nodig om de frontend te bouwen.
- Een RESTful API onder `/api/v1`, met OpenAPI-beschrijving.

## Wat nog komt

- Inloggen met je Commons-account (OAuth 2.0) en een beheerpaneel (fase 2).
- Uitsneden uploaden naar Commons, op je eigen naam, na een overzicht en een bevestiging: met `{{Extracted from}}`, de licentie van het origineel, categorieën en gestructureerde gegevens; eerst op een testwiki (fase 2).
- Draaien op [Wikimedia Toolforge](https://toolforge.org/) (fase 3).
- Regio's terugschrijven naar het origineel, batches over een categorie, en meer (fase 4; zie de [backlog](BACKLOG.md)).

## Documentatie

- [Functioneel ontwerp](docs/functioneel-ontwerp.md)
- [REST-API](docs/api.md)
- [Privacy (concept)](docs/privacy.md), ook [in het Engels](docs/privacy.en.md)
- [Overdracht](docs/overdracht.md): de stand van zaken en de werkwijze, voor wie het werk overneemt
- [Backlog](BACKLOG.md)
- [Changelog](CHANGELOG.md)

## Broncode

Komt op GitHub als [KBNLwikimedia/commons-mineventory](https://github.com/KBNLwikimedia/commons-mineventory) en draait straks als `commons-mineventory` op Toolforge. Tot en met 0.31.0 heette het project *Commons Cutter* (`commons-cutter`); het Python-package heet nog `cutter/`.

## Licentie

MIT voor de code. Onderdelen van derden houden hun eigen licentie: Codex (GPL-2.0-or-later), Vue (MIT) en `meta-sam-parser` (SAM License).
