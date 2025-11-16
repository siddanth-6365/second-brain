"""Supabase authentication helpers"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from backend.config import settings

logger = logging.getLogger(__name__)

_http_bearer = HTTPBearer(auto_error=False)


class AuthenticatedUser(BaseModel):
    """Represents an authenticated Supabase user"""

    id: str
    email: Optional[str] = None
    role: Optional[str] = None
    aud: Optional[str] = None
    app_metadata: Dict[str, Any] = Field(default_factory=dict)
    user_metadata: Dict[str, Any] = Field(default_factory=dict)
    access_token: Optional[str] = None


class SupabaseAuthService:
    """Validates Supabase access tokens and returns user metadata"""

    def __init__(self):
        if not settings.supabase_url or not settings.supabase_anon_key:
            logger.warning(
                "Supabase configuration missing. Authentication will fail until "
                "SUPABASE_URL and SUPABASE_ANON_KEY are configured."
            )

    async def get_user(self, token: str) -> AuthenticatedUser:
        """Fetch the Supabase user associated with the provided JWT"""
        if not token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials")

        if not settings.supabase_url or not settings.supabase_anon_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Supabase authentication is not configured on the server",
            )

        url = settings.supabase_url.rstrip("/") + "/auth/v1/user"
        headers = {
            "Authorization": f"Bearer {token}",
            "apikey": settings.supabase_anon_key,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, headers=headers)
        except httpx.HTTPError as exc:
            logger.error(f"Failed to contact Supabase auth endpoint: {exc}")
            raise HTTPException(status_code=502, detail="Unable to verify credentials with Supabase") from exc

        if response.status_code != 200:
            logger.info("Supabase token rejected with status %s", response.status_code)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired credentials")

        data = response.json()
        user_id = data.get("id")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Supabase user payload")

        return AuthenticatedUser(
            id=user_id,
            email=data.get("email"),
            role=data.get("role"),
            aud=data.get("aud"),
            app_metadata=data.get("app_metadata") or {},
            user_metadata=data.get("user_metadata") or {},
            access_token=token,
        )


_auth_service: Optional[SupabaseAuthService] = None


def get_auth_service() -> SupabaseAuthService:
    """Return singleton SupabaseAuthService"""
    global _auth_service
    if _auth_service is None:
        _auth_service = SupabaseAuthService()
    return _auth_service


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_http_bearer),
) -> AuthenticatedUser:
    """FastAPI dependency that returns the authenticated Supabase user"""
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Authorization header")

    auth_service = get_auth_service()
    return await auth_service.get_user(credentials.credentials)


