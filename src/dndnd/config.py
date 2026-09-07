from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="DNDND_", extra="ignore"
    )

    database_url: str = "sqlite:///data/dndnd.db"
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3:8b"
    request_timeout_seconds: float = 180.0

    def ensure_local_directories(self) -> None:
        prefix = "sqlite:///"
        if self.database_url.startswith(prefix):
            Path(self.database_url.removeprefix(prefix)).parent.mkdir(
                parents=True, exist_ok=True
            )


@lru_cache
def get_settings() -> Settings:
    return Settings()
