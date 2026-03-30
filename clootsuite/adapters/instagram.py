"""Instagram platform adapter (skeleton)."""

from typing import Optional

from clootsuite.core.models import Platform

from .base import PlatformAdapter


class InstagramAdapter(PlatformAdapter):
    """Instagram adapter (skeleton - to be implemented)."""

    platform = Platform.INSTAGRAM

    async def authenticate(self) -> str:
        """Perform Instagram OAuth authentication.

        Raises:
            NotImplementedError: Instagram authentication not yet implemented.
        """
        raise NotImplementedError(
            "Instagram authentication is not yet implemented. "
            "Coming soon with Meta Graph API."
        )

    async def upload_video(
        self,
        video_path: str,
        caption: str,
        hashtags: Optional[list[str]] = None,
    ) -> str:
        """Upload video to Instagram.

        Args:
            video_path: Path to video file.
            caption: Post caption.
            hashtags: Optional list of hashtags.

        Raises:
            NotImplementedError: Instagram upload not yet implemented.
        """
        raise NotImplementedError(
            "Instagram video upload is not yet implemented. "
            "Coming soon with Meta Graph API."
        )

    async def refresh_token(self) -> str:
        """Refresh Instagram access token.

        Raises:
            NotImplementedError: Instagram token refresh not yet implemented.
        """
        raise NotImplementedError(
            "Instagram token refresh is not yet implemented. "
            "Coming soon with Meta Graph API."
        )
