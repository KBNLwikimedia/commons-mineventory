"""Local entry point: flask --app app run --debug (and npm run dev for the frontend)."""

from dotenv import load_dotenv

load_dotenv()

from cutter import create_app  # noqa: E402  (load .env before reading config)

app = create_app()
