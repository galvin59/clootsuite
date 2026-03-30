"""Token management using OS keyring."""

import json
from typing import Optional

import keyring

from .models import Credentials, Platform


class AuthManager:
    """Manages OAuth tokens using OS keyring for secure storage."""

    SERVICE_NAME = "clootsuite"

    @staticmethod
    def _get_keyring_key(platform: Platform) -> str:
        """Generate keyring key for a platform."""
        platform_str = platform.value if isinstance(platform, Platform) else str(platform)
        return f"{AuthManager.SERVICE_NAME}_{platform_str}"

    @staticmethod
    def store_credentials(credentials: Credentials) -> None:
        """Store credentials in OS keyring.

        Args:
            credentials: Credentials object to store.
        """
        key = AuthManager._get_keyring_key(credentials.platform)
        creds_json = credentials.model_dump_json()
        keyring.set_password(AuthManager.SERVICE_NAME, key, creds_json)

    @staticmethod
    def retrieve_credentials(platform: Platform) -> Optional[Credentials]:
        """Retrieve credentials from OS keyring.

        Args:
            platform: Platform to retrieve credentials for.

        Returns:
            Credentials object if found, None otherwise.
        """
        key = AuthManager._get_keyring_key(platform)
        try:
            creds_json = keyring.get_password(AuthManager.SERVICE_NAME, key)
            if creds_json:
                return Credentials(**json.loads(creds_json))
        except Exception:
            pass
        return None

    @staticmethod
    def delete_credentials(platform: Platform) -> None:
        """Delete credentials from OS keyring.

        Args:
            platform: Platform to delete credentials for.
        """
        key = AuthManager._get_keyring_key(platform)
        try:
            keyring.delete_password(AuthManager.SERVICE_NAME, key)
        except Exception:
            pass

    @staticmethod
    def update_access_token(
        platform: Platform,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_at: Optional[int] = None,
    ) -> None:
        """Update access token for a platform.

        Args:
            platform: Platform to update token for.
            access_token: New access token.
            refresh_token: Optional new refresh token.
            expires_at: Optional token expiration timestamp.
        """
        creds = AuthManager.retrieve_credentials(platform)
        if creds:
            creds.access_token = access_token
            if refresh_token:
                creds.refresh_token = refresh_token
            if expires_at:
                creds.expires_at = expires_at
            AuthManager.store_credentials(creds)
