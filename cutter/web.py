"""Server-rendered pages (functional design 10.2): every page is a Jinja
template with places where Vue apps are mounted. No single-page app; every
state keeps its own URL.

The page loads its scripts from the Vite dev server during development (with
hot reload) and from static/dist/ (via Vite's manifest) when built.
"""

import json
import socket
import time
from urllib.parse import urlsplit

from flask import Blueprint, Response, current_app, g, render_template, request, session, url_for
from markupsafe import Markup

from . import __version__, beschrijving, changelog as changelog_parser, i18n, markdown_lite, prompts
from .config import ROOT_DIR

web = Blueprint("web", __name__)

MANIFEST = ROOT_DIR / "static" / "dist" / ".vite" / "manifest.json"
_probe = {"time": 0.0, "up": False}


# -- Vite ------------------------------------------------------------------------------


def _dev_server_up(url):
    """Whether the Vite dev server answers (checked at most every 5 seconds)."""
    now = time.monotonic()
    if now - _probe["time"] < 5:
        return _probe["up"]
    parts = urlsplit(url)
    try:
        with socket.create_connection((parts.hostname, parts.port or 80), timeout=0.2):
            up = True
    except OSError:
        up = False
    _probe.update(time=now, up=up)
    return up


def use_dev_server():
    mode = (current_app.config.get("VITE_DEV") or "auto").lower()
    if mode in ("aan", "ja", "1", "true"):
        return True
    if mode in ("uit", "nee", "0", "false"):
        return False
    if current_app.debug and _dev_server_up(current_app.config["VITE_DEV_SERVER"]):
        return True
    return not MANIFEST.exists()


def _manifest():
    return json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}


def vite_tags(entry):
    """Script and stylesheet tags for a Vite entry (e.g. "frontend/main-index.js")."""
    if use_dev_server():
        base = current_app.config["VITE_DEV_SERVER"].rstrip("/")
        return Markup(
            f'<script type="module" src="{base}/@vite/client"></script>\n'
            f'<script type="module" src="{base}/{entry}"></script>'
        )
    manifest = _manifest()
    chunk = manifest.get(entry)
    if not chunk:
        return Markup(f"<!-- {entry} niet gebouwd: draai npm run build of npm run dev -->")
    css, seen = [], set()

    def collect(name):
        if name in seen or name not in manifest:
            return
        seen.add(name)
        css.extend(manifest[name].get("css", []))
        for imported in manifest[name].get("imports", []):
            collect(imported)

    collect(entry)
    tags = [f'<link rel="stylesheet" href="/static/dist/{href}">' for href in dict.fromkeys(css)]
    tags.append(f'<script type="module" src="/static/dist/{chunk["file"]}"></script>')
    return Markup("\n".join(tags))


# -- Language and globals ----------------------------------------------------------------


@web.before_app_request
def _language():
    g.taal = i18n.choose(request.args, session, request.accept_languages)


def _t(key, **params):
    return i18n.translate(g.get("taal", i18n.DEFAULT), key, **params)


def _language_url(language):
    args = request.args.to_dict()
    args["uselang"] = language
    return url_for(request.endpoint or "web.index", **(request.view_args or {}), **args)


@web.app_context_processor
def _globals():
    return {
        "app_versie": __version__,
        "detectie_modus": current_app.config["DETECTIE_MODUS"],
        "broncode_url": current_app.config["BRONCODE_URL"],
        "taal": g.get("taal", i18n.DEFAULT),
        "talen": i18n.LANGUAGES,
        "taal_url": _language_url,
        "t": _t,
        "vite_tags": vite_tags,
        "vite_dev": use_dev_server(),
        "client_config": _client_config,
    }


def _muse_info():
    config = current_app.config
    effort = config.get("BEELDMODEL_REDENEREN")
    effort = effort if effort in beschrijving.EFFORTS else None
    model = config["BEELDMODEL"]
    cheap = config["BEELDMODEL_RECHTENVRIJ"]
    return {
        "model": model,
        "rechtenvrij_model": cheap,
        "contributor": config["BEELDMODEL_CONTRIBUTOR"],
        "redeneren": effort,
        "beschrijving_usd": beschrijving.estimate(model, effort),
        "pagina_usd": beschrijving.estimate(model, effort, beschrijving.ESTIMATE_PAGE_INPUT),
        "beschrijving_rechtenvrij_usd": beschrijving.estimate(cheap, effort),
    }


def _client_config(page, **extra):
    """What the Vue apps on a page need: language, texts, mode and settings
    (embedded as JSON, so the browser loads nothing from elsewhere)."""
    config = current_app.config
    data = {
        "pagina": page,
        "taal": g.get("taal", i18n.DEFAULT),
        "teksten": i18n.messages(g.get("taal", i18n.DEFAULT)),
        "versie": __version__,
        "modus": config["DETECTIE_MODUS"],
        "betaald": config["DETECTIE_MODUS"] == "live",
        "upload": config["COMMONS_UPLOAD"],
        "sam_model": config["SAM_MODEL"],
        "muse": _muse_info(),
        "snel_zoeken": [
            {"sleutel": key, "label": label, "termen": terms} for key, (label, terms) in prompts.CATEGORIEEN.items()
        ],
        "alles": [{"en": term, "nl": prompts.dutch(term)} for term in prompts.ALLES],
        **extra,
    }
    text = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return Markup(f'<script id="cutter-config" type="application/json">{text}</script>')


# -- Pages ---------------------------------------------------------------------------------


def _start():
    keys = ("url", "titel", "mid", "pagina", "object", "prompt", "modus", "categorie")
    return {key: request.args.get(key, "") for key in keys}


@web.get("/")
def index():
    return render_template("index.html", start=_start())


@web.get("/objecten")
def objects_overview():
    """All saved and detected objects, with facets and the trash (data via the API)."""
    return render_template("objecten.html", titel=_t("objects.title"))


@web.get("/commons")
def commons_menu():
    """The upload menu of one file (9.1): concepts, check, preview."""
    return render_template("commons.html", titel=_t("upload.title"), mid=request.args.get("mid", ""))


@web.get("/verbruik")
def usage():
    """Log of paid calls. Phase 2: only for the access list and administrators (8.3)."""
    return render_template("verbruik.html", titel=_t("usage.title"))


def _markdown_page(path, title):
    text = (ROOT_DIR / path).read_text(encoding="utf-8")
    return render_template("tekstpagina.html", titel=title, inhoud=Markup(markdown_lite.render(text)))


@web.get("/docs")
def docs():
    return _markdown_page("docs/api.md", _t("footer.docs"))


@web.get("/privacy")
def privacy():
    return _markdown_page("docs/privacy.md", _t("footer.privacy"))


@web.get("/changelog")
def changelog():
    text = (ROOT_DIR / "CHANGELOG.md").read_text(encoding="utf-8")
    return render_template(
        "changelog.html", titel=_t("footer.changelog"), changelog=changelog_parser.parse(text), bron_url=url_for("web.changelog_text")
    )


@web.get("/changelog.md")
def changelog_text():
    text = (ROOT_DIR / "CHANGELOG.md").read_text(encoding="utf-8")
    return Response(text, mimetype="text/plain; charset=utf-8")


SITEMAP = (
    ("web.index", "nav.home"),
    ("web.objects_overview", "objects.title"),
    ("web.usage", "usage.title"),
    ("web.docs", "footer.docs"),
    ("api.get_openapi", "footer.api"),
    ("web.changelog", "footer.changelog"),
    ("web.privacy", "footer.privacy"),
)


@web.get("/sitemap")
def sitemap():
    links = [(url_for(endpoint), _t(key)) for endpoint, key in SITEMAP]
    return render_template("sitemap.html", titel=_t("footer.sitemap"), links=links)


@web.get("/sitemap.xml")
def sitemap_xml():
    """Only the public pages; the API and the work pages stay out (robots.txt)."""
    root = request.url_root.rstrip("/")
    urls = "".join(f"<url><loc>{root}{url_for(e)}</loc></url>" for e in ("web.index", "web.docs", "web.changelog", "web.privacy"))
    xml = f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>'
    return Response(xml, mimetype="application/xml")


@web.get("/robots.txt")
def robots():
    """Keep crawlers out of the API (detection can cost money) and the work pages."""
    text = "User-agent: *\nDisallow: /api/\nDisallow: /objecten\nDisallow: /verbruik\nDisallow: /commons\nDisallow: /beheer\n"
    return Response(text, mimetype="text/plain")
