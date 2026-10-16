"""Application settings, read from environment variables."""

import os

DEFAULT_DATABASE_URL = "postgresql+psycopg://stockpilot:stockpilot@localhost:5432/stockpilot"


class Settings:
    app_name: str = os.getenv("APP_NAME", "StockPilot API")
    environment: str = os.getenv("APP_ENV", "local")
    database_url: str = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)
    # Comma-separated list of allowed CORS origins (only needed when the
    # frontend is served from a different origin, e.g. `npm run dev`).
    cors_origins: list[str] = [
        o.strip()
        for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
        if o.strip()
    ]


settings = Settings()
