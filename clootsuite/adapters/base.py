"""Abstract base class for platform adapters."""

from abc import ABC, abstractmethod
from typing import Optional

from clootsuite.core.models import Platform


class PlatformAdapter(ABC):
    """Abstract base class for social media platform adapters."""

    platform: Platform

    @abstractmethod
    async def authenticate(self) -> str:
        """Perform OAuth authentication flow.

        Returns:
            Access token.
        """
        pass

    @abstractmethod
    async def upload_video(
        self,
        video_path: str,
        caption: str,
        hashtags: Optional[list[str]] = None,
    ) -> str:
        """Upload video to the platform.

        Args:
            video_path: Path to video file.
            caption: Post caption.
            hashtags: Optional list of hashtags.

        Returns:
            Post ID on the platform.
        """
        pass

    @abstractmethod
    async def refresh_token(self) -> str:
        """Refresh OAuth access token.

        Returns:
            New access token.
        """
        pass
