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
   - Bestaande paginaoverzichten hebben alleen Nederlands; *Opnieuw vragen* (betaald) haalt ook het Engels op.
   - Nagaan of Commons-bots P1163, P4092, P3575, P2048 en P2049 na een upload zelf zetten (FO 16), zodat de upload ze niet dubbel zet.

12c. [ ] Open punten uit de code-review (4-11-2026; de ernstige zijn in 0.25.0 opgelost):
   - Budget: SAM-aanroepen controleren het dagbudget pas achteraf (kosten 0 bij de check), er is geen grens aan het aantal zoektermen, en parallelle betaalde vragen kunnen het budget samen overschrijden. Vooraf reserveren onder een slot.
   - Vóór de deploy (hoort bij 13 en 15): alle wijzigende endpoints zijn nog globaal (DELETE `/prullenbak` leegt ieders prullenbak; `/verbruik` en `/status` tonen gebruikersnamen). Per gebruiker scheiden zodra OAuth er is.
   - Robuustheid: vreemde Commons-gegevens (een regio met `1.2.3`, een notitie met `dimx=nan`) en foute invoer (NaN in punt of rechthoek, een niet-getal als pagina) geven een 500 in plaats van 400; `objecten.json` niet atomisch geschreven, en de opruimtaak schrijft zonder het slot van de dienst.
   - Zware gratis GET's: `invoer.jpg` decodeert elke keer het hele origineel (geen cache), `history()` doorzoekt de hele cache, het verbruikslog wordt per status meermaals gelezen.
   - Frontend: oude antwoorden van zoekopdrachten kunnen nieuwe overschrijven (Wikidata-zoeken in vier componenten, één `useWikidataLookup()` maken); timers en de ResizeObserver van de viewer worden niet opgeruimd; facetten op de pagina Objecten kunnen vastlopen als een gekozen waarde verdwijnt.
   - Dubbel werk opruimen: Wikidata-zoeken (4×), tekstvak-hoogte, laad- en Opslaan/Annuleren-blokken, `savedLabel`-opmaak, de prijs van een SAM-aanroep (4×), drie `wbgetentities`-lussen, `output_text` dubbel, drie samenvoegroutines; `{{Art Photo}}` valt terug op `{{Information}}`.
   - Toegankelijkheid: iconknoppen per rij met de naam van het object, `aria-current="page"`, tabbladen op de telefoon met pijltjestoetsen en `role="tabpanel"`.

## Fase 2: OAuth, upload naar een testwiki, categorieën

13. [ ] OAuth 2.0 server-side, owner-only consumer voor ontwikkeling.
14. [ ] Upload via de stash, waarschuwingen tonen, SDC, `{{Image extracted}}` op het origineel; eerst op een testwiki. Daarbij de regio van de uitsnede op het origineel (P180 met P2677), zoals de proefweergave al toont (FO 9.4), als Olaf dat bij de upload wil.
14a. [ ] Na de upload bij elke uitsnede een link "Openen in CropTool" (FO 9, stap 6): CropTool werkt alleen op bestanden die al op Commons staan, dus pas na de upload.
15. [ ] Beheerpaneel `/beheer` (FO 8.4): beheerders (start: `BEHEERDERS_START`), toegangslijst met aanvragen, daglimieten (100 per gebruiker; 500 aanroepen en $2 per dag in totaal), noodknoppen, modellen, bewaartermijnen, logboek. Opslag: SQLite lokaal, ToolsDB op Toolforge.
15a. [ ] Een categorie als invoer: bladeren door de bestanden van `Category:…`.

## Fase 3: live

16. [ ] SAM en Muse Spark live, alleen na een opdracht van Olaf; kalibratie op albums, prenten en kaarten.
17. [ ] Eerst nagaan of de betaalde Meta-API op Toolforge mag. Deploy naar Toolforge (Build Service; de frontend bouwen in de Build Service of in een GitHub Action), publieke OAuth-consumer, privacyverklaring, projectpagina en volgcategorie op Commons.
18. [ ] Eerste echte uploads, door Olaf. Daarvoor aanmaken (Olaf): Category:Uploaded with Commons Cutter, Category:Cut-outs from media contributed by Koninklijke Bibliotheek, Category:Cut-outs from media from Delpher.

## Fase 4: verdieping

19. [ ] Batch over meerdere bestanden (een hele categorie in één keer).
20. [ ] Regio's terugschrijven naar het origineel (P180 met P2677), ook los van een upload; het voorbeeld per uitsnede staat al in de proefweergave.
21. [ ] Gadget of menu-item "Openen in de Commons Cutter" op Commons (de CropTool-link bij geüploade uitsneden is 14a).
22. [ ] IIIF-annotaties exporteren.
23. [ ] Meer talen in de interface (translatewiki.net).
24. [ ] Eigen API-sleutel per gebruiker voor scripts.
