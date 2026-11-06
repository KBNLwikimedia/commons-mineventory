"""REST API under /api/v1 (functional design, chapter 11). The UI is a client
of these same endpoints.

Conventions from the Delpher Uitsnijder: JSON errors {"fout": …} with a fixed
"code" the UI translates, X-Robots-Tag: noindex, 201 on creating, and a GET
never costs money and never changes anything.
"""

import hashlib
import math
import re
from urllib.parse import quote

from flask import Blueprint, Response, current_app, g, jsonify, request, session

from . import __version__, concept, export, weergave
from .cache import FetchError
from .commons import CommonsError, public as public_file
from .detectie.basis import DetectionError
from .openapi import openapi_spec

api = Blueprint("api", __name__, url_prefix="/api/v1")

IMAGE_DEFAULT_WIDTH = 1280


@api.after_request
def _no_indexing(response):
    """Search engines and crawlers have no business in the API. An old path
    (deprecated since 0.29.0, gone in 0.33.0) says so, with its successor."""
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    successor = g.get("successor")
    rule = request.url_rule.rule if request.url_rule else ""
    if successor is None and "/object/<object_id>" in rule:
        successor = request.path.replace("/object/", "/objecten/", 1)
    if successor:
        response.headers["Deprecation"] = "true"
        response.headers["Link"] = f'<{successor}>; rel="successor-version"'
    return response


def _client():
    return current_app.extensions["commons"]


def _service():
    return current_app.extensions["detectiedienst"]


def _descriptions():
    return current_app.extensions["beschrijvingsdienst"]


def _user():
    """The logged-in Commons user (phase 2: OAuth). Until then, in debug mode
    only, LOKALE_GEBRUIKER stands in for a login, so live mode can be tried
    locally; on a server (no debug) it is ignored."""
    # Phase 2: the user OAuth puts in the session. Nothing sets it yet, so it is not
    # read: a forged session cookie must never count as a login.
    return (current_app.debug and current_app.config.get("LOKALE_GEBRUIKER")) or None


def _require_paid_access(paid):
    """Paid calls only for logged-in users on the access list (8.3). In dummy
    mode nothing is paid, so nothing is checked."""
    if not paid:
        return
    user = _user()
    if not user:
        raise DetectionError("Log in met je Commons-account om betaalde aanroepen te doen.", status=401, code="login_required")
    allowed = set(current_app.config["TOEGESTANE_GEBRUIKERS"]) | set(current_app.config["BEHEERDERS_START"])
    if user not in allowed:
        raise DetectionError(
            "Je staat niet op de toegangslijst voor betaalde aanroepen. Vraag toegang aan.", status=403, code="not_on_access_list"
        )


def _require_trusted_user():
    """On a server (not in debug mode): only for a logged-in user on the access list.
    For what concerns everybody (the usage log with user names, emptying the whole
    trash) until OAuth separates users (phase 2). Locally nothing changes."""
    if current_app.debug or current_app.testing:
        return
    user = _user()
    allowed = set(current_app.config["TOEGESTANE_GEBRUIKERS"]) | set(current_app.config["BEHEERDERS_START"])
    if not user or user not in allowed:
        raise DetectionError("Alleen voor ingelogde gebruikers op de toegangslijst.", status=403, code="not_on_access_list")


def _file(mid):
    match = re.fullmatch(r"[Mm](\d+)", mid or "")
    if not match:
        raise CommonsError(f"'{mid}' is geen M-id (bijv. M28830642).", status=400, code="bad_mid")
    return _client().load_file({"pageid": int(match.group(1))})


def _page_file(mid, n):
    file = _file(mid)
    _client().page_ref(file, n)
    return file


def _body():
    body = request.get_json(silent=True)
    return body if isinstance(body, dict) else {}


@api.before_request
def _same_site_only():
    """A request that changes something (or costs money) only from the app's own
    pages: another website cannot make the browser POST, PATCH or DELETE here
    (CSRF). Browsers send Origin and Sec-Fetch-Site; scripts and tests may send
    neither. A body must be JSON."""
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return None
    if request.headers.get("Sec-Fetch-Site", "same-origin") not in ("same-origin", "none"):
        raise DetectionError("Alleen vanaf de eigen pagina's van de app.", status=403, code="cross_site")
    origin = request.headers.get("Origin")
    if origin and origin != request.host_url.rstrip("/"):
        raise DetectionError("Alleen vanaf de eigen pagina's van de app.", status=403, code="cross_site")
    if request.content_length and not request.is_json:
        raise DetectionError("Stuur de gegevens als JSON (Content-Type: application/json).", status=415, code="not_json")
    return None


MID = re.compile(r"M\d{1,12}")


# -- Errors -------------------------------------------------------------------------------


@api.errorhandler(CommonsError)
def _commons_error(exc):
    return jsonify({"fout": exc.message, "code": exc.code}), exc.status


@api.errorhandler(DetectionError)
def _detection_error(exc):
    return jsonify({"fout": exc.message, "code": exc.code, "opnieuw": exc.retry, "budget": _service().verbruik.status(_user())}), exc.status


@api.errorhandler(FetchError)
def _fetch_error(exc):
    current_app.logger.warning("Commons fetch failed: %s", exc)
    return jsonify({"fout": "Commons is traag of onbereikbaar. Probeer het opnieuw.", "code": "commons_unreachable", "detail": str(exc)}), 502


@api.app_errorhandler(404)
def _not_found(exc):
    if request.path.startswith("/api/"):
        return jsonify({"fout": "Deze bron bestaat niet in de API. Zie /api/v1/openapi.json.", "code": "not_found"}), 404
    return exc


@api.app_errorhandler(405)
def _method_not_allowed(exc):
    if request.path.startswith("/api/"):
        response = jsonify({"fout": f"Methode {request.method} is hier niet toegestaan.", "code": "method_not_allowed"})
        response.status_code = 405
        response.headers["Allow"] = ", ".join(exc.valid_methods or [])
        return response
    return exc


# -- Files and pages ------------------------------------------------------------------------


def _file_resource(file):
    public = public_file(file)
    public["pagina_lijst"] = [
        {"n": n, "afbeelding_url": f"/api/v1/bestand/{file['mid']}/pagina/{n}/afbeelding?w=120"} for n in range(1, file["paginas"] + 1)
    ]
    return public


@api.get("/bestand")
def find_file():
    """Normalise the input (url, titel or mid) and return the file."""
    text = request.args.get("url") or request.args.get("titel") or request.args.get("mid")
    if not text:
        raise CommonsError("Geef url=…, titel=… of mid=… mee.", code="empty_input")
    return jsonify(_file_resource(_client().load_file(text)))


@api.get("/bestand/<mid>")
def get_file(mid):
    return jsonify(_file_resource(_file(mid)))


@api.get("/bestand/<mid>/pagina/<int:n>")
def get_page(mid, n):
    """Page size, objects, and how many regions Commons has (7.5)."""
    file = _page_file(mid, n)
    page = _client().load_page(file, n)
    objects = [_service().public(file, n, o) for o in _service().page_objects(file, n)]
    trashed = {}
    for o in _service()._load_store(file, n)["prullenbak"]:
        if o.get("zoekterm"):
            trashed[o["zoekterm"]] = trashed.get(o["zoekterm"], 0) + 1
    return jsonify(
        {
            **page,
            "mid": file["mid"],
            "afbeelding_url": f"/api/v1/bestand/{file['mid']}/pagina/{n}/afbeelding",
            "regio_aantal": file["regio_aantal"] if n == 1 else 0,
            "notitie_aantal": file["notitie_aantal"] if n == 1 else 0,
            "objecten": objects,
            # Per search term: how many objects of this page are in the trash.
            "prullenbak_termen": trashed,
        }
    )


@api.get("/bestand/<mid>/pagina/<int:n>/afbeelding")
def get_page_image(mid, n):
    """A reduced page image (a Commons thumbnail step of at least w, cached)."""
    try:
        width = int(request.args.get("w", IMAGE_DEFAULT_WIDTH))
    except ValueError:
        raise CommonsError("Parameter w moet een getal zijn.")
    file = _page_file(mid, n)
    data = _client().page_image(file, n, max(20, min(3840, width)))
    mimetype = "image/png" if data[:8] == b"\x89PNG\r\n\x1a\n" else "image/webp" if data[8:12] == b"WEBP" else "image/jpeg"
    response = Response(data, mimetype=mimetype)
    response.headers["Cache-Control"] = "public, max-age=86400"
    return response


# -- Detection ----------------------------------------------------------------------------


def _number(value, name):
    """A finite number from a request, else 400 (never NaN or infinity)."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise DetectionError(f"'{name}' moet een getal zijn.", status=400, code="invalid_body") from None
    if not math.isfinite(number):
        raise DetectionError(f"'{name}' moet een eindig getal zijn.", status=400, code="invalid_body")
    return number


def _minscore(value):
    score = _number(value or 0, "minscore")
    if not 0 <= score <= 1:
        raise DetectionError("Parameter minscore moet een getal tussen 0 en 1 zijn.", status=400, code="invalid_body")
    return score


@api.post("/bestand/<mid>/pagina/<int:n>/detecties")
def create_detection(mid, n):
    """Run a detection (7): {"prompt", "modus", "minscore"}, a
    click {"punt": {x, y}}, a manual rectangle {"rechthoek": {x, y, w, h}}
    (free), or a SAM mask for an object with a rectangle {"masker_voor": id}.
    Only through POST, so link previews and crawlers can never cost money."""
    file = _page_file(mid, n)
    body = _body()
    service = _service()
    paid = service.detector.betaald
    if "punt" in body:
        point = body["punt"] if isinstance(body["punt"], dict) else {}
        if "x" not in point or "y" not in point:
            raise DetectionError("Geef punt.x en punt.y mee (pixels van het origineel).", status=400)
        x, y = _number(point["x"], "punt.x"), _number(point["y"], "punt.y")
        _require_paid_access(paid)
        result = service.point(file, n, x, y, user=_user())
    elif "rechthoek" in body:
        rect = body["rechthoek"] if isinstance(body["rechthoek"], dict) else {}
        result = service.rectangle(file, n, {k: _number(rect.get(k), f"rechthoek.{k}") for k in ("x", "y", "w", "h")})
    elif "masker_voor" in body:
        _require_paid_access(paid)
        result = service.refine_mask(file, n, str(body["masker_voor"]), user=_user())
    else:
        modus = body.get("modus", "prompt")
        if modus != "commons":
            _require_paid_access(paid and service.plan(file, n, service.terms(body.get("prompt", ""), modus))["betaald"])
        result = service.detect(
            file, n, prompt=body.get("prompt", ""), modus=modus,
            minscore=_minscore(body.get("minscore")), user=_user(),
        )
    return jsonify(result), 201


@api.get("/bestand/<mid>/pagina/<int:n>/detecties/raming")
def estimate_detection(mid, n):
    """What a detection would cost (paid calls, cached terms). Never calls the detector."""
    file = _page_file(mid, n)
    result = _service().detect(
        file, n, prompt=request.args.get("prompt", ""), modus=request.args.get("modus", "prompt"),
        minscore=_minscore(request.args.get("minscore")), dry_run=True, user=_user(),
    )
    return jsonify(result)


@api.get("/bestand/<mid>/pagina/<int:n>/inventaris")
def inventory_plan(mid, n):
    """The stored overview ("Wat staat op deze pagina?") and what a new one would cost."""
    return jsonify(_descriptions().inventory_plan(_page_file(mid, n), n, user=_user()))


@api.delete("/bestand/<mid>/pagina/<int:n>/inventaris")
def forget_inventory(mid, n):
    """Remove the whole page overview from the page. Free."""
    return jsonify(_descriptions().forget_inventory(_page_file(mid, n), n))


@api.patch("/bestand/<mid>/pagina/<int:n>/inventaris")
def edit_inventory(mid, n):
    """Change the description of the image by hand: paginasoort, paginasoort_en,
    samenvatting, samenvatting_en, tekst. Free."""
    return jsonify(_descriptions().edit_inventory(_page_file(mid, n), n, _body()))


@api.get("/bestand/<mid>/pagina/<int:n>/inventaris/geschiedenis")
def inventory_history(mid, n):
    """Earlier descriptions of the image, newest first (free)."""
    return jsonify({"geschiedenis": _descriptions().inventory_history(_page_file(mid, n), n)})


@api.delete("/bestand/<mid>/pagina/<int:n>/inventaris/geschiedenis/<versie>")
def delete_inventory_version(mid, n, versie):
    """Delete one earlier description of the image. Free."""
    return jsonify(_descriptions().forget_inventory_version(_page_file(mid, n), n, versie))


@api.put("/bestand/<mid>/pagina/<int:n>/inventaris/<deel>")
def put_inventory_part(mid, n, deel):
    """Make an earlier description of the image current again: {"versie": …}
    (only the part "beschrijving" has versions). Free."""
    if deel != "beschrijving":
        raise DetectionError("Alleen de beschrijving heeft eerdere versies.", status=404, code="not_found")
    body = _body()
    if not isinstance(body.get("versie"), str) or not body["versie"]:
        raise DetectionError("Geef de 'versie' uit de geschiedenis.", status=400, code="invalid_body")
    return jsonify(_descriptions().restore_inventory(_page_file(mid, n), n, body["versie"]))


@api.delete("/bestand/<mid>/pagina/<int:n>/inventaris/<deel>")
def forget_inventory_part(mid, n, deel):
    """Remove one part of the overview: beschrijving or zoektermen. Free."""
    return jsonify(_descriptions().forget_inventory(_page_file(mid, n), n, deel))


@api.post("/bestand/<mid>/pagina/<int:n>/inventaris/<deel>")
def inventory_part(mid, n, deel):
    """Ask one part of the overview anew (beschrijving or zoektermen); always
    a new answer, paid in live mode. The other part stays."""
    body = _body()
    _require_paid_access(_descriptions().vision.betaald)
    return jsonify(_descriptions().inventory(_page_file(mid, n), n, body.get("model"), again=True, user=_user(), part=deel, detail=body.get("detailniveau")))


@api.post("/bestand/<mid>/pagina/<int:n>/inventaris")
def inventory(mid, n):
    """Ask Muse Spark what is on the page (paid in live mode, cached)."""
    body = _body()
    _require_paid_access(_descriptions().vision.betaald)
    return jsonify(
        _descriptions().inventory(_page_file(mid, n), n, body.get("model"), again=bool(body.get("opnieuw")), user=_user(), detail=body.get("detailniveau"))
    )


# -- Objects ------------------------------------------------------------------------------


@api.post("/bestand/<mid>/pagina/<int:n>/groepen")
def make_group(mid, n):
    """Make one object of several (7.4): {"objecten": [ids]} or {"zoekterm": "…"},
    optionally with {"naam": "…"}. Free. 201 with the group and all objects of the page."""
    body = _body()
    result = _service().group(_page_file(mid, n), n, ids=body.get("objecten"), term=body.get("zoekterm"), name=body.get("naam"))
    return jsonify(result), 201


@api.delete("/bestand/<mid>/pagina/<int:n>/groepen/<object_id>")
def remove_group(mid, n, object_id):
    """Undo a group (7.4): its members come back. Free."""
    return jsonify({"objecten": _service().ungroup(_page_file(mid, n), n, object_id)})


@api.post("/bestand/<mid>/pagina/<int:n>/samenvoegingen")
def merge_duplicates(mid, n):
    """Merge the objects of the page that show the same picture (7.4). Free."""
    file = _page_file(mid, n)
    service = _service()
    merged = service.merge_duplicates(file, n)
    return jsonify({"objecten": [service.public(file, n, o) for o in service.page_objects(file, n)], "samengevoegd": merged})


@api.patch("/bestand/<mid>/pagina/<int:n>/objecten")
def patch_objects(mid, n):
    """{"geselecteerd": [ids]} (exactly these are selected) or {"objecten":
    [{"id", "status"}]}; {"samenvoegen": true} merges duplicates (7.4)."""
    file = _page_file(mid, n)
    body = _body()
    service = _service()
    merged = 0
    if body.get("samenvoegen"):  # deprecated (0.29.0): POST …/samenvoegingen
        g.successor = f"{request.script_root}/api/v1/bestand/{mid}/pagina/{n}/samenvoegingen"
        merged = service.merge_duplicates(file, n)
        objects = [service.public(file, n, o) for o in service.page_objects(file, n)]
    elif "geselecteerd" in body:
        objects = service.set_selection(file, n, body["geselecteerd"])
    elif isinstance(body.get("objecten"), list):
        objects = service.set_statuses(file, n, body["objecten"])
    else:
        raise DetectionError("Geef 'geselecteerd' (een lijst id's), 'objecten' (een lijst {id, status}) of 'samenvoegen': true.", status=400)
    return jsonify({"objecten": objects, "samengevoegd": merged})


@api.get("/bestand/<mid>/pagina/<int:n>/objecten/<object_id>")
@api.get("/bestand/<mid>/pagina/<int:n>/object/<object_id>")
def get_object(mid, n, object_id):
    return jsonify(_service().get_object(_page_file(mid, n), n, object_id))


@api.patch("/bestand/<mid>/pagina/<int:n>/objecten/<object_id>")
@api.patch("/bestand/<mid>/pagina/<int:n>/object/<object_id>")
def patch_object(mid, n, object_id):
    """{"bijschrift": {"tekst"} | null}, {"naam": "…" | null}, {"status": …} and/or
    {"prullenbak": true | false}. The name is your own name for the object in the list."""
    body = _body()
    fields = {"bijschrift", "naam", "status", "prullenbak"}
    if not body or not set(body) <= fields:
        raise DetectionError("Te wijzigen: 'bijschrift', 'naam', 'status' en 'prullenbak'.", status=400)
    file = _page_file(mid, n)
    service = _service()
    if "prullenbak" in body:
        if not isinstance(body["prullenbak"], bool):
            raise DetectionError("'prullenbak' is true of false.", status=400)
        if body["prullenbak"] != service.in_trash(file, n, object_id):
            (service.delete_object if body["prullenbak"] else service.restore_object)(file, n, object_id)
    if "status" in body:
        service.set_statuses(file, n, [{"id": object_id, "status": body["status"]}])
    if "bijschrift" in body:
        service.set_caption(file, n, object_id, body["bijschrift"])
    if "naam" in body:
        service.set_name(file, n, object_id, body["naam"])
    return jsonify(service.get_object(file, n, object_id))


@api.delete("/bestand/<mid>/pagina/<int:n>/objecten/<object_id>")
@api.delete("/bestand/<mid>/pagina/<int:n>/object/<object_id>")
def delete_object(mid, n, object_id):
    """To the trash (it can be restored)."""
    file = _page_file(mid, n)
    objects = _service().delete_object(file, n, object_id)
    return jsonify({"verwijderd": object_id, "objecten": objects})


def _preview_width():
    value = request.args.get("w")
    if value in (None, "", "origineel"):
        return None
    try:
        return max(50, min(1600, int(value)))
    except ValueError:
        raise DetectionError("Parameter w moet een getal zijn, of 'origineel'.", status=400)


def _image(data, mimetype, filename=None):
    """An image response. With ?download=1 it is an attachment (the browser
    saves it), otherwise it is shown (inline)."""
    response = Response(data, mimetype=mimetype)
    response.headers["Cache-Control"] = "private, max-age=300"
    if filename:
        disposition = "attachment" if request.args.get("download") in ("1", "true", "ja") else "inline"
        # An ASCII fallback plus the full UTF-8 name (RFC 6266), e.g. with an en dash.
        fallback = "".join(c if 32 <= ord(c) < 127 and c not in '"\\' else "_" for c in filename)
        response.headers["Content-Disposition"] = f"{disposition}; filename=\"{fallback}\"; filename*=UTF-8''{quote(filename, safe='')}"
    return response


def _download_name(file, n, object_id, kind):
    """The file name of a download: the name in the Commons concept, with the right extension."""
    try:
        name = concept.concept(file, _service()._find(file, n, object_id))["bestandsnaam"]
    except DetectionError:
        return f"{object_id}.{kind}"
    return f"{name.rsplit('.', 1)[0]}.{kind}"


@api.get("/bestand/<mid>/pagina/<int:n>/objecten/<object_id>/uitsnede.jpg")
@api.get("/bestand/<mid>/pagina/<int:n>/object/<object_id>/uitsnede.jpg")
def cutout_jpeg(mid, n, object_id):
    """The rectangle as JPG: at full resolution, or a preview with w=…."""
    file = _page_file(mid, n)
    width = _preview_width()
    if width:
        return _image(_service().cutout_jpeg(file, n, object_id, width), "image/jpeg")
    return _image(_service().saved_file(file, n, object_id, "jpg"), "image/jpeg", _download_name(file, n, object_id, "jpg"))


@api.get("/bestand/<mid>/pagina/<int:n>/objecten/<object_id>/uitsnede.png")
@api.get("/bestand/<mid>/pagina/<int:n>/object/<object_id>/uitsnede.png")
def cutout_png(mid, n, object_id):
    """The shape of the object as transparent PNG, at full resolution."""
    file = _page_file(mid, n)
    return _image(_service().saved_file(file, n, object_id, "png"), "image/png", _download_name(file, n, object_id, "png"))


@api.get("/bestand/<mid>/pagina/<int:n>/objecten/<object_id>/masker.png")
@api.get("/bestand/<mid>/pagina/<int:n>/object/<object_id>/masker.png")
def mask_image(mid, n, object_id):
    data = _service().mask_png(_page_file(mid, n), n, object_id)
    response = Response(data, mimetype="image/png")
    response.headers["Cache-Control"] = "public, max-age=86400"
    return response


# -- AI-completed version (Muse Image, 7.7) -------------------------------------------------


def _completions():
    return current_app.extensions["aanvuldienst"]


@api.get("/bestand/<mid>/pagina/<int:n>/objecten/<object_id>/aanvulling")
def completion_plan(mid, n, object_id):
    """The AI-completed version of the cut-out, if any, and what a new one costs. Free."""
    return jsonify(_completions().plan(_page_file(mid, n), n, object_id))


@api.post("/bestand/<mid>/pagina/<int:n>/objecten/<object_id>/aanvulling")
def completion_make(mid, n, object_id):
    """Have Muse Image fill in what is missing in the cut-out (paid in live mode,
    cached; {"opnieuw": true} asks anew). The result is invented: never a source."""
    _require_paid_access(_completions().editor.betaald)
    body = _body()
    result = _completions().complete(_page_file(mid, n), n, object_id, again=bool(body.get("opnieuw")), user=_user())
    return jsonify(result), 201


@api.delete("/bestand/<mid>/pagina/<int:n>/objecten/<object_id>/aanvulling")
def completion_forget(mid, n, object_id):
    """Remove the AI-completed version from the object. Free."""
    return jsonify({"object": _completions().forget(_page_file(mid, n), n, object_id)})


@api.get("/bestand/<mid>/pagina/<int:n>/objecten/<object_id>/aangevuld-ingevuld.png")
def completion_filled(mid, n, object_id):
    """What the AI filled in, as a transparent overlay for the AI-completed version (approximate)."""
    return _image(_completions().filled_overlay(_page_file(mid, n), n, object_id), "image/png")


@api.get("/bestand/<mid>/pagina/<int:n>/objecten/<object_id>/aangevuld.png")
def completion_image(mid, n, object_id):
    """The PNG of the AI-completed version."""
    file = _page_file(mid, n)
    name = _download_name(file, n, object_id, "png").rsplit(".", 1)[0] + " (AI-augmented).png"
    return _image(_completions().image(file, n, object_id), "image/png", name)


# -- Description ----------------------------------------------------------------------------


@api.get("/bestand/<mid>/pagina/<int:n>/objecten/<object_id>/beschrijving")
@api.get("/bestand/<mid>/pagina/<int:n>/object/<object_id>/beschrijving")
def description_plan(mid, n, object_id):
    """The stored description (or null) and what a new one would cost. Free."""
    return jsonify(_descriptions().plan(_page_file(mid, n), n, object_id, user=_user()))


@api.post("/bestand/<mid>/pagina/<int:n>/objecten/<object_id>/beschrijving")
@api.post("/bestand/<mid>/pagina/<int:n>/object/<object_id>/beschrijving")
def describe_object(mid, n, object_id):
    """"Wat staat hierop?" (paid in live mode, cached). Body: {"model": "auto" |
    "standaard" | "contributor", "opnieuw": false, "aanwijzing": "…", "marge": 0.25,
    "alleen_groep": true}; the optional hint is an extra instruction for the model ("only the
    boy"), the margin the share of the box shown around it (0-1); for a group, "alleen_groep":
    false leaves out the instruction to look at its members only."""
    body = _body()
    if not isinstance(body.get("aanwijzing") or "", str):
        raise DetectionError("'aanwijzing' is een tekst.", status=400, code="invalid_body")
    if not isinstance(body.get("alleen_groep", True), bool):
        raise DetectionError("'alleen_groep' is true of false.", status=400, code="invalid_body")
    _require_paid_access(_descriptions().vision.betaald)
    file = _page_file(mid, n)
    return jsonify(
        _descriptions().describe(
            file, n, object_id, body.get("model"), again=bool(body.get("opnieuw")), user=_user(),
            hint=body.get("aanwijzing"), margin=body.get("marge"), group_focus=body.get("alleen_groep", True),
        )
    )


@api.get("/bestand/<mid>/pagina/<int:n>/objecten/<object_id>/beschrijving/geschiedenis")
@api.get("/bestand/<mid>/pagina/<int:n>/object/<object_id>/beschrijving/geschiedenis")
def description_history(mid, n, object_id):
    """Earlier descriptions of the object, newest first (free)."""
    return jsonify({"geschiedenis": _descriptions().history(_page_file(mid, n), n, object_id)})


@api.delete("/bestand/<mid>/pagina/<int:n>/objecten/<object_id>/beschrijving/geschiedenis/<versie>")
def delete_description_version(mid, n, object_id, versie):
    """Delete one earlier version (its "versie" from the history). Free."""
    return jsonify({"geschiedenis": _descriptions().forget_version(_page_file(mid, n), n, object_id, versie)})


@api.delete("/bestand/<mid>/pagina/<int:n>/object/<object_id>/beschrijving/geschiedenis")
def forget_description_version(mid, n, object_id):
    """Deprecated (0.29.0): DELETE …/objecten/<id>/beschrijving/geschiedenis/<versie>. Free."""
    version = request.args.get("versie", "")
    if not version:
        raise DetectionError("Geef de 'versie' die weg moet.", status=400, code="invalid_body")
    g.successor = f"{request.script_root}/api/v1/bestand/{mid}/pagina/{n}/objecten/{object_id}/beschrijving/geschiedenis/{quote(version, safe='')}"
    return jsonify({"geschiedenis": _descriptions().forget_version(_page_file(mid, n), n, object_id, version)})


@api.put("/bestand/<mid>/pagina/<int:n>/objecten/<object_id>/beschrijving")
def put_description(mid, n, object_id):
    """Make an earlier version from the history the current description:
    {"versie": …}. The current one goes into the history. Free."""
    body = _body()
    if not isinstance(body.get("versie"), str) or not body["versie"]:
        raise DetectionError("Geef de 'versie' uit de geschiedenis.", status=400, code="invalid_body")
    return jsonify(_descriptions().restore(_page_file(mid, n), n, object_id, version=body["versie"]))


@api.post("/bestand/<mid>/pagina/<int:n>/object/<object_id>/beschrijving/terugzetten")
def restore_description(mid, n, object_id):
    """Deprecated (0.29.0): PUT …/objecten/<id>/beschrijving. Body: {"versie": …},
    or the older {"tijdstempel": …, "bewerkt": true|false}. Free."""
    g.successor = f"{request.script_root}/api/v1/bestand/{mid}/pagina/{n}/objecten/{object_id}/beschrijving"
    body = _body()
    if not isinstance(body.get("versie"), str) and not isinstance(body.get("tijdstempel"), str):
        raise DetectionError("Geef de 'versie' van de eerdere beschrijving.", status=400, code="invalid_body")
    return jsonify(_descriptions().restore(_page_file(mid, n), n, object_id, body.get("tijdstempel"), body.get("bewerkt"), body.get("versie")))


@api.get("/bestand/<mid>/pagina/<int:n>/objecten/<object_id>/beschrijving/invoer.jpg")
@api.get("/bestand/<mid>/pagina/<int:n>/object/<object_id>/beschrijving/invoer.jpg")
def description_input(mid, n, object_id):
    """What the image description would see: the box with ?marge= (0-1,
    default 0.25) around it, the box outlined in red. ?max= (up to 4000
    pixels) gives a larger version, to read the text in it. Free."""
    try:
        max_side = int(request.args.get("max") or 0) or None
    except ValueError:
        raise DetectionError("'max' is een aantal pixels.", status=400) from None
    data = _descriptions().model_preview(_page_file(mid, n), n, object_id, request.args.get("marge"), max_side)
    return _image(data, "image/jpeg")


@api.patch("/bestand/<mid>/pagina/<int:n>/objecten/<object_id>/beschrijving")
@api.patch("/bestand/<mid>/pagina/<int:n>/object/<object_id>/beschrijving")
def edit_description(mid, n, object_id):
    """Change the texts of the description by hand (free). Body: any of
    {"onderwerp", "onderwerp_en", "bedrijf_of_naam", "beschrijving", "beschrijving_en",
    "tekst_in_beeld", "tekst_rond_beeld"}."""
    return jsonify(_descriptions().edit(_page_file(mid, n), n, object_id, _body()))


@api.delete("/bestand/<mid>/pagina/<int:n>/objecten/<object_id>/beschrijving")
@api.delete("/bestand/<mid>/pagina/<int:n>/object/<object_id>/beschrijving")
def delete_description(mid, n, object_id):
    return jsonify(_descriptions().remove(_page_file(mid, n), n, object_id))


@api.get("/wikidata/zoek")
def search_wikidata():
    """Wikidata items for a search term (free), to choose depicts (6.2)."""
    language = request.args.get("taal", "en")
    if language not in ("nl", "en"):
        language = "en"
    return jsonify({"resultaten": _client().search_items(request.args.get("q", ""), language)})


# -- Commons concept (9.1) --------------------------------------------------------------------


def _ai_texts(obj):
    description = obj.get("beschrijving") or {}
    if not description:
        return None
    return {
        "caption": {"nl": description.get("onderwerp") or "", "en": description.get("onderwerp_en") or ""},
        "beschrijving": {"nl": description.get("beschrijving") or "", "en": description.get("beschrijving_en") or ""},
    }


def _concept(file, n, obj):
    service = _service()
    stored = obj.get("commons") or {}
    try:
        facts = service.file_facts(file, n, obj, stored.get("formaat") or "jpg")
    except Exception:  # noqa: BLE001 - the SDC then simply lacks size and checksum
        current_app.logger.warning("No file facts for %s/%s/%s", file["mid"], n, obj["id"], exc_info=True)
        facts = None
    result = concept.concept(file, obj, facts, service.client.load_page(file, n))
    result.update(
        {
            "id": obj["id"],
            "pagina": n,
            "opgeslagen": bool(obj.get("opgeslagen")),
            "bijschrift": (obj.get("bijschrift") or {}).get("tekst"),
            # What "Wat staat hierop?" said, so the UI can go back to it.
            "ai": _ai_texts(obj),
            # Label and short description of every depicts item, from Wikidata.
            "beeldt_af_info": _client().item_info([d["q"] for d in result["beeldt_af"]]) if result["beeldt_af"] else {},
            # Labels of the properties and items in the structured data, for the preview.
            "sdc_labels": _client().entity_labels(
                concept.sdc_entity_ids(result["sdc"]) + concept.sdc_entity_ids((result.get("origineel") or {}).get("sdc") or {})
                + [r["q"] for r in (result.get("origineel") or {}).get("regios", [])]
            ),
        }
    )
    return result


@api.get("/bestand/<mid>/pagina/<int:n>/objecten/<object_id>/commons/weergave")
@api.get("/bestand/<mid>/pagina/<int:n>/object/<object_id>/commons/weergave")
def render_concept(mid, n, object_id):
    """The wikitext of the concept as Commons would render it (action=parse,
    only reads), cleaned: no images, styles or scripts. Free."""
    file = _page_file(mid, n)
    result = concept.concept(file, _service()._find(file, n, object_id))
    html = _client().render_wikitext(result["wikitekst"], "File:" + result["bestandsnaam"])
    return jsonify({"html": weergave.clean_html(html)})


@api.get("/bestand/<mid>/pagina/<int:n>/objecten/<object_id>/commons")
@api.get("/bestand/<mid>/pagina/<int:n>/object/<object_id>/commons")
def get_concept(mid, n, object_id):
    """The Commons concept of an object: name, texts, licence, categories,
    depicts, rights label, wikitext and SDC. Free."""
    file = _page_file(mid, n)
    return jsonify(_concept(file, n, _service()._find(file, n, object_id)))


@api.patch("/bestand/<mid>/pagina/<int:n>/objecten/<object_id>/commons")
@api.patch("/bestand/<mid>/pagina/<int:n>/object/<object_id>/commons")
def patch_concept(mid, n, object_id):
    """Change the concept; {"herstel": true} goes back to the proposal."""
    body = _body()
    file = _page_file(mid, n)
    service = _service()
    obj = service._find(file, n, object_id)
    if body.get("herstel") is True:
        stored = {}
    else:
        try:
            concept.validate_patch(body)
        except ValueError as exc:
            raise DetectionError(str(exc), status=400, code="invalid_concept")
        stored = {**(obj.get("commons") or {}), **body}
    service.set_field(file, n, object_id, "commons", stored)
    return jsonify(_concept(file, n, service._find(file, n, object_id)))


def _saved_objects(file):
    """(page, object) for every saved object of the file, over all pages."""
    result = []
    for n in range(1, file["paginas"] + 1):
        result += [(n, o) for o in _service().page_objects(file, n) if o.get("opgeslagen")]
    return result


@api.get("/bestand/<mid>/commons")
def upload_menu(mid):
    """The upload menu (9.1): all saved cut-outs of the file with their concept."""
    file = _file(mid)
    items = [{**_concept(file, n, o), "object": _service().public(file, n, o)} for n, o in _saved_objects(file)]
    return jsonify(
        {
            "bestand": public_file(file),
            "upload_aan": current_app.config["COMMONS_UPLOAD"],
            "aantal": len(items),
            "uitsneden": items,
        }
    )


@api.get("/bestand/<mid>/commons/controle")
def check_before_upload(mid):
    """Check before upload (free, read-only on Commons): does the name exist,
    does the same image exist (SHA-1), do the categories exist.
    ?objecten=1:obj-a,2:obj-b (page:id); default: the chosen ones."""
    raw = request.args.get("objecten")
    wanted = None
    if raw is not None:
        wanted = []
        for item in filter(None, raw.split(",")):
            page, _, object_id = item.partition(":")
            if not object_id:
                raise DetectionError("'objecten' is een lijst pagina:id, gescheiden door komma's.", status=400, code="invalid_parameter")
            wanted.append({"pagina": page, "id": object_id})
    return jsonify({"controle": _check(mid, wanted)})


@api.post("/bestand/<mid>/commons/controle")
def check_before_upload_post(mid):
    """Deprecated (0.29.0): GET …/commons/controle?objecten=pagina:id,…"""
    g.successor = f"{request.script_root}/api/v1/bestand/{mid}/commons/controle"
    return jsonify({"controle": _check(mid, _body().get("objecten"))})


def _check(mid, wanted):
    file = _file(mid)
    saved = _saved_objects(file)
    if wanted is not None:
        if not isinstance(wanted, list):
            raise DetectionError("'objecten' moet een lijst zijn.", status=400, code="invalid_body")
        keys = {(int(_number(w.get("pagina", 1), "pagina")), str(w.get("id"))) for w in wanted if isinstance(w, dict)}
        saved = [(n, o) for n, o in saved if (n, o["id"]) in keys]
    concepts, sha1s = {}, {}
    for n, obj in saved:
        c = concept.concept(file, obj)
        if wanted is None and not c["gekozen"]:
            continue
        concepts[obj["id"]] = c
        data = _service().saved_file(file, n, obj["id"], c["formaat"])
        sha1s[obj["id"]] = hashlib.sha1(data).hexdigest()
    if not concepts:
        raise DetectionError("Er is niets om te controleren: sla eerst uitsneden op en vink ze aan.", status=400, code="nothing_selected")
    return concept.check(_client(), concepts, sha1s)


@api.post("/bestand/<mid>/commons/uploads")
def create_upload(mid):
    """Upload the chosen cut-outs (phase 2: OAuth, stash, SDC). Requires a
    login, {"bevestigd": true} and COMMONS_UPLOAD=aan."""
    _file(mid)
    if _body().get("bevestigd") is not True:
        raise DetectionError("Bevestig eerst dat je de beschrijving, licentie en rechten hebt gecontroleerd.", status=400, code="not_confirmed")
    if not current_app.config["COMMONS_UPLOAD"]:
        raise DetectionError(
            "Uploaden staat uit (COMMONS_UPLOAD=uit). Kopieer de wikitekst of download de zip.", status=503, code="upload_disabled"
        )
    if not _user():
        raise DetectionError("Log in met je Commons-account om te uploaden.", status=401, code="login_required")
    raise DetectionError("Uploaden naar Commons komt in fase 2.", status=501, code="not_implemented")


@api.get("/uploads/<task>")
def get_upload(task):
    raise DetectionError(f"Upload '{task}' bestaat niet.", status=404)


# -- Saving and export ------------------------------------------------------------------------


@api.post("/bestand/<mid>/pagina/<int:n>/uitsneden")
def create_cutouts(mid, n):
    """Save cut-outs of the given or selected objects, at full resolution."""
    file = _page_file(mid, n)
    return jsonify(_service().save_objects(file, n, _body().get("ids"))), 201


@api.get("/bestand/<mid>/pagina/<int:n>/uitsneden")
def list_cutouts(mid, n):
    file = _page_file(mid, n)
    saved = [_service().public(file, n, o) for o in _service().page_objects(file, n) if o.get("opgeslagen")]
    return jsonify({"aantal": len(saved), "uitsneden": saved})


@api.get("/bestand/<mid>/export")
def export_file(mid):
    """Everything saved for the file: formaat=zip (default, with the wikitext
    per cut-out) or json (file, objects and concepts)."""
    file = _file(mid)
    fmt = request.args.get("formaat", "zip")
    saved = _saved_objects(file)
    if fmt == "json":
        return jsonify(
            {
                "bestand": public_file(file),
                "objecten": [{**_service().public(file, n, o), "pagina": n, "commons": _concept(file, n, o)} for n, o in saved],
            }
        )
    if fmt != "zip":
        raise DetectionError("Formaat moet 'zip' of 'json' zijn (IIIF volgt later).", status=400)
    if not saved:
        raise DetectionError("Voor dit bestand is nog niets opgeslagen. Selecteer objecten en kies Selectie opslaan.", status=404, code="nothing_saved")
    wikitexts = {o["id"]: concept.concept(file, o)["wikitekst"] for _n, o in saved}
    data, _count = export.file_zip(_service()._file_dir(file), wikitexts)
    response = Response(data, mimetype="application/zip")
    response.headers["Content-Disposition"] = f'attachment; filename="{file["mid"]}.zip"'
    return response


# -- Trash and overviews ------------------------------------------------------------------------


def _objects(trash):
    sources = {s for s in (request.args.get("bron") or "").split(",") if s}
    saved = {"1": True, "ja": True, "true": True, "0": False, "nee": False, "false": False}.get(request.args.get("opgeslagen", ""))
    objects = _service().all_objects(sources or None, trash=trash, mid=request.args.get("mid"), saved=saved)
    return jsonify({"aantal": len(objects), "prullenbak": trash, "objecten": objects})


@api.get("/prullenbak")
def trash():
    return _objects(True)


@api.delete("/prullenbak")
def empty_trash():
    """Permanently delete everything in the trash, or only {"objecten": [{"mid", "pagina", "id"}]}."""
    _require_trusted_user()
    targets = _body().get("objecten")
    if targets is not None and not isinstance(targets, list):
        raise DetectionError("'objecten' moet een lijst zijn.", status=400)
    deleted = _service().empty_trash(targets)
    return jsonify({"verwijderd": deleted, "over": len(_service().all_objects(trash=True))})


@api.delete("/prullenbak/<mid>/<int:n>/<object_id>")
def purge_from_trash(mid, n, object_id):
    if not MID.fullmatch(mid):
        raise DetectionError(f"'{mid}' is geen M-id.", status=400, code="invalid_mid")
    file = {"mid": mid}
    service = _service()
    if not service.in_trash(file, n, object_id):
        raise DetectionError(f"Object '{object_id}' staat niet in de prullenbak.", status=404)
    service.purge_object(file, n, object_id)
    return jsonify({"verwijderd": object_id, "over": len(service.all_objects(trash=True))})


@api.get("/objecten")
def all_objects():
    """All objects over all files; filters: bron (comma-separated), mid, opgeslagen."""
    return _objects(False)


def _date_param(value, name):
    if value and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise DetectionError(f"Parameter {name} moet een datum zijn (JJJJ-MM-DD).", status=400)
    return value or None


@api.get("/verbruik")
def usage():
    """Paid calls per day; optional `van` and `tot` (inclusive)."""
    _require_trusted_user()
    usage = _service().verbruik
    summary = usage.summary(_date_param(request.args.get("van"), "van"), _date_param(request.args.get("tot"), "tot"))
    return jsonify({**summary, "vandaag": usage.status(_user()), "logboek": usage.entries()[-500:][::-1]})


@api.get("/verbruik/<datum>")
def usage_day(datum):
    _require_trusted_user()
    entries = _service().verbruik.day(_date_param(datum, "datum"))
    return jsonify(
        {
            "datum": datum,
            "aanroepen": sum(e.get("afbeeldingen", 1) for e in entries),
            "kosten_usd": round(sum(e.get("kosten_usd", 0) for e in entries), 4),
            "logboek": entries,
        }
    )


@api.get("/status")
def get_status():
    return jsonify(
        {
            "versie": __version__,
            "modus": current_app.config["DETECTIE_MODUS"],
            "detector": _service().detector.model,
            "upload": current_app.config["COMMONS_UPLOAD"],
            "gebruiker": _user(),
            "budget": _service().verbruik.status(_user()),
        }
    )


@api.get("/openapi.json")
def get_openapi():
    return jsonify(openapi_spec())
