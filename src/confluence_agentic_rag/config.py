"""
Application configuration (env-driven settings).

Loads Confluence settings from environment variables (.env supported).
"""

import os
from dotenv import load_dotenv
from pydantic import BaseModel


load_dotenv()


class Settings(BaseModel):
    """Runtime settings loaded from environment variables."""

    confluence_base_url: str = os.getenv("CONFLUENCE_BASE_URL", "").strip()
    confluence_email: str = os.getenv("CONFLUENCE_EMAIL", "").strip()
    confluence_api_token: str = os.getenv("CONFLUENCE_API_TOKEN", "").strip()
    confluence_space_key: str = os.getenv("CONFLUENCE_SPACE_KEY", "").strip()

    def validate_or_raise(self) -> "Settings":
        """Validate required environment variables and raise a helpful error
        if missing."""
        missing = [k for k, v in self.model_dump().items() if not v]
        if missing:
            raise ValueError(f"Missing env vars: {', '.join(missing)}")
        return self
