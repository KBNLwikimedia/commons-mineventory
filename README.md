# Commons Cutter

Een experimentele webapp om objecten te vinden in afbeeldingen op [Wikimedia Commons](https://commons.wikimedia.org/), ze uit te snijden als transparante PNG of als JPG, ze te laten beschrijven, en de uitsneden na controle weer op Commons te publiceren, met een koppeling naar het origineel. Een verdieping op [CropTool](https://commons.wikimedia.org/wiki/Commons:CropTool): niet één rechthoek met de hand, maar veel objecten tegelijk, gevonden met AI.

De app is afgeleid van de [Delpher Uitsnijder](https://github.com/ookgezellig/delpher-uitsnijder), die hetzelfde doet voor pagina's uit Delpher.

> **Dit is een experiment.** Het is geen officiële dienst van de KB, nationale bibliotheek, of van de Wikimedia Foundation. Aan deze toepassing kunnen geen rechten worden ontleend.

## Status

Ontwerpfase. Er is nog geen code. Het ontwerp staat in [docs/functioneel-ontwerp.md](docs/functioneel-ontwerp.md); de open vragen staan in hoofdstuk 15 daarvan.

## Wat de app gaat doen

- Een Commons-bestand openen via de URL, de titel of de M-id.
- Objecten en maskers detecteren met SAM 3.1 (Meta Model API): zoeken met een zoekterm, Snel zoeken, Aanwijzen, Alles detecteren, Slim detecteren.
- Regio's overnemen die al op Commons staan (de gele rechthoeken van *beeldt af* met positie, en bestandsnotities), gratis, en elke regio als apart bestand uitsnijden.
- "Wat staat hierop?" en "Wat staat op deze pagina?" met Muse Spark.
- Inloggen met je Commons-account (OAuth 2.0).
- Uitsneden uploaden naar Commons, op je eigen naam, na een overzicht en een bevestiging: met `{{Extracted from}}`, de licentie van het origineel, categorieën en gestructureerde gegevens.
- Een tweetalige interface (Nederlands en Engels) in de stijl van Wikimedia, met [Codex](https://doc.wikimedia.org/codex/latest/) en Vue 3, gebouwd met Vite. De server is Python (Flask); Node.js is alleen nodig om de frontend te bouwen.
- Draaien op [Wikimedia Toolforge](https://toolforge.org/).

## Documentatie

- [Functioneel ontwerp](docs/functioneel-ontwerp.md)
- [Backlog](BACKLOG.md)
- [Changelog](CHANGELOG.md)

## Broncode

Komt op GitHub als [KBNLwikimedia/commons-cutter](https://github.com/KBNLwikimedia/commons-cutter) en draait straks als `commons-cutter` op Toolforge.

## Licentie

MIT voor de code. Onderdelen van derden houden hun eigen licentie: Codex (GPL-2.0-or-later), Vue (MIT) en `meta-sam-parser` (SAM License).
