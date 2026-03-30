"""Tests for ClootSuite core models."""

import pytest

from clootsuite.core.models import Credentials, Platform, PostRequest, PostResult


class TestPlatform:
    """Tests for Platform enum."""

    def test_platform_values(self) -> None:
        """Test that all expected platforms exist."""
        assert Platform.TIKTOK.value == "tiktok"
        assert Platform.INSTAGRAM.value == "instagram"
        assert Platform.X.value == "x"

    def test_platform_from_string(self) -> None:
        """Test creating Platform from string."""
        assert Platform("tiktok") == Platform.TIKTOK
        assert Platform("instagram") == Platform.INSTAGRAM
        assert Platform("x") == Platform.X


class TestCredentials:
    """Tests for Credentials model."""

    def test_credentials_creation(self) -> None:
        """Test creating credentials."""
        creds = Credentials(
            platform=Platform.TIKTOK,
            access_token="test_token_123",
        )
        assert creds.platform == Platform.TIKTOK
        assert creds.access_token == "test_token_123"
        assert creds.refresh_token is None

    def test_credentials_with_refresh_token(self) -> None:
        """Test credentials with refresh token."""
        creds = Credentials(
            platform=Platform.TIKTOK,
            access_token="access_123",
            refresh_token="refresh_456",
            expires_at=1234567890,
        )
        assert creds.refresh_token == "refresh_456"
        assert creds.expires_at == 1234567890

    def test_credentials_json_serialization(self) -> None:
        """Test JSON serialization of credentials."""
        creds = Credentials(
            platform=Platform.INSTAGRAM,
            access_token="test_token",
            refresh_token="refresh_token",
        )
        json_str = creds.model_dump_json()
        assert "test_token" in json_str
        assert "refresh_token" in json_str

    def test_credentials_json_deserialization(self) -> None:
        """Test JSON deserialization of credentials."""
        json_data = {
            "platform": "tiktok",
            "access_token": "token_abc",
            "refresh_token": "refresh_xyz",
        }
        creds = Credentials(**json_data)
        assert creds.platform == Platform.TIKTOK
        assert creds.access_token == "token_abc"


class TestPostRequest:
    """Tests for PostRequest model."""

    def test_post_request_basic(self) -> None:
        """Test basic post request creation."""
        req = PostRequest(
            video_path="/path/to/video.mp4",
            caption="Test caption",
            platforms=[Platform.TIKTOK],
        )
        assert req.video_path == "/path/to/video.mp4"
        assert req.caption == "Test caption"
        assert req.platforms == [Platform.TIKTOK]

    def test_post_request_multiple_platforms(self) -> None:
        """Test post request with multiple platforms."""
        req = PostRequest(
            video_path="/path/to/video.mp4",
            caption="Multi-platform post",
            platforms=[Platform.TIKTOK, Platform.INSTAGRAM, Platform.X],
        )
        assert len(req.platforms) == 3

    def test_post_request_with_hashtags(self) -> None:
        """Test post request with hashtags."""
        req = PostRequest(
            video_path="/path/to/video.mp4",
            caption="Hashtag test",
            platforms=[Platform.TIKTOK],
            hashtags=["gaming", "fun", "viral"],
        )
        assert req.hashtags == ["gaming", "fun", "viral"]

    def test_post_request_default_hashtags(self) -> None:
        """Test post request with default None hashtags."""
        req = PostRequest(
            video_path="/path/to/video.mp4",
            caption="No hashtags",
            platforms=[Platform.INSTAGRAM],
        )
        assert req.hashtags is None


class TestPostResult:
    """Tests for PostResult model."""

    def test_post_result_success(self) -> None:
        """Test successful post result."""
        result = PostResult(
            platform=Platform.TIKTOK,
            success=True,
            post_id="abc123",
        )
        assert result.platform == Platform.TIKTOK
        assert result.success is True
        assert result.post_id == "abc123"
        assert result.error is None

    def test_post_result_failure(self) -> None:
        """Test failed post result."""
        result = PostResult(
            platform=Platform.INSTAGRAM,
            success=False,
            error="Authentication failed",
        )
        assert result.platform == Platform.INSTAGRAM
        assert result.success is False
        assert result.post_id is None
        assert result.error == "Authentication failed"

    def test_post_result_default_error_none(self) -> None:
        """Test that error defaults to None."""
        result = PostResult(
            platform=Platform.X,
            success=True,
            post_id="xyz789",
        )
        assert result.error is None
