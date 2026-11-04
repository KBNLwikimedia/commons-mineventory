"""Commons Cutter: detect and cut out objects in images on Wikimedia Commons (experiment)."""

__version__ = "0.15.0"


def create_app(config=None, commons_client=None, detector=None, vision=None):
    """Flask application factory.

    `config` (a Config), `commons_client`, `detector` and `vision` (the
    vision-language model) can be injected for tests.
    """
    from flask import Flask

    from .api import api
    from .beschrijving import DescriptionService, make_vision
    from .cache import CachedFetcher, FileCache, RateLimiter
    from .commons import CommonsClient
    from .config import ROOT_DIR, Config
    from .detectie.dienst import DetectionService, make_detector
    from .verbruik import Verbruik
    from .web import web

    config = config or Config()
    app = Flask(
        __name__,
        template_folder=str(ROOT_DIR / "templates"),
        static_folder=str(ROOT_DIR / "static"),
    )
    app.config.update(config.as_flask_config())
    app.secret_key = config.FLASK_SECRET_KEY or "dev-only-not-secret"
    app.json.ensure_ascii = False

    if commons_client is None:
        _use_os_trust_store()
        fetcher = CachedFetcher(
            FileCache(config.CACHE_DIR / "commons"),
            RateLimiter(config.COMMONS_MIN_INTERVAL),
            user_agent=config.COMMONS_USER_AGENT,
            timeout=config.COMMONS_TIMEOUT,
        )
        commons_client = CommonsClient(
            fetcher,
            api=config.COMMONS_API,
            wikidata_api=config.WIKIDATA_API,
            cache_dir=config.CACHE_DIR,
            max_age=config.COMMONS_CACHE_SECONDEN,
            max_megapixels=config.MAX_MEGAPIXELS,
        )
    app.extensions["commons"] = commons_client
    app.extensions["detectiedienst"] = DetectionService(
        detector or make_detector(app.config),
        commons_client,
        config.CACHE_DIR,
        config.UITVOER_DIR,
        Verbruik(
            config.UITVOER_DIR / "verbruik",
            config.DAGLIMIET_AANROEPEN,
            per_user_limit=config.DAGLIMIET_PER_GEBRUIKER,
            daily_budget=config.DAGBUDGET_USD,
        ),
    )
    app.extensions["beschrijvingsdienst"] = DescriptionService(
        vision or make_vision(app.config), app.extensions["detectiedienst"], app.config, config.CACHE_DIR
    )

    app.register_blueprint(api)
    app.register_blueprint(web)
    return app


def _use_os_trust_store():
    """Use the operating system's certificate store when `truststore` is installed
    (needed behind TLS-inspecting proxies, harmless elsewhere)."""
    try:
        import truststore
    except ImportError:
        return
    truststore.inject_into_ssl()
