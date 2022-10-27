from functools import lru_cache
from typing import Optional

from pydantic import SecretStr
from fastapi import Depends, HTTPException, Request, status, APIRouter
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

import foxops.reconciliation as reconciliation
from foxops.database import DAL
from foxops.hosters import Hoster
from foxops.hosters.gitlab import AuthGitLab, GitLabSettings, get_gitlab_settings, get_gitlab_auth_router
from foxops.settings import DatabaseSettings, Settings

# NOTE: Yes, you may absolutely use proper dependency injection at some point.

#: Holds a singleton of the database engine
async_engine: AsyncEngine | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore


@lru_cache
def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings()


def get_dal(settings: DatabaseSettings = Depends(get_database_settings)) -> DAL:
    global async_engine

    if async_engine is None:
        async_engine = create_async_engine(settings.url.get_secret_value(), future=True, echo=False, pool_pre_ping=True)

    return DAL(async_engine)


def get_hoster(request: Request, settings: GitLabSettings = Depends(get_gitlab_settings)) -> Hoster:
    token: str = request.headers.get("Authorization").removeprefix("Bearer")
    return AuthGitLab(settings, SecretStr(token))


def get_hoster_auth_router() -> APIRouter:
    return get_gitlab_auth_router()


def get_reconciliation():
    return reconciliation


class HosterTokenHeaderAuth(APIKeyHeader):
    def __init__(self):
        super().__init__(name="Authorization")

    async def __call__(self, request: Request):
        authorization_header: Optional[str] = await super().__call__(request)
        if not authorization_header:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Authorization header")

        if not authorization_header.startswith("Bearer ") or not authorization_header.removeprefix("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization header must start with 'Bearer ' followed by the token",
            )


hoster_token_auth_scheme: HosterTokenHeaderAuth = HosterTokenHeaderAuth()
