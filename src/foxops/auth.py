from pydantic import BaseModel, SecretStr, ValidationError, EmailStr
from typing import Optional, ClassVar
from fastapi import HTTPException, status, Depends, Header
from fastapi.security import SecurityScopes
from fastapi.security.utils import get_authorization_scheme_param
from aiocache import Cache  # type: ignore

from foxops.models import User
from foxops.jwt import JWTSettings, JWTTokenData, JWTError, get_jwt_settings, decode_jwt_token


class AuthHTTPException(HTTPException):
    def __init__(self, **kwargs):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={'WWW-Authenticate': 'Bearer'},
            **kwargs
        )


class AuthData(BaseModel):
    cache: ClassVar[Optional[Cache]] = None

    user: User
    hoster_token: Optional[SecretStr] = None
    refresh_token: Optional[SecretStr] = None

    @classmethod
    def initialize(cls, cache: Cache) -> Cache:
        cls.cache = cache
        return cls.cache

    @classmethod
    async def register(cls, data: 'AuthData') -> Optional['AuthData']:
        ret = None
        if cls.cache:
            ret = await cls.cache.set(data.user.email, data)  # type: ignore
        return ret

    @classmethod
    async def get(cls, user: User) -> Optional['AuthData']:
        data = None
        if cls.cache:
            data = await cls.cache.get(user.email)  # type: ignore
        return data


async def get_auth_data(*,
                        authorization: str = Header(None),
                        jwt_settings: JWTSettings = Depends(get_jwt_settings),
                        ) -> AuthData:
    scheme, token = get_authorization_scheme_param(authorization)
    if scheme.lower() != "bearer":
        raise AuthHTTPException(detail="token scheme must be Bearer")
    try:
        token_data: Optional[JWTTokenData] = decode_jwt_token(jwt_settings, token)
        if not token_data:
            raise AuthHTTPException(detail="unable to decode jwt token")
        auth_data: Optional[AuthData] = await AuthData.get(User(email=EmailStr(token_data.sub)))
    except (ValidationError, JWTError) as e:
        raise AuthHTTPException(detail=f"{e}")

    if not auth_data:
        raise AuthHTTPException(detail=f"user {token_data.sub} not found")

    return auth_data


async def get_hoster_token(*,
                           auth_data: AuthData = Depends(get_auth_data)
                           ) -> Optional[SecretStr]:
    return auth_data.hoster_token


async def get_current_user(*,
                           security_scopes: SecurityScopes,
                           auth_data: AuthData = Depends(get_auth_data)
                           ) -> Optional[User]:
    user = auth_data.user
    for scope in security_scopes.scopes:
        if scope not in user.scopes:
            raise AuthHTTPException(detail=f"not enough permissions (missing scope={scope})")
    return user
