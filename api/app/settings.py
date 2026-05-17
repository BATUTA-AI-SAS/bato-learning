from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    database_url: str = "postgresql+psycopg://bato:bato_dev@postgres:5432/bato_learning"
    redis_url: str = "redis://redis:6379/0"
    phoenix_collector_endpoint: str = "http://phoenix:6006/v1/traces"
    temporal_address: str = "temporal:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "audits"


settings = Settings()
