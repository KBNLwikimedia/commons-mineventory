# Changelog

Alle noemenswaardige wijzigingen in dit project staan in dit bestand.
De opmaak volgt [Keep a Changelog](https://keepachangelog.com/nl/1.1.0/) en het project gebruikt [Semantic Versioning](https://semver.org/lang/nl/).

## [0.25.0] - 2026-11-04

Uit een kritische review van code en documentatie (4-11-2026).

### Beveiliging

- Zonder `FLASK_SECRET_KEY` gebruikt de app een willekeurige sleutel per proces in plaats van een vaste, en een sessiecookie telt (tot OAuth) niet meer als login. Wie de vaste sleutel kende, kon eerder een cookie met een gebruikersnaam ondertekenen en betaalde aanroepen doen.
- CSRF: verzoeken die iets veranderen of geld kosten (POST, PATCH, DELETE) komen alleen nog van de eigen pagina's van de app (Origin en Sec-Fetch-Site) en moeten JSON zijn. Een andere website kon de browser eerder een betaalde vraag laten doen (code `cross_site`, 403; `not_json`, 415).
- Wikitekst-injectie: vrije tekst in het Commons-concept (AI-teksten, captions, beschrijving, inscripties) staat er nu letterlijk in, met de wikitekens als HTML-entiteit. Tekst als `}}`, `[[Category:…]]`, `{{subst:…}}`, `~~~~` of `__NOINDEX__` kan geen sjabloon, categorie of handtekening meer toevoegen. Sjablonen uit het origineel (zoals `{{Creator:…}}`) blijven werken. Categorienamen worden gecontroleerd.
- De configuratie in de pagina escapet `<`, `>` en `&`, zodat tekst uit de URL het script niet kan afsluiten. Taallinks geven geen Flask-interne parameters (`_external` …) door.
- De opschoner van de Commons-weergave laat geen `position`, `z-index` of `transform` meer door (geen elementen over de app heen) en ziet CSS-escapes.
- Prompt-injectie: de tekst die het paginaoverzicht las, kan de markeringen van zijn eigen blok niet meer bevatten; elk tekstveld van een AI-antwoord is hooguit 4000 tekens.
- Strengere controle van een concept-PATCH (datum, maker, gekozen, talen van caption en beschrijving, `bron`) en van de M-id bij definitief verwijderen.

### Opgelost

- Commons-concept: een wijziging die nog opgeslagen moest worden, kon bij snel wisselen van object op het nieuwe object terechtkomen; nu gaat die naar het juiste object, en herladen gooit geen niet-opgeslagen wijziging meer weg. Dezelfde wijziging wordt niet meer twee keer verstuurd.
- Na Broncode → Weergave stonden de potloodjes en *[bewerken]* er niet meer.
- *Ongedaan maken* na *Naar de prullenbak* zette het object terug in het bestand dat op dat moment open was, niet in het eigen bestand.
- Het paginaoverzicht van een pagina die je net verliet, kon op de nieuwe pagina verschijnen.
- De vergroter wist bij een ander object ook de zoekopdracht en foutmelding van het vorige.

### Verwijderd

- Ongebruikte vertalingen, CSS-regels en code (onder meer een dubbele regel en de Wikidata-beschrijving van het oude formulier).

### Gewijzigd

- Documentatie bijgewerkt tot 0.24.2: README (functies), CLAUDE.md (stand, techniek, beheerpaneel), BACKLOG (nummering, gedane punten, open punten uit de review), functioneel ontwerp, privacyverklaring (wat naar Meta en Wikidata gaat), `.env.example` en de OpenAPI-beschrijving (bodies zoals de code ze leest).

## [0.24.2] - 2026-11-04

### Gewijzigd

- Lightbox: het tekstvak bij *Aanpassen* is zo hoog als de tekst die erin staat (een korte tekst geeft een laag vak), en hooguit zo hoog als het venster; een lange tekst scrolt.

## [0.24.1] - 2026-11-04

### Gewijzigd

- Commons-concept: het potloodje bij *Inscriptions* opent nu een venster op hetzelfde tabblad om *Tekst in het beeld* en *Tekst rond het beeld* te bewerken, in plaats van naar *Wat staat hierop?* te springen. De tekst wordt bij de beschrijving van het object opgeslagen, dus beide tabbladen tonen dezelfde tekst.

## [0.24.0] - 2026-11-04

### Gewijzigd

- Commons-concept, nu net als een bestandspagina op Commons: twee tabbladen, *Bestandsinformatie* en *Gestructureerde gegevens*. Op *Bestandsinformatie* staat bovenaan het kader *Captions* met *Bewerken* rechts, dan de weergave met *[bewerken]* achter de kop Summary (beschrijving, datum en maker in één venster) en bij Licensing de opmerking *van het origineel*; de potloodjes per rij blijven. Daaronder de categorieën. Op *Gestructureerde gegevens* staan de uitspraken, met 'beeldt af' (P180) bovenaan en bewerkbaar, ook als er nog geen item is: zoals op Commons met het zoekveld *Zoek om items toe te voegen*. Op *Gestructureerde gegevens* heeft elke uitspraak die van het origineel komt (auteursrechtenstatus, licentie, maker, datum van creatie, collectie) rechts *Bewerken*, zoals op Commons: je past alleen de waarden aan (een Wikidata-item via zoeken, een datum als 1708, 1708-02 of 1708-02-28, bij de maker ook 'onbekend'), haalt er een weg of voegt er een toe; de kwalificaties van het origineel blijven, nieuwe kwalificaties of bronnen kunnen niet. De feiten van het bestand zelf (type, MIME-type, checksum, grootte, afmetingen) zijn niet te bewerken. Een melding zegt dat verder verfijnen na de upload op Commons zelf gebeurt. API: veld `sdc_waarden` in het concept. Weergave en Broncode staan weer naast elkaar. *Formaat* (JPG/PNG) staat nu rechts naast de bestandsnaam. Per tabblad een knop *Broncode* om de wikitekst of JSON te zien (alleen lezen).

## [0.23.0] - 2026-11-04

### Toegevoegd

- Commons-concept: je bewerkt de uitsnede nu op de Commons-pagina zelf. In de weergave zoals Commons die toont, heeft elke rij die uit het concept komt een potloodje (Description, Title, Date, Author/Maker); dat opent een klein venster met *Opslaan* en *Annuleren*, waarna Commons de weergave opnieuw maakt. Het potloodje bij *Inscriptions* gaat naar *Wat staat hierop?*. De categorieën staan eronder in een balk zoals op Commons, met × om weg te halen, *Terugzetten* en een veld om er een toe te voegen. In de gestructureerde gegevens pas je de captions aan met een potloodje, haal je een 'beeldt af'-item weg met × en zoek je er een bij. Het aparte formulier (Caption, Beschrijving, Datum, Maker, Inscripties, Categorieën, Beeldt af) is weg; bovenaan staan nog Bestandsnaam, Formaat en de rechten. De broncode (wikitekst en JSON) blijft alleen-lezen. Rijen van de informatiesjablonen houden daarvoor hun id (`fileinfotpl_…`) in de opgeschoonde HTML.
- *Voorstellen voor 'beeldt af' (P180)*: het zoekveld geeft suggesties terwijl je typt (na twee letters en een korte pauze): Wikidata-items met Q-nummer en beschrijving. Kies er een en hij komt in *beeldt af* van het Commons-concept. Enter of *Zoeken* toont alle treffers als lijst. De suggesties staan compact (kleine letter, één regel per item), en zolang ze open zijn is er ruimte onder het blok, zodat ze onderaan de vergroter passen.
- Commons-concept: een blok *Inscripties* (na Datum en Maker) toont welke gelezen teksten als `{{Inscription}}` meegaan (type `text` en `caption`) en waar: in `inscriptions` of, bij `{{Information}}` en `{{Book}}`, als extra rij in `other fields`. Met een link naar het sjabloon en naar *Wat staat hierop?* om de tekst aan te passen.
- Staat de muis in het beeld op een object waarvan de rij in de objectenlijst buiten beeld staat, dan scrolt de lijst mee tot die rij zichtbaar is (alleen de lijst, niet de pagina; na een korte pauze, zodat de lijst niet springt als je de muis over het beeld beweegt).

## [0.22.1] - 2026-11-04

### Gewijzigd

- *Wat staat hierop?*: in plaats van één knop *Tekst aanpassen* heeft elk veld een eigen potloodje, achter de tekst: Onderwerp (nl en en samen), Naam, Beschrijving (nl en en samen), Tekst in het beeld en Tekst rond het beeld. Het veld wordt ter plekke bewerkbaar, met *Opslaan* en *Annuleren* (Esc). *Naam* is nu ook met de hand aan te passen (ook via de API). Het tekstvak is meteen even hoog als de tekst, en heeft bij één veld geen extra label. *Ongedaan maken*, *Terug naar de AI-tekst* en *Beschrijving wissen* blijven.
- Het linkje onder het voorbeeld heet nu *groot bekijken, tekst controleren en aanpassen*.
- *Voorstellen voor 'beeldt af' (P180)*: de kop linkt naar P180 op Wikidata, en er is een zoekveld om zelf naar Wikidata-items te zoeken (gratis, alleen lezen). Een gevonden item voeg je met + toe aan *beeldt af* in het Commons-concept. Het blok staat er nu ook als de AI geen voorstellen gaf.

## [0.22.0] - 2026-11-04

### Toegevoegd

- Commons-concept: *Tekst in het beeld* en *Tekst rond het beeld* gaan mee naar Commons in `inscriptions`, met het sjabloon `{{Inscription}}` (type `text` voor de tekst in de uitsnede, `caption` voor de tekst eromheen op het origineel), regelovergangen behouden. `{{Information}}` en `{{Book}}` hebben geen inscriptions-veld; daar wordt het een extra rij *Inscripties* in `other fields`.
- Lightbox: bij *Aanpassen* is het tekstvak bijna zo hoog als het venster en blijft het beeld even groot, zodat je de tekst ernaast kunt blijven lezen. Komt het grote beeld niet binnen, dan staat er een melding met *Opnieuw proberen* in plaats van een gebroken afbeelding.
- Vergroter: in de kop, op alle drie de tabbladen, "Uitsnede uit" met de naam van het origineel als link naar de bestandspagina op Commons.
- Hoofdviewer: een zoomschuif naast de knoppen − en +, van 2 tot 300%. De schuif is logaritmisch, zodat elke stap even groot voelt, ook bij een klein percentage.
- *Wat staat hierop?*: klik op het voorbeeld *wat de AI ziet* (of op *groot bekijken*) voor een lightbox met dat beeld in een veel grotere resolutie (tot 3000 pixels), passend in het venster, op 100%, of met een zoomschuif van 10 tot 400%. Net als in de hoofdviewer zoomt het scrollwiel rond de muis en verplaats je het beeld door te slepen. Beide teksten zijn daar ook met de hand aan te passen (*Aanpassen*, dan *Opslaan* of *Annuleren*), terwijl je naar het beeld kijkt; dat werkt als *Tekst aanpassen* in de vergroter, met *Ongedaan maken* en *Terug naar de AI-tekst*. Ernaast staan *Tekst in het beeld* en *Tekst rond het beeld* die de AI las, zodat je ze op het beeld kunt controleren. De API geeft de grotere versie met `invoer.jpg?max=` (tot 4000 pixels); het model zelf krijgt altijd 1024.

## [0.21.2] - 2026-11-04

### Gewijzigd

- Vergroter, tabblad *Uitsnede*: zolang de uitsnede nog gemaakt wordt (bij een groot origineel kan dat even duren), staat er een voortgangsbalk met de tekst "De uitsnede wordt gemaakt in volledige resolutie…". Ook na het wisselen tussen PNG en JPG. Lukt het laden niet, dan staat er een foutmelding in plaats van een leeg vak.

## [0.21.1] - 2026-11-04

### Gewijzigd

- "Opgeslagen, *nog … dagen*" staat in de objectenlijst en op de pagina *Objecten* in een kleinere letter; de resterende periode staat cursief en vet, zodat die opvalt (in de laatste week in oranje). Zo ook in de vergroter.
- Pagina *Objecten*: onder elk object staat "Uitsnede uit" met de naam van het origineel (zonder "File:"), als link naar de bestandspagina op Commons; zo ook in de prullenbak.

## [0.21.0] - 2026-11-04

### Toegevoegd

- Uitsneden uit originelen boven 100 megapixel (FO 5.4): de app leest zo'n origineel met libvips (`pyvips[binary]`, nieuw in `requirements.txt`) stuk voor stuk, in volledige resolutie, in plaats van het te weigeren. Detecteren gebeurt op de verkleinde versie, zoals altijd. JPEG, PNG en (meerpagina-)TIFF; 16-bits, grijs en CMYK worden 8-bits sRGB. De bestandsregel meldt het bij zo'n groot bestand. Gemeten: een uitsnede uit een JPEG van 150 megapixel piekt op ongeveer 100 MB in plaats van ongeveer 450 MB. Zonder pyvips weigert de app zulke bestanden, zoals voorheen.
- Bij elke opgeslagen uitsnede staat hoe lang die nog bewaard wordt: "opgeslagen, nog 23 dagen" in de objectenlijst en op de pagina *Objecten*, met de datum in de tooltip, en in de laatste week in oranje. In de vergroter staat het onder *Opgeslagen*, met de (i) over de bewaartermijnen. De API geeft het als `opgeslagen.verloopt` en `opgeslagen.laatst_gebruikt`, gerekend zoals de opruimtaak dat doet.

### Verwijderd

- Snel zoeken ook uit de code: de API-modus `categorie`, de twaalf vaste groepen in `cutter/prompts.py`, `snel_zoeken` in de paginaconfiguratie en de vertalingen `quick.*`. De AI-suggesties per afbeelding vervangen het (zie 0.11.0). `docs/api.md`, het FO, de OpenAPI-beschrijving en de backlog zijn bijgewerkt.

## [0.20.0] - 2026-11-04

### Gewijzigd

- Commons-concept, sjabloon van het origineel (besluiten van Olaf, `docs/artwork-velden.md`): een uitsnede is een detail van hetzelfde object. Wat over het object gaat, gaat mee: ook `object type`, `department`, `place of creation`, `place of discovery`, `notes`, en bij KB-prenten `publisher` en `place of publication`. Wat over het hele beeld of de maten gaat, niet: `dimensions`, `depicted people`, `depicted place`, `exhibition history`. Nieuw voor de uitsnede: `depicted part` (nl/en) en `inscriptions` (de tekst in beeld). Uit `other_fields` gaan de rijen over het object mee (bijv. *Binder/bindery*), die over het beeld niet. De velden staan in de volgorde van de documentatie.
- Aliassen uit de documentatie worden herkend (`year`, `publication date`, `technique`, `material`, `size`, `gallery`, `museum`, `id`, en bij `{{Artwork}}` en `{{Photograph}}` `location`), in de spelling van het origineel.
- `{{Map}}` wordt overgenomen zoals `{{Artwork}}`: kaartdatum, drukdatum, plaats, blad en schaal gaan mee, het middelpunt (`latitude`, `longitude`) en de legenda niet. `{{Photograph}}` houdt ook `camera coord`, `{{Book}}` ook `wikisource`.
- Categorieën: een uitsnede van een bestand uit *Media contributed by Koninklijke Bibliotheek* komt in *Cut-outs from media contributed by Koninklijke Bibliotheek*, een uitsnede uit *Media from Delpher* in *Cut-outs from media from Delpher*; de partnercategorie zelf gaat niet mee. Dat loopt via het partnersjabloon in `source`, met de bestaande parameter `category=`: `{{Koninklijke Bibliotheek|category=[[Category:Cut-outs from media contributed by Koninklijke Bibliotheek]]}}` (en zo ook `{{Delpher}}`). De vermelding van de partner blijft dus staan.

### Gewijzigd

- `docs/artwork-velden.md`: per veld van `{{Artwork}}`, `{{Photograph}}` en `{{Book}}` wat het Commons-concept nu doet en een voorstel (overnemen, opnieuw invullen of weglaten), met een steekproef van 596 KB-bestanden op Commons en de besluiten van Olaf.

## [0.19.0] - 2026-11-04

### Toegevoegd

- Op een telefoon (smaller dan 48rem, ongeveer 770 pixels) zijn de drie kolommen tabbladen: *Objecten*, *Beeld* en *Detectie* (FO 10.5), in een balk die bovenaan blijft staan. *Beeld* is het eerste. Op grotere schermen verandert er niets.

### Gewijzigd

- In de uitlegpopups kan tekst vet staan; in *Hoe lang wordt dit bewaard?* staan de termijnen, "geen archief" en "blijft altijd" vet.

## [0.18.0] - 2026-11-04

### Toegevoegd

- Opruimtaak voor de bewaartermijnen (FO 12.1): `flask --app app opruimen` telt wat weg zou gaan, `--echt` verwijdert het. Originelen en de Commons-cache na 7 dagen, niet-geüploade uitsneden en maskers na 30 dagen, detecties en beschrijvingen na 1 jaar, telkens vanaf het laatste gebruik. Het verbruikslog blijft altijd. De app zet bij elk lezen de toegangstijd van het bestand, zodat de termijn vanaf het laatste gebruik telt.
- De bewaartermijnen staan in de interface: een (i) met popup *Hoe lang wordt dit bewaard?* naast het aantal objecten boven *Selectie opslaan*, en op de pagina *Objecten* een regel dat opgeslagen uitsneden na 30 dagen zonder gebruik verdwijnen. De termijnen komen uit de configuratie (`bewaren` in de paginaconfiguratie).

### Gewijzigd

- *Bijsnijden in CropTool* staat niet meer in de vergroter: CropTool nam het kader uit de link niet over en toonde de hele afbeelding. In het detectiepaneel staat nu onderaan een uitklapblok **Bijsnijden in CropTool** (standaard ingeklapt, met uitleg en een info-popup), met een knop die het hele bestand in CropTool opent. Met het logo van CropTool2 (het Codex-icoon *cut*, dat CropTool2 zelf ook gebruikt). Alleen bij afbeeldingen van één pagina.

## [0.17.0] - 2026-11-04

### Toegevoegd

- Staat de muis op een kader in het beeld (of op een rij in de objectenlijst), dan krijgt die rij in de lijst een rand in de kleur van het kader: rood voor geselecteerd, blauw voor gevonden maar niet geselecteerd, en zo verder volgens de kleurenlegenda.

- Vergroter, tabblad *Uitsnede*: link **Bijsnijden in CropTool**, die CropTool opent met het kader van het object al geselecteerd (parameters `title`, `left`, `top`, `width`, `height` uit de README van CropTool). Alleen bij enkele afbeeldingen; bij PDF, DjVu en meerpagina-TIFF niet, omdat het kader daar in pixels van een gerenderde pagina staat.

- *Wat staat hierop?*: de knop *Beschrijf deze afbeelding* staat nu onder *AI-bijsturing*, zodat je eerst bijstuurt en dan vraagt.

## [0.16.0] - 2026-11-04

### Toegevoegd

- AI-suggesties voor deze afbeelding: Muse Spark leest nu ook de tekst in en onder de afbeelding (bijvoorbeeld het rijmpje onder een prent) en neemt die letterlijk over. Die staat onder de samenvatting. Het overzicht heeft versie 3 (veld `tekst`); een bestaand overzicht heeft dat veld niet, *Opnieuw om suggesties vragen* (betaald) haalt het op.
- *Wat staat hierop?*: de tekst die het overzicht in en onder de hele afbeelding las, gaat als context mee naar de beschrijving van elke uitsnede (bijvoorbeeld het rijmpje dat over het plaatje gaat). Muse Spark gebruikt hem om de uitsnede te benoemen en beschrijven, en om tekst in of rond de uitsnede beter te lezen. Een vraag met paginatekst is een andere vraag dan zonder (eigen cache); de beschrijving onthoudt of hij gebruikt is (`paginatekst`).

### Opgelost

- Een object aan- en uitvinken terwijl de muis op de rij in de lijst staat, maakte het masker in het beeld lichter: het object verloor zijn markering "onder de muis" en werd daardoor net als de andere objecten gedimd. De markeringen blijven nu staan, ook als het beeld na het antwoord van de server opnieuw wordt getekend.

## [0.15.0] - 2026-11-04

### Toegevoegd

- Detectiepaneel: naast elke kop (AI-suggesties, Uit Commons, Zoeken, Aanwijzen of tekenen, Bulk-operaties) een info-icoontje dat een popup met uitleg opent: wat het doet, wat het kost en waar je op let.

- Een klein Wikimedia Commons-logo rechts in de kopregel, met een link naar Commons (het logo komt uit Codex en staat in de app zelf; er wordt niets van Wikimedia geladen).

### Gewijzigd

- *Wat staat hierop?*: de uitleg bovenaan heeft een tweede alinea over *AI-bijsturing* (een aanwijzing of meer ruimte rond de uitsnede): je krijgt er een beter resultaat mee, en je kunt het ook meteen instellen, nog voor de eerste vraag.

## [0.14.1] - 2026-11-04

### Gewijzigd

- De bovenkant van de pagina is compacter: het invoerveld en het geopende bestand staan naast elkaar (op een smal scherm onder elkaar), met een kleinere miniatuur. Licentie, rechten en de gegevens van het bestand staan op één regel en *Metadata* is een kleine uitklapregel. Een lege meldingenlijst neemt geen ruimte meer in.

## [0.14.0] - 2026-11-04

### Toegevoegd

- Maskers zijn duidelijker zichtbaar (minder doorzichtig).
- Boven het beeld een uitklapblok *Kleurenlegenda* (standaard ingeklapt, alleen als *Kaders* aan staat, en alleen met de kleuren die op de pagina voorkomen): geselecteerd, gevonden maar niet geselecteerd, nieuw (uit de laatste zoekactie), regio die al op Commons staat, met de hand getekende rechthoek, uitgesloten, en dikker voor gekozen of onder de muis. De tooltip van een nieuw object zegt "nieuw".
- In de balk boven het beeld drie vinkjes, zoals in de Delpher Uitsnijder: **Maskers** (de vorm van elk object), **Kaders** (de rechthoeken; verborgen blijven ze aanklikbaar) en **Namen**. De keuze wordt in deze browser onthouden. **Namen** zet de naam van elk object boven zijn kader (de score staat in de tooltip), in de kleur van dat kader. Regio's van Commons hebben hun naam altijd.

### Gewijzigd

- Detectiepaneel: *AI-suggesties voor deze afbeelding* staat nu bovenaan, als eerste optie (boven *Uit Commons* en *Zoeken*); *Zoeken* is standaard ingeklapt. *Aanwijzen* en *Rechthoek tekenen* zijn samengevoegd tot één uitklapblok *Aanwijzen of tekenen* (standaard ingeklapt), met beide schakelaars onder elkaar.

## [0.13.2] - 2026-11-04

### Gewijzigd

- Alle uitklapblokken in de app (Codex *Accordion*: het detectiepaneel, de vergroter, de proefweergave, *Laatst bezocht*, …) klappen nu vloeiend open en dicht, eerst versnellend en dan afremmend (0,35 seconde), in plaats van in één keer; niet bij 'minder beweging' in het systeem (`frontend/accordion-motion.js`).
- *Wat staat hierop?*: het voorbeeld van wat de AI ziet vliegt nu boven alles uit naar *AI-bijsturing* en terug, tegelijk met het uit- en inklappen, zodat het onderweg niet wordt afgesneden.

## [0.13.1] - 2026-11-04

### Gewijzigd

- *Wat staat hierop?*: zodra *AI-bijsturing* openklapt, glijdt het voorbeeld van wat de AI ziet vloeiend mee naar dat blok (0,6 seconde, eerst versnellend en dan afremmend, niet bij 'minder beweging' in het systeem), naast de aanwijzing en de schuifregelaar; dichtklappen zet het weer bovenaan.

## [0.13.0] - 2026-11-04

### Gewijzigd

- *Wat staat hierop?* opnieuw ingedeeld, met één vaste volgorde voor de eerste en elke volgende vraag:
  1. rechts bovenaan de uitsnede zoals de AI hem ziet (rood kader, met de gekozen ruimte; ook vóór de eerste vraag); links het antwoord (of vooraf een korte uitleg wat je krijgt, met het bijschrift dat meegaat), met de acties voor dat antwoord op één regel: *Tekst aanpassen*, *Terug naar de AI-tekst*, *Ongedaan maken*, en rechts *Beschrijving wissen*;
  2. één knop om de AI te vragen, met de kosten: de eerste keer de hoofdknop *Beschrijf deze afbeelding*, daarna *Beschrijf deze afbeelding opnieuw*; ernaast staat welke bijsturing meegaat (bijv. "met ruimte 0% · aanwijzing …");
  3. ingeklapt: *AI-bijsturing* (aanwijzing, ruimte, wat de AI ziet; de kop toont de huidige keuze), *Eerdere beschrijvingen*, en *Model, kosten en kwaliteit*. Daartussen de suggesties voor *beeldt af*.

## [0.12.0] - 2026-11-04

### Toegevoegd

- *Wat staat hierop?*: blok **Eerdere beschrijvingen**: elke beschrijving die vervangen werd (door een nieuwe vraag, terugzetten of wissen) blijft bewaard, met tijd, model, aanwijzing en ruimte; ook antwoorden die nog in de cache staan komen erin, zodat varianten van vóór deze versie terug te halen zijn. *Deze gebruiken* zet er een terug (gratis); de huidige gaat dan de lijst in. API: `GET …/beschrijving/geschiedenis` en `POST …/beschrijving/terugzetten`.
- *Wat staat hierop?*: de aanwijzing en de ruimte rond de uitsnede staan samen in een eigen blok **AI-bijsturing**, met de voorbeeldweergave van wat de AI ziet en de knoppen om (opnieuw) te beschrijven (de losse miniatuur van de uitsnede naast de beschrijving is weg); de aanwijzing werkt nu ook bij de eerste vraag.
- *Wat staat hierop?*: *Tekst rond het beeld* en *Tekst in het beeld* zijn nu ook met de hand aan te passen (*Tekst aanpassen*) en met een prullenbakje te verwijderen, met *Ongedaan maken* en *Terug naar de AI-tekst*, net als onderwerp en beschrijving.
- *Wat staat hierop?*: rechts staat nu **wat de AI ziet**: de uitsnede (rood kader) met de ruimte eromheen die naar het model gaat, en een schuifregelaar *Ruimte rond de uitsnede* van 0 tot 100% (standaard 25%). Minder ruimte houdt andere dingen buiten beeld (zoals een tweede kind), meer ruimte geeft context (zoals tekst rond het beeld). Geldt voor de volgende vraag; de gekozen ruimte wordt bewaard bij de beschrijving. API: `marge` in de POST, en `GET …/beschrijving/invoer.jpg?marge=` (gratis).
- *Wat staat hierop?*: een veld *Aanwijzing voor de AI (optioneel)* bij *Beschrijf deze afbeelding opnieuw*, bijvoorbeeld "alleen de jongen". De aanwijzing gaat als aparte opdracht mee in de vraag aan het model (niet als bijschrift, niet naar Commons), wordt bewaard bij de beschrijving en staat in *Model, kosten en kwaliteit*. Een andere aanwijzing is een andere vraag, dus geen antwoord uit de cache. API: `aanwijzing` in de POST.

### Gewijzigd

- *Wat staat hierop?*: de knop *Opnieuw vragen* heet nu *Beschrijf deze afbeelding opnieuw* / *Describe this image again*.

## [0.11.1] - 2026-11-04

### Gewijzigd

- *Opnieuw vragen* bij de AI-suggesties heet nu *Opnieuw om suggesties vragen* / *Ask for suggestions again*. Bij één object in de prullenbak staat er "1 staat in de prullenbak" (was "1 are").

## [0.11.0] - 2026-11-04

### Toegevoegd

- *AI-suggesties voor deze afbeelding*: elke zoekterm toont hoeveel objecten ermee op de afbeelding staan, en een regel eronder telt het op ("12 objecten gevonden met 6 van de 11 zoektermen"), met hoeveel er in de prullenbak staan. De tooltip van een zoekterm noemt verwacht, gevonden en in de prullenbak. De pagina-API geeft daarvoor `prullenbak_termen`.
- Objectenlijst: naast *Alle* en *Geen* nu ook *Omkeren* (selecteert wat niet geselecteerd was, en andersom).

### Gewijzigd

- *Prullenbak legen*: de knop in de bevestiging heet nu *Definitief verwijderen* / *Delete permanently*; bij één object staat er geen "1 objecten" meer.
- De bron *met de hand getekend* heet nu *met de hand getekende rechthoek* / *hand-drawn rectangle* (facet, objectenlijst, vergroter).
- Pagina *Objecten*: de facetten (bron, bestand, alleen opgeslagen) staan in een kolom links, onder elkaar; de knop *Naar de prullenbak* onder elk object is een klein prullenbakje.

### Verwijderd

- Het blok *Snel zoeken* (vaste groepen zoals wapens, portretten, schepen) is weg uit het detectiepaneel: op Commons staan duizenden soorten objecten, dus een vaste lijst klopt voor veel afbeeldingen niet. De *AI-suggesties voor deze afbeelding* (nu standaard open) doen dit per afbeelding. De API-modus `categorie` en *Alles detecteren* blijven bestaan.

### Opgelost

- De tooltip in het beeld toont de AI-beschrijving nu in de taal van de interface (was altijd Nederlands).

## [0.10.0] - 2026-11-04

### Toegevoegd

- De objectenlijst staat op alfabet (bij gelijke naam van boven naar beneden). Namen die vaker voorkomen krijgen in de lijst een nummer (*house 1*, *house 2*); dat nummer staat alleen in de lijst, niet in de vergroter en niet in het Commons-concept.
- *AI-suggesties voor deze afbeelding*: knop **Alle objecten detecteren (n)** zoekt alle voorgestelde termen in één keer met de AI-beelddetectie (één aanroep per term, met de kosten op de knop en een bevestiging vooraf). Dat is nu de hoofdknop; *Opnieuw vragen* staat ernaast.
- Pagina *Objecten*: elk object heeft een knop *Naar de prullenbak*; een nieuw facet *Bestand*; en een knop die alles wat de filters tonen in één keer naar de prullenbak verplaatst (*Getoonde objecten naar de prullenbak (n)*, met bevestiging). Daarna een melding met *Ongedaan maken*.
- De melding *Naar de prullenbak verplaatst* toont welke uitsnede het was: een miniatuur, de naam en de beschrijving (of het bijschrift).

### Opgelost

- *Opnieuw vragen* bij de AI-suggesties stelde de vraag niet opnieuw: de app kreeg steeds het opgeslagen antwoord terug (gratis, maar zonder nieuwe suggesties). Nu stuurt de knop `opnieuw: true` en vraagt hij het model echt opnieuw, na de bevestiging van de kosten. De uitleg eronder zegt dat dat weer geld kost en dat het antwoord op het vorige kan lijken.

## [0.9.1] - 2026-11-04

### Gewijzigd

- README, CLAUDE.md, BACKLOG.md, het functioneel ontwerp (v0.5), `docs/api.md` en `docs/privacy.md` bijgewerkt naar de stand van 0.9.0: bewerkbare AI-teksten, AI-merkjes, de modelkeuze als code, de proefweergave zoals op Commons, de extra SDC en de regio op het origineel als voorbeeld.

## [0.9.0] - 2026-11-04

### Gewijzigd

- Het AI-merkje bij *AI-suggesties voor deze afbeelding* staat nu achter de samenvatting van het AI-paginaoverzicht, in plaats van in de kop.
- *AI-suggesties voor deze afbeelding*: het AI-paginaoverzicht geeft soort en samenvatting nu ook in het Engels (`paginasoort_en`, `samenvatting_en`), schuin onder het Nederlands, zoals in de vergroter. Een bestaand overzicht heeft alleen Nederlands; *Opnieuw vragen* haalt beide talen op (nieuwe cacheversie).
- *Wat staat hierop?*: ook bij *Soort* staat het AI-merkje, met uitleg dat soort en zekerheid door het taalmodel zijn gekozen en dat de zekerheid geen gemeten score is.

## [0.8.0] - 2026-11-04

### Toegevoegd

- *Wat staat hierop?*: een AI-merkje (robot, "AI") bij onderwerp en beschrijving. Een klik opent een venster dat uitlegt dat een taalmodel de tekst schreef, wat er mis kan gaan en wat je moet controleren; ook of de tekst met de hand is aangepast. Hetzelfde merkje staat bij *AI-suggesties voor deze afbeelding* zodra er een AI-paginaoverzicht is, en bij *Bron: AI-beelddetectie* op het tabblad *Uitsnede* (met uitleg over de detectie: vorm, label, de score van dit object, wat je controleert).

### Gewijzigd

- *Wat staat hierop?*: soort en zekerheid (bijv. *tekening*, *hoog*) staan nu in de taal van de interface (*drawing*, *high*). De waarschuwing zegt nu wat je moet controleren: het onderwerp en de beschrijving.
- *Wat staat hierop?*: het blok *Model en kosten* heet nu *Model, kosten en kwaliteit* en bevat de waarschuwing dat een taalmodel zich kan vergissen (stond onder de beschrijving).

## [0.7.0] - 2026-11-04

### Toegevoegd

- Commons-concept, *Proefweergave*: de wikitekst en de gestructureerde gegevens hebben elk een schakelaar **Weergave / Broncode**.
  - *Weergave* van de wikitekst: zo zet Commons hem op de bestandspagina. Commons maakt de HTML (`action=parse`, alleen lezen, gecachet); de server laat alleen veilige tags staan, zonder afbeeldingen, stijlen of scripts, zodat je browser niets van Wikimedia laadt. Alleen opgevraagd als de proefweergave open is. Nieuw: `GET …/object/{id}/commons/weergave`.
  - De gestructureerde gegevens van de uitsnede hebben nu ook *is een* (P31) *digitale afbeelding*, mediatype (P1163, `image/jpeg` of `image/png` naar het formaat), checksum (P4092, SHA-1), grootte (P3575, byte) en hoogte en breedte (P2048/P2049, pixel) van het bestand zoals het geüpload wordt. *Subject has role* (P2868, bijv. *collection highlight*) bij de collectie gaat niet meer mee: dat gaat over het origineel.
  - Nieuw blok *Regio op het origineel*: voorbeeld van wat het origineel bij het uploaden kan krijgen, per *beeldt af*-item een verklaring met de plaats van de uitsnede (P2677 `pct:…`), zoals de regio's op Commons; regio's die het origineel al heeft worden herkend. Dat is een bewerking van het origineel en komt pas in fase 2.
  - Inklapbare blokken (zoals de instelling bij *Collectie*) staan net als op Commons dicht, met *Uitklappen*/*Inklappen*. Het Wikidata-logo en het potloodje (*Edit this at Wikidata*) staan erbij als eigen icoontjes, met de link naar Wikidata; er wordt niets van Wikimedia geladen.
  - *Weergave* van de gestructureerde gegevens: zoals het tabblad *Gestructureerde gegevens* op Commons, met captions, *beeldt af* bovenaan, en elke eigenschap met zijn waarden en kwalificaties, met labels van Wikidata (`sdc_labels` in het concept).

## [0.6.2] - 2026-11-04

### Gewijzigd

- *Model en kosten*: "Contributor-variant" is een link naar Meta's uitleg van de Contributor-modus.
- Commons-concept: de links onder caption en beschrijving (*Bijschrift overnemen*, *Terug naar de AI-beeldbeschrijving*, …) zitten nu in één klein menu (⋯, *Invullen vanuit…*) naast het veld. *Ongedaan maken* staat er alleen direct na zo'n invulling, zolang je het veld nog niet zelf hebt aangepast.
- *Wat staat hierop?*: de knop *Opnieuw tonen (gratis)* is weg; *Terug naar de AI-tekst* doet dat nu, en een gewiste beschrijving komt bij opnieuw vragen gratis uit de cache.
- *Model en kosten* legt in gewone woorden uit waarom een model is gekozen (vrij van auteursrecht, rechtenlabel, …), in het Nederlands en het Engels, in plaats van "auteursrechtstatus Q19652 en een PD-sjabloon". De API geeft daarvoor `reden_code` en `labels` (plan) en `model_reden_code` en `model_reden_labels` (beschrijving).
- Alle knoppen in de app zijn nu blauw (Codex *progressive*), ook de snelzoek- en suggestieknoppen, zoom, de oog-knop en de infoknop. Alleen verwijderen blijft rood; de hoofdactie is gevuld blauw.

## [0.6.1] - 2026-11-04

### Gewijzigd

- In de regel over de live modus zijn de modelnamen links: SAM naar ai.meta.com/sam3, Muse Spark naar het modeloverzicht op dev.meta.ai.
- De knop *Opnieuw vragen* / *Ask again* bij de AI-suggesties is nu blauw en op normale grootte, zodat hij niet lijkt op de voorgestelde zoektermen.
- De uitleg bij *Aanwijzen* noemt Shift-slepen niet meer; tekenen heeft een eigen blok (*Rechthoek tekenen*).
- Het kopje *Suggesties voor deze pagina* heet nu "AI-suggesties voor deze afbeelding" / "AI suggestions for this image".

## [0.6.0] - 2026-11-04

### Toegevoegd

- Een prullenbakje in het veld *Bijschrift* maakt het leeg en haalt het bijschrift direct van het object; "Ongedaan maken" verschijnt dan in hetzelfde veld en zet het terug.

- "Naar de prullenbak" vraagt eerst bevestiging en zegt waar de prullenbak is (pagina Objecten, tabblad Prullenbak); daarna volgt een melding met "Ongedaan maken" en een link naar de prullenbak. `/objecten?tab=prullenbak` opent de prullenbak direct. In de bevestiging zijn "pagina Objecten" en "Prullenbak" links (in een nieuw tabblad).

- Tabblad *Uitsnede*: **Downloaden** (JPG of PNG als bestand, met de naam uit het Commons-concept) en **Bekijken** (in een nieuw tabblad) zijn nu aparte knoppen; `?download=1` op de uitsnede-URL levert een bijlage.

- Commons-concept: na "Bijschrift overnemen", "Bijschrift toevoegen aan de beschrijving" of "Terug naar de AI-beeldbeschrijving" staat onder dat veld "Ongedaan maken", ook als de AI-beschrijving intussen is gewist.

- Zonder AI-beschrijving heet een object naar zijn bijschrift (in plaats van het label van de AI-beelddetectie, bijv. "person"), en toont *Wat staat hierop?* het bijschrift met de uitleg dat het als hulp meegaat.

- Commons-concept: elk item bij *Beeldt af* toont zijn korte beschrijving van Wikidata (in de taal van de interface, anders de andere); zonder Nederlandse of Engelse beschrijving staat dat erbij.

- *Wat staat hierop?*: **Tekst aanpassen** maakt onderwerp en beschrijving van de AI-beeldbeschrijving met de hand bewerkbaar, in het Nederlands en het Engels. Na opslaan staat er "Ongedaan maken"; een aangepaste beschrijving krijgt het label "Met de hand aangepast" en "Terug naar de AI-tekst". API: `PATCH …/object/{id}/beschrijving` (gratis); de AI-tekst blijft bewaard in `ai_origineel`.

- De Q-nummers bij *Suggesties voor 'beeldt af'* en bij *Beeldt af* in het Commons-concept zijn links naar het Wikidata-item (nieuw tabblad).

- De knop om een beschrijving te vragen heet nu "Beschrijf deze afbeelding" / "Describe this image" (was "Wat staat hierop?", gelijk aan de naam van het tabblad).

- De namen die de app zelf aan objecten geeft (*klik*, *rechthoek*, *regio*) volgen nu de taal van de interface: in het Engels *pointed-out object*, *rectangle*, *region*. Voorheen bleef "rechthoek" ook in de Engelse interface Nederlands.

- In de objectenlijst staat voor elk object een kleine uitsnede (96 px breed); een klik erop opent de vergroter.

- Objectenlijst: een regel krijgt een andere achtergrond als de muis erboven staat, en ook als de muis boven die uitsnede in het beeld staat.

- De randen tussen de drie kolommen van het werkblad zijn versleepbaar (ook met de pijltjestoetsen); dubbelklikken zet de breedte terug. De breedtes worden in deze browser onthouden.

### Opgelost

- Wijzigingen aan objecten die tegelijk binnenkomen (bijvoorbeeld uit twee vensters) overschreven elkaar soms. Lezen, aanpassen en wegschrijven van een objectbestand is nu één vergrendelde stap.

## [0.5.0] - 2026-11-03

### Toegevoegd

- Commons-concept: onder caption en beschrijving (nl en en) staat "Terug naar de AI-beeldbeschrijving" zodra het veld afwijkt van wat "Wat staat hierop?" gaf; één klik zet die tekst terug.
- *Wat staat hierop?* opnieuw ingedeeld: de kosten staan op de knoppen zelf ("Opnieuw vragen · ± US$ 0,0004", "Opnieuw tonen · gratis"), de voorstellen voor *beeldt af* zijn een eigen blok met een kop, en model, reden en de kosten van deze beschrijving staan onderaan in een apart blok.
- *Wat staat hierop?*: knop "Beschrijving wissen" (met bevestiging); het antwoord blijft in de cache, opnieuw vragen is dan gratis.

## [0.4.0] - 2026-11-03

### Toegevoegd

- Selectiemodus *Rechthoek tekenen* in het detectiepaneel: met een gewone sleepbeweging kies je zelf een uitsnede (gratis), die een eigen object wordt dat je kunt opslaan en naar Commons brengen. Shift-slepen blijft werken; *Aanwijzen* en *Rechthoek tekenen* zetten elkaar uit.

### Gewijzigd

- Commons-concept: links het rechtenlabel, de bestandsnaam en het formaat als Codex-schakelaar (JPG | PNG, met uitleg), rechts het voorbeeld van de uitsnede, met ruimte onder de tabbalk. Hetzelfde voorbeeld staat ook bij *Wat staat hierop?*.
- Een info-knopje bij *Bijschrift* legt uit wat het bijschrift doet en waar het terugkomt.
- Het bijschrift doet nu meer: het staat in de objectenlijst en de tooltip, "Wat staat hierop?" krijgt het als context mee (een ander bijschrift is een nieuwe vraag), en in het Commons-concept neem je het met één klik over als caption of voeg je het toe aan de beschrijving.
- Dezelfde termen als in de Delpher Uitsnijder: *AI-beelddetectie* (SAM), *AI-beeldbeschrijving* ("Wat staat hierop?", Muse Spark) en *AI-paginaoverzicht* ("Wat staat op deze pagina?"); bij een beschrijving staat dat een taalmodel zich kan vergissen.
- Het tabblad *Uitsnede* heeft bij objecten met een masker een schakelaar PNG | JPG: de transparante vorm of de gewone rechthoek.

## [0.3.0] - 2026-11-03

### Toegevoegd

- Datum en maker van het origineel ook als de wikitekst ze leeg laat: uit de gestructureerde gegevens van het bestand, of uit het Wikidata-item van het werk (`|wikidata=` in `{{Book}}`, `{{Artwork}}` …; P577 of P571, en P170, P50 of P110). Een decennium wordt `{{other date|decade|…}}`, een onbekende maker `{{Unknown|author}}`. Het concept toont waar elke waarde vandaan komt; de metadata van het bestand noemen het werk.

### Gewijzigd

- De wikitekst van een uitsnede gebruikt de parameternamen van het sjabloon van het origineel (`{{Book}}`: `|Date=`, `|Author=`), neemt bij `{{Book}}` de gegevens van het boek en de Wikidata-koppeling over, en schrijft de maker uit het concept weg (die ontbrak bij `{{Artwork}}`).
- Het Commons-concept slaat elke wijziging vanzelf op (ook een Wikidata-item dat je via het zoekveld toevoegt; dat ging eerder verloren zonder Opslaan). De knop Opslaan is vervallen.
- De tabbalk van de vergroter blijft staan als je scrolt.
- Paginatitels zijn nu schreefloos en vet, net als de rest van de app en de Codex-componenten (eerder serif zoals Vector 2022).

## [0.2.0] - 2026-11-03

### Toegevoegd

- `LOKALE_GEBRUIKER`: tot er OAuth is, telt deze Commons-gebruiker als ingelogd, zodat live-modus (SAM en Muse Spark) lokaal te testen is. Werkt alleen als Flask in debug-modus draait; de naam staat dan in de header.

### Gewijzigd

- Rechtenlabel "In orde" heet nu "Geen rechtenbezwaren" (Engels: "No rights concerns"). Alle rechtenlabels zijn Codex-chips in dezelfde stijl als de licentie, met de uitleg in een tooltip; de licentiechip is neutraal.
- Bevestigingen (kosten, definitief verwijderen, prullenbak legen) zijn een Codex-dialoog in plaats van het venster van de browser, en liggen boven de vergroter. "Opnieuw tonen" komt uit de cache en vraagt geen bevestiging meer.
- De knop "Terug naar het voorstel" in het Commons-concept heet nu "Automatisch concept terugzetten" en vraagt eerst bevestiging, omdat hij alle eigen wijzigingen weggooit, ook gekozen Wikidata-items.
- *Laatst bezocht*: de app onthoudt (per browser) welke bestanden je hebt geopend, met de pagina. Op de lege startpagina staat de lijst; bij een open bestand bovenaan de linkerkolom. Een startpagina zonder parameters opent het bestand dat het laatst open was.
- Wachten op SAM of Muse Spark toont een voortgangsbalk met de verstreken seconden direct onder de knop waarop je klikte.
- Op elke pagina behalve de startpagina staat een link "Terug naar de Commons Cutter", naar het bestand dat het laatst open was.
- De vergroter is te verplaatsen (titelbalk slepen) en groter of kleiner te maken (aan een rand of hoek trekken); de plek wordt onthouden, dubbelklik op de titelbalk zet hem terug in het midden.
- Het Commons-concept toont bovenaan de uitsnede zoals die naar Commons gaat, als JPG of als transparante PNG.
- Wachten op "Wat staat hierop?" toont een voortgangsbalk met de verstreken seconden.
- Het blok *Uit Commons* in het detectiepaneel verschijnt alleen als Commons voor deze pagina regio's of bestandsnotities heeft.

## [0.1.0] - 2026-11-03

Fase 1: lokaal, zonder kosten (BACKLOG 3 t/m 12).

### Toegevoegd

- Skelet overgenomen uit de Delpher Uitsnijder in het package `cutter/`: Flask-app, configuratie uit omgevingsvariabelen (`.env.example`), bestandscache met verlooptijd, `DummyDetector`, `MetaSamDetector` (alleen getest met fixtures, nu ook met boxprompts), maskers, prompts met EN/MIN, verbruikslog met daglimiet per gebruiker, algemene daglimiet en dagbudget.
- Commons-adapter: invoer normaliseren (bestandspagina, `index.php`, `curid`, upload.wikimedia.org en thumbnails, titel met of zonder `File:`/`Bestand:`, M-id), imageinfo, wikitekst, SDC, categorieën, PDF/DjVu/TIFF met pagina's, origineel één keer ophalen en bewaren. Eigen User-Agent, `maxlag=5`, ongeveer één verzoek per seconde, cache.
- Licentie en rechtenlabels uit wikitekst, extmetadata en SDC: merk, persoonlijkheidsrechten, origineel ter discussie (uploaden uit), alleen in de VS vrij, naamsvermelding verplicht, in orde; publiek domein voor de keuze van het Contributor-model.
- Frontend met Vite, Vue 3 en Codex 2.6 via npm; Flask laadt de bestanden van de Vite-devserver of via het manifest uit `static/dist/`. De viewer uit de Delpher Uitsnijder als gewone JS-module, met Shift-slepen voor een rechthoek. Vitest.
- Tweetalige interface (Nederlands en Engels) uit `frontend/i18n/`, gedeeld door Jinja en Vue; taal via `?uselang=`, de sessie of de browser.
- Detectiemodi met de dummydetector: zoekterm, Snel zoeken met twaalf Commons-groepen, Aanwijzen, Alles detecteren, Slim detecteren, Dubbelingen samenvoegen, paginaoverzicht.
- Uit Commons: de regio's uit *beeldt af* (P180 met P2677, `pct:` en pixels) en de bestandsnotities (`{{ImageNote}}`) als losse, gele objecten; nooit samengevoegd; optioneel een masker via een SAM-boxprompt.
- Opslaan in de volledige resolutie van het origineel (JPG kwaliteit 95, en bij een masker een transparante PNG), zip met `LEESMIJ.txt` en de wikitekst per uitsnede, `/objecten` met facetten en prullenbak.
- "Wat staat hierop?" met de context van Commons, antwoorden in het Nederlands en Engels en `wikidata_suggesties`; gratis Wikidata-zoeken voor *beeldt af*. Alleen dummy en fixtures.
- Commons-concept per object (bestandsnaam met het Engelse onderwerp voorop, hooguit 240 bytes; wikitekst met `{{Extracted from}}`, de licentie van het origineel en de volgcategorie; SDC), keuzemenu op `/commons`, controle vooraf (alleen lezen op Commons) en proefweergave. Geen upload.
- REST-API onder `/api/v1` met OpenAPI, `docs/api.md` op `/docs`, `/privacy` (concept), `/changelog`, `/sitemap`, `robots.txt`.
- Tests: Python met opgenomen Commons-antwoorden (`tests/record_commons.py`) en Vitest voor de frontend.
- Functioneel ontwerp (`docs/functioneel-ontwerp.md`), met de besluiten van Olaf van 3 november 2026 en de open vragen.
- README, CLAUDE.md, BACKLOG en deze changelog.

### Gewijzigd

- De app heet nu **Commons Cutter** (`commons-cutter`), in plaats van Commons Uitsnijder. Tool, repo en map krijgen dezelfde Engelse naam.
- FO v0.4: de tweede ronde besluiten van Olaf (3 november 2026) verwerkt.
- Bewaartermijnen op Toolforge vastgelegd (FO 12.1).
- De rol van de Upload Stash beschreven: alleen een controlestap vóór het publiceren (FO 9.1).
- Ontwerp van het beheerpaneel (FO 8.4): beheerders op Wikimedia-account, toegangslijst met aanvragen, limieten, noodknoppen en een logboek.
