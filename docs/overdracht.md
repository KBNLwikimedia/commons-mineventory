# Overdracht – Commons Mineventory

Stand: versie 0.31.1, 5 november 2026. Voor wie (mens of Claude-sessie) het werk overneemt. Lees daarna, in deze volgorde: [CLAUDE.md](../CLAUDE.md), [het functioneel ontwerp](functioneel-ontwerp.md), [de backlog](../BACKLOG.md) en [de changelog](../CHANGELOG.md).

## Waar het staat

- **Naam**: sinds 0.31.0 heet de app *Commons Mineventory* (eerst Commons Cutter). Sinds 0.31.1 heten ook map, repo, npm-pakket en Toolforge-tool `commons-mineventory`; het Python-package heet nog `cutter/` en de CSS-klassen beginnen nog met `cc-` (bewust, backlog 12f).
- **Fase 1 (lokaal, zonder kosten) is klaar** en sinds 0.9.0 op aanwijzing van Olaf verfijnd. Olaf draait de app zelf in live-modus, met zijn eigen sleutel voor de Meta Model API.
- **Fase 2 (OAuth, upload naar een testwiki, beheerpaneel) is nog niet begonnen.** Uploaden en inloggen zijn knoppen zonder werking.
- Tests: 257 in Python (`pytest`), 40 in de frontend (`npm test`). Alle groen bij 0.31.1.

## De interface in het kort

Van links naar rechts, in de volgorde van het werk (sinds 0.29.0):

| Kolom | Wat | Bestanden |
| --- | --- | --- |
| **Bekeken** | geopende afbeeldingen met miniatuur; daaronder **Opzij gezet** (inklapbaar, slepen of prullenbakje; pijl omhoog zet terug) | `ViewedPanel.vue`, `HistoryList.vue`, `state.js` |
| **Beeld** | de viewer (gewone JS, niet herschrijven in Vue) met zoom, Maskers/Kaders/Namen | `ViewerPane.vue`, `viewer/viewer.js` |
| **Objecten zoeken** | AI-suggesties (beschrijving en zoektermen, elk apart opnieuw of weg; beschrijving met de hand aan te passen, met versies), Uit Commons, Zoeken, Aanwijzen of tekenen, CropTool | `DetectionPanel.vue`, `PageDescription.vue` |
| **Wat je vond** | de objecten (genummerd: *man 1*, *man 2*), onderaan Geselecteerde objecten beschrijven (met een regel over wat de knop doet), Dubbelingen samenvoegen, Selectie opslaan, zip, Naar Commons | `ObjectList.vue`, `CutterApp.vue` |

- Elke kolom schuift in tot een strook (`ColumnHeader.vue`, `ColumnStrip.vue`) en heeft een kop met uitleg en een (i).
- De **vergroter** (`Magnifier.vue`) heeft Vorige/Volgende (ook ← →), slaat een niet-opgeslagen bijschrift vanzelf op, en blijft open na *Naar de prullenbak*.
- **Object en uitsnede**: een object is gevonden gegevens, een uitsnede het opgeslagen beeldbestand. Zie *Begrippen* in het functioneel ontwerp.

## Afspraken die je niet uit de code haalt

- **Uitleg en AI-resultaat zien er anders uit**: uitleg is klein en grijs (`cc-uitleg`), wat de AI zei staat in een kader (`cc-ai-resultaat`), een uitkomst (gevonden, niets gevonden) als Codex-melding onder de knop die erom vroeg.
- **Knoppen met kosten** dragen het bedrag; elke betaalde actie vraagt eerst om bevestiging. Een knop zonder iets te doen is uitgeschakeld (niet verborgen).
- **Tweetalig**: alle tekst in `frontend/i18n/nl.json` en `en.json`, dezelfde sleutels en invulplekken. Foutmeldingen: in het Nederlands de eigen melding van de server, in het Engels de vertaling van de code (`error.<code>`); een nieuwe foutcode krijgt dus altijd een vertaling. Tekst die de server meestuurt (rechtenredenen, controle vooraf, niet-ondersteunde bestanden) gaat als code met detail mee, niet als Nederlandse zin.
- **REST**: zelfstandige naamwoorden, meervoud voor lijsten (`…/objecten/{id}`), geen werkwoorden in paden; een GET kost nooit geld en verandert niets. De oude paden van vóór 0.29.0 werken nog tot 0.32.0 (`Deprecation`-kop) en gaan dan weg (backlog 12e). OpenAPI (`cutter/openapi.py`) en `docs/api.md` lopen gelijk met de routes; een test controleert dat.
- **Gegevens van Olaf**: test op zijn server nooit een betaalde knop (Zoeken, Aanwijzen, Beschrijf, Opnieuw, Transparante PNG maken). Wat je wél test, zet je terug (ongedaan maken, versie terugzetten, testversies verwijderen).

## Werkwijze en valkuilen

- **Betaalde stromen testen zonder kosten**: start een tweede server in dummy-modus met eigen mappen, en ruim die daarna op:

  ```
  DETECTIE_MODUS=dummy CACHE_DIR=<tijdelijk>/cache UITVOER_DIR=<tijdelijk>/uitvoer VITE_DEV=uit flask --app app run --port 5055
  ```

  De dummy vindt altijd iets; "niets gevonden" is daar niet na te bootsen.
- **Teksten verversen**: Olaf draait `npm run dev`; Vite werkt de code live bij, maar de vertalingen zitten in de pagina en komen pas mee na herladen. Een stijlbestand met hetzelfde versienummer kan in de browsercache blijven (Ctrl+F5).
- **Bestanden wijzigen**: grote of meervoudige wijzigingen gingen het betrouwbaarst met een klein Python-script (`.venv/Scripts/python -I script.py`); heredocs in de shell braken op aanhalingstekens.
- **Git**: altijd `git -c safe.directory=D:/KB-OPEN/github-repos/commons-mineventory …`; niet pushen zonder opdracht.
- **Commit-routine**: versie ophogen in `cutter/__init__.py` en `package.json` (dan `npm install --package-lock-only`), README "Fase 1 is klaar (versie …)" en CLAUDE.md "Klaar (stand …)", de Unreleased-sectie van CHANGELOG.md een versie en datum geven, `pytest`, `npm test` en `npm run build` draaien, en de commit afsluiten met de Co-Authored-By-regel.
- Grote antwoorden over loopback worden op Olafs machine soms afgekapt (`ERR_CONNECTION_RESET`); dat ligt niet aan de app.

## Wat openstaat

- **Wacht op Olaf**: de vijf vragen bij backlog 15b (venster *Beeldt af en caption voor de hele afbeelding*, FO 9.7).
- **Klein**: backlog 12b (oude paginaoverzichten zonder Engels; nagaan welke SDC-velden Commons-bots zelf zetten) en 12e (verouderde API-paden weghalen in 0.32.0).
- **Fase 2**: OAuth (13), upload via de stash op een testwiki (14), beheerpaneel (15), categorie als invoer (15a). Pas daarna kan per gebruiker gescheiden worden (12c).
