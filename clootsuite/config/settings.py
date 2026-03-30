"""Pydantic settings for ClootSuite configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Settings loaded from environment variables."""

    # TikTok configuration
    tiktok_client_key: str
    tiktok_client_secret: str
    tiktok_sandbox_mode: bool = True
    tiktok_redirect_uri: str = "http://localhost:8080/callback"

    # Meta/Instagram configuration
    meta_app_id: str
    meta_app_secret: str
    meta_redirect_uri: str = "http://localhost:8080/callback"

    # X/Twitter configuration
    x_client_id: str
    x_client_secret: str
    x_redirect_uri: str = "http://localhost:8080/callback"

    # Server configuration
    oauth_callback_port: int = 8080

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
