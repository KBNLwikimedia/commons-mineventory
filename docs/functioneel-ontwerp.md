# Functioneel ontwerp – Commons Uitsnijder

Werktitel: **Commons Uitsnijder**. Status: concept v0.3, 3 november 2026 (v0.2: antwoorden van Olaf op de belangrijkste vragen verwerkt, en de regio's uit de gestructureerde gegevens uitgewerkt in 7.5; v0.3: frontend met Vite, zie 10.2). Opdrachtgever en eigenaar: Olaf Janssen (KB, Wikimedia-coördinator). Bouw: Claude Code, op basis van dit document.

Dit FO beschrijft een variant van de [Delpher Uitsnijder](https://github.com/ookgezellig/delpher-uitsnijder) (versie 0.18.13, lokaal in `D:\KB-OPEN\github-repos\delpher-uitsnijder`) voor afbeeldingen op Wikimedia Commons. Waar dit document "de Delpher Uitsnijder" zegt, gaat het om die app: haar FO, `docs/api.md`, `docs/commons-beschrijving.md`, `docs/beeld-taalmodel.md` en `docs/meta-sam-api.md`. Die documenten blijven de bron voor alles wat ongewijzigd wordt overgenomen. Dit FO beschrijft vooral wat anders is.

Punten met **[Vraag]** wachten op een keuze van Olaf; ze staan ook in hoofdstuk 15.

## 1. Doel

Een experimentele webapp waarmee je een bestand op Wikimedia Commons opent, er objecten in detecteert (met box en masker), ze uitsnijdt als transparante PNG of als JPG, ze laat beschrijven, en de uitsneden na controle **weer op Commons publiceert**, met een nette koppeling naar het origineel.

Voorbeelden:

- Uit een album amicorum de losse wapenschilden, portretten en tekeningen halen, zoals uit [Album amicorum van Jacob van Bronckhorst van Batenburg (8077131573).jpg](https://commons.wikimedia.org/wiki/File:Album_amicorum_van_Jacob_van_Bronckhorst_van_Batenburg_(8077131573).jpg) (2000 × 1429 px, publiek domein).
- Uit een prent, kaart of krantenpagina op Commons de losse figuren, vignetten, logo's of illustraties uitsnijden.
- De figuren die op Commons al als regio zijn vastgelegd, los uitsnijden. Op [Book of Hours of Philip of Burgundy - KW76F - folio 283r - Heaven - All Saints - Jean Le Tavernier.jpg](https://commons.wikimedia.org/wiki/File:Book_of_Hours_of_Philip_of_Burgundy_-_KW76F_-_folio_283r_-_Heaven_-_All_Saints_-_Jean_Le_Tavernier.jpg) staan 13 heiligen met een eigen rechthoek in *beeldt af* (zie 7.5). Elke heilige wordt een eigen bestand.
- Een gescande boekpagina (PDF, DjVu of TIFF met meerdere pagina's) doorzoeken op illustraties.
- Alle uitsneden van een bestand in één keer voorbereiden voor upload, met beschrijving, licentie, categorieën en *beeldt af* (depicts).

## 2. Verhouding tot CropTool

[CropTool](https://commons.wikimedia.org/wiki/Commons:CropTool) (croptool2.toolforge.org, broncode [wpmed/croptool2](https://github.com/wpmed/croptool2), PHP, GPL-2.0, OAuth 1.0a, ondersteund door Wiki Project Med) is het gangbare gereedschap om op Commons een bestand bij te snijden. De Commons Uitsnijder is daar een **verdieping** op, geen vervanging.

| | CropTool | Commons Uitsnijder |
| --- | --- | --- |
| Selectie | Eén rechthoek, met de hand getrokken; randdetectie | Veel objecten tegelijk, gevonden met AI (zoekterm, Snel zoeken, Aanwijzen, Alles detecteren), met maskers; handmatige rechthoek als terugvaloptie |
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
- Vanuit de app een link "Openen in CropTool" bij elke uitsnede die al op Commons staat, met de box als vooringevulde selectie (CropTool accepteert die in de querystring; het exacte formaat bij de bouw nagaan).

## 3. Uitgangspunten

- **Experiment.** Geen officiële dienst van de KB of de Wikimedia Foundation. Dat staat in de footer.
- **Detectie en beschrijving** rechtstreeks via de **Meta Model API** (SAM 3.1 en Muse Spark), zoals in de Delpher Uitsnijder. Eén API-sleutel van de KB, op de server (besluit Olaf, 3-11-2026).
- **Inloggen** met het Commons-account van de gebruiker via **OAuth 2.0**. Uploads gebeuren op naam van die gebruiker.
- **Uploaden alleen na een klik** van de gebruiker, na een overzicht en een bevestiging. Nooit vanzelf.
- **Geen live aanroepen naar de Meta Model API** zonder expliciete opdracht van Olaf. Tests draaien op fixtures.
- **Hosting**: lokaal tijdens de bouw, daarna op **Wikimedia Toolforge**.
- **RESTful**: alles via `/api/v1`; de UI is een client van dezelfde API. Een GET kost nooit geld en verandert niets.
- **Taal**: interface en documentatie in het Nederlands; code, identifiers en commentaar in het Engels. Codex en de API-velden in het Nederlands, zoals in de Delpher Uitsnijder. **[Vraag]** Ook een Engelse interface (i18n), gezien het internationale publiek van Commons?
- **Volledige resolutie**: uitsneden en uploads altijd op de oorspronkelijke resolutie van het Commons-bestand, nooit op de verkleinde versie die naar het model gaat.

## 4. Wat hergebruikt wordt en wat vervalt

### 4.1 Overnemen (kopiëren en aanpassen, geen gedeelde bibliotheek)

| Delpher Uitsnijder | In de Commons Uitsnijder |
| --- | --- |
| `uitsnijder/detectie/basis.py`, `dummy.py`, `meta_sam.py`, `maskers.py` | Ongewijzigd: de detectorinterface, `DummyDetector`, `MetaSamDetector` (met `meta-sam-parser`), maskers lui decoderen en cachen |
| `uitsnijder/detectie/dienst.py` | De kern blijft: zoektermen, cache per afbeelding+term+model, samenvoegen van dubbelingen (IoU), selectie, prullenbak, opslaan, uitsnede-JPG. De Delpher-delen (zones, ALTO, bijschriften, koppeling aan artikelen) gaan eruit |
| `uitsnijder/prompts.py` | EN/MIN-syntax, de vertaaltabel en de Snel zoeken-groepen. De groepen aanpassen aan Commons (zie 7.4) |
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
- De **Delpher-stijl** (`delpher-theme.css`, het Delpher-logo) en de Firefox-extensie (die kan later terugkomen als "Openen in de Commons Uitsnijder", zie de backlog).
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

**[Vraag]** Ook een **categorie** als invoer (alle bestanden in `Category:…` als lijst om door te bladeren), net als een aflevering in Delpher? Voorstel: fase 2.

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
- **PDF en DjVu**: per pagina, als de gerenderde pagina van Commons (`page<n>-<breedte>px`) op de grootste beschikbare breedte. Dat is niet de "echte" scan, maar meestal de beste die Commons levert. **[Vraag]** Voldoende, of moeten we de PDF zelf renderen (dat vraagt een zware bibliotheek, strijdig met "geen zware libs")?
- **Meerpagina-TIFF**: per pagina, uit het origineel.
- **SVG, GIF, video en audio**: niet ondersteund; de app meldt dat.
- **Grote bestanden**: Commons heeft scans van honderden megapixels. Pillow beschermt tegen "decompression bombs"; op Toolforge is het werkgeheugen per webservice beperkt. Voorstel: tot **100 megapixel** gewoon verwerken; daarboven alleen detecteren op de verkleinde versie en uitsnijden in tegels uit het origineel, of weigeren met een melding. **[Vraag]** Welke grens?

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
- De server stuurt een verkleinde versie (standaard 2000 px breed) als base64-data-URL. **[Vraag]** Of de publieke URL van de Commons-thumbnail: dat spaart bandbreedte, maar dan haalt Meta het beeld zelf op bij Wikimedia (met hun eigen User-Agent). Voorstel: data-URL, zoals nu.
- Antwoord via `meta-sam-parser`; maskers lui decoderen en cachen.
- Cache per **SHA-1 van het bestand** + pagina + term + model. Een nieuwe versie van het bestand (andere SHA-1) geeft dus een nieuwe detectie.

### 6.2 Beschrijving (Muse Spark)

"Wat staat hierop?" per object en "Wat staat op deze pagina?" per bestand, zoals in `docs/beeld-taalmodel.md`, met dezelfde JSON-velden (`soort`, `onderwerp`, `bedrijf_of_naam`, `tekst_in_beeld`, `tekst_rond_beeld`, `beschrijving`, `zekerheid`). Verschillen:

- **Context** voor het model: de beschrijving en de caption van het origineel (als platte tekst, ingekort), de zichtbare categorieën en de bestaande *beeldt af*-items, uitdrukkelijk als hulp en niet als waarheid. In plaats van de ALTO-tekst.
- **Nieuw veld `wikidata_suggesties`**: hooguit drie zoektermen voor *beeldt af* (bijv. "coat of arms", "Jacob van Bronckhorst van Batenburg"). De app zoekt die gratis op met `wbsearchentities`; de gebruiker kiest het item. Het model verzint zelf geen Q-nummers.
- **Taal**: beschrijving in het Nederlands, plus een Engelse caption. **[Vraag]** Altijd beide talen?

### 6.3 Contributor of Standard

De regel uit de Delpher Uitsnijder ("Contributor alleen als alles klopt") wordt:

1. P6216 van het origineel is **publiek domein** (`Q19652`) én de licentie is een PD-sjabloon (geen CC). Bij CC-licenties zou Meta het werk mogen gebruiken om te trainen zonder de voorwaarden (naamsvermelding, gelijk delen) na te komen; dat doen we niet.
2. Geen labels **Merk**, **Persoonlijkheidsrechten** of **Origineel ter discussie**.
3. `BEELDMODEL_CONTRIBUTOR=aan` (standaard `uit`).

Anders: Standard. **[Vraag]** Wil de KB dit überhaupt voor bestanden van anderen op Commons? Voorstel: standaard uit laten.

### 6.4 Kosten en limieten

Op basis van de metingen in de Delpher Uitsnijder:

| Actie | Aanroepen | Kosten (ongeveer) |
| --- | --- | --- |
| Eén zoekterm | 1 SAM | $0,0025 |
| Aanwijzen (puntprompt) | 1 SAM | $0,0025 |
| Alles detecteren | 8 SAM | $0,02 |
| Wat staat hierop? (`low`) | 1 Muse | $0,005 (Standard), $0,0003 (Contributor) |
| Wat staat op deze pagina? (`low`) | 1 Muse | $0,007 |
| Slim detecteren | 1 Muse + n SAM | ±$0,03 |
| Een typische sessie: één bestand, Alles detecteren, tien beschrijvingen | 8 SAM + 10 Muse | ±$0,07 |

Limieten:

- **Daglimiet per gebruiker** (`DAGLIMIET_PER_GEBRUIKER`, 100 aanroepen, besloten 3-11-2026) en een **algemene daglimiet** (`DAGLIMIET_AANROEPEN`, voorstel 1000) plus een **dagbudget in dollars** (`DAGBUDGET_USD`, voorstel $5). Boven een limiet: 429 met de resterende tijd.
- In live-modus vraagt de app vóór elke betaalde actie om bevestiging, met het bedrag (zoals nu).
- Meta: 3000 verzoeken per minuut voor SAM; Contributor heeft lagere limieten.

Wie betaalde aanroepen mag doen: zie 8.3 (een toegangslijst).

## 7. Detectiemodi

Alle modi uit de Delpher Uitsnijder blijven, op één gedeelde selectie per pagina.

### 7.1 Zoeken met een zoekterm

EN/MIN-syntax, Nederlandse termen via de vertaaltabel naar Engels, één SAM-aanroep per begrip.

### 7.2 Snel zoeken

Vaste groepen, aangepast aan wat er op Commons staat: wapens en heraldiek, portretten, figuren en personen, dieren, planten en bloemen, gebouwen, kaarten, schepen, initialen en vignetten, logo's en beeldmerken, handschrift en tekstblokken, foto's in een album. Elke groep is een vooringevulde prompt.

### 7.3 Aanwijzen

Klikken op een plek zonder bekend object: een puntprompt aan SAM (één betaalde aanroep), resultaat als kandidaat. Shift-slepen: een handmatige rechthoek (gratis).

### 7.4 Bulk-operaties

Alles detecteren, Slim detecteren (eerst het paginaoverzicht, dan SAM met de voorgestelde termen), Alles beschrijven, Dubbelingen samenvoegen. Elke stap met bevestiging en kosten.

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

"Wat staat op deze pagina?" met zoektermen als chips onder Snel zoeken, zoals nu.

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

Besloten door Olaf (3-11-2026): betaalde aanroepen alleen voor een **toegangslijst** (`TOEGESTANE_GEBRUIKERS`, Commons-gebruikersnamen, komma-gescheiden), met een daglimiet van **100 aanroepen per gebruiker** (`DAGLIMIET_PER_GEBRUIKER=100`). Ingelogde gebruikers die niet op de lijst staan, zien de knoppen met kosten grijs, met de uitleg waarom. Uploaden mag iedere ingelogde gebruiker, want dat kost niets. **[Vraag]** Wie komen er op de lijst, en hoe vraagt iemand toegang aan?

In het verbruikslog staat per aanroep de Commons-gebruikersnaam. **[Vraag]** Mag dat (privacy op Toolforge, zie 12.3), of alleen een gehashte naam?

## 9. Publiceren op Commons

### 9.1 Werkwijze

Gebaseerd op `docs/commons-beschrijving.md` van de Delpher Uitsnijder:

1. **Concept per object** (veld `commons`): bestandsnaam, beschrijving, caption (nl/en), datum, maker, bron, licentie, categorieën, *beeldt af*, rechtenlabel, en de keuze PNG of JPG. Gratis samengesteld, bewerkbaar in de vergroter.
2. **Keuzemenu**: alle opgeslagen uitsneden van het bestand, met miniatuur, concept, rechtenlabel en een vinkje. Standaard aangevinkt: alleen **In orde** en **Naamsvermelding verplicht**.
3. **Controle vooraf** (gratis, alleen lezen): bestaat de naam al, bestaat dezelfde afbeelding al (SHA-1), bestaan de categorieën.
4. **Proefweergave**: de volledige wikitekst en de SDC-verklaringen per uitsnede.
5. **Uploaden (n)**, alleen na het bevestigingsvinkje: *"Ik heb de beschrijving, de licentie en de rechten gecontroleerd. De bestanden worden op mijn naam geüpload."* Eén tegelijk, met voortgang en een knop **Stoppen**.
6. **Na de upload**: de Commons-URL bij het object; optioneel `{{Image extracted}}` op het origineel (9.3); een link "Openen in CropTool".

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
[[Category:Uploaded with Commons Uitsnijder]]
```

- **`{{Extracted from|File:…}}`** op de nieuwe pagina, net als CropTool.
- **`{{Extracted from|File:…}}` is verplicht** op elke uitsnede, JPG en gemaskerde PNG, zodat altijd te zien is wat het bronbestand is (eis van Olaf, 3-11-2026). De app laat het niet weghalen.
- **`{{Image extracted|<nieuw bestand>}}`** op het origineel: een bewerking van de pagina van iemand anders. CropTool doet dit ook. Besloten door Olaf (3-11-2026): **standaard aan, per upload uit te zetten**. Eén bewerking voor alle uitsneden van een sessie; een bestaand sjabloon wordt aangevuld, niet gedupliceerd. De bewerkingssamenvatting noemt de nieuwe bestanden.
- Gebruikt het origineel `{{Artwork}}`, `{{Photograph}}` of `{{Book}}`, dan neemt de app dat sjabloon over met de velden die op de uitsnede ook kloppen (maker, datum, instelling, inventarisnummer) en een nieuwe `description`/`title`. Welke velden precies: bij de bouw vastleggen per sjabloon.
- **Licentie**: alle sjablonen uit de licentiesectie van het origineel, letterlijk. Bij `{{Flickrreview}}` of `{{LicenseReview}}` met een bevestiging: de bevestiging komt **niet** mee (CropTool doet dat ook niet), maar wel een verwijzing naar het origineel.
- **Categorieën**: de zichtbare categorieën van het origineel als voorstel (aan te vinken), plus wat de gebruiker toevoegt. Onderhoudscategorieën en `{{Assessments}}`, `{{QI}}`, `{{FP}}` en dergelijke komen nooit mee.
- **Volgcategorie** `Category:Uploaded with Commons Uitsnijder` (verborgen). **[Vraag]** Akkoord, en wie maakt die categorie aan?
- **Uploadsamenvatting**: *"Uitsnede uit [[File:…]] met de [[Commons:Commons Uitsnijder|Commons Uitsnijder]]; beschrijving deels opgesteld met een taalmodel en gecontroleerd door de uploader."*

### 9.4 Gestructureerde gegevens (SDC)

Na de upload, in één `wbeditentity` op `M<pageid>`:

| Verklaring | Waarde |
| --- | --- |
| Caption (`labels`) | nl, en optioneel en; hooguit 250 tekens |
| P180 *beeldt af* | Door de gebruiker gekozen Wikidata-items (6.2), eventueel met P1354 *getoond met* |
| P6216 *auteursrechtstatus*, P275 *licentie* | Overgenomen van het origineel |
| P170 *maker*, P571 *datum van creatie* | Overgenomen van het origineel, als aanwezig |
| P195 *collectie* | Overgenomen van het origineel, als aanwezig |
| Relatie met het origineel | **Te onderzoeken.** Kandidaten: P7482 *bron van het bestand* met een kwalificator die naar het origineel wijst, of alleen de wikitekst (`{{Extracted from}}`). Kijken wat de gemeenschap gebruikt |

**Backlog:** op het origineel een P180 met P2677 *relatieve positie in afbeelding* voor elk object, zodat de regio's ook op het origineel vindbaar zijn. Dat is een bewerking van het origineel; alleen als Olaf het wil.

### 9.5 PNG of JPG

- **JPG** (rechthoek, volledige resolutie, kwaliteit 95) is de standaard: de gangbare vorm op Commons voor uitsneden van scans en foto's.
- **PNG met transparantie** (de vorm van het object) als keuze per object, bijvoorbeeld voor een wapen of een figuur. Waarschuwing als de PNG groter is dan 20 MB.
- Optioneel beide, als twee bestanden die naar elkaar verwijzen (`|other versions=`).
- Een masker dat (bijna) rechthoekig is, wordt altijd JPG.

### 9.6 Testen

- Eerst alleen met nagebootste antwoorden van de API (fixtures).
- Daarna echte uploads op een testwiki: `test-commons.wikimedia.org` of de bètacluster (`commons.wikimedia.beta.wmcloud.org`). **Bij de bouw nagaan** welke van de twee OAuth en SDC ondersteunt.
- `COMMONS_UPLOAD=uit` (standaard): alles werkt behalve de uploadknop; dan kun je de wikitekst kopiëren of een zip downloaden met bestanden en wikitekst.

## 10. Interface met Codex

### 10.1 Welke Codex

Het verzoek noemde Codex **v0.4.1**. Dat is een oude versie (2022), nog zonder de **CSS-only-componenten**. De huidige versie is **2.7.0** (november 2026). Besloten door Olaf (3-11-2026): **Codex 2.x met Vue 3, gebouwd met Vite**. Dit wijkt bewust af van de Delpher Uitsnijder, die geen build-stap heeft. Waarom 2.x: de huidige versie sluit aan bij wat Commons zelf gebruikt (Vector 2022), heeft CSS-only-componenten en levert de designtokens als CSS-variabelen.

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
- **Taal**: componentnamen en code in het Engels, teksten in de interface in het Nederlands, net als nu. Later Engels via een vertaalbestand (fase 4).

### 10.3 Look en feel

- Zo dicht mogelijk bij Commons in Vector 2022: witte achtergrond, `--color-progressive` (#36c) voor acties, de lettertypen van de systeeminterface, rustige randen.
- **Geen Commons-logo als eigen merk**: het Commons-logo is een merk van de Wikimedia Foundation. Wel de naam "Commons Uitsnijder", een eigen eenvoudig icoon (schaar of uitsnede) en de zin "werkt met Wikimedia Commons". **[Vraag]** Akkoord, of het logo vragen aan de WMF?
- Kleuren alleen via Codex-tokens; eigen toevoegingen (maskerkleuren, selectie) in `static/css/app.css` als variabelen.

### 10.4 Indeling

Zoals in de Delpher Uitsnijder, met Commons-inhoud:

- **Header**: icoon, "Commons Uitsnijder", label *experiment*, rechts **Inloggen** of de gebruikersnaam met een menu (Mijn uploads, Uitloggen).
- **Invoerbalk**: Commons-URL of titel, knop **Openen**. Daaronder: titel, miniatuur, licentie (als Codex-*chip*), maker, datum, link naar de bestandspagina, en een uitklapbare **Metadata** (beschrijving, categorieën, SDC).
- **Links**: bestand › pagina's (bij PDF/DjVu/TIFF, als miniaturen) › objecten.
- **Midden**: de viewer met zoom en pan, overlays voor boxen en maskers, Aanwijzen met een groene rand.
- **Rechts**: het detectiepaneel in uitklapbare blokken (Codex *Accordion*-stijl): Bulk-operaties, Zoeken, Snel zoeken, Voorstellen voor deze pagina, Aanwijzen, **Uit Commons**. Daaronder de resultatenlijst met vinkjes, en de knoppen **Selectie opslaan**, **Downloaden (zip)** en **Naar Commons…**.
- **Vergroter**: de uitsnede, "Wat staat hierop?", het bijschrift en het Commons-concept (tab).
- **Pagina's**: `/objecten` (alle uitsneden, met het facet "Op Commons"), `/commons` (het keuzemenu), `/verbruik`, `/docs`, `/changelog`.
- **Footer**: *"Dit is een experiment. Het is geen officiële dienst van de KB, nationale bibliotheek, of van de Wikimedia Foundation. Aan deze toepassing kunnen geen rechten worden ontleend."* Plus links naar de documentatie, de API, de broncode, de privacyverklaring en de changelog.
- **Meldingen** als Codex *Message* (notice, warning, error, success).

### 10.5 Mobiel

Panelen als tabbladen (Bestand, Beeld, Detectie). Bekijken en selecteren wel; uploaden bij voorkeur op een groot scherm.

## 11. REST-API

Versieprefix `/api/v1`, OpenAPI op `/api/v1/openapi.json`, documentatie op `/docs`. Zelfde conventies als in de Delpher Uitsnijder: JSON-fouten `{"fout": …}`, `X-Robots-Tag: noindex`, een GET kost nooit geld. `{mid}` is de M-id (`M28830642`).

| Methode | Pad | Functie |
| --- | --- | --- |
| GET | `/` met `url`, `titel` of `mid`, en `pagina` | De UI; met parameters opent het bestand meteen |
| GET | `/api/v1/bestand?url=…|titel=…|mid=…` | Normaliseren; titel, M-id, afmetingen, MIME, SHA-1, licentie, maker, categorieën, SDC-samenvatting, paginalijst, rechtenlabels |
| GET | `/api/v1/bestand/{mid}/pagina/{n}` | Pagina: afmetingen, objecten, regio's uit Commons |
| GET | `/api/v1/bestand/{mid}/pagina/{n}/afbeelding?w=` | Verkleinde afbeelding (gecachet) |
| POST | `/api/v1/bestand/{mid}/pagina/{n}/detecties` | Detectie (`prompt`, `modus`: `prompt`, `alles`, `commons`, `categorie`; of `punt`). 201 |
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
| GET | `/oauth/login`, `/oauth/callback`, POST `/oauth/logout` | Inloggen (geen deel van `/api/v1`) |

API-gebruik zonder browser: met de sessiecookie na het inloggen. **[Vraag]** Ook een eigen API-sleutel per gebruiker voor scripts? Voorstel: later.

## 12. Toolforge

### 12.1 Opzet

- Een tool-account op Toolforge, bijvoorbeeld **`commons-uitsnijder`** (URL `https://commons-uitsnijder.toolforge.org/`). **[Vraag]** Naam, en wie zijn de beheerders (Olaf, een KB-collega)?
- **Build Service** met een `Procfile` (`web: gunicorn --workers 2 --bind 0.0.0.0:$PORT wsgi:app`) en `requirements.txt`; deployen met `toolforge build start <git-url>` en `toolforge webservice buildservice restart`. Alternatief: de klassieke `webservice python3.11` met een venv. Voorstel: Build Service.
- **De frontend bouwen** (Vite, zie 10.2). Op Toolforge draait alleen Python; Node.js is alleen nodig om `static/dist/` te maken. Twee routes, bij de bouw kiezen:
  1. **In de Build Service zelf**: als die naast Python ook een Node-stap kan draaien (`npm ci && npm run build`). Het eenvoudigst, als het kan.
  2. **In een GitHub Action** (terugvaloptie): bij elke push naar `main` bouwt de Action de frontend en zet het resultaat in een aparte branch (bijv. `deploy`), die de Build Service ophaalt. `static/dist/` komt dan nooit in `main`.
- **Configuratie** met `toolforge envvars create …` (`MODEL_API_KEY`, `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`, `FLASK_SECRET_KEY`). Nooit in de repo.
- **Opslag**: cache en uitvoer op de gedeelde schijf van de tool (`/data/project/<tool>/`), met een opruimtaak (bijv. originelen na 7 dagen weg, uitsneden na 30 dagen, tenzij geüpload). **[Vraag]** Bewaartermijnen?
- **Sessies**: server-side, in Redis van Toolforge of in bestanden; tokens versleuteld.
- **Lange taken** (Alles beschrijven, uploads van tientallen bestanden): pagina voor pagina vanuit de browser, zoals nu, of als `toolforge jobs`-taak. Voorstel: vanuit de browser, met de knop Stoppen.
- **Werkgeheugen**: een webservice heeft standaard een beperkt geheugen; grote scans (5.4) kunnen dat overschrijden. Bij de bouw meten en zo nodig meer aanvragen.
- **Broncode**: openbaar, met een open-sourcelicentie (verplicht op Toolforge). Licentie: **MIT** (besloten door Olaf, 3-11-2026). Let op: Codex (GPL-2.0-or-later), Vue (MIT) en `meta-sam-parser` (SAM License) houden hun eigen licentie; dat staat in de README, en Vite zet de licentieteksten bij de gebouwde bundel. **[Vraag]** GitHub onder `KBNLwikimedia` of onder `ookgezellig`?

### 12.2 Lokaal ontwikkelen

Twee terminals:

- `flask --app app run --debug`, met `DETECTIE_MODUS=dummy`, `COMMONS_UPLOAD=uit` en `COMMONS_OWNER_TOKEN` voor uploads naar een testwiki;
- `npm run dev` voor de frontend (Vite, met direct herladen). Eenmalig vooraf: `npm install`.

Tests: `pytest` voor Python en `npm test` (Vitest) voor de frontend.

### 12.3 Regels van Toolforge en privacy

- Volgens de gebruiksvoorwaarden van Toolforge mag een tool geen persoonsgegevens (zoals IP-adressen) naar derden lekken zonder dat de gebruiker dat weet. Daarom: geen externe CDN's, lettertypen of scripts (alles zit in de gebouwde bundel en komt van de tool zelf), en een **privacyverklaring** op `/privacy`.
- **Meta Model API**: de server stuurt beelden van Commons (openbaar) en de context (beschrijving, categorieën) naar Meta, nooit gegevens van de gebruiker. De privacyverklaring zegt dat. **[Vraag]** Is een commerciële, betaalde API van Meta acceptabel voor een Toolforge-tool, en moet dat vooraf langs de Toolforge-beheerders? Bij de bouw de gebruiksvoorwaarden nalezen.
- Verbruikslog met gebruikersnamen: zie 8.3.

## 13. Fasering

**Fase 0 (nu):** dit FO, de repo, de open vragen.

**Fase 1: lokaal, zonder kosten**

1. Skelet overnemen uit de Delpher Uitsnijder: detectie (`DummyDetector`), prompts, cache, verbruik, API-conventies, tests.
2. Commons-adapter: invoer normaliseren, imageinfo, wikitekst, SDC, licentie- en rechtenlabels, meerpaginabestanden, caching.
3. Frontend-opzet met Vite, Vue 3 en Codex 2.x; de viewer uit de Delpher Uitsnijder als JS-module; de koppeling Flask–Vite (10.2). Daarna de UI.
4. Uit Commons: de regio's uit de gestructureerde gegevens (P180 met P2677) als objecten, en de bestandsnotities.
5. Opslaan, zip, `/objecten`.
6. Commons-concept per object, keuzemenu, controle vooraf en proefweergave, zonder upload.

**Fase 2: OAuth en upload naar een testwiki**

7. OAuth 2.0 server-side, met een owner-only consumer.
8. Upload via de stash, SDC, `{{Image extracted}}` op het origineel; alles eerst op de testwiki.

**Fase 3: live**

9. Detectie en beschrijving live (`DETECTIE_MODUS=live`), alleen na een opdracht van Olaf. Kalibratie op Commons-materiaal (albums, prenten, kaarten).
10. Deploy naar Toolforge, publieke consumer aanvragen, privacyverklaring, de projectpagina `Commons:Commons Uitsnijder` en de volgcategorie.
11. De eerste echte uploads op Commons, door Olaf zelf.

**Fase 4: verdieping**

12. Een categorie als invoer; batch over meerdere bestanden.
13. Regio's terugschrijven naar het origineel (P180 met P2677).
14. Een link vanuit Commons: gadget of een item in het menu Hulpmiddelen ("Openen in de Commons Uitsnijder"), zoals CropTool.
15. IIIF-annotaties exporteren.
16. Engelse interface.

## 14. Repo-structuur (doel)

```
commons-uitsnijder/
  app.py  wsgi.py  Procfile  requirements.txt  .env.example  .gitignore
  uitsnijder/ (commons.py, regios.py, oauth.py, upload.py, wikitekst.py, sdc.py, rechten.py,
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
| Repo | `commons-uitsnijder`, in `D:\KB-OPEN\github-repos\commons-uitsnijder` | – |
| Kosten | Eén API-sleutel van de KB voor de Meta-aanroepen | 3, 6.4 |
| Codex | 2.x met Vue 3 | 10.1 |
| Build-stap | Vite (Node.js alleen bij het ontwikkelen en bouwen); de viewer blijft een gewone JS-module; op Toolforge draait alleen Python | 10.2, 12.1 |
| Wie mag betalen | Een toegangslijst, met 100 aanroepen per gebruiker per dag | 6.4, 8.3 |
| OAuth | Server-side, als confidential client | 8.1 |
| `{{Image extracted}}` | Standaard aan op het origineel, per upload uit te zetten | 9.3 |
| `{{Extracted from}}` | Verplicht op elke uitsnede | 9.3 |
| Bestandsnaam | Onderwerp voorop, in het Engels | 9.2 |
| Licentie van de code | MIT | 12.1 |
| Regio's uit de gestructureerde gegevens | De app vindt ze en snijdt elke regio als apart bestand uit | 7.5 |

### Nog open

**Belangrijkst**

1. **Toegangslijst**: wie komen erop, en hoe vraagt iemand toegang aan? (8.3)
2. **Toolforge**: toolnaam (voorstel `commons-uitsnijder`), beheerders, en of een betaalde API van Meta daar acceptabel is. GitHub onder `KBNLwikimedia` of `ookgezellig`? (12)
3. **Algemene daglimiet** en dagbudget (voorstel 1000 aanroepen en $5 per dag). (6.4)

**Verder**

4. Een categorie als invoer al in fase 1, of pas in fase 4? (5.1)
5. PDF/DjVu: de gerenderde pagina van Commons volstaat? Grens voor grote bestanden (voorstel 100 megapixel)? (5.4)
6. Contributor-model voor publiek-domeinbestanden van anderen: aan of uit (voorstel uit)? (6.3)
7. Beschrijving en caption altijd in het Nederlands én het Engels? Engelse interface later? (3, 6.2)
8. Volgcategorie `Category:Uploaded with Commons Uitsnijder` en een projectpagina op Commons? (9.3)
9. Gebruikersnamen in het verbruikslog: leesbaar of gehasht? Bewaartermijnen op Toolforge? (8.3, 12.1)
10. Logo: eigen icoon (voorstel) of het Commons-logo met toestemming van de WMF? (10.3)
11. Testwiki: test-commons of de bètacluster? (9.6)
12. Beeld naar SAM als data-URL (voorstel) of als publieke thumbnail-URL? (6.1)
13. Een eigen API-sleutel per gebruiker voor scripts, of later? (11)

## 16. Te verifiëren bij de bouw

- De thumbnailstappen die Commons nu toestaat (5.2).
- Het formaat van de vooringevulde selectie in CropTool (2).
- De minimale set OAuth-grants (8.2).
- Of de testwiki OAuth 2.0 en SDC ondersteunt (9.6).
- Welke SDC-eigenschap de relatie uitsnede → origineel vastlegt (9.4).
- Of de Toolforge Build Service een Node-stap (`npm ci && npm run build`) vóór de Python-build kan draaien, of dat de frontend in een GitHub Action wordt gebouwd (12.1).
- Welke Vue-versie Codex 2.x vraagt, en of Codex-componenten die zich in een Jinja-pagina mounten goed samengaan met de CSS van Flask-pagina's (10.2).
- Geheugen en time-outs van een Build Service-webservice op Toolforge (12.1).
- Of Commons regels heeft voor beschrijvingen die deels met een taalmodel zijn gemaakt.
