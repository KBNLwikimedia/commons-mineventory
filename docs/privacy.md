# Privacy – Commons Mineventory

*Concept, fase 1. De definitieve verklaring komt vóór de deploy naar Toolforge (fase 3).* [English version](/privacy?uselang=en)

De Commons Mineventory is een experiment. Het is geen officiële dienst van de KB, nationale bibliotheek, of van de Wikimedia Foundation.

## Wat de app van jou verwerkt

- **Zonder login**: niets dat naar jou te herleiden is. De app gebruikt een sessiecookie om je taalkeuze (Nederlands of Engels) te onthouden.
- **Met login (fase 2)**: je Commons-gebruikersnaam en een toegangstoken van Wikimedia (OAuth 2.0). Het token staat alleen op de server, in een server-side sessie, en nooit in je browser.
- **Verbruikslog**: bij elke betaalde aanroep (SAM of Muse Spark) legt de app vast wanneer, voor welk bestand en door welke Commons-gebruiker. Dit log is alleen zichtbaar voor gebruikers op de toegangslijst en voor beheerders.

## Wat naar derden gaat

- **Wikimedia Commons en Wikidata**: de server haalt bestanden en gegevens op; jouw browser laadt alleen bestanden van de tool zelf. Voor de proefweergave laat de server Commons de wikitekst van een concept renderen; je browser krijgt alleen opgeschoonde HTML, zonder afbeeldingen, stijlen of scripts van Wikimedia.
- **Wikidata-zoeken**: zoektermen voor *beeldt af* gaan via de server naar Wikidata (`wbsearchentities`), niet vanuit je browser.
- **Meta Model API** (alleen in live-modus): de server stuurt een verkleinde versie van het openbare Commons-bestand (voor SAM hooguit 1920 px breed) of een uitsnede (hooguit 1024 px) naar Meta, met de context van de bestandspagina (beschrijving, categorieën), de tekst die het model eerder in de afbeelding las, je zoektermen, en wat je zelf invult als bijschrift of aanwijzing. Nooit gegevens over jou als persoon.
- **Geen externe scripts, lettertypen of CDN's**: alles wat je browser laadt, komt van de tool zelf. Zo lekt je IP-adres niet naar derden, zoals de gebruiksvoorwaarden van Toolforge vragen.

## In je browser bewaard

Dit staat in de opslag van je eigen browser (localStorage), niet op de server, en verdwijnt als je die opslag wist:

- de lijst *Bekeken* (de afbeeldingen die je opende) en wat je daarvan *Opzij gezet* hebt;
- welke kolommen je hebt ingeschoven en hoe breed ze zijn;
- de keuze voor Maskers, Kaders en Namen, en de plaats en grootte van de vergroter;
- welke zoektermen je hebt uitgezet voor *Alle objecten detecteren*, en welke kopjes open of dicht staan.

## Bewaren op de server

Originelen 7 dagen, uitsneden die nog niet zijn geüpload 30 dagen, detecties en beschrijvingen 1 jaar, telkens vanaf het laatste gebruik (functioneel ontwerp 12.1). Het verbruikslog blijft.
