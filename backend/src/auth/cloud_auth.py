"""Cloud API authentication client for local app."""

import httpx
from src.config import get_settings

settings = get_settings()


class CloudAuthClient:
    """Client for communicating with cloud authentication API."""

    def __init__(self):
        self.base_url = settings.cloud_api_url.rstrip('/')
        self.timeout = 10.0

    async def login(
        self,
        email: str,
        password: str,
        device_name: str | None = None,
        device_id: str | None = None
    ) -> dict:
        """Login via cloud API and return tokens."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            payload = {
                "email": email,
                "password": password,
                "device_name": device_name,
                "device_id": device_id
            }

            response = await client.post(
                f"{self.base_url}/api/auth/login",
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def verify_license(self, token: str) -> dict:
        """Verify license token with cloud API."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/license/verify",
                json={"token": token}
            )
            response.raise_for_status()
            return response.json()

    async def get_usage(self, token: str) -> dict:
        """Get current usage statistics."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/api/usage/current",
                json={"token": token}
            )
            response.raise_for_status()
            return response.json()
