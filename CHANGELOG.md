# Changelog

Alle noemenswaardige wijzigingen in dit project staan in dit bestand.
De opmaak volgt [Keep a Changelog](https://keepachangelog.com/nl/1.1.0/) en het project gebruikt [Semantic Versioning](https://semver.org/lang/nl/).

## [Unreleased]

## [0.39.1] - 2026-11-12

### Toegevoegd

- Onder de AI-zoektermen staat een regel: *Niet goed? Haal het object rechts weg. Iets anders zoeken? Gebruik Zoeken of Aanwijzen of tekenen*, met links naar die blokken.
- Vindt een zoekactie iets dat in de prullenbak ligt, dan staat in de melding een knop *Terugzetten uit de prullenbak*; de melding zegt daarna zelf hoeveel er terug zijn (wens Olaf). *Niets nieuws voor …* heet nu *Geen nieuwe objecten voor …: wat de AI vond, was er al*, zodat het niet meer als een fout leest.

### Verwijderd

- De potloodjes bij de AI-zoektermen (wens Olaf): een term is wat de AI zei, het getal telt de objecten van dat woord. Een eigen woord gaf veel complexiteit, zoals een knop *sky* die eigenlijk *driveway* was. Een fout object haal je rechts weg; iets anders zoek je met *Zoeken* of *Aanwijzen of tekenen*. De eigen woorden die de browser nog had, worden vergeten.

### Gewijzigd

- De knoppen bij *Staat al op Commons* tonen de naam van het item op Commons (*stairs*), niet het woord van de AI (*staircase*, nu in de tooltip); twee AI-woorden voor hetzelfde item geven één knop (wens Olaf).
- De beschrijving van de hele afbeelding staat per taal in een vak met een vaste hoogte, dat scrolt als de tekst langer is; het potlood en het AI-merkje staan ernaast. Schuiven met *Lengte* verandert de hoogte van de pagina dus niet meer (wens Olaf).
- Terwijl de AI de afbeelding opnieuw beschrijft, staat de wachtbalk direct onder *Beschrijving opnieuw*, niet meer onder de tekst (wens Olaf).
- De zoektermen onder *Staat al op Commons* zijn gedimd (minder fel groen, wat grijzer), omdat je er niet op kunt klikken (wens Olaf).
- De gekozen stand van een schuif (lengte, detailniveau) staat altijd op een eigen regel onder de schuif; een lange stand zoals *Commons-caption (hooguit 250 tekens)* sprong eerst van naast de schuif naar eronder (wens Olaf).

### Gerepareerd

- Een AI-zoekterm die je met het potlood een eigen woord gaf, telde de objecten van beide woorden: *driveway*, hernoemd tot *sky*, toonde *sky 2* bij één object *sky*. Het getal telt nu alleen het woord op het knopje (wens Olaf).
- Een antwoord van de AI dat geen JSON is, of een beschrijving zonder tekst, gold als een goed antwoord: het werd bewaard en in de cache gezet, zodat *Wat staat op deze pagina?* daarna gratis hetzelfde kapotte antwoord teruggaf. Nu volgt een melding (502 `unreadable_answer`) met de vraag het opnieuw te proberen; de aanroep is wel geboekt, er wordt niets bewaard.
- Liet de AI één lengte leeg, dan zei de app dat de beschrijving van vóór de vier lengtes was. Nu zegt hij dat de AI deze lengte niet gaf.

## [0.39.0] - 2026-11-12

### Toegevoegd

- De beschrijving van de hele afbeelding komt in één AI-aanroep in alle vier de lengtes (kort, normaal, Commons-caption, uitgebreid; wens Olaf). De schuif *Lengte* wisselt er gratis en meteen tussen. Elke lengte houdt zijn eigen aanpassingen met de hand en zijn eigen AI-origineel; *Eerdere beschrijvingen* bewaart de vier samen als één versie. *Naar Commons* gebruikt de lengte Commons-caption. Een beschrijving van vóór deze versie heeft alleen zijn eigen lengte; de app zegt dat op de andere standen. API: `beschrijvingen` in het overzicht en `beschrijvingsniveau` bij `PATCH …/inventaris`. Eén lengte opnieuw vragen kost iets meer uitvoer dan voorheen; eerder opgeslagen antwoorden gelden voor de nieuwe vraag niet.

## [0.38.1] - 2026-11-11

### Gewijzigd

- *Wat staat op deze pagina?* maakt de beschrijving van de hele afbeelding voortaan als Commons-bijschrift: zo rijk mogelijk, nooit langer dan 250 tekens, zodat hij zo naar de gestructureerde gegevens op Commons kan (wens Olaf). Een andere lengte kies je daarna met de schuif bij de beschrijving. De kostenbevestiging en de uitleg zeggen dit; een eerder gemaakt overzicht houdt zijn eigen lengte.
- De zoektermen onder *AI-suggesties voor deze afbeelding* staan in twee blokken (wens Olaf): *Staat al op Commons* (wat de AI zag en het bestand al als *beeldt af* heeft; knoppen die niets doen, groen met het aantal gekoppelde objecten; lokaliseren gaat onder *Van Commons*) en *Nieuw, nog niet op Commons* (met vinkje en potlood; alleen deze gaan mee met *Alle objecten lokaliseren*). Het merkje *op Commons* is daarmee weg.
- *Van Commons > Beeldt af* is alleen lezen (wens Olaf): het potloodje om het zoekwoord van een item te veranderen is weg; de AI zoekt op het Engelse label. Eerder ingestelde zoekwoorden (in de browser) tellen niet meer, ook niet bij het koppelen door hernoemen. De uitleg eindigt met *Nieuw item toevoegen?* en drie wegen als links: de *AI-suggesties*, *Zoeken* en *Aanwijzen of tekenen* (wens Olaf).
- *Zoeken* heeft een tip als het bestand *Beeldt af*-items heeft: vond de AI een item niet onder zijn eigen naam, zoek dan met een ander woord en hernoem het gevonden object naar dat item; dan wordt het eraan gekoppeld (wens Olaf).

## [0.38.0] - 2026-11-11

### Toegevoegd

- Nieuwe schermafbeeldingen (11 november 2026, versie 0.38.0) in de README en de rondleiding op de projectsite: tien schermen, waaronder *Beeldt af* lokaliseren, *Naar Commons*, het objectenoverzicht als lijst en de changelog met facetten; een nieuwe `carrousel.gif`. README en beginpagina van de site noemen de nieuwe functies; de documentatie-index op de site zegt per document wat erin staat en bij welke versie hij hoort.
- Een beschrijving van de afbeelding die als Commons-bijschrift is gemaakt (hooguit 250 tekens), telt de tekens terwijl je de samenvatting met de hand aanpast; te lang kan niet worden opgeslagen (wens Olaf).
- Hernoem je een object (potlood) naar het woord van een *Beeldt af*-item (label of zoekwoord, hoofdletters tellen niet), dan wordt het ook aan dat item gekoppeld: het telt daar mee (groen) en gaat met zijn kader naar Commons. Een koppeling aan een ander *Beeldt af*-item vervalt. Met een melding en *Ongedaan maken*. API: `"item"` bij `PATCH …/objecten/{id}` (wens Olaf: *child 3* hernoemd tot *doll*).

### Gewijzigd

- De kostenbevestiging van *Wat staat op deze pagina?* noemt de drie dingen die de AI maakt als opsomming (wens Olaf).
- De knoppen *Beschrijving opnieuw* en *Verwijderen* lopen in een smalle kolom door op een nieuwe regel in plaats van afgekapt te worden.
- *Toevoegen aan gestructureerde gegevens (op Commons)* is uitgeschakeld zolang er niets toe te voegen is (geen objecten, geen AI-suggesties en geen bijschrift op Commons om met de hand te herschrijven), met de reden eronder (wens Olaf).
- Elk uitklapblok begint met een korte uitleg in één stijl (wat je er doet, en wat er daarna gebeurt): *Van Commons*, *AI-suggesties voor deze afbeelding*, *Zoeken*, *Aanwijzen of tekenen*, *Naar Commons*, *Kleurenlegenda*, *Bulkacties* en *Opslaan en exporteren* (wens Olaf).
- *AI-suggesties voor deze afbeelding*: de zin dat de suggesties bij de afbeelding horen (en hoe je ze weghaalt), staat er pas als er suggesties zijn, niet bij de eerste vraag (wens Olaf).
- De (i)-uitleg kan sub-opsommingen hebben (regels met `  - `); bij *Naar Commons* zo voor beeldt af (items uit Commons krijgen een kader; andere objecten worden reconciliatievoorstellen, je kiest zelf het best passende Wikidata-item) en de vier keuzes voor bijschriften (wens Olaf).
- *Naar Commons*: de uitleg onder de knop als opsomming (beeldt af, bijschrift), met *kader* in plaats van *plaats*, en een kortere knop: *Toevoegen aan gestructureerde gegevens (op Commons)* (de kop zegt al *Naar Commons*; wens Olaf).

## [0.37.0] - 2026-11-10

### Toegevoegd

- Lokaliseren met woorden waar SAM op deze afbeelding al naar zocht, vraagt eerst: *Bewaarde antwoorden gebruiken* (gratis) of *SAM opnieuw vragen* (betaald, met het bedrag; meestal hetzelfde resultaat). API: `"vers": true` bij `POST …/detecties`, `?vers=1` en `in_cache` bij de raming (wens Olaf).

### Opgelost

- Na *Deze afbeelding opnieuw beginnen* kon lokaliseren mislukken met *Er ging iets mis* (twee keer, bovenaan): Windows hield de verwijderde mappen vast, omdat de Vite-dev-server ook `uitvoer/` volgde. Vite volgt de datamappen niet meer, opnieuw beginnen zet de map eerst opzij, een map in gebruik geeft een duidelijke melding, en een fout bij lokaliseren staat onder de knop (wens Olaf).

### Gewijzigd

- De knop *Toevoegen aan de gestructureerde gegevens van deze afbeelding (op Commons)* staat niet meer onder *AI-suggesties voor deze afbeelding*, maar in een eigen uitklapblok *Naar Commons*, als laatste onder *Beschrijven en vinden*: ook wie geen AI gebruikte (alleen items uit Commons lokaliseerde of het bijschrift aanpaste), vindt hem nu. Met een (i) en een algemenere uitleg (wens Olaf).
- *Bijsnijden in CropTool* is geen uitklapblok meer onder *Beschrijven en vinden* (het neemt niets over uit de app), maar een kleine link in de bestandskop, naast het M-id en Q-id. Daarbij twee nieuwe links naar Commons: *Waar gebruikt* (Global usage) en *Geschiedenis* van de bestandspagina (wens Olaf).
- De groene (gevonden) en grijze (gezocht, niets gevonden) knoppen bij *Beeldt af* en de AI-zoektermen hebben een sterkere kleur (wens Olaf).
- De koppen van de vier kolommen hebben een iets donkerdere achtergrond (wens Olaf).

## [0.36.0] - 2026-11-10

### Toegevoegd

- *Metadata*: *Categorieën* heet nu *Commons-categorieën*, en elke categorie linkt naar haar pagina op Commons (wens Olaf).
- *Metadata*: elk licentiesjabloon linkt naar zijn sjabloonpagina op Commons, en staat er maar één keer (wens Olaf).
- *Metadata*: *Beeldt af* en *Maker* linken naar hun Wikidata-items (wens Olaf).
- *Metadata* → *Werk op Wikidata*: bij *Collectie* en *Locatie* het logo van die instelling achter de naam (P154 op Wikidata, bijvoorbeeld de KB), via de server; API: `GET /api/v1/wikidata/{q}/logo` (wens Olaf).
- Bestandskop: naast de bestandsnaam staan het M-id (naar de gestructureerde gegevens op Commons) en het Q-id van het werk op Wikidata, allebei te klikken, het Q-id met een klein Wikidata-logo; het Q-id onder *Metadata* ook, en *Werk op Wikidata* heeft het logo ervoor (wens Olaf).
- *Objecten*, *Prullenbak*, *Changelog* en *Verbruik*: de gekozen facetten en de zoektekst staan in het adres en komen daar weer uit, met dezelfde namen als de export (`?bron=sam&mid=M1&q=lemon`); zo is elke weergave een bladwijzer (wens Olaf). Ook de gesorteerde kolom (`sorteer`), de weergave (`weergave=lijst|tabel`) en een open vergroter op *Objecten* (`object`, `vergroten`); op de afbeeldingspagina het zoekveld (`q`), *Minimale zekerheid* (`zekerheid`) en *Alleen deze maskers/kaders tonen* (`maskers`, `kaders`).
- *Bekeken*: ↻ naast het prullenbakje (alleen actief als er voor die afbeelding iets bewaard is) begint een afbeelding opnieuw: na een bevestiging gaan alle objecten, de prullenbak, opgeslagen uitsneden, de AI-suggesties en het concept voor Commons weg, en vergeet de browser de gezochte woorden. De cache blijft. De (i) bij *Bekeken* legt uit wat ↻ precies doet. De bevestiging noemt wat er weggaat als lijst, met links naar de objecten, de prullenbak, de opgeslagen uitsneden en de AI-suggesties van die afbeelding; *Objecten* opent met `?mid=` en `?opgeslagen=1` op dat bestand. Een keuze *Eerdere AI-antwoorden houden* of *De AI opnieuw vragen*; met de tweede tellen eerdere antwoorden in de cache niet meer voor die afbeelding (`?ai=opnieuw`). API: `GET` en `DELETE …/bestand/{mid}/werk` (wens Olaf).
- *AI-suggesties voor deze afbeelding* en de (i) zeggen nu dat de suggesties bij de afbeelding horen, niet bij de objecten (wens Olaf).
- *Ook gevonden als: boy × child ×* in de objectenlijst en de vergroter: met × haal je een woord weg waar de beelddetectie ernaast zat; het object telt dan niet meer onder dat woord, met *Ongedaan maken*. Een woord dat ook in de naam of de beschrijving staat, heeft geen ×. In de lijst in kleine letters, vanaf het derde woord achter *+n meer*. API: `DELETE …/objecten/{id}/ook/{woord}` en `POST …/objecten/{id}/ook` (wens Olaf).

### Gewijzigd

- *Ontdubbelen*: de melding zegt welke objecten in welke zijn opgegaan, bijvoorbeeld *suitcase → cardboard box*, als lijst met opsommingstekens (wens Olaf).
- *Alleen deze maskers tonen*: een samengevoegd object telt ook mee onder de woorden waarmee het gevonden is (*girl* in *child*, *suitcase* in *cardboard box*); het masker houdt de kleur van zijn eigen soort (wens Olaf).
- Na een zoekopdracht staan de objecten waarin vondsten zijn opgegaan als lijst met opsommingstekens onder de melding (wens Olaf).
- *Beeldt af, zonder regio*: na de eerste ronde heet de knop *Alle items opnieuw lokaliseren*, en het bedrag telt alleen woorden die nog niet in de cache staan (wens Olaf).
- *Changelog* in het Engels: de soorten wijziging (*Added*, *Changed*, *Fixed*, …), de inleiding en de facetten in de taal van de interface, met een regel dat de wijzigingen zelf in het Nederlands staan (wens Olaf).
- Engels: *Depicts, without a region* heet nu *Depicts, without a location* (wens Olaf).

### Opgelost

- Beschrijvingen en andere tekst van Commons toonden soms CSS van een sjabloon (`.mw-parser-output .plainlist ul{…}`); stijlblokken, scripts en losse CSS-regels gaan nu weg, voor alle bestanden (wens Olaf).
- De kolom met de afbeelding had geen kop; nu wel (*Afbeelding*, met een (i) en de pijl om haar weg te schuiven), en de koppen van alle vier de kolommen zijn even hoog, zodat hun onderrand één lijn is, met een lichte achtergrond (wens Olaf).
- Meldingen stonden bovenaan de pagina in plaats van bij de knop die erom vroeg: *Opnieuw lezen van Commons*, het weghalen van (een deel van) de AI-suggesties, *Selectie opslaan*, het masker van SAM in de vergroter en het weghalen van een vorm. Nu staan ze, met hun fouten, bij die knop (wens Olaf).
- Na het openen van een afbeelding herschreef de pagina het hele adres; nu veranderen alleen bestand en pagina, en blijven andere keuzes (`uselang`, `q`, …) staan.
- *AI-suggesties*: een zoekterm telde objecten niet die met dat woord gevonden en daarna in een ander object opgegaan waren (*girl* in *child*, *lawn* in *fence*), of die in een groep zitten; nu wel, en de regel *Op de afbeelding* telt elk object één keer (wens Olaf).
- Ontdubbelen werkte niet met objecten in een groep: een nieuwe vondst of een object dat hetzelfde toont als een lid van een groep, gaat nu in dat lid op (wens Olaf).
- Bij samenvoegen ging de koppeling aan een *Beeldt af*-item verloren (*car* in *vintage car*); die blijft nu bewaard.

## [0.35.0] - 2026-11-09

### Toegevoegd

- *Verbruik*: alle kolommen zijn sorteerbaar met een klik op de kop. *Changelog*: een tabelweergave met sorteerbare kolommen naast *Per versie* (wens Olaf).
- *Objecten* en *Prullenbak*: een lijstweergave met sorteerbare kolommen naast de kaarten; ‹ › in de vergroter volgen de volgorde van de lijst (wens Olaf).
- *Objecten* en *Prullenbak*: een zoekveld boven de facetten, zoals op *Changelog*. De knoppen voor alles wat zichtbaar is, de vergroter en de export volgen het (wens Olaf).

## [0.34.0] - 2026-11-09

### Toegevoegd

- *Alleen deze maskers tonen*: wat je in het zoekveld boven de objectenlijst typt, staat er als vinkje bij met het aantal treffers, bijvoorbeeld *doll (2)*, ook als het woord alleen in de AI-beschrijving voorkomt (wens Olaf).
- *Changelog*, *Verbruik* en *Objecten* (ook de prullenbak): exporteren als JSON, CSV en Excel, van wat de facetten en het zoekveld tonen, met `GET …/export` in de API (wens Olaf).
- API: `GET /api/v1/changelog` geeft de changelog als gegevens (wens Olaf).
- *Changelog* en *Verbruik*: facetten en een zoekveld, in de stijl van de pagina *Objecten*, met een versleepbare rand (wens Olaf). *Changelog*: soort wijziging, versiereeks en datum. *Verbruik*: soort, datum, bestand (met miniatuur), model en gebruiker; de uitkomst toont ook de kosten van wat past.
- *Changelog* en *Verbruik*: een facet met meer dan zes waarden zet de zevende en verder in een uitklapblok, dat zegt hoeveel erin aangevinkt is. De waarden staan op aantal, hoogste eerst; datums en versiereeksen op nieuwste eerst (wens Olaf).
- *Verbruik*: bij het facet *Model* een (i) met uitleg over de vier modellen en een korte omschrijving achter elke modelnaam (wens Olaf).

### Opgelost

- *Verbruik*: bij een AI-aangevulde versie stond de vertaalsleutel in de kolom Soort.

### Gewijzigd

- *Alleen deze maskers tonen*: een eigen naam (potlood) bepaalt nu de soort, ook bij een getekend kader of een klik; een pop die bij *person* gevonden is, wordt met de naam *doll* een eigen soort met een eigen kleur en telt mee onder *doll* én *person* (wens Olaf).
- *Alleen deze maskers tonen*: een groep van gemengde soorten telt mee onder elk van de soorten van zijn leden en blijft zichtbaar als er één aan staat; zijn masker houdt de kleur van het kader (wens Olaf).
- *Beeldt af, zonder regio* en de zoektermen bij *AI-suggesties*: *alle aan · alle uit · omkeren* staat nu onder de items of termen, naast de knop die alles tegelijk zoekt, met ervoor *Vinkjes selecteren:*, in plaats van in de uitleg (wens Olaf).
- *Beeldt af, zonder regio*: met een deel van de vinkjes heet de knop nu *Gekozen items lokaliseren* in plaats van *Gekozen termen detecteren* (wens Olaf).
- *Zoeken en objecten detecteren*: de knoppen heten nu *Alle objecten lokaliseren* en *Gekozen termen lokaliseren*, net als bij *Beeldt af, zonder regio* (wens Olaf).

## [0.33.16] - 2026-11-08

### Gewijzigd

- Een **groep heeft nu de soort van zijn leden** (wens Olaf): *group: cloud (13)* staat onder *cloud* bij *Alleen deze maskers tonen*, met de kleur en de stip van die soort, en vervaagt niet meer zodra je een andere soort uitvinkt. Een groep van gemengde soorten heeft geen soort.
- Een **regio uit Commons heeft nu zijn naam als soort** (wens Olaf): *dog* staat ook bij *Alleen deze maskers tonen*, met een stip in de lijst.

## [0.33.15] - 2026-11-08

### Documentatie

- FO (10, 12.1), overdracht, backlog, README en CLAUDE.md bijgewerkt: de Kleurenlegenda, de alleen-lezen vergroter voor de prullenbak, *Tonen in map*, de opslag op de Build Service, en drie valkuilen (geen `:class` op de viewer, de laadvolgorde van Codex in Vite, `watch` voor een `const`).

### Gewijzigd

- In de lijst met objecten staat nu **Vinkjes selecteren:** voor *Alle · Geen · Omkeren*, met per link een tooltip over wat er met de vinkjes gebeurt (wens Olaf).

## [0.33.14] - 2026-11-08

### Opgelost

- *Maskers*, *Kaders* of *Namen* aan- of uitzetten wiste de filters in de afbeelding: alle maskers kwamen terug terwijl er maar één soort aangevinkt stond (gemeld door Olaf). Vue herschreef bij elke wijziging de hele class-lijst van de viewer, en daarmee ook wat de viewer zelf had gezet (filter, vervagen, kruisdraad bij aanwijzen of tekenen). De schakelaars zetten nu alleen nog hun eigen class.

## [0.33.13] - 2026-11-08

### Gewijzigd

- In de *Kleurenlegenda* staat voor de vinkjes **Alleen deze kaders tonen** (EN *Show only these boxes*), zoals *Alleen deze maskers tonen* bij de maskers (wens Olaf).
- De (i) van de kleuren staat nu in de kop *Kleurenlegenda*; *Alleen deze kaders tonen* en *Alleen deze maskers tonen* staan recht onder elkaar, even groot en even vet, zodat de vinkjes van beide regels op dezelfde plek beginnen (wens Olaf).
- De regel van de maskers staat nu ook in de *Kleurenlegenda*, zodat de kop met de (i) er altijd is, ook met *Kaders* uit; dichtklappen verbergt beide regels (wens Olaf).
- Een klik op de (i) van de *Kleurenlegenda* klapt de legenda ook open; in de Engelse uitleg heet het kader nu *Boxes*, zoals de schakelaar (wens Olaf).

## [0.33.12] - 2026-11-08

### Verwijderd

- De schakelaar **Kleur maskers: per soort / per status** (besluit Olaf): een masker toont nu altijd de soort, een kader altijd de status, zodat elke kleur één betekenis heeft. Met één soort op de afbeelding volgen de maskers nog de kleur van hun kader. De stippen in de lijst staan er dus altijd; de keuze die de browser onthield, telt niet meer.

### Opgelost

- Een object in focus uitvinken in de lijst kon **alle kaders en namen in de afbeelding laten vervagen**, ook dat van het object zelf, tot je *Kaders* uit- en weer aanzette (gemeld door Olaf). De viewer bepaalt nu na elke wijziging opnieuw of er echt een object onder de muis is; alleen dan vervagen de andere.
- *Alleen tonen*: de soorten vormen één blok dat binnen zichzelf afbreekt, zodat een tweede regel onder de eerste soort begint (wens Olaf); in een smalle kolom gaat het hele blok naar een eigen regel. De vinkjes staan op één hoogte met hun naam, dicht bij hun naam en met meer ruimte tussen de soorten; elk vinkje heeft de kleur van zijn soort (gevuld als het aan staat, de rand als het uit staat), dus zonder aparte stip, en met het aantal objecten van die soort erachter (wens Olaf).
- De **Kleurenlegenda** van de kaders heeft nu ook een vinkje per status (geselecteerd, gevonden, Commons-regio, zelf getekend, uitgesloten), in de kleur van het kader, met aantallen en *Alle · Geen · Omkeren* (wens Olaf). Uitvinken laat die objecten vervagen; samen met *Alleen tonen*: goed zichtbaar is wat in beide aan staat. *Nieuw* en *dikker* blijven uitleg.
- De *Kleurenlegenda* van de kaders staat nu standaard open, zoals de regel van de maskers, met de (i) vooraan in de regel; is de legenda dicht of staan de kaders uit, dan staat die ene (i) vooraan in de regel van de maskers (wens Olaf).
- *Alleen tonen* heet nu **Alleen deze maskers tonen** (EN *Show only these masks*), zodat duidelijk is dat het over de maskers gaat (wens Olaf).

## [0.33.11] - 2026-11-08

### Gewijzigd

- *Alleen tonen* in de viewer: de soorten zijn nu **vinkjes** in plaats van links, met **Alle · Geen · Omkeren** zoals in de lijst met objecten (wens Olaf). Aangevinkt is zichtbaar; in het begin staan alle soorten aan, en een soort die later gevonden wordt ook. Kleine letters en vinkjes, zoals de rest van de regel.

## [0.33.10] - 2026-11-08

### Toegevoegd

- Een **(i)** bij *Kleur maskers* en in de *Kleurenlegenda* van de viewer (wens Olaf): één venster dat alle kleuren uitlegt: het kader (status), het masker (*per soort* of *per status*, met de stippen in de lijst), de witte rand van een masker, *Alleen tonen* en de schakelaars *Maskers*, *Kaders* en *Namen*.

## [0.33.9] - 2026-11-08

### Verwijderd

- De **verouderde API-paden** van vóór 0.29.0 (besluit Olaf, backlog 12e): `…/object/{object_id}` en alles daaronder, POST `…/beschrijving/terugzetten`, DELETE `…/beschrijving/geschiedenis?versie=`, `{"samenvoegen": true}` bij PATCH `…/objecten` en POST `…/commons/controle`. Ze geven nu 404 (of 400 voor `samenvoegen`); de app gebruikte ze al niet meer. Geen `Deprecation`-kop meer, en `deprecated` uit de OpenAPI.

### Toegevoegd

- Een **eigen naam** (potlood) gaat nu altijd mee in de prompt als aanwijzing, ook bij een **groep** (*The user named this group as a whole: …*), een **getekend kader** en een **klik** (wens Olaf). Zonder naam krijgen die nog steeds geen aanwijzing. FO 6.2.
- **Een kleur per soort object** (wens Olaf): met twee of meer soorten (zoektermen, zoals *plate* en *wine glass*) krijgen de maskers per soort een eigen kleur, met een stip in die kleur in de lijst *Objecten*. Het kader houdt de kleur van de status. Onder de werkbalk van de viewer staat *Alleen tonen*: elke soort is een link die alleen de maskers van die soort toont; *Alle soorten* toont ze weer allemaal. Niet voor getekende kaders, kliks, groepen en regio's uit Commons. FO 10.
- Pagina *Objecten*: de **rand tussen de filters en de objecten is versleepbaar** (ook met de pijltjes; dubbelklik zet hem terug; onthouden in de browser), en in het facet *Bestand* staat bij elk bestand een **miniatuur**; een klik toont de afbeelding groot, te zoomen (schuif, knoppen, muiswiel), te verslepen en te scrollen zoals in de vergroter, met de omtrek van het masker van elk object van dat bestand (wit met een donkere rand; zonder vorm het kader) uit het tabblad waar je het opende (*Objecten* of *Prullenbak*), zodat je ziet waar ze op de afbeelding staan, met *Openen in Mineventory* (met het icoon van de app) en *Op Commons* (met het Commons-logo) (wens Olaf). Het tabblad **Prullenbak** heeft dezelfde facetten en de versleepbare rand, met *Getoonde objecten terugzetten* en *Getoonde objecten definitief verwijderen* (met bevestiging en miniaturen) als er gefilterd is (wens Olaf). De kaarten in de prullenbak hebben ook het **oog** (de vergroter, met ‹ › door de getoonde prullenbak; alleen om te bekijken: alleen het tabblad *Uitsnede* (zonder *AI-aangevuld*, *Wat staat hierop?* en *Commons-concept*), zonder de keuze PNG/JPG, zonder bijschrift, downloads, *Aanvullen met AI* en *Naar de prullenbak*, met de zin dat je het terugzet om het te bewerken) en tonen nu ook de bron, *AI-aangevuld* en *opgeslagen* (een object in de prullenbak houdt zijn opgeslagen uitsneden tot je de prullenbak leegt).
- Pagina *Objecten*: het facet **AI-aangevuld** (objecten met een AI-aangevulde versie) onder *Bron*, met *AI-aangevuld* op de kaart, en een **oog** naast de prullenbak dat het object in de vergroter opent (`?vergroten=1` naast `?object=`); met het facet *AI-aangevuld* aan opent het oog meteen het tabblad met de AI-aangevulde versie (`?vergroten=aangevuld`) (wens Olaf). Het oog opent de **vergroter op de pagina *Objecten* zelf**: sluiten laat je waar je was, met je filters, en ‹ › gaan door de objecten die de filters tonen (Ctrl-klik opent de afbeeldingspagina; *Vorm met SAM* gaat ook daarheen, want dat kost geld en vraagt de afbeelding). De prullenbak op een kaart vraagt nu eerst bevestiging, met de miniatuur (ook bij *alle getoonde objecten*, tot 40), zoals de knop voor alle getoonde objecten; bij een regio uit Commons met de zin dat er op Commons niets verandert. *Ongedaan maken · Naar de prullenbak* liep aan elkaar.
- Schakelaar **Kleur maskers: per soort / per status** op de regel van de soorten, onthouden in de browser (wens Olaf). Elke kleur betekent zo één ding: het kader de status, de vulling van het masker de soort (of de status).
- Bij een **opgeslagen uitsnede** op de pagina *Objecten* (en in de prullenbak): *Bestand openen* en *Downloaden* (de PNG van de vorm, anders de JPG, in volledige resolutie), en alleen als de app op je eigen computer draait (debugmodus, zelfde machine) ook *Tonen in map*: de verkenner opent met het bestand geselecteerd (wens Olaf). Op Toolforge ziet niemand de schijf; daar blijven openen en downloaden. API: `POST …/objecten/{id}/uitsnede/mapvenster` (anders 403 `not_local`).
- Link **Prullenbak** in de kop, naast *Objecten* (wens Olaf): opent `/objecten?tab=prullenbak`.
- Elk masker in de viewer krijgt een **rand van 2 pixels**, wit met een dunne donkere rand erbuiten (wens Olaf): zonder eigen betekenis, leesbaar op elk beeld, even dik bij elke zoom. Hij volgt de vorm (een SVG-filter) en verdwijnt met *Maskers* uit.

## [0.33.8] - 2026-11-08

### Toegevoegd

- **Aanwijzing uit de detectie** in de vraag *Wat staat hierop?* (wens Olaf): één zin over wat de app al weet, met voorrang een eigen naam, het label van een Commons-regio, of de zoekterm van SAM met de zekerheid (*probably (part of) what "table" describes … Check what you see*; onder 50% *unsure*). Niet bij een groep, een getekend kader, een klik of een eigen prompt. Zichtbaar in de prompt; het antwoord bewaart `detectie_aanwijzing`. Of het helpt, toetst Olaf: docs/vergelijking-detectie-aanwijzing.md, backlog 12i. FO 6.2.
- *Wat is dit?*: een eigen **AI-prompt** per object (wens Olaf). Eén rij *AI-prompt*, ook bij een groep (de groepszin met *Alleen deze objecten* staat erin als *Deel van de prompt van de app voor deze groep*, grijs bij een eigen prompt), toont welke prompt de volgende vraag gebruikt (*Tonen*), met een potlood om hem aan te passen, *Prompt bewaren*, *Terug naar de prompt van de app* en *Eerdere prompts* om opnieuw te gebruiken of te verwijderen. API: `PUT`/`DELETE …/beschrijving/prompt`, `DELETE …/beschrijving/prompt/geschiedenis/{versie}`; het antwoord bewaart `prompt_eigen`. Opgenomen in het herontwerp van het tabblad (docs/ontwerp-wat-is-dit.md, backlog 12h). FO 6.2.
- Het venster van *Describe* in de bulkacties toont naast de instellingen *wat de AI ziet* (met het rode kader), dat de ruimte rond de uitsnede volgt; klik op een object of gebruik de pijltjes om een ander te zien. De prompt hoort bij het gekozen object. Het venster legt zichzelf uit, zonder verwijzing naar *Wat is dit?* (wens Olaf). Naast de schuif *Lengte* staat de schakelaar *Commons-caption* met het Commons-merkje, zoals bij de beschrijving van de hele afbeelding; de lengte begint hier op *Commons-caption* (hooguit 250 tekens). De objecten staan in een tabel met hun AI-parameters (lengte, ruimte, aanwijzing, prompt), met vaste kolombreedtes. Elk object heeft eigen instellingen: met *Alle objecten (n)* gekozen (standaard) gaat een wijziging naar alle, met één object gekozen alleen naar dat object (wens Olaf). *Reset defaults (for all objects)* zet ze allemaal terug. De instellingen, tot en met de prompt, staan in de uitklapper *Settings for the AI* (standaard dicht, grotere kop); een klik op één object klapt hem open. Drie niveaus van koppen: secties, instellingen en uitleg. Onderaan *Unhappy with the AI descriptions?*: daarna pas je elke beschrijving per object aan in de vergroter (het oog).
- *Describe* in de bulkacties opent een eigen venster met de instellingen voor de AI, net als *Wat is dit?* (wens Olaf): een optionele aanwijzing, de lengte (tot een Commons-caption van hooguit 250 tekens), de ruimte rond de uitsnede (begint op 0%) en de prompt zoals hij naar het model gaat (alleen te lezen). Die instellingen gaan mee met elk object. Nieuw: `GET …/objecten/{id}/beschrijving/prompt` (gratis). FO 7.4.
- Bulkactie *Describe* heeft nu ook *Per kind*, zoals Group en Trash (wens Olaf): per zoekterm de zichtbare objecten zonder beschrijving, met het bedrag bij elke link en de gewone bevestiging met miniaturen. FO 7.4.
- Een smal zoekveld in de kop van de objectenlijst, naast *All · None · Invert* (wens Olaf): alleen objecten waarvan de naam, zoekterm, het item, het bijschrift of de beschrijving alle woorden bevat, in de lijst en in het beeld. *Alle · Geen · Omkeren* en *alle* in de bulkacties gaan dan over de gevonden objecten; vinkjes daarbuiten blijven staan. Zoeken kan in het Nederlands en het Engels; een (i) naast het veld legt het uit. FO 7.6.
- Twee uitklappers onder de objectenlijst, standaard dicht: *Bulk actions* (de vier tabbladen Describe, Deduplicate, Group en Trash) en *Save and export* (Save selection, Download (zip), To Commons en de bewaartermijnen) (wens Olaf).
- De (i) bij *Found objects (cut-outs)* legt *Bulk actions* en *Save and export* elk in een eigen alinea uit, in plaats van het oude *At the bottom*; de inleiding en *Ticking* verwijzen naar *Save and export* (wens Olaf).
- In de objectenlijst krijgt een object dat nog geen beschrijving heeft (niet door de AI en geen eigen bijschrift) een klein label *not described yet*, met uitleg bij de muis (wens Olaf).

### Gewijzigd

- *Beeldt af, zonder regio*: de knop heet *Locate all items* (was *Detect all items*), en de *Bulk*-uitleg zegt *locating* (wens Olaf).
- *Beeldt af, zonder regio*: de uitleg in een nieuwe volgorde: *Single items:* (vet; klikken op een item), *Bulk:* (vet; de vinkjes met alles aan · alles uit · omkeren), *Search word:* (vet; het potlood), *Results:* (vet; groen/grijs) en *Add new region:* (vet), met een link die *Point or draw* openklapt en ernaartoe scrolt. De regel *Cost per item* is weg (wens Olaf).
- Uitleg boven de vinkjes bij *Beeldt af, zonder regio* en bij de zoektermen: *Unselect an item that should not go along when detecting all items in bulk* (wens Olaf; de zoektermen net zo).
- *Van Commons*, *Beeldt af, zonder regio*: de uitleg luidt nu *According to Commons, these items are already 'depicted' (P180) in the image, but without a specific location / bounding box*, met een link naar P180 op Wikidata (wens Olaf).

## [0.33.7] - 2026-11-07

### Gewijzigd

- *Zoektermen zonder gevonden object* is een gewone kop in plaats van een uitklapblok (wens Olaf).
- *Met plek* heet nu *Neem 'relatieve positie in afbeelding' (P2677) op als kwalificator*, met een link naar P2677 op Wikidata (wens Olaf).
- *Met plek* in het venster heeft een (i) in plaats van een tooltip, met uitleg voor die regel zelf: wat er met en zonder plek op Commons komt, met het item en het aantal objecten (wens Olaf).

## [0.33.6] - 2026-11-06

### Opgelost

- Een AI-caption van meer dan 250 tekens (niet gevraagd als Commons-caption) staat niet meer standaard aangevinkt, zodat hij het bewaren van het concept niet blokkeert; de melding noemt de taal.
- *Concept bewaren* bleef uitgeschakeld met *een caption is langer dan 250 tekens* terwijl je die caption niet had aangepast; nu telt alleen een tekst die echt bewaard wordt.
- Een AI-zoekterm krijgt op Wikidata bij voorkeur een item met precies die naam, met dezelfde hoofdletters: *lute* gaf eerst *Paris* (bijnaam Lutetia), *lemon* de band *LemON*.

### Toegevoegd

- Tabblad *Captions*: is het AI-voorstel langer dan 250 tekens, dan zegt het venster hoe lang, met *Inkorten tot 250 tekens* (gratis, na de laatste hele zin) en *Commons-caption laten maken door de AI* (betaald, met de gewone bevestiging; de huidige beschrijving gaat naar *Eerdere beschrijvingen*). Het nieuwe voorstel komt meteen in het venster (wens Olaf).
- Bij *Voorstellen* in het venster een (i) die een regel uitlegt (de bronnen, *met plek* en *zonder plek*, het potloodje en het prullenbakje), en *Alle · Geen · Omkeren* voor de vinkjes (wens Olaf).
- Een rood prullenbakje per regel in het venster haalt een voorstel weg dat je niet wilt zien (wens Olaf); het blijft weg in het concept (`verborgen`), met *Weer tonen* om het terug te halen.
- Wijs je een afbeelding van een Wikidata-item aan, dan verschijnt er een grotere versie naast (wens Olaf).
- Een Wikidata-item zonder afbeelding krijgt een grijs vakje *Geen afbeelding* in plaats van een lege plek (wens Olaf).
- Ook bij *Zoektermen zonder gevonden object* staan de afbeelding (P18) en de beschrijving van het Wikidata-item, en een potloodje om een ander item te kiezen (wens Olaf).
- Het venster *Gestructureerde gegevens van deze afbeelding* is te verslepen (aan de titelbalk) en van grootte te veranderen (aan de randen en hoeken), zoals de vergroter; dubbelklik op de titelbalk zet het terug (wens Olaf).
- In het venster *Gestructureerde gegevens van deze afbeelding* staat bij elk Wikidata-item zijn eigen afbeelding (P18), als die er is, ook bij de zoekresultaten van *Ander item kiezen* (wens Olaf). Zo zie je sneller of het het goede item is. Via de eigen server (`GET /wikidata/{q}/afbeelding`), zodat de browser niets van Wikimedia laadt; gecachet.

## [0.33.5] - 2026-11-06

### Toegevoegd

- **Geen dubbele verklaringen op het origineel, zichtbaar** (backlog 15e, regels 1 en 4 van FO 9.7): het venster *Gestructureerde gegevens van deze afbeelding* zegt per regel welke objecten hun plek al met de upload van hun uitsnede krijgen (één verklaring per object), en het *Commons-concept* van een object noemt de items die het venster er al voor heeft. API: `upload` per object in `GET …/origineel`, `in_venster` in het Commons-concept.
- **AI-aangevuld: eigen prompt en eerdere versies** (wens Olaf, FO 7.7): een potloodje bij de AI-prompt om die aan te passen voor de volgende keer, met *Terug naar de prompt van de app*; eerdere versies als carrousel met klein beeld, prompt en tijd, *Deze gebruiken* (gratis) en verwijderen. *Weghalen* bewaart de versie bij de eerdere. API: `prompt` bij `POST …/aanvulling`, `PUT …/aanvulling`, `DELETE …/aanvulling/geschiedenis/{sleutel}`, `aangevuld.png?sleutel=`.
- **Venster *Gestructureerde gegevens van deze afbeelding*** (FO 9.7, backlog 15b, wens Olaf), met de knop *Toevoegen aan de gestructureerde gegevens van deze afbeelding (op Commons)* in *AI-suggesties voor deze afbeelding*. Tabblad *Beeldt af (P180)*: wat al op Commons staat (alleen lezen; bij een item zonder plek dat de app vond, kun je de plek laten toevoegen), en de voorstellen: items die je bij uitsneden koos (aangevinkt), de AI-zoektermen en de suggesties van *Wat staat hierop?*, gratis opgezocht op Wikidata (niet aangevinkt, met AI-merkje, ander item te kiezen), hetzelfde item uit meer bronnen als één regel, *met plek* per regel, zoektermen zonder object ingeklapt, en zelf een item toevoegen. Tabblad *Captions*: per taal de caption op Commons en het AI-voorstel, met *Toevoegen*, of bij een bestaande caption *Zelf schrijven* (standaard, begint met beide), *Bestaande houden* of *Vervangen*, met een teller tot 250 tekens. *Concept bewaren* (API: `GET` en `PUT …/origineel`); *Op Commons opslaan…* komt in fase 2 en staat er uitgeschakeld. Uit bij bestanden met meer pagina's.

### Gewijzigd

- FO 9.7 *Verhouding tot 9.4: geen botsingen* (vraag Olaf): de uitsnede krijgt *beeldt af* zonder positie (ander bestand, geen botsing); op het origineel schrijven de upload en het venster allebei, met regels: één lijst geplande wijzigingen, ontdubbelen vóór het schrijven, met positie gaat voor zonder, één verklaring per object. Backlog 15e.
- Backlog 19d (idee Olaf): *Verder vanaf deze versie* bij een AI-aangevulde versie; FO 7.7 legt uit dat opnieuw vragen altijd bij de oorspronkelijke uitsnede begint.
- *Afbeelding aanvullen met AI* staat op het tabblad *Uitsnede* alleen de eerste keer; opnieuw vragen doe je op het tabblad *AI-aangevuld* (wens Olaf).
- De uitleg onder de knop voor de gestructureerde gegevens zegt dat de zoektermen en gevonden objecten kandidaten zijn voor 'beeldt af' (P180), en dat je ze in het venster zelf bekijkt en goedkeurt (wens Olaf).
- Het deel *Zoektermen* in *AI-suggesties voor deze afbeelding* heet nu *Zoeken en objecten detecteren* (*Search & detect objects*), en de knop *Toevoegen aan de gestructureerde gegevens van deze afbeelding (op Commons)* (wens Olaf).
- De uitleg (i) bij *Uit Commons* noemt de vier soorten gegevens als opsomming, met daarna een alinea per soort (wens Olaf). Een (i)-uitleg kan nu opsommingen en meer dan drie alinea's hebben.
- Functioneel ontwerp 9.8 *Notitie op het origineel* (voorstel, backlog 15d): een object met zijn beschrijving als `{{ImageNote}}` op de bestandspagina, omdat ImageAnnotator notities voor iedereen tekent en Commons regio's uit de gestructureerde gegevens niet (besluit Olaf).
- Functioneel ontwerp 7.5: nagekeken hoe Commons de regio's (P180 met P2677) tekent. Niet standaard; alleen met het gebruikersscript van de tool Wikidata Image Positions, en dan met alleen het label van het item.

## [0.33.4] - 2026-11-06

### Gewijzigd

- Een fout bij een bulkactie (beschrijven, ontdubbelen, groeperen, prullenbak) staat in het tabblad, onder de knop, niet meer bovenaan de pagina (wens Olaf). Is de server niet bereikbaar, dan staat er een begrijpelijke melding in plaats van *Failed to fetch*.
- Het kostenvenster van *Geselecteerde beschrijven* en *Alle beschrijven* toont de objecten als lijst met kleine uitsneden, zoals bij groeperen, in plaats van een rij namen (wens Olaf).

## [0.33.3] - 2026-11-06

### Gewijzigd

- **Bulkacties in vier tabbladen** onder de lijst (wens Olaf, FO 7.4): *Beschrijven*, *Ontdubbelen*, *Groeperen* en *Prullenbak*, elk met een knop voor de selectie en een voor alle zichtbare objecten, en bij groeperen en de prullenbak ook per soort. Het getal staat in de tabnaam. *Dubbelingen samenvoegen* heet nu *Ontdubbelen*, om het verschil met groeperen duidelijk te maken. Nieuw: ontdubbelen van alleen de selectie (API: `{"objecten": [ids]}` bij POST `…/samenvoegingen`), alles beschrijven, alles groeperen, en de selectie of alles naar de prullenbak.
- Hernoemen (potloodje of dubbelklikken) begint met de huidige naam in het veld, geselecteerd, zodat je die kunt aanpassen in plaats van een lege regel met een grijze naam (wens Olaf). Leegmaken zet de automatische naam terug.

## [0.33.2] - 2026-11-06

### Toegevoegd

- **Lengte** bij de beschrijving van een object: in de *AI-modifiers* van *Wat staat hierop?* dezelfde schuif als bij de hele afbeelding, met *Kort*, *Normaal*, *Commons-caption* (hooguit 250 tekens) en *Uitgebreid* (wens Olaf). API: `beschrijvingsniveau` bij `POST …/beschrijving`. In het functioneel ontwerp (6.2) en het ontwerp van *Wat staat hierop?*.

### Gewijzigd

- De stand en de schakelaar heten nu **Commons-caption** in plaats van Wikidata-caption, met een Commons-teken in plaats van het Wikidata-logo: het gaat om captions op Commons (wens Olaf). Ook in de documentatie.

### Opgelost

- Een *beeldt af*-chip in *Uit Commons* toont na het aanpassen met het potloodje je eigen zoekwoord, zoals de AI-zoektermen; het Wikidata-label en de Q-id staan in de tooltip (wens Olaf).

## [0.33.1] - 2026-11-06

### Toegevoegd

- **Per soort in bulk** onder *Geselecteerde objecten groeperen*: twee tabbladen, *Groeperen* (zoals voorheen *Groeperen: alle …*) en *Naar de prullenbak* (wens Olaf). Met *alle hoed (17)* gaan alle zichtbare objecten van die soort in één keer naar de prullenbak, na een bevestiging met de lijst; één melding met *Ongedaan maken* voor allemaal. Bij regio's uit Commons zegt het venster dat er op Commons niets verandert.

## [0.33.0] - 2026-11-06

### Toegevoegd

- **Uit Commons gebruikt alles wat het bestand al heeft** (backlog 26, FO 7.5, wens Olaf): de captions op Commons (alleen lezen) en de *beeldt af* (P180) zonder regio als chips. Een klik laat de AI-beelddetectie dat item zoeken (betaald, met bedrag en bevestiging); wat gevonden wordt, krijgt meteen dat Wikidata-item, dus ook als *beeldt af* in het Commons-concept. Het zoekwoord (het Engelse label) is per item aan te passen met het potloodje; aanvinken en *Alle items detecteren* zoals bij de zoektermen. Uitleg dat de app alleen aanvult, met een link naar de gegevens op Commons.
- De bestaande captions en *beeldt af*-items gaan mee als context als de AI de afbeelding beschrijft. Een AI-zoekterm voor iets wat al als *beeldt af* op Commons staat, krijgt het merkje *op Commons*.
- API: `items` ({zoekterm: Q-id}) bij `POST …/detecties`.
- Ook bij de AI-zoektermen in *AI-suggesties voor deze afbeelding* pas je het zoekwoord aan met een potloodje (wens Olaf): de chip toont dan je eigen woord, de tooltip zegt waarmee gezocht is, en *Alle objecten detecteren* gebruikt het ook. Per bestand en pagina onthouden in de browser; leeg zet het terug.
- **Prullenbak met keuze** bij een object met een vorm van SAM bij een rechthoek, zoals een regio uit Commons na *Vorm met SAM* (wens Olaf): *Alleen de vorm van SAM* (gratis; het object houdt zijn rechthoek, bij een regio die van Commons) of *Het hele object naar de prullenbak*. Bij een regio uit Commons zegt het venster altijd dat er op Commons niets verandert, met een link: weghalen of aanpassen doe je op Commons zelf. API: `DELETE …/objecten/{id}/vorm`.
- **Opnieuw lezen van Commons** in *Uit Commons* (wens Olaf, na het toevoegen van een Engelse caption): de app bewaart wat hij van Commons leest een dag; de link leest het bestand opnieuw. Gratis, alleen lezen. API: `POST /bestand/{mid}/opnieuw-lezen`.

### Gewijzigd

- Zoekchips (AI-zoektermen en *beeldt af*-items) kleuren na het zoeken: groen met het aantal als er iets op de afbeelding staat, grijs met een 0 als er gezocht is maar niets gevonden (wens Olaf). Welke woorden gezocht zijn, onthoudt de browser per bestand en pagina.
- In het kostenvenster van de AI-beelddetectie staan de zoektermen als opsomming; een lange lijst scrolt, zodat het venster nooit hoger wordt dan het scherm (wens Olaf).
- *Uit Commons* heeft drie uitklapblokken, zoals *AI-suggesties voor deze afbeelding*: *Captions op Commons*, *Regio's en notities* en *Beeldt af, zonder regio* (wens Olaf).
- De uitleg bij *Beeldt af, zonder regio* is een opsomming; de link heet *Toon de 'beeldt af'-verklaringen op Commons* (wens Olaf).
- Heeft het bestand gegevens op Commons, dan is *Uit Commons* open en zijn de andere blokken van *Beschrijven en vinden* dicht (wens Olaf); zonder zulke gegevens zijn de AI-suggesties open. *Uit Commons* verschijnt ook zonder regio's, als er een caption of *beeldt af* is.

### Opgelost

- De schakelaar *Kaders* verborg het gele kader van een geselecteerde regio uit Commons niet, en ook niet de naam erbij; nu wel (de naam blijft met *Namen* aan). Na *Vorm met SAM* staat er één kader, dat van SAM (wens Olaf).

## [0.32.12] - 2026-11-06

### Gewijzigd

- Nieuwe koppen van de kolommen (wens Olaf): *Objecten zoeken* heet nu **Beschrijven en vinden** (*Describe and find*), want de kolom beschrijft ook de hele afbeelding en maakt captions en zoektermen; *Wat je vond* heet nu **Gevonden objecten (uitsneden)** (*Found objects (cut-outs)*). De uitleg (i) zegt dat ook. Functioneel ontwerp, overdracht en README bijgewerkt.
- In *Beschrijven en vinden* staat *Uit Commons* nu boven *AI-suggesties voor deze afbeelding* (wens Olaf): wat al op Commons staat, gaat voor nieuwe AI-suggesties. De uitleg (i) volgt die volgorde.
- De uitleg (i) bij *Gevonden objecten (uitsneden)* heeft een eigen alinea over **het potloodje** (een object een eigen naam geven) (wens Olaf).

### Ontwerp

- Functioneel ontwerp 7.5, voorstel: ook de bestaande captions en de *beeldt af* (P180) zonder positie gebruiken in *Uit Commons*, als chips waarmee je het item op de afbeelding laat zoeken; als context voor de AI (backlog 26).
- Functioneel ontwerp 9.7 *Beeldt af en caption voor de hele afbeelding*: de besluiten van Olaf over het verzoenen van de AI-caption en de zoektermen (P180) met wat al op Commons staat. Alleen aanvullen, met uitleg dat je bestaande gegevens op Commons zelf aanpast; de caption uit de stand *Wikidata-caption*; een bestaande caption standaard samenvoegen in een tekstvak; geen venster bij bestanden met meer pagina's. Het samenstellen en het concept komen nu, vóór OAuth (backlog 15b).
- De schakelaar *Wikidata-caption* heeft kleinere letters en een kleiner schuifje (wens Olaf).
- Onder *Generate description again* en *Remove description* staat nu uitleg, net als onder de zoektermen: wat de AI beschrijft, aanpassen met het potloodje, eerdere versies, de stand *Wikidata-caption*, en dat opnieuw vragen weer kost (wens Olaf).

### Toegevoegd

- Stand **Wikidata-caption (hooguit 250 tekens)** (naam op aanwijzing van Olaf), ook met één klik via een schakelaar met het Wikidata-logo naast de schuif; uit zet de schuif terug op de stand ervoor in de schuif *Uitgebreidheid* van de beschrijving van de hele afbeelding (wens Olaf). 250 tekens is de grens van een caption in de gestructureerde gegevens op Commons (nagekeken op Commons:File captions; niet 255). De vraag aan de AI vraagt om hooguit 230 tekens; is het antwoord toch langer, dan kapt de server het af na de laatste hele zin (of het laatste hele woord, met …), zodat het nooit langer is dan 250, in het Nederlands en het Engels.

## [0.32.11] - 2026-11-06

### Gewijzigd

- Functioneel ontwerp 7.8 *3D-model van een uitsnede* (idee Olaf, nice-to-have, niet gepland): met SAM 3D Objects van Meta via Runware (beeld + masker → GLB, ongeveer $0,005), in een eigen tabblad om te draaien; achterkant verzonnen, nooit naar Commons. Met een vergelijking van de 3D-modellen op Runware. Backlog 19c.

### Toegevoegd

- Schuif **Uitgebreidheid** bij de beschrijving van de hele afbeelding (wens Olaf): *Kort* (een paar woorden), *Normaal* (één zin, zoals voorheen) of *Uitgebreid* (een alinea over wat er te zien is, de compositie, details, kleuren en stijl). Staat bovenaan, met daaronder naast elkaar *Beschrijving opnieuw laten maken* en *Beschrijving verwijderen*, net als bij de zoektermen, onder een eigen tussenkop *Beschrijving van de afbeelding* (wens Olaf); die en *Zoektermen* zijn elk in te klappen, net als *Aanwijzen* en *Tekenen* in *Aanwijzen of tekenen*; *Eerdere beschrijvingen* daarbinnen heeft als derde niveau een kleinere kop; los van het detailniveau van de zoektermen; de stand gaat mee in de vraag, staat bij het overzicht (`beschrijvingsniveau`) en heeft een eigen plek in de cache. API: `beschrijvingsniveau` bij POST `…/inventaris` en `…/inventaris/beschrijving`. Bij *Eerdere beschrijvingen* staat per AI-versie de gebruikte uitgebreidheid (bijv. *uitgebreidheid: Uitgebreid (een alinea)*); bij versies die al in de geschiedenis stonden, is de lengte onbekend en staat er niets (wens Olaf).

## [0.32.10] - 2026-11-06

### Gewijzigd

- *Afbeelding aanvullen met AI*: het onderwerp in de prompt is eerst de naam die je zelf gaf (bijv. *lute*), dan het onderwerp uit de beschrijving, het bijschrift of de zoekterm; nooit meer een interne naam als *klik* of *rechthoek*, dan staat er *an object* (melding Olaf). Ook in de AI-prompt van een groep. Een nieuwe vraag geeft dus een nieuwe aanvulling (en kost in live-modus weer $0,01); bestaande versies blijven.

- *Naar de prullenbak* vraagt altijd om bevestiging, overal (in de lijst, in de vergroter en op de pagina *Objecten*); de keuze *Niet meer vragen* is weg (wens Olaf). In de bewerker staat het object met zijn uitsnede in het venster.

- *Eerdere beschrijvingen* (van de afbeelding, en van een object in *Wat staat hierop?*) zijn een carrousel in plaats van een lange lijst (wens Olaf): één versie tegelijk, met *Vorige* en *Volgende* (ook ← en →), *2 van 5*, en ronde stippen eronder om naar een versie te springen. *Deze gebruiken* en het prullenbakje staan bij de versie. Eén onderdeel voor beide (`VersionCarousel.vue`).

- Elke bevestiging van kosten zegt nu ook wat er gaat gebeuren, boven het bedrag (wens Olaf): zoeken met welke zoektermen, de hele afbeelding laten bekijken of alleen de beschrijving of de zoektermen opnieuw (met het detailniveau), welke objecten beschreven worden, aanwijzen, de vorm in een rechthoek zoeken, en een object beschrijven in de vergroter.

- *Zoektermen*: eerst wat de zoektermen maakt, compact: de schuif *Detailniveau*, en daaronder altijd naast elkaar *Zoektermen opnieuw laten maken* (met het bedrag) en *Alle zoektermen verwijderen*, daaronder de zoektermen zelf als het resultaat, met de melding van het zoeken direct eronder (wens Olaf). De uitleg bij de schuif en over *opnieuw* staat nu in de tooltip. De knoppen heten *Zoektermen opnieuw laten maken* / *Generate search terms again* en *Alle zoektermen verwijderen* / *Remove all search terms* (wens Olaf), en zo heten ook het bevestigingsvenster, de knop erin en de melding daarna. Bij de beschrijving van de afbeelding: *Beschrijving opnieuw laten maken* / *Generate description again* en *Beschrijving verwijderen* / *Remove description* (wens Olaf).

### Opgelost

- De melding na het zoeken telde alles wat de AI vond, ook vondsten die niet als eigen object in de lijst komen (melding Olaf: *2 objecten gevonden* bij één zichtbaar trosje druiven). Nu telt *gevonden* alleen wat rechts en in het beeld staat, en zegt de melding waar de rest bleef: samengevallen met een object dat er al stond (met de naam), al in een groep, in de prullenbak, of verborgen door de minimale zekerheid. API: `nieuw` is alleen wat op de pagina staat, plus `elders`. De objecten waar de melding over gaat, de gevonden objecten en de groepen of objecten waarin een vondst opging, hebben in *Wat je vond* een groene rand (wens Olaf). De lijst schuift naar het eerste van die objecten. De melding heeft een kruisje om hem te sluiten; dan verdwijnen ook de groene randen (wens Olaf). Gingen alle vondsten elders heen, dan is de melding blauw in plaats van geel. Bij *Niets gevonden* staan de andere manieren als opsomming, met een hoofdletter: *Zoek met een ander woord*, *Wijs het object aan* en *Teken een rechthoek*; de laatste twee zetten die manier meteen aan (wens Olaf).

## [0.32.9] - 2026-11-06

### Toegevoegd

- Objecten in *Wat je vond* een eigen naam geven, zoals lagen in Photoshop (wens Olaf): dubbelklik op de naam of klik op het potlood; Enter bewaart, Esc annuleert, leeg geeft de automatische naam terug (die staat grijs in het veld). De naam gaat voor in de lijst, de vergroter en de bevestigingsvensters, en geldt in de AI-prompt van een groep als naam van het object. Niet het bijschrift en niet voor Commons. API: `naam` bij PATCH `…/objecten/{id}`.

## [0.32.8] - 2026-11-06

### Gewijzigd

- Functioneel ontwerp hoofdstuk 18 *Canvas: een speelveld voor uitsneden* (idee Olaf, nice-to-have, niet gepland): uitsneden en transparante beelden combineren tot nieuwe werken, in lagen, met export en bronvermelding; nooit naar Commons. Met Olafs antwoorden op het vragenformulier (18.12). Backlog 25.

## [0.32.7] - 2026-11-06

### Gewijzigd

- *Groeperen: alle … (n)* staat nu in *Wat je vond*, direct onder *Geselecteerde objecten groeperen*, zodat beide manieren van groeperen bij elkaar staan; niet meer onder de zoektermen (wens Olaf). Het werkt voor elke zoekterm met twee of meer losse objecten, ook van *Zoeken*.

## [0.32.6] - 2026-11-06

### Toegevoegd

- Ontwerpvoorstel om het tabblad *Wat staat hierop?* opnieuw in te delen met vier subtabbladen (*Antwoord*, *AI-prompt en bijsturing*, *Beeldt af (P180)*, *Eerder*), met schets en open vragen: `docs/ontwerp-wat-is-dit.md`, backlog 12h. Wacht op akkoord van Olaf; ook op de projectsite.
- In de vergroter zijn de uitsnede en de AI-aangevulde versie te zoomen en te verschuiven zoals in de hoofdviewer: knoppen, een schuif, het muiswiel en slepen, *Ware grootte* en *Passend* (wens Olaf, `ZoomImage.vue`, met dezelfde viewer-module).

### Gewijzigd

- Een groep beschrijven: de opdracht beweegt mee met *Ruimte rond de uitsnede* (melding Olaf). Zonder ruimte: *negeer alles wat verder te zien is*; met ruimte: *beschrijf alleen deze objecten als onderwerp, en gebruik de omgeving alleen als context, bijvoorbeeld een onderschrift*. Zo werkt de schuif weer. Met de schakelaar *Alleen deze objecten* (standaard aan) zet je de groepsopdracht uit; dan beschrijft de AI de groep als een gewone uitsnede. API: `alleen_groep` bij POST `…/beschrijving`.
- Een groep beschrijven: de eerdere beschrijvingen van de objecten erin gaan mee als context (wens Olaf): per object het onderwerp en de beschrijving in het Engels, en de tekst die erin en eromheen gelezen is, gemarkeerd als eerdere AI-antwoorden die fout kunnen zijn. Ze staan ook in de rij *AI-prompt*. Een antwoord van voordat een object beschreven was, wordt niet hergebruikt.
- Het grote venster (*groot bekijken*) gebruikt zijn hele hoogte voor het beeld, zodat *Passend* bij het openen het beeld echt passend maakt; eerst bleef het beeldvlak laag en het beeld klein (melding Olaf).
- In het grote venster staat boven de tekstvelden: *Heeft de AI tekst gemist, of las hij iets verkeerd? Vul het hier zelf in of verbeter het, met Bewerken.* (wens Olaf).
- De link onder *wat de AI ziet* zegt nu waar het om gaat (vraag Olaf): *groot bekijken en de tekst die de AI las (2) controleren* als de AI tekst in of rond het beeld las, *groot bekijken; de AI las geen tekst* als dat niet zo is (met uitleg dat je gemiste tekst daar zelf invult), en alleen *groot bekijken* vóór de eerste beschrijving.
- De automatische opdracht bij het beschrijven van een groep is nu zichtbaar (vraag Olaf): bij *AI-bijsturing* (*AI modifiers*) staat de **AI-prompt** die de app zelf toevoegt, cursief, met de objecten als pillen, als rij zoals *Bijschrift*, altijd zichtbaar in het tabblad *Wat staat hierop?* (wens Olaf), en onder het antwoord staat waarnaar gekeken is. Onder de uitsnede staat bij *Bron* waaruit de groep bestaat.
- Het venster *Groep opheffen* noemt de objecten zoals de lijst ze noemt (uit hun beschrijving of bijschrift), niet meer met hun korte zoekterm (melding Olaf). De namen zelf gingen nooit verloren: na het opheffen staan ze in de lijst zoals voor het groeperen.
- De AI-aangevulde versie heeft een doorzichtige achtergrond op een schaakbord, zoals de uitsnede: het wit dat met de rand verbonden is, wordt doorzichtig; wit binnen het onderwerp en alles binnen de vorm van de uitsnede blijft (wens Olaf). Ook de download is doorzichtig.
- Een groep aanvullen met AI: het onderwerp in de vraag aan Muse Image is de beschrijving of de naam van de groep, of anders de namen van de objecten erin, niet meer het woord *groep*.
- In het tabblad *AI-aangevuld* staat ook de **AI-prompt**, precies zoals die naar Muse Image ging (in het Engels; nu bewaard als `prompt`), cursief met het onderwerp als pil. Dat de app daarna de witte achtergrond doorzichtig maakt, staat er los onder, want dat hoort niet bij de prompt (wens Olaf).
- In het tabblad *AI-aangevuld* staan *Bron* en *Resolutie* in dezelfde stijl als onder de uitsnede (wens Olaf).

## [0.32.5] - 2026-11-06

### Toegevoegd

- De AI-aangevulde versie heeft in de vergroter een eigen tabblad *AI-aangevuld*, na *Uitsnede*, als er een is (wens Olaf). Na het aanvullen gaat de vergroter er vanzelf naartoe.
- De download van de AI-aangevulde versie heet in het Engels, zoals de rest van de bestandsnaam: *… (AI-augmented).png* (wens Olaf).
- Onder de AI-aangevulde versie staat de resolutie, naast die van de uitsnede, bijv. *Resolutie: 1536 × 1056 px (de uitsnede: 2754 × 1897 px)* (wens Olaf).
- Het venster bij *Weghalen* van de AI-aangevulde versie zegt nu wat er gebeurt: niet naar de prullenbak, het beeld blijft 30 dagen bewaard en is met *Afbeelding aanvullen met AI* gratis terug te halen (wens Olaf).
- Schakelaar *Toon wat de AI invulde* (wens Olaf): een magenta laag over de aangevulde versie op de plekken waar de uitsnede geen vorm had en de AI iets tekende. Bij benadering, want de AI tekent het hele beeld opnieuw. API: GET `…/objecten/{id}/aangevuld-ingevuld.png`.

## [0.32.4] - 2026-11-06

### Toegevoegd

- **AI-aangevulde versie** in de vergroter (opdracht Olaf, FO 7.7, backlog 19b): een knop met het bedrag laat Muse Image (`muse-image-1.0`) de witte gaten in een uitsnede invullen, bijv. waar op het origineel iets voor het object stond. Het resultaat staat apart onder de uitsnede, met een AI-merkje en de waarschuwing dat het verzonnen is; het is geen bron en gaat nooit als uitsnede naar Commons. Zonder zoeken op internet, gecachet, $0,01 per beeld in live-modus (eerst een bevestiging); in de proefmodus nagebootst. Downloaden als PNG, bekijken en weghalen. API: GET, POST en DELETE `…/objecten/{id}/aanvulling`, GET `…/aangevuld.png`. Live nog niet geprobeerd (geen betaalde aanroepen zonder opdracht).
- **Groeperen** (wens Olaf, FO 7.4, backlog 12g): van veel kleine objecten één object maken, zoals in PowerPoint. *Groeperen (n)* onder de objecten voor de geselecteerde, en onder de zoektermen *Groeperen: alle waterdruppels (15) · alle bladeren (9)* met één klik per zoekterm. De groep krijgt één kader om alle leden en de vereniging van hun maskers, heet bijv. *groep: waterdruppel (15)* en kan als één uitsnede naar Commons. De leden blijven bewaard: *Groep opheffen* in de lijst zet ze terug, en een nieuwe zoekopdracht zet ze niet los terug. Gratis. API: POST `…/groepen`, DELETE `…/groepen/{id}`.

### Gewijzigd

- Groeperen en *Groep opheffen* vragen eerst om bevestiging in een venster met de objecten erin, elk met een kleine uitsnede (wens Olaf). Bij groeperen kun je een eigen naam geven; leeg laten geeft de voorgestelde naam, die in het grijs in het veld staat (API: `"naam"` bij POST `…/groepen`). Bij opheffen zegt het venster ook als een bijschrift, beschrijving of opgeslagen uitsnede van de groep verloren gaat. De groene meldingen na groeperen en opheffen zijn weg.
- Is de AI-aangevulde versie klaar, dan schuift de vergroter ernaartoe (wens Olaf).
- De knop voor de AI-aangevulde versie heet nu *Afbeelding aanvullen met AI* / *Complete the image with AI* (wens Olaf).
- In *Wat je vond* scrolt op een breed scherm alleen de lijst van objecten: de schuifbalk staat naast de lijst en loopt niet meer door naast de knoppen eronder, die altijd zichtbaar blijven (wens Olaf). Alleen als zelfs een korte lijst niet past, scrolt de kolom zelf.
- Een groep beschrijven (*Wat is dit?*): de vraag aan de AI zegt nu waaruit de groep bestaat, bijv. *lemon (1), bunch of grapes (2)*, en om alleen daarnaar te kijken, niet naar wat verder in het kader te zien is (wens Olaf). Het antwoord onthoudt dat (`alleen_naar`); een eerder antwoord zonder die vraag wordt niet hergebruikt.
- De zekerheidsschuif loopt van de laagste tot de hoogste zekerheid op de afbeelding (wens Olaf): daaronder verandert er niets, daarboven zou alles verdwijnen.
- De knop heet nu *Geselecteerde objecten groeperen (n)* / *Group selected objects (n)* (wens Olaf).
- Backlog 19b: idee *AI-aangevulde versie* van een uitsnede met Muse Image, met de voorwaarden (geen bron, apart gemarkeerd, nooit als uitsnede naar Commons).
- Functioneel ontwerp 7.4 en backlog 12g: *Groeperen* uitgewerkt, met Olafs besluiten (5-11-2026): ook *Groepeer alle …* per zoekterm met één klik, en een groep mag als één uitsnede naar Commons. Nog niet gebouwd.

## [0.32.3] - 2026-11-05

### Toegevoegd

- Schuif **Detailniveau** bij *Beschrijf deze afbeelding* en bij *Zoektermen opnieuw vragen* (wens Olaf): van *Alleen het hoofdonderwerp* (1 zoekterm) via *Hoofdzaken* (ongeveer 3) en *Normaal* (tot 12, zoals voorheen) tot *Veel details* (tot 20 soorten, ook kleine dingen). De stand gaat mee in de vraag aan Muse Spark, staat bij het overzicht (`detailniveau`) en heeft een eigen plek in de cache; *Normaal* houdt de antwoorden van vóór de schuif. API: `detailniveau` in de body van POST `…/inventaris` en `…/inventaris/zoektermen`.
- Schuif **Minimale zekerheid** boven de objecten in *Wat je vond* (wens Olaf): verbergt objecten van de AI-beelddetectie onder de gekozen zekerheid, ook wat al gevonden is, gratis. Verborgen objecten zijn niet geselecteerd en gaan dus niet mee bij opslaan of beschrijven; terugschuiven laat ze weer zien. Onthouden in de browser.

### Gewijzigd

- Een afbeelding uit *Bekeken* opent binnen de app, zonder de pagina opnieuw te laden, zodat je meteen *Het bestand wordt opgehaald van Commons…* en het grijze skelet ziet (wens Olaf). Ctrl-klik opent hem nog steeds in een nieuw tabblad.
- *Niets gevonden voor …* zegt nu hoe je het anders probeert, met twee links (wens Olaf): *zoek met een ander of algemener woord* opent *Zoeken* met de term al ingevuld, *wijs het object aan of teken er een rechthoek omheen* opent *Aanwijzen of tekenen*.
- *Teruggezet uit de prullenbak* noemt het object, met de kleine uitsnede en de naam, zoals de melding bij het weggooien (wens Olaf).
- De melding *Naar de prullenbak* (met Ongedaan maken) en *Teruggezet* staan nu in de kolom *Wat je vond*, boven de lijst van objecten, waar je het object weggooide, en niet meer bovenaan de pagina (wens Olaf).

## [0.32.2] - 2026-11-05

### Toegevoegd

- Wachten op een bestand is zichtbaar (wens Olaf): na *Openen* staat onder de invoer *Het bestand wordt opgehaald van Commons…* met een voortgangsbalk, de seconden en een grijs skelet op de plek van het werkblad. Daarna, tot de afbeelding binnen is, een melding in de beeldkolom (de eerste keer haalt de server het origineel op) over een bewegend skelet; lukt het niet, dan een foutmelding. Zonder beweging bij *verminderde beweging*.

### Gewijzigd

- Functioneel ontwerp: Olafs antwoorden op de vragen bij het dashboard (17.10) en het starttegoed (8.6.6) zijn besluiten. Het dashboard wordt nu gebouwd, vóór OAuth, met de bewerker op `/bewerken`; de voorscan door AI is uitgesteld (te duur bij grote categorieën; backlog 19a). Het starttegoed is eenmalig 100 aanroepen, en een eigen Meta-sleutel gaat altijd voor. Fasering, besluitentabel, backlog 15a en 15c en de overdracht zijn bijgewerkt.

## [0.32.1] - 2026-11-05

### Toegevoegd

- Link naar de projectsite (GitHub Pages) in de footer van de app, tussen Documentatie en API; instelbaar met `PROJECTSITE_URL` (`.env.example`).

### Gewijzigd

- Functioneel ontwerp 8.5 *Werk per gebruiker* (besluit Olaf 5-11-2026): op Toolforge een eigen uitvoermap per ingelogde gebruiker, de cache en de AI-antwoorden gedeeld; met voorstellen voor de mapnaam, werk zonder inloggen, de verhuizing van de lokale mappen, het slot, de bewaartermijnen en de privacyverklaring. Nieuw backlogpunt 13a, bij OAuth (13).
- Functioneel ontwerp hoofdstuk 17 *Dashboard: collecties uit categorieën* (voorstel, op verzoek van Olaf): een categorie openen als raster van miniaturen, per bestand kiezen of er objecten in staan, een voorscan met SAM die de keuze voorstelt, en de gekozen bestanden als werkset één voor één in de bewerker; met schetsen, API, opslag, een volgorde voor de eerste bouw en negen vragen (17.10). Backlog 15a verwijst ernaar. Collecties zijn per gebruiker (besluit Olaf, 5-11-2026; FO 8.5 en 17.7). Merkjes en filters voor afbeeldingen die al bewerkt zijn, door jou in de app of op Commons (met de Mineventory of ander gereedschap), zodat je geen werk dubbel doet (17.4); twee vragen erbij (17.10).
- Functioneel ontwerp 8.6 *Starttegoed en een eigen Meta-sleutel* (voorstel, wens Olaf): op Toolforge ±$0,25 tegoed per ingelogde gebruiker, daarna een eigen sleutel voor de Meta Model API die versleuteld op de server staat en nooit via de API, logs of bestanden terugkomt; met API, beheer, verbruik en zes vragen (8.6.6). Nieuw backlogpunt 15c.
- Overdracht en backlog 12f: de code staat op GitHub; wat overblijft is `.env` bijwerken en de oude map verwijderen (Olaf).

## [0.32.0] - 2026-11-05

### Toegevoegd

- Projectsite voor GitHub Pages (besluit Olaf 5-11-2026: Pages is de documentatie en uitleg, de werkende app komt op Toolforge). `site/index.html` is een tweetalige landingspagina (NL/EN) met een klikbare carrousel van de schermafbeeldingen (pijlen, stippen, toetsen, pauze, vergroten), de functies, de werkwijze, de vergelijking met CropTool en de status per fase. `site/build.py` zet de documentatie (functioneel ontwerp, API, velden per sjabloon, privacy, overdracht, backlog, changelog) om naar webpagina's met menu en inhoudsopgave, met python-markdown in plaats van Jekyll, zodat de `{{…}}`-sjablonen in de docs heel blijven. De GitHub Action `.github/workflows/pages.yml` bouwt en publiceert de site bij elke push naar `main`. Geen externe lettertypen, scripts of CDN's.
- README: badge en alinea over de projectsite.

### Gewijzigd

- De verouderde API-paden van vóór 0.29.0 werken nog tot 0.33.0 (was 0.32.0, die werd de projectsite); OpenAPI, `docs/api.md`, de overdracht en backlog 12e zeggen dat.

## [0.31.4] - 2026-11-05

### Toegevoegd

- README: badges (versie, status, licentie, laatste commit, techniek) en een rondleiding langs de schermen: een geanimeerde carrousel (`docs/screenshots/carrousel.gif`) en een galerij van negen schermafbeeldingen met bijschriften (`docs/screenshots/`).

## [0.31.3] - 2026-11-05

### Gewijzigd

- De map is hernoemd naar `commons-mineventory`, de Python-omgeving opnieuw gemaakt; de GitHub-repo `KBNLwikimedia/commons-mineventory` is openbaar, met CLAUDE.md, de overdracht en de backlog erin (besluit Olaf 5-11-2026). Backlog 12f en `docs/overdracht.md` bijgewerkt.
- `.gitignore` sluit vóór het openbaar maken ook andere `.env.*`-bestanden uit (behalve `.env.example`), logbestanden, testdekking en `desktop.ini`.

## [0.31.2] - 2026-11-05

### Gewijzigd

- Overdracht vóór het hernoemen van de map: `docs/overdracht.md` heeft een paragraaf *Na het hernoemen* (Python-omgeving opnieuw, `.env`, controleren, GitHub-repo aanmaken) en beschrijft de interface van 0.31; CLAUDE.md legt uit waarom het package nog `cutter/` heet; BACKLOG 12f verwijst naar de stappen.

## [0.31.1] - 2026-11-05

### Gewijzigd

- Technische naam `commons-mineventory` in plaats van `commons-cutter` (backlog 12f, stap 1): de URL's in `.env.example` en de standaardwaarden in `cutter/config.py` (broncode, User-Agent), het npm-pakket, het sleeptype in de Bekeken-kolom, het pad in CLAUDE.md, README en het functioneel ontwerp (Toolforge-tool, repo, map). Het Python-package `cutter/` en de `cc-`-voorvoegsels blijven. De map hernoemen en de GitHub-repo aanmaken doet Olaf.

## [0.31.0] - 2026-11-05

### Gewijzigd

- De verouderde API-paden van vóór 0.29.0 werken nog tot 0.32.0; 0.31.0 werd de nieuwe naam (backlog 12e).
- **Nieuwe naam: Commons Mineventory** (besluit Olaf 5-11-2026), met de tagline *Detect objects in a Commons image. Find, cut out and describe them with AI.* / *Detecteer objecten in een Commons-afbeelding. Vind ze, snijd ze uit en beschrijf ze met AI.* De naam staat in de kop, de paginatitels, de teksten, de documentatie, de OpenAPI-titel, de User-Agent (`CommonsMineventory/0.1`), de volgcategorie (*Uploaded with Commons Mineventory*) en de projectpagina (`Commons:Commons Mineventory`). Map, repo, Toolforge-naam en package heten nog `commons-cutter`/`cutter`; backlog 12f.
- **Nieuw logo** (keuze Olaf): een afbeelding met twee gevonden objecten in stippelkaders, en ernaast een lijst: de inventaris. Het vervangt de schaar.
- *Selectie beschrijven* heet nu *Geselecteerde objecten beschrijven*, met een regel eronder die zegt wat de knop doet: alleen geselecteerde objecten zonder beschrijving tellen mee, hoeveel dat er zijn, en waarom de knop uit staat als ze allemaal al beschreven zijn (opnieuw beschrijven gaat per object in de vergroter).
- De uitkomst van *Dubbelingen samenvoegen* en *Geselecteerde objecten beschrijven* staat nu als melding onder die knoppen in plaats van bovenaan de pagina; vindt samenvoegen niets, dan staat er in rood dat er geen dubbelingen zijn (eerst: "0 dubbelingen samengevoegd"), anders in groen hoeveel er zijn samengevoegd; met een X om de melding weg te klikken.
- In de objectenlijst staat bij een object met een beschrijving *beschreven* (met uitleg bij aanwijzen), zodat je ziet welke *Geselecteerde objecten beschrijven* overslaat.
- Het (i) over bewaartermijnen staat niet meer naast de telling van de geselecteerde objecten (daar leek het over de selectie te gaan), maar onder de knoppen voor opslaan, zip en Commons, met het woord *Bewaartermijnen* erbij.

## [0.30.1] - 2026-11-05

### Toegevoegd

- `docs/overdracht.md`: de stand van zaken, de interface in het kort, afspraken die je niet uit de code haalt, werkwijze en valkuilen (zoals testen op een dummy-server), en wat openstaat.

### Gewijzigd

- De verouderde API-paden van vóór 0.29.0 werken nog tot 0.31.0 (eerst stond er 0.30.0); backlog 12e.
- Documentatie bijgewerkt: README (wat de app nu doet), CLAUDE.md (overdracht, testen op een dummy-server, vormafspraken), BACKLOG.md (12d, 12e), functioneel ontwerp (status v0.8).
- *Wat staat hierop?*: de regel bij het bijschrift zegt nu dat het meegaat als je hieronder op *Beschrijf deze afbeelding* klikt.
- In de vergroter heet *De vorm laten vinden* nu *Transparante PNG maken (omtrek vinden met AI, US$ 0,0025)*, met een tooltip met uitleg.
- Een bijschrift dat je in de vergroter typt maar niet opslaat, wordt toch opgeslagen als je naar een ander tabblad gaat (zoals *Wat staat hierop?*, dat het dan meteen gebruikt), naar een ander object gaat of de vergroter sluit.
- De uitleg bij *Bijschrift* in de vergroter staat nu als grijze tekst in het lege invoerveld: "Hint voor de AI: met een bijschrift geeft ‘Wat staat hierop?’ een betere beschrijving." Het (i)-knopje erbij is weg.
- *Aanwijzen of tekenen* geeft nu ook een uitkomst in het paneel, net als *Zoeken*: welk object er gevonden is, dat je op een bekend object klikte (gratis), of dat er op die plek niets is, met een tip; en bij een rechthoek onder welke naam hij is toegevoegd.

## [0.30.0] - 2026-11-05

### Gewijzigd

- *Naar de prullenbak* in de vergroter laat de vergroter open: hij gaat door naar het volgende object van de lijst (aan het eind het vorige), en sluit alleen als er geen objecten meer zijn. Ongedaan maken in de melding blijft.
- Met *Aanwijzen* of *Tekenen* aan blijft de muis een vizier (kruisje), ook boven een kader; eerder werd het daar een handje. Ook de tooltip met de naam van een object blijft dan weg.
- De vergroter heeft in de kop *Vorige* en *Volgende* (ook met ← en →, behalve tijdens het typen), met "3 / 31" ertussen: in de volgorde van de lijst *Wat je vond*; de lijst en het beeld lopen mee. De titel toont de naam zoals de lijst (*boom 2*).
- *Aanwijzen*: een klik telt alleen als een bestaand object als hij op de vorm (het masker) van dat object valt, niet al binnen zijn kader. Een vogel vóór het kader van een boom is nu aan te wijzen. Objecten zonder masker (regio's van Commons, getekende rechthoeken) houden een klik niet meer tegen. De kosten worden daarom bij elke klik vooraf gemeld.
- Meldingen over één object (zoals *Naar de prullenbak verplaatst* met *Ongedaan maken*) passen op één compacte regel: een kleine miniatuur, de naam, de tekst en de acties; de beschrijving staat in de tooltip.
- *Naar de prullenbak* (in de app en op de pagina Objecten) heeft in de bevestiging een vinkje *Niet meer vragen*: met dat vinkje en *Naar de prullenbak* vraagt de app het in dit tabblad niet meer, tot je het sluit (sessionStorage). Ongedaan maken in de melding erna blijft.
- Na een zoekactie staat de uitkomst in het blok waar je zocht (Zoeken, AI-suggesties of Uit Commons): hoeveel objecten er gevonden zijn voor welke term, hoeveel uitgesloten met MIN, of dat er niets is gevonden, met een tip. Eerder kwam dat alleen als melding bovenaan de pagina.
- *Selectie beschrijven* (met het bedrag op de knop) en *Dubbelingen samenvoegen* staan nu onderaan *Wat je vond*, boven *Selectie opslaan*: ze werken op wat je gevonden en aangevinkt hebt. Het blok *Bulk-operaties* in *Objecten zoeken* is vervallen.

### Toegevoegd

- De beschrijving van de hele afbeelding (*AI-suggesties voor deze afbeelding*) is met de hand aan te passen, net als bij een uitsnede: een potloodje achter het Nederlands, het Engels en de gelezen tekst, met Opslaan en Annuleren, *Met de hand aangepast*, *Terug naar de AI-tekst* en *Ongedaan maken*. API: `PATCH …/pagina/{n}/inventaris`.
- *Eerdere beschrijvingen* van de afbeelding: elke versie, van de AI of met de hand, blijft bewaard (hooguit 30), ook bij *Beschrijving opnieuw* of *Verwijderen*; met *Deze gebruiken* terug te zetten (de zoektermen blijven) en per versie te verwijderen. API: `GET …/inventaris/geschiedenis`, `PUT …/inventaris/beschrijving`, `DELETE …/inventaris/geschiedenis/{versie}`.
- Bij de zoektermen naast *alle aan · alle uit* ook *omkeren*.
- De privacyverklaring ook in het Engels (`docs/privacy.en.md`): `/privacy` volgt de taal van de interface, met een link naar de andere taal. Beide bijgewerkt met wat er nu in de browser bewaard wordt (*Bekeken*, *Opzij gezet*, ingeschoven kolommen, uitgezette zoektermen).
- Tweetaligheid nagelopen: in de Engelse interface verschijnt geen Nederlandse tekst van de server meer. Foutmeldingen: in het Nederlands de eigen melding van de server, in het Engels de vertaling van de foutcode (alle codes vertaald, ook de algemene per HTTP-status). Niet-ondersteunde bestanden (`niet_ondersteund_code`), de rechtenredenen in Metadata (`reden_codes`), de controle vooraf (`detail` per waarschuwing) en de kolom Term in het verbruik (bij AI-beschrijvingen het model en het deel) worden nu vertaald.
- De namen bij de kaders in het beeld (en in de tooltip) krijgen dezelfde nummers als in de lijst als een naam vaker voorkomt: *man 1*, *man 2*, … (`numberedNames` in state.js).
- *Eerdere beschrijvingen* (van de afbeelding en van een uitsnede): de hele tekst als popup bij aanwijzen, en *Hele tekst tonen* (klik op de versie) klapt hem uit. Het kopje van elke versie is kleiner.

## [0.29.0] - 2026-11-05

### Toegevoegd

- Bevestigingen kunnen opmaak hebben: alinea's, een vet kopje en een lijst. De bevestigingen van *Bekeken* gebruiken dat: de vraag, dan *Wat blijft*, *Terug naar de afbeelding* en *Echt verwijderen*, met links naar de pagina Objecten en de Prullenbak. De M-id is een link: een klik opent de afbeelding weer (in de invoerbalk) en zet hem terug bij Bekeken.
- *Bekeken*: een gebied **Opzij gezet** onderaan de kolom, met een kop die in- en uitklapt (onthouden). Het prullenbakje bij een afbeelding zet die daar neer, zonder bevestiging; slepen kan ook, in beide richtingen. In *Opzij gezet* zet de pijl omhoog een afbeelding terug en haalt het prullenbakje hem helemaal van de lijst (na een bevestiging). Een afbeelding weer openen zet hem ook terug. De lijst houdt nu 50 afbeeldingen bij. De link onderaan heet *Hele lijst wissen (Bekeken én Opzij gezet)*, zodat duidelijk is dat beide gebieden leeg gaan.
- Uitleg van het verschil tussen een *object* (wat er gevonden is, alleen gegevens) en een *uitsnede* (het beeldbestand dat je ervan opslaat): in het infovenster van *Wat je vond*, bij de bewaartermijnen, op de pagina Objecten, in de bevestigingen van de prullenbak en van de lijst *Bekeken*, en in README, functioneel ontwerp (*Begrippen*) en docs/api.md. De bevestiging bij *Bekeken* zegt ook hoe je terugkomt bij de afbeelding (de M-id in de invoerbalk, of via de pagina Objecten).
- Een afbeelding uit de lijst *Bekeken* halen (of de lijst wissen) vraagt eerst een bevestiging, met de uitleg dat alleen de vermelding verdwijnt: afbeelding, objecten, beschrijvingen en uitsneden blijven, en objecten verwijder je via de Prullenbak.
- Elke kolom (Bekeken, Beeld, Objecten zoeken, Wat je vond) schuift met de pijl in zijn kop weg tot een smalle strook met de naam (en het aantal); een klik op de strook opent hem weer. Het beeld neemt de vrije ruimte; is het beeld ingeschoven, dan de eerste open kolom. Onthouden in de browser; op smalle schermen niet van toepassing.
- Een kolom *Bekeken* helemaal links: de afbeeldingen die je in deze browser opende, met miniatuur, de huidige gemarkeerd. De breedte is te verslepen. *Laatst bezocht* staat daardoor niet meer boven de objecten. Op smalle schermen is de kolom verborgen.
- *AI-suggesties voor deze afbeelding*: beschrijving en zoektermen elk apart opnieuw vragen of verwijderen. De eerste vraag blijft één aanroep voor beide (het goedkoopst). Daarna staat onder de beschrijving *Beschrijving opnieuw* en onder de zoektermen *Zoektermen opnieuw*, elk met het bedrag: één nieuwe, betaalde aanroep voor alleen dat deel, het andere deel (en je vinkjes) blijft staan. *Verwijderen* per deel is gratis en vraagt eerst om bevestiging; gevonden objecten blijven. Dit vervangt *Opnieuw om suggesties vragen*. API: `POST …/inventaris` met `deel`, `DELETE …/inventaris?deel=`.
- *AI-suggesties voor deze afbeelding*: een vinkje in elke zoekterm om die wel of niet mee te nemen met *Alle objecten detecteren* (dan *Gekozen termen detecteren (n)*, met het bedrag voor alleen die termen), met *alle aan* en *alle uit*. Uitgezette termen worden doorgestreept; de keuze wordt per bestand en pagina in de browser onthouden.

### Gewijzigd

- De API is helemaal RESTful (docs/api.md, *Afspraken* en *Verouderde paden*): een object heet `…/pagina/{n}/objecten/{object_id}` (meervoud, zoals de lijst); een eerdere beschrijving terugzetten is `PUT …/beschrijving` met `{"versie"}`; één versie verwijderen `DELETE …/beschrijving/geschiedenis/{versie}`; dubbelingen samenvoegen `POST …/pagina/{n}/samenvoegingen`; de controle vooraf een `GET …/commons/controle?objecten=pagina:id,…`; een deel van het paginaoverzicht `POST` of `DELETE …/inventaris/{deel}`. De oude paden werken nog tot 0.30.0, met `Deprecation: true` en een `Link` naar het nieuwe pad, en staan in OpenAPI als `deprecated`.
- Nieuwe volgorde van de kolommen, van links naar rechts in de volgorde van het werk, zoals in de Delpher Uitsnijder: beeld, *Objecten zoeken* (het detectiepaneel, eerst *Zoeken en bewaren*), *Wat je vond* (de objecten). De knoppen *Selectie opslaan*, *Downloaden (zip)* en *Naar Commons…* staan nu onder de objecten en blijven in beeld als de lijst scrollt. Op een telefoon: tabbladen Beeld, Detectie, Objecten.
- *AI-suggesties voor deze afbeelding* in de volgorde van het werk: eerst de vraag (met uitleg en bedrag), dan het antwoord van de AI in een eigen kader, dan de zoektermen met *Alle objecten detecteren*, dan wat er gevonden is, en als laatste *Opnieuw om suggesties vragen* met zijn uitleg. Uitleg is in het hele detectiepaneel kleiner en grijs (`cc-uitleg`), zodat die niet meer op een AI-resultaat lijkt.
- *AI-suggesties voor deze afbeelding*: boven de zoektermen staat nu dat je met een zoekterm laat zien waar dat op de afbeelding staat (met de kosten per term), en *Alle objecten detecteren* staat direct achter de zoektermen in plaats van eronder.

### Opgelost

- Boven het beeld stonden twee percentages naast elkaar (de huidige zoom en de knop *100%*). De knop heet nu *Ware grootte*; het percentage is de huidige zoom.
- *Maskers*, *Kaders* en *Namen* boven het beeld zijn uitgeschakeld zolang er geen objecten zijn.
- Een knop die breder is dan een smalle kolom (zoals *Alle objecten detecteren* met het bedrag) werd aan beide kanten afgekapt; de tekst loopt nu door op een volgende regel.

## [0.28.0] - 2026-11-04

### Toegevoegd

- Metadata: het werk op Wikidata zoals `{{Artwork}}` het op Commons toont. Het item komt uit `|wikidata=` in het sjabloon of, als dat er niet is, uit *digitale weergave van* (P6243) in de gestructureerde gegevens van het bestand, zoals `{{Artwork}}` zelf doet. Getoond worden titel, maker, datum, beschrijving, soort object, onderdeel van, beeldt af, materiaal, afmetingen, collectie, inventarisnummer, locatie, plaats van vervaardiging en links. Datum en maker uit dat item gaan nu ook mee in het Commons-concept als het bestand zelf ze niet heeft.
- Een kop boven de linker- en de rechterkolom: *Wat je vond* en *Zoeken en bewaren*, met één regel uitleg en een (i)-venster dat opsomt wat je in die kolom kunt doen (`ColumnHeader.vue`).
- Een tagline in de kop van de pagina: "Objecten vinden, uitsnijden en beschrijven" (Engels: "Find, cut out and describe objects"), vóór "werkt met Wikimedia Commons"; ook als beschrijving van de pagina (`<meta name="description">`).
- Functioneel ontwerp 9.7 (voorstel, nog niet gebouwd): *beeldt af* en caption voor de hele afbeelding, in een eigen venster; backlogpunt 15b.

### Gewijzigd

- *Selectie beschrijven* is uitgeschakeld zolang er geen aangevinkte objecten zonder beschrijving zijn, en toont hoeveel het er zijn; *Dubbelingen samenvoegen* is uitgeschakeld bij minder dan twee objecten. Een korte regel zegt wat je eerst moet doen.

### Verwijderd

- De knop *Slim detecteren* in *Bulk-operaties*: eerst AI-suggesties vragen en dan *Alle objecten detecteren* doet hetzelfde.
- De knop *Alles detecteren* in *Bulk-operaties*: *Alle objecten detecteren* bij de AI-suggesties doet hetzelfde, met termen die bij de afbeelding passen in plaats van een vaste lijst. In de API blijft `modus: "alles"` bestaan.

## [0.27.2] - 2026-11-04

### Opgelost

- De opruimtaak (`flask --app app opruimen --echt`) schreef `objecten.json` zonder het slot van de app. Als je op hetzelfde moment in de app iets op die pagina wijzigde, kon die wijziging verloren gaan. De app en de opruimtaak delen nu één slot dat ook tussen processen werkt (`cutter/slot.py`, een slot op `uitvoer/.slot`; ook voor meerdere workers op Toolforge). Alleen tellen (zonder `--echt`) wacht niet op het slot.

## [0.27.1] - 2026-11-04

### Toegevoegd

- *Eerdere beschrijvingen*: een prullenbakje per versie om die (na bevestiging) te verwijderen. Een AI-antwoord dat nog in de cache staat, blijft voor dit object weg; de cache zelf blijft. API: `DELETE …/beschrijving/geschiedenis?versie=…`.

### Opgelost

- De knop *Deze gebruiken* in *Eerdere beschrijvingen* werd bij een lange tekst afgekapt; de knoppen houden nu hun volle breedte.

## [0.27.0] - 2026-11-04

### Toegevoegd

- *Eerdere beschrijvingen* is nu versiebeheer, voor AI-antwoorden én je eigen aanpassingen: elke keer dat je een tekst met de hand wijzigt (onderwerp, naam, beschrijving, tekst in of rond het beeld; ook in de lightbox en op het tabblad Commons-concept), gaat de versie zoals die was eerst naar de geschiedenis. Elke versie heeft een eigen tijd (`bewerkt_op` voor een aanpassing, tot op de milliseconde) en is met *Deze gebruiken* terug te zetten. De lijst toont "met de hand aangepast op …" en ook de tekst in en rond het beeld. Een wijziging die niets verandert, maakt geen nieuwe versie. API: de geschiedenis geeft per versie `versie`; terugzetten met `{"versie": …}`.
- `{{Art Photo}}` wordt overgenomen als `{{Art Photo}}` (viel terug op `{{Information}}`): kunstenaar, plaats, fotograaf, fotodatum en beide licenties gaan mee, de beschrijving van de hele foto niet; de titel wordt de caption van de uitsnede.

### Gewijzigd

- Eén regel voor "hetzelfde beeld": *Alles detecteren*, *Dubbelingen samenvoegen* en het opslaan gebruiken nu allemaal `same_picture` (ook een kleiner kader dat bijna helemaal in een groter ligt); regio's van Commons worden nooit samengevoegd. *Alles detecteren* gebruikte eerder alleen de overlap (IoU).
- Eén functie haalt labels en beschrijvingen van Wikidata op (`_wikidata_entities`), in plaats van drie bijna gelijke lussen; de verzoeken zelf zijn ongewijzigd.

## [0.26.0] - 2026-11-04

Backlog 12c: de open punten uit de code-review.

### Beveiliging

- Budget: een betaalde aanroep boekt zijn kosten vooraf en houdt die vast zolang hij loopt (`Verbruik.reservation`), zodat gelijktijdige vragen samen de daglimiet of het dagbudget niet meer kunnen overschrijden. SAM-aanroepen geven nu ook hun prijs mee aan de controle (het budget werd eerder pas achteraf bewaakt). Hooguit 20 zoektermen per opdracht (`too_many_terms`).
- Op een server (niet in debug-modus) zijn het verbruikslog (met gebruikersnamen) en het legen van de hele prullenbak alleen voor ingelogde gebruikers op de toegangslijst, tot OAuth de gebruikers scheidt. Lokaal verandert er niets.

### Opgelost

- Foute invoer geeft een nette 400 in plaats van een 500: NaN of oneindig in een punt, rechthoek of minscore, een punt zonder x of y, een lijst id's die geen lijst van teksten is, een verkeerd object bij het legen van de prullenbak.
- Vreemde gegevens van Commons worden overgeslagen in plaats van een fout te geven: een regio als `1.2.3` of `nan`, een bestandsnotitie met `dimx=nan`.
- `objecten.json` en `bestand.json` worden atomisch geschreven (eerst een tijdelijk bestand): een crash laat nooit een half bestand achter.
- Zoeken op Wikidata: een laat antwoord op een oudere vraag overschrijft geen nieuwer resultaat meer, en een lopende zoekopdracht stopt als het venster sluit of een ander object opent.
- Bij het sluiten van de vergroter stoppen alle timers, en de viewer kijkt niet meer naar de grootte van een element dat weg is.
- Pagina *Objecten*: een gekozen bron of bestand zonder objecten meer (alles naar de prullenbak) valt uit de keuze; de lijst liep daardoor vast.

### Gewijzigd

- Sneller: het grotere beeld van *wat de AI ziet* (lightbox) wordt één keer gemaakt en daarna uit de cache gehaald; het opzoeken van eerdere beschrijvingen doorzoekt de hele cache hooguit eens per minuut; het verbruikslog wordt alleen opnieuw gelezen als het veranderd is.
- Minder dubbele code: één Wikidata-zoeker voor alle zoekvelden (`frontend/wikidata.js`), één hulp voor de hoogte van tekstvakken (`frontend/autosize.js`), één onderdeel voor *opgeslagen, nog … dagen* (`SavedLabel.vue`), de prijs van een SAM-aanroep op één plek (van de server, `sam_usd`), één functie voor de tekst van een modelantwoord.
- Toegankelijkheid: de knoppen per object en per bezocht bestand noemen het object of bestand in hun naam, de huidige pagina heeft `aria-current="page"`, de tabbladen op de telefoon werken met de pijltjestoetsen, Home en End, en de kolommen zijn gekoppeld aan hun tabblad; de knop + bij de categorieën heeft een naam.

## [0.25.0] - 2026-11-04

Uit een kritische review van code en documentatie (4-11-2026).

### Beveiliging

- Zonder `FLASK_SECRET_KEY` gebruikt de app een willekeurige sleutel per proces in plaats van een vaste, en een sessiecookie telt (tot OAuth) niet meer als login. Wie de vaste sleutel kende, kon eerder een cookie met een gebruikersnaam ondertekenen en betaalde aanroepen doen.
- CSRF: verzoeken die iets veranderen of geld kosten (POST, PATCH, DELETE) komen alleen nog van de eigen pagina's van de app (Origin en Sec-Fetch-Site) en moeten JSON zijn. Een andere website kon de browser eerder een betaalde vraag laten doen (code `cross_site`, 403; `not_json`, 415).
- Wikitekst-injectie: vrije tekst in het Commons-concept (AI-teksten, captions, beschrijving, inscripties) staat er nu letterlijk in, met de wikitekens als HTML-entiteit. Tekst als `}}`, `[[Category:…]]`, `{{subst:…}}`, `~~~~` of `__NOINDEX__` kan geen sjabloon, categorie of handtekening meer toevoegen. Sjablonen uit het origineel (zoals `{{Creator:…}}`) blijven werken. Categorienamen worden gecontroleerd.
- De configuratie in de pagina escapet `<`, `>` en `&`, zodat tekst uit de URL het script niet kan afsluiten. Taallinks geven geen Flask-interne parameters (`_external` …) door.
- De opschoner van de Commons-weergave laat geen `position`, `z-index` of `transform` meer door (geen elementen over de app heen) en ziet CSS-escapes.
- Prompt-injectie: de tekst die het paginaoverzicht las, kan de markeringen van zijn eigen blok niet meer bevatten; elk tekstveld van een AI-antwoord is hooguit 4000 tekens.
- Strengere controle van een concept-PATCH (datum, maker, gekozen, talen van caption en beschrijving, `bron`) en van de M-id bij definitief verwijderen.

### Opgelost

- Commons-concept: een wijziging die nog opgeslagen moest worden, kon bij snel wisselen van object op het nieuwe object terechtkomen; nu gaat die naar het juiste object, en herladen gooit geen niet-opgeslagen wijziging meer weg. Dezelfde wijziging wordt niet meer twee keer verstuurd.
- Na Broncode → Weergave stonden de potloodjes en *[bewerken]* er niet meer.
- *Ongedaan maken* na *Naar de prullenbak* zette het object terug in het bestand dat op dat moment open was, niet in het eigen bestand.
- Het paginaoverzicht van een pagina die je net verliet, kon op de nieuwe pagina verschijnen.
- De vergroter wist bij een ander object ook de zoekopdracht en foutmelding van het vorige.

### Verwijderd

- Ongebruikte vertalingen, CSS-regels en code (onder meer een dubbele regel en de Wikidata-beschrijving van het oude formulier).

### Gewijzigd

- Documentatie bijgewerkt tot 0.24.2: README (functies), CLAUDE.md (stand, techniek, beheerpaneel), BACKLOG (nummering, gedane punten, open punten uit de review), functioneel ontwerp, privacyverklaring (wat naar Meta en Wikidata gaat), `.env.example` en de OpenAPI-beschrijving (bodies zoals de code ze leest).

## [0.24.2] - 2026-11-04

### Gewijzigd

- Lightbox: het tekstvak bij *Aanpassen* is zo hoog als de tekst die erin staat (een korte tekst geeft een laag vak), en hooguit zo hoog als het venster; een lange tekst scrolt.

## [0.24.1] - 2026-11-04

### Gewijzigd

- Commons-concept: het potloodje bij *Inscriptions* opent nu een venster op hetzelfde tabblad om *Tekst in het beeld* en *Tekst rond het beeld* te bewerken, in plaats van naar *Wat staat hierop?* te springen. De tekst wordt bij de beschrijving van het object opgeslagen, dus beide tabbladen tonen dezelfde tekst.

## [0.24.0] - 2026-11-04

### Gewijzigd

- Commons-concept, nu net als een bestandspagina op Commons: twee tabbladen, *Bestandsinformatie* en *Gestructureerde gegevens*. Op *Bestandsinformatie* staat bovenaan het kader *Captions* met *Bewerken* rechts, dan de weergave met *[bewerken]* achter de kop Summary (beschrijving, datum en maker in één venster) en bij Licensing de opmerking *van het origineel*; de potloodjes per rij blijven. Daaronder de categorieën. Op *Gestructureerde gegevens* staan de uitspraken, met 'beeldt af' (P180) bovenaan en bewerkbaar, ook als er nog geen item is: zoals op Commons met het zoekveld *Zoek om items toe te voegen*. Op *Gestructureerde gegevens* heeft elke uitspraak die van het origineel komt (auteursrechtenstatus, licentie, maker, datum van creatie, collectie) rechts *Bewerken*, zoals op Commons: je past alleen de waarden aan (een Wikidata-item via zoeken, een datum als 1708, 1708-02 of 1708-02-28, bij de maker ook 'onbekend'), haalt er een weg of voegt er een toe; de kwalificaties van het origineel blijven, nieuwe kwalificaties of bronnen kunnen niet. De feiten van het bestand zelf (type, MIME-type, checksum, grootte, afmetingen) zijn niet te bewerken. Een melding zegt dat verder verfijnen na de upload op Commons zelf gebeurt. API: veld `sdc_waarden` in het concept. Weergave en Broncode staan weer naast elkaar. *Formaat* (JPG/PNG) staat nu rechts naast de bestandsnaam. Per tabblad een knop *Broncode* om de wikitekst of JSON te zien (alleen lezen).

## [0.23.0] - 2026-11-04

### Toegevoegd

- Commons-concept: je bewerkt de uitsnede nu op de Commons-pagina zelf. In de weergave zoals Commons die toont, heeft elke rij die uit het concept komt een potloodje (Description, Title, Date, Author/Maker); dat opent een klein venster met *Opslaan* en *Annuleren*, waarna Commons de weergave opnieuw maakt. Het potloodje bij *Inscriptions* gaat naar *Wat staat hierop?*. De categorieën staan eronder in een balk zoals op Commons, met × om weg te halen, *Terugzetten* en een veld om er een toe te voegen. In de gestructureerde gegevens pas je de captions aan met een potloodje, haal je een 'beeldt af'-item weg met × en zoek je er een bij. Het aparte formulier (Caption, Beschrijving, Datum, Maker, Inscripties, Categorieën, Beeldt af) is weg; bovenaan staan nog Bestandsnaam, Formaat en de rechten. De broncode (wikitekst en JSON) blijft alleen-lezen. Rijen van de informatiesjablonen houden daarvoor hun id (`fileinfotpl_…`) in de opgeschoonde HTML.
- *Voorstellen voor 'beeldt af' (P180)*: het zoekveld geeft suggesties terwijl je typt (na twee letters en een korte pauze): Wikidata-items met Q-nummer en beschrijving. Kies er een en hij komt in *beeldt af* van het Commons-concept. Enter of *Zoeken* toont alle treffers als lijst. De suggesties staan compact (kleine letter, één regel per item), en zolang ze open zijn is er ruimte onder het blok, zodat ze onderaan de vergroter passen.
- Commons-concept: een blok *Inscripties* (na Datum en Maker) toont welke gelezen teksten als `{{Inscription}}` meegaan (type `text` en `caption`) en waar: in `inscriptions` of, bij `{{Information}}` en `{{Book}}`, als extra rij in `other fields`. Met een link naar het sjabloon en naar *Wat staat hierop?* om de tekst aan te passen.
- Staat de muis in het beeld op een object waarvan de rij in de objectenlijst buiten beeld staat, dan scrolt de lijst mee tot die rij zichtbaar is (alleen de lijst, niet de pagina; na een korte pauze, zodat de lijst niet springt als je de muis over het beeld beweegt).

## [0.22.1] - 2026-11-04

### Gewijzigd

- *Wat staat hierop?*: in plaats van één knop *Tekst aanpassen* heeft elk veld een eigen potloodje, achter de tekst: Onderwerp (nl en en samen), Naam, Beschrijving (nl en en samen), Tekst in het beeld en Tekst rond het beeld. Het veld wordt ter plekke bewerkbaar, met *Opslaan* en *Annuleren* (Esc). *Naam* is nu ook met de hand aan te passen (ook via de API). Het tekstvak is meteen even hoog als de tekst, en heeft bij één veld geen extra label. *Ongedaan maken*, *Terug naar de AI-tekst* en *Beschrijving wissen* blijven.
- Het linkje onder het voorbeeld heet nu *groot bekijken, tekst controleren en aanpassen*.
- *Voorstellen voor 'beeldt af' (P180)*: de kop linkt naar P180 op Wikidata, en er is een zoekveld om zelf naar Wikidata-items te zoeken (gratis, alleen lezen). Een gevonden item voeg je met + toe aan *beeldt af* in het Commons-concept. Het blok staat er nu ook als de AI geen voorstellen gaf.

## [0.22.0] - 2026-11-04

### Toegevoegd

- Commons-concept: *Tekst in het beeld* en *Tekst rond het beeld* gaan mee naar Commons in `inscriptions`, met het sjabloon `{{Inscription}}` (type `text` voor de tekst in de uitsnede, `caption` voor de tekst eromheen op het origineel), regelovergangen behouden. `{{Information}}` en `{{Book}}` hebben geen inscriptions-veld; daar wordt het een extra rij *Inscripties* in `other fields`.
- Lightbox: bij *Aanpassen* is het tekstvak bijna zo hoog als het venster en blijft het beeld even groot, zodat je de tekst ernaast kunt blijven lezen. Komt het grote beeld niet binnen, dan staat er een melding met *Opnieuw proberen* in plaats van een gebroken afbeelding.
- Vergroter: in de kop, op alle drie de tabbladen, "Uitsnede uit" met de naam van het origineel als link naar de bestandspagina op Commons.
- Hoofdviewer: een zoomschuif naast de knoppen − en +, van 2 tot 300%. De schuif is logaritmisch, zodat elke stap even groot voelt, ook bij een klein percentage.
- *Wat staat hierop?*: klik op het voorbeeld *wat de AI ziet* (of op *groot bekijken*) voor een lightbox met dat beeld in een veel grotere resolutie (tot 3000 pixels), passend in het venster, op 100%, of met een zoomschuif van 10 tot 400%. Net als in de hoofdviewer zoomt het scrollwiel rond de muis en verplaats je het beeld door te slepen. Beide teksten zijn daar ook met de hand aan te passen (*Aanpassen*, dan *Opslaan* of *Annuleren*), terwijl je naar het beeld kijkt; dat werkt als *Tekst aanpassen* in de vergroter, met *Ongedaan maken* en *Terug naar de AI-tekst*. Ernaast staan *Tekst in het beeld* en *Tekst rond het beeld* die de AI las, zodat je ze op het beeld kunt controleren. De API geeft de grotere versie met `invoer.jpg?max=` (tot 4000 pixels); het model zelf krijgt altijd 1024.

## [0.21.2] - 2026-11-04

### Gewijzigd

- Vergroter, tabblad *Uitsnede*: zolang de uitsnede nog gemaakt wordt (bij een groot origineel kan dat even duren), staat er een voortgangsbalk met de tekst "De uitsnede wordt gemaakt in volledige resolutie…". Ook na het wisselen tussen PNG en JPG. Lukt het laden niet, dan staat er een foutmelding in plaats van een leeg vak.

## [0.21.1] - 2026-11-04

### Gewijzigd

- "Opgeslagen, *nog … dagen*" staat in de objectenlijst en op de pagina *Objecten* in een kleinere letter; de resterende periode staat cursief en vet, zodat die opvalt (in de laatste week in oranje). Zo ook in de vergroter.
- Pagina *Objecten*: onder elk object staat "Uitsnede uit" met de naam van het origineel (zonder "File:"), als link naar de bestandspagina op Commons; zo ook in de prullenbak.

## [0.21.0] - 2026-11-04

### Toegevoegd

- Uitsneden uit originelen boven 100 megapixel (FO 5.4): de app leest zo'n origineel met libvips (`pyvips[binary]`, nieuw in `requirements.txt`) stuk voor stuk, in volledige resolutie, in plaats van het te weigeren. Detecteren gebeurt op de verkleinde versie, zoals altijd. JPEG, PNG en (meerpagina-)TIFF; 16-bits, grijs en CMYK worden 8-bits sRGB. De bestandsregel meldt het bij zo'n groot bestand. Gemeten: een uitsnede uit een JPEG van 150 megapixel piekt op ongeveer 100 MB in plaats van ongeveer 450 MB. Zonder pyvips weigert de app zulke bestanden, zoals voorheen.
- Bij elke opgeslagen uitsnede staat hoe lang die nog bewaard wordt: "opgeslagen, nog 23 dagen" in de objectenlijst en op de pagina *Objecten*, met de datum in de tooltip, en in de laatste week in oranje. In de vergroter staat het onder *Opgeslagen*, met de (i) over de bewaartermijnen. De API geeft het als `opgeslagen.verloopt` en `opgeslagen.laatst_gebruikt`, gerekend zoals de opruimtaak dat doet.

### Verwijderd

- Snel zoeken ook uit de code: de API-modus `categorie`, de twaalf vaste groepen in `cutter/prompts.py`, `snel_zoeken` in de paginaconfiguratie en de vertalingen `quick.*`. De AI-suggesties per afbeelding vervangen het (zie 0.11.0). `docs/api.md`, het FO, de OpenAPI-beschrijving en de backlog zijn bijgewerkt.

## [0.20.0] - 2026-11-04

### Gewijzigd

- Commons-concept, sjabloon van het origineel (besluiten van Olaf, `docs/artwork-velden.md`): een uitsnede is een detail van hetzelfde object. Wat over het object gaat, gaat mee: ook `object type`, `department`, `place of creation`, `place of discovery`, `notes`, en bij KB-prenten `publisher` en `place of publication`. Wat over het hele beeld of de maten gaat, niet: `dimensions`, `depicted people`, `depicted place`, `exhibition history`. Nieuw voor de uitsnede: `depicted part` (nl/en) en `inscriptions` (de tekst in beeld). Uit `other_fields` gaan de rijen over het object mee (bijv. *Binder/bindery*), die over het beeld niet. De velden staan in de volgorde van de documentatie.
- Aliassen uit de documentatie worden herkend (`year`, `publication date`, `technique`, `material`, `size`, `gallery`, `museum`, `id`, en bij `{{Artwork}}` en `{{Photograph}}` `location`), in de spelling van het origineel.
- `{{Map}}` wordt overgenomen zoals `{{Artwork}}`: kaartdatum, drukdatum, plaats, blad en schaal gaan mee, het middelpunt (`latitude`, `longitude`) en de legenda niet. `{{Photograph}}` houdt ook `camera coord`, `{{Book}}` ook `wikisource`.
- Categorieën: een uitsnede van een bestand uit *Media contributed by Koninklijke Bibliotheek* komt in *Cut-outs from media contributed by Koninklijke Bibliotheek*, een uitsnede uit *Media from Delpher* in *Cut-outs from media from Delpher*; de partnercategorie zelf gaat niet mee. Dat loopt via het partnersjabloon in `source`, met de bestaande parameter `category=`: `{{Koninklijke Bibliotheek|category=[[Category:Cut-outs from media contributed by Koninklijke Bibliotheek]]}}` (en zo ook `{{Delpher}}`). De vermelding van de partner blijft dus staan.

### Gewijzigd

- `docs/artwork-velden.md`: per veld van `{{Artwork}}`, `{{Photograph}}` en `{{Book}}` wat het Commons-concept nu doet en een voorstel (overnemen, opnieuw invullen of weglaten), met een steekproef van 596 KB-bestanden op Commons en de besluiten van Olaf.

## [0.19.0] - 2026-11-04

### Toegevoegd

- Op een telefoon (smaller dan 48rem, ongeveer 770 pixels) zijn de drie kolommen tabbladen: *Objecten*, *Beeld* en *Detectie* (FO 10.5), in een balk die bovenaan blijft staan. *Beeld* is het eerste. Op grotere schermen verandert er niets.

### Gewijzigd

- In de uitlegpopups kan tekst vet staan; in *Hoe lang wordt dit bewaard?* staan de termijnen, "geen archief" en "blijft altijd" vet.

## [0.18.0] - 2026-11-04

### Toegevoegd

- Opruimtaak voor de bewaartermijnen (FO 12.1): `flask --app app opruimen` telt wat weg zou gaan, `--echt` verwijdert het. Originelen en de Commons-cache na 7 dagen, niet-geüploade uitsneden en maskers na 30 dagen, detecties en beschrijvingen na 1 jaar, telkens vanaf het laatste gebruik. Het verbruikslog blijft altijd. De app zet bij elk lezen de toegangstijd van het bestand, zodat de termijn vanaf het laatste gebruik telt.
- De bewaartermijnen staan in de interface: een (i) met popup *Hoe lang wordt dit bewaard?* naast het aantal objecten boven *Selectie opslaan*, en op de pagina *Objecten* een regel dat opgeslagen uitsneden na 30 dagen zonder gebruik verdwijnen. De termijnen komen uit de configuratie (`bewaren` in de paginaconfiguratie).

### Gewijzigd

- *Bijsnijden in CropTool* staat niet meer in de vergroter: CropTool nam het kader uit de link niet over en toonde de hele afbeelding. In het detectiepaneel staat nu onderaan een uitklapblok **Bijsnijden in CropTool** (standaard ingeklapt, met uitleg en een info-popup), met een knop die het hele bestand in CropTool opent. Met het logo van CropTool2 (het Codex-icoon *cut*, dat CropTool2 zelf ook gebruikt). Alleen bij afbeeldingen van één pagina.

## [0.17.0] - 2026-11-04

### Toegevoegd

- Staat de muis op een kader in het beeld (of op een rij in de objectenlijst), dan krijgt die rij in de lijst een rand in de kleur van het kader: rood voor geselecteerd, blauw voor gevonden maar niet geselecteerd, en zo verder volgens de kleurenlegenda.

- Vergroter, tabblad *Uitsnede*: link **Bijsnijden in CropTool**, die CropTool opent met het kader van het object al geselecteerd (parameters `title`, `left`, `top`, `width`, `height` uit de README van CropTool). Alleen bij enkele afbeeldingen; bij PDF, DjVu en meerpagina-TIFF niet, omdat het kader daar in pixels van een gerenderde pagina staat.

- *Wat staat hierop?*: de knop *Beschrijf deze afbeelding* staat nu onder *AI-bijsturing*, zodat je eerst bijstuurt en dan vraagt.

## [0.16.0] - 2026-11-04

### Toegevoegd

- AI-suggesties voor deze afbeelding: Muse Spark leest nu ook de tekst in en onder de afbeelding (bijvoorbeeld het rijmpje onder een prent) en neemt die letterlijk over. Die staat onder de samenvatting. Het overzicht heeft versie 3 (veld `tekst`); een bestaand overzicht heeft dat veld niet, *Opnieuw om suggesties vragen* (betaald) haalt het op.
- *Wat staat hierop?*: de tekst die het overzicht in en onder de hele afbeelding las, gaat als context mee naar de beschrijving van elke uitsnede (bijvoorbeeld het rijmpje dat over het plaatje gaat). Muse Spark gebruikt hem om de uitsnede te benoemen en beschrijven, en om tekst in of rond de uitsnede beter te lezen. Een vraag met paginatekst is een andere vraag dan zonder (eigen cache); de beschrijving onthoudt of hij gebruikt is (`paginatekst`).

### Opgelost

- Een object aan- en uitvinken terwijl de muis op de rij in de lijst staat, maakte het masker in het beeld lichter: het object verloor zijn markering "onder de muis" en werd daardoor net als de andere objecten gedimd. De markeringen blijven nu staan, ook als het beeld na het antwoord van de server opnieuw wordt getekend.

## [0.15.0] - 2026-11-04

### Toegevoegd

- Detectiepaneel: naast elke kop (AI-suggesties, Uit Commons, Zoeken, Aanwijzen of tekenen, Bulk-operaties) een info-icoontje dat een popup met uitleg opent: wat het doet, wat het kost en waar je op let.

- Een klein Wikimedia Commons-logo rechts in de kopregel, met een link naar Commons (het logo komt uit Codex en staat in de app zelf; er wordt niets van Wikimedia geladen).

### Gewijzigd

- *Wat staat hierop?*: de uitleg bovenaan heeft een tweede alinea over *AI-bijsturing* (een aanwijzing of meer ruimte rond de uitsnede): je krijgt er een beter resultaat mee, en je kunt het ook meteen instellen, nog voor de eerste vraag.

## [0.14.1] - 2026-11-04

### Gewijzigd

- De bovenkant van de pagina is compacter: het invoerveld en het geopende bestand staan naast elkaar (op een smal scherm onder elkaar), met een kleinere miniatuur. Licentie, rechten en de gegevens van het bestand staan op één regel en *Metadata* is een kleine uitklapregel. Een lege meldingenlijst neemt geen ruimte meer in.

## [0.14.0] - 2026-11-04

### Toegevoegd

- Maskers zijn duidelijker zichtbaar (minder doorzichtig).
- Boven het beeld een uitklapblok *Kleurenlegenda* (standaard ingeklapt, alleen als *Kaders* aan staat, en alleen met de kleuren die op de pagina voorkomen): geselecteerd, gevonden maar niet geselecteerd, nieuw (uit de laatste zoekactie), regio die al op Commons staat, met de hand getekende rechthoek, uitgesloten, en dikker voor gekozen of onder de muis. De tooltip van een nieuw object zegt "nieuw".
- In de balk boven het beeld drie vinkjes, zoals in de Delpher Uitsnijder: **Maskers** (de vorm van elk object), **Kaders** (de rechthoeken; verborgen blijven ze aanklikbaar) en **Namen**. De keuze wordt in deze browser onthouden. **Namen** zet de naam van elk object boven zijn kader (de score staat in de tooltip), in de kleur van dat kader. Regio's van Commons hebben hun naam altijd.

### Gewijzigd

- Detectiepaneel: *AI-suggesties voor deze afbeelding* staat nu bovenaan, als eerste optie (boven *Uit Commons* en *Zoeken*); *Zoeken* is standaard ingeklapt. *Aanwijzen* en *Rechthoek tekenen* zijn samengevoegd tot één uitklapblok *Aanwijzen of tekenen* (standaard ingeklapt), met beide schakelaars onder elkaar.

## [0.13.2] - 2026-11-04

### Gewijzigd

- Alle uitklapblokken in de app (Codex *Accordion*: het detectiepaneel, de vergroter, de proefweergave, *Laatst bezocht*, …) klappen nu vloeiend open en dicht, eerst versnellend en dan afremmend (0,35 seconde), in plaats van in één keer; niet bij 'minder beweging' in het systeem (`frontend/accordion-motion.js`).
- *Wat staat hierop?*: het voorbeeld van wat de AI ziet vliegt nu boven alles uit naar *AI-bijsturing* en terug, tegelijk met het uit- en inklappen, zodat het onderweg niet wordt afgesneden.

## [0.13.1] - 2026-11-04

### Gewijzigd

- *Wat staat hierop?*: zodra *AI-bijsturing* openklapt, glijdt het voorbeeld van wat de AI ziet vloeiend mee naar dat blok (0,6 seconde, eerst versnellend en dan afremmend, niet bij 'minder beweging' in het systeem), naast de aanwijzing en de schuifregelaar; dichtklappen zet het weer bovenaan.

## [0.13.0] - 2026-11-04

### Gewijzigd

- *Wat staat hierop?* opnieuw ingedeeld, met één vaste volgorde voor de eerste en elke volgende vraag:
  1. rechts bovenaan de uitsnede zoals de AI hem ziet (rood kader, met de gekozen ruimte; ook vóór de eerste vraag); links het antwoord (of vooraf een korte uitleg wat je krijgt, met het bijschrift dat meegaat), met de acties voor dat antwoord op één regel: *Tekst aanpassen*, *Terug naar de AI-tekst*, *Ongedaan maken*, en rechts *Beschrijving wissen*;
  2. één knop om de AI te vragen, met de kosten: de eerste keer de hoofdknop *Beschrijf deze afbeelding*, daarna *Beschrijf deze afbeelding opnieuw*; ernaast staat welke bijsturing meegaat (bijv. "met ruimte 0% · aanwijzing …");
  3. ingeklapt: *AI-bijsturing* (aanwijzing, ruimte, wat de AI ziet; de kop toont de huidige keuze), *Eerdere beschrijvingen*, en *Model, kosten en kwaliteit*. Daartussen de suggesties voor *beeldt af*.

## [0.12.0] - 2026-11-04

### Toegevoegd

- *Wat staat hierop?*: blok **Eerdere beschrijvingen**: elke beschrijving die vervangen werd (door een nieuwe vraag, terugzetten of wissen) blijft bewaard, met tijd, model, aanwijzing en ruimte; ook antwoorden die nog in de cache staan komen erin, zodat varianten van vóór deze versie terug te halen zijn. *Deze gebruiken* zet er een terug (gratis); de huidige gaat dan de lijst in. API: `GET …/beschrijving/geschiedenis` en `POST …/beschrijving/terugzetten`.
- *Wat staat hierop?*: de aanwijzing en de ruimte rond de uitsnede staan samen in een eigen blok **AI-bijsturing**, met de voorbeeldweergave van wat de AI ziet en de knoppen om (opnieuw) te beschrijven (de losse miniatuur van de uitsnede naast de beschrijving is weg); de aanwijzing werkt nu ook bij de eerste vraag.
- *Wat staat hierop?*: *Tekst rond het beeld* en *Tekst in het beeld* zijn nu ook met de hand aan te passen (*Tekst aanpassen*) en met een prullenbakje te verwijderen, met *Ongedaan maken* en *Terug naar de AI-tekst*, net als onderwerp en beschrijving.
- *Wat staat hierop?*: rechts staat nu **wat de AI ziet**: de uitsnede (rood kader) met de ruimte eromheen die naar het model gaat, en een schuifregelaar *Ruimte rond de uitsnede* van 0 tot 100% (standaard 25%). Minder ruimte houdt andere dingen buiten beeld (zoals een tweede kind), meer ruimte geeft context (zoals tekst rond het beeld). Geldt voor de volgende vraag; de gekozen ruimte wordt bewaard bij de beschrijving. API: `marge` in de POST, en `GET …/beschrijving/invoer.jpg?marge=` (gratis).
- *Wat staat hierop?*: een veld *Aanwijzing voor de AI (optioneel)* bij *Beschrijf deze afbeelding opnieuw*, bijvoorbeeld "alleen de jongen". De aanwijzing gaat als aparte opdracht mee in de vraag aan het model (niet als bijschrift, niet naar Commons), wordt bewaard bij de beschrijving en staat in *Model, kosten en kwaliteit*. Een andere aanwijzing is een andere vraag, dus geen antwoord uit de cache. API: `aanwijzing` in de POST.

### Gewijzigd

- *Wat staat hierop?*: de knop *Opnieuw vragen* heet nu *Beschrijf deze afbeelding opnieuw* / *Describe this image again*.

## [0.11.1] - 2026-11-04

### Gewijzigd

- *Opnieuw vragen* bij de AI-suggesties heet nu *Opnieuw om suggesties vragen* / *Ask for suggestions again*. Bij één object in de prullenbak staat er "1 staat in de prullenbak" (was "1 are").

## [0.11.0] - 2026-11-04

### Toegevoegd

- *AI-suggesties voor deze afbeelding*: elke zoekterm toont hoeveel objecten ermee op de afbeelding staan, en een regel eronder telt het op ("12 objecten gevonden met 6 van de 11 zoektermen"), met hoeveel er in de prullenbak staan. De tooltip van een zoekterm noemt verwacht, gevonden en in de prullenbak. De pagina-API geeft daarvoor `prullenbak_termen`.
- Objectenlijst: naast *Alle* en *Geen* nu ook *Omkeren* (selecteert wat niet geselecteerd was, en andersom).

### Gewijzigd

- *Prullenbak legen*: de knop in de bevestiging heet nu *Definitief verwijderen* / *Delete permanently*; bij één object staat er geen "1 objecten" meer.
- De bron *met de hand getekend* heet nu *met de hand getekende rechthoek* / *hand-drawn rectangle* (facet, objectenlijst, vergroter).
- Pagina *Objecten*: de facetten (bron, bestand, alleen opgeslagen) staan in een kolom links, onder elkaar; de knop *Naar de prullenbak* onder elk object is een klein prullenbakje.

### Verwijderd

- Het blok *Snel zoeken* (vaste groepen zoals wapens, portretten, schepen) is weg uit het detectiepaneel: op Commons staan duizenden soorten objecten, dus een vaste lijst klopt voor veel afbeeldingen niet. De *AI-suggesties voor deze afbeelding* (nu standaard open) doen dit per afbeelding. De API-modus `categorie` en *Alles detecteren* blijven bestaan.

### Opgelost

- De tooltip in het beeld toont de AI-beschrijving nu in de taal van de interface (was altijd Nederlands).

## [0.10.0] - 2026-11-04

### Toegevoegd

- De objectenlijst staat op alfabet (bij gelijke naam van boven naar beneden). Namen die vaker voorkomen krijgen in de lijst een nummer (*house 1*, *house 2*); dat nummer staat alleen in de lijst, niet in de vergroter en niet in het Commons-concept.
- *AI-suggesties voor deze afbeelding*: knop **Alle objecten detecteren (n)** zoekt alle voorgestelde termen in één keer met de AI-beelddetectie (één aanroep per term, met de kosten op de knop en een bevestiging vooraf). Dat is nu de hoofdknop; *Opnieuw vragen* staat ernaast.
- Pagina *Objecten*: elk object heeft een knop *Naar de prullenbak*; een nieuw facet *Bestand*; en een knop die alles wat de filters tonen in één keer naar de prullenbak verplaatst (*Getoonde objecten naar de prullenbak (n)*, met bevestiging). Daarna een melding met *Ongedaan maken*.
- De melding *Naar de prullenbak verplaatst* toont welke uitsnede het was: een miniatuur, de naam en de beschrijving (of het bijschrift).

### Opgelost

- *Opnieuw vragen* bij de AI-suggesties stelde de vraag niet opnieuw: de app kreeg steeds het opgeslagen antwoord terug (gratis, maar zonder nieuwe suggesties). Nu stuurt de knop `opnieuw: true` en vraagt hij het model echt opnieuw, na de bevestiging van de kosten. De uitleg eronder zegt dat dat weer geld kost en dat het antwoord op het vorige kan lijken.

## [0.9.1] - 2026-11-04

### Gewijzigd

- README, CLAUDE.md, BACKLOG.md, het functioneel ontwerp (v0.5), `docs/api.md` en `docs/privacy.md` bijgewerkt naar de stand van 0.9.0: bewerkbare AI-teksten, AI-merkjes, de modelkeuze als code, de proefweergave zoals op Commons, de extra SDC en de regio op het origineel als voorbeeld.

## [0.9.0] - 2026-11-04

### Gewijzigd

- Het AI-merkje bij *AI-suggesties voor deze afbeelding* staat nu achter de samenvatting van het AI-paginaoverzicht, in plaats van in de kop.
- *AI-suggesties voor deze afbeelding*: het AI-paginaoverzicht geeft soort en samenvatting nu ook in het Engels (`paginasoort_en`, `samenvatting_en`), schuin onder het Nederlands, zoals in de vergroter. Een bestaand overzicht heeft alleen Nederlands; *Opnieuw vragen* haalt beide talen op (nieuwe cacheversie).
- *Wat staat hierop?*: ook bij *Soort* staat het AI-merkje, met uitleg dat soort en zekerheid door het taalmodel zijn gekozen en dat de zekerheid geen gemeten score is.

## [0.8.0] - 2026-11-04

### Toegevoegd

- *Wat staat hierop?*: een AI-merkje (robot, "AI") bij onderwerp en beschrijving. Een klik opent een venster dat uitlegt dat een taalmodel de tekst schreef, wat er mis kan gaan en wat je moet controleren; ook of de tekst met de hand is aangepast. Hetzelfde merkje staat bij *AI-suggesties voor deze afbeelding* zodra er een AI-paginaoverzicht is, en bij *Bron: AI-beelddetectie* op het tabblad *Uitsnede* (met uitleg over de detectie: vorm, label, de score van dit object, wat je controleert).

### Gewijzigd

- *Wat staat hierop?*: soort en zekerheid (bijv. *tekening*, *hoog*) staan nu in de taal van de interface (*drawing*, *high*). De waarschuwing zegt nu wat je moet controleren: het onderwerp en de beschrijving.
- *Wat staat hierop?*: het blok *Model en kosten* heet nu *Model, kosten en kwaliteit* en bevat de waarschuwing dat een taalmodel zich kan vergissen (stond onder de beschrijving).

## [0.7.0] - 2026-11-04

### Toegevoegd

- Commons-concept, *Proefweergave*: de wikitekst en de gestructureerde gegevens hebben elk een schakelaar **Weergave / Broncode**.
  - *Weergave* van de wikitekst: zo zet Commons hem op de bestandspagina. Commons maakt de HTML (`action=parse`, alleen lezen, gecachet); de server laat alleen veilige tags staan, zonder afbeeldingen, stijlen of scripts, zodat je browser niets van Wikimedia laadt. Alleen opgevraagd als de proefweergave open is. Nieuw: `GET …/object/{id}/commons/weergave`.
  - De gestructureerde gegevens van de uitsnede hebben nu ook *is een* (P31) *digitale afbeelding*, mediatype (P1163, `image/jpeg` of `image/png` naar het formaat), checksum (P4092, SHA-1), grootte (P3575, byte) en hoogte en breedte (P2048/P2049, pixel) van het bestand zoals het geüpload wordt. *Subject has role* (P2868, bijv. *collection highlight*) bij de collectie gaat niet meer mee: dat gaat over het origineel.
  - Nieuw blok *Regio op het origineel*: voorbeeld van wat het origineel bij het uploaden kan krijgen, per *beeldt af*-item een verklaring met de plaats van de uitsnede (P2677 `pct:…`), zoals de regio's op Commons; regio's die het origineel al heeft worden herkend. Dat is een bewerking van het origineel en komt pas in fase 2.
  - Inklapbare blokken (zoals de instelling bij *Collectie*) staan net als op Commons dicht, met *Uitklappen*/*Inklappen*. Het Wikidata-logo en het potloodje (*Edit this at Wikidata*) staan erbij als eigen icoontjes, met de link naar Wikidata; er wordt niets van Wikimedia geladen.
  - *Weergave* van de gestructureerde gegevens: zoals het tabblad *Gestructureerde gegevens* op Commons, met captions, *beeldt af* bovenaan, en elke eigenschap met zijn waarden en kwalificaties, met labels van Wikidata (`sdc_labels` in het concept).

## [0.6.2] - 2026-11-04

### Gewijzigd

- *Model en kosten*: "Contributor-variant" is een link naar Meta's uitleg van de Contributor-modus.
- Commons-concept: de links onder caption en beschrijving (*Bijschrift overnemen*, *Terug naar de AI-beeldbeschrijving*, …) zitten nu in één klein menu (⋯, *Invullen vanuit…*) naast het veld. *Ongedaan maken* staat er alleen direct na zo'n invulling, zolang je het veld nog niet zelf hebt aangepast.
- *Wat staat hierop?*: de knop *Opnieuw tonen (gratis)* is weg; *Terug naar de AI-tekst* doet dat nu, en een gewiste beschrijving komt bij opnieuw vragen gratis uit de cache.
- *Model en kosten* legt in gewone woorden uit waarom een model is gekozen (vrij van auteursrecht, rechtenlabel, …), in het Nederlands en het Engels, in plaats van "auteursrechtstatus Q19652 en een PD-sjabloon". De API geeft daarvoor `reden_code` en `labels` (plan) en `model_reden_code` en `model_reden_labels` (beschrijving).
- Alle knoppen in de app zijn nu blauw (Codex *progressive*), ook de snelzoek- en suggestieknoppen, zoom, de oog-knop en de infoknop. Alleen verwijderen blijft rood; de hoofdactie is gevuld blauw.

## [0.6.1] - 2026-11-04

### Gewijzigd

- In de regel over de live modus zijn de modelnamen links: SAM naar ai.meta.com/sam3, Muse Spark naar het modeloverzicht op dev.meta.ai.
- De knop *Opnieuw vragen* / *Ask again* bij de AI-suggesties is nu blauw en op normale grootte, zodat hij niet lijkt op de voorgestelde zoektermen.
- De uitleg bij *Aanwijzen* noemt Shift-slepen niet meer; tekenen heeft een eigen blok (*Rechthoek tekenen*).
- Het kopje *Suggesties voor deze pagina* heet nu "AI-suggesties voor deze afbeelding" / "AI suggestions for this image".

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
