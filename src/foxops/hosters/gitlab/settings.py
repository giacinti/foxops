from pydantic import BaseSettings, SecretStr
from functools import cache


class GitLabSettings(BaseSettings):
    address: str
    client_id: str
    client_secret: SecretStr
    client_scope: str = "api"

    class Config:
        env_prefix: str = "foxops_gitlab_"
        secrets_dir: str = "/var/run/secrets/foxops"


@cache
def get_gitlab_settings() -> GitLabSettings:
    return GitLabSettings()  # type: ignore
