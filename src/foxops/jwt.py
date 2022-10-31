from functools import cache
import secrets
from datetime import datetime, timedelta
from typing import Any, Optional, Union
from pydantic import BaseModel, BaseSettings, SecretStr, EmailStr

from jose import jwt  # type: ignore
from jose.exceptions import JWTError as JWTError  # type: ignore # noqa: F401


class JWTSettings(BaseSettings):
    secret_key: SecretStr = SecretStr(secrets.token_hex(32))
    algorithm: str = "HS256"
    token_expire: int = 30  # 30 minutes

    class Config:
        env_prefix = "foxops_jwt_"
        secrets_dir = "/var/run/secrets/foxops"


@cache
def get_jwt_settings() -> JWTSettings:
    return JWTSettings()  # type: ignore


class TokenData(BaseModel):
    token_type: str
    exp: Union[datetime, timedelta, None]
    hoster_token: SecretStr
    refresh_token: SecretStr
    user_email: EmailStr


def create_access_token(settings: JWTSettings,
                        data: dict,
                        expiration: Union[datetime, timedelta, None] = None
                        ) -> str:
    to_encode: dict = data.copy()
    if expiration:
        if isinstance(expiration, datetime):
            expire: datetime = expiration
        elif isinstance(expiration, timedelta):
            expire = datetime.utcnow() + expiration
        else:  # should not be there
            raise ValueError("wrong data type for expiration")
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.token_expire)
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(to_encode,
                                  settings.secret_key.get_secret_value(),
                                  settings.algorithm)
    return encoded_jwt


def decode_access_token(settings: JWTSettings,
                        token: str) -> Optional[TokenData]:
    token_data: Optional[TokenData] = None
    payload: dict[str, Any] = jwt.decode(token,
                                         settings.secret_key.get_secret_value(),
                                         algorithms=[settings.algorithm])
    token_data = TokenData(**payload)
    return token_data
