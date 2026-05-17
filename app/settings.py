"""Application settings. Loaded from environment / .env."""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core
    app_name: str = "bato-learning"
    log_level: str = "info"

    # Persistence
    database_url: str = "sqlite+aiosqlite:///./data/learning.db"
    content_dir: Path = Path("app/content")

    # Tutor LLM (DeepSeek, OpenAI-compatible API)
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    deepseek_max_tokens: int = 1024

    # Legacy Anthropic settings (kept for the cached field name; safe to ignore if empty)
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"
    anthropic_max_tokens: int = 1024
    anthropic_cache_ttl: str = "1h"

    # Tutor behavior
    chat_max_history_messages: int = 12
    chat_max_input_tokens: int = 12_000

    # Auth
    session_secret_key: str = "dev-only-change-in-prod-please"
    session_cookie_name: str = "bato_session"
    session_max_age_seconds: int = 60 * 60 * 24 * 30  # 30 days

    # Single-user identity (legacy default; new users created via /auth/register)
    default_user_name: str = "tú"


settings = Settings()
