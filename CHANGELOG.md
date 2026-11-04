# Changelog

Alle noemenswaardige wijzigingen in dit project staan in dit bestand.
De opmaak volgt [Keep a Changelog](https://keepachangelog.com/nl/1.1.0/) en het project gebruikt [Semantic Versioning](https://semver.org/lang/nl/).

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

### Documentatie

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
