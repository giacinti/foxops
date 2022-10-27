import pytest
from _pytest.monkeypatch import MonkeyPatch

from foxops.settings import Settings
from foxops.settings import DatabaseSettings
from foxops.hosters.gitlab import GitLabSettings


@pytest.mark.filterwarnings('ignore:directory "/var/run/secrets/foxops" does not exist')
def test_settings_can_load_config_from_env(monkeypatch: MonkeyPatch):
    # GIVEN
    monkeypatch.setenv("FOXOPS_LOGLEVEL", "dummy")
    monkeypatch.setenv("FOXOPS_DATABASE_URL", "dummy")
    monkeypatch.setenv("FOXOPS_GITLAB_ADDRESS", "dummy")
    monkeypatch.setenv("FOXOPS_GITLAB_CLIENT_ID", "dummy")
    monkeypatch.setenv("FOXOPS_GITLAB_CLIENT_SECRET", "dummy")

    # WHEN
    settings = Settings()
    db_settings: DatabaseSettings = DatabaseSettings()
    gitlab_settings: GitLabSettings = GitLabSettings()  # type: ignore

    # THEN
    assert settings.log_level == "dummy"
    assert db_settings.url.get_secret_value() == "dummy"
    assert gitlab_settings.address == "dummy"
    assert gitlab_settings.client_id == "dummy"
    assert gitlab_settings.client_secret.get_secret_value() == "dummy"
