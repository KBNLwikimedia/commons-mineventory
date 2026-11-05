# Functioneel ontwerp – Commons Mineventory

Naam: **Commons Mineventory** (besluit Olaf 5-11-2026; *mine* + *inventory*: een inventaris van wat er in een afbeelding staat, gedolven met AI; tot en met 0.30.1 heette de app *Commons Cutter*, besluit 3-11-2026). Tagline: *Detect objects in a Commons image. Find, cut out and describe them with AI.* Tool, repo en map heten sinds 0.31.1 `commons-mineventory`; het Python-package heet nog `cutter/` (backlog 12f). Status: concept v0.8, 5 november 2026 (v0.8: bijgewerkt tot app-versie 0.30.1: Begrippen, kolommen in werkvolgorde (10.4), bulk onder de objecten (7.4), paginaoverzicht per deel (7.6); de stand van zaken staat in docs/overdracht.md; v0.7: voorstel 9.7, *beeldt af* en caption voor de hele afbeelding; v0.6: bijgewerkt tot app-versie 0.24.2; zie CHANGELOG.md voor alles wat sinds 0.9.0 gebouwd is; v0.5: bijgewerkt naar wat er in fase 1 is gebouwd, app-versie 0.9.0: bewerkbare AI-teksten, AI-merkjes, proefweergave zoals op Commons, extra SDC, regio op het origineel als voorbeeld; v0.2: antwoorden van Olaf op de belangrijkste vragen verwerkt, en de regio's uit de gestructureerde gegevens uitgewerkt in 7.5; v0.3: frontend met Vite, zie 10.2; v0.4: tweede ronde antwoorden en de naam Commons Cutter). Opdrachtgever en eigenaar: Olaf Janssen (KB, Wikimedia-coördinator). Bouw: Claude Code, op basis van dit document.

Dit FO beschrijft een variant van de [Delpher Uitsnijder](https://github.com/ookgezellig/delpher-uitsnijder) (versie 0.18.13, lokaal in `D:\KB-OPEN\github-repos\delpher-uitsnijder`) voor afbeeldingen op Wikimedia Commons. Waar dit document "de Delpher Uitsnijder" zegt, gaat het om die app: haar FO, `docs/api.md`, `docs/commons-beschrijving.md`, `docs/beeld-taalmodel.md` en `docs/meta-sam-api.md`. Die documenten blijven de bron voor alles wat ongewijzigd wordt overgenomen. Dit FO beschrijft vooral wat anders is.

Punten met **[Vraag]** wachten op een keuze van Olaf; ze staan ook in hoofdstuk 15. Wat Olaf heeft besloten, staat bij het onderwerp en in de tabel in hoofdstuk 15.

## Begrippen

**Object en uitsnede.** Een *object* is wat er op de afbeelding gevonden is: een kader (soms met de vorm, het masker), een naam, een status en eventueel een beschrijving en een Commons-concept. Het is alleen gegevens, en het wordt bewaard tot de pagina een jaar niet geopend is. Een *uitsnede* is het beeldbestand dat je van een object maakt met *Selectie opslaan*: een JPG van het kader en een PNG van de vorm, in de volledige resolutie van het origineel. Uitsneden worden 30 dagen na het laatste gebruik verwijderd (tenzij ze op Commons staan); het object blijft dan, en opnieuw opslaan maakt de uitsnede opnieuw. Elke uitsnede hoort bij een object; een object heeft pas een uitsnede als je het opslaat. De miniaturen in de lijsten zijn geen uitsneden: die maakt de app telkens even voor het tonen. In de interface staat dit ook bij *Wat je vond*, de bewaartermijnen, de prullenbak en de lijst *Bekeken* (sinds 0.29.0).

## 1. Doel

Een experimentele webapp waarmee je een bestand op Wikimedia Commons opent, er objecten in detecteert (met box en masker), ze uitsnijdt als transparante PNG of als JPG, ze laat beschrijven, en de uitsneden na controle **weer op Commons publiceert**, met een nette koppeling naar het origineel.

Voorbeelden:

- Uit een album amicorum de losse wapenschilden, portretten en tekeningen halen, zoals uit [Album amicorum van Jacob van Bronckhorst van Batenburg (8077131573).jpg](https://commons.wikimedia.org/wiki/File:Album_amicorum_van_Jacob_van_Bronckhorst_van_Batenburg_(8077131573).jpg) (2000 × 1429 px, publiek domein).
- Uit een prent, kaart of krantenpagina op Commons de losse figuren, vignetten, logo's of illustraties uitsnijden.
- De figuren die op Commons al als regio zijn vastgelegd, los uitsnijden. Op [Book of Hours of Philip of Burgundy - KW76F - folio 283r - Heaven - All Saints - Jean Le Tavernier.jpg](https://commons.wikimedia.org/wiki/File:Book_of_Hours_of_Philip_of_Burgundy_-_KW76F_-_folio_283r_-_Heaven_-_All_Saints_-_Jean_Le_Tavernier.jpg) staan 13 heiligen met een eigen rechthoek in *beeldt af* (zie 7.5). Elke heilige wordt een eigen bestand.
- Een gescande boekpagina (PDF, DjVu of TIFF met meerdere pagina's) doorzoeken op illustraties.
- Alle uitsneden van een bestand in één keer voorbereiden voor upload, met beschrijving, licentie, categorieën en *beeldt af* (depicts).

## 2. Verhouding tot CropTool

[CropTool](https://commons.wikimedia.org/wiki/Commons:CropTool) (croptool2.toolforge.org, broncode [wpmed/croptool2](https://github.com/wpmed/croptool2), PHP, GPL-2.0, OAuth 1.0a, ondersteund door Wiki Project Med) is het gangbare gereedschap om op Commons een bestand bij te snijden. De Commons Mineventory is daar een **verdieping** op, geen vervanging.

| | CropTool | Commons Mineventory |
| --- | --- | --- |
| Selectie | Eén rechthoek, met de hand getrokken; randdetectie | Veel objecten tegelijk, gevonden met AI (zoekterm, AI-suggesties per afbeelding, Aanwijzen), met maskers; handmatige rechthoek als terugvaloptie |
| Vorm van de uitsnede | Rechthoek | Rechthoek (JPG) of de vorm van het object (transparante PNG) |
| Bewerkingen | Rechtzetten, draaien, spiegelen, helderheid/contrast, verliesloos JPEG (jpegtran) | Geen beeldbewerking in fase 1. Wel: rand eromheen instelbaar, keuze PNG of JPG |
| Bestandstypen | JPEG, PNG, TIFF, SVG, WebP, GIF; één pagina uit PDF/DjVu | JPEG, PNG, TIFF, WebP; pagina's uit PDF/DjVu/TIFF (zie 5.4). Geen SVG en geen geanimeerde GIF |
| Resultaat | Origineel overschrijven, of één nieuw bestand | Altijd **nieuwe** bestanden, nooit het origineel overschrijven; meerdere uitsneden per keer |
| Beschrijving | Neemt de beschrijving van het origineel over | Nieuwe beschrijving per uitsnede: wat het model ziet (als voorstel), plus de gegevens van het origineel |
| Koppeling | `{{Extracted from}}` op de nieuwe pagina, `{{Image extracted}}` op het origineel | Hetzelfde (zie 9.3) |
| Gestructureerde gegevens (SDC) | Niet bekend | Caption, *beeldt af* (P180), licentie en auteursrechtstatus overgenomen |
| Kosten | Gratis | SAM en Muse Spark kosten geld (zie 6.4) |

**Bewuste keuzes:**

- Geen eigen beeldbewerking. Wie wil rechtzetten of de helderheid aanpassen, gebruikt CropTool, eventueel op de nieuwe uitsnede.
- Geen "origineel overschrijven". Dat is CropTools terrein, en een uitsnede van een object is een ander werk dan het origineel.
- Na de upload een link "Openen in CropTool" bij elke uitsnede die op Commons staat (backlog 14a). CropTool neemt geen vooringevuld kader over (getest in 0.17.0); het detectiepaneel heeft nu *Bijsnijden in CropTool* voor het hele bestand (0.18.0).

## 3. Uitgangspunten

- **Experiment.** Geen officiële dienst van de KB of de Wikimedia Foundation. Dat staat in de footer.
- **Detectie en beschrijving** rechtstreeks via de **Meta Model API** (SAM 3.1 en Muse Spark), zoals in de Delpher Uitsnijder. Eén API-sleutel van de KB, op de server (besluit Olaf, 3-11-2026).
- **Inloggen** met het Commons-account van de gebruiker via **OAuth 2.0**. Uploads gebeuren op naam van die gebruiker.
- **Uploaden alleen na een klik** van de gebruiker, na een overzicht en een bevestiging. Nooit vanzelf.
- **Geen live aanroepen naar de Meta Model API** zonder expliciete opdracht van Olaf. Tests draaien op fixtures.
- **Hosting**: lokaal tijdens de bouw, daarna op **Wikimedia Toolforge**.
- **RESTful**: alles via `/api/v1`; de UI is een client van dezelfde API. Een GET kost nooit geld en verandert niets.
- **Taal**: de interface is **meteen tweetalig, Nederlands en Engels** (besluit Olaf, 3-11-2026). De documentatie is Nederlands; code, identifiers en commentaar zijn Engels. De API-velden blijven Nederlands, zoals in de Delpher Uitsnijder.
  - Alle teksten in vertaalbestanden (`frontend/i18n/nl.json` en `en.json`), gedeeld door de Jinja-templates en de Vue-componenten. Geen tekst hard in de code.
  - De taal volgt, in deze volgorde: `?uselang=` in de URL (zoals op Commons), de keuze van de gebruiker (taalkeuze in de header, onthouden in de sessie), de taal van de browser, en anders Engels.
  - Foutmeldingen van de API blijven Nederlands (`{"fout": …}`), met daarnaast een vaste code (`"code": "not_found"`) die de UI vertaalt.
  - Andere talen kunnen later via [translatewiki.net](https://translatewiki.net/) of een vertaalbestand erbij.
- **Volledige resolutie**: uitsneden en uploads altijd op de oorspronkelijke resolutie van het Commons-bestand, nooit op de verkleinde versie die naar het model gaat.

## 4. Wat hergebruikt wordt en wat vervalt

### 4.1 Overnemen (kopiëren en aanpassen, geen gedeelde bibliotheek)

| Delpher Uitsnijder | In de Commons Mineventory |
| --- | --- |
| `uitsnijder/detectie/basis.py`, `dummy.py`, `meta_sam.py`, `maskers.py` | Ongewijzigd: de detectorinterface, `DummyDetector`, `MetaSamDetector` (met `meta-sam-parser`), maskers lui decoderen en cachen |
| `uitsnijder/detectie/dienst.py` | De kern blijft: zoektermen, cache per afbeelding+term+model, samenvoegen van dubbelingen (IoU), selectie, prullenbak, opslaan, uitsnede-JPG. De Delpher-delen (zones, ALTO, bijschriften, koppeling aan artikelen) gaan eruit |
| `uitsnijder/prompts.py` | EN/MIN-syntax, de vertaaltabel en de lijst voor Alles detecteren (zie 7.4) |
| `uitsnijder/beschrijving.py` | "Wat staat hierop?" en het paginaoverzicht, met `reasoning.effort` en de modelkeuze. De context is anders: geen ALTO, wel de Commons-beschrijving, caption en categorieën (zie 6.2) |
| `uitsnijder/verbruik.py`, `/verbruik` | Ongewijzigd, plus de Commons-gebruiker per aanroep (zie 8.3) |
| `uitsnijder/cache.py`, `config.py`, `changelog.py`, `markdown_lite.py` | Ongewijzigd, met andere sleutels en variabelen |
| `uitsnijder/export.py` | Zip en JSON blijven; de IIIF-export wordt een backlog-item |
| `uitsnijder/api.py`, `openapi.py` | Zelfde opbouw en conventies (`{"fout": …}`, `X-Robots-Tag`, 201 bij aanmaken, oude paden markeren), andere resources (hoofdstuk 11) |
| `static/js/viewer.js`, `app.js`, `lightbox.js`, `objecten.js`, `verbruik.js` | De viewer (zoom, pan, overlays, klik/Ctrl-klik, Aanwijzen) wordt een gewone JS-module, gebundeld door Vite. De rest (panelen, vergroter, objectenpagina, verbruik) wordt opnieuw opgebouwd als Vue-componenten met Codex, met dezelfde logica (hoofdstuk 10) |
| `docs/commons-beschrijving.md` | Basis voor de uploadstap: keuzemenu, rechtenlabels, controle vooraf, proefweergave, `maxlag`, één upload tegelijk |
| Tests met fixtures | Dezelfde aanpak; de opgenomen SAM- en Muse-antwoorden kunnen mee |

### 4.2 Vervalt

- De **Delpher-adapter** (`delpher.py`): metadata, DIDL, OCR per artikel, `imageheader`, de imageviewer van de KB, de resolver.
- **ALTO** en alles wat ervan afhangt: koppen, illustratieblokken, bijschriften uit de OCR (`bijschrift.py`), "tekst eromheen" als controle van de OCR.
- De **krantenhiërarchie** (`hierarchie.py`): aflevering › pagina › artikel, de koppelregel object → artikel, `config/delpher_collectiesets.json` en de typedetectie krant/tijdschrift/boek.
- De **Delpher-stijl** (`delpher-theme.css`, het Delpher-logo) en de Firefox-extensie (die kan later terugkomen als "Openen in de Commons Mineventory", zie de backlog).
- **De rechtenregel op verschijningsjaar** (`rechten.py`, `RECHTEN_GRENSJAAR`). Op Commons is de licentie al vastgesteld; zie 5.3.
- Het **bot-wachtwoord** uit `docs/commons-beschrijving.md`. In plaats daarvan OAuth (hoofdstuk 8).

### 4.3 Nieuw

- Een **Commons-adapter** (`commons.py`): bestand opzoeken, imageinfo, wikitekst, SDC, pagina's van PDF/DjVu/TIFF.
- **OAuth 2.0** en een sessie per gebruiker.
- **Upload naar Commons** met wikitekst en SDC.
- **Gratis regio's uit Commons zelf** (de opvolger van "Uit Delpher", zie 7.5).
- Een **daglimiet per gebruiker** naast de algemene daglimiet.

## 5. De bron: Wikimedia Commons

### 5.1 Invoer

De gebruiker plakt in het invoerveld een van:

- een bestandspagina: `https://commons.wikimedia.org/wiki/File:Album_amicorum_….jpg` (ook `Bestand:` en andere taalvarianten, `?uselang=…`, `/w/index.php?title=File:…`, en `#`-fragmenten);
- een directe bestandslink op `upload.wikimedia.org` (ook een thumbnail-URL: de app leidt de bestandsnaam af);
- een titel met of zonder `File:`, met spaties of underscores;
- een M-id (`M28830642`) of een `curid`.

Eén verzoek normaliseert dit naar de canonieke titel en de page-id. Een redirect (hernoemd bestand) wordt gevolgd en gemeld. Bestaat het bestand niet, of staat het niet op Commons maar op een andere wiki, dan meldt de app dat met een voorbeeld-URL.

Een **categorie** als invoer (alle bestanden in `Category:…` als lijst om door te bladeren, net als een aflevering in Delpher) komt in **fase 2** (besluit Olaf, 3-11-2026).

### 5.2 Gegevens ophalen (MediaWiki Action API)

Alles via `https://commons.wikimedia.org/w/api.php`, met een eigen User-Agent, `maxlag=5`, caching en hooguit ongeveer één verzoek per seconde.

| Wat | Aanroep |
| --- | --- |
| Titel, page-id, redirect | `action=query&titles=…&redirects=1&prop=info` |
| Afmetingen, MIME, SHA-1, origineel | `prop=imageinfo&iiprop=url|size|mime|sha1|extmetadata|bitdepth` |
| Verkleinde versie voor de viewer en het model | `iiurlwidth=…` (thumbnail-URL). Commons beperkt thumbnails tot vaste stapgroottes; de app vraagt de dichtstbijzijnde stap aan in plaats van een willekeurige breedte. **Bij de bouw verifiëren** welke stappen er nu zijn |
| Licentie en maker (leesbaar) | `extmetadata`: `LicenseShortName`, `License`, `UsageTerms`, `Artist`, `Credit`, `ImageDescription`, `DateTimeOriginal`, `Attribution`, `AttributionRequired`, `Restrictions` |
| Wikitekst | `prop=revisions&rvprop=content|ids&rvslots=main` (voor de sjablonen: licentie, `{{Information}}`/`{{Artwork}}`, `{{Personality rights}}`, `{{Trademarked}}`, `{{Delete}}`, `{{Flickrreview}}`, `{{ImageNote}}`) |
| Gestructureerde gegevens | `action=wbgetentities&ids=M<pageid>`: captions, P180 *beeldt af* (met kwalificatoren), P6216 auteursrechtstatus, P275 licentie, P170 maker, P571 datum, P195 collectie, P7482 bron |
| Categorieën | `prop=categories&clshow=!hidden` (zichtbaar) en apart de verborgen |
| Meerpaginabestanden | `iiprop=…|metadata` en `pagecount`; per pagina een thumbnail met `iiurlparam=page<n>-<breedte>px` |
| Bestaat de uitsnede al? | `list=allimages&aisha1=<sha1>` (zie 9.5) |

Voor het origineel in volledige resolutie haalt de server het bestand één keer op van `upload.wikimedia.org` en cachet het. Uitsnijden gebeurt altijd op dat origineel.

### 5.3 Licentie, maker en rechten

Op Commons staat elk bestand al onder een vrije licentie of in het publieke domein. De app hoeft dus niet zelf te raden of iets vrij is, zoals bij Delpher. Wel:

- **De uitsnede erft de licentie van het origineel.** Een uitsnede is een afgeleid werk; bij CC BY-SA moet de uitsnede ook onder CC BY-SA, met naamsvermelding. De app neemt de licentiesjablonen uit de wikitekst van het origineel letterlijk over (zie 9.3) en de licentie- en statusverklaringen uit de SDC.
- **Maker en naamsvermelding** komen uit het origineel (`|author=` of `{{Creator:…}}`, `Artist`, `Attribution`). De uitsnede vermeldt het origineel als bron.
- **Waarschuwen, niet blokkeren**, net als in de Delpher Uitsnijder. Rechtenlabels per uitsnede, aangepast aan Commons:

| Label | Wanneer |
| --- | --- |
| **Merk** | Het origineel heeft `{{Trademarked}}`, of "Wat staat hierop?" zegt `soort` = logo/advertentie, of noemt een bedrijf. Standaard uit; mee na bevestiging met een reden |
| **Persoonlijkheidsrechten** | `{{Personality rights}}` op het origineel en de uitsnede toont een persoon |
| **Origineel ter discussie** | `{{Delete}}`, `{{Copyvio}}`, `{{No permission since}}` of een openstaande licentiecontrole (`{{Flickrreview}}` zonder bevestiging, `{{LicenseReview}}`). **Uploaden uitgeschakeld**, zoals CropTool dat ook doet bij Flickr-bestanden die nog wachten |
| **Alleen in de VS vrij** | `{{PD-US-only}}`-achtige sjablonen. Ter info: dat mag op Commons niet, dus de app meldt het |
| **Naamsvermelding verplicht** | CC BY / CC BY-SA en dergelijke: de app zet de maker en de licentie verplicht in de nieuwe pagina |
| **In orde** | Publiek domein of een vrije licentie, zonder de signalen hierboven |

### 5.4 Bestandstypen en resolutie

- **JPEG, PNG, WebP, TIFF**: direct. TIFF wordt intern naar RGB omgezet; de uitsnede wordt PNG of JPG.
- **PDF en DjVu**: per pagina, als de gerenderde pagina van Commons (`page<n>-<breedte>px`) op de grootste beschikbare breedte. Dat is niet de "echte" scan, maar meestal de beste die Commons levert, en het volstaat (besluit Olaf, 3-11-2026). De app rendert PDF's niet zelf.
- **Meerpagina-TIFF**: per pagina, uit het origineel.
- **SVG, GIF, video en audio**: niet ondersteund; de app meldt dat.
- **Grote bestanden**: Commons heeft scans van honderden megapixels. Pillow beschermt tegen "decompression bombs"; op Toolforge is het werkgeheugen per webservice beperkt. Voorstel: tot **100 megapixel** gewoon verwerken; daarboven alleen detecteren op de verkleinde versie en uitsnijden in tegels uit het origineel, of weigeren met een melding. Niet beantwoord in ronde 2; de app gaat uit van het voorstel (100 megapixel), bij de bouw te meten op Toolforge.
  **Gebouwd in 0.21.0** (besluit Olaf, 4-11-2026): boven `MAX_MEGAPIXELS` leest de app het origineel met **libvips** (`pyvips[binary]`, `cutter/tegels.py`) stuk voor stuk. Detecteren en de viewer gebruiken de verkleinde versie van Commons, zoals bij elk bestand; voor een uitsnede, het voorbeeld en de vraag aan Muse Spark wordt alleen het nodige stuk gedecodeerd, in volledige resolutie. JPEG, PNG en (meerpagina-)TIFF; 16-bits, grijs en CMYK worden 8-bits sRGB. Gemeten: een uitsnede van 2000 × 1500 uit een JPEG van 150 megapixel piekt op ongeveer 100 MB geheugen (Pillow zou het hele beeld decoderen, ongeveer 450 MB). Zonder pyvips weigert de app zulke bestanden, zoals voorheen.

### 5.5 Hiërarchie

Veel platter dan bij Delpher:

1. **Bestand** (titel, M-id, licentie, maker, datum, categorieën).
2. **Pagina** (alleen bij PDF/DjVu/TIFF; bij een gewone afbeelding is er één pagina).
3. **Object**: de detectie, met box, masker, label, score, herkomst, beschrijving en het Commons-concept.

Opslag: `uitvoer/<M-id>/objecten.json` per bestand en per pagina, zoals in de Delpher Uitsnijder. De M-id is stabiel, ook als het bestand wordt hernoemd.

## 6. Detectie en beschrijving

### 6.1 Detectie (SAM 3.1)

Ongewijzigd ten opzichte van de Delpher Uitsnijder (`docs/meta-sam-api.md`):

- `POST https://api.meta.ai/v1/responses` met `model: sam-3.1`, één Engelse noun phrase per aanroep, of een punt- of boxprompt (Aanwijzen).
- De server stuurt een verkleinde versie (standaard 1920 px breed) als base64-data-URL. Besloten (3-11-2026): **data-URL**, zoals in de Delpher Uitsnijder. Dan haalt Meta niets zelf op bij Wikimedia, en bepaalt de app de resolutie.
- Antwoord via `meta-sam-parser`; maskers lui decoderen en cachen.
- Cache per **SHA-1 van het bestand** + pagina + term + model. Een nieuwe versie van het bestand (andere SHA-1) geeft dus een nieuwe detectie.

### 6.2 Beschrijving (Muse Spark)

"Wat staat hierop?" per object en "Wat staat op deze pagina?" per bestand, zoals in `docs/beeld-taalmodel.md`, met dezelfde JSON-velden (`soort`, `onderwerp`, `bedrijf_of_naam`, `tekst_in_beeld`, `tekst_rond_beeld`, `beschrijving`, `zekerheid`). Verschillen:

- **Context** voor het model: de beschrijving en de caption van het origineel (als platte tekst, ingekort), de zichtbare categorieën en de bestaande *beeldt af*-items, uitdrukkelijk als hulp en niet als waarheid. In plaats van de ALTO-tekst. Daarnaast (sinds 0.13–0.16): het bijschrift van de uitsnede, de aanwijzing van de gebruiker (AI-bijsturing) en de tekst die het paginaoverzicht in en onder de hele afbeelding las.
- **Nieuw veld `wikidata_suggesties`**: hooguit drie zoektermen voor *beeldt af* (bijv. "coat of arms", "Jacob van Bronckhorst van Batenburg"). De app zoekt die gratis op met `wbsearchentities`; de gebruiker kiest het item. Het model verzint zelf geen Q-nummers.
- **Taal**: beschrijving en caption in het Nederlands én het Engels (in één aanroep). Niet beantwoord in ronde 2; dit is het voorstel, en het past bij de tweetalige interface. Het paginaoverzicht geeft sinds app-versie 0.9.0 ook soort en samenvatting in beide talen (`paginasoort_en`, `samenvatting_en`); `soort` en `zekerheid` komen uit een vaste Nederlandse lijst en de interface vertaalt ze.
- **Met de hand aanpassen** (gebouwd, 0.6.0; sinds 0.22.1 met een potloodje per veld): onderwerp en beschrijving (nl en en), naam, tekst in en rond het beeld, met *Ongedaan maken* na het opslaan; ook in de lightbox naast het grote beeld (0.22.0). De eerste keer dat een veld verandert, bewaart de app de AI-tekst in `ai_origineel`, zodat *Terug naar de AI-tekst* altijd kan; `bewerkt` zegt of er nog iets afwijkt.
- **Herkenbaar als AI** (gebouwd, 0.8.0): bij soort, onderwerp, beschrijving, het paginaoverzicht en *Bron: AI-beelddetectie* staat een AI-merkje. Een klik opent een venster dat uitlegt wat het model deed (met een link naar het model en, bij de detectie, de score van het object), wat er mis kan gaan en wat de gebruiker moet controleren. De waarschuwing dat een taalmodel zich kan vergissen staat in het blok *Model, kosten en kwaliteit*.

### 6.3 Contributor of Standard

De regel uit de Delpher Uitsnijder ("Contributor alleen als alles klopt") wordt:

1. P6216 van het origineel is **publiek domein** (`Q19652`) én de licentie is een PD-sjabloon (geen CC). Bij CC-licenties zou Meta het werk mogen gebruiken om te trainen zonder de voorwaarden (naamsvermelding, gelijk delen) na te komen; dat doen we niet.
2. Geen labels **Merk**, **Persoonlijkheidsrechten** of **Origineel ter discussie**.
3. `BEELDMODEL_CONTRIBUTOR=aan` (standaard `aan`, zie onder).

Anders: Standard.

Besloten door Olaf (3-11-2026): **Contributor aan voor publiek domein**, ook voor bestanden van anderen. `BEELDMODEL_CONTRIBUTOR` staat daarom standaard op `aan`. Voorwaarden 1 en 2 blijven gelden: bij twijfel gaat het naar Standard. Per aanroep wordt vastgelegd welk model is gebruikt en waarom, zoals in de Delpher Uitsnijder. De reden staat er als Nederlandse tekst (voor logs en verbruik) en als code (`reden_code`: `publiek_domein`, `contributor_uit`, `rechtenlabel`, `niet_vrij`, `standaard_gekozen`) die de interface in gewone woorden toont, met een link naar Meta's uitleg van de Contributor-modus.

### 6.4 Kosten en limieten

Op basis van de metingen in de Delpher Uitsnijder:

| Actie | Aanroepen | Kosten (ongeveer) |
| --- | --- | --- |
| Eén zoekterm | 1 SAM | $0,0025 |
| Aanwijzen (puntprompt) | 1 SAM | $0,0025 |
| Alles detecteren | 8 SAM | $0,02 |
| Wat staat hierop? (`low`) | 1 Muse | $0,005 (Standard), $0,0003 (Contributor) |
| Wat staat op deze pagina? (`low`) | 1 Muse | $0,007 |
| AI-suggesties en dan Alle objecten detecteren | 1 Muse + n SAM | ±$0,03 |
| Een typische sessie: één bestand, Alles detecteren, tien beschrijvingen | 8 SAM + 10 Muse | ±$0,07 |

Limieten:

- **Daglimiet per gebruiker** (`DAGLIMIET_PER_GEBRUIKER`, 100 aanroepen, besloten 3-11-2026) en een **algemene daglimiet** van **500 aanroepen** (`DAGLIMIET_AANROEPEN=500`) plus een **dagbudget van $2** (`DAGBUDGET_USD=2`), beide besloten door Olaf op 3-11-2026. Boven een limiet: 429 met de resterende tijd.
- In live-modus vraagt de app vóór elke betaalde actie om bevestiging, met het bedrag (zoals nu).
- Meta: 3000 verzoeken per minuut voor SAM; Contributor heeft lagere limieten.

Wie betaalde aanroepen mag doen: zie 8.3 (een toegangslijst). De limieten zijn aan te passen in het beheerpaneel (8.4).

## 7. Detectiemodi

Alle modi uit de Delpher Uitsnijder blijven, op één gedeelde selectie per pagina.

### 7.1 Zoeken met een zoekterm

EN/MIN-syntax, Nederlandse termen via de vertaaltabel naar Engels, één SAM-aanroep per begrip.

### 7.2 Snel zoeken

**Uit de interface gehaald (4-11-2026, besluit Olaf):** op Commons staan duizenden soorten objecten, dus een vaste lijst klopt voor veel afbeeldingen niet. De AI-suggesties per afbeelding (7.6) vervangen dit. Sinds 0.21.0 is ook de API-modus `categorie` weg.

Vaste groepen, aangepast aan wat er op Commons staat: wapens en heraldiek, portretten, figuren en personen, dieren, planten en bloemen, gebouwen, kaarten, schepen, initialen en vignetten, logo's en beeldmerken, handschrift en tekstblokken, foto's in een album. Elke groep is een vooringevulde prompt.

### 7.3 Aanwijzen

Klikken op een plek zonder bekend object: een puntprompt aan SAM (één betaalde aanroep), resultaat als kandidaat. Een handmatige rechthoek (gratis) heeft een eigen blok, *Rechthoek tekenen*; Shift-slepen doet hetzelfde zonder die modus.

### 7.4 Bulk-operaties

Sinds 0.30.0 (besluit Olaf, 5-11-2026) staan *Selectie beschrijven* (sinds 0.31.0 *Geselecteerde objecten beschrijven*) en *Dubbelingen samenvoegen* niet meer in de kolom *Objecten zoeken*, maar onderaan *Wat je vond*, boven *Selectie opslaan*: ze werken op wat je gevonden en aangevinkt hebt. Het blok *Bulk-operaties* is daarmee vervallen.

Geselecteerde objecten beschrijven (alleen de geselecteerde objecten zonder beschrijving) en Dubbelingen samenvoegen. Elke betaalde stap met bevestiging en kosten. Een knop is uitgeschakeld als er niets te doen is: geen aangevinkte objecten zonder beschrijving, of minder dan twee objecten. Onder de knoppen staat in een grijze regel wat *Geselecteerde objecten beschrijven* zal doen: hoeveel geselecteerde objecten nog geen beschrijving hebben, welke worden overgeslagen, en als ze allemaal al beschreven zijn dat opnieuw beschrijven per object in de vergroter gaat.

Sinds 0.28.0 uit de interface (besluit Olaf, 4-11-2026): *Alles detecteren* (SAM met een vaste lijst soorten beeld, zoals illustratie, portret en wapen) en *Slim detecteren* (eerst het paginaoverzicht, dan SAM met de voorgestelde termen). *Alle objecten detecteren* bij de AI-suggesties doet hetzelfde met termen die bij deze afbeelding passen. In de API blijft `modus: "alles"` bestaan.

### 7.5 Uit Commons (gratis, zonder SAM)

De opvolger van "Uit Delpher": regio's die op Commons al bestaan. Eis van Olaf (3-11-2026): de app moet de **regio's uit de gestructureerde gegevens** (de gele rechthoeken op de bestandspagina) vinden en elke regio als **aparte afbeelding** kunnen uitsnijden en uploaden.

**Regio's in de gestructureerde gegevens (belangrijkste bron)**

- Op Commons kun je bij *beeldt af* (P180) met de kwalificator P2677 *relatieve positie in afbeelding* aangeven waar het item staat. De bestandspagina tekent die als gele rechthoeken met de naam van het item.
- De waarde is `pct:x,y,b,h`: linksboven en de afmetingen, in procenten van de breedte en hoogte van de afbeelding. Volgens IIIF bestaat ook de vorm in pixels (`x,y,b,h` zonder `pct:`); de app leest beide.
- Voorbeeld, het bestand met Alle Heiligen (M83565772), gelezen op 3-11-2026: 13 verklaringen P180 met P2677, bijvoorbeeld Catharina van Alexandrië (Q179718) op `pct:35.5814,68.7074,21.0853,24.2104` en Johannes de Doper (Q40662) op `pct:45.1206,35.0335,9.75884,16.4123`.
- De app leest ze met `wbgetentities` (zie 5.2), rekent ze om naar pixels van het origineel en maakt per regio een object:
  - bron `commons`, soort `regio`;
  - label = het Wikidata-label in het Nederlands, of in het Engels als dat er niet is; de Q-id staat erbij;
  - box = de regio, masker = een rechthoek;
  - herkomst: de M-id, het id van de verklaring en de waarde van P2677, zodat de koppeling met het origineel controleerbaar blijft.
- Regio's overlappen vaak, zoals de heiligen in het voorbeeld. Dat geeft niets: elke regio is een eigen object. Ze worden **niet** samengevoegd met de IoU-regel.
- **Optioneel een masker met SAM**: per regio één boxprompt aan SAM (`<|box;…|>`, zie `docs/meta-sam-api.md` van de Delpher Uitsnijder) geeft de vorm van de figuur, voor een transparante PNG. Dat kost één SAM-aanroep per regio, met bevestiging. Standaard blijft het een rechthoek (JPG).
- **Knoppen** in het blok *Uit Commons*: "Regio's uit Commons (n)" laadt ze allemaal, gratis. In de lijst en op de pagina tonen ze in het geel, zoals op Commons, met de naam erbij.

**Uploaden van een regio**

- Elke regio wordt een eigen bestand, met `{{Extracted from|File:<origineel>}}` naar het bronbestand (9.3), ook bij een gemaskerde PNG.
- *Beeldt af* van de uitsnede is meteen het item van de regio (Q179718), zonder P2677, want de uitsnede toont alleen dat item. Een caption en een bestandsnaam worden voorgesteld uit het label: *"Catherine of Alexandria – extracted from Book of Hours of Philip of Burgundy - KW76F - folio 283r - Heaven - All Saints - Jean Le Tavernier.jpg"*.
- Het origineel krijgt `{{Image extracted}}` (9.3). Aan de verklaring P180 op het origineel verandert niets.

**Andere bronnen**

- **Bestandsnotities** (`{{ImageNote}}` van de ImageAnnotator-gadget) in de wikitekst: rechthoek plus tekst. De tekst wordt het bijschrift.
- **Bestaande uitsneden**: `{{Image extracted}}` op het origineel noemt bestanden die al zijn uitgesneden. Die worden getoond als "staat al op Commons" (zonder positie, tenzij die af te leiden is). Een regio waarvan het item al op een bestaande uitsnede als *beeldt af* staat, krijgt het label "al uitgesneden".

### 7.6 Paginaoverzicht

"Wat staat op deze pagina?" met zoektermen als chips in het blok *AI-suggesties voor deze afbeelding*, met per term hoeveel objecten op de afbeelding staan (en in de prullenbak), en een knop *Alle objecten detecteren* (sinds 0.29.0 alleen voor de aangevinkte termen).

Sinds 0.29.0 (besluit Olaf, 5-11-2026): de eerste vraag is één aanroep voor beschrijving én zoektermen (het goedkoopst: het beeld gaat één keer mee). Daarna kan elk deel apart opnieuw (*Beschrijving opnieuw*, *Zoektermen opnieuw*: één aanroep met een vraag voor alleen dat deel, het andere deel blijft) of apart verwijderd worden (gratis). Twee aparte aanroepen vanaf het begin zouden ongeveer anderhalf keer zo veel kosten.

## 8. Inloggen en rechten (OAuth)

### 8.1 Patroon

Overgenomen uit de **IIIF Manifest Upload Workbench** (`src/api/oauth.js`, `docs/oauth-registration.md`): OAuth 2.0 van Wikimedia via Meta-Wiki.

- Autoriseren: `https://meta.wikimedia.org/w/rest.php/oauth2/authorize`
- Token: `https://meta.wikimedia.org/w/rest.php/oauth2/access_token`
- Profiel: `https://meta.wikimedia.org/w/rest.php/oauth2/resource/profile`
- Authorization code met PKCE (`S256`) en een `state` tegen CSRF; refresh-token voor langere sessies.
- Uploaden in twee stappen: eerst naar de **upload stash** (`action=upload&stash=1`), dan publiceren met `filekey`. Waarschuwingen (`exists`, `duplicate`, `badfilename`) komen zo vóór het publiceren boven, en worden aan de gebruiker getoond, niet stil genegeerd.
- Daarna SDC met `wbeditentity` op `M<pageid>`.
- Dubbelingen vooraf zoeken op SHA-1 (`list=allimages&aisha1=`).
- Bestandsnamen begrenzen op **255 bytes** (niet tekens), en verboden tekens eruit (`# < > [ ] { } | / \ :` en stuurtekens).

**Verschil met de workbench:** die draait helemaal in de browser (een "public client"). Hier staan de uitsneden en de Meta-sleutel op de server, en moet de server weten wie er betaalde aanroepen doet. Voorstel:

- **Server-side OAuth 2.0** in Flask, als **confidential client** (authorization code + PKCE). De token staat alleen op de server, in een server-side sessie, nooit in de browser.
- De server uploadt met de token van de gebruiker (`Authorization: Bearer …`).
- Besloten door Olaf (3-11-2026): server-side.

### 8.2 Registratie van de consumer

- **Ontwikkeling**: een *owner-only* consumer op Meta-Wiki. Die is direct goedgekeurd, maar werkt alleen voor Olafs account en kent geen autorisatieflow; de app gebruikt dan de access-token uit `COMMONS_OWNER_TOKEN` (zoals `VITE_OWNER_ACCESS_TOKEN` in de workbench, OI-09 daar).
- **Toolforge**: een publieke consumer met callback `https://<toolnaam>.toolforge.org/oauth/callback`. Die moet door een beheerder worden goedgekeurd (dagen tot twee weken).
- **Grants** (minimaal): *Basic rights*, *Upload new files* (`uploadfile`), *Edit existing pages* (`editpage`, nodig voor SDC en voor `{{Image extracted}}` op het origineel), *Create, edit, and move pages* (`createeditmovepage`, voor de nieuwe bestandspagina). Niet: overschrijven (`uploadeditmovefile`), want de app overschrijft nooit. **Bij de bouw verifiëren** welke set strikt nodig is.
- `OAUTH_CLIENT_ID` en `OAUTH_CLIENT_SECRET` alleen als omgevingsvariabele (op Toolforge: `toolforge envvars`). Nooit in de repo.

### 8.3 Wie mag wat

| Actie | Zonder login | Ingelogd |
| --- | --- | --- |
| Bestand openen, bekijken, gratis regio's (7.5), bestaande detecties en beschrijvingen bekijken | ja | ja |
| Betaalde aanroepen (SAM, Muse) | nee | ja, binnen de daglimieten (6.4) |
| Uitsneden downloaden (zip) | ja | ja |
| Uploaden naar Commons | nee | ja, op eigen naam |

Besloten door Olaf (3-11-2026): betaalde aanroepen alleen voor een **toegangslijst** (`TOEGESTANE_GEBRUIKERS`, Commons-gebruikersnamen, komma-gescheiden), met een daglimiet van **100 aanroepen per gebruiker** (`DAGLIMIET_PER_GEBRUIKER=100`). Ingelogde gebruikers die niet op de lijst staan, zien de knoppen met kosten grijs, met de uitleg waarom. Uploaden mag iedere ingelogde gebruiker, want dat kost niets. Olaf beheert de lijst (besluit 3-11-2026), in het **beheerpaneel** van de tool (8.4). In het begin staat alleen Olaf erop; anderen voegt hij toe in het paneel. Een beheerder staat altijd op de toegangslijst. Toegang vraag je aan met de knop **Toegang aanvragen** bij de grijze knoppen; de aanvraag komt in het beheerpaneel.

In het verbruikslog staat per aanroep de Commons-gebruikersnaam, **leesbaar** (besluit Olaf, 3-11-2026). `/verbruik` is alleen zichtbaar voor gebruikers op de toegangslijst en voor beheerders, en de privacyverklaring (12.3) noemt het.

### 8.4 Beheerders en het beheerpaneel

Eis van Olaf (3-11-2026): Olaf is nu de enige beheerder, maar wil andere beheerders kunnen toevoegen via hun Wikimedia-account, en de instellingen van de tool in een **beheerpaneel** kunnen invoeren.

**Twee soorten beheer**, die los van elkaar staan:

| | Beheerder in de app | Beheerder (maintainer) op Toolforge |
| --- | --- | --- |
| Wat je kunt | Het beheerpaneel: toegang, limieten, instellingen | De server: deployen, logs, omgevingsvariabelen, de API-sleutel |
| Account | Wikimedia-account (SUL), ingelogd via OAuth | Wikimedia developer-account (LDAP), met SSH-sleutel |
| Toevoegen | In het beheerpaneel, op Commons-gebruikersnaam | Op [toolsadmin.wikimedia.org](https://toolsadmin.wikimedia.org/), door een bestaande maintainer. Het beheerpaneel kan dat niet |
| Nu | Olaf | Olaf |

**Beheerpaneel** op `/beheer`, met Codex, alleen voor ingelogde beheerders:

- **Beheerders**: toevoegen en verwijderen op Commons-gebruikersnaam. De app controleert of het account bestaat (`list=users`). De eerste beheerder komt uit de omgevingsvariabele `BEHEERDERS_START` (`OlafJanssen`); die blijft altijd beheerder en is niet uit het paneel te verwijderen, zodat niemand zichzelf of anderen buitensluit.
- **Toegangslijst**: wie betaalde aanroepen mag doen, met per gebruiker optioneel een eigen daglimiet. Toevoegen, verwijderen, tijdelijk blokkeren.
- **Aanvragen**: aanvragen voor toegang, met naam, datum en een korte reden van de aanvrager; goedkeuren of afwijzen.
- **Limieten en kosten**: daglimiet per gebruiker, algemene daglimiet, dagbudget in dollars.
- **Noodknoppen**: betaalde aanroepen pauzeren (alle SAM- en Muse-aanroepen uit, voor iedereen) en uploaden naar Commons pauzeren.
- **Modellen**: Contributor aan of uit; redeneerinspanning (`low` enzovoort).
- **Bewaartermijnen**: originelen, uitsneden, cache (12.1).
- **Overzicht**: verbruik vandaag en deze maand, per gebruiker; ruimte op schijf.
- **Logboek** van alle wijzigingen in het paneel: wie, wat, wanneer, oude en nieuwe waarde.

**Wat niet in het paneel kan:** geheimen. `MODEL_API_KEY`, `OAUTH_CLIENT_SECRET` en `FLASK_SECRET_KEY` blijven omgevingsvariabelen op Toolforge (`toolforge envvars`), en zijn ook voor beheerders niet te zien of te wijzigen in de app.

**Opslag:** de instellingen, lijsten, aanvragen en het logboek staan in een kleine database: lokaal SQLite, op Toolforge ToolsDB (MariaDB), achter één opslaglaag in de code. SQLite op de gedeelde NFS-schijf van Toolforge is af te raden vanwege de bestandsvergrendeling; bij de bouw verifiëren. De omgevingsvariabelen uit 6.4 en 12.1 (`DAGLIMIET_*`, `DAGBUDGET_USD`, `BEWAAR_*`, `BEELDMODEL_CONTRIBUTOR`) zijn alleen nog de **beginwaarden**; zodra een beheerder iets in het paneel wijzigt, geldt de waarde uit de database.

**Beveiliging:** elke wijziging is een POST, PATCH of DELETE met een CSRF-token; alleen voor beheerders (anders 403); het paneel en de API eronder staan niet in de sitemap en hebben `noindex`.

## 9. Publiceren op Commons

### 9.1 Werkwijze

Gebaseerd op `docs/commons-beschrijving.md` van de Delpher Uitsnijder:

1. **Concept per object** (veld `commons`): bestandsnaam, beschrijving, caption (nl/en), datum, maker, bron, licentie, categorieën, *beeldt af*, rechtenlabel, en de keuze PNG of JPG. Gratis samengesteld, bewerkbaar in de vergroter: op de weergave zelf (potloodjes, *[bewerken]*), op de tabbladen *Bestandsinformatie* en *Gestructureerde gegevens*, zoals op Commons (0.23–0.24).
2. **Keuzemenu**: alle opgeslagen uitsneden van het bestand, met miniatuur, concept, rechtenlabel en een vinkje. Standaard aangevinkt: alleen **In orde** en **Naamsvermelding verplicht**.
3. **Controle vooraf** (gratis, alleen lezen): bestaat de naam al, bestaat dezelfde afbeelding al (SHA-1), bestaan de categorieën.
4. **Proefweergave**: de volledige wikitekst en de SDC-verklaringen per uitsnede, elk met een schakelaar **Weergave / Broncode** (gebouwd, 0.7.0):
   - *Weergave* van de wikitekst: Commons maakt de HTML (`action=parse`, alleen lezen, gecachet; een POST omdat de tekst lang kan zijn). De server laat alleen veilige tags staan, zonder afbeeldingen, stijlen of scripts, zodat de browser niets van Wikimedia laadt (12.3). Inklapbare blokken (zoals een instelling) staan net als op Commons dicht; het Wikidata-logo en het potloodje tekent de app zelf. Alleen opgevraagd als de proefweergave open is.
   - *Weergave* van de SDC: zoals het tabblad *Gestructureerde gegevens* op Commons, met captions, *beeldt af* bovenaan, elke eigenschap met waarden en kwalificaties, en labels van Wikidata.
   - Een blok *Regio op het origineel* toont wat het origineel voor deze uitsnede zou krijgen (9.4).
5. **Uploaden (n)**, alleen na het bevestigingsvinkje: *"Ik heb de beschrijving, de licentie en de rechten gecontroleerd. De bestanden worden op mijn naam geüpload."* Eén tegelijk, met voortgang en een knop **Stoppen**.
6. **Na de upload**: de Commons-URL bij het object; optioneel `{{Image extracted}}` op het origineel (9.3); een link "Openen in CropTool".

**De Upload Stash** ([Commons:UploadStash](https://commons.wikimedia.org/wiki/Commons:UploadStash)) is alleen de controlestap vlak vóór het publiceren (stap 5, zie ook 8.1): de app zet een uitsnede in de stash van de gebruiker, toont de waarschuwingen van Commons, en publiceert daarna met de wikitekst en de SDC. De stash vervangt de opslag op Toolforge (12.1) niet:

- een bestand in de stash verdwijnt na 48 uur als het niet is gepubliceerd;
- de stash vraagt een login met uploadrechten, terwijl bekijken, uitsnijden en downloaden ook zonder login moeten werken;
- terugdownloaden uit de stash kan alleen voor bestanden onder 1 MiB;
- de stash bewaart alleen het bestand, geen beschrijving, licentie of SDC.

Besloten door Olaf (3-11-2026): **geen** knop om uitsneden in de stash klaar te zetten voor een ander gereedschap, zoals de Upload Workbench. Publiceren gebeurt altijd vanuit de Commons Mineventory.

### 9.2 Bestandsnaam

Besloten door Olaf (3-11-2026): **onderwerp voorop, in het Engels**.

**`<Subject> – extracted from <titel origineel zonder extensie>.<png|jpg>`**, ingekort tot 240 bytes (de titel van het origineel wordt zo nodig ingekort, het onderwerp niet). Bijvoorbeeld:

*Coat of arms – extracted from Album amicorum van Jacob van Bronckhorst van Batenburg (8077131573).jpg*

*Catherine of Alexandria – extracted from Book of Hours of Philip of Burgundy - KW76F - folio 283r - Heaven - All Saints - Jean Le Tavernier.jpg*

- Het onderwerp is het Engelse label van het Wikidata-item (bij een regio, 7.5), anders het Engelse `onderwerp` uit "Wat staat hierop?" (een nieuw veld naast het Nederlandse), anders het Engelse SAM-label. De gebruiker past het aan.
- De titel van het origineel blijft zoals hij is, ook als die Nederlands is.
- Bij een botsing (zelfde naam) volgt een volgnummer: *"Coat of arms (2) – extracted from …"*.

### 9.3 Wikitekst

```
=={{int:filedesc}}==
{{Information
|description={{nl|1=<beschrijving>}}{{en|1=<optioneel>}}
|date=<datum van het origineel, letterlijk overgenomen>
|source={{Extracted from|File:<origineel>}}
|author=<auteur van het origineel, letterlijk overgenomen>
|permission=<letterlijk overgenomen, als aanwezig>
|other versions=
}}
=={{int:license-header}}==
<licentiesjablonen van het origineel, letterlijk overgenomen>

[[Category:<door de gebruiker gekozen categorieën>]]
[[Category:Uploaded with Commons Mineventory]]
```

- **`{{Extracted from|File:…}}`** op de nieuwe pagina, net als CropTool.
- **`{{Extracted from|File:…}}` is verplicht** op elke uitsnede, JPG en gemaskerde PNG, zodat altijd te zien is wat het bronbestand is (eis van Olaf, 3-11-2026). De app laat het niet weghalen.
- **`{{Image extracted|<nieuw bestand>}}`** op het origineel: een bewerking van de pagina van iemand anders. CropTool doet dit ook. Besloten door Olaf (3-11-2026): **standaard aan, per upload uit te zetten**. Eén bewerking voor alle uitsneden van een sessie; een bestaand sjabloon wordt aangevuld, niet gedupliceerd. De bewerkingssamenvatting noemt de nieuwe bestanden.
- Gebruikt het origineel `{{Artwork}}`, `{{Photograph}}` of `{{Book}}`, dan neemt de app dat sjabloon over met de velden die op de uitsnede ook kloppen (maker, datum, instelling, inventarisnummer) en een nieuwe `description`/`title`. Welke velden: vastgelegd in docs/artwork-velden.md (0.20.0), ook voor `{{Map}}`; de tekst in en rond het beeld als `{{Inscription}}` (0.22.0).
- **Licentie**: alle sjablonen uit de licentiesectie van het origineel, letterlijk. Bij `{{Flickrreview}}` of `{{LicenseReview}}` met een bevestiging: de bevestiging komt **niet** mee (CropTool doet dat ook niet), maar wel een verwijzing naar het origineel.
- **Categorieën**: de zichtbare categorieën van het origineel als voorstel (aan te vinken), plus wat de gebruiker toevoegt. Onderhoudscategorieën en `{{Assessments}}`, `{{QI}}`, `{{FP}}` en dergelijke komen nooit mee.
- **Volgcategorie** `Category:Uploaded with Commons Mineventory` (verborgen), en een projectpagina **`Commons:Commons Mineventory`**. Olaf maakt beide aan (besluit 3-11-2026), vóór de eerste echte upload.
- **Uploadsamenvatting**: *"Uitsnede uit [[File:…]] met de [[Commons:Commons Mineventory|Commons Mineventory]]; beschrijving deels opgesteld met een taalmodel en gecontroleerd door de uploader."*

### 9.4 Gestructureerde gegevens (SDC)

Na de upload, in één `wbeditentity` op `M<pageid>`:

| Verklaring | Waarde |
| --- | --- |
| Caption (`labels`) | nl, en optioneel en; hooguit 250 tekens |
| P180 *beeldt af* | Door de gebruiker gekozen Wikidata-items (6.2), eventueel met P1354 *getoond met* |
| P6216 *auteursrechtstatus*, P275 *licentie* | Overgenomen van het origineel |
| P170 *maker*, P571 *datum van creatie* | Overgenomen van het origineel, als aanwezig |
| P195 *collectie* | Overgenomen van het origineel, als aanwezig, zonder de kwalificator P2868 *subject heeft rol* (bijv. *collection highlight*): die gaat over het origineel |
| P31 *is een* | Q1250322 *digitale afbeelding* |
| P1163 *mediatype* | `image/jpeg` of `image/png`, naar het gekozen formaat |
| P4092 *checksum* | SHA-1 van het uitgesneden bestand, met P459 *bepalingsmethode* = SHA-1 |
| P3575 *gegevensgrootte*, P2048 *hoogte*, P2049 *breedte* | Van het uitgesneden bestand zoals het geüpload wordt (byte, pixel) |
| Relatie met het origineel | **Te onderzoeken.** Kandidaten: P7482 *bron van het bestand* met een kwalificator die naar het origineel wijst, of alleen de wikitekst (`{{Extracted from}}`). Kijken wat de gemeenschap gebruikt |

**Regio op het origineel:** per *beeldt af*-item van de uitsnede een P180 met P2677 *relatieve positie in afbeelding* (`pct:x,y,w,h` van de uitsnede in het hele beeld) op het origineel, zodat de regio's ook daar vindbaar zijn, zoals bij het Book of Hours. Gewenst door Olaf (4-11-2026): de regio's horen op het origineel, niet op de uitsnede. Gebouwd als voorbeeld in de proefweergave (0.7.0; regio's die het origineel al heeft worden herkend; niet bij bestanden met meer pagina's). Het echte schrijven is een bewerking van het origineel en komt met de upload (fase 2) of later (fase 4).

### 9.5 PNG of JPG

- **JPG** (rechthoek, volledige resolutie, kwaliteit 95) is de standaard: de gangbare vorm op Commons voor uitsneden van scans en foto's.
- **PNG met transparantie** (de vorm van het object) als keuze per object, bijvoorbeeld voor een wapen of een figuur. Waarschuwing als de PNG groter is dan 20 MB.
- Optioneel beide, als twee bestanden die naar elkaar verwijzen (`|other versions=`).
- Een masker dat (bijna) rechthoekig is, wordt altijd JPG.

### 9.6 Testen

- Eerst alleen met nagebootste antwoorden van de API (fixtures).
- Daarna echte uploads op een testwiki: `test-commons.wikimedia.org` of de bètacluster (`commons.wikimedia.beta.wmcloud.org`). **Bij de bouw nagaan** welke van de twee OAuth en SDC ondersteunt.
- `COMMONS_UPLOAD=uit` (standaard): alles werkt behalve de uploadknop; dan kun je de wikitekst kopiëren of een zip downloaden met bestanden en wikitekst.

### 9.7 Beeldt af en caption voor de hele afbeelding

Voorstel (4-11-2026, op verzoek van Olaf). Nog niet gebouwd. Punten met **[Vraag]** wachten op een keuze van Olaf.

**Doel.** Wat de AI op de hele afbeelding vond, ook vastleggen in de gestructureerde gegevens van het origineel:
- de herkende dingen (boy, girl, vintage car, …) als *beeldt af* (P180);
- de samenvatting van het paginaoverzicht (7.6) als caption.

Er gaat alleen iets naar Commons wat de gebruiker heeft gecontroleerd en aangevinkt, en pas na een bevestiging. Het is een bewerking van het origineel, de bestandspagina van iemand anders. Het opslaan komt daarom in fase 2, na OAuth, en eerst op de testwiki (9.6). Het samenstellen en bekijken kan eerder: dat is gratis en verandert niets op Commons.

**Waar.** In een eigen venster (een brede `CdxDialog`), niet in het uitklapblok *AI-suggesties voor deze afbeelding*: dat wordt anders te vol.
- In dat blok komt onder de zoektermen één knop: *Toevoegen aan de gegevens van deze afbeelding…*. Die knop is blauw maar niet gevuld; *Alle objecten detecteren* blijft de hoofdactie.
- De knop verschijnt zodra er een paginaoverzicht is, of minstens één object met een gekozen *beeldt af*-item.

**Indeling.**

```
┌ Gegevens van deze afbeelding ─────────────────────────────── ✕ ┐
│ [mini-afbeelding ]  003-KW XKZ 0214-…-page3.jpg ↗               │
│ [met de kaders   ]  [ Beeldt af (P180) ]  [ Captions ]          │
│                                                                 │
│  Al op Commons: …                                 (alleen lezen)│
│  Voorstellen                                                    │
│  ☑ boy (Q3010) – young male human     1 object ▣  door jou      │
│  ☐ girl (Q3031) – young female human  1 object ▣  AI ✎          │
│  ☐ automobile (Q1420)                 1 object ▣  AI ✎          │
│  ▸ Zoektermen zonder gevonden object (door, lawn)               │
│  + Ander item toevoegen [zoeken op Wikidata…]                   │
├─────────────────────────────────────────────────────────────────┤
│ 3 × beeldt af toevoegen · 1 caption toevoegen                   │
│                           [Annuleren]  [Op Commons opslaan…]    │
└─────────────────────────────────────────────────────────────────┘
```

- In de kop staan de naam van het bestand (met link naar Commons) en een kleine weergave van de hele afbeelding met de kaders. Wijs je een regel in het venster aan, dan lichten de kaders van die objecten op, net als bij de lijst links.
- Er zijn twee tabbladen: *Beeldt af (P180)* en *Captions*.
- Onderaan staat wat er gaat veranderen, met *Annuleren* en de hoofdknop *Op Commons opslaan…*. Tot fase 2 heet die knop *Concept bewaren*.
- Vóór het opslaan volgt een bevestiging met precies de wijzigingen en de bewerkingssamenvatting.

**Tabblad Beeldt af (P180).**

1. ***Al op Commons*** (grijs, alleen lezen): de P180-items die het origineel al heeft, met hun label. Heeft een item een positie (P2677), dan staat er een merkje bij. Hier verandert niets aan.
2. ***Voorstellen***: één regel per Wikidata-item. Elke regel heeft:
   - een vinkje;
   - het item: label, Q-id, korte beschrijving en een link naar Wikidata;
   - de objecten op de afbeelding die erbij horen: het aantal en de kleur van hun kader;
   - de bron.

   Er zijn drie bronnen:
   - ***Door jou gekozen bij een uitsnede***: de *beeldt af*-items uit het Commons-concept van de objecten (9.1). Die heb je al gecontroleerd, dus ze staan aangevinkt.
   - ***AI-zoekterm***: de chips uit het paginaoverzicht. De app zoekt elke term gratis op Wikidata op (`wbsearchentities`, in het Engels) en stelt het beste resultaat voor. Met het potloodje kies je een ander item, via dezelfde zoeker met autosuggestie als bij de uitsnede. Deze regels krijgen een AI-merkje en staan **niet** aangevinkt: je vinkt pas aan na controle.
   - ***AI-suggestie bij een uitsnede***: de `wikidata_suggesties` van "Wat staat hierop?" die je nog niet koos. Ook met AI-merkje, niet aangevinkt.

   Waar die bronnen samenkomen:
   - Hetzelfde item uit meer bronnen wordt één regel.
   - Een item dat het origineel al heeft, staat alleen bij *Al op Commons*.
   - Objecten in de prullenbak of met de status *uitgesloten* tellen niet mee.
   - Zoektermen waarbij geen object is gevonden (in het voorbeeld door en lawn), staan ingeklapt onderaan. Ze komen alleen mee als je ze openklapt en aanvinkt.
3. ***Ander item toevoegen***: een zoekveld met autosuggestie, voor wat de AI niet vond.

**Positie (P2677).** Per regel kies je *met positie*, standaard aan:
- **Met positie** wordt elk object een eigen verklaring: P180 met P2677 `pct:x,y,b,h`, uit het kader van het object in het hele beeld. Zo werkt ook het Book of Hours (7.5). Commons tekent die regio's op de bestandspagina, en de app leest ze de volgende keer gratis terug als objecten (7.5).
- **Zonder positie** wordt het één verklaring zonder kwalificator.

**[Vraag]** Positie standaard aan of uit?

**Tabblad Captions.** Per taal, Nederlands en Engels, een kaart met drie delen:
- ***Nu op Commons***: de bestaande caption, of "nog geen caption".
- ***AI-voorstel***: de samenvatting van het paginaoverzicht (`samenvatting` en `samenvatting_en`), met een AI-merkje.
  - Zonder de paginasoort ervoor ("prentenboekpagina —"), want dat is geen beschrijving.
  - Is het voorstel langer dan 250 tekens, dan zegt het venster dat het moet worden ingekort.
- ***De keuze***:
  - Zonder bestaande caption: *Toevoegen*, aangevinkt. Het AI-voorstel staat in een tekstvak dat je kunt aanpassen, met *Ongedaan maken* en een teller tot 250 tekens.
  - Met een bestaande caption: *Bestaande houden* (standaard), *Vervangen door het AI-voorstel* of *Zelf schrijven* (een tekstvak dat begint met het AI-voorstel). Bij vervangen staan de oude en de nieuwe tekst onder elkaar.

Captions in andere talen staan eronder, alleen lezen; die blijven zoals ze zijn.

Is er nog geen paginaoverzicht, dan legt het venster uit dat het voorstel uit *AI-suggesties voor deze afbeelding* komt (betaald, met bevestiging). Zelf een caption schrijven kan altijd.

**Opslaan op Commons (fase 2).**
- **Eén bewerking**: `wbeditentity` op `M<pageid>`, met alleen de nieuwe verklaringen en de gekozen captions. De app stuurt `baserevid` mee: de versie die het venster las. Is het origineel intussen gewijzigd, dan leest de app het opnieuw en toont het venster de nieuwe stand. Zo gaat er nooit iets over de wijziging van een ander heen.
- **Alleen toevoegen.** Bestaande verklaringen, kwalificatoren en captions in andere talen blijven zoals ze zijn. Een caption verandert alleen bij de keuze *Vervangen* of *Zelf schrijven*; de oude tekst blijft in de geschiedenis van de pagina staan.
- **Bewerkingssamenvatting** (in het Engels), bijvoorbeeld: `Added depicts (3) and caption (nl) with Commons Mineventory; AI suggestions checked by the user`.
- **Daarna** leest de app het origineel opnieuw; de cache van dit bestand vervalt. Objecten met een positie staan voortaan ook als regio van Commons (7.5).
- **Rechten**: de grant *Edit existing pages* (8.2). Die is al nodig voor `{{Image extracted}}`.
- **Kosten**: geen. Er is geen AI-aanroep, alleen leesverzoeken aan Wikidata en één bewerking op Commons.

**Bewaren.** Wat je in het venster kiest, bewaart de app per pagina in `uitvoer/<mid>/pagina_<n>/origineel.json`, net als het Commons-concept per object. Zo kun je later verder. Na het opslaan op Commons staat daar wanneer en door wie.

**API (voorstel).**

| Methode | Pad | Wat |
| --- | --- | --- |
| GET | `/bestand/{mid}/pagina/{n}/origineel` | De voorstellen, de stand op Commons en de bewaarde keuzes. Gratis; de Wikidata-zoekopdrachten voor de zoektermen zijn leesverzoeken en worden gecachet |
| PUT | `/bestand/{mid}/pagina/{n}/origineel` | De keuzes bewaren (concept). Gratis |
| POST | `/bestand/{mid}/pagina/{n}/origineel/opslaan` | Naar Commons (fase 2): ingelogd, na bevestiging, met `baserevid` |

**Verhouding tot 9.4.** De regio op het origineel per geüploade uitsnede (9.4) en dit venster schrijven dezelfde soort verklaringen, P180 met P2677, met dezelfde code. Fase 4 punt 15 (regio's terugschrijven, ook los van een upload) valt hiermee samen.

**Niet in dit venster.** De gelezen tekst in en onder het beeld. Op het origineel zou dat wikitekst zijn (`{{Inscription}}`), geen SDC, en dat is een andere bewerking.

**[Vraag] voor Olaf:**
1. **Positie**: standaard één verklaring per object, met P2677 (voorstel)? Of standaard één verklaring per item, zonder positie?
2. **Item al aanwezig zonder positie**: een AI-voorstel voor een item dat het origineel al heeft, maar zonder positie. Overslaan (voorstel)? Of de positie als kwalificator toevoegen aan die bestaande verklaring? Dat laatste wijzigt de verklaring van een ander.
3. **AI-herkomst**: moet een verklaring of caption die uit een AI-voorstel komt dat ook in de SDC tonen, met een kwalificator of referentie ("gevonden met AI, gecontroleerd door een mens")? Of is de bewerkingssamenvatting genoeg? Voorstel: alleen de samenvatting. Een vaste Commons-conventie hiervoor is niet bekend (zie 16).
4. **Bestaande caption**: standaard *Bestaande houden* (voorstel)?
5. **Bestanden met meer pagina's** (PDF, TIFF, DjVu): de SDC hoort bij het hele bestand, niet bij één pagina. Het venster dan uitzetten? Of alleen P180 zonder positie en zonder caption toestaan?

## 10. Interface met Codex

### 10.1 Welke Codex

Het verzoek noemde Codex **v0.4.1**. Dat is een oude versie (2022), nog zonder de **CSS-only-componenten**. De app gebruikt **2.6.0** (package.json). Besloten door Olaf (3-11-2026): **Codex 2.x met Vue 3, gebouwd met Vite**. Dit wijkt bewust af van de Delpher Uitsnijder, die geen build-stap heeft. Waarom 2.x: de huidige versie sluit aan bij wat Commons zelf gebruikt (Vector 2022), heeft CSS-only-componenten en levert de designtokens als CSS-variabelen.

### 10.2 Frontend-opbouw met Vite

**Wat waar draait:**

| Onderdeel | Techniek | Waar |
| --- | --- | --- |
| Server: Commons-adapter, detectie, beschrijving, OAuth, upload, REST-API, de HTML-pagina's (Jinja) | Python, Flask | Op Toolforge |
| Panelen, lijsten, dialogen, Lookup, het uploadoverzicht | Vue 3-componenten (`.vue`) met Codex | In de browser, gebouwd door Vite |
| Viewer: canvas, zoom, pan, overlays, maskers, klik/Ctrl-klik, Aanwijzen, Shift-slepen | Gewone JavaScript-module, zonder Vue | In de browser, gebundeld door Vite |
| Vite en npm | Node.js (lokaal: v24.12) | Alleen bij het ontwikkelen en bouwen, niet op Toolforge |

**Afspraken:**

- **Codex via npm**: `@wikimedia/codex`, `@wikimedia/codex-icons` en `@wikimedia/codex-design-tokens`, met vaste versies in `package-lock.json`. De Vue-versie volgt wat Codex vraagt.
- **De viewer blijft gewone JS.** Overgenomen uit de Delpher Uitsnijder (`viewer.js` en de interactie uit `app.js`), omgezet naar een ES-module. Niet herschrijven in Vue: tekenen gebeurt tientallen keren per seconde, en de reactiviteit van Vue maakt dat trager. Bovendien blijft de code dan uitwisselbaar met de Delpher Uitsnijder. Een dunne Vue-component zet de viewer op de pagina. Viewer en Vue praten via een kleine, gedocumenteerde interface: functies (`zoomToBox`, `setObjects`, `setSelection`) en events (`object-click`, `point`, `rectangle`).
- **Flask blijft de pagina's maken.** Elke pagina (`/`, `/objecten`, `/commons`, `/verbruik`) is een Jinja-template met een of meer plekken waar een Vue-app wordt gemount. Geen single-page-app en geen router in de browser; elke toestand houdt een eigen URL, zoals nu.
- **Koppeling Flask–Vite**: in ontwikkeling laadt de template de bestanden van de Vite-devserver (direct herladen bij elke wijziging); in productie leest Flask `static/dist/.vite/manifest.json` en zet de juiste bestandsnamen (met hash) in de template. Een kleine helper in `web.py`.
- **Commando's**: `npm run dev` (naast `flask --app app run --debug`), `npm run build` (schrijft naar `static/dist/`), `npm test` (Vitest, voor de JS-logica van viewer en componenten).
- **Geen externe CDN's**: alles zit in de gebouwde bundel en wordt door Flask uitgeleverd. Niets wordt in de browser van unpkg of jsDelivr geladen; dat lekt het IP-adres van gebruikers naar derden, en dat staat Toolforge niet toe zonder toestemming (zie 12.3).
- **`static/dist/` staat niet in git.** Het wordt gebouwd: lokaal voor het ontwikkelen, en voor Toolforge in de deploy (zie 12.1).
- **Taal**: componentnamen en code in het Engels. De teksten van de interface staan in `frontend/i18n/nl.json` en `en.json` (zie 3); de Vue-componenten gebruiken ze via een kleine vertaalfunctie (of `vue-i18n`), en Flask levert dezelfde bestanden aan de Jinja-templates.

### 10.3 Look en feel

- Zo dicht mogelijk bij Commons in Vector 2022: witte achtergrond, `--color-progressive` (#36c) voor acties, de lettertypen van de systeeminterface, rustige randen.
- **Geen Commons-logo als eigen merk**: het Commons-logo is een merk van de Wikimedia Foundation. Wel de naam "Commons Mineventory", een eigen eenvoudig icoon (sinds de nieuwe naam: een afbeelding met gevonden objecten in stippelkaders en een lijst ernaast, de inventaris) en de zin "werkt met Wikimedia Commons". Besloten (3-11-2026): een **eigen icoon**.
- Kleuren alleen via Codex-tokens; eigen toevoegingen (maskerkleuren, selectie) in `static/css/app.css` als variabelen.

### 10.4 Indeling

Zoals in de Delpher Uitsnijder, met Commons-inhoud:

- **Header**: icoon, "Commons Mineventory", label *experiment*, rechts de taalkeuze (NL/EN) en **Inloggen** of de gebruikersnaam met een menu (Mijn uploads, Uitloggen).
- **Invoerbalk**: Commons-URL of titel, knop **Openen**. Daaronder: titel, miniatuur, licentie (als Codex-*chip*), maker, datum, link naar de bestandspagina, en een uitklapbare **Metadata** (beschrijving, categorieën, SDC).
Sinds 0.29.0 van links naar rechts in de volgorde van het werk, zoals in de Delpher Uitsnijder (besluit Olaf, 4-11-2026): beeld, objecten zoeken, wat je vond.

- **Links**: de viewer met zoom en pan, overlays voor boxen en maskers, Aanwijzen met een groene rand.
- **Midden**: *Objecten zoeken*, het detectiepaneel in uitklapbare blokken (Codex *Accordion*), sinds 0.14.0 in deze volgorde: AI-suggesties voor deze afbeelding, Uit Commons, Zoeken, Aanwijzen of tekenen, Bijsnijden in CropTool (0.18.0).
- **Rechts**: *Wat je vond*: laatst bezocht › pagina's (bij PDF/DjVu/TIFF, als miniaturen) › de objecten met vinkjes, en onderaan (blijft in beeld) de knoppen **Geselecteerde objecten beschrijven**, **Dubbelingen samenvoegen**, **Selectie opslaan**, **Downloaden (zip)** en **Naar Commons…**.
- Elke kolom heeft een kop met één regel uitleg en een (i)-venster (0.28.0).
- **Vergroter**: de uitsnede, "Wat staat hierop?", het bijschrift en het Commons-concept (tab).
- **Gebouwd in fase 1 (stand 0.9.0)**: de randen tussen de drie kolommen zijn versleepbaar (ook met de pijltjestoetsen; breedte per browser onthouden); de objectenlijst toont een miniatuur per object, en een regel licht op als de muis erboven of boven die uitsnede in het beeld staat; alle knoppen zijn Codex-blauw (*progressive*), verwijderen blijft rood; in het Commons-concept zitten de invulacties per veld in een klein menu (⋯) met *Ongedaan maken* direct erna; de namen die de app zelf geeft (klik, rechthoek, regio) en soort en zekerheid volgen de taal van de interface.
- **Pagina's**: `/objecten` (alle uitsneden, met het facet "Op Commons"), `/commons` (het keuzemenu), `/verbruik`, `/docs`, `/changelog`.
- **Footer**: *"Dit is een experiment. Het is geen officiële dienst van de KB, nationale bibliotheek, of van de Wikimedia Foundation. Aan deze toepassing kunnen geen rechten worden ontleend."* Plus links naar de documentatie, de API, de broncode, de privacyverklaring en de changelog.
- **Meldingen** als Codex *Message* (notice, warning, error, success).

### 10.5 Mobiel

Panelen als tabbladen (Objecten, Beeld, Detectie; gebouwd in 0.19.0, *Beeld* eerst). Bekijken en selecteren wel; uploaden bij voorkeur op een groot scherm.

## 11. REST-API

Versieprefix `/api/v1`, OpenAPI op `/api/v1/openapi.json`, documentatie op `/docs`. Zelfde conventies als in de Delpher Uitsnijder: JSON-fouten `{"fout": …}`, `X-Robots-Tag: noindex`, een GET kost nooit geld. `{mid}` is de M-id (`M28830642`).

| Methode | Pad | Functie |
| --- | --- | --- |
| GET | `/` met `url`, `titel` of `mid`, en `pagina` | De UI; met parameters opent het bestand meteen |
| GET | `/api/v1/bestand?url=…|titel=…|mid=…` | Normaliseren; titel, M-id, afmetingen, MIME, SHA-1, licentie, maker, categorieën, SDC-samenvatting, paginalijst, rechtenlabels |
| GET | `/api/v1/bestand/{mid}/pagina/{n}` | Pagina: afmetingen, objecten, regio's uit Commons |
| GET | `/api/v1/bestand/{mid}/pagina/{n}/afbeelding?w=` | Verkleinde afbeelding (gecachet) |
| POST | `/api/v1/bestand/{mid}/pagina/{n}/detecties` | Detectie (`prompt`, `modus`: `prompt`, `alles`, `commons`; of `punt`). 201 |
| GET | `/api/v1/bestand/{mid}/pagina/{n}/detecties/raming` | Kostenraming; voert niets uit |
| GET, POST | `/api/v1/bestand/{mid}/pagina/{n}/inventaris` | Paginaoverzicht |
| PATCH | `/api/v1/bestand/{mid}/pagina/{n}/objecten` | Selectie of status wijzigen |
| GET, PATCH, DELETE | `/api/v1/bestand/{mid}/pagina/{n}/object/{oid}` | Eén object; DELETE = prullenbak |
| GET | `…/object/{oid}/uitsnede.png` en `…/uitsnede.jpg` | De uitsnede in volledige resolutie |
| GET, POST, DELETE | `…/object/{oid}/beschrijving` | Wat staat hierop? |
| GET, PATCH | `…/object/{oid}/commons` | Het Commons-concept (gratis) |
| GET, POST | `/api/v1/bestand/{mid}/pagina/{n}/uitsneden` | Uitsneden opslaan |
| GET | `/api/v1/bestand/{mid}/commons` | Het keuzemenu |
| POST | `/api/v1/bestand/{mid}/commons/controle` | Controle vooraf (alleen lezen op Commons) |
| POST | `/api/v1/bestand/{mid}/commons/uploads` | Uploaden van de gekozen objecten; vereist een login, `{"bevestigd": true}` en `COMMONS_UPLOAD=aan`. 202 met een taak-id |
| GET | `/api/v1/uploads/{taak}` | Voortgang van een upload; DELETE stopt hem |
| GET | `/api/v1/bestand/{mid}/export?formaat=zip|json` | Exporteren, inclusief wikitekst per uitsnede |
| GET, DELETE | `/api/v1/prullenbak` | Prullenbak |
| GET | `/api/v1/objecten` | Alle opgeslagen objecten, met filters |
| GET | `/api/v1/status` | Versie, modus, ingelogde gebruiker, budgetten |
| GET | `/api/v1/verbruik` | Verbruikslog |
| GET, PATCH | `/api/v1/beheer/instellingen` | Limieten, noodknoppen, modellen, bewaartermijnen (alleen beheerders) |
| GET, POST, DELETE | `/api/v1/beheer/beheerders[/{gebruiker}]` | Beheerders (alleen beheerders) |
| GET, POST, PATCH, DELETE | `/api/v1/beheer/toegang[/{gebruiker}]` | Toegangslijst, met eigen daglimiet of blokkade (alleen beheerders) |
| GET, PATCH | `/api/v1/beheer/aanvragen[/{id}]` | Aanvragen bekijken, goedkeuren of afwijzen (alleen beheerders) |
| POST | `/api/v1/toegang/aanvragen` | Toegang aanvragen (iedere ingelogde gebruiker; één openstaande aanvraag per gebruiker) |
| GET | `/api/v1/beheer/logboek` | Logboek van wijzigingen (alleen beheerders) |
| GET | `/beheer` | Het beheerpaneel (UI) |
| GET | `/oauth/login`, `/oauth/callback`, POST `/oauth/logout` | Inloggen (geen deel van `/api/v1`) |

API-gebruik zonder browser: met de sessiecookie na het inloggen. Een eigen API-sleutel per gebruiker voor scripts komt **later, in fase 4** (besluit 3-11-2026).

## 12. Toolforge

### 12.1 Opzet

- Een tool-account op Toolforge: **`commons-mineventory`** (URL `https://commons-mineventory.toolforge.org/`). De naam moet Engels zijn; de repo heet hetzelfde (besluit Olaf, 3-11-2026; naam gewijzigd 5-11-2026, eerst `commons-cutter`). Op 5-11-2026 nagekeken: `KBNLwikimedia/commons-mineventory` bestaat nog niet op GitHub; of de naam vrij is op Toolforge (toolsadmin) en Toolhub, wordt nagekeken bij de deploy (backlog 12f). Olaf is de enige maintainer; andere maintainers voegt hij toe op toolsadmin. Beheerders in de app staan los daarvan (8.4).
- **Build Service** met een `Procfile` (`web: gunicorn --workers 2 --bind 0.0.0.0:$PORT wsgi:app`) en `requirements.txt`; deployen met `toolforge build start <git-url>` en `toolforge webservice buildservice restart`. Alternatief: de klassieke `webservice python3.11` met een venv. Voorstel: Build Service.
- **De frontend bouwen** (Vite, zie 10.2). Op Toolforge draait alleen Python; Node.js is alleen nodig om `static/dist/` te maken. Twee routes, bij de bouw kiezen:
  1. **In de Build Service zelf**: als die naast Python ook een Node-stap kan draaien (`npm ci && npm run build`). Het eenvoudigst, als het kan.
  2. **In een GitHub Action** (terugvaloptie): bij elke push naar `main` bouwt de Action de frontend en zet het resultaat in een aparte branch (bijv. `deploy`), die de Build Service ophaalt. `static/dist/` komt dan nooit in `main`.
- **Configuratie** met `toolforge envvars create …` (`MODEL_API_KEY`, `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`, `FLASK_SECRET_KEY`). Nooit in de repo.
- **Opslag**: cache en uitvoer op de gedeelde schijf van de tool (`/data/project/commons-mineventory/`). Die schijf is gedeeld en niet bedoeld voor veel of blijvende opslag, dus een dagelijkse opruimtaak (`toolforge jobs`) ruimt op. Bewaartermijnen, besloten door Olaf (3-11-2026); ze tellen vanaf het **laatste gebruik**, niet vanaf het aanmaken:

  | Wat | Termijn | Waarom |
  | --- | --- | --- |
  | Originelen (de gedownloade scans) | 7 dagen | Staan altijd op Commons en zijn gratis opnieuw op te halen |
  | Uitsneden en maskers die nog niet zijn geüpload | 30 dagen | Tijd om te controleren, te uploaden of als zip te downloaden. De app toont bij elke uitsnede wanneer die verloopt |
  | Uitsneden die op Commons staan | Het bestand gaat weg na de upload; de gegevens (Commons-URL, datum, gebruiker) blijven | Het bestand op Commons is de blijvende kopie |
  | Detecties en beschrijvingen (de antwoorden van SAM en Muse Spark, klein) | 1 jaar | Opnieuw vragen kost geld; met de cache kost het nog eens openen van een bestand niets |

  Instelbaar met `BEWAAR_ORIGINELEN_DAGEN=7`, `BEWAAR_UITSNEDEN_DAGEN=30` en `BEWAAR_CACHE_DAGEN=365`. De opruimtaak en de app (ook met meerdere workers) schrijven de objecten van een pagina onder één gedeeld slot, een slot op het bestand `uitvoer/.slot` dat ook tussen processen werkt (`cutter/slot.py`). Zo overschrijft de opruimtaak nooit een wijziging die iemand op hetzelfde moment in de app maakt. Hoeveel ruimte een tool mag gebruiken, bij de bouw nagaan; dat kan de termijnen nog veranderen.

  Gebouwd in 0.18.0 (`cutter/opruimen.py`): het commando `flask --app app opruimen` telt wat weg zou gaan; met `--echt` wordt het verwijderd. Op Toolforge draait het dagelijks als `toolforge jobs`-taak met `--echt`. Het laatste gebruik is de toegangstijd van een bestand, die de app bij elk lezen zet (de wijzigingstijd blijft staan, want de Commons-cache gebruikt die voor de versheid). Precies:
  - **7 dagen**: `cache/originelen` en `cache/commons` (API-antwoorden en paginabeelden; allebei gratis opnieuw op te halen).
  - **30 dagen**: opgeslagen uitsneden en maskers (`uitvoer/<mid>/pagina_<n>/jpg`, `png`, `maskers`); het object vergeet dan dat het opgeslagen was, en opnieuw opslaan maakt ze weer aan. Ook voorbeelden en maskerafbeeldingen in de cache. Objecten die op Commons staan, houden hun gegevens.
  - **1 jaar**: de antwoorden van SAM en Muse Spark in de cache, en een hele pagina (objecten en beschrijvingen) die zo lang niet geopend is.
  - Nooit: het verbruikslog (`uitvoer/verbruik`).
- **Sessies**: server-side, in Redis van Toolforge of in bestanden; tokens versleuteld.
- **Lange taken** (Alles beschrijven, uploads van tientallen bestanden): pagina voor pagina vanuit de browser, zoals nu, of als `toolforge jobs`-taak. Voorstel: vanuit de browser, met de knop Stoppen.
- **Werkgeheugen**: een webservice heeft standaard een beperkt geheugen; grote scans (5.4) kunnen dat overschrijden. Bij de bouw meten en zo nodig meer aanvragen.
- **Broncode**: openbaar, met een open-sourcelicentie (verplicht op Toolforge). Licentie: **MIT** (besloten door Olaf, 3-11-2026). Let op: Codex (GPL-2.0-or-later), Vue (MIT) en `meta-sam-parser` (SAM License) houden hun eigen licentie; dat staat in de README, en Vite zet de licentieteksten bij de gebouwde bundel. De code komt op GitHub onder **`KBNLwikimedia/commons-mineventory`** (besluit 3-11-2026, naam 5-11-2026).

### 12.2 Lokaal ontwikkelen

Twee terminals:

- `flask --app app run --debug`, met `DETECTIE_MODUS=dummy`, `COMMONS_UPLOAD=uit` en `COMMONS_OWNER_TOKEN` voor uploads naar een testwiki;
- `npm run dev` voor de frontend (Vite, met direct herladen). Eenmalig vooraf: `npm install`.

Tests: `pytest` voor Python en `npm test` (Vitest) voor de frontend.

### 12.3 Regels van Toolforge en privacy

- Volgens de gebruiksvoorwaarden van Toolforge mag een tool geen persoonsgegevens (zoals IP-adressen) naar derden lekken zonder dat de gebruiker dat weet. Daarom: geen externe CDN's, lettertypen of scripts (alles zit in de gebouwde bundel en komt van de tool zelf), en een **privacyverklaring** op `/privacy`.
- **Proefweergave van de wikitekst**: de server laat Commons de wikitekst renderen (`action=parse`) en geeft de browser alleen opgeschoonde HTML zonder afbeeldingen, stijlen of scripts; de browser laadt dus niets van Wikimedia (9.1).
- **Meta Model API**: de server stuurt beelden van Commons (openbaar) en de context (beschrijving, categorieën) naar Meta, nooit gegevens van de gebruiker. De privacyverklaring zegt dat. Of een commerciële, betaalde API van Meta acceptabel is voor een Toolforge-tool, zoeken we uit vóór de deploy (besluit Olaf, 3-11-2026: "zien we te zijner tijd").
- Verbruikslog met gebruikersnamen: zie 8.3.

## 13. Fasering

**Fase 0 (nu):** dit FO, de repo, de open vragen.

**Fase 1: lokaal, zonder kosten**

1. Skelet overnemen uit de Delpher Uitsnijder: detectie (`DummyDetector`), prompts, cache, verbruik, API-conventies, tests.
2. Commons-adapter: invoer normaliseren, imageinfo, wikitekst, SDC, licentie- en rechtenlabels, meerpaginabestanden, caching.
3. Frontend-opzet met Vite, Vue 3 en Codex 2.x; de viewer uit de Delpher Uitsnijder als JS-module; de koppeling Flask–Vite (10.2); de vertaalbestanden voor Nederlands en Engels (3). Daarna de UI, meteen tweetalig.
4. Uit Commons: de regio's uit de gestructureerde gegevens (P180 met P2677) als objecten, en de bestandsnotities.
5. Opslaan, zip, `/objecten`.
6. Commons-concept per object, keuzemenu, controle vooraf en proefweergave, zonder upload.

**Fase 2: OAuth, upload naar een testwiki, categorieën**

7. OAuth 2.0 server-side, met een owner-only consumer.
8. Upload via de stash, SDC, `{{Image extracted}}` op het origineel; alles eerst op de testwiki (welke, blijkt bij de bouw).
9. Beheerpaneel (8.4): beheerders, toegangslijst, aanvragen, limieten (100 per gebruiker; 500 aanroepen en $2 per dag in totaal), noodknoppen, logboek; opslag in SQLite (lokaal) en ToolsDB (Toolforge).
10. Een categorie als invoer: bladeren door de bestanden van `Category:…` (5.1).

**Fase 3: live**

11. Detectie en beschrijving live (`DETECTIE_MODUS=live`), alleen na een opdracht van Olaf. Kalibratie op Commons-materiaal (albums, prenten, kaarten).
12. Deploy naar Toolforge als `commons-mineventory`, publieke consumer aanvragen, privacyverklaring. Olaf maakt de projectpagina `Commons:Commons Mineventory` en de volgcategorie aan.
13. De eerste echte uploads op Commons, door Olaf zelf.

**Fase 4: verdieping**

14. Batch over meerdere bestanden (een hele categorie in één keer).
15. Regio's terugschrijven naar het origineel (P180 met P2677); het voorbeeld staat al in de proefweergave (9.4). Valt samen met het venster *Beeldt af en caption voor de hele afbeelding* (9.7), dat al in fase 2 kan, na de upload.
16. Een link vanuit Commons: gadget of een item in het menu Hulpmiddelen ("Openen in de Commons Mineventory"), zoals CropTool.
17. IIIF-annotaties exporteren.
18. Eigen API-sleutel per gebruiker voor scripts.
19. Meer talen in de interface.

## 14. Repo-structuur (doel)

```
commons-mineventory/
  app.py  wsgi.py  Procfile  requirements.txt  .env.example  .gitignore
  cutter/ (beheer.py, opslag.py, commons.py, regios.py, oauth.py, upload.py, wikitekst.py, sdc.py, rechten.py, weergave.py,
               detectie/{basis,dummy,meta_sam,maskers,dienst}.py, beschrijving.py,
               prompts.py, verbruik.py, cache.py, export.py, api.py, openapi.py, web.py)
  templates/                         (Jinja-pagina's met mountpunten voor Vue)
  frontend/ (main-*.js per pagina, components/*.vue, viewer/*.js, api.js, styles/)
  static/dist/                       (gebouwd door Vite; niet in git)
  package.json  package-lock.json  vite.config.js
  docs/ (functioneel-ontwerp.md, api.md, oauth-registratie.md, deploy-toolforge.md, privacy.md)
  tests/ (met fixtures voor Commons, SAM en Muse)
  README.md  CLAUDE.md  CHANGELOG.md  BACKLOG.md  LICENSE
```

## 15. Open vragen voor Olaf

### Besloten (3-11-2026)

| Onderwerp | Besluit | Waar |
| --- | --- | --- |
| Naam | **Commons Mineventory** (5-11-2026; eerder Commons Cutter); tool, repo en map heten `commons-mineventory` (lokaal `D:\KB-OPEN\github-repos\commons-mineventory`, op GitHub `KBNLwikimedia/commons-mineventory`); het Python-package heet nog `cutter/`. Backlog 12f | 12.1 |
| Kosten | Eén API-sleutel van de KB voor de Meta-aanroepen | 3, 6.4 |
| Codex | 2.x met Vue 3 | 10.1 |
| Build-stap | Vite (Node.js alleen bij het ontwikkelen en bouwen); de viewer blijft een gewone JS-module; op Toolforge draait alleen Python | 10.2, 12.1 |
| Wie mag betalen | Een toegangslijst, beheerd in het beheerpaneel; in het begin alleen Olaf; toegang aanvragen in de app | 8.3, 8.4 |
| Beheer | Olaf is de enige beheerder; andere beheerders voegt hij toe op Wikimedia-account in een beheerpaneel in de tool, waar ook de toegangslijst, limieten en instellingen staan. Maintainers op Toolforge gaan via toolsadmin | 8.4 |
| Betaalde Meta-API op Toolforge | Later uitzoeken, vóór de deploy | 12.3 |
| Daglimieten | 100 aanroepen per gebruiker; in totaal 500 aanroepen en $2 per dag | 6.4 |
| OAuth | Server-side, als confidential client | 8.1 |
| `{{Image extracted}}` | Standaard aan op het origineel, per upload uit te zetten | 9.3 |
| `{{Extracted from}}` | Verplicht op elke uitsnede | 9.3 |
| Bestandsnaam | Onderwerp voorop, in het Engels | 9.2 |
| Licentie van de code | MIT | 12.1 |
| Regio's uit de gestructureerde gegevens | De app vindt ze en snijdt elke regio als apart bestand uit | 7.5 |
| Interface | Meteen tweetalig, Nederlands en Engels | 3 |
| Categorie als invoer | Fase 2 | 5.1, 13 |
| PDF en DjVu | De gerenderde pagina van Commons volstaat | 5.4 |
| Contributor-model | Aan voor publiek domein, ook bij bestanden van anderen | 6.3 |
| Volgcategorie en projectpagina | Beide; Olaf maakt ze aan | 9.3 |
| Verbruikslog | Gebruikersnamen leesbaar, alleen zichtbaar voor de toegangslijst en beheerders | 8.3 |
| Logo | Eigen icoon | 10.3 |
| Testwiki | Wat bij de bouw blijkt te werken | 9.6 |
| Beeld naar SAM | Als data-URL | 6.1 |
| API-sleutel per gebruiker | Later, fase 4 | 11, 13 |
| Bewaartermijnen op Toolforge | Originelen 7 dagen, niet-geüploade uitsneden 30 dagen, detecties en beschrijvingen 1 jaar; telt vanaf het laatste gebruik | 12.1 |
| Upload Stash | Alleen als controlestap vlak vóór het publiceren; geen overdracht aan de Upload Workbench of andere tools | 9.1 |

### Aangenomen (niet beantwoord, voorstel geldt tot Olaf anders zegt)

- Grote bestanden: boven 100 megapixel stuk voor stuk met libvips (5.4; besluit Olaf 4-11-2026, gebouwd in 0.21.0).
- Beschrijving en caption in het Nederlands én het Engels (6.2).

### Nog open

Geen vragen die de bouw van fase 1 en 2 tegenhouden. Later:

1. Is een commerciële, betaalde API van Meta acceptabel voor een Toolforge-tool? Vóór de deploy in fase 3 uitzoeken (besluit Olaf: "zien we te zijner tijd"). (12.3)

## 16. Te verifiëren bij de bouw

- Of ToolsDB de juiste plek is voor de gegevens van het beheerpaneel, en hoe de tool erbij kan (8.4).

- De thumbnailstappen die Commons nu toestaat (5.2).
- De minimale set OAuth-grants (8.2).
- Of de testwiki OAuth 2.0 en SDC ondersteunt (9.6).
- Welke SDC-eigenschap de relatie uitsnede → origineel vastlegt (9.4).
- Of Commons afspraken heeft over *beeldt af* en captions die met AI zijn gevonden, en hoe ander gereedschap dat P2677 schrijft (zoals Wikidata Image Positions) dat vastlegt (9.7).
- Of Commons-bots P1163, P4092, P3575, P2048 en P2049 na een upload zelf toevoegen, zodat de app ze niet dubbel zet (9.4).
- Of de Toolforge Build Service een Node-stap (`npm ci && npm run build`) vóór de Python-build kan draaien, of dat de frontend in een GitHub Action wordt gebouwd (12.1).
- Welke Vue-versie Codex 2.x vraagt, en of Codex-componenten die zich in een Jinja-pagina mounten goed samengaan met de CSS van Flask-pagina's (10.2).
- Geheugen en time-outs van een Build Service-webservice op Toolforge (12.1).
- Of Commons regels heeft voor beschrijvingen die deels met een taalmodel zijn gemaakt.
