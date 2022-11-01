from functools import lru_cache
from typing import Optional

from pydantic import SecretStr, ValidationError
from fastapi import Depends, HTTPException, Request, status, APIRouter, Header
from fastapi.security.api_key import APIKeyHeader
from fastapi.security.utils import get_authorization_scheme_param
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

import foxops.reconciliation as reconciliation
from foxops.database import DAL
from foxops.hosters import Hoster
from foxops.hosters.gitlab import GitLab, GitLabSettings, get_gitlab_settings, get_gitlab_auth_router
from foxops.settings import DatabaseSettings, Settings
from foxops.jwt import JWTError, JWTSettings, TokenData, decode_access_token, get_jwt_settings

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


def get_hoster_token(*,
                     authorization: str = Header(None),
                     jwt_settings: JWTSettings = Depends(get_jwt_settings),
                     ) -> SecretStr:
    scheme, token = get_authorization_scheme_param(authorization)
    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail="Token scheme must be Bearer"
        )
    try:
        token_data: Optional[TokenData] = decode_access_token(jwt_settings, token)
    except (ValidationError, JWTError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail=f"{e}"
        )
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"},
            detail="unknown error"
        )
    return token_data.hoster_token


def get_hoster(
    *,
    settings: GitLabSettings = Depends(get_gitlab_settings),
    hoster_token: SecretStr = Depends(get_hoster_token),
) -> Hoster:
    return GitLab(settings, hoster_token)


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
