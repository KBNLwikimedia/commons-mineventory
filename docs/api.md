# API – Commons Cutter

De Commons Cutter heeft een REST-API onder `/api/v1`. De interface in de browser is zelf een client van deze API. De machineleesbare beschrijving staat op [/api/v1/openapi.json](/api/v1/openapi.json); dit document is de uitleg erbij. Ontwerp: [functioneel ontwerp, hoofdstuk 11](functioneel-ontwerp.md).

## Afspraken

- Alle antwoorden zijn JSON (behalve afbeeldingen en de zip). Veldnamen zijn Nederlands, zoals in de Delpher Uitsnijder.
- **Een GET kost nooit geld en verandert niets.** Detectie en beschrijving gaan alleen via POST, zodat linkvoorbeelden en crawlers nooit kosten maken. Voor elke betaalde actie is er een gratis raming.
- Fouten: `{"fout": "<Nederlandse melding>", "code": "<vaste code>"}` met een passende HTTP-status. De interface vertaalt de `code` (zie `frontend/i18n/`). Bij detectiefouten komt ook `budget` mee.
- `201` bij aanmaken (detecties, uitsneden), `202` bij een upload (fase 2).
- Elke API-respons heeft `X-Robots-Tag: noindex, nofollow`.
- `{mid}` is de M-id van het bestand op Commons (`M28830642`); `{n}` het paginanummer (1 bij een gewone afbeelding); `{object_id}` het id van een object (`obj-…`).
- Object en uitsnede: een object (`…/objecten/{object_id}`) is wat er gevonden is, alleen gegevens; een uitsnede is het beeldbestand dat je ervan opslaat (`POST …/uitsneden`, daarna `…/uitsnede.jpg` en `…/uitsnede.png` in volledige resolutie). Zonder opslaan geven `uitsnede.jpg` en `uitsnede.png` het beeld op aanvraag, zonder het te bewaren.
- REST: elk pad is een bron (zelfstandig naamwoord, een lijst in het meervoud: `…/objecten/{object_id}`); GET leest, POST maakt aan of start iets nieuws, PUT zet, PATCH wijzigt een deel, DELETE verwijdert. Geen werkwoorden in de paden (sinds 0.29.0).
- Inloggen (OAuth 2.0) komt in fase 2. Betaalde aanroepen vragen dan een login en een plek op de toegangslijst; in de proefmodus (`DETECTIE_MODUS=dummy`) is alles gratis en is geen login nodig.

## Bestand en pagina's

| Methode | Pad | Functie |
| --- | --- | --- |
| GET | `/bestand?url=…`, `?titel=…` of `?mid=…` | Invoer normaliseren (URL, titel, M-id, curid, upload.wikimedia.org) en het bestand teruggeven: titel, M-id, afmetingen, MIME, SHA-1, licentie, maker, datum, categorieën, SDC-samenvatting, rechtenlabels, paginalijst. `uitsnijden_mogelijk` zegt of uitsneden in volledige resolutie kunnen; `tegels: true` dat het origineel boven `MAX_MEGAPIXELS` ligt en stuk voor stuk met libvips gelezen wordt (sinds 0.21.0). `werk`: het Wikidata-item van het werk, uit `|wikidata=` in het sjabloon of anders uit *digitale weergave van* (P6243) in de SDC (`via`: `wikitekst` of `sdc`), met titel, beschrijving, makers, datum, soort, onderdeel van, beeldt af, materiaal, afmetingen, collectie met inventarisnummers, locatie, plaats van vervaardiging en links, zoals `{{Artwork}}` ze toont (sinds 0.28.0); de SDC-samenvatting heeft daarvoor ook `digitale_weergave_van` |
| GET | `/bestand/{mid}` | Hetzelfde, op M-id |
| GET | `/bestand/{mid}/pagina/{n}` | Afmetingen van de pagina (pixels van het origineel), objecten, aantal regio's en notities uit Commons, en `prullenbak_termen`: per zoekterm hoeveel objecten van deze pagina in de prullenbak staan |
| GET | `/bestand/{mid}/pagina/{n}/afbeelding?w=` | Een verkleinde afbeelding: de dichtstbijzijnde thumbnailstap van Commons van minstens `w` pixels (20, 40, 60, 120, 250, 330, 500, 960, 1280, 1920, 3840), gecachet |

Voorbeeld:

```
GET /api/v1/bestand?url=https://commons.wikimedia.org/wiki/File:Album_amicorum_van_Jacob_van_Bronckhorst_van_Batenburg_(8077131573).jpg
```

## Detectie

| Methode | Pad | Functie |
| --- | --- | --- |
| POST | `/bestand/{mid}/pagina/{n}/detecties` | Een detectie. Body: `{"prompt": "wapen en portret min tekst", "modus": "prompt"}`; of `"modus"`: `alles` of `commons` (de regio's uit Commons, gratis). Of `{"punt": {"x", "y"}}` (Aanwijzen), `{"rechthoek": {"x", "y", "w", "h"}}` (met de hand, gratis) of `{"masker_voor": "<object-id>"}` (de vorm van een regio via een SAM-boxprompt). Antwoord 201 met alle objecten van de pagina en de nieuwe id's |
| GET | `/bestand/{mid}/pagina/{n}/detecties/raming` | Wat een detectie zou kosten (zelfde parameters als query); voert niets uit |
| GET | `/bestand/{mid}/pagina/{n}/inventaris` | Het opgeslagen paginaoverzicht ("Wat staat op deze pagina?") en de kosten van een nieuw |
| DELETE | `/bestand/{mid}/pagina/{n}/inventaris` | Het hele paginaoverzicht verwijderen: samenvatting, zoektermen en de gelezen tekst, die dan ook niet meer meegaat als context bij "Wat staat hierop?". Gevonden objecten blijven. Het antwoord blijft in de cache: een POST zonder `opnieuw` brengt het gratis terug. Geeft `{"verwijderd": true\|false, "inventaris": null}`. Gratis |
| DELETE | `/bestand/{mid}/pagina/{n}/inventaris/{deel}` | Eén deel verwijderen (sinds 0.29.0): `beschrijving` (paginasoort, samenvatting, gelezen tekst) of `zoektermen`; het andere deel blijft. Zijn beide delen leeg, dan gaat het hele overzicht weg. Geeft `{"verwijderd", "inventaris"}` (wat overblijft, of `null`). Een onbekend deel: 404. Gratis |
| POST | `/bestand/{mid}/pagina/{n}/inventaris/{deel}` | Eén deel opnieuw vragen (sinds 0.29.0): altijd een nieuw, betaald antwoord, met een vraag en antwoordformaat voor alleen dat deel; het andere deel blijft. `delen` in het overzicht zegt wanneer en met welk model elk deel opnieuw is gevraagd. Body: `{"model": "auto"}` (optioneel) |
| POST | `/bestand/{mid}/pagina/{n}/inventaris` | Muse Spark vragen wat er op de pagina staat; zoektermen voor SAM. Body: `{"model": "auto", "opnieuw": false}`. Met `"opnieuw": true` komt er een nieuw antwoord voor beide delen. Het overzicht heeft `paginasoort` en `samenvatting` in het Nederlands en (sinds 0.9.0) `paginasoort_en` en `samenvatting_en` in het Engels, en (sinds 0.16.0) `tekst`: de tekst die het model in en onder de afbeelding leest, letterlijk |


Regio's uit Commons (`modus: commons`) zijn de verklaringen *beeldt af* (P180) met *relatieve positie in afbeelding* (P2677, `pct:x,y,b,h` of pixels) en de bestandsnotities (`{{ImageNote}}`). Elke regio wordt een eigen object (`bron: commons`, `soort: regio` of `notitie`) met het Wikidata-item in `wikidata`; regio's worden nooit samengevoegd.

## Objecten

| Methode | Pad | Functie |
| --- | --- | --- |
| PATCH | `/bestand/{mid}/pagina/{n}/objecten` | `{"geselecteerd": [ids]}` (precies deze zijn geselecteerd) of `{"objecten": [{"id", "status"}]}` |
| POST | `/bestand/{mid}/pagina/{n}/samenvoegingen` | Dubbelingen samenvoegen (sinds 0.29.0; eerder `{"samenvoegen": true}` in de PATCH hierboven, dat nog tot 0.30.0 werkt): objecten die hetzelfde beeld tonen, worden één. Geeft `{"objecten", "samengevoegd"}`. Gratis |
| GET | `/bestand/{mid}/pagina/{n}/objecten/{object_id}` | Eén object, ook als het in de prullenbak ligt (`in_prullenbak`) |
| PATCH | `/bestand/{mid}/pagina/{n}/objecten/{object_id}` | `{"bijschrift": {"tekst": …} \| null}`, `{"status": …}`, `{"prullenbak": true \| false}` |
| DELETE | `/bestand/{mid}/pagina/{n}/objecten/{object_id}` | Naar de prullenbak |
| GET | `/bestand/{mid}/pagina/{n}/objecten/{object_id}/uitsnede.jpg` | De rechthoek als JPG in volledige resolutie; met `?w=` een voorbeeld |
| GET | `/bestand/{mid}/pagina/{n}/objecten/{object_id}/uitsnede.png` | De vorm van het object als transparante PNG, in volledige resolutie |
| GET | `/bestand/{mid}/pagina/{n}/objecten/{object_id}/masker.png` | Het masker (wit is het object), op de resolutie van het masker |

Statussen: `kandidaat`, `geselecteerd`, `uitgesloten`. Bronnen: `sam`, `dummy`, `commons`, `handmatig`.

## Beschrijving ("Wat staat hierop?")

| Methode | Pad | Functie |
| --- | --- | --- |
| GET | `/bestand/{mid}/pagina/{n}/objecten/{object_id}/beschrijving` | De opgeslagen beschrijving en wat een nieuwe kost, met het model en de reden |
| POST | `/bestand/{mid}/pagina/{n}/objecten/{object_id}/beschrijving` | Muse Spark vragen (gecachet). Body: `{"model": "auto" \| "standaard" \| "contributor", "opnieuw": false, "aanwijzing": "…"}`. Met `marge` (0 tot 1, standaard 0,25, in stappen van 0,05) kies je hoeveel ruimte rond het kader het model ziet; de gekozen marge staat in de beschrijving (`marge`). De optionele `aanwijzing` (hooguit 300 tekens) is een extra opdracht voor het model, bijv. "alleen de jongen"; hij wordt bewaard in de beschrijving (`aanwijzing`) en hoort bij de cachesleutel. Heeft de pagina een AI-overzicht met `tekst` (de tekst in en onder de afbeelding), dan gaat die als context mee; `paginatekst: true` in de beschrijving zegt dat, en de tekst hoort ook bij de cachesleutel |
| PATCH | `/bestand/{mid}/pagina/{n}/objecten/{object_id}/beschrijving` | De teksten met de hand wijzigen (gratis). Body: een of meer van `onderwerp`, `onderwerp_en`, `bedrijf_of_naam` (sinds 0.22.1), `beschrijving`, `beschrijving_en`, `tekst_in_beeld`, `tekst_rond_beeld` (een lege tekst haalt het veld leeg). De eerste keer dat een veld verandert, blijft de AI-tekst bewaard in `ai_origineel`; `bewerkt` zegt of er nog iets afwijkt. 409 zonder beschrijving |
| GET | `/bestand/{mid}/pagina/{n}/objecten/{object_id}/beschrijving/geschiedenis` | Eerdere versies van de beschrijving, nieuwste eerst: wat bij een nieuwe vraag, een aanpassing met de hand, terugzetten of wissen is vervangen (hooguit 30), plus antwoorden die nog in de cache staan. Elke versie heeft `versie` (en bij een aanpassing `bewerkt_op`). Gratis |
| DELETE | `/bestand/{mid}/pagina/{n}/objecten/{object_id}/beschrijving/geschiedenis/{versie}` | Eén eerdere versie verwijderen (sinds 0.27.1; dit pad sinds 0.29.0), met de `versie` uit de geschiedenis. Een AI-antwoord dat nog in de cache staat, wordt voor dit object verborgen; de cache zelf blijft. De huidige beschrijving gaat zo niet weg. Gratis |
| PUT | `/bestand/{mid}/pagina/{n}/objecten/{object_id}/beschrijving` | Een eerdere versie weer de huidige beschrijving maken (gratis; sinds 0.29.0, eerder POST `…/terugzetten`). Body: `{"versie": …}` uit de geschiedenis; elke versie, ook een aanpassing met de hand, heeft een eigen `versie`. De huidige gaat naar de geschiedenis |
| GET | `/bestand/{mid}/pagina/{n}/objecten/{object_id}/beschrijving/invoer.jpg?marge=0.25` | Wat het model zou zien: het kader met die marge eromheen, het kader in rood. Met `max=` (1024 tot 4000 pixels, de langste zijde) een grotere versie om de tekst in het beeld te lezen en te controleren; het model zelf krijgt altijd 1024. Gratis (er gaat niets naar het model) |
| DELETE | `/bestand/{mid}/pagina/{n}/objecten/{object_id}/beschrijving` | De beschrijving vergeten (het antwoord blijft in de cache) |
| GET | `/wikidata/zoek?q=…&taal=nl\|en` | Wikidata-items zoeken voor *beeldt af* (gratis) |

Velden: `soort`, `onderwerp`, `onderwerp_en`, `bedrijf_of_naam`, `tekst_in_beeld`, `tekst_rond_beeld`, `beschrijving`, `beschrijving_en`, `zekerheid`, `wikidata_suggesties` (hooguit drie zoektermen; het model verzint geen Q-nummers). Contributor alleen bij publiek domein zonder rechtenlabels (FO 6.3). `soort` en `zekerheid` komen uit een vaste Nederlandse lijst; de interface vertaalt ze. De reden voor het model staat als tekst in `model_reden` (Nederlands) en als code in `model_reden_code` (`publiek_domein`, `contributor_uit`, `rechtenlabel`, `niet_vrij`, `standaard_gekozen`), met de blokkerende rechtenlabels in `model_reden_labels`; de GET geeft hetzelfde als `reden`, `reden_code` en `labels`. Na een bewerking met de hand: `ai_origineel` en `bewerkt` (zie PATCH).

## Commons-concept en upload

| Methode | Pad | Functie |
| --- | --- | --- |
| GET | `/bestand/{mid}/pagina/{n}/objecten/{object_id}/commons` | Het concept: bestandsnaam, formaat, caption en beschrijving (nl/en), datum, maker, licentiesjablonen, categorieën, *beeldt af*, rechtenlabel, wikitekst, SDC en uploadsamenvatting, met `sdc_labels` (labels van eigenschappen en items in de SDC, voor de preview) en `origineel`: wat het origineel voor deze uitsnede zou krijgen (per *beeldt af*-item een P180 met P2677 `pct:x,y,w,h`; `aanwezig` als het origineel die regio al heeft; `null` bij bestanden met meer pagina's). De SDC bevat ook P31 *digitale afbeelding*, P1163 mediatype, P4092 SHA-1, P3575 grootte, P2048/P2049 hoogte en breedte van het uitgesneden bestand. Gratis |
| GET | `/bestand/{mid}/pagina/{n}/objecten/{object_id}/commons/weergave` | De wikitekst zoals Commons hem weergeeft: `{"html": …}`. Commons maakt de HTML (`action=parse`, alleen lezen, gecachet); de app laat alleen veilige tags staan, zonder afbeeldingen, stijlen of scripts, zodat de browser van de gebruiker voor deze preview niets van Wikimedia laadt. Gratis |
| PATCH | `/bestand/{mid}/pagina/{n}/objecten/{object_id}/commons` | Velden wijzigen (`bestandsnaam`, `formaat`, `beschrijving`, `caption`, `datum`, `maker`, `categorieen`, `beeldt_af`, `image_extracted`, `merk_bevestigd`, `gekozen`, `sdc_waarden`), of `{"herstel": true}`. `sdc_waarden` (sinds 0.24.0) vervangt de waarden van uitspraken van het origineel (P6216, P275, P170, P571, P195): `{"P195": [{"item": "Q…", "bron": 0}], "P571": [{"tijd": "1708-02"}], "P170": [{"onbekend": true}]}`; `bron` is het volgnummer van de uitspraak van het origineel waarvan de kwalificaties blijven; een lege lijst haalt de uitspraak weg. Kwalificaties en bronnen zijn niet te wijzigen |
| GET | `/bestand/{mid}/commons` | Het keuzemenu: alle opgeslagen uitsneden van het bestand met hun concept |
| GET | `/bestand/{mid}/commons/controle?objecten=1:obj-a,2:obj-b` | Controle vooraf, alleen lezen op Commons (sinds 0.29.0 een GET): bestaat de naam, staat dezelfde afbeelding er al (SHA-1), bestaan de categorieën. `objecten` is een lijst `pagina:id`; zonder de aangevinkte |
| POST | `/bestand/{mid}/commons/uploads` | Uploaden (fase 2). Vereist een login, `{"bevestigd": true}` en `COMMONS_UPLOAD=aan`; nu: 503 `upload_disabled` |
| GET | `/uploads/{task}` | Voortgang van een upload (fase 2) |

Bestandsnaam: `<Onderwerp> – extracted from <titel origineel zonder extensie>.<jpg|png>`, hooguit 240 bytes. De wikitekst heeft altijd `{{Extracted from|File:…}}`, de licentiesjablonen van het origineel letterlijk (zonder licentiecontrole) en `[[Category:Uploaded with Commons Cutter]]`.

## Opslaan en exporteren

| Methode | Pad | Functie |
| --- | --- | --- |
| POST | `/bestand/{mid}/pagina/{n}/uitsneden` | Uitsneden opslaan in volledige resolutie: JPG (de rechthoek, kwaliteit 95) en, bij een masker, een transparante PNG en het masker. Body: `{"ids": [...]}`; zonder ids de geselecteerde |
| GET | `/bestand/{mid}/pagina/{n}/uitsneden` | De opgeslagen uitsneden van een pagina. Elk object met `opgeslagen` heeft daarin ook `laatst_gebruikt` en `verloopt` (ISO 8601, UTC): wanneer de opruimtaak de bestanden weghaalt als ze tot dan niet gebruikt worden (`BEWAAR_UITSNEDEN_DAGEN`, FO 12.1). Dat staat ook bij de objecten in de andere antwoorden |
| GET | `/bestand/{mid}/export?formaat=zip\|json` | Alles van een bestand: een zip (met `LEESMIJ.txt`, `bestand.json`, de uitsneden en de wikitekst per uitsnede) of JSON |

Opslag op schijf: `uitvoer/<M-id>/bestand.json` en `uitvoer/<M-id>/pagina_<n>/{objecten.json, jpg/, png/, maskers/}`.

## Prullenbak en overzichten

| Methode | Pad | Functie |
| --- | --- | --- |
| GET | `/objecten?bron=…&mid=…&opgeslagen=1` | Alle objecten over alle bestanden |
| GET | `/prullenbak` | De prullenbak |
| DELETE | `/prullenbak` | Alles definitief verwijderen, of alleen `{"objecten": [{"mid", "pagina", "id"}]}` |
| DELETE | `/prullenbak/{mid}/{n}/{object_id}` | Eén object definitief verwijderen, met de bestanden |
| GET | `/verbruik?van=&tot=` | Het verbruikslog: aanroepen en kosten per dag, en de laatste regels van het log. Op een server (niet in debug-modus) alleen voor ingelogde gebruikers op de toegangslijst (sinds 0.26.0); dat geldt ook voor `/verbruik/{datum}` en voor het legen van de hele prullenbak |
| GET | `/verbruik/{datum}` | Het verbruik van één dag |
| GET | `/status` | Versie, modus, ingelogde gebruiker, budgetten |
| GET | `/openapi.json` | De OpenAPI-beschrijving |

## Verouderde paden

Deze paden werken nog tot versie 0.30.0. Het antwoord heeft dan `Deprecation: true` en een `Link` naar het nieuwe pad (`rel="successor-version"`); in `/api/v1/openapi.json` staan ze als `deprecated`.

| Oud (tot 0.30.0) | Nieuw (sinds 0.29.0) |
| --- | --- |
| `/bestand/{mid}/pagina/{n}/object/{object_id}` en alles daaronder (`…/uitsnede.jpg`, `…/uitsnede.png`, `…/masker.png`, `…/beschrijving`, `…/beschrijving/geschiedenis`, `…/beschrijving/invoer.jpg`, `…/commons`, `…/commons/weergave`) | hetzelfde onder `/bestand/{mid}/pagina/{n}/objecten/{object_id}` |
| POST `/bestand/{mid}/pagina/{n}/object/{object_id}/beschrijving/terugzetten` | PUT `/bestand/{mid}/pagina/{n}/objecten/{object_id}/beschrijving` |
| DELETE `/bestand/{mid}/pagina/{n}/object/{object_id}/beschrijving/geschiedenis?versie=…` | DELETE `/bestand/{mid}/pagina/{n}/objecten/{object_id}/beschrijving/geschiedenis/{versie}` |
| PATCH `/bestand/{mid}/pagina/{n}/objecten` met `{"samenvoegen": true}` | POST `/bestand/{mid}/pagina/{n}/samenvoegingen` |
| POST `/bestand/{mid}/commons/controle` met `{"objecten": …}` | GET `/bestand/{mid}/commons/controle?objecten=…` |

Oude paden, zoals de test ze controleert: `/bestand/{mid}/pagina/{n}/object/{object_id}`, `/bestand/{mid}/pagina/{n}/object/{object_id}/uitsnede.jpg`, `/bestand/{mid}/pagina/{n}/object/{object_id}/uitsnede.png`, `/bestand/{mid}/pagina/{n}/object/{object_id}/masker.png`, `/bestand/{mid}/pagina/{n}/object/{object_id}/beschrijving`, `/bestand/{mid}/pagina/{n}/object/{object_id}/beschrijving/geschiedenis`, `/bestand/{mid}/pagina/{n}/object/{object_id}/beschrijving/terugzetten`, `/bestand/{mid}/pagina/{n}/object/{object_id}/beschrijving/invoer.jpg`, `/bestand/{mid}/pagina/{n}/object/{object_id}/commons`, `/bestand/{mid}/pagina/{n}/object/{object_id}/commons/weergave`.

## Foutcodes

| Code | Betekenis |
| --- | --- |
| `empty_input`, `bad_input`, `bad_mid` | De invoer is leeg of geen bruikbare URL, titel of M-id |
| `not_commons`, `not_a_file` | Het bestand staat niet op Commons, of het is geen bestand |
| `not_found` | Bestand, pagina, object of pad bestaat niet |
| `commons_unreachable`, `commons_error` | Commons is traag, onbereikbaar of gaf een fout |
| `too_large`, `unsupported` | Te groot om in volledige resolutie uit te snijden, of een bestandstype dat niet kan (SVG, GIF, video) |
| `empty_prompt`, `too_small`, `nothing_selected`, `nothing_saved`, `invalid_concept` | Ongeldige of lege opdracht |
| `daily_limit`, `user_limit`, `daily_budget` | Een limiet is bereikt (429) |
| `login_required`, `not_on_access_list` | Betaalde aanroepen vragen een login en de toegangslijst |
| `upload_disabled`, `not_confirmed`, `not_implemented` | Uploaden staat uit, is niet bevestigd, of komt in fase 2 |
| `contributor_not_allowed`, `no_api_key`, `no_mask` | Modelkeuze, configuratie of SAM vond niets |
| `too_many_terms` | Meer dan 20 zoektermen in één opdracht (sinds 0.26.0) |
| `cross_site` (403), `not_json` (415) | Een verzoek dat iets verandert of geld kost, komt niet van de eigen pagina's van de app, of heeft geen JSON-body (bescherming tegen CSRF, sinds 0.25.0) |
| `invalid_body`, `invalid_mid`, `no_description` (409), `no_thumbnail`, `method_not_allowed` | Ongeldige body of M-id, nog geen beschrijving, Commons gaf geen verkleinde afbeelding, of een methode die de route niet kent |
