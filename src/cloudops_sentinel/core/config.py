"""Configuration loading and validation.

Chain: built-in Pydantic defaults <- config/default.yaml (repo) <- user config
(~/.config/cloudops-sentinel/config.yaml or $XDG_CONFIG_HOME).
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

APP_DIR_NAME = "cloudops-sentinel"


class MonitoringConfig(BaseModel):
    interval: int = Field(default=5, ge=1)


class ThresholdsConfig(BaseModel):
    cpu_warning: float = 70
    cpu_critical: float = 90
    cpu_duration: int = 300
    memory_warning: float = 75
    memory_critical: float = 90
    disk_warning: float = 80
    disk_critical: float = 90


class StorageConfig(BaseModel):
    retention_days: int = Field(default=30, ge=1)


class AlertsConfig(BaseModel):
    enabled: bool = True


class AnimationsConfig(BaseModel):
    enabled: bool = True


class AIConfig(BaseModel):
    enabled: bool = False


class SentinelConfig(BaseModel):
    monitoring: MonitoringConfig = MonitoringConfig()
    thresholds: ThresholdsConfig = ThresholdsConfig()
    storage: StorageConfig = StorageConfig()
    alerts: AlertsConfig = AlertsConfig()
    animations: AnimationsConfig = AnimationsConfig()
    ai: AIConfig = AIConfig()


def config_dir() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / APP_DIR_NAME


def user_config_path() -> Path:
    return config_dir() / "config.yaml"


def data_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local" / "share")
    return Path(base) / APP_DIR_NAME


def logs_dir() -> Path:
    return data_dir() / "logs"


def _defaults_path() -> Path | None:
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "config" / "default.yaml"
        if candidate.is_file():
            return candidate
    return None


def _load_yaml(path: Path) -> dict:
    try:
        return yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in {path}: {e}") from e


def load_config(path: Path | str | None = None) -> SentinelConfig:
    data: dict = {}
    defaults = _defaults_path()
    if defaults is not None:
        data.update(_load_yaml(defaults))
    user_path = Path(path) if path else user_config_path()
    if user_path.is_file():
        data.update(_load_yaml(user_path))
    return SentinelConfig(**data)