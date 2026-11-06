# Ontwerp: het tabblad *Wat staat hierop?* opnieuw indelen

Voorstel van 6 november 2026, op verzoek van Olaf. **Nog niet goedgekeurd en nog niet gebouwd** (backlog 12h). Olaf komt hier op terug.

## Aanleiding

Het tabblad *Wat staat hierop?* in de vergroter (`frontend/components/Magnifier.vue`) is in versie 0.32.x stap voor stap gegroeid. Uitgezoomd is het rommelig: antwoord, vraag, geschiedenis, Wikidata en techniek lopen door elkaar, en het voorbeeldbeeld *wat de AI ziet* springt heen en weer. Olaf vroeg ook om de AI-prompt van een groep in het uitklapblok te zetten, onder de naam *AI-prompt en bijsturing*.

## Zoals het nu is (0.32.6)

Negen blokken onder elkaar:

1. uitleg vooraf (alleen vóór de eerste vraag);
2. het antwoord: *Soort*, *Onderwerp*, *Beschrijving*, de gelezen teksten, met potloodjes, *Ongedaan maken*, *Terug naar de AI-tekst* en *Beschrijving verwijderen*;
3. rechts het voorbeeld *wat de AI ziet* (met *groot bekijken*);
4. de rij *AI-prompt* van een groep, met de schakelaar *Alleen deze objecten* en de eerdere beschrijvingen van de objecten;
5. het uitklapblok *AI-bijsturing*: een aanwijzing en *Ruimte rond de uitsnede*; het voorbeeld verhuist hierheen zolang het blok open is;
6. de knop *Beschrijf deze afbeelding* (of *opnieuw*), met het bedrag;
7. *Eerdere beschrijvingen* (uitklapblok);
8. *Suggesties voor 'beeldt af'* (P180, Wikidata);
9. *Model, kosten en kwaliteit* (uitklapblok).

## Voorstel: vier subtabbladen, in de volgorde van het werk

```
┌ Uitsnede │ AI-aangevuld │ Wat staat hierop? │ Commons-concept ─────────────────────┐
│  ( Antwoord )  ( AI-prompt en bijsturing )  ( Beeldt af (P180) )  ( Eerder (2) )  │
├───────────────────────────────────────────────────────────────┬───────────────────┤
│ 1. ANTWOORD                                                   │ ┌───────────────┐ │
│ Soort 🤖      persoon · zekerheid: hoog                       │ │ wat de AI ziet│ │
│ Onderwerp 🤖  jongen in wit matrozenpak met doos        ✎     │ │ (rood: de     │ │
│               Boy in white sailor suit with box         ✎     │ │ uitsnede)     │ │
│ Beschrijving 🤖 Een jongen met kort rood haar …         ✎     │ └───────────────┘ │
│ Tekst rond het beeld  Doozen vol met lekkers …       ✎ 🗑    │ groot bekijken en │
│ [Met de hand aangepast]  Terug naar de AI-tekst  🗑 Verwijderen│ de gelezen tekst  │
│                                                               │ controleren (1)   │
│ [ Beschrijf deze afbeelding opnieuw  ± $0,0004 ]  ruimte 0%   │                   │
│ Niet goed? Pas de vraag aan → AI-prompt en bijsturing         │                   │
│ ▸ Model, kosten en kwaliteit   (ingeklapt)                    │                   │
└───────────────────────────────────────────────────────────────┴───────────────────┘
```

- **Antwoord** (standaard): wat de AI zei, met bewerken en ongedaan maken, en de knop om (opnieuw) te vragen, met het bedrag. Rechts staat altijd hetzelfde voorbeeld *wat de AI ziet*; het springt niet meer. *Model, kosten en kwaliteit* staat ingeklapt onderaan, als achtergrondinformatie.
- **AI-prompt en bijsturing**: alles wat de volgende vraag stuurt, op één plek:
  - de **AI-prompt** van een groep, met de schakelaar *Alleen deze objecten* en de eerdere beschrijvingen van de objecten (alleen bij een groep);
  - de **aanwijzing voor de AI**;
  - **Ruimte rond de uitsnede**, met het voorbeeld ernaast dat meebeweegt;
  - onderaan dezelfde knop *Beschrijf deze afbeelding* met het bedrag, zodat je meteen kunt vragen.
- **Beeldt af (P180)**: de Wikidata-suggesties en zelf zoeken. De volgende stap na een beschrijving; hoort bij het Commons-concept.
- **Eerder (n)**: eerdere beschrijvingen, om terug te zetten of te verwijderen. Alleen als die er zijn.

**Vóór de eerste vraag** opent *Antwoord* met de uitleg die er nu staat, de grote knop *Beschrijf deze afbeelding*, en een link *eerst de vraag aanpassen → AI-prompt en bijsturing*.

## Waarom zo

- Elk subtabblad heeft één doel; de hoofdactie (vragen, met het bedrag) staat altijd op dezelfde plek.
- Bij een gewoon object zie je geen groepsopties.
- Er verdwijnt geen functie; ze krijgen alleen een vaste plek.
- Codex-tabbladen (`CdxTabs`, niet omkaderd), zodat ze onder de hoofdtabbladen van de vergroter als tweede laag te herkennen zijn.

## Open punten voor Olaf

1. Akkoord met de vier subtabbladen en hun namen?
2. *Model, kosten en kwaliteit* ingeklapt onder *Antwoord* (voorstel), of een eigen subtabblad?
3. *Beeldt af (P180)* hier, of naar het tabblad *Commons-concept*, waar het voor gebruikt wordt?
4. Moet het subtabblad onthouden worden bij *Vorige*/*Volgende* (voorstel: ja, zolang de vergroter open is)?

## Bij het bouwen

- Alleen `Magnifier.vue` (en de stijl in `static/css/app.css`) verandert; de API niet.
- Vertalingen in `frontend/i18n/nl.json` en `en.json` voor de namen van de subtabbladen en de link.
- Testen op de proefserver (poort 5055, proefmodus), met een gewoon object en met een groep.
