# Functioneel ontwerp – Commons Mineventory

Naam: **Commons Mineventory** (besluit Olaf 5-11-2026; *mine* + *inventory*: een inventaris van wat er in een afbeelding staat, gedolven met AI; tot en met 0.30.1 heette de app *Commons Cutter*, besluit 3-11-2026). Tagline: *Detect objects in a Commons image. Find, cut out and describe them with AI.* Tool, repo en map heten sinds 0.31.1 `commons-mineventory`; het Python-package heet nog `cutter/` (backlog 12f). Status: concept v0.9, 5 november 2026 (v0.9: hoofdstuk 17, het dashboard met collecties uit categorieën, per gebruiker, en 8.6, starttegoed en eigen Meta-sleutel, beide als voorstel; v0.8: bijgewerkt tot app-versie 0.30.1: Begrippen, kolommen in werkvolgorde (10.4), bulk onder de objecten (7.4), paginaoverzicht per deel (7.6); de stand van zaken staat in docs/overdracht.md; v0.7: voorstel 9.7, *beeldt af* en caption voor de hele afbeelding; v0.6: bijgewerkt tot app-versie 0.24.2; zie CHANGELOG.md voor alles wat sinds 0.9.0 gebouwd is; v0.5: bijgewerkt naar wat er in fase 1 is gebouwd, app-versie 0.9.0: bewerkbare AI-teksten, AI-merkjes, proefweergave zoals op Commons, extra SDC, regio op het origineel als voorbeeld; v0.2: antwoorden van Olaf op de belangrijkste vragen verwerkt, en de regio's uit de gestructureerde gegevens uitgewerkt in 7.5; v0.3: frontend met Vite, zie 10.2; v0.4: tweede ronde antwoorden en de naam Commons Cutter). Opdrachtgever en eigenaar: Olaf Janssen (KB, Wikimedia-coördinator). Bouw: Claude Code, op basis van dit document.

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

Een **categorie** als invoer (alle bestanden in `Category:…` als lijst om door te bladeren, net als een aflevering in Delpher) komt in **fase 2** (besluit Olaf, 3-11-2026). Sinds 5-11-2026 uitgewerkt als dashboard met collecties, vóór de bewerker: zie hoofdstuk 17. Besluit Olaf (5-11-2026): dat wordt nu gebouwd, vóór OAuth.

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

Wie betaalde aanroepen mag doen: zie 8.3 (een toegangslijst). De limieten zijn aan te passen in het beheerpaneel (8.4). Op Toolforge komt daar een starttegoed van ongeveer $0,25 per ingelogde gebruiker bij, en daarna een eigen Meta-sleutel (8.6, voorstel).

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

**Groeperen** (wens Olaf, 5-11-2026, zoals in PowerPoint; gebouwd in 0.32.4, backlog 12g). Bij veel kleine objecten van één soort, zoals 15 waterdruppels en 9 bladeren op een stilleven, wil je niet 24 losse uitsneden, maar bijvoorbeeld *groep waterdruppels* en *groep bladeren*.

- **Groeperen (n)** onder de objecten in *Wat je vond*, naast *Dubbelingen samenvoegen*: maakt van de geselecteerde objecten (twee of meer) één object. Uitgeschakeld bij minder dan twee.
- **Groepeer alle …** per zoekterm, met één klik (besluit Olaf): onder de zoektermen staat *Groeperen: alle waterdruppels (15) · alle bladeren (9)* voor elke zoekterm met twee of meer losse objecten.
- **Het groepsobject**: het kader is het kleinste kader om alle leden heen; het masker is de vereniging van hun maskers (wat in minstens één masker valt). De naam is *groep:* + de soort + het aantal (*groep: waterdruppel (15)*, Engels *group: water drop (15)*); een bijschrift geeft hem een eigen naam. Bron en zekerheid: die van de leden (de laagste zekerheid), met het merkje *groep (15)*.
- **Bevestigen** (wens Olaf): groeperen en opheffen vragen eerst om bevestiging in een venster met de objecten, elk met een kleine uitsnede. Bij groeperen een veld voor een eigen naam (niet verplicht); de voorgestelde naam staat er in het grijs in. Geen aparte melding achteraf.
- **De leden blijven bewaard** in de groep, niet in de prullenbak. **Groep opheffen** (in de lijst) zet ze terug zoals ze waren, en verwijdert het groepsobject. Een beschrijving of bijschrift van de groep gaat dan verloren, na een bevestiging.
- **Beschrijven** (*Wat staat hierop?*, sinds 0.32.4–0.32.6): de vraag aan de AI krijgt een **AI-prompt** mee met de objecten van de groep. Zonder ruimte rond de uitsnede: *beschrijf alleen deze objecten; negeer de rest*; met ruimte: *beschrijf alleen deze objecten als onderwerp, en gebruik de omgeving alleen als context* (bijvoorbeeld een onderschrift). De eerdere beschrijvingen van de objecten gaan mee als context, gemarkeerd als eerdere AI-antwoorden die fout kunnen zijn. De rij *AI-prompt* toont wat meegaat; de schakelaar *Alleen deze objecten* zet het uit (API: `alleen_groep`).
- **Naar Commons** (besluit Olaf): een groep mag als één uitsnede naar Commons, zoals elk ander object: het kader in volledige resolutie, met het masker als transparante PNG. De beschrijving door de AI gaat over de groep als geheel.
- **Anders dan Dubbelingen samenvoegen**: samenvoegen maakt van objecten die vrijwel op dezelfde plek liggen één object en gooit de rest weg; groeperen houdt verschillende objecten bij elkaar en is terug te draaien.
- Gratis: alles gebeurt op de server, zonder aanroep van een model.
- **API**: POST `…/pagina/{n}/groepen` met `{"objecten": [ids]}` of `{"zoekterm": "water drop"}` geeft 201 met het groepsobject; DELETE `…/pagina/{n}/groepen/{id}` heft de groep op.

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

**Detailniveau** (wens Olaf, 5-11-2026, sinds 0.32.3): een schuif bij *Beschrijf deze afbeelding* en bij *Zoektermen opnieuw* bepaalt hoeveel soorten objecten de AI als zoekterm voorstelt: *Alleen het hoofdonderwerp* (1), *Hoofdzaken* (ongeveer 3), *Normaal* (tot 12, zoals voorheen) of *Veel details* (tot 20, ook kleine dingen zoals insecten, knopen en ornamenten). SAM zelf kent geen aantal: het vindt alle exemplaren van een zoekterm. De schuif bepaalt dus *waarnaar* gezocht wordt. Elk niveau heeft een eigen antwoord in de cache; *Normaal* houdt de antwoorden van vóór de schuif. Meer zoektermen betekent meer SAM-aanroepen als je ze allemaal laat zoeken; de knop toont het bedrag.

**Minimale zekerheid** (sinds 0.32.3): een schuif boven de objecten in *Wat je vond* (0 tot 95%) verbergt objecten van de AI-beelddetectie met een lagere zekerheid, ook wat al gevonden is, zonder nieuwe aanroep. Objecten zonder zekerheid (met de hand, uit Commons) blijven altijd zichtbaar. Wat verborgen is, is niet geselecteerd en gaat dus niet mee bij opslaan of beschrijven. De schuif bepaalt zo *hoeveel* je overhoudt. Onthouden in de browser.

### 7.7 AI-aangevulde versie

Idee en opdracht van Olaf (5-11-2026, backlog 19b; gebouwd in 0.32.4). Waar op het origineel iets voor een object stond (de jongen op de rug van de kat), heeft de uitsnede gaten. Een extra knop in de vergroter, **Afbeelding aanvullen met AI** (met het bedrag), laat **Muse Image** (`muse-image-1.0`, `/v1/images/edits`, $0,01 per beeld) die gaten invullen.

- **Wat er gebeurt**: de transparante uitsnede gaat op wit mee (hooguit 1536 pixels), met de vraag alleen de witte delen van het onderwerp in te vullen, in dezelfde stijl, techniek en kleuren, zonder iets te veranderen of toe te voegen. Zoeken op internet en code zijn uitgezet (`tool_enablement`). Het onderwerp komt uit de beschrijving, het bijschrift of de zoekterm.
- **Verzonnen, geen bron.** Het model weet niet wat er achter het andere voorwerp zat. De versie staat daarom apart, onder de uitsnede, met een AI-merkje en een waarschuwing, en gaat **nooit als uitsnede naar Commons**. Het Commons-concept en de upload gebruiken altijd de echte uitsnede.
- **Lagere resolutie**: Muse Image maakt het beeld in zijn eigen resolutie, en tekent het hele beeld opnieuw; ook buiten de gaten kan het iets veranderen.
- **Kosten**: in live-modus eerst een bevestiging met het bedrag; toegangslijst, daglimieten en verbruikslog gelden zoals bij de andere modellen. Gecachet per verstuurd beeld en vraag: nog eens vragen kost niets, *opnieuw* wel. In de proefmodus een nagebootste versie (de uitsnede op wit met *AI-aangevuld (dummy)*).
- **Bewaren**: het beeld staat in `cache/aanvullingen` en gaat na 30 dagen zonder gebruik weg, zoals uitsneden (12.1); het object onthoudt `aangevuld` (model, onderwerp, afmetingen, kosten). *Weghalen* haalt het van het object.
- **Downloaden** als PNG met *(AI-augmented)* in de bestandsnaam, of bekijken in een nieuw tabblad.
- **Doorzichtig en zoombaar** (sinds 0.32.6): het wit dat met de rand verbonden is, wordt doorzichtig (op een schaakbord, zoals de uitsnede); wit binnen het onderwerp en binnen de vorm van de uitsnede blijft. Uitsnede en aangevulde versie zijn in de vergroter te zoomen en te verschuiven zoals in de hoofdviewer. *Bron* en *Resolutie* staan eronder in dezelfde stijl als bij de uitsnede.
- **Eigen tabblad** *AI-aangevuld* in de vergroter, na *Uitsnede*, alleen als er een aangevulde versie is (sinds 0.32.5). Een schakelaar **Toon wat de AI invulde** legt een magenta laag over de plekken waar de uitsnede geen vorm had en de AI iets tekende; bij benadering.

### 7.8 3D-model van een uitsnede (nice-to-have)

Idee van Olaf (6-11-2026). **Nice-to-have, nog niet gepland en nog niet gebouwd** (backlog 19c). Van een uitgesneden object, bijvoorbeeld een luit op een stilleven, een 3D-model laten maken dat je in de vergroter kunt draaien en waarop je kunt inzoomen.

**Welk model.** De Meta Model API kent geen 3D (nagekeken 6-11-2026). Meta heeft wel **[SAM 3D Objects](https://ai.meta.com/research/sam3d/)**, een apart onderzoeksmodel dat van één beeld met het masker van een object een 3D-model met textuur maakt, ook als het object deels bedekt is. Zelf draaien vraagt een GPU (niet op Toolforge). Het is te huur via **[Runware](https://runware.ai/collections/best-3d-models)**, een aanbieder met één API voor veel modellen:

| Model (Runware) | Prijs per model (6-11-2026) | Kort |
| --- | --- | --- |
| **SAM 3D Objects** (`meta:sam@3d`, voorstel) | $0,005 tot $0,009 | Beeld + masker + prompt → GLB met textuur |
| TRELLIS.2 (Microsoft, open) | $0,0077 | Beeld → 3D; tweede keuze, zonder masker |
| Hunyuan 3D 3.1 Rapid / Pro | $0,225 | Pro met meerdere aanzichten en PBR-materialen |
| Tripo 3D v3.1 | $0,30 | Nauwkeurige vorm en textuur |
| Rodin Gen-2 | $0,40 | Nette mesh, lokaal bewerken |
| Meshy-6 | $0,80 | Productieklare mesh, low-poly |

SAM 3D Objects past het best: het vraagt precies wat de app al heeft (het originele beeld, het **masker** van het object en een prompt, bijv. de naam of de beschrijving) en geeft een **GLB** terug, voor ongeveer een halve cent. Runware vermeldt *Zero Data Retention*; bij de bouw nagaan wat dat precies inhoudt.

**Zoals *Afbeelding aanvullen met AI* (7.7):**
- Een knop **3D-model maken** in de vergroter, met het bedrag; eerst een bevestiging die zegt wat er gebeurt.
- Een eigen tabblad **3D** (als er een model is), met een 3D-weergave om te draaien en te zoomen (`<model-viewer>` of three.js via npm, geen CDN), het AI-merkje, de prompt, en een waarschuwing: **de achterkant, de diepte en de zijkanten zijn verzonnen**; geen bron, **nooit als uitsnede naar Commons**.
- Downloaden als **GLB**; weghalen (het bestand blijft de bewaartermijn lang in de cache, 12.1).
- Gecachet per beeld, masker, prompt en model: nog eens vragen kost niets, *opnieuw* wel.
- In de **proefmodus** een nagebootst 3D-model (bijv. een vlak met de uitsnede als textuur), zodat alles zonder kosten te testen is.
- Later ook op het canvas (18), als laag die je draait.

**Een tweede aanbieder naast Meta.** Dat vraagt:
- een eigen sleutel `RUNWARE_API_KEY`, alleen als omgevingsvariabele (`.env.example` bijwerken);
- een regel in de privacyverklaring (NL en EN) dat het beeld en het masker naar Runware gaan voor dit model;
- verbruik en kosten in het verbruikslog, met de aanbieder erbij, en binnen de daglimieten en het dagbudget (6.4); bij het starttegoed (8.6) telt het als één aanroep;
- bij de bouw: de licentie van SAM 3D (eigen licentie van Meta) en de voorwaarden van Runware nalezen, en of het resultaat gebruikt mag worden zoals hier bedoeld.

**API** (voorstel), zoals 7.7: GET, POST en DELETE `…/objecten/{id}/model3d` en GET `…/objecten/{id}/model3d.glb`.

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

Wens van Olaf (5-11-2026), uitgewerkt in 8.6: op Toolforge krijgt ook wie niet op de toegangslijst staat een starttegoed van ongeveer $0,25 voor betaalde aanroepen, en voert daarna een eigen sleutel voor de Meta Model API in (*bring your own key*).

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

### 8.5 Werk per gebruiker

Besluit Olaf (5-11-2026): op Toolforge werkt elke ingelogde gebruiker aan zijn eigen beelden. Twee mensen die dezelfde afbeelding openen, zien elk hun eigen objecten, bijschriften en prullenbak, en overschrijven elkaars werk niet. Tot en met fase 1 is er één gedeelde uitvoermap per afbeelding (`uitvoer/<mid>/`), zonder gebruiker; dat werkt alleen zolang er één gebruiker is (backlog 12c). Gebouwd wordt dit samen met OAuth (8.1, backlog 13a).

**Wat per gebruiker is en wat gedeeld blijft:**

| Wat | Waar | Waarom |
| --- | --- | --- |
| Objecten, maskers, bijschriften en hun versies, de prullenbak, opgeslagen uitsneden, Commons-concepten, gegevens van uploads | **Per gebruiker**: `uitvoer/gebruikers/<id>/<mid>/…` | Dit is iemands eigen werk |
| Collecties op het dashboard, met keuzes, voorscan-samenvattingen en de status in de werkset (17) | **Per gebruiker**: `uitvoer/gebruikers/<id>/collecties/` | Elke gebruiker heeft een eigen dashboard (besluit Olaf, 5-11-2026) |
| Originelen, Commons-antwoorden, paginabeelden, Wikidata | **Gedeeld**: `cache/` | Openbare gegevens; delen spaart schijfruimte en verzoeken aan Commons |
| Antwoorden van SAM en Muse Spark in de cache | **Gedeeld**: `cache/` | Dezelfde vraag over hetzelfde beeld kost dan maar één keer geld. Een antwoord uit de cache kost niets en telt dus niet mee voor de daglimiet. Wat iemand ermee doet (bewaren, aanpassen, weggooien) staat in zijn eigen map |
| Verbruik en daglimieten | **Centraal**, met de gebruikersnaam per aanroep (8.3); later in de database van het beheerpaneel (8.4) | Limieten tellen per gebruiker en voor de hele tool |
| *Bekeken* en *Opzij gezet*, kolombreedtes | In de browser (`localStorage`), zoals nu | Hoort bij het apparaat, niet bij de server |

**Voorstellen (gelden tot Olaf anders zegt):**

- **Mapnaam**: de vaste centrale gebruikers-id uit het OAuth-profiel (`sub`), niet de gebruikersnaam. Die verandert niet als iemand zijn account hernoemt, en bevat geen tekens die in een padnaam lastig zijn. De leesbare naam staat in een klein bestand in de map, voor het beheerpaneel. Onder `uitvoer/gebruikers/`, zodat een gebruikersmap nooit kan botsen met `uitvoer/verbruik` of een M-id.
- **REST-API**: de paden blijven gelijk. De server haalt de gebruiker uit de sessie; een verzoek kan nooit een gebruiker of map meegeven, dus niemand komt via de app bij het werk van een ander. Ook een beheerder niet, op het overzicht in het beheerpaneel na.
- **Zonder inloggen** (8.3: bekijken, gratis regio's, zip): het werk hoort bij de browsersessie, in `uitvoer/sessies/<sessie-id>/`, en verdwijnt na 1 dag. Wie daarna inlogt, neemt het mee naar zijn eigen map.
- **Lokaal, zonder OAuth** (fase 1, Olafs eigen server): alles valt onder één vaste gebruiker `lokaal`. De bestaande mappen `uitvoer/M…` verhuizen eenmalig naar `uitvoer/gebruikers/lokaal/`, met een commando dat eerst telt en pas met `--echt` verplaatst, zoals `opruimen`. Wie lokaal met de owner-only consumer inlogt (8.2), werkt in zijn eigen map; het werk van `lokaal` kan hij overnemen.
- **Slot**: één slot per gebruikersmap in plaats van één voor de hele uitvoer (`cutter/slot.py`), zodat gebruikers elkaar niet laten wachten. De opruimtaak neemt per map het slot van die map.
- **Bewaartermijnen** (12.1) gelden per gebruikersmap, met dezelfde termijnen. Het beheerpaneel (8.4) toont bij *Overzicht* de ruimte per gebruiker, en een beheerder kan de map van een gebruiker legen (met bevestiging, in het logboek).
- **Privacy**: de privacyverklaring (12.3) zegt dat het werk per gebruiker op de server staat, hoe lang, en dat beheerders alleen de omvang zien.
- **Samenwerken** aan één afbeelding (werk van een ander inzien of overnemen) valt hier buiten; dat is een later idee.

### 8.6 Starttegoed en een eigen Meta-sleutel (bring your own key)

Wens van Olaf (5-11-2026). Nog niet gebouwd. Zijn besluiten (5-11-2026) staan in 8.6.6.

#### 8.6.1 Het idee

- Op Toolforge krijgt **elke ingelogde gebruiker een starttegoed** van **100 aanroepen**, met SAM of Muse Spark. Dat kost de KB $0,25 (alleen SAM, $0,0025 per stuk) tot ongeveer $0,70 (alleen Muse Spark) per gebruiker (6.4). Dit tegoed betaalt de KB, met de sleutel van de KB (3).
- Met een **eigen sleutel voor de Meta Model API** betaalt de gebruiker zijn aanroepen zelf, bij Meta. Heeft hij er een, dan gaat die altijd voor, en blijft het tegoed bewaard (8.6.3).
- De sleutel is **alleen op de server** te gebruiken. Hij komt nooit terug naar de browser, niet in de API, niet in logs en niet in een export. Ook beheerders kunnen hem niet zien (8.6.4).
- Lokaal (fase 1, Olafs eigen server) verandert er niets: de sleutel uit `.env` geldt zonder tegoed.

Dit is iets anders dan de *eigen API-sleutel per gebruiker voor scripts* (11, fase 4). Die geeft toegang tot de API van de Commons Mineventory zelf. Deze sleutel is voor de API van Meta.

#### 8.6.2 Het tegoed

- **Eenmalig**, bij de eerste keer inloggen, niet elke dag of maand (besluit Olaf).
- **In aanroepen**, niet in dollars (besluit Olaf): **100 aanroepen**, of het nu SAM is ($0,0025) of Muse Spark ($0,005 tot $0,007, 6.4). Dat is eenvoudig uit te leggen. Wie alleen Muse Spark gebruikt, kost de KB wel bijna drie keer zoveel; het dagbudget (hieronder) blijft de rem. De interface toont *"Tegoed: 72 van 100 aanroepen"*.
- **De cache is gratis.** Een antwoord dat al in de cache staat (ook van een ander, 8.5), kost niets en gaat niet van het tegoed af.
- **Vooraf geboekt.** Net als het dagbudget nu (12c, 0.26.0) reserveert de app het bedrag vóór de aanroep en verrekent daarna. Zo kan het tegoed nooit onder nul, ook niet bij een voorscan van honderden bestanden (17.5).
- **De bestaande limieten** (6.4) blijven gelden voor alles wat de KB betaalt: het dagbudget van $2 en 500 aanroepen voor de hele tool, en 100 aanroepen per gebruiker per dag. Met 100 aanroepen per gebruiker kunnen per dag dus drie tot vijf nieuwe gebruikers hun tegoed opmaken voordat de tool aan haar grens zit (vijf bij alleen SAM, door de 500 aanroepen; ongeveer drie bij alleen Muse Spark, door de $2). Daarna meldt de app dat het gratis tegoed voor vandaag op is, en dat het met een eigen sleutel wel kan.
- **In het beheerpaneel** (8.4): de hoogte van het starttegoed, en per gebruiker het tegoed bekijken, extra tegoed geven of het tegoed op nul zetten. Elke wijziging staat in het logboek.
- **De toegangslijst** (8.3) blijft voor wie zonder tegoedgrens op kosten van de KB mag werken, zoals Olaf en collega's. Voor hen geldt alleen de daglimiet. Iedere andere ingelogde gebruiker heeft het starttegoed en daarna een eigen sleutel. De knop *Toegang aanvragen* blijft (besluit Olaf).

#### 8.6.3 Een eigen sleutel invoeren

- Op een pagina **Mijn account** (`/account`, via het menu bij de gebruikersnaam, 10.4): een wachtwoordveld *Eigen sleutel voor de Meta Model API*, met een korte uitleg en een link naar Meta om een sleutel te maken.
- **Opslaan** controleert de sleutel. Lukt dat, dan wordt hij versleuteld bewaard (8.6.4) en wordt het veld leeggemaakt. Daarna toont de pagina alleen nog *"Eigen sleutel ingesteld: eindigt op …a1b2, gecontroleerd op 5-11-2026"*, met *Vervangen* en *Verwijderen* (destructief, met bevestiging).
  - Bij de bouw nagaan of Meta een gratis manier heeft om een sleutel te controleren, bijvoorbeeld een lijst van modellen (16). Zo niet, dan controleert de app de sleutel bij de eerste echte aanroep en meldt het als die niet werkt.
- **Onthouden of alleen deze sessie**: standaard onthoudt de app de sleutel versleuteld. Wie dat niet wil, kiest *Alleen voor deze sessie*; dan staat hij alleen in de server-side sessie en verdwijnt hij bij uitloggen (besluit Olaf).
- **Een eigen daglimiet in dollars**, optioneel, als rem op je eigen kosten (bijv. $1 per dag).
- **Wanneer de app welke sleutel gebruikt**:
  1. Staat de gebruiker op de toegangslijst: de sleutel van de KB.
  2. Anders, met een eigen sleutel: altijd die sleutel, ook als er nog tegoed is; het tegoed blijft dan bewaard (besluit Olaf).
  3. Anders, zolang er tegoed is: de sleutel van de KB, één aanroep van het tegoed af.
  4. Anders: de knoppen met kosten zijn uitgeschakeld (niet verborgen, 10.4), met de uitleg *"Je tegoed is op. Voer je eigen sleutel in om verder te gaan."* en een link naar *Mijn account*.
- **Welke sleutel betaalt** staat bij de bevestiging vóór elke betaalde actie: *"Kost 8 aanroepen, van je tegoed (72 van 100 over)"* of *"Kost ongeveer $0,02, op je eigen sleutel"*.
- **Contributor of Standard** (6.3): dezelfde regels, ook met een eigen sleutel. Op *Mijn account* kan de gebruiker Contributor voor zijn eigen sleutel uitzetten, want het gaat dan om zijn eigen afspraak met Meta.
- **Verbruik**: elke aanroep in het verbruikslog krijgt `betaald_door`: `kb` (toegangslijst of tegoed) of `eigen_sleutel`, nooit de sleutel zelf. Aanroepen met een eigen sleutel tellen niet mee voor het dagbudget van de KB. *Mijn account* toont je eigen verbruik per dag.

#### 8.6.4 De sleutel beschermen

De sleutel is van de gebruiker en kost hem geld. Hij mag dus nooit uitlekken:

- **Alleen schrijven.** De API kan een sleutel opslaan, vervangen en verwijderen, maar nooit teruggeven. Een GET geeft alleen of er een sleutel is, de laatste vier tekens, wanneer hij gecontroleerd is, en of hij werkte.
- **Versleuteld bewaard**, in de database van het beheerpaneel (8.4; ToolsDB op Toolforge), per vaste gebruikers-id uit OAuth (8.5). De versleuteling gebruikt een geheim dat alleen een omgevingsvariabele is (`SLEUTEL_VERSLEUTELING`, op Toolforge met `toolforge envvars`), net als `MODEL_API_KEY`. Zonder dat geheim is de database waardeloos. De sleutel staat nooit in een bestand op de gedeelde schijf.
- **Alleen op de server ontsleuteld**, vlak voor een aanroep naar Meta, en alleen in de kop `Authorization` van die aanroep. Nooit in een cookie, de sessie in de browser, een URL, een foutmelding, een log, het verbruikslog, een export of de cache.
- **Logs schoonhouden**: de code logt nooit de koppen van een verzoek aan Meta. Een filter in de logging vervangt alles wat op een sleutel lijkt door `***`. Een test controleert dat een sleutel niet in de antwoorden, de logs of de bestanden in `uitvoer/` terechtkomt.
- **Ook beheerders zien hem niet.** Het beheerpaneel toont alleen of een gebruiker een eigen sleutel heeft. Een beheerder kan hem wel verwijderen, bijvoorbeeld bij misbruik; dat staat in het logboek en de gebruiker ziet het op *Mijn account*.
- **Opgeruimd**: een sleutel die een jaar niet gebruikt is, verwijdert de opruimtaak (12.1). Verwijderen is echt weg, ook uit de database.
- **CSRF-token** bij elk opslaan en verwijderen, alleen voor de ingelogde gebruiker zelf, alleen over HTTPS (Toolforge).
- **Privacyverklaring** (12.3): de app bewaart de sleutel versleuteld en gebruikt hem alleen voor de aanroepen van de gebruiker. Antwoorden die met een eigen sleutel zijn betaald, komen in de gedeelde cache (8.5) en kunnen dus anderen gratis helpen (besluit Olaf).

#### 8.6.5 API (voorstel)

| Methode | Pad | Wat |
| --- | --- | --- |
| GET | `/api/v1/account` | Ingelogd: tegoed (aanroepen over, van het starttegoed), toegangslijst ja/nee, eigen sleutel (alleen of hij er is, de laatste vier tekens, gecontroleerd), eigen daglimiet, verbruik vandaag |
| PUT | `/api/v1/account/meta-sleutel` | Een eigen sleutel opslaan of vervangen (`{"sleutel": "…", "onthouden": true}`). Controleert hem. 200 met dezelfde samenvatting als de GET, zonder de sleutel |
| DELETE | `/api/v1/account/meta-sleutel` | De eigen sleutel verwijderen |
| PATCH | `/api/v1/account` | Eigen daglimiet; Contributor uit voor de eigen sleutel |
| PATCH | `/api/v1/beheer/toegang/{gebruiker}` | Uitgebreid: tegoed bijboeken of op nul zetten; een eigen sleutel verwijderen (alleen beheerders) |

`/api/v1/status` noemt het tegoed of *eigen sleutel*, zodat de header het kan tonen. Een fout van Meta door een verkeerde of lege sleutel geeft een eigen code (`own_key_invalid`, `credit_exhausted`), met een vertaling in nl.json en en.json.

#### 8.6.6 Besluiten van Olaf (5-11-2026)

1. **Eenmalig**: het starttegoed krijg je één keer, bij de eerste keer inloggen.
2. **In aanroepen**: 100 aanroepen, of het nu SAM of Muse Spark is (niet in dollars, zoals voorgesteld).
3. **Een eigen sleutel gaat altijd voor**: wie een eigen sleutel heeft, betaalt daarmee, en het tegoed blijft bewaard (niet eerst het tegoed, zoals voorgesteld).
4. **Onthouden**: de sleutel standaard versleuteld onthouden, met de keuze *Alleen voor deze sessie*.
5. **Toegangslijst**: blijft, voor wie onbeperkt op kosten van de KB mag werken.
6. **Gedeelde cache**: antwoorden die met een eigen sleutel zijn betaald, komen in de gedeelde cache.

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
| GET, PATCH | `/api/v1/account` | Eigen tegoed, verbruik en instellingen (8.6.5) |
| PUT, DELETE | `/api/v1/account/meta-sleutel` | Eigen Meta-sleutel opslaan of verwijderen; nooit terug te lezen (8.6.4) |
| GET | `/account` | Mijn account (UI) |

API-gebruik zonder browser: met de sessiecookie na het inloggen. Een eigen API-sleutel per gebruiker voor scripts komt **later, in fase 4** (besluit 3-11-2026).

## 12. Toolforge

### 12.1 Opzet

- Een tool-account op Toolforge: **`commons-mineventory`** (URL `https://commons-mineventory.toolforge.org/`). De naam moet Engels zijn; de repo heet hetzelfde (besluit Olaf, 3-11-2026; naam gewijzigd 5-11-2026, eerst `commons-cutter`). Op 5-11-2026 nagekeken: `KBNLwikimedia/commons-mineventory` bestaat nog niet op GitHub; of de naam vrij is op Toolforge (toolsadmin) en Toolhub, wordt nagekeken bij de deploy (backlog 12f). Olaf is de enige maintainer; andere maintainers voegt hij toe op toolsadmin. Beheerders in de app staan los daarvan (8.4).
- **Build Service** met een `Procfile` (`web: gunicorn --workers 2 --bind 0.0.0.0:$PORT wsgi:app`) en `requirements.txt`; deployen met `toolforge build start <git-url>` en `toolforge webservice buildservice restart`. Alternatief: de klassieke `webservice python3.11` met een venv. Voorstel: Build Service.
- **De frontend bouwen** (Vite, zie 10.2). Op Toolforge draait alleen Python; Node.js is alleen nodig om `static/dist/` te maken. Twee routes, bij de bouw kiezen:
  1. **In de Build Service zelf**: als die naast Python ook een Node-stap kan draaien (`npm ci && npm run build`). Het eenvoudigst, als het kan.
  2. **In een GitHub Action** (terugvaloptie): bij elke push naar `main` bouwt de Action de frontend en zet het resultaat in een aparte branch (bijv. `deploy`), die de Build Service ophaalt. `static/dist/` komt dan nooit in `main`.
- **Configuratie** met `toolforge envvars create …` (`MODEL_API_KEY`, `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`, `FLASK_SECRET_KEY`, en voor de eigen sleutels van gebruikers `SLEUTEL_VERSLEUTELING`, 8.6.4). Nooit in de repo.
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
  - **30 dagen**: opgeslagen uitsneden en maskers (`uitvoer/<mid>/pagina_<n>/jpg`, `png`, `maskers`; vanaf fase 2 per gebruiker onder `uitvoer/gebruikers/<id>/`, zie 8.5); het object vergeet dan dat het opgeslagen was, en opnieuw opslaan maakt ze weer aan. Ook voorbeelden en maskerafbeeldingen in de cache. Objecten die op Commons staan, houden hun gegevens.
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
6a. Het dashboard met collecties uit categorieën (17), zonder voorscan door AI, lokaal onder de gebruiker `lokaal` (besluit Olaf 5-11-2026: nu bouwen, vóór OAuth).

**Fase 2: OAuth, upload naar een testwiki, categorieën**

7. OAuth 2.0 server-side, met een owner-only consumer. Daarmee het werk per gebruiker gescheiden (8.5).
8. Upload via de stash, SDC, `{{Image extracted}}` op het origineel; alles eerst op de testwiki (welke, blijkt bij de bouw).
9. Beheerpaneel (8.4): beheerders, toegangslijst, aanvragen, limieten (100 per gebruiker; 500 aanroepen en $2 per dag in totaal), noodknoppen, logboek; opslag in SQLite (lokaal) en ToolsDB (Toolforge). Daarna het starttegoed en de eigen Meta-sleutel (8.6), want die hebben OAuth en de database nodig.
10. Een categorie als invoer: bladeren door de bestanden van `Category:…` (5.1). Vervallen: wordt het dashboard (17), al in fase 1 (6a).

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
20. Nice-to-have: een canvas om uitsneden te combineren tot nieuwe werken (18), niet voor Commons.
21. Nice-to-have: een 3D-model van een uitsnede via SAM 3D Objects op Runware (7.8), niet voor Commons.

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
| Dashboard met collecties | Nu bouwen, vóór OAuth; de bewerker naar `/bewerken`; voorlopig geen voorscan door AI (5-11-2026) | 17, 17.10 |
| Starttegoed | Eenmalig 100 aanroepen; een eigen Meta-sleutel gaat altijd voor; de toegangslijst blijft (5-11-2026) | 8.6, 8.6.6 |
| Werk per gebruiker | Elke ingelogde gebruiker werkt in een eigen uitvoermap; cache en AI-antwoorden blijven gedeeld (5-11-2026) | 8.5 |

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
- Of de Meta Model API een gratis manier heeft om een sleutel te controleren, en wat Meta toestaat bij het gebruik van sleutels van anderen in een tool (8.6.3).
- De goedkoopste verzoeken om per bestand van een collectie te zien welke uitsneden er met de Commons Mineventory of ander gereedschap op Commons staan (17.4, *Al bewerkt*).
- Hoeveel miniaturen `prop=imageinfo&iiurlwidth=` per verzoek levert bij `generator=categorymembers` (17.3), en of miniaturen van `upload.wikimedia.org` sneller dan één per seconde mogen (17.3).

## 17. Dashboard: collecties uit categorieën

Op verzoek van Olaf (5-11-2026). Nog niet gebouwd. Zijn besluiten (5-11-2026) staan in 17.10. Het belangrijkste: **nu bouwen, vóór OAuth**, en **voorlopig geen voorscan door AI**; je kiest met de hand (17.5).

### 17.1 Doel

Vóór het werk per afbeelding (de bewerker, 10.4) komt een **dashboard**. Daar stel je **collecties** samen: sets afbeeldingen die je daarna één voor één in de bewerker detecteert, uitsnijdt en beschrijft.

1. Je opent een **categorie** van Commons. De app toont alle afbeeldingen erin als **miniaturen**.
2. Per afbeelding geef je met een **vinkje** aan of er iets in staat dat de moeite van het uitsnijden waard is: illustraties, wapens, portretten, foto's in een album.
3. Je kiest **met de hand**. Een *voorscan* met SAM, die per afbeelding laat zien of er objecten in staan, is ontworpen maar uitgesteld (17.5).
4. Met één knop wordt de selectie een **werkset**. Die loop je in de bewerker één voor één door, met *Vorige* en *Volgende* en een status per afbeelding (17.6).

Dit vervangt "Een categorie als invoer" (5.1, backlog 15a) en is de eerste stap naar "Batch over meerdere bestanden" (13, fase 4 punt 14).

### 17.2 Begrippen

- **Collectie**: een benoemde set Commons-bestanden met een bron (nu: één categorie), en per bestand een keuze en een status. Een collectie is alleen gegevens; de afbeeldingen blijven op Commons.
- **Keuze** per bestand: *wel* (aangevinkt: hier staan objecten in), *niet* (bewust uitgevinkt) of *nog niet bekeken*.
- **Voorscan**: een detectie met SAM op de hele afbeelding, met een of enkele zoektermen die voor de hele collectie gelden. De uitkomst is een voorstel voor de keuze.
- **Werkset**: de bestanden van een collectie met keuze *wel*, in de volgorde van de collectie. Er is geen apart object "werkset": het is een weergave van de collectie.
- **Status** per bestand in de werkset: *te doen*, *bezig* (in de bewerker geopend), *klaar* of *overgeslagen*.

### 17.3 Een categorie openen

- **Invoer**: `Category:Album amicorum van Jacob van Bronckhorst van Batenburg`, `Categorie:…`, een URL van de categoriepagina, of alleen de naam. Normaliseren zoals bij een bestand (5.1). Een redirect (`{{Category redirect}}`) wordt gevolgd en gemeld.
- **Eerst een voorproefje** (gratis, één verzoek, `prop=categoryinfo`): het aantal bestanden en het aantal subcategorieën. Daarna maak je de collectie aan, met de naam van de categorie als voorgestelde naam.
- **Bestanden ophalen**: `generator=categorymembers&gcmtype=file&prop=imageinfo&iiprop=url|size|mime|sha1&iiurlwidth=<stap>`, per blok (`gcmcontinue`), met een eigen User-Agent, `maxlag=5`, caching en ongeveer één verzoek per seconde (5.2). De M-id is `M` + de page-id; daar is geen extra verzoek voor nodig.
- **Subcategorieën**: standaard alleen de categorie zelf. Onder de miniaturen staan de subcategorieën als chips met hun aantal bestanden; met een klik voeg je er een aan de collectie toe (één niveau diep; besluit Olaf).
- **Grootte**: hooguit **1000 bestanden** per collectie. Bij een grotere categorie meldt de app dat, en neemt de eerste 1000 in de volgorde van Commons (`cmsort=sortkey`; besluit Olaf).
- **Bestandstypen** (5.4): SVG, GIF, video en audio staan er grijs en zonder vinkje in, met de reden. PDF, DjVu en meerpagina-TIFF zijn één tegel met het aantal pagina's erop; een latere voorscan alleen op pagina 1 (besluit Olaf).
- **Bijwerken**: *Opnieuw ophalen* zoekt nieuwe en verdwenen bestanden in de categorie. Nieuwe bestanden komen erbij als *nog niet bekeken*. Een verdwenen bestand blijft in de collectie staan, met een merkje. Gemaakt werk gaat nooit verloren.

**Miniaturen en privacy.** De browser laadt niets van Wikimedia (12.3). De server haalt elke miniatuur op in een vaste stapgrootte van Commons (5.2, bijv. 250 px; de stappen nog verifiëren, 16), cachet die 7 dagen (zoals `cache/commons`, 12.1) en levert hem aan de browser. De miniaturen laden pas als ze in beeld komen (lazy).

**Snelheid.** Bij één verzoek per seconde duren 500 miniaturen ruim 8 minuten. Miniaturen in standaardmaten komen uit de cache van `upload.wikimedia.org` en kosten Commons weinig. Daarvoor **4 tegelijk** (ongeveer 4 per seconde; besluit Olaf), en de API-verzoeken naar `api.php` op één per seconde houden. Bij de bouw nagaan wat de richtlijnen van Wikimedia hierover zeggen (16).

### 17.4 Het dashboard

**Startpagina** met de collecties als kaarten:

```
┌ Commons Mineventory ─────────────────────────────── NL/EN  Inloggen ┐
│ Collecties                                                          │
│ [ Category:… of URL                                ] [Categorie openen] │
│ Of open één bestand: [ File:… of URL              ] [Openen]        │
│                                                                     │
│ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐      │
│ │ ▦▦▦▦ (4 mini's)  │ │ ▦▦▦▦             │ │ ▦▦▦▦             │      │
│ │ Album amicorum … │ │ Book of Hours …  │ │ Prenten 1650 …   │      │
│ │ 212 bestanden    │ │ 48 bestanden     │ │ 530 bestanden    │      │
│ │ 37 gekozen       │ │ 12 gekozen       │ │ nog niet bekeken │      │
│ │ ███░░░ 9/37 klaar│ │ ██████ 12/12     │ │                  │      │
│ │ 2 dagen geleden  │ │ gisteren         │ │ vandaag          │      │
│ └──────────────────┘ └──────────────────┘ └──────────────────┘      │
└─────────────────────────────────────────────────────────────────────┘
```

- Per kaart: vier miniaturen, de naam, de bron (categorie, met link naar Commons), het aantal bestanden, het aantal gekozen, de voortgang van de werkset (*klaar* van het totaal) en wanneer de collectie het laatst is geopend.
- In een menu (⋯) per kaart: *Hernoemen*, *Opnieuw ophalen* en *Verwijderen* (destructief, met bevestiging). Verwijderen haalt alleen de collectie weg; objecten en uitsneden in de bewerker blijven.
- Eén bestand openen kan vanaf het dashboard nog steeds, zonder collectie (zoals nu).

**Collectiepagina** (`/collecties/<id>`): het raster met miniaturen.

```
┌ Album amicorum van Jacob van Bronckhorst van Batenburg ──────── ⋯ ┐
│ Category:Album amicorum … ↗ · 212 bestanden · 37 gekozen · 9 klaar │
│                                                                    │
│ Toon: (Alle) (Gekozen) (Niet gekozen) (Nog niet bekeken)           │
│       (Voorscan: objecten) (Voorscan: niets)     Grootte: ──●──    │
│ [Alles kiezen] [Niets kiezen]                                      │
│                                                                    │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐              │
│ │☑ ▢▢  │ │☐     │ │☑ ▢   │ │◻     │ │☑ ▢▢▢ │ │◻ PDF │              │
│ │ 3 AI │ │ 0 AI │ │ 1 AI │ │      │ │ 3    │ │ 12p  │              │
│ │klaar │ │      │ │bezig │ │      │ │      │ │      │              │
│ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘              │
│                                                                    │
├ Voorscan met SAM ──────────────────────────────────────────────────┤
│ Zoektermen: [illustration ×] [coat of arms ×] [+ term]             │
│ 175 bestanden nog niet gescand × 2 termen = 350 aanroepen          │
│                       [Voorscan (175) – ongeveer $0,88]            │
├────────────────────────────────────────────────────────────────────┤
│ 37 gekozen · 28 te doen                [Werkset openen (37) ▶]     │
└────────────────────────────────────────────────────────────────────┘
```

- **Tegel**: de miniatuur, een vinkje linksboven, de bestandsnaam (ingekort; in volle lengte bij aanwijzen), en na een voorscan de gevonden kaders als dunne rechthoeken op de miniatuur, met het aantal en een AI-merkje. Onderaan de status in de werkset.
- **Kiezen**: klik op het vinkje; klik op de tegel opent een grotere weergave (de lightbox, met Vorige/Volgende en de toetsen ← →, *spatie* = vinkje aan/uit). Shift-klik kiest een reeks. Een tegel zonder keuze heeft een open vinkje (◻), een bewust uitgevinkte een leeg vinkje (☐).
- **Filters** als chips met hun aantal, zoals de facetten op `/objecten`. Een schuif voor de grootte van de miniaturen, onthouden in de browser.
- **Voorscan**: het deel *Voorscan met SAM* in de schets en de filters *Voorscan: …* komen pas als de voorscan terugkomt (17.5). In de eerste bouw zijn ze er niet.
- **Hoofdactie** (de enige gevulde knop): *Werkset openen (n)*. Uitgeschakeld als er niets gekozen is.
- Wat er al met een bestand gebeurd is, staat ook op de tegel; zie hieronder.

**Al bewerkt met de Commons Mineventory** (wens Olaf, 5-11-2026). Op het dashboard en in het raster zie je welke afbeeldingen al bewerkt zijn, zodat je geen werk dubbel doet en geen uitsneden dubbel uploadt. Er zijn twee bronnen, allebei gratis:

1. ***Door jou, in de app*** (uit je eigen map, 8.5; geen verzoek aan Commons). Per bestand het verste dat je kwam:
   - *geopend*: wel in de bewerker geweest, maar geen objecten;
   - *objecten (n)*: gevonden, maar nog niet opgeslagen;
   - *uitsneden (n)*: opgeslagen als JPG of PNG;
   - *geüpload (n)*: met de app naar Commons gebracht.
2. ***Op Commons, door wie dan ook*** (leesverzoeken, per blok van 50 bestanden, gecachet voor 1 dag):
   - *Uitsneden met de Commons Mineventory (n)*: bestanden in de volgcategorie `Category:Uploaded with Commons Mineventory` (9.3) met `{{Extracted from}}` naar dit origineel. Dat geldt ook voor uploads door anderen en vanaf een andere server.
   - *Uitgesneden met ander gereedschap (n)*: `{{Image extracted}}` op het origineel noemt bestanden die niet uit de Mineventory komen, bijvoorbeeld van CropTool (7.5). Ook dat is werk dat je niet dubbel wilt doen.
   - *Regio's op Commons (n)*: het origineel heeft al P180 met P2677 (7.5). Die regio's kun je gratis gebruiken, en ze kunnen ook met het venster uit 9.7 zijn gezet.

   Welke verzoeken het goedkoopst zijn, bepaal ik bij de bouw (16). Bijvoorbeeld `prop=linkshere` op de bestanden van de collectie, beperkt tot bestandspagina's, en dan `prop=categories&clcategories=` voor de volgcategorie. Of eenmalig de hele volgcategorie lezen en die per origineel indelen.

   Daarnaast houdt de app een **centraal register** bij van wat ze zelf op Commons heeft gezet: uploads, `{{Image extracted}}` en regio's op het origineel, met datum en gebruikersnaam. Dat is openbare informatie (het staat op Commons), dus het register is gedeeld en niet per gebruiker (8.5). Zo weet de app het meteen, ook voordat de cache van Commons verloopt.

**Hoe je het ziet:**
- **Op de tegel** een merkje in de hoek: blauw voor *door jou bewerkt*, groen met het aantal voor *op Commons met de Mineventory*, grijs voor *ander gereedschap*. Bij aanwijzen staat er wat en wanneer, met links naar de uitsneden op Commons.
- **Filters**: *Nog niet bewerkt*, *Door jou bewerkt*, *Al op Commons*.
- **Op de kaart van de collectie**: *"212 bestanden · 18 al op Commons · 9 door jou bewerkt"*.
- **Bij de voorscan** (later, 17.5): bestanden die al uitsneden op Commons hebben, slaat de voorscan standaard over. Dat spaart geld. Met een vinkje *Ook bestanden die al bewerkt zijn* scan je ze toch.
- **Bij het kiezen**: een bestand dat al op Commons is uitgesneden, wordt nooit vanzelf aangevinkt, ook niet door de voorscan. Kies je het zelf, dan blijft het merkje staan.
- **In de bewerker**: open je zo'n bestand, dan staat onder de titel een melding: *"Van dit bestand staan al 3 uitsneden op Commons, gemaakt met de Commons Mineventory"*, met de links. Bij *Naar Commons* (9.1) waarschuwt de controle vooraf al voor dezelfde afbeelding (SHA-1, 9.5). Dit komt er dus bij, eerder in het werk.
- **Waarschuwen, niet blokkeren** (zoals bij de rechten, 5.3): je kunt een bewerkt bestand altijd openen en opnieuw bewerken, bijvoorbeeld om een object toe te voegen dat de vorige keer ontbrak (besluit Olaf).

**Werk van andere gebruikers dat nog niet op Commons staat** blijft onzichtbaar. Iedereen werkt in een eigen map (8.5), en wat iemand nog niet gepubliceerd heeft, is van hem (besluit Olaf).

### 17.5 Voorscan met SAM

**Uitgesteld** (besluit Olaf, 5-11-2026): voorlopig geen voorscan door AI. Bij een grotere categorie van bijvoorbeeld 2000 bestanden kost die al snel $5; Olaf kiest dan liever met de hand. Wat hieronder staat, is het ontwerp voor later (backlog 19a). Komt de voorscan terug, dan zijn twee vragen nog open: SAM of ook Muse Spark, en automatisch aanvinken of alleen tonen.

- **Wat**: per bestand één SAM-aanroep per zoekterm (6.1, een gewone zoekterm uit 7.1), op dezelfde verkleinde versie als in de bewerker (1920 px). De zoektermen gelden voor de hele collectie en worden bij de collectie bewaard. Voorstel voor de eerste term: `illustration`. De gebruiker past ze aan, zoals in *Zoeken* (EN/MIN-syntax en de vertaaltabel werken ook hier).
- **Hergebruik**: de voorscan is dezelfde detectie als *Zoeken* in de bewerker en gebruikt dezelfde cache (per SHA-1 + pagina + term + model). Open je het bestand later in de bewerker, dan staan de gevonden objecten er al, als kandidaat (niet geselecteerd), en zoeken op dezelfde term kost niets meer.
- **Keuze voorstellen**: vindt de voorscan minstens één object met een score boven de drempel (voorstel: 0,5), dan wordt het vinkje gezet, met een AI-merkje (*voorgesteld door AI*). Vindt hij niets, dan blijft het bestand *nog niet bekeken*, met *niets gevonden*. Een keuze die de gebruiker zelf maakte, verandert de voorscan nooit. Open: automatisch aanvinken, of alleen tonen?
- **Kosten en bevestiging**: de knop draagt het bedrag (bestanden zonder voorscan × termen × $0,0025). Vóór de start volgt een bevestiging met het aantal aanroepen en het bedrag (6.4). Een voorscan van een term die al in de cache staat, kost niets en telt niet mee.
- **Uitvoeren**: vanuit de browser, bestand voor bestand, met voortgang en een knop **Stoppen** (12.1, *Lange taken*). Bij een limiet (429) stopt de voorscan netjes, met de melding hoeveel er nog te doen is. Wat klaar is, blijft bewaard.
- **Limieten** (6.4): een categorie van 300 bestanden met één term is 300 aanroepen. Dat is meer dan de 100 per gebruiker per dag en het grootste deel van de 500 voor de hele tool. Voorstel: de voorscan houdt zich aan dezelfde limieten en loopt dus soms over meer dagen (*Verder met de voorscan*), en de beheerder kan de limieten in het beheerpaneel (8.4) verhogen. Op Toolforge geldt daarnaast het starttegoed (8.6): een voorscan van een grote categorie past daar meestal niet in, en vraagt dus een eigen sleutel. De bevestiging zegt vooraf hoeveel van het tegoed gaat en wat op de eigen sleutel komt.
- **Alternatief: AI-suggesties per bestand** (het paginaoverzicht, 7.6) als voorscan, met Muse Spark. Dat kost ongeveer $0,007 per bestand, bijna drie keer een SAM-term, maar geeft ook een beschrijving en zoektermen die passen bij dat bestand, en die staan in de bewerker meteen klaar. Open: eerst alleen SAM, of ook het paginaoverzicht?
- **Fase 1-regel**: gebouwd en getest met de `DummyDetector` en fixtures. Live alleen op Olafs eigen server, door Olaf zelf.

### 17.6 De werkset in de bewerker

- *Werkset openen* opent de bewerker op het eerste bestand dat nog *te doen* is: `/bewerken?collectie=<id>&mid=M…`.
- Onder de invoerbalk staat dan een **werksetbalk**:

```
◀ Vorige │ Album amicorum … · 10 van 37 · 9 klaar │ ✓ Klaar  ⤼ Overslaan │ Volgende ▶ │ Naar de collectie
```

- *Vorige* en *Volgende* lopen door de werkset (ook met Alt+← en Alt+→; de pijltjes zonder Alt blijven van de viewer en de vergroter).
- **Status**: een bestand wordt *bezig* zodra je het opent. *Klaar* en *Overslaan* zet je zelf, en gaan meteen naar het volgende bestand dat nog *te doen* is. Geen automatische *klaar*, want de app weet niet wanneer je klaar bent (besluit Olaf).
- De kolom **Bekeken** toont boven de gewone lijst de werkset, met de status per bestand, zodat je er ook rechtstreeks naartoe springt.
- Al het andere in de bewerker werkt zoals nu. De werkset verandert niets aan de objecten, uitsneden of het Commons-concept per bestand.
- **Later** (tweede iteratie, niet in de eerste bouw): acties over de hele werkset vanaf de collectiepagina, zoals *AI-suggesties voor alle gekozen bestanden*, *Selectie opslaan voor alle bestanden* of één keuzemenu voor de upload van de hele werkset (9.1).

### 17.7 Bewaren

- **Per gebruiker** (besluit Olaf, 5-11-2026): op Toolforge heeft elke ingelogde gebruiker een eigen dashboard met eigen collecties. Die staan in de eigen map van de gebruiker (8.5): `uitvoer/gebruikers/<id>/collecties/<collectie-id>.json`, met `<id>` de vaste gebruikers-id uit OAuth. Twee gebruikers die dezelfde categorie openen, hebben elk een eigen collectie, met eigen vinkjes en een eigen status. Wat gedeeld blijft (8.5): de miniaturen en de Commons-gegevens in de cache, en de antwoorden van SAM. Een voorscan die een ander al deed, kost dus niets, maar de keuzes die daaruit volgen staan bij jezelf.
  - De API kent geen gebruiker in het pad. De server haalt de gebruiker uit de sessie, en een collectie van een ander geeft 404, ook als je het id kent.
  - Zonder inloggen werkt het dashboard voor de browsersessie en verdwijnt het na 1 dag (8.5). Lokaal, zonder OAuth, valt alles onder de gebruiker `lokaal`.
  - Tot OAuth er is (backlog 13 en 13a), bouwen we het al zo: alle opslag gaat via één functie die de map van de huidige gebruiker geeft (nu altijd `lokaal`). Dan hoeft er bij OAuth niets te verhuizen of te veranderen.
- Een collectie bevat: naam, bron, zoektermen voor de voorscan, aangemaakt, laatst geopend, en per bestand de M-id, titel, SHA-1, afmetingen, MIME, aantal pagina's, keuze (met *door wie*: gebruiker of AI), de samenvatting van de voorscan (per term het aantal objecten en de hoogste score) en de status.
- De kaders op de miniaturen komen uit de detectiecache, niet uit de collectie; de collectie blijft dus klein.
- Het id is kort en willekeurig (bijv. `c-7f3a9b`), niet de naam van de categorie: twee collecties uit dezelfde categorie mogen.
- **Bewaartermijn** (12.1): een collectie die een jaar niet geopend is, ruimt `opruimen` op, net als een pagina.
- Schrijven onder het slot (`cutter/slot.py`) en atomisch, zoals de objecten.

### 17.8 Pagina's en REST-API (voorstel)

**Pagina's**:

| Pad | Wat |
| --- | --- |
| `/` | Het dashboard (de collecties). Met `?url=`, `?titel=` of `?mid=` stuurt het door naar `/bewerken?…`, zodat bestaande links blijven werken (besluit Olaf) |
| `/bewerken` | De bewerker zoals nu (10.4); met `?collectie=` de werksetbalk |
| `/collecties/<id>` | Het raster van één collectie |

**API** onder `/api/v1`, volgens de afspraken (zelfstandige naamwoorden, meervoud, een GET kost niets):

| Methode | Pad | Wat |
| --- | --- | --- |
| GET | `/categorie?titel=…` | Normaliseren en voorproefje: titel, aantal bestanden en subcategorieën, de subcategorieën. Gratis |
| GET, POST | `/collecties` | Alle collecties; een nieuwe aanmaken (`{"bron": {"categorie": "…"}, "naam": "…"}`). 201 |
| GET, PATCH, DELETE | `/collecties/{id}` | Eén collectie; naam en zoektermen wijzigen; verwijderen |
| POST | `/collecties/{id}/verversingen` | Opnieuw ophalen uit Commons (gratis; maakt een nieuwe stand, vandaar POST). 201 |
| GET, PATCH | `/collecties/{id}/bestanden` | De bestanden, met filters (`keuze`, `status`, `voorscan`, `bewerkt`: `nee`, `door_jou`, `op_commons`); per bestand ook wat er al mee gedaan is (17.4, *Al bewerkt*); keuze en status van een of meer bestanden wijzigen |
| GET | `/bestand/{mid}/bewerkingen` | Wat er met dit bestand al gebeurd is: door jou in de app, en op Commons (met de Mineventory, met ander gereedschap, regio's). Gratis, gecachet |
| GET | `/bestand/{mid}/miniatuur?w=` | De miniatuur, via de server en gecachet (17.3) |
| GET | `/collecties/{id}/voorscans/raming` | Later (17.5): kostenraming voor de voorscan; voert niets uit |
| POST | `/collecties/{id}/bestanden/{mid}/voorscans` | Later (17.5): de voorscan van één bestand (SAM, betaald, binnen de limieten). 201. De browser roept dit bestand voor bestand aan, met Stoppen |

docs/api.md en `cutter/openapi.py` worden bijgewerkt bij de bouw.

### 17.9 Eerste bouw

Klein en zonder kosten, in deze volgorde, elk met tests:

1. **Commons**: categorie normaliseren, voorproefje, bestanden ophalen per blok, miniaturen via de server (fixtures voor de tests).
2. **Collecties**: opslag in de map van de huidige gebruiker (nu `lokaal`, 17.7), de API uit 17.8 zonder voorscan, `opruimen`. Een test controleert dat twee gebruikers elkaars collecties niet zien.
3. **Dashboard en collectiepagina** (Vue en Codex, tweetalig): kaarten, raster, vinkjes, filters, lightbox, *Werkset openen*, en de merkjes *Al bewerkt* (eerst door jou, daarna op Commons; het centrale register komt met de upload, 14).
4. **Bewerker naar `/bewerken`**, met de werksetbalk en de werkset in *Bekeken*.
5. **Voorscan**: uitgesteld (17.5, besluit Olaf). De eerste bouw kost dus niets.

Daarna itereren op aanwijzing van Olaf. De voorscan (17.5) en acties over de hele werkset (17.6, *Later*) komen in een volgende ronde.

### 17.10 Besluiten van Olaf (5-11-2026)

1. **Startpagina**: het dashboard op `/`, de bewerker naar `/bewerken`; oude links (`/?url=…`, `/?mid=…`) sturen door.
2. **Voorscan**: voorlopig **geen voorscan door AI**: "bij grotere categorieën van bv. 2000 beelden kost dat al snel 5 USD, dan doe ik het liever handmatig". De vragen SAM of ook Muse Spark, en automatisch aanvinken of alleen tonen, komen terug als de voorscan terugkomt (17.5, backlog 19a). Daarmee vervalt ook de vraag naar de limieten voor de voorscan.
3. **Subcategorieën**: standaard alleen de categorie zelf, subcategorieën (één niveau) met een klik erbij; hooguit 1000 bestanden per collectie.
4. **Meerpaginabestanden**: één tegel per bestand (een latere voorscan alleen op pagina 1).
5. **Miniaturen**: 4 tegelijk van `upload.wikimedia.org`; `api.php` blijft op één verzoek per seconde.
6. **Status *klaar***: alleen met de hand.
7. **Fasering**: nu bouwen, vóór OAuth, lokaal onder de gebruiker `lokaal` (13, fase 1 punt 6a). Backlog 15a wordt daarmee het eerstvolgende punt.
8. **Al bewerkt**: alleen waarschuwen, met een merkje en een melding; nooit tegenhouden.
9. **Werk van anderen in de app**: onzichtbaar tot het op Commons staat.


## 18. Canvas: een speelveld voor uitsneden (nice-to-have)

Idee van Olaf (6-11-2026). **Nice-to-have, nog niet gepland en nog niet gebouwd** (backlog 25). Olafs antwoorden op het vragenformulier staan in 18.12.

### 18.1 Doel

Uit één boek, vriendenboek, atlas, tijdschrift of handschrift (één Commons-categorie) ontstaan veel losse transparante uitsneden, al dan niet aangevuld met AI (7.7). Het **canvas** is een speelveld om daarmee te spelen: objecten erop slepen, verschuiven, schalen, draaien, combineren en groeperen tot **nieuwe samengestelde werken**, ook met uitsneden uit andere werken en met transparante beelden van anderen op Commons.

Zo'n werk heeft geen documentaire of encyclopedische waarde. Het gaat daarom **nooit naar Commons**: je bewaart het om verder te werken, en je exporteert het als beeld, met de bronnen en licenties erbij.

### 18.2 Bronnen

Links op het scherm staan de objecten die je kunt gebruiken, als miniaturen om naar het canvas te slepen:

- **Al je eigen uitsneden**, uit alle bestanden, te filteren per collectie of categorie (17), per bestand en op naam. Van elke uitsnede het origineel en, als die er is, de AI-aangevulde versie (7.7). Alleen objecten met een vorm (transparante PNG) of een rechthoek.
- **Wikimedia Commons**:
  - standaard de categorie [Category:Transparent background](https://commons.wikimedia.org/wiki/Category:Transparent_background) (wens Olaf), met subcategorieën op aanvraag;
  - **zelf categorieën toevoegen** (bijv. de categorie van een ander boek of van uploads met de Commons Mineventory); de app onthoudt ze per gebruiker;
  - **zoeken** op Commons, beperkt tot bestanden die transparantie kunnen hebben (PNG, WebP, SVG, GIF).
  Alles via de server (privacy, 12.3), met de gewone regels voor Commons: eigen User-Agent, caching, ongeveer één verzoek per seconde.
- **Eigen afbeelding uploaden** vanaf je computer (PNG, WebP of SVG met transparantie, ook JPG). Zo'n bestand blijft privé, in je eigen map (8.5), en gaat niet naar Commons.
- **Openverse** (beelden met een vrije licentie, open API) als dienst buiten Commons, als die er later bij komt; niet in de eerste versie (zie 18.12, vraag 1 en 2).

### 18.3 Het scherm

Een eigen pagina **`/canvas`**, te openen vanaf het dashboard (17) en vanaf een collectie; elk canvas heeft een eigen adres (`/canvas/<id>`).

```
┌ Commons Mineventory · Canvas: "Vriendenboek-collage" ────────── Opslaan  Exporteren ▾ ┐
│ ┌ Objecten ──────────────┐ ┌──────────────────────────────────┐ ┌ Lagen ───────────┐ │
│ │ Bron: [Mijn uitsneden ▾]│ │                                  │ │ 👁 🔒 tekst       │ │
│ │ 🔍 zoeken               │ │     🐈 (AI)        🌸            │ │ 👁 🔒 groep: 🍋×3 │ │
│ │ ┌──┐┌──┐┌──┐┌──┐       │ │          👦📦 ← geselecteerd     │ │ 👁 🔒 jongen ●    │ │
│ │ │🐈││👦││🌸││🍋│       │ │   🍋🍋🍋                         │ │ 👁 🔒 kat (AI)    │ │
│ │ └──┘└──┘└──┘└──┘       │ │                 🦅               │ │ 👁 🔒 achtergrond │ │
│ │ ── Commons ──          │ │                                  │ ├ Eigenschappen ───┤ │
│ │ Transparent background  │ └──────────────────────────────────┘ │ (●) origineel    │ │
│ │ + categorie toevoegen   │  A4 staand · 100% · raster aan       │ ( ) AI-aangevuld │ │
│ │ ── Eigen bestand ──     │                                      │ schaal, draai,   │ │
│ │ [ Uploaden ]            │                                      │ dekking, bron ↗  │ │
│ └────────────────────────┘                                      └──────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

- **Links**: de bronnen (18.2). Slepen naar het canvas plaatst het object op ware grootte, of passend als het groter is dan het canvas.
- **Midden**: het canvas, met zoom en verschuiven zoals in de viewer (muiswiel, slepen met de spatiebalk), een raster en uitlijnhulp.
- **Rechts boven**: het **lagenpaneel**, zoals in Photoshop (wens Olaf): elk object is een eigen laag, de bovenste ligt vooraan. Per laag: zichtbaar (oog), vergrendeld (slot), naam, en slepen om de volgorde te veranderen. Een groep is een laag die je openklapt.
- **Rechts onder**: de eigenschappen van de geselecteerde laag (18.5).
- Tweetalig en in Codex-stijl, zoals de rest van de app.

### 18.4 Bewerkingen

| Bewerking | Hoe |
| --- | --- |
| Verplaatsen, schalen, draaien | Slepen; hoekgrepen (Shift houdt de verhouding); draaigreep; of getallen in de eigenschappen |
| Spiegelen | Horizontaal of verticaal, knop of toets |
| Voor en achter | In het lagenpaneel slepen, of *Naar voren*, *Naar achteren*, *Helemaal voor*, *Helemaal achter* |
| Kopiëren en plakken | Ctrl+C en Ctrl+V dupliceren de laag (ook een groep), iets verschoven |
| Groeperen | Ctrl+G groepeert de geselecteerde lagen, Ctrl+Shift+G heft de groep op; een groep verplaats, schaal en draai je als geheel |
| Ongedaan maken | Ctrl+Z en Ctrl+Y (of Ctrl+Shift+Z), voor elke bewerking |
| Doorzichtigheid | Per laag, 0 tot 100% |
| Achtergrond | Doorzichtig, een kleur, of een afbeelding (uit dezelfde bronnen) als onderste laag |
| Tekst | Een tekstlaag met lettertype (alleen meegeleverde lettertypen, geen externe), grootte, kleur |
| Uitlijnhulp | Een raster en hulplijnen die opspringen bij randen en middens van andere lagen |
| Verwijderen | Del of Backspace; ongedaan te maken |

Meer selecteren met Shift-klik of een rechthoek trekken. Met de pijltjes schuif je een laag een pixel, met Shift tien.

### 18.5 Origineel of AI-aangevuld

- Elke laag die uit een eigen uitsnede komt, heeft in de eigenschappen een schakelaar **origineel / AI-aangevuld** (wens Olaf). Standaard **het origineel**; AI-aangevuld kan alleen als die versie er is (7.7).
- Een AI-aangevulde laag heeft in het lagenpaneel het AI-merkje, zodat altijd te zien is wat verzonnen is.
- Vanuit de eigenschappen kun je een uitsnede zonder aangevulde versie meteen laten aanvullen (*Afbeelding aanvullen met AI*, met het bedrag en een bevestiging, zoals in de vergroter).

### 18.6 Bewaren

- **Meerdere canvassen per gebruiker op de server** (besluit Olaf), in de eigen map (8.5): `uitvoer/gebruikers/<id>/canvassen/<canvas-id>.json`, met een lijst op het dashboard (naam, miniatuur, laatst bewerkt).
- Een canvas bewaart **verwijzingen**, geen kopieën: per laag de bron (eigen uitsnede met M-id, pagina en object-id; een Commons-bestand; een eigen upload), de versie (origineel of AI-aangevuld), positie, schaal, draaiing, spiegeling, dekking, zichtbaarheid en volgorde. Eigen uploads staan in `uitvoer/gebruikers/<id>/canvas-bestanden/`.
- **Automatisch opslaan** na elke bewerking (na een korte pauze), plus *Opslaan als* om een kopie te maken.
- Verdwijnt een bron (uitsnede in de prullenbak, verlopen bewaartermijn, verwijderd van Commons), dan blijft de laag staan met een merkje en de laatst bekende miniatuur, en kun je hem vervangen.
- **Bewaartermijn**: een canvas dat een jaar niet geopend is, ruimt `opruimen` op (12.1). De uitsneden die een canvas gebruikt, tellen als gebruikt, zodat ze niet verlopen zolang het canvas leeft.

### 18.7 Exporteren

- **PNG** (ook met doorzichtige achtergrond), **JPG**, **PDF** (bijvoorbeeld om te printen), **SVG** (met een eigen groep per laag) en een **projectbestand** (JSON met de verwijzingen, om te delen of later weer te openen).
- **Resolutie**: in het formaat van het canvas (18.8), met de lagen in de beste beschikbare resolutie: uitsneden in volledige resolutie van het origineel, AI-aangevulde versies in hun eigen (lagere) resolutie.
- **Bronvermelding** (besluit Olaf): bij elke export automatisch een lijst met de gebruikte bronnen en hun licenties, **als bijlage** (een tekstbestand naast het beeld, of een pagina in de PDF) **en onder het beeld** (een smalle strook, uit te zetten). Per bron: titel, maker, licentie en link naar Commons; bij een AI-aangevulde versie *aangevuld met AI (Muse Image)*; bij een eigen upload *eigen bestand*. Een waarschuwing als een licentie *gelijk delen* vraagt (CC BY-SA), of als een bron geen vrije licentie heeft.
- **Niet naar Commons**: er is geen uploadknop. Delen gaat via de export of het projectbestand (besluit Olaf).
- De export wordt op de server gemaakt (de originelen staan daar), als downloadbestand.

### 18.8 Formaat

Een **gekozen formaat** bij het aanmaken, later te wijzigen (besluit Olaf): A4 en A3 (staand of liggend), vierkant, 16:9, of een eigen maat in pixels. Voor A4 en A3 een resolutie in dpi (standaard 300) voor het printen.

### 18.9 AI op het canvas (betaalde extra)

Besluit Olaf: mag, als **betaalde extra met Muse Image** (7.7), met het bedrag op de knop en eerst een bevestiging. Voorbeelden, uit te werken bij de bouw:

- een **achtergrond laten maken** bij een omschrijving (bijv. *a 17th-century landscape*), als onderste laag;
- het geheel **in één stijl laten samenvloeien** (licht, schaduw, kleur), als nieuwe laag of nieuw canvas, met het origineel bewaard.

Wat de AI maakt, krijgt het AI-merkje en staat in de bronvermelding als *gemaakt met AI*.

### 18.10 Techniek (bij de bouw kiezen)

- Een canvasbibliotheek via npm (bijv. Konva of Fabric.js), meegebouwd door Vite; **geen CDN** (12.3). De viewer uit de Delpher Uitsnijder blijft zoals hij is; het canvas is een eigen onderdeel.
- Beelden van Commons komen via de server (een proxy met cache), net als de miniaturen in 17.3, zodat de browser niets van Wikimedia laadt en het canvas geen CORS-problemen heeft bij de export.
- Grote originelen: op het canvas een verkleinde versie (bijv. hooguit 2000 px), bij de export de volledige resolutie.

### 18.11 Pagina's en REST-API (voorstel)

| Methode | Pad | Wat |
| --- | --- | --- |
| GET | `/canvas`, `/canvas/<id>` | Pagina's: de lijst en één canvas |
| GET, POST | `/api/v1/canvassen` | Je canvassen; een nieuw aanmaken (naam, formaat). 201 |
| GET, PUT, DELETE | `/api/v1/canvassen/{id}` | Eén canvas (lagen en instellingen); bewaren; verwijderen |
| GET | `/api/v1/canvas-bronnen?soort=uitsneden\|commons\|eigen&zoek=…&categorie=…` | Wat links staat: eigen uitsneden, Commons (categorieën en zoeken), eigen uploads. Gratis |
| POST | `/api/v1/canvas-bestanden` | Een eigen afbeelding uploaden (privé). 201 |
| POST | `/api/v1/canvassen/{id}/exports` | Een export maken (`{"formaat": "png" \| "jpg" \| "pdf" \| "svg" \| "json"}`), met de bronvermelding. 201 met een downloadlink |

### 18.12 Antwoorden van Olaf (6-11-2026)

1. **Bronnen**: al je eigen uitsneden uit alle bestanden; zoeken op Wikimedia Commons; een eigen afbeelding uploaden. Andere zoekdiensten koos Olaf hier niet.
2. **Buiten Commons**: als het er komt, dan **Openverse** (alleen vrije licenties, open API). Omdat Olaf bij vraag 1 geen andere zoekdiensten koos: niet in de eerste versie.
3. **Bronvermelding**: automatisch, als bijlage en onder het beeld.
4. **Bewerkingen**: alles uit 18.4: verplaatsen, schalen, draaien, spiegelen, voor en achter, kopiëren en plakken, groeperen, ongedaan maken, doorzichtigheid, achtergrond, tekst, uitlijnhulp en raster.
5. **Standaardversie**: het origineel, AI-aangevuld met de schakelaar.
6. **Bewaren**: meerdere canvassen per gebruiker op de server.
7. **Export**: PNG (ook doorzichtig), JPG, PDF, SVG en een projectbestand.
8. **Formaat**: een gekozen formaat.
9. **Plek**: een eigen pagina `/canvas`, vanaf het dashboard en een collectie.
10. **AI**: ja, als betaalde extra met Muse Image, met bedrag en bevestiging.
11. **Delen**: alleen via export of projectbestand.
12. **Extra (opmerking Olaf)**: [Category:Transparent background](https://commons.wikimedia.org/wiki/Category:Transparent_background) als vaste bron; zelf andere Commons-categorieën toevoegen; werken in **lagen** zoals in Photoshop, met een eigen laag per object (PNG en andere formaten met transparantie).

**Nog open** (later, bij het oppakken): de naam van de functie (*Canvas*, *Speelveld*, *Collage*?), welke AI-extra's eerst (18.9), en of een canvas ook objecten uit de collecties van andere gebruikers mag gebruiken zodra die op Commons staan.

**Afhankelijk van**: werk per gebruiker (8.5) voor het bewaren, het dashboard (17) als ingang, de AI-aangevulde versie (7.7).
