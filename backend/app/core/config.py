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
    # Telegram id of the bot owner (Denis). Used to deliver flow previews
    # from the constructor's "Test" button.
    bot_owner_telegram_id: int = Field(default=0, alias="BOT_OWNER_TELEGRAM_ID")

    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_service_role_key: str = Field(default="", alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_anon_key: str = Field(default="", alias="SUPABASE_ANON_KEY")

    storage_bucket_outfits: str = Field(default="outfit-images", alias="STORAGE_BUCKET_OUTFITS")
    storage_bucket_courses: str = Field(default="course-files", alias="STORAGE_BUCKET_COURSES")
    storage_bucket_pdfs: str = Field(default="outfit-pdfs", alias="STORAGE_BUCKET_PDFS")

    public_web_url: str = Field(default="https://marinazau.denchy.cyou", alias="PUBLIC_WEB_URL")
    booking_url: str = Field(default="https://zaugolnikova.ru/", alias="BOOKING_URL")
    footer_brand_url: str = Field(default="https://malinacode.is-a.dev", alias="FOOTER_BRAND_URL")
    brand_name: str = Field(default="Marina Photo", alias="BRAND_NAME")

    # Constructor (Denis) vs content (Marina). Two separate passwords.
    admin_password: str = Field(default="", alias="ADMIN_PASSWORD")
    mama_password: str = Field(default="", alias="MAMA_PASSWORD")
    jwt_secret: str = Field(default="change-me-in-production", alias="JWT_SECRET")
    jwt_ttl_hours: int = Field(default=24, alias="JWT_TTL_HOURS")

    cors_origins: str = Field(
        default="http://localhost:5173,https://marinazau.denchy.cyou",
        alias="CORS_ORIGINS",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
