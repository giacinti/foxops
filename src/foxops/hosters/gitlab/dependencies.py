from functools import lru_cache
from .settings import GitLabSettings


@lru_cache
def get_gitlab_settings() -> GitLabSettings:
    return GitLabSettings()  # type: ignore
