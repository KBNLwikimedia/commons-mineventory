# Overdracht – Commons Mineventory

Stand: versie 0.32.4, 6 november 2026. Voor wie (mens of Claude-sessie) het werk overneemt. Lees daarna, in deze volgorde: [CLAUDE.md](../CLAUDE.md), [het functioneel ontwerp](functioneel-ontwerp.md), [de backlog](../BACKLOG.md) en [de changelog](../CHANGELOG.md).

## Waar het staat

- **Naam**: sinds 0.31.0 heet de app *Commons Mineventory* (eerst Commons Cutter), met een eigen logo (een afbeelding met gevonden objecten en een lijst) en de tagline *Detect objects in a Commons image. Find, cut out and describe them with AI.* Sinds 0.31.1 staat in de repo overal de technische naam `commons-mineventory` (URL's, npm-pakket, Toolforge-tool, map). Het Python-package heet bewust nog `cutter/` en de CSS-klassen beginnen nog met `cc-` (backlog 12f).
- **De map is hernoemd** van `D:\KB-OPEN\github-repos\commons-cutter` naar `D:\KB-OPEN\github-repos\commons-mineventory` (Olaf, 5-11-2026, na 0.31.2); `.venv` is opnieuw gemaakt en de tests zijn groen. De repo staat openbaar op [GitHub](https://github.com/KBNLwikimedia/commons-mineventory), ook met CLAUDE.md, deze overdracht en de backlog (besluit Olaf).
- **Fase 1 (lokaal, zonder kosten) is klaar** en sinds 0.9.0 op aanwijzing van Olaf verfijnd. Olaf draait de app zelf in live-modus, met zijn eigen sleutel voor de Meta Model API.
- **Fase 2 (OAuth, upload naar een testwiki, beheerpaneel) is nog niet begonnen.** Uploaden en inloggen zijn knoppen zonder werking.
- Tests: 262 in Python (`pytest`), 40 in de frontend (`npm test`). Alle groen bij 0.32.4.

## De interface in het kort

Van links naar rechts, in de volgorde van het werk (sinds 0.29.0):

| Kolom | Wat | Bestanden |
| --- | --- | --- |
| **Bekeken** | geopende afbeeldingen met miniatuur; daaronder **Opzij gezet** (inklapbaar, slepen of prullenbakje; pijl omhoog zet terug) | `ViewedPanel.vue`, `HistoryList.vue`, `state.js` |
| **Beeld** | de viewer (gewone JS, niet herschrijven in Vue) met zoom, Maskers/Kaders/Namen | `ViewerPane.vue`, `viewer/viewer.js` |
| **Objecten zoeken** | AI-suggesties (beschrijving en zoektermen, elk apart opnieuw of weg; beschrijving met de hand aan te passen, met versies), Uit Commons, Zoeken, Aanwijzen of tekenen, CropTool | `DetectionPanel.vue`, `PageDescription.vue` |
| **Wat je vond** | de objecten (genummerd: *man 1*, *man 2*; *beschreven* bij een object met een beschrijving), onderaan Geselecteerde objecten beschrijven (met een regel over wat de knop doet), Dubbelingen samenvoegen (de uitkomst als melding direct onder de knoppen, rood of groen, met een X), Selectie opslaan, zip, Naar Commons, en daaronder *Bewaartermijnen* | `ObjectList.vue`, `CutterApp.vue` |

- Elke kolom schuift in tot een strook (`ColumnHeader.vue`, `ColumnStrip.vue`) en heeft een kop met uitleg en een (i).
- De **vergroter** (`Magnifier.vue`) heeft Vorige/Volgende (ook ← →), slaat een niet-opgeslagen bijschrift vanzelf op, en blijft open na *Naar de prullenbak*.
- **Object en uitsnede**: een object is gevonden gegevens, een uitsnede het opgeslagen beeldbestand. Zie *Begrippen* in het functioneel ontwerp.

## Afspraken die je niet uit de code haalt

- **Uitleg en AI-resultaat zien er anders uit**: uitleg is klein en grijs (`cc-uitleg`), wat de AI zei staat in een kader (`cc-ai-resultaat`), een uitkomst (gevonden, niets gevonden) als Codex-melding onder de knop die erom vroeg.
- **Knoppen met kosten** dragen het bedrag; elke betaalde actie vraagt eerst om bevestiging. Een knop zonder iets te doen is uitgeschakeld (niet verborgen).
- **Tweetalig**: alle tekst in `frontend/i18n/nl.json` en `en.json`, dezelfde sleutels en invulplekken. Foutmeldingen: in het Nederlands de eigen melding van de server, in het Engels de vertaling van de code (`error.<code>`); een nieuwe foutcode krijgt dus altijd een vertaling. Tekst die de server meestuurt (rechtenredenen, controle vooraf, niet-ondersteunde bestanden) gaat als code met detail mee, niet als Nederlandse zin.
- **REST**: zelfstandige naamwoorden, meervoud voor lijsten (`…/objecten/{id}`), geen werkwoorden in paden; een GET kost nooit geld en verandert niets. De oude paden van vóór 0.29.0 werken nog tot 0.33.0 (`Deprecation`-kop) en gaan dan weg (backlog 12e). OpenAPI (`cutter/openapi.py`) en `docs/api.md` lopen gelijk met de routes; een test controleert dat.
- **Gegevens van Olaf**: test op zijn server nooit een betaalde knop (Zoeken, Aanwijzen, Beschrijf, Opnieuw, Transparante PNG maken). Wat je wél test, zet je terug (ongedaan maken, versie terugzetten, testversies verwijderen).

## Na het hernoemen van de map

Gedaan op 5-11-2026: stap 1, 3 en 4 (de code staat sinds 0.31.3 op GitHub); stap 2 doet Olaf. Voor de geschiedenis:

Een Claude-sessie hoort bij het mappad; begin na het hernoemen een nieuwe sessie in de nieuwe map (het Claude-geheugen van de oude map was leeg, er gaat niets verloren). Daarna, in deze volgorde:

1. **Python-omgeving opnieuw maken**: `.venv` bevat vaste paden naar de oude map. Verwijder `.venv`, maak hem opnieuw (`py -3.14 -m venv .venv`) en installeer (`.venv\Scripts\pip install -r requirements.txt`). `node_modules` werkt gewoon door.
2. **`.env` bijwerken** (Olaf; Claude leest `.env` nooit): `BRONCODE_URL` en de URL in `COMMONS_USER_AGENT` naar `https://github.com/KBNLwikimedia/commons-mineventory`. De User-Agent zonder spatie in de naam: `CommonsMineventory/0.1 (…)`.
3. **Controleren**: `git -c safe.directory=D:/KB-OPEN/github-repos/commons-mineventory status`, `pytest`, `npm test`, en de app starten (`flask --app app run --debug` en `npm run dev`).
4. **GitHub** (Olaf, maakt de repo openbaar): `gh repo create KBNLwikimedia/commons-mineventory --public --source . --push`. Op 5-11-2026 was die naam nog vrij.
5. Daarna backlog 12f afvinken. De Toolforge-naam wordt pas bij de deploy (17) nagekeken.

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
- **Projectsite (GitHub Pages)**: documentatie en uitleg, niet de app (die komt op Toolforge). Bronnen in `site/` (`index.html`, `docs.css`, `build.py`); de Action `.github/workflows/pages.yml` bouwt bij een push naar `main` die `site/`, `docs/`, BACKLOG.md of CHANGELOG.md raakt. Een nieuw document voeg je toe aan `DOCS` in `site/build.py`; nieuwe schermafbeeldingen aan `docs/screenshots/` en aan `SLIDES` in `site/index.html` (met bijschrift in beide talen). Op Windows kan de indexer `_site/` vergrendelen; bouw dan naar een andere map (`python site/build.py <map>`).

## Wat openstaat

- **Olaf**: `.env` bijwerken (`BRONCODE_URL`, de URL in `COMMONS_USER_AGENT`) en de lege oude map `commons-cutter` verwijderen. Daarmee is backlog 12f af, op de Toolforge-naam na.
- **Een terminal starten**: Flask staat alleen in `.venv`. Zet de omgeving aan met `.venv\Scripts\Activate.ps1`, of start met `.venv\Scripts\flask --app app run --debug`.
- **Volgende bouw**: het dashboard met collecties (backlog 15a, FO 17), nu al, vóór OAuth, onder de gebruiker `lokaal`, zonder voorscan door AI. Volgorde in FO 17.9, stap 1 tot en met 4; Olafs besluiten in FO 17.10.
- **Starttegoed** (backlog 15c, FO 8.6): besloten (FO 8.6.6), te bouwen na OAuth en de database.
- **Wacht op Olaf**: de vijf vragen bij backlog 15b (venster *Beeldt af en caption voor de hele afbeelding*, FO 9.7).
- **Klein**: backlog 12b (oude paginaoverzichten zonder Engels; nagaan welke SDC-velden Commons-bots zelf zetten) en 12e (verouderde API-paden weghalen in 0.33.0).
- **Fase 2**: OAuth (13) met werk per gebruiker (13a, FO 8.5: eigen uitvoermap per gebruiker, gedeelde cache), upload via de stash op een testwiki (14), beheerpaneel (15), categorie als invoer (15a). Pas daarna kan per gebruiker gescheiden worden (12c).
