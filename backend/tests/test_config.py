from releaseguard.config import Settings


def test_credentials_not_in_settings_repr():
    text = repr(Settings(password="fake-db-secret", gemini_api_key="fake-key"))
    assert "fake-db-secret" not in text and "fake-key" not in text


def test_default_target_preserves_local_graph(monkeypatch):
    monkeypatch.setenv("FALKORDB_TARGET", "local")
    monkeypatch.setenv("FALKORDB_HOST", "127.0.0.1")
    settings = Settings.load()
    assert settings.target == "local"
    assert settings.host == "127.0.0.1"


def test_cloud_requires_explicit_host_and_credential(monkeypatch):
    import pytest

    monkeypatch.setenv("FALKORDB_TARGET", "cloud")
    monkeypatch.setenv("FALKORDB_CLOUD_HOST", "")
    with pytest.raises(ValueError, match="Cloud host/password"):
        Settings.load()


def test_cloud_tls_verification_enabled_by_default(monkeypatch):
    monkeypatch.setenv("FALKORDB_TARGET", "cloud")
    monkeypatch.setenv("FALKORDB_CLOUD_HOST", "example.invalid")
    monkeypatch.setenv("FALKORDB_CLOUD_PASSWORD", "fake-cloud-secret")
    monkeypatch.setenv("FALKORDB_CLOUD_SSL", "true")
    settings = Settings.load()
    assert settings.ssl
    assert settings.password == "fake-cloud-secret"
    assert "fake-cloud-secret" not in repr(settings)
