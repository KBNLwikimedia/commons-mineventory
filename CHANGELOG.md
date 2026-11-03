# Changelog

Alle noemenswaardige wijzigingen in dit project staan in dit bestand.
De opmaak volgt [Keep a Changelog](https://keepachangelog.com/nl/1.1.0/) en het project gebruikt [Semantic Versioning](https://semver.org/lang/nl/).

## [Unreleased]

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
