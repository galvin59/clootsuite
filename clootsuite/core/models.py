"""Core Pydantic models for ClootSuite."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class Platform(str, Enum):
    """Supported social media platforms."""

    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    X = "x"


class Credentials(BaseModel):
    """OAuth credentials for a platform."""

    platform: Platform
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[int] = None

    class Config:
        """Pydantic config."""
        use_enum_values = True


class PostRequest(BaseModel):
    """Request to publish a post across platforms."""

    video_path: str
    caption: str
    platforms: list[Platform]
    hashtags: Optional[list[str]] = None

    class Config:
        """Pydantic config."""
        use_enum_values = True


class PostResult(BaseModel):
    """Result of publishing a post."""

    platform: Platform
    success: bool
    post_id: Optional[str] = None
    error: Optional[str] = None

    class Config:
        """Pydantic config."""
        use_enum_values = True
