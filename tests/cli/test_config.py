import pytest

from cloudops_sentinel.core.config import load_config


def test_defaults_apply(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    cfg = load_config()
    assert cfg.monitoring.interval == 5
    assert cfg.storage.retention_days == 30
    assert cfg.ai.enabled is False


def test_user_config_overrides(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    user = tmp_path / "cfg" / "cloudops-sentinel" / "config.yaml"
    user.parent.mkdir(parents=True)
    user.write_text("monitoring:\n  interval: 9\nstorage:\n  retention_days: 60\n")
    cfg = load_config()
    assert cfg.monitoring.interval == 9
    assert cfg.storage.retention_days == 60
    assert cfg.thresholds.cpu_warning == 70


def test_invalid_yaml_raises(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    user = tmp_path / "cfg" / "cloudops-sentinel" / "config.yaml"
    user.parent.mkdir(parents=True)
    user.write_text("monitoring: [unclosed")
    with pytest.raises(ValueError, match="Invalid YAML"):
        load_config()


def test_invalid_values_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "cfg"))
    user = tmp_path / "cfg" / "cloudops-sentinel" / "config.yaml"
    user.parent.mkdir(parents=True)
    user.write_text("monitoring:\n  interval: 0\n")
    with pytest.raises(ValueError):
        load_config()