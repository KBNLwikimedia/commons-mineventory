"""The one HTTP client for the Meta Model API, shared by SAM (meta_sam.py),
Muse Spark (beschrijving.py) and Muse Image (aanvulling.py).

It posts JSON with the API key and maps every failure to a DetectionError.
The texts that differ per caller (no key, a refused request, too many
requests) are passed in, so each caller keeps its own messages.
"""

import requests

from .basis import DetectionError


class MetaClient:
    def __init__(self, api_key, base_url="https://api.meta.ai/v1", timeout=90, session=None):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()

    def post(self, path, body, model, no_key, no_key_code=None, refused="Het model weigerde het verzoek", busy=None):
        """POST `body` to `path` (e.g. "/responses"); returns the response on HTTP 200.

        `no_key` (+ `no_key_code`) is the message without an API key, `refused`
        the prefix for HTTP 400, `busy` the message for HTTP 429 (default:
        "too many requests to '<model>'")."""
        if not self.api_key:
            raise DetectionError(no_key, status=503, code=no_key_code)
        try:
            response = self.session.post(
                f"{self.base_url}{path}",
                json=body,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise DetectionError("De Meta Model API is niet bereikbaar.", retry=True) from exc
        status = response.status_code
        if status == 200:
            return response
        try:
            detail = (response.json().get("error") or {}).get("message", "")
        except ValueError:
            detail = ""
        if status == 400:
            raise DetectionError(f"{refused}: {detail}".rstrip(": "), status=400)
        if status in (401, 403):
            raise DetectionError("De API-sleutel voor de Meta Model API wordt niet geaccepteerd.", status=503)
        if status == 404:
            raise DetectionError(f"Model '{model}' niet gevonden of geen toegang.", status=503)
        if status == 429:
            busy = busy or f"Te veel verzoeken aan '{model}'; probeer het zo opnieuw."
            raise DetectionError(busy, status=429, retry=True)
        raise DetectionError(f"De Meta Model API gaf een fout (HTTP {status}).", retry=True)
