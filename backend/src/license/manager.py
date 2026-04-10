"""License token caching and verification."""

import json
from pathlib import Path
from typing import Optional
from src.auth.cloud_auth import CloudAuthClient
from src.config import get_settings

settings = get_settings()


class LicenseManager:
    """Manages license token caching and verification."""

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.token_file = vault_path / settings.license_token_path
        self.cloud_client = CloudAuthClient()
        self._cached_token: Optional[str] = None
        self._cached_data: Optional[dict] = None

    def load_token(self) -> Optional[str]:
        """Load license token from local cache."""
        if self._cached_token:
            return self._cached_token

        if not self.token_file.exists():
            return None

        try:
            data = json.loads(self.token_file.read_text())
            self._cached_token = data.get('token')
            self._cached_data = data
            return self._cached_token
        except (json.JSONDecodeError, IOError):
            return None

    def save_token(self, token: str, user_data: dict) -> None:
        """Save license token to local cache."""
        self._cached_token = token
        self._cached_data = {**user_data, 'token': token}

        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        self.token_file.write_text(json.dumps(self._cached_data, indent=2))

    def clear_token(self) -> None:
        """Clear cached license token."""
        self._cached_token = None
        self._cached_data = None
        if self.token_file.exists():
            self.token_file.unlink()

    async def verify(self, offline_grace_period_hours: int = 24) -> Optional[dict]:
        """Verify license with cloud API.

        Returns license data if valid, None if invalid.
        Uses cached data if cloud is unreachable within grace period.
        """
        token = self.load_token()
        if not token:
            return None

        try:
            result = await self.cloud_client.verify_license(token)

            if result.get('valid'):
                # Update cache with fresh data
                self._cached_data = {
                    **self._cached_data,
                    'user': result.get('user'),
                    'tier': result.get('tier'),
                    'limits': result.get('limits')
                }
                return self._cached_data
            else:
                # License invalid - clear cache
                self.clear_token()
                return None

        except Exception as e:
            # Cloud unreachable - check grace period
            if self._cached_data:
                # TODO: Implement grace period check based on last verified time
                # For now, allow offline use
                return self._cached_data
            return None

    async def refresh(self) -> bool:
        """Refresh license data from cloud."""
        return await self.verify() is not None
