from functools import cache
import secrets
from datetime import datetime, timedelta
from typing import Any, Optional, Union, List
from pydantic import BaseModel, BaseSettings, SecretStr

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


class JWTTokenData(BaseModel):
    sub: str
    scopes: List[str] = []


def create_jwt_token(settings: JWTSettings,
                     data: JWTTokenData,
                     expiration: Union[datetime, timedelta, None] = None
                     ) -> str:
    to_encode: dict = data.dict().copy()
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


def decode_jwt_token(settings: JWTSettings,
                     token: str) -> Optional[JWTTokenData]:
    payload: dict[str, Any] = jwt.decode(token,
                                         settings.secret_key.get_secret_value(),
                                         algorithms=[settings.algorithm])
    return JWTTokenData(**payload)
