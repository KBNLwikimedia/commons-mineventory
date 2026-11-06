# Backlog

Werk de items in volgorde af, tenzij Olaf anders zegt. Bron: `docs/functioneel-ontwerp.md`, hoofdstuk 13.

## Fase 0: ontwerp

1. [x] Functioneel ontwerp, repo, open vragen.
2. [x] Antwoorden van Olaf op de open vragen (FO hoofdstuk 15) verwerken in het FO.
   - Gedaan (3-11-2026): Codex 2.x met Vue 3, gebouwd met Vite, toegangslijst met 100 aanroepen per gebruiker, OAuth server-side, `{{Image extracted}}` standaard aan, bestandsnaam met het onderwerp voorop in het Engels, MIT, regio's uit de gestructureerde gegevens.
   - Gedaan (3-11-2026, ronde 2): naam Commons Cutter (`commons-cutter`), GitHub KBNLwikimedia, daglimieten 500 aanroepen en $2, categorie als invoer in fase 2, gerenderde PDF-pagina's, Contributor aan voor publiek domein, meteen tweetalig, volgcategorie en projectpagina, leesbaar verbruikslog, eigen icoon, data-URL, API-sleutel in fase 4.
   - Gedaan (3-11-2026, ronde 3): Olaf is de enige beheerder en staat als enige op de toegangslijst; beheerders, toegangslijst en instellingen gaan via een beheerpaneel in de tool (FO 8.4).
   - De vraag of de betaalde Meta-API op Toolforge mag, staat bij punt 17.

## Fase 1: lokaal, zonder kosten

3. [x] Skelet overnemen uit de Delpher Uitsnijder: Flask-app, config, cache, `DummyDetector`, `MetaSamDetector` (alleen fixtures), prompts, verbruik, API-conventies, tests.
4. [x] Commons-adapter: invoer normaliseren (URL, titel, M-id), imageinfo, origineel ophalen en cachen, wikitekst, SDC, categorieën, meerpaginabestanden.
5. [x] Licentie en rechtenlabels uit de wikitekst en de SDC (merk, persoonlijkheidsrechten, origineel ter discussie, naamsvermelding verplicht).
6. [x] Frontend-opzet: Vite, Vue 3, Codex 2.x via npm, koppeling Flask–Vite (manifest), Vitest, vertaalbestanden nl/en met taalkeuze. De viewer uit de Delpher Uitsnijder als JS-module. Daarna de UI: header, invoerbalk, viewer, detectiepaneel, vergroter.
7. [x] Detectiemodi: zoekterm, Aanwijzen, bulk, paginaoverzicht (dummy). Snel zoeken (vaste Commons-groepen) is in 0.11.0 uit de interface en in 0.21.0 ook uit de API gehaald; de AI-suggesties per afbeelding vervangen het.
8. [x] Uit Commons: regio's uit de gestructureerde gegevens (P180 met P2677, `pct:` en pixels) als losse objecten, elk apart uit te snijden; optioneel een masker via een SAM-boxprompt; plus bestandsnotities (`{{ImageNote}}`). Testbestand: Book of Hours of Philip of Burgundy - KW76F - folio 283r (13 regio's).
9. [x] Opslaan in volledige resolutie (PNG en JPG), zip, `/objecten`, prullenbak.
10. [x] "Wat staat hierop?" met Commons-context en `wikidata_suggesties` (fixtures).
11. [x] Commons-concept per object, keuzemenu, controle vooraf, proefweergave; nog geen upload.
12. [x] REST-API, OpenAPI, `/docs`, sitemap.
   - Gedaan (4-11-2026): "Bijsnijden in CropTool" als uitklapblok in het detectiepaneel (0.18.0; een vooringevuld kader nam CropTool niet over); de opruimtaak voor de bewaartermijnen, `flask --app app opruimen [--echt]` (0.18.0); mobiel als tabbladen Objecten, Beeld, Detectie (0.19.0); de velden van `{{Artwork}}`, `{{Photograph}}`, `{{Book}}` en `{{Map}}` per sjabloon, besloten met Olaf (0.20.0, docs/artwork-velden.md); bij elke opgeslagen uitsnede hoe lang die nog bewaard wordt, en uitsneden uit originelen boven 100 megapixel met libvips (0.21.0). Fase 1 heeft geen blokkerende punten meer; wat klein openstaat, staat bij 12b.
12a. [x] Verfijning op aanwijzing van Olaf (3 en 4-11-2026, versies 0.2.0 tot en met 0.9.0; details in CHANGELOG.md):
   - Live-modus lokaal getest door Olaf, met zijn eigen sleutel.
   - AI-teksten: onderwerp en beschrijving met de hand aan te passen (Ongedaan maken, Terug naar de AI-tekst); AI-merkjes met uitleg (model, score, wat te controleren); soort, zekerheid en paginaoverzicht in beide talen; de modelkeuze in gewone woorden.
   - Bijschrift: prullenbakje en Ongedaan maken in het veld; gaat als hulp mee naar het model; geeft het object zijn naam als er geen AI-beschrijving is.
   - Werkblad: versleepbare kolomranden, miniaturen en hover in de objectenlijst, Rechthoek tekenen, alle knoppen Codex-blauw, prullenbak met bevestiging en Ongedaan maken.
   - Commons-concept: per-veld invulmenu met Ongedaan maken (sinds 0.23.0 bewerken op de weergave zelf), Wikidata-beschrijving bij *beeldt af*, aparte knoppen Downloaden en Bekijken, proefweergave van wikitekst en SDC zoals op Commons (Weergave/Broncode), extra SDC (P31, P1163, P4092, P3575, P2048, P2049), voorbeeld van de regio op het origineel.
12b. [ ] Kleine punten die nog open staan:
   - Bestaande paginaoverzichten van vóór 0.9.0 hebben alleen Nederlands; *Beschrijving opnieuw* (betaald) haalt ook het Engels op.
   - Nagaan of Commons-bots P1163, P4092, P3575, P2048 en P2049 na een upload zelf zetten (FO 16), zodat de upload ze niet dubbel zet.

12c. [x] Open punten uit de code-review (4-11-2026), opgepakt in 0.26.0: budget vooraf geboekt en een grens aan zoektermen; 400 in plaats van 500 bij foute invoer of vreemde Commons-gegevens; atomisch schrijven; cache voor zware gratis verzoeken; één Wikidata-zoeker zonder late antwoorden; timers en observers opgeruimd; vastlopende facetten; minder dubbele code; toegankelijkheid. Wat overblijft:
   - Per gebruiker scheiden (prullenbak, objecten, verbruik) kan pas met OAuth (13, uitgewerkt in 13a en FO 8.5); tot dan zijn verbruikslog en het legen van de hele prullenbak op een server alleen voor de toegangslijst.
   - Opgelost: de opruimtaak schreef zonder het slot van de dienst; sinds 0.27.2 delen de app en de opruimtaak een slot dat ook tussen processen werkt (`cutter/slot.py`). De drie `wbgetentities`-lussen, de samenvoegroutines en `{{Art Photo}}` zijn in 0.27.0 opgelost.
12d. [x] Verfijning op aanwijzing van Olaf (4 en 5-11-2026, versies 0.28.0 tot en met 0.31.0; details in CHANGELOG.md): werk uit Wikidata in Metadata; kolommen in werkvolgorde (Bekeken met Opzij gezet, Beeld, Objecten zoeken, Wat je vond), elk inschuifbaar; RESTful API; AI-suggesties per deel opnieuw of weg, beschrijving van de afbeelding met de hand en met versies, zoektermen aan/uit/omkeren; uitkomst van elke actie in het paneel; Aanwijzen op de vorm in plaats van het kader; vergroter met Vorige/Volgende en automatisch opslaan van het bijschrift; Selectie beschrijven en Samenvoegen onder de objecten; uitleg object/uitsnede; volledige tweetaligheid en Engelse privacyverklaring. Stand en werkwijze staan in docs/overdracht.md.
12e. [ ] De verouderde API-paden van vóór 0.29.0 (`…/object/{id}`, `…/beschrijving/terugzetten`, `…/geschiedenis?versie=`, `samenvoegen` in de PATCH, POST `…/commons/controle`) weghalen in 0.33.0 (0.31.0 werd de nieuwe naam, 0.32.0 de projectsite op GitHub Pages), met de tabel in docs/api.md en `DEPRECATED` in cutter/openapi.py.
12f. [ ] Nieuwe naam *Commons Mineventory* (besluit Olaf 5-11-2026) technisch doorvoeren.
   - [x] In de repo (0.31.1): URL's in `.env.example` en `cutter/config.py`, npm-pakket, CLAUDE.md, README, docs en FO 12.1 heten `commons-mineventory`. `KBNLwikimedia/commons-mineventory` was op 5-11-2026 vrij op GitHub. Het Python-package `cutter/` en de `cc-`-voorvoegsels blijven (intern; hernoemen kost veel voor weinig).
   - [x] Olaf (5-11-2026): de map hernoemd naar `D:\KB-OPEN\github-repos\commons-mineventory` en `.venv` opnieuw gemaakt; pytest en npm test groen. `.env` bijwerken (`BRONCODE_URL`, de URL in `COMMONS_USER_AGENT`) doet Olaf zelf.
   - [x] De GitHub-repo `KBNLwikimedia/commons-mineventory` is openbaar en bevat de code (0.31.3, 5-11-2026), met CLAUDE.md, overdracht en backlog (besluit Olaf); de projectsite staat op https://kbnlwikimedia.github.io/commons-mineventory/ (0.32.0).
   - [ ] Bij de deploy (17): nagaan of `commons-mineventory` vrij is op Toolforge en Toolhub.
12g. [x] **Groeperen** (wens Olaf 5-11-2026, zoals in PowerPoint; uitgewerkt in FO 7.4): bij veel kleine objecten van één soort (bijv. 15 waterdruppels en 9 bladeren op M99521736) maak je er één object van, bijv. *groep waterdruppels*, met één kader om alles heen en de maskers samengevoegd. Een knop *Groeperen (n)* voor de geselecteerde objecten, en per zoekterm *Groepeer alle …* met één klik (besluit Olaf). De leden blijven in de groep bewaard, zodat *Groep opheffen* ze terugzet. Een groep mag als één uitsnede naar Commons (besluit Olaf). Anders dan *Dubbelingen samenvoegen*. Gratis. Gebouwd in 0.32.4; sinds 0.32.6 met een bevestigingsvenster (objecten en een eigen naam) en een AI-prompt die meebeweegt met de ruimte rond de uitsnede. *Groep opheffen* staat in de lijst, nog niet in de vergroter.
12h. [ ] **Tabblad *Wat staat hierop?* opnieuw indelen** (vraag Olaf 6-11-2026): vier subtabbladen *Antwoord*, *AI-prompt en bijsturing*, *Beeldt af (P180)* en *Eerder (n)*, in de volgorde van het werk; het voorbeeld *wat de AI ziet* op een vaste plek. Voorstel en open vragen in [docs/ontwerp-wat-is-dit.md](docs/ontwerp-wat-is-dit.md). **Wacht op Olafs akkoord.**

## Fase 2: OAuth, upload naar een testwiki, categorieën

13. [ ] OAuth 2.0 server-side, owner-only consumer voor ontwikkeling.
13a. [ ] Werk per gebruiker (FO 8.5, besluit Olaf 5-11-2026), samen met 13: eigen uitvoermap per ingelogde gebruiker (`uitvoer/gebruikers/<id>/<mid>/`, id = `sub` uit het OAuth-profiel); de cache en de AI-antwoorden blijven gedeeld. Daarbij: de gebruiker uit de sessie in elke opslagroute (de REST-paden blijven gelijk); een sessiemap voor wie niet is ingelogd (1 dag); een vaste gebruiker `lokaal` zonder OAuth, met een commando dat de bestaande `uitvoer/M…` eenmalig verhuist (tellen, daarna `--echt`); een slot per gebruikersmap; opruimen per map; prullenbak legen en verbruikslog per gebruiker (rest van 12c); de privacyverklaring (NL en EN) bijwerken. Tests: twee gebruikers op dezelfde afbeelding zien elkaars objecten niet, en een verzoek kan geen andere map kiezen. Ruimte per gebruiker en het legen van een map komen in het beheerpaneel (15).
14. [ ] Upload via de stash, waarschuwingen tonen, SDC, `{{Image extracted}}` op het origineel; eerst op een testwiki. Daarbij de regio van de uitsnede op het origineel (P180 met P2677), zoals de proefweergave al toont (FO 9.4), als Olaf dat bij de upload wil.
14a. [ ] Na de upload bij elke uitsnede een link "Openen in CropTool" (FO 9, stap 6): CropTool werkt alleen op bestanden die al op Commons staan, dus pas na de upload.
15. [ ] Beheerpaneel `/beheer` (FO 8.4): beheerders (start: `BEHEERDERS_START`), toegangslijst met aanvragen, daglimieten (100 per gebruiker; 500 aanroepen en $2 per dag in totaal), noodknoppen, modellen, bewaartermijnen, logboek. Opslag: SQLite lokaal, ToolsDB op Toolforge.
15a. [ ] Een categorie als invoer: bladeren door de bestanden van `Category:…`. Uitgewerkt als dashboard met collecties en een werkset in de bewerker (FO 17). Besluiten Olaf 5-11-2026 (FO 17.10): **nu bouwen, vóór OAuth**, dus als eerstvolgende punt; dashboard op `/`, bewerker naar `/bewerken`; met de hand kiezen, voorlopig geen voorscan door AI (19a). Eerste bouw volgens FO 17.9, stap 1 tot en met 4.
15b. [ ] **Venster *Beeldt af en caption voor de hele afbeelding*** (FO 9.7): de AI-caption (stand *Wikidata-caption*) en de zoektermen als P180-kandidaten verzoenen met de captions en P180 die het bestand op Commons al heeft. Besluiten Olaf 6-11-2026 in FO 9.7: per object met positie; bestaande P180 alleen aanvullen (met uitleg: aanpassen doe je op Commons zelf); bij een item zonder positie kiest de gebruiker; bestaande caption standaard *Zelf schrijven* met beide teksten; talen nl, en en de interfacetaal; AI-herkomst alleen in de bewerkingssamenvatting; bestanden met meer pagina's: knop uit.
   - **Nu, vóór OAuth** (wens Olaf): het venster, de Wikidata-zoekopdrachten (gratis, gecachet) en *Concept bewaren* (GET en PUT `…/origineel`).
   - **Fase 2**, na 13 en 14: *Op Commons opslaan* (`wbeditentity` met `baserevid`), eerst op de testwiki.
15c. [ ] Starttegoed (eenmalig 100 aanroepen, SAM of Muse Spark) per ingelogde gebruiker en een eigen Meta-sleutel die altijd voorgaat, *bring your own key* (FO 8.6, wens Olaf 5-11-2026). Na 13 en 15 (OAuth en de database). Sleutel versleuteld (`SLEUTEL_VERSLEUTELING`), alleen schrijven via de API, nooit in logs, antwoorden of bestanden; tests daarop. Besluiten Olaf 5-11-2026 in FO 8.6.6.

## Fase 3: live

16. [ ] SAM en Muse Spark live, alleen na een opdracht van Olaf; kalibratie op albums, prenten en kaarten.
17. [ ] Eerst nagaan of de betaalde Meta-API op Toolforge mag. Deploy naar Toolforge (Build Service; de frontend bouwen in de Build Service of in een GitHub Action), publieke OAuth-consumer, privacyverklaring, projectpagina en volgcategorie op Commons.
18. [ ] Eerste echte uploads, door Olaf. Daarvoor aanmaken (Olaf): Category:Uploaded with Commons Mineventory, Category:Cut-outs from media contributed by Koninklijke Bibliotheek, Category:Cut-outs from media from Delpher.

## Fase 4: verdieping

19. [ ] Batch over meerdere bestanden (een hele categorie in één keer).
19a. [ ] Voorscan met AI voor een collectie (FO 17.5): uitgesteld (besluit Olaf 5-11-2026, te duur bij grote categorieën). Open als hij terugkomt: SAM of ook Muse Spark, automatisch aanvinken of alleen tonen.
19b. [x] **AI-aangevulde versie** (gebouwd in 0.32.4, FO 7.7; live nog niet geprobeerd) van een uitsnede (idee Olaf 5-11-2026): witte plekken in een uitsnede, bijv. waar op de prent iets voor het object stond (de jongen op de rug van de kat), laten invullen door **Muse Image 1.0** (`muse-image-1.0`, `/v1/images/edits`, $0,01 per beeld). Het model **verzint** wat er ontbreekt; het is dus geen bron. Voorwaarden: een aparte, duidelijk gemarkeerde versie naast de echte uitsnede, met een AI-merkje en een bevestiging van het bedrag vooraf; nooit als uitsnede naar Commons (een eventuele upload alleen als AI-gegenereerd beeld, volgens de regels van Commons). Bij het uitwerken nagaan: de resolutie (Muse Image maakt het beeld in zijn eigen resolutie, niet die van het origineel), dat er geen masker is en het model het hele beeld opnieuw tekent, en het zoeken op internet uitzetten (`enable_web_search`, `enable_image_search`).
19c. [ ] **Nice-to-have: 3D-model van een uitsnede** (idee Olaf 6-11-2026, FO 7.8): met **SAM 3D Objects** van Meta via **Runware** (`meta:sam@3d`, beeld + masker + prompt → GLB, $0,005 tot $0,009 per model). Knop met bedrag en bevestiging, eigen tabblad *3D* om te draaien en te zoomen, waarschuwing *achterkant verzonnen*, download als GLB, nooit naar Commons; proefmodus met een nagebootst model. Vraagt een tweede aanbieder: `RUNWARE_API_KEY`, privacyverklaring, verbruikslog en limieten; licentie van SAM 3D en voorwaarden van Runware nalezen.
20. [ ] Regio's terugschrijven naar het origineel (P180 met P2677), ook los van een upload; het voorbeeld per uitsnede staat al in de proefweergave. Valt samen met 15b.
21. [ ] Gadget of menu-item "Openen in de Commons Mineventory" op Commons (de CropTool-link bij geüploade uitsneden is 14a).
22. [ ] IIIF-annotaties exporteren.
23. [ ] Meer talen in de interface (translatewiki.net).
24. [ ] Eigen API-sleutel per gebruiker voor scripts.
25. [ ] **Nice-to-have: Canvas**, een speelveld om uitsneden (origineel of AI-aangevuld), transparante beelden van Commons (o.a. Category:Transparent background en zelf gekozen categorieën) en eigen uploads te combineren tot nieuwe werken, in lagen zoals in Photoshop, met kopiëren, groeperen, ongedaan maken, tekst en achtergrond; meerdere canvassen per gebruiker; export als PNG, JPG, PDF, SVG en projectbestand met automatische bronvermelding; nooit naar Commons. Ontwerp en Olafs antwoorden in FO 18 (6-11-2026). Na 8.5 (werk per gebruiker) en 17 (dashboard).
26. [ ] **Alles uit Commons gebruiken** (FO 7.5, voorstel 6-11-2026, vraag Olaf over Atlas de Wit 1698-pl017): in *Uit Commons* ook de bestaande captions (alleen lezen) en de P180 zonder positie als chips; een klik zoekt het item met SAM (betaald, zoekwoord aanpasbaar) en koppelt het gevonden object meteen aan dat Q-item; positie later toevoegen via 9.7. Bestaande caption en P180 als context voor de AI; AI-zoektermen die al op Commons staan krijgen een merkje.
