"""Detection rules — build :class:`Rule` objects from config.

Config source is Part 1's ``core.config.SentinelConfig`` (thresholds for
cpu/memory/disk). Event/log-based signals have built-in defaults (PRD §15):
no config surface for them in V1.
"""

from __future__ import annotations

from cloudops_sentinel.core.config import SentinelConfig
from cloudops_sentinel.models.rule import Rule

DEFAULT_RULES: dict[str, Rule] = {
    "service": Rule(metric="service", critical=1, operator="gte"),
    "http_errors": Rule(metric="http_errors", warning=5, critical=20, operator="gte"),
    "log_error_spike": Rule(metric="log_error_spike", warning=10, critical=50, operator="gte"),
}


def rules_from_config(cfg: SentinelConfig | None = None) -> dict[str, Rule]:
    """Config thresholds → Rules. Missing/None config → PRD §15 defaults."""
    rules: dict[str, Rule] = {
        "cpu": Rule(
            metric="cpu",
            warning=70,
            critical=90,
            duration=300,
        ),
        "memory": Rule(metric="memory", warning=75, critical=90),
        "disk": Rule(metric="disk", warning=80, critical=90),
    }
    if cfg is not None:
        t = cfg.thresholds
        rules["cpu"] = Rule(
            metric="cpu",
            warning=t.cpu_warning,
            critical=t.cpu_critical,
            duration=t.cpu_duration,
        )
        rules["memory"] = Rule(
            metric="memory", warning=t.memory_warning, critical=t.memory_critical
        )
        rules["disk"] = Rule(metric="disk", warning=t.disk_warning, critical=t.disk_critical)
    rules.update(DEFAULT_RULES)
    return rules
