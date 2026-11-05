# Privacy – Commons Mineventory

*Draft, phase 1. The final statement comes before the deployment to Toolforge (phase 3).* [Nederlandse versie](/privacy?uselang=nl)

The Commons Mineventory is an experiment. It is not an official service of the KB, National Library of the Netherlands, or of the Wikimedia Foundation.

## What the app processes about you

- **Without logging in**: nothing that can be traced to you. The app uses a session cookie to remember your choice of language (Dutch or English).
- **With a login (phase 2)**: your Commons user name and an access token from Wikimedia (OAuth 2.0). The token is kept only on the server, in a server-side session, and never in your browser.
- **Usage log**: for every paid call (SAM or Muse Spark) the app records when, for which file and by which Commons user. This log is visible only to users on the access list and to administrators.

## What goes to third parties

- **Wikimedia Commons and Wikidata**: the server fetches files and data; your browser loads files from the tool itself only. For the preview, the server has Commons render the wikitext of a draft; your browser gets only cleaned-up HTML, without images, styles or scripts from Wikimedia.
- **Searching Wikidata**: search terms for *depicts* go to Wikidata through the server (`wbsearchentities`), not from your browser.
- **Meta Model API** (live mode only): the server sends a smaller version of the public Commons file (for SAM at most 1920 px wide) or a cut-out (at most 1024 px) to Meta, with the context of the file page (description, categories), the text the model read in the image earlier, your search terms, and what you type yourself as a caption or hint. Never any data about you as a person.
- **No external scripts, fonts or CDNs**: everything your browser loads comes from the tool itself. That way your IP address does not leak to third parties, as the Toolforge terms of use ask.

## Kept in your browser

This is kept in your own browser's storage (localStorage), not on the server, and goes away when you clear that storage:

- the *Viewed* list (the images you opened) and what you have *Set aside*;
- which columns you slid away and how wide they are;
- your choice of Masks, Boxes and Names, and the position and size of the magnifier;
- which search terms you switched off for *Detect all objects*, and which headers are open or folded.

## Kept on the server

Originals 7 days, cut-outs not yet uploaded 30 days, detections and descriptions 1 year, each counted from the last use (functional design 12.1, in Dutch). The usage log stays.
