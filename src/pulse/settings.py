from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = f"sqlite:///{ROOT / 'data' / 'pulse.db'}"
    assets_dir: Path = ROOT / "data" / "assets"
    outbound_dir: Path = ROOT / "outbound"
    brand_file: Path = ROOT / "config" / "brand.yaml"
    calendar_file: Path = ROOT / "config" / "calendar.yaml"
    templates_dir: Path = ROOT / "templates"
    timezone: str = "America/Mexico_City"
    auto_approve: bool = True
    enabled_platforms: str = "webhook,web"
    publish_due: bool = True
    generate_per_cycle: int = 1

    webhook_url: str = ""
    webhook_token: str = ""

    x_api_key: str = ""
    x_api_secret: str = ""
    x_access_token: str = ""
    x_access_token_secret: str = ""

    linkedin_access_token: str = ""
    linkedin_author_urn: str = ""
    linkedin_api_version: str = "202608"

    meta_access_token: str = ""
    instagram_business_id: str = ""
    facebook_page_id: str = ""

    web_publish_endpoint: str = ""
    web_publish_token: str = ""

    def platforms(self) -> list[str]:
        return [p.strip().lower() for p in self.enabled_platforms.split(",") if p.strip()]


def get_settings() -> Settings:
    return Settings()
