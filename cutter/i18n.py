"""Interface languages (functional design 3): Dutch and English, from the
translation files in frontend/i18n/, shared by the Jinja templates and the Vue
components. The language follows, in this order: ?uselang= in the URL, the
user's choice (kept in the session), the browser's language, else English.
"""

import json
import re
from functools import lru_cache

from .config import ROOT_DIR

LANGUAGES = ("nl", "en")
DEFAULT = "en"
I18N_DIR = ROOT_DIR / "frontend" / "i18n"


@lru_cache(maxsize=None)
def _load(language, mtime):
    return json.loads((I18N_DIR / f"{language}.json").read_text(encoding="utf-8"))


def messages(language):
    """All texts of a language (reloaded when the file changes)."""
    path = I18N_DIR / f"{language}.json"
    return _load(language, path.stat().st_mtime)


def choose(args, session, accept_languages):
    """The interface language for a request; a ?uselang= is remembered."""
    wanted = (args.get("uselang") or "").lower()
    if wanted in LANGUAGES:
        session["taal"] = wanted
        return wanted
    if session.get("taal") in LANGUAGES:
        return session["taal"]
    for language, _quality in accept_languages:
        code = language.lower().split("-")[0]
        if code in LANGUAGES:
            return code
    return DEFAULT


def translate(language, key, **params):
    """The text for `key`, with {name} placeholders filled in; the key itself
    when it is missing (so a missing text shows up, instead of an empty spot)."""
    text = messages(language).get(key)
    if text is None:
        text = messages(DEFAULT).get(key, key)
    return re.sub(r"\{(\w+)\}", lambda m: str(params.get(m.group(1), m.group(0))), text)
