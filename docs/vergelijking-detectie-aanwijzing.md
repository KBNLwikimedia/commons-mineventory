# Vergelijking: helpt de detectie-aanwijzing in de prompt?

Checklijst voor Olaf, 8 november 2026 (versie 0.33.8). **Dit kost geld** (een handvol vragen aan Muse Spark, elk een paar tienden van een cent); doe het op je eigen server in live-modus. Claude doet geen betaalde aanroepen.

## Wat er veranderd is

Sinds 0.33.8 krijgt de vraag *Wat staat hierop?* (in de vergroter en bij *Beschrijven* in de bulkacties) één zin mee over wat de app al weet van het object (FO 6.2, `detection_clue` in `cutter/beschrijving.py`):

- **een eigen naam** (met het potlood gegeven): *The user named this object: "…". Take this as what it shows, unless the image clearly shows something else.*
- **een regio uit Commons**: het label van die regio, als iets wat een mens heeft aangegeven;
- **anders de zoekterm van SAM, met de zekerheid**:
  - vanaf 50%: *An image detector (SAM) found this object when searching for "table" (certainty 75%). It is probably (part of) what "table" describes, or something related to it. Check what you see; if it is something else, describe what it really is.*
  - onder 50%: dezelfde zin, maar *it was unsure … It may be (part of) what "…" describes, or something else entirely; describe what you actually see.*
- **een eigen naam gaat altijd mee**, ook bij een groep (*The user named this group as a whole: …*), een zelf getekend kader en een klik (*Aanwijzen*);
- **zonder eigen naam geen zin** bij een groep (die noemt zijn leden al), een getekend kader en een klik; nooit bij een eigen prompt.

Tip: neem ook een **groep met een eigen naam** of een **getekend kader met een naam** mee in de vergelijking.

Je ziet de zin in de prompt: in de vergroter onder *AI-prompt* → *Tonen*, en in het venster van *Beschrijven* onder *Prompt voor de AI*. Het antwoord bewaart welke aanwijzing meeging (`detectie_aanwijzing`: `naam`, `commons`, `zoekterm` of leeg).

## Zo vergelijk je

Je hebt de oude antwoorden nodig om te vergelijken. Objecten die al vóór 0.33.8 beschreven zijn, hebben die: hun beschrijving is zonder aanwijzing gemaakt.

1. **Kies 6 tot 10 objecten** die al een beschrijving hebben van vóór vandaag, liefst gemengd:
   - 2 of 3 waar SAM het goed had en de beschrijving goed was;
   - 2 of 3 waar de beschrijving vaag of fout was (zoals *table 2*: een donkere doek zonder tafel erbij);
   - 1 of 2 waar **SAM het fout had** (bijv. een perzik gevonden als *lemon*): hier zie je of de AI de fout overneemt;
   - 1 met een **lage zekerheid** (onder 50%);
   - 1 die je zelf een **naam** hebt gegeven.
2. Noteer per object de zoekterm, de zekerheid en de huidige beschrijving (of laat die staan: hij komt onder *Eerdere beschrijvingen*).
3. Open het object in de vergroter, tabblad *Wat staat hierop?*. Kijk onder *AI-prompt* → *Tonen* of de zin klopt.
4. Klik **Beschrijf deze afbeelding opnieuw**, met **dezelfde** lengte en ruimte als het oude antwoord (zie *Eerdere beschrijvingen*), zodat alleen de aanwijzing verschilt.
5. Vergelijk het nieuwe antwoord met het oude (*Eerdere beschrijvingen*), en vul de tabel hieronder in.

| Object | Zoekterm (zekerheid) | Oud: onderwerp | Nieuw: onderwerp | Beter / gelijk / slechter | Nam de AI een fout van SAM over? |
| --- | --- | --- | --- | --- | --- |
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |

Let vooral op:

- Wordt het onderwerp **specifieker en juister** (*tafel met donker kleed* in plaats van *donkere stof*)?
- Worden de **Wikidata-suggesties** (beeldt af) beter?
- Bij een **foute zoekterm**: zegt de AI wat het echt is, of herhaalt hij de fout?
- Bij een **lage zekerheid**: is de AI terecht voorzichtig?

## Daarna

- **Beter**: laten zo. Eventueel de drempel van 50% (`CLUE_SURE`) bijstellen.
- **Neemt fouten over**: de zin voorzichtiger maken, of alleen meesturen boven een hogere zekerheid. Zeg het tegen Claude; het is één constante en twee zinnen.
- **Geen verschil of slechter**: weer weghalen (één regel in `_question`).
- Zet de uitkomst in backlog 12i en in FO 6.2.
