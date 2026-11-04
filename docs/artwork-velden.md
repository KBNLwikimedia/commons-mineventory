# Velden van {{Artwork}}, {{Photograph}} en {{Book}} in het Commons-concept

Status: **besloten door Olaf en gebouwd** (4-11-2026, app-versie 0.20.0). De besluiten staan onderaan. Hoort bij FO 9.3: "welke velden precies: bij de bouw vastleggen per sjabloon".

Gebruikt het origineel `{{Artwork}}`, `{{Photograph}}` of `{{Book}}`, dan krijgt de uitsnede hetzelfde sjabloon. Dit overzicht zegt per veld wat de app nu doet en wat ik voorstel. De velden komen uit de documentatie van de sjablonen op Commons.

## Het principe

Een uitsnede is een **detail van hetzelfde fysieke object**. Daaruit volgt:

- **Over het object als geheel** (wie het maakte, wanneer, waarvan, waar het is, herkomst): klopt ook voor het detail. **Overnemen.**
- **Over wat er te zien is, of hoe groot het is**: klopt niet voor het detail. **Opnieuw invullen** voor de uitsnede (caption, AI-beschrijving, tekst in beeld), of **weglaten**.
- **Over het bestand** (bron, licentie, andere versies): **eigen waarde** voor de uitsnede (`{{Extracted from}}`, de licentie van het origineel).

Legenda: **overnemen** = letterlijk van het origineel · **nieuw** = voor de uitsnede ingevuld · **weg** = niet in het concept · ✱ = verandert ten opzichte van nu.

## {{Artwork}}

| Veld (aliassen) | Nu | Voorstel | Waarom |
| --- | --- | --- | --- |
| `artist` / `author` | maker uit het concept | zo laten | Maker van het geheel = maker van het detail |
| `title` | caption van de uitsnede (nl/en) | zo laten | Het detail heeft geen eigen titel; de caption beschrijft het |
| `object type` | weg | ✱ **overnemen** | Een detail van een schilderij is nog steeds een schilderij |
| `description` | AI-beschrijving (nl/en) | zo laten | |
| `depicted people`, `depicted place` | weg | weg | Gaat over het hele beeld; *beeldt af* in de SDC zegt wat het detail toont |
| `depicted part` | weg | ✱ **nieuw**: het onderwerp van de uitsnede | Precies voor details bedoeld ("detail: wapen"). Vraag: in welke taal, of met `{{LangSwitch}}`? |
| `date` (`year`) | datum uit het concept | zo laten | |
| `medium` (`technique`, `material`) | overnemen | zo laten | |
| `dimensions` (`size`) | weg | weg | Maten van het hele object kloppen niet voor het detail |
| `institution` (`gallery`, `museum`) | overnemen | zo laten | |
| `department` (`location`) | weg | ✱ **overnemen** | Waar het object is, geldt ook voor het detail |
| `accession number` (`id`) | overnemen | zo laten | |
| `place of creation` | weg | ✱ **overnemen** | |
| `place of discovery` | weg | ✱ **overnemen** | |
| `object history` | overnemen | zo laten | |
| `exhibition history` | weg | ✱ **overnemen** | Het object is tentoongesteld, het detail dus ook. Vraag: of liever weg, omdat het lang kan zijn? |
| `credit line` | overnemen | zo laten | |
| `inscriptions` | weg | ✱ **nieuw**: *tekst in beeld* van de uitsnede, als die er is | De inscripties van het geheel horen niet bij elk detail; wat in de uitsnede staat wel |
| `notes` | weg | weg | Gaat meestal over het geheel |
| `references` | overnemen | zo laten | |
| `source` | `{{Extracted from}}` | zo laten | Besluit Olaf 3-11-2026 |
| `permission` | uit het concept | zo laten | |
| `other_versions` | leeg | zo laten (leeg) | `{{Extracted from}}` en `{{Image extracted}}` leggen de link al |
| `wikidata` | overnemen | **vraag** | Zie hieronder |
| `photographer` | overnemen | zo laten | De fotograaf van de reproductie |
| `other_fields`, `strict`, `demo`, `wikidata_cat` | weg | weg | Technisch of te vrij |

## {{Art Photo}}

Sinds 0.27.0 als `{{Art Photo}}` overgenomen, met dezelfde regel als `{{Artwork}}`: `artist`, `location` (plaats van het werk), `photographer`, `photo date`, `artwork license` en `photo license` gaan mee; `photo description` (de beschrijving van de hele foto) niet; de `title` wordt de caption van de uitsnede.

## {{Photograph}}

Zelfde principe. Afwijkend van {{Artwork}}:

| Veld | Nu | Voorstel |
| --- | --- | --- |
| `photographer` | maker uit het concept | zo laten |
| `camera coord` | weg | ✱ **overnemen**: de standplaats van de camera geldt ook voor een detail |
| `original description`, `original description info`, `biased` | weg | weg: de beschrijving van de bron gaat over het hele beeld |
| `depicted part` | bestaat niet in {{Photograph}} | onderwerp in `title` (zoals nu) |

## {{Book}}

Een uitsnede uit een boek is een detail van een pagina; het boek blijft het boek.

| Veld | Nu | Voorstel | Waarom |
| --- | --- | --- | --- |
| `Author`, `Translator`, `Editor`, `Illustrator` | overnemen (auteur als maker) | zo laten | |
| `Title`, `Subtitle`, `Series title`, `Volume`, `Edition` | overnemen | zo laten | De titel is die van het boek; caption en beschrijving zeggen wat het detail is |
| `Publisher`, `Printer`, `City`, `Language` | overnemen | zo laten | |
| `Publication date` (`Date`) | datum uit het concept, als `Date=` (een alias die {{Book}} kent) | zo laten, maar de spelling van het origineel volgen als dat `Publication date` gebruikt | |
| `Description` | AI-beschrijving | zo laten | |
| `Institution`, `Department`, `Accession number` | institution en accession number overnemen | ✱ ook `Department` | |
| `ISBN`, `LCCN`, `OCLC`, `References`, `Wikisource` | overnemen (`Wikisource` nu weg) | ✱ ook `Wikisource` | |
| `Image`, `Image page`, `Pageoverview`, `noimage`, `Homecat`, `Linkback` | weg | weg | Gaan over het meerpaginabestand of over sjabloonbouw |
| `Source`, `Permission`, `Other_versions` | als bij {{Artwork}} | zo laten | |
| `Wikidata` | overnemen | **vraag** | Zie hieronder |

## Ook ✱: aliassen

Nu herkent de app alleen de hoofdnamen. Een origineel met `|gallery=`, `|id=`, `|technique=`, `|year=`, `|location=` of `|size=` verliest die waarden. Voorstel: de aliassen uit de documentatie herkennen en in de uitsnede de spelling van het origineel houden (zoals nu al met hoofdletters).

## Steekproef: bestanden van de KB op Commons

Op 4-11-2026 bekeken: 596 bestanden uit [Category:Media contributed by Koninklijke Bibliotheek](https://commons.wikimedia.org/wiki/Category:Media_contributed_by_Koninklijke_Bibliotheek) (31.869 bestanden, geen subcategorieën), verspreid over het alfabet en de uploaddatum. Alleen gelezen, één verzoek per seconde.

**Welk sjabloon:** `{{Artwork}}` 439 (74%), `{{Book}}` 119 (20%), `{{Information}}` 33 (6%), `{{Map}}` 4 (1%). Geen `{{Photograph}}`.

**Ingevulde velden van `{{Artwork}}`** (veel uploads met GWToolset zetten alle velden neer, ook lege; hier alleen de gevulde): source 439, institution 392, title 390, date 390, description 336, artist 218, dimensions 214, accession number 194, medium 188, object type 188, author 137, **notes 134**, place of creation 106, references 95, **location 42**, photographer 41, wikidata 40, inscriptions 39, **publisher 38, place of publication 38**, depicted people 21, object history 9. In `other_fields`: *Binder/bindery* (36), *Persons related to this object* (3), *Depicted locations* (2).

**Ingevulde velden van `{{Book}}`**: description, source, references en `Homecat` bij alle 119; wikidata 108 (het boek komt dus meestal uit Wikidata), language 103, city 36; title, author en date maar 9 tot 10 keer. In `other_fields`: *Book dimensions*.

**Andere sjablonen** die vaak voorkomen: `{{Koninklijke Bibliotheek}}` (594, in `source`), `{{Institution:Koninklijke Bibliotheek}}` (513), `{{Creator:…}}`, `{{Size}}`, `{{Other date}}`, `{{Technique}}`, `{{PD-art}}` en `{{PD-old-…}}`. **`{{Extracted from}}` staat al op 82 en `{{Image extracted}}` op 20 bestanden**: er zijn al uitsneden uit KB-bestanden.

**Wat dat betekent voor het voorstel:**

- ✱ `location` is bij de KB de gebruikelijke spelling van `department`: herkennen (zie aliassen) en overnemen.
- ✱ `publisher` en `place of publication` staan bij KB-prenten in `{{Artwork}}`, al documenteert het sjabloon ze niet. Ze gaan over het object: **overnemen**.
- ✱ `other_fields` met `{{Information field}}`: velden over het object (*Binder/bindery*, *Book dimensions*) overnemen; *Depicted locations* en *Persons related to this object* weglaten (gaan over het hele beeld). Voorstel: overnemen, behalve namen met *depicted*.
- ✱ `notes` bevat bij de KB vooral context over de collectie ("This object is part of the collection of bookbindings…"). Dat geldt ook voor het detail. Zie vraag 5.
- ✱ `{{Map}}` komt weinig voor (4 van 596), maar KB-kaarten hebben eigen velden (`map date`, `print date`, `latitude`, `longitude`, `printer`, `publisher`). Voorstel: `{{Map}}` net zo behandelen als `{{Artwork}}`, met dezelfde regel (object: overnemen; beeld en maten: weg).
- `{{Koninklijke Bibliotheek}}` in `source` zet het bestand in *Media contributed by Koninklijke Bibliotheek*. Bij een uitsnede wordt `source` `{{Extracted from}}`, dus dat sjabloon (en die categorie) verdwijnt nu. Zie vraag 6.

## Vragen aan Olaf

1. **`wikidata` van het origineel overnemen?** Met `|wikidata=Q…` haalt {{Artwork}} titel, maker en datum uit het Wikidata-item van het **hele** kunstwerk, en kan die boven de eigen velden tonen. Voor een detail is dat half juist. Opties: (a) overnemen, zoals nu; (b) weglaten, en het werk alleen in de SDC noemen (*beeldt af* of *onderdeel van*); (c) overnemen, maar de `title` altijd zelf invullen. Mijn voorkeur: **(c)**.
2. **`depicted part`**: het onderwerp in het Engels, of tweetalig met `{{LangSwitch}}`? Mijn voorkeur: tweetalig, zoals `title`.
3. **`exhibition history`**: overnemen (het hoort bij het object) of weglaten (kan lang zijn)? Mijn voorkeur: overnemen.
4. **`inscriptions`** uit *tekst in beeld*: dat is AI-tekst. Alleen invullen als je die tekst in de vergroter hebt nagekeken, of altijd, met de AI-melding in de beschrijving? Mijn voorkeur: altijd, want de bewerkingssamenvatting zegt al dat een taalmodel heeft meegeholpen.

5. **`notes` overnemen?** Bij de KB is het meestal collectiecontext, die ook voor het detail geldt; bij andere instellingen kan het over het hele beeld gaan. Mijn voorkeur: overnemen.
6. **`{{Koninklijke Bibliotheek}}` (en vergelijkbare partnersjablonen) meenemen?** Dan komt de uitsnede ook in *Media contributed by Koninklijke Bibliotheek*. Opties: (a) meenemen, naast `{{Extracted from}}` in `source`; (b) weglaten, omdat de uitsnede niet door de KB is aangeleverd; (c) meenemen met `|category=` naar een eigen categorie, bijv. *Cut-outs from media contributed by Koninklijke Bibliotheek*. Mijn voorkeur: (a), want het is materiaal van de KB.

Na je antwoorden bouw ik de ✱-punten, met een test per sjabloon.

## Besluiten van Olaf (4-11-2026)

1. `wikidata`: **overnemen, met een eigen `title`** (de caption van de uitsnede).
2. `depicted part`: **tweetalig** nl/en, zoals `title`.
3. `exhibition history`: **weglaten**.
4. `inscriptions`: **altijd** de tekst in beeld van de uitsnede, als die er is. Sinds 0.22.0 met `{{Inscription|…|type=text}}`, en ook de tekst rond het beeld (`type=caption`, met de opmerking dat die buiten de uitsnede op het origineel staat). Bij `{{Information}}` en `{{Book}}`, die geen inscriptions-veld hebben, als rij *Inscripties* in `other fields` (besluit Olaf, 4-11-2026).
5. `notes`: **overnemen**.
6. Categorieën: staat het origineel in *Media contributed by Koninklijke Bibliotheek*, dan krijgt de uitsnede **Category:Cut-outs from media contributed by Koninklijke Bibliotheek**; staat het in *Media from Delpher*, dan **Category:Cut-outs from media from Delpher**. De categorie van het origineel zelf gaat niet mee. Altijd ook de volgcategorie *Uploaded with Commons Cutter*. Komt een beeld niet van de KB of Delpher, dan kiest de gebruiker zelf een categorie. Beide nieuwe categorieën bestaan nog niet op Commons; Olaf maakt ze aan, vóór de eerste echte upload.

De categorie loopt via het partnersjabloon (besluit Olaf, 4-11-2026): `{{Koninklijke Bibliotheek}}` en `{{Delpher}}` hebben al een parameter `category=`. De uitsnede krijgt in `source` naast `{{Extracted from}}` bijvoorbeeld `{{Koninklijke Bibliotheek|category=[[Category:Cut-outs from media contributed by Koninklijke Bibliotheek]]}}`. Zo blijft de vermelding van de KB staan en komt de uitsnede in de eigen categorie. De sjablonen zelf hoeven niet te veranderen. Vinkt de gebruiker de cut-out-categorie uit, dan gaat ook het partnersjabloon niet mee, omdat dat anders de categorie van het origineel zou toevoegen.
