import json

import pytest
from typer.testing import CliRunner

from cloudops_sentinel.cli.app import app

runner = CliRunner()

DB_ENV: dict = {}


def run(*args, env=None):
    merged = {**DB_ENV, **(env or {})}
    return runner.invoke(app, list(args), env=merged)


@pytest.fixture(scope="module")
def db_env(tmp_path_factory):
    DB_ENV["SENTINEL_DB"] = str(tmp_path_factory.mktemp("db") / "sentinel.db")
    return DB_ENV


@pytest.fixture(scope="module")
def simulated(db_env):
    result = run("simulate", "cpu-spike", "--duration", "5", "--json")
    assert result.exit_code == 0
    return json.loads(result.output)["incident"]["id"]


def test_help_shows_grouped_commands():
    result = run("--help")
    assert result.exit_code == 0
    for group in ("Monitoring", "Incidents", "System", "Tools"):
        assert group in result.output


def test_version():
    result = run("--version")
    assert result.exit_code == 0
    assert "CloudOps Sentinel" in result.output


def test_status():
    result = run("status")
    assert result.exit_code == 0
    assert "HOST" in result.output or "CloudOps Sentinel" in result.output
    assert "CPU" in result.output
    assert "HEALTHY" in result.output or "WARNING" in result.output


def test_status_json():
    result = run("status", "--json")
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "host" in data and "resources" in data
    assert isinstance(data["resources"]["cpu"], (int, float))


def test_no_color_flag():
    result = run("status", "--no-color")
    assert result.exit_code == 0
    assert "\x1b[" not in result.output


def test_no_color_env():
    result = run("status", env={"NO_COLOR": "1"})
    assert result.exit_code == 0
    assert "\x1b[" not in result.output


def test_health_runs():
    result = run("health")
    assert result.exit_code in (0, 1, 2)
    assert "Overall Health" in result.output


def test_health_exit_codes(monkeypatch):
    incidents = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    services = [{"name": "ssh", "status": "RUNNING"}]
    host = {"hostname": "x", "os": "Linux", "uptime": "1d"}
    monkeypatch.setattr(
        "cloudops_sentinel.cli.app._status_data",
        lambda: {
            "host": host,
            "resources": {"cpu": 95.0, "memory": 50.0, "disk": 50.0, "network": "NORMAL"},
            "services": services,
            "incidents": incidents,
        },
    )
    assert run("health").exit_code == 2
    monkeypatch.setattr(
        "cloudops_sentinel.cli.app._status_data",
        lambda: {
            "host": host,
            "resources": {"cpu": 80.0, "memory": 50.0, "disk": 50.0, "network": "NORMAL"},
            "services": services,
            "incidents": incidents,
        },
    )
    assert run("health").exit_code == 1


def test_incident_id_validation():
    result = run("diagnose", "not-an-id")
    assert result.exit_code == 1
    assert "INVALID_INCIDENT_ID" in result.output


def test_diagnose_json(simulated):
    result = run("diagnose", simulated, "--json")
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["id"] == simulated
    assert "probable_cause" in data


def test_simulate_unknown_scenario():
    result = run("simulate", "bogus")
    assert result.exit_code == 1
    assert "SIMULATOR_SCENARIO_UNKNOWN" in result.output


def test_simulate_valid_scenario_json(db_env):
    result = run("simulate", "cpu-spike", "--duration", "5", "--json", env=db_env)
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["scenario"] == "cpu-spike"
    assert data["incident"]["id"].startswith("INC-")


def test_config_show_json():
    result = run("config", "--json")
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["storage"]["retention_days"] == 30


def test_retention_set_writes_user_config(tmp_path):
    result = run(
        "retention", "set", "60",
        env={"XDG_CONFIG_HOME": str(tmp_path / "cfg")},
    )
    assert result.exit_code == 0
    written = (tmp_path / "cfg" / "cloudops-sentinel" / "config.yaml").read_text()
    assert "retention_days: 60" in written


def test_incidents_table(simulated):
    result = run("incidents")
    assert result.exit_code == 0
    assert simulated in result.output