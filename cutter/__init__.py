"""Commons Mineventory: detect and cut out objects in images on Wikimedia Commons (experiment)."""

__version__ = "0.40.5"


def create_app(config=None, commons_client=None, detector=None, vision=None, image_editor=None):
    """Flask application factory.

    `config` (a Config), `commons_client`, `detector` and `vision` (the
    vision-language model) can be injected for tests.
    """
    import secrets

    from flask import Flask

    from .aanvulling import CompletionService, make_image_editor
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
    # Without FLASK_SECRET_KEY: a random key per process (sessions do not survive a
    # restart), never a fixed one that anybody could use to sign a session cookie.
    app.secret_key = config.FLASK_SECRET_KEY or secrets.token_hex(32)
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
    app.extensions["detectiedienst"] = service = DetectionService(
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
    service.keep_cutout_days = config.BEWAAR_UITSNEDEN_DAGEN
    app.extensions["beschrijvingsdienst"] = DescriptionService(
        vision or make_vision(app.config), app.extensions["detectiedienst"], app.config, config.CACHE_DIR
    )
    # The AI-completed version of a cut-out (Muse Image, 7.7): never a source, never to Commons as a cut-out.
    app.extensions["aanvuldienst"] = CompletionService(image_editor or make_image_editor(app.config), service, config.CACHE_DIR)

    app.register_blueprint(api)
    app.register_blueprint(web)
    _register_commands(app, config)
    return app


def _register_commands(app, config):
    """flask --app app opruimen [--echt]: the cleanup by retention period (12.1);
    on Toolforge a daily `toolforge jobs` task."""
    import click

    @app.cli.command("opruimen")
    @click.option("--echt", is_flag=True, help="Echt verwijderen; zonder deze optie alleen tellen.")
    def cleanup_command(echt):
        """Ruim originelen, uitsneden en cache op volgens de bewaartermijnen."""
        from .opruimen import Cleanup, summary

        click.echo(summary(Cleanup.from_config(config).run(apply=echt)))


def _use_os_trust_store():
    """Use the operating system's certificate store when `truststore` is installed
    (needed behind TLS-inspecting proxies, harmless elsewhere)."""
    try:
        import truststore
    except ImportError:
        return
    truststore.inject_into_ssl()
