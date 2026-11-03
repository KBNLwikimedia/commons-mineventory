# Backlog

Werk de items in volgorde af, tenzij Olaf anders zegt. Bron: `docs/functioneel-ontwerp.md`, hoofdstuk 13.

## Fase 0: ontwerp

1. [x] Functioneel ontwerp, repo, open vragen.
2. [ ] Antwoorden van Olaf op de open vragen (FO hoofdstuk 15) verwerken in het FO.
   - Gedaan (3-11-2026): Codex 2.x met Vue 3, gebouwd met Vite, toegangslijst met 100 aanroepen per gebruiker, OAuth server-side, `{{Image extracted}}` standaard aan, bestandsnaam met het onderwerp voorop in het Engels, MIT, regio's uit de gestructureerde gegevens.
   - Gedaan (3-11-2026, ronde 2): naam Commons Cutter (`commons-cutter`), GitHub KBNLwikimedia, daglimieten 500 aanroepen en $2, categorie als invoer in fase 2, gerenderde PDF-pagina's, Contributor aan voor publiek domein, meteen tweetalig, volgcategorie en projectpagina, leesbaar verbruikslog, eigen icoon, data-URL, API-sleutel in fase 4.
   - Gedaan (3-11-2026, ronde 3): Olaf is de enige beheerder en staat als enige op de toegangslijst; beheerders, toegangslijst en instellingen gaan via een beheerpaneel in de tool (FO 8.4).
   - Later: of de betaalde Meta-API op Toolforge mag (vóór de deploy).

## Fase 1: lokaal, zonder kosten

3. [x] Skelet overnemen uit de Delpher Uitsnijder: Flask-app, config, cache, `DummyDetector`, `MetaSamDetector` (alleen fixtures), prompts, verbruik, API-conventies, tests.
4. [x] Commons-adapter: invoer normaliseren (URL, titel, M-id), imageinfo, origineel ophalen en cachen, wikitekst, SDC, categorieën, meerpaginabestanden.
5. [x] Licentie en rechtenlabels uit de wikitekst en de SDC (merk, persoonlijkheidsrechten, origineel ter discussie, naamsvermelding verplicht).
6. [x] Frontend-opzet: Vite, Vue 3, Codex 2.x via npm, koppeling Flask–Vite (manifest), Vitest, vertaalbestanden nl/en met taalkeuze. De viewer uit de Delpher Uitsnijder als JS-module. Daarna de UI: header, invoerbalk, viewer, detectiepaneel, vergroter.
7. [x] Detectiemodi: zoekterm, Snel zoeken (Commons-groepen), Aanwijzen, bulk, paginaoverzicht (dummy).
8. [x] Uit Commons: regio's uit de gestructureerde gegevens (P180 met P2677, `pct:` en pixels) als losse objecten, elk apart uit te snijden; optioneel een masker via een SAM-boxprompt; plus bestandsnotities (`{{ImageNote}}`). Testbestand: Book of Hours of Philip of Burgundy - KW76F - folio 283r (13 regio's).
9. [x] Opslaan in volledige resolutie (PNG en JPG), zip, `/objecten`, prullenbak.
10. [x] "Wat staat hierop?" met Commons-context en `wikidata_suggesties` (fixtures).
11. [x] Commons-concept per object, keuzemenu, controle vooraf, proefweergave; nog geen upload.
12. [x] REST-API, OpenAPI, `/docs`, sitemap.
   - Open uit fase 1 (3-11-2026): mobiel als tabbladen (nu stapelen de kolommen), "Openen in CropTool", de opruimtaak voor de bewaartermijnen, `{{Artwork}}`-velden per sjabloon nalopen met Olaf, tegels voor bestanden boven 100 megapixel.

## Fase 2: OAuth, upload naar een testwiki, categorieën

13. [ ] OAuth 2.0 server-side, owner-only consumer voor ontwikkeling.
14. [ ] Upload via de stash, waarschuwingen tonen, SDC, `{{Image extracted}}` op het origineel; eerst op een testwiki.
15. [ ] Beheerpaneel `/beheer` (FO 8.4): beheerders (start: `BEHEERDERS_START`), toegangslijst met aanvragen, daglimieten (100 per gebruiker; 500 aanroepen en $2 per dag in totaal), noodknoppen, modellen, bewaartermijnen, logboek. Opslag: SQLite lokaal, ToolsDB op Toolforge.
15a. [ ] Een categorie als invoer: bladeren door de bestanden van `Category:…`.

## Fase 3: live

16. [ ] SAM en Muse Spark live, alleen na een opdracht van Olaf; kalibratie op albums, prenten en kaarten.
17. [ ] Deploy naar Toolforge (Build Service; de frontend bouwen in de Build Service of in een GitHub Action), publieke OAuth-consumer, privacyverklaring, projectpagina en volgcategorie op Commons.
18. [ ] Eerste echte uploads, door Olaf.

## Fase 4: verdieping

19. [ ] Batch over meerdere bestanden (een hele categorie in één keer).
20. [ ] Regio's terugschrijven naar het origineel (P180 met P2677).
21. [ ] Gadget of menu-item "Openen in de Commons Cutter" op Commons; link "Openen in CropTool" bij geüploade uitsneden.
22. [ ] IIIF-annotaties exporteren.
23. [ ] Meer talen in de interface (translatewiki.net).
24. [ ] Eigen API-sleutel per gebruiker voor scripts.
