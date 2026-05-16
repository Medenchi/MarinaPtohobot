from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = Field(default="", alias="BOT_TOKEN")
    bot_username: str = Field(default="", alias="BOT_USERNAME")

    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_service_role_key: str = Field(default="", alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_anon_key: str = Field(default="", alias="SUPABASE_ANON_KEY")

    storage_bucket_outfits: str = Field(default="outfit-images", alias="STORAGE_BUCKET_OUTFITS")
    storage_bucket_courses: str = Field(default="course-files", alias="STORAGE_BUCKET_COURSES")
    storage_bucket_pdfs: str = Field(default="outfit-pdfs", alias="STORAGE_BUCKET_PDFS")

    public_web_url: str = Field(default="https://marinazau.denchy.cyou", alias="PUBLIC_WEB_URL")
    photographer_website_url: str = Field(
        default="https://zaugolnikova.ru/",
        alias="PHOTOGRAPHER_WEBSITE_URL",
    )
    footer_brand_url: str = Field(default="https://malinacode.is-a.dev", alias="FOOTER_BRAND_URL")

    # Simple password-based admin login (no email/signup).
    admin_password: str = Field(default="", alias="ADMIN_PASSWORD")
    jwt_secret: str = Field(default="change-me-in-production", alias="JWT_SECRET")
    jwt_ttl_hours: int = Field(default=24, alias="JWT_TTL_HOURS")

    cors_origins: str = Field(
        default="http://localhost:5173,https://marinazau.denchy.cyou",
        alias="CORS_ORIGINS",
    )

    # Telegram premium custom emoji IDs (set via @get_emoji_id_robot).
    # Empty values -> bot falls back to plain text labels w/ unicode emoji.
    emoji_obraz: str = Field(default="", alias="EMOJI_OBRAZ")
    emoji_pint: str = Field(default="", alias="EMOJI_PINT")
    emoji_website: str = Field(default="", alias="EMOJI_WEBSITE")
    emoji_download: str = Field(default="", alias="EMOJI_DOWNLOAD")
    emoji_play: str = Field(default="", alias="EMOJI_PLAY")
    emoji_reset: str = Field(default="", alias="EMOJI_RESET")
    emoji_book: str = Field(default="", alias="EMOJI_BOOK")
    emoji_back: str = Field(default="", alias="EMOJI_BACK")
    emoji_sparkles: str = Field(default="", alias="EMOJI_SPARKLES")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
