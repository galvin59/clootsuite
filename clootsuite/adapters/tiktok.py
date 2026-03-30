"""TikTok platform adapter with OAuth2 and Content Posting API v2."""

import asyncio
import hashlib
import secrets
import time
import webbrowser
from typing import Optional
from urllib.parse import urlencode, parse_qs, urlparse

import httpx

from clootsuite.config import settings
from clootsuite.core.auth_manager import AuthManager
from clootsuite.core.models import Credentials, Platform
from clootsuite.oauth.server import OAuthCallbackServer

from .base import PlatformAdapter


class TikTokAdapter(PlatformAdapter):
    """TikTok adapter for OAuth2 authentication and video publishing."""

    platform = Platform.TIKTOK

    # TikTok API endpoints
    OAUTH_AUTHORIZE_URL = "https://www.tiktok.com/v2/auth/authorize/"
    OAUTH_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
    API_BASE_URL = "https://open.tiktokapis.com/v2"

    def __init__(self) -> None:
        """Initialize TikTok adapter."""
        self.client_key = settings.tiktok_client_key
        self.client_secret = settings.tiktok_client_secret
        self.redirect_uri = settings.tiktok_redirect_uri
        self.sandbox_mode = settings.tiktok_sandbox_mode

    async def authenticate(self) -> str:
        """Perform TikTok OAuth2 authentication flow.

        Uses manual copy-paste of redirect URL since TikTok
        does not allow localhost redirect URIs.

        Returns:
            Access token.

        Raises:
            RuntimeError: If authentication fails.
        """
        # Generate PKCE code_verifier and code_challenge
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = hashlib.sha256(code_verifier.encode("ascii")).hexdigest()

        # Build authorization URL
        auth_params = {
            "client_key": self.client_key,
            "scope": "user.info.basic,video.upload,video.publish",
            "response_type": "code",
            "redirect_uri": self.redirect_uri,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        auth_url = f"{self.OAUTH_AUTHORIZE_URL}?{urlencode(auth_params)}"

        # Open browser for user to authorize
        webbrowser.open(auth_url)

        # Ask user to paste the redirect URL after authorization
        print("\nAfter authorizing, you will be redirected to a page that may not load.")
        print("Copy the FULL URL from your browser's address bar and paste it here.\n")
        redirect_url = input("Paste the redirect URL here: ").strip()

        # Extract authorization code from URL
        parsed = urlparse(redirect_url)
        query_params = parse_qs(parsed.query)
        auth_code = query_params.get("code", [None])[0]

        if not auth_code:
            raise RuntimeError(
                "No authorization code found in URL. "
                "Make sure you copied the full URL after authorizing."
            )

        # Exchange code for token
        token_response = await self._exchange_code_for_token(auth_code, code_verifier)
        access_token = token_response["access_token"]

        # Store credentials
        credentials = Credentials(
            platform=self.platform,
            access_token=access_token,
            refresh_token=token_response.get("refresh_token"),
            expires_at=token_response.get("expires_in"),
        )
        AuthManager.store_credentials(credentials)

        return access_token

    async def _exchange_code_for_token(self, code: str, code_verifier: str) -> dict:
        """Exchange authorization code for access token.

        Args:
            code: Authorization code from OAuth callback.
            code_verifier: PKCE code verifier.

        Returns:
            Token response dict with access_token.

        Raises:
            RuntimeError: If token exchange fails.
        """
        payload = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "code_verifier": code_verifier,
            "redirect_uri": self.redirect_uri,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.OAUTH_TOKEN_URL,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        if response.status_code != 200:
            raise RuntimeError(f"Token exchange failed: {response.text}")

        body = response.json()

        # TikTok v2 wraps response in "data" key
        if "data" in body:
            return body["data"]

        return body

    async def upload_video(
        self,
        video_path: str,
        caption: str,
        hashtags: Optional[list[str]] = None,
    ) -> str:
        """Upload video to TikTok using Content Posting API v2.

        Args:
            video_path: Path to video file.
            caption: Post caption.
            hashtags: Optional list of hashtags.

        Returns:
            Post ID.

        Raises:
            RuntimeError: If upload fails.
        """
        # Retrieve credentials
        credentials = AuthManager.retrieve_credentials(self.platform)
        if not credentials:
            raise RuntimeError("No TikTok credentials found. Run 'cloot auth login tiktok'")

        access_token = credentials.access_token

        # Build caption with hashtags
        full_caption = caption
        if hashtags:
            full_caption += " " + " ".join(f"#{tag}" for tag in hashtags)

        import os
        video_size = os.path.getsize(video_path)

        # Step 1: Initialize video upload (Direct Post)
        init_response = await self._init_video_upload(
            access_token=access_token,
            caption=full_caption,
            video_size=video_size,
        )
        upload_url = init_response["upload_url"]
        publish_id = init_response["publish_id"]

        # Step 2: Upload video file in chunks
        await self._upload_video_chunks(
            video_path=video_path,
            upload_url=upload_url,
            video_size=video_size,
        )

        # Step 3: Check publish status
        post_id = await self._check_publish_status(
            access_token=access_token,
            publish_id=publish_id,
        )

        return post_id

    async def _init_video_upload(
        self,
        access_token: str,
        caption: str,
        video_size: int,
    ) -> dict:
        """Initialize video upload session via Direct Post.

        Args:
            access_token: OAuth access token.
            caption: Post caption.
            video_size: Size of video file in bytes.

        Returns:
            Response dict with upload_url and publish_id.

        Raises:
            RuntimeError: If initialization fails.
        """
        url = f"{self.API_BASE_URL}/post/publish/video/init/"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        # Calculate chunk count (max 64MB per chunk)
        chunk_size = 10 * 1024 * 1024  # 10MB
        total_chunk_count = max(1, -(-video_size // chunk_size))  # ceiling division

        payload = {
            "post_info": {
                "title": caption[:150],
                "privacy_level": "SELF_ONLY",
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": min(chunk_size, video_size),
                "total_chunk_count": total_chunk_count,
            },
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            raise RuntimeError(f"Video init failed ({response.status_code}): {response.text}")

        body = response.json()
        if body.get("error", {}).get("code", "ok") != "ok":
            raise RuntimeError(f"Video init error: {body['error']}")

        return body["data"]

    async def _upload_video_chunks(
        self,
        video_path: str,
        upload_url: str,
        video_size: int,
    ) -> None:
        """Upload video file in chunks to presigned URL.

        Args:
            video_path: Path to video file.
            upload_url: Presigned upload URL.
            video_size: Total size of video file in bytes.

        Raises:
            RuntimeError: If upload fails.
        """
        chunk_size = 10 * 1024 * 1024  # 10MB chunks

        with open(video_path, "rb") as f:
            offset = 0
            while offset < video_size:
                chunk = f.read(chunk_size)
                if not chunk:
                    break

                end = offset + len(chunk) - 1
                headers = {
                    "Content-Range": f"bytes {offset}-{end}/{video_size}",
                    "Content-Type": "video/mp4",
                }

                async with httpx.AsyncClient(timeout=120) as client:
                    response = await client.put(
                        upload_url,
                        content=chunk,
                        headers=headers,
                    )

                if response.status_code not in (200, 201, 202, 204, 206):
                    raise RuntimeError(
                        f"Chunk upload failed: {response.status_code} {response.text}"
                    )

                offset += len(chunk)

    async def _check_publish_status(
        self,
        access_token: str,
        publish_id: str,
    ) -> str:
        """Check publish status after upload.

        With Direct Post, publishing happens automatically after upload.
        This polls the status endpoint to confirm.

        Args:
            access_token: OAuth access token.
            publish_id: Publish ID from init.

        Returns:
            Publish ID (used as post reference).

        Raises:
            RuntimeError: If publish fails.
        """
        url = f"{self.API_BASE_URL}/post/publish/status/fetch/"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        payload = {"publish_id": publish_id}

        # Poll for up to 60 seconds
        for _ in range(12):
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)

            if response.status_code != 200:
                raise RuntimeError(f"Status check failed: {response.text}")

            body = response.json()
            if body.get("error", {}).get("code", "ok") != "ok":
                raise RuntimeError(f"Publish error: {body['error']}")

            status = body.get("data", {}).get("status", "")

            if status == "PUBLISH_COMPLETE":
                return publish_id
            elif status in ("FAILED", "PUBLISH_FAILED"):
                fail_reason = body.get("data", {}).get("fail_reason", "unknown")
                raise RuntimeError(f"Publish failed: {fail_reason}")

            # Wait before polling again
            await asyncio.sleep(5)

        # If still processing after 60s, return publish_id anyway
        return publish_id

    async def refresh_token(self) -> str:
        """Refresh TikTok access token.

        Returns:
            New access token.

        Raises:
            RuntimeError: If refresh fails.
        """
        credentials = AuthManager.retrieve_credentials(self.platform)
        if not credentials or not credentials.refresh_token:
            raise RuntimeError("No refresh token available")

        payload = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "refresh_token": credentials.refresh_token,
            "grant_type": "refresh_token",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self.OAUTH_TOKEN_URL, json=payload)

        if response.status_code != 200:
            raise RuntimeError(f"Token refresh failed: {response.text}")

        token_response = response.json()
        new_access_token = token_response["access_token"]

        # Update stored credentials
        AuthManager.update_access_token(
            self.platform,
            new_access_token,
            token_response.get("refresh_token"),
            token_response.get("expires_in"),
        )

        return new_access_token
