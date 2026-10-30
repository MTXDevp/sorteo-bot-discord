from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Lee de .env en local y de variables de entorno en prod.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    discord_token: str = Field(repr=False)
    command_prefix: str = "!"
    log_level: str = "INFO"

    voice_channel_sorteo: str = "Sorteo"
    voice_channel_evento: str = "Evento"

    data_dir: Path = Path("data")
    sqlite_path: Path = Path("data/sorteo.db")
    legacy_json_path: Path = Path("participaciones.json")

    fuzzy_threshold: int = Field(default=70, ge=0, le=100)
    draw_reveal_delay_seconds: float = Field(default=1.5, ge=0.0, le=30.0)

    @field_validator("command_prefix")
    @classmethod
    def _prefix_no_vacio(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("command_prefix no puede estar vacío")
        return value

    @property
    def resolved_sqlite_path(self) -> Path:
        # acepta ruta relativa o absoluta y se asegura de que exista la carpeta
        path = self.sqlite_path if self.sqlite_path.is_absolute() else Path.cwd() / self.sqlite_path
        path.parent.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
