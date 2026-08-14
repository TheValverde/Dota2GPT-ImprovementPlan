from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    opendota_api_key: str | None = None
    opendota_base_url: str = "https://api.opendota.com/api"
    host: str = "0.0.0.0"
    port: int = 8765
    data_dir: str | None = Field(
        default=None,
        validation_alias=AliasChoices("DOTA2_COACH_DATA", "DATA_DIR"),
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
