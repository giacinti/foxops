from pydantic import BaseSettings, SecretStr


class Settings(BaseSettings):
    gitlab_address: str
    gitlab_token: SecretStr
    static_token: SecretStr
    database_url: SecretStr = SecretStr("sqlite+aiosqlite:///./test.db")
    log_level: str = "INFO"

    class Config:
        env_prefix = "foxops_"
        secrets_dir = "/var/run/secrets/foxops"
