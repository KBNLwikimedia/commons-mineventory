"""Rights labels for a Commons file and its cut-outs (functional design 5.3).

On Commons the licence is already settled, so the app does not guess whether
something is free. It warns, it does not block, except for an original under
discussion (deletion request, copyright violation, pending licence review):
then uploading is switched off, as CropTool does.
"""

import re

from . import sdc, wikitekst

# Label ids, most serious first; the first one present is the main label.
ORDER = ("ter_discussie", "merk", "persoonlijkheidsrechten", "alleen_vs", "naamsvermelding", "in_orde")

DISPUTED = {
    "delete", "copyvio", "speedydelete", "speedy", "no permission since", "no license since",
    "no source since", "nld", "npd", "nsd", "dw no source since", "deletion request",
}
REVIEWS = {"flickrreview", "licensereview", "license review", "ipernityreview", "picasareview"}
PERSONALITY = {"personality rights", "personality", "consent"}
TRADEMARK = {"trademarked", "trademark", "insignia"}

# Kinds from "Wat staat hierop?" (beschrijving.KINDS) that point at a trademark or a person.
TRADEMARK_KINDS = {"logo", "advertentie"}
PERSON_KINDS = {"portret", "persoon"}
PERSON_LABELS = {"person", "portrait", "human figure", "man", "woman", "child", "saint"}


def _pending_review(template):
    """A licence review without a confirmation: no reviewer/date parameters,
    or an explicit pending/failed state."""
    values = [v.strip().lower() for v in template.params.values()]
    if any(v in ("fail", "failed", "pending", "error") for v in values):
        return True
    named = {k for k, v in template.params.items() if v.strip() and not k.isdigit()}
    return len(template.positional()) < 2 and not named & {"reviewer", "date", "1", "2"}


def file_labels(wikitext, extmetadata=None, parsed_sdc=None):
    """Rights signals of the original file.

    Returns {"labels": [...], "label": main label, "redenen": [Dutch reasons],
    "upload_toegestaan": bool, "publiek_domein": bool, "naamsvermelding_verplicht": bool}.
    """
    extmetadata = extmetadata or {}
    parsed_sdc = parsed_sdc or {}
    calls = wikitekst.templates(wikitext or "", nested=True)
    names = {t.name for t in calls}
    restrictions = (extmetadata.get("Restrictions") or "").lower()
    short = (extmetadata.get("LicenseShortName") or "").strip()
    labels, reasons = set(), []

    disputed = sorted(names & DISPUTED)
    pending = [t.name for t in calls if t.name in REVIEWS and _pending_review(t)]
    if disputed or pending:
        labels.add("ter_discussie")
        if disputed:
            reasons.append("Het origineel staat ter discussie: " + ", ".join("{{%s}}" % n for n in disputed) + ".")
        if pending:
            reasons.append("De licentiecontrole is nog niet bevestigd: " + ", ".join("{{%s}}" % n for n in pending) + ".")
    if names & TRADEMARK or "trademark" in restrictions:
        labels.add("merk")
        reasons.append("Het origineel bevat een merk ({{Trademarked}}).")
    if names & PERSONALITY or "personality" in restrictions:
        labels.add("persoonlijkheidsrechten")
        reasons.append("Op het origineel staan persoonlijkheidsrechten ({{Personality rights}}).")
    if any(n == "pd-us-only" or n.endswith("-us-only") for n in names):
        labels.add("alleen_vs")
        reasons.append("Alleen in de Verenigde Staten vrij ({{PD-US-only}}); dat mag op Commons niet.")
    attribution = (
        str(extmetadata.get("AttributionRequired", "")).lower() == "true"
        or bool(re.match(r"cc[ -]by", short, re.I))
        or any(re.match(r"cc-by", n) for n in names)
    )
    if attribution:
        labels.add("naamsvermelding")
        reasons.append(f"Naamsvermelding verplicht ({short or 'CC BY'}): maker en licentie komen in de nieuwe pagina.")
    if not labels - {"naamsvermelding"} and not attribution:
        labels.add("in_orde")
    raw_licenses = [
        raw for raw in wikitekst.license_templates(wikitext or "")
        if wikitekst.LICENSE_NAME.match(wikitekst.normalise_name(raw[2:].split("|")[0].split("}")[0]))
    ]
    # Public domain (6.3): P6216 says so and the licence templates are PD, with
    # no CC or GFDL among them (also not inside {{self|…}}).
    pd_template = bool(raw_licenses) and any(re.match(r"\{\{\s*pd", r, re.I) for r in raw_licenses) and not any(
        re.search(r"cc-|cc0|cc-zero|gfdl", r, re.I) for r in raw_licenses
    )
    ordered = [label for label in ORDER if label in labels]
    return {
        "labels": ordered,
        "label": ordered[0] if ordered else "in_orde",
        "redenen": reasons,
        "upload_toegestaan": "ter_discussie" not in labels,
        "publiek_domein": sdc.is_public_domain(parsed_sdc) and pd_template,
        "naamsvermelding_verplicht": attribution,
    }


def object_labels(file_rights, obj):
    """Labels of one cut-out (5.3): the file's labels, but personality rights
    only when the cut-out shows a person, and a trademark also when "Wat staat
    hierop?" says logo/advertisement or names a company. A confirmed trademark
    (the user's choice, with a reason) is kept on the object as `merk_bevestigd`."""
    labels = set(file_rights.get("labels", []))
    description = obj.get("beschrijving") or {}
    kind = description.get("soort")
    label = (obj.get("label") or "").lower()
    shows_person = kind in PERSON_KINDS or label in PERSON_LABELS
    if "persoonlijkheidsrechten" in labels and not shows_person:
        labels.discard("persoonlijkheidsrechten")
    if kind in TRADEMARK_KINDS or (kind == "logo" and description.get("bedrijf_of_naam")):
        labels.add("merk")
    labels.discard("in_orde")
    if not labels:
        labels.add("in_orde")
    ordered = [label for label in ORDER if label in labels]
    return {"labels": ordered, "label": ordered[0]}


def default_checked(labels):
    """Checked by default in the upload menu (9.1): only In orde and Naamsvermelding verplicht."""
    return set(labels) <= {"in_orde", "naamsvermelding"}
