"""Publisher: async orchestrator for multi-platform publishing."""

import asyncio
from typing import Optional

from clootsuite.adapters.base import PlatformAdapter
from clootsuite.adapters.instagram import InstagramAdapter
from clootsuite.adapters.tiktok import TikTokAdapter
from clootsuite.adapters.x import XAdapter

from .models import Platform, PostRequest, PostResult


class Publisher:
    """Orchestrates publishing to multiple platforms in parallel."""

    def __init__(self) -> None:
        """Initialize publisher with platform adapters."""
        self.adapters: dict[Platform, PlatformAdapter] = {
            Platform.TIKTOK: TikTokAdapter(),
            Platform.INSTAGRAM: InstagramAdapter(),
            Platform.X: XAdapter(),
        }

    async def publish(
        self,
        post_request: PostRequest,
    ) -> list[PostResult]:
        """Publish video to multiple platforms in parallel.

        Args:
            post_request: Post request with video, caption, and platforms.

        Returns:
            List of PostResult objects, one per requested platform.
        """
        tasks = []
        for platform in post_request.platforms:
            adapter = self.adapters.get(platform)
            if adapter:
                task = self._publish_to_platform(adapter, post_request)
                tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=False)
        return results

    async def _publish_to_platform(
        self,
        adapter: PlatformAdapter,
        post_request: PostRequest,
    ) -> PostResult:
        """Publish to a single platform.

        Args:
            adapter: Platform adapter instance.
            post_request: Post request.

        Returns:
            PostResult with success/error information.
        """
        try:
            post_id = await adapter.upload_video(
                video_path=post_request.video_path,
                caption=post_request.caption,
                hashtags=post_request.hashtags or [],
            )
            return PostResult(
                platform=adapter.platform,
                success=True,
                post_id=post_id,
            )
        except Exception as e:
            return PostResult(
                platform=adapter.platform,
                success=False,
                error=str(e),
            )
