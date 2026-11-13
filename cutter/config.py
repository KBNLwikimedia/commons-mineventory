"""Configuration, read exclusively from environment variables (see .env.example).

Settings an administrator may change later in the admin panel (limits,
retention, the Contributor switch; functional design 8.4) are only the
starting values here.
"""

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def _env(name, default=None):
    value = os.environ.get(name)
    return value if value not in (None, "") else default


def _env_int(name, default):
    return int(_env(name, default))


def _env_float(name, default):
    return float(_env(name, default))


def _env_bool(name, default):
    return str(_env(name, default)).lower() in ("aan", "ja", "1", "true", "on")


def _env_list(name, default=""):
    return [part.strip() for part in str(_env(name, default)).split(",") if part.strip()]


class Config:
    """Snapshot of the environment at app start-up."""

    def __init__(self):
        # Detection: dummy (phase 1) or live (Meta Model API, only on Olaf's instruction).
        self.DETECTIE_MODUS = _env("DETECTIE_MODUS", "dummy")
        self.MODEL_API_KEY = _env("MODEL_API_KEY")
        self.META_API_BASE = _env("META_API_BASE", "https://api.meta.ai/v1")
        self.SAM_MODEL = _env("SAM_MODEL", "sam-3.1")

        # Limits (functional design 6.4); starting values for the admin panel.
        self.DAGLIMIET_AANROEPEN = _env_int("DAGLIMIET_AANROEPEN", 500)
        self.DAGLIMIET_PER_GEBRUIKER = _env_int("DAGLIMIET_PER_GEBRUIKER", 100)
        self.DAGBUDGET_USD = _env_float("DAGBUDGET_USD", 2.0)

        # Description by Muse Spark (functional design 6.2 and 6.3). Contributor
        # only for public-domain files without rights signals, and only when on.
        self.BEELDMODEL = _env("BEELDMODEL", "muse-spark-1.3")
        self.BEELDMODEL_RECHTENVRIJ = _env("BEELDMODEL_RECHTENVRIJ", "muse-spark-1.3-contributor")
        self.BEELDMODEL_CONTRIBUTOR = _env_bool("BEELDMODEL_CONTRIBUTOR", "aan")
        # Medium by default (wish Olaf 13-11-2026): the descriptions are better, for a little more.
        self.BEELDMODEL_REDENEREN = _env("BEELDMODEL_REDENEREN", "medium")

        # Wikimedia Commons (read-only in phase 1).
        self.COMMONS_API = _env("COMMONS_API", "https://commons.wikimedia.org/w/api.php")
        self.WIKIDATA_API = _env("WIKIDATA_API", "https://www.wikidata.org/w/api.php")
        self.COMMONS_MIN_INTERVAL = _env_float("COMMONS_MIN_INTERVAL", 1.0)
        self.COMMONS_TIMEOUT = _env_float("COMMONS_TIMEOUT", 60.0)
        self.COMMONS_CACHE_SECONDEN = _env_int("COMMONS_CACHE_SECONDEN", 86400)
        self.COMMONS_USER_AGENT = _env(
            "COMMONS_USER_AGENT",
            "CommonsMineventory/0.1 (https://github.com/KBNLwikimedia/commons-mineventory; experiment) python-requests",
        )
        self.COMMONS_UPLOAD = _env_bool("COMMONS_UPLOAD", "uit")
        self.MAX_MEGAPIXELS = _env_int("MAX_MEGAPIXELS", 100)

        # Access (phase 2: OAuth and the admin panel; starting values only).
        self.TOEGESTANE_GEBRUIKERS = _env_list("TOEGESTANE_GEBRUIKERS", "OlafJanssen")
        self.BEHEERDERS_START = _env_list("BEHEERDERS_START", "OlafJanssen")
        self.FLASK_SECRET_KEY = _env("FLASK_SECRET_KEY")
        # Until OAuth (phase 2): a Commons user name that counts as logged in,
        # only when Flask runs in debug mode on your own machine.
        self.LOKALE_GEBRUIKER = _env("LOKALE_GEBRUIKER")

        # Retention (functional design 12.1), counted from the last use.
        self.BEWAAR_ORIGINELEN_DAGEN = _env_int("BEWAAR_ORIGINELEN_DAGEN", 7)
        self.BEWAAR_UITSNEDEN_DAGEN = _env_int("BEWAAR_UITSNEDEN_DAGEN", 30)
        self.BEWAAR_CACHE_DAGEN = _env_int("BEWAAR_CACHE_DAGEN", 365)

        # Storage.
        self.CACHE_DIR = Path(_env("CACHE_DIR", ROOT_DIR / "cache"))
        self.UITVOER_DIR = Path(_env("UITVOER_DIR", ROOT_DIR / "uitvoer"))

        # Frontend: the Vite dev server (development) or static/dist (built).
        # VITE_DEV: auto (dev server in debug mode when it runs), aan or uit.
        self.VITE_DEV = _env("VITE_DEV", "auto")
        self.VITE_DEV_SERVER = _env("VITE_DEV_SERVER", "http://localhost:5173")

        # Links in the footer.
        self.BRONCODE_URL = _env("BRONCODE_URL", "https://github.com/KBNLwikimedia/commons-mineventory")
        self.PROJECTSITE_URL = _env("PROJECTSITE_URL", "https://kbnlwikimedia.github.io/commons-mineventory/")

    def as_flask_config(self):
        return {k: v for k, v in vars(self).items() if k.isupper()}
