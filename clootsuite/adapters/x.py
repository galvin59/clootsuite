"""X (Twitter) platform adapter (skeleton)."""

from typing import Optional

from clootsuite.core.models import Platform

from .base import PlatformAdapter


class XAdapter(PlatformAdapter):
    """X (Twitter) adapter (skeleton - to be implemented)."""

    platform = Platform.X

    async def authenticate(self) -> str:
        """Perform X OAuth 2.0 authentication.

        Raises:
            NotImplementedError: X authentication not yet implemented.
        """
        raise NotImplementedError(
            "X (Twitter) authentication is not yet implemented. "
            "Coming soon with OAuth 2.0 and v2 API."
        )

    async def upload_video(
        self,
        video_path: str,
        caption: str,
        hashtags: Optional[list[str]] = None,
    ) -> str:
        """Upload video to X.

        Args:
            video_path: Path to video file.
            caption: Post caption.
            hashtags: Optional list of hashtags.

        Raises:
            NotImplementedError: X upload not yet implemented.
        """
        raise NotImplementedError(
            "X video upload is not yet implemented. "
            "Coming soon with v2 API."
        )

    async def refresh_token(self) -> str:
        """Refresh X access token.

        Raises:
            NotImplementedError: X token refresh not yet implemented.
        """
        raise NotImplementedError(
            "X token refresh is not yet implemented. "
            "Coming soon with OAuth 2.0."
        )
